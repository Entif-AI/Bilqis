"""SQLite object, node, verification, and statistics owner."""
from __future__ import annotations
import hashlib
import sqlite3
import threading
import time
import zlib
from contextlib import contextmanager
from pathlib import Path
from .contracts import (SCHEMA_VERSION, SQLITE_BUSY_TIMEOUT_MS, SQLITE_MMAP_BYTES, SQLITE_CACHE_KIB, DataPlaneError, _error)

_C05_FIXED_SCHOOL_TRUST_SQL = """
CREATE TABLE IF NOT EXISTS bamf_c05_fixed_school_trust(
    run_identity_sha256 TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    foundation_parent_manifest_sha256 TEXT NOT NULL,
    receipt_sha256 TEXT NOT NULL UNIQUE,
    receipt_payload BLOB NOT NULL,
    cohort_sha256 TEXT NOT NULL,
    cohort_payload_sha256 TEXT NOT NULL,
    cohort_payload BLOB NOT NULL
) WITHOUT ROWID;
CREATE TRIGGER IF NOT EXISTS bamf_c05_fixed_school_trust_no_update
BEFORE UPDATE ON bamf_c05_fixed_school_trust
BEGIN
    SELECT RAISE(ABORT, 'BAMF_C05_FIXED_SCHOOL_TRUST_IMMUTABLE');
END;
CREATE TRIGGER IF NOT EXISTS bamf_c05_fixed_school_trust_no_delete
BEFORE DELETE ON bamf_c05_fixed_school_trust
BEGIN
    SELECT RAISE(ABORT, 'BAMF_C05_FIXED_SCHOOL_TRUST_IMMUTABLE');
END;
"""

_PLANNER_FRONTIER_TRUST_SQL = """
CREATE TABLE IF NOT EXISTS bamf_planner_frontier_trust(
    trust_key_sha256 TEXT PRIMARY KEY,
    builder_sha256 TEXT NOT NULL,
    input_digest TEXT NOT NULL,
    factory_release_sha256 TEXT NOT NULL,
    output_digest TEXT NOT NULL,
    frontier_release_sha256 TEXT NOT NULL,
    receipt_sha256 TEXT NOT NULL UNIQUE,
    receipt_payload BLOB NOT NULL
) WITHOUT ROWID;
CREATE TRIGGER IF NOT EXISTS bamf_planner_frontier_trust_no_update
BEFORE UPDATE ON bamf_planner_frontier_trust
BEGIN
    SELECT RAISE(ABORT, 'BAMF_PLANNER_FRONTIER_TRUST_IMMUTABLE');
END;
CREATE TRIGGER IF NOT EXISTS bamf_planner_frontier_trust_no_delete
BEFORE DELETE ON bamf_planner_frontier_trust
BEGIN
    SELECT RAISE(ABORT, 'BAMF_PLANNER_FRONTIER_TRUST_IMMUTABLE');
END;
"""

class DataPlaneStoreMixin:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(
            self.path, timeout=30.0, isolation_level=None, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
        self._db.execute("PRAGMA temp_store=MEMORY")
        self._db.execute(f"PRAGMA mmap_size={SQLITE_MMAP_BYTES}")
        self._db.execute(f"PRAGMA cache_size=-{SQLITE_CACHE_KIB}")
        self._db.executescript("""
        CREATE TABLE IF NOT EXISTS meta(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE IF NOT EXISTS objects(
            sha256 TEXT PRIMARY KEY,
            payload BLOB NOT NULL,
            raw_bytes INTEGER NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE IF NOT EXISTS nodes(
            sha256 TEXT PRIMARY KEY,
            payload BLOB NOT NULL,
            generation INTEGER NOT NULL,
            parent_sha256 TEXT
        ) WITHOUT ROWID;
        CREATE TABLE IF NOT EXISTS verified_files(
            path TEXT NOT NULL,
            expected_sha256 TEXT NOT NULL,
            st_dev INTEGER NOT NULL,
            st_ino INTEGER NOT NULL,
            size_bytes INTEGER NOT NULL,
            mtime_ns INTEGER NOT NULL,
            ctime_ns INTEGER NOT NULL,
            verified_ns INTEGER NOT NULL,
            PRIMARY KEY(path, expected_sha256)
        ) WITHOUT ROWID;
        CREATE INDEX IF NOT EXISTS verified_files_identity
        ON verified_files(expected_sha256,st_dev,st_ino,size_bytes,mtime_ns,ctime_ns);
        CREATE TABLE IF NOT EXISTS event_ledgers(
            run_dir TEXT PRIMARY KEY,
            st_dev INTEGER NOT NULL,
            st_ino INTEGER NOT NULL,
            indexed_bytes INTEGER NOT NULL,
            mtime_ns INTEGER NOT NULL,
            ctime_ns INTEGER NOT NULL
        ) WITHOUT ROWID;
        CREATE TABLE IF NOT EXISTS event_index(
            run_dir TEXT NOT NULL,
            event_id TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            occurrences INTEGER NOT NULL,
            conflicted INTEGER NOT NULL,
            PRIMARY KEY(run_dir, event_id)
        ) WITHOUT ROWID;
        CREATE TABLE IF NOT EXISTS bamf_genesis_trust(
            run_id TEXT PRIMARY KEY,
            generation INTEGER NOT NULL CHECK(generation = 0),
            manifest_sha256 TEXT NOT NULL UNIQUE,
            payload_sha256 TEXT NOT NULL,
            payload BLOB NOT NULL
        ) WITHOUT ROWID;
        CREATE TRIGGER IF NOT EXISTS bamf_genesis_trust_no_update
        BEFORE UPDATE ON bamf_genesis_trust
        BEGIN
            SELECT RAISE(ABORT, 'BAMF_GENESIS_TRUST_IMMUTABLE');
        END;
        CREATE TRIGGER IF NOT EXISTS bamf_genesis_trust_no_delete
        BEFORE DELETE ON bamf_genesis_trust
        BEGIN
            SELECT RAISE(ABORT, 'BAMF_GENESIS_TRUST_IMMUTABLE');
        END;
        """)
        self._db.executescript(_C05_FIXED_SCHOOL_TRUST_SQL)
        self._db.executescript(_PLANNER_FRONTIER_TRUST_SQL)
        row = self._db.execute(
            "SELECT value FROM meta WHERE key='schema_version'").fetchone()
        if row is None:
            self._db.execute(
                "INSERT INTO meta(key,value) VALUES('schema_version',?)",
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
                raise
            else:
                self._db.execute("COMMIT")

    def put_object(self, digest: str, raw: bytes) -> None:
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(DataPlaneError.OBJECT_DIGEST_INVALID.value)
        payload = zlib.compress(raw, level=6)
        with self._lock:
            self._db.execute(
                "INSERT OR IGNORE INTO objects(sha256,payload,raw_bytes) VALUES(?,?,?)",
                (digest, payload, len(raw)))

    def get_object(self, digest: str) -> bytes:
        with self._lock:
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
            self._db.execute(
                "INSERT OR IGNORE INTO nodes(sha256,payload,generation,parent_sha256) "
                "VALUES(?,?,?,?)",
                (digest, raw, generation, parent_sha256))

    def get_node(self, digest: str) -> bytes:
        with self._lock:
            row = self._db.execute(
                "SELECT payload FROM nodes WHERE sha256=?", (digest,)).fetchone()
        if row is None:
            raise ValueError(_error(DataPlaneError.NODE_MISSING, digest))
        raw = row[0]
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(_error(DataPlaneError.NODE_CORRUPTED, digest))
        return raw

    @staticmethod
    def _stat_identity(path: Path) -> tuple[int, int, int, int, int]:
        st = path.stat()
        return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)

    def verified_file(self, path: Path, expected_sha256: str) -> bool:
        path = Path(path).resolve(strict=True)
        identity = self._stat_identity(path)
        with self._lock:
            row = self._db.execute(
                "SELECT st_dev,st_ino,size_bytes,mtime_ns,ctime_ns "
                "FROM verified_files WHERE path=? AND expected_sha256=?",
                (str(path), expected_sha256)).fetchone()
            if row == identity:
                return True
            alias = self._db.execute(
                "SELECT 1 FROM verified_files WHERE expected_sha256=? AND "
                "st_dev=? AND st_ino=? AND size_bytes=? AND mtime_ns=? AND ctime_ns=? "
                "LIMIT 1",
                (expected_sha256, *identity)).fetchone()
        return alias is not None

    def remember_verified_file(self, path: Path, expected_sha256: str) -> None:
        path = Path(path).resolve(strict=True)
        dev, ino, size, mtime, ctime = self._stat_identity(path)
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO verified_files("
                "path,expected_sha256,st_dev,st_ino,size_bytes,mtime_ns,ctime_ns,verified_ns"
                ") VALUES(?,?,?,?,?,?,?,?)",
                (str(path), expected_sha256, dev, ino, size, mtime, ctime,
                 time.time_ns()))

    def stats(self) -> dict:
        with self._lock:
            objects = self._db.execute(
                "SELECT COUNT(*),COALESCE(SUM(length(payload)),0),COALESCE(SUM(raw_bytes),0) "
                "FROM objects").fetchone()
            nodes = self._db.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            verified = self._db.execute(
                "SELECT COUNT(*) FROM verified_files").fetchone()[0]
            event_ledgers = self._db.execute(
                "SELECT COUNT(*) FROM event_ledgers").fetchone()[0]
            indexed_events = self._db.execute(
                "SELECT COUNT(*) FROM event_index").fetchone()[0]
        return {
            "path": str(self.path), "objects": objects[0],
            "compressed_object_bytes": objects[1], "raw_object_bytes": objects[2],
            "nodes": nodes, "verified_files": verified,
            "event_ledgers": event_ledgers, "indexed_events": indexed_events,
        }
