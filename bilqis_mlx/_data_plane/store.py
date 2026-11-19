"""SQLite connection and immutable object/node metadata owner."""
from __future__ import annotations
import hashlib
import sqlite3
import threading
import zlib
from contextlib import contextmanager
from pathlib import Path
from .contracts import (
    LEGACY_SCHEMA_VERSION, SCHEMA_VERSION, SQLITE_BUSY_TIMEOUT_MS, SQLITE_MMAP_BYTES, SQLITE_CACHE_KIB,
    DataPlaneError, _error,
)
from .schema import CORE_SCHEMA_SQL, C05_FIXED_SCHOOL_TRUST_SQL, PLANNER_FRONTIER_TRUST_SQL

class DataPlaneStoreMixin:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._archive_dirty_paths: set[Path] = set()
        self._db = sqlite3.connect(
            self.path, timeout=30.0, isolation_level=None, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
        self._db.execute("PRAGMA temp_store=MEMORY")
        self._db.execute(f"PRAGMA mmap_size={SQLITE_MMAP_BYTES}")
        self._db.execute(f"PRAGMA cache_size=-{SQLITE_CACHE_KIB}")
        self._db.executescript(CORE_SCHEMA_SQL)
        self._db.executescript(C05_FIXED_SCHOOL_TRUST_SQL)
        self._db.executescript(PLANNER_FRONTIER_TRUST_SQL)
        row = self._db.execute(
            "SELECT value FROM meta WHERE key='schema_version'").fetchone()
        if row is None:
            self._db.execute(
                "INSERT INTO meta(key,value) VALUES('schema_version',?)",
                (str(SCHEMA_VERSION),))
        elif int(row[0]) == LEGACY_SCHEMA_VERSION:
            self._db.execute(
                "UPDATE meta SET value=? WHERE key='schema_version'",
                (str(SCHEMA_VERSION),))
        elif int(row[0]) != SCHEMA_VERSION:
            raise ValueError(DataPlaneError.SCHEMA_UNSUPPORTED.value)

    def close(self) -> None:
        with self._lock:
            self._db.close()

    @contextmanager
    def transaction(self):
        """One durable multi-object commit; nested callers share this connection."""
        with self._lock:
            if self._db.in_transaction:
                yield self
                return
            self._db.execute("BEGIN IMMEDIATE")
            try:
                yield self
            except BaseException:
                self._db.execute("ROLLBACK")
                self._archive_dirty_paths.clear()
                raise
            else:
                self._archive_flush()
                self._db.execute("COMMIT")

    def put_object(self, digest: str, raw: bytes) -> None:
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(DataPlaneError.OBJECT_DIGEST_INVALID.value)
        with self._lock:
            with self.transaction():
                exists = self._db.execute(
                    "SELECT 1 FROM archived_objects WHERE sha256=? UNION ALL "
                    "SELECT 1 FROM objects WHERE sha256=? LIMIT 1",
                    (digest, digest)).fetchone()
                if exists is not None:
                    return
                payload = zlib.compress(raw, level=6)
                pack_id, offset = self._archive_append(
                    "objects", digest, len(raw), payload)
                self._db.execute(
                    "INSERT INTO archived_objects("
                    "sha256,pack_id,pack_offset,raw_bytes,compressed_bytes) VALUES(?,?,?,?,?)",
                    (digest, pack_id, offset, len(raw), len(payload)))

    def get_object(self, digest: str) -> bytes:
        with self._lock:
            archived = self._db.execute(
                "SELECT pack_id,pack_offset,raw_bytes,compressed_bytes "
                "FROM archived_objects WHERE sha256=?", (digest,)).fetchone()
            if archived is not None:
                return self._archive_read("objects", *archived[:2], digest,
                                          archived[2], archived[3])
            row = self._db.execute(
                "SELECT payload,raw_bytes FROM objects WHERE sha256=?", (digest,)
            ).fetchone()
        if row is None:
            raise ValueError(_error(DataPlaneError.OBJECT_MISSING, digest))
        raw = zlib.decompress(row[0])
        if len(raw) != row[1] or hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(_error(DataPlaneError.OBJECT_CORRUPTED, digest))
        return raw

    def put_object_reference(self, reference: str, raw: bytes) -> str:
        """Atomically point one stable data-plane name at immutable content."""
        if (not isinstance(reference, str) or not reference
                or "\n" in reference or "\r" in reference):
            raise ValueError(DataPlaneError.OBJECT_DIGEST_INVALID.value)
        digest = hashlib.sha256(raw).hexdigest()
        self.put_object(digest, raw)
        with self.transaction():
            self._db.execute(
                "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
                ("object_reference_v1:" + reference, digest),
            )
        return digest

    def get_object_reference(self, reference: str) -> tuple[str, bytes] | None:
        """Resolve a stable data-plane name without weakening content integrity."""
        if (not isinstance(reference, str) or not reference
                or "\n" in reference or "\r" in reference):
            raise ValueError(DataPlaneError.OBJECT_DIGEST_INVALID.value)
        with self._lock:
            row = self._db.execute(
                "SELECT value FROM meta WHERE key=?",
                ("object_reference_v1:" + reference,),
            ).fetchone()
        if row is None:
            return None
        digest = row[0]
        return digest, self.get_object(digest)

    def put_node(self, digest: str, raw: bytes, generation: int,
                 parent_sha256: str | None) -> None:
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(DataPlaneError.NODE_DIGEST_INVALID.value)
        with self._lock:
            with self.transaction():
                exists = self._db.execute(
                    "SELECT 1 FROM archived_nodes WHERE sha256=? UNION ALL "
                    "SELECT 1 FROM nodes WHERE sha256=? LIMIT 1",
                    (digest, digest)).fetchone()
                if exists is not None:
                    return
                payload = zlib.compress(raw, level=6)
                pack_id, offset = self._archive_append(
                    "nodes", digest, len(raw), payload)
                self._db.execute(
                    "INSERT INTO archived_nodes("
                    "sha256,pack_id,pack_offset,raw_bytes,compressed_bytes,generation,parent_sha256) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (digest, pack_id, offset, len(raw), len(payload), generation, parent_sha256))

    def get_node(self, digest: str) -> bytes:
        with self._lock:
            archived = self._db.execute(
                "SELECT pack_id,pack_offset,raw_bytes,compressed_bytes "
                "FROM archived_nodes WHERE sha256=?", (digest,)).fetchone()
            if archived is not None:
                return self._archive_read("nodes", *archived[:2], digest,
                                          archived[2], archived[3])
            row = self._db.execute(
                "SELECT payload FROM nodes WHERE sha256=?", (digest,)).fetchone()
        if row is None:
            raise ValueError(_error(DataPlaneError.NODE_MISSING, digest))
        raw = row[0]
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(_error(DataPlaneError.NODE_CORRUPTED, digest))
        return raw
