"""Crash-safe append-only pack storage for immutable data-plane payloads."""
from __future__ import annotations

import fcntl
import hashlib
import os
import sqlite3
import struct
import uuid
import zlib
from contextlib import contextmanager
from pathlib import Path
from .contracts import DataPlaneError

_MAGIC = b"BQPK1"
_HEADER = struct.Struct(">5s32sQQ")
_METADATA_UPDATE_BATCH_RECORDS = 1000


class DataPlaneArchiveMixin:
    """Store immutable payload bytes outside the hot SQLite control database."""

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def _ensure_archive_directory(self, path: Path) -> None:
        missing = []
        cursor = path
        while not cursor.exists():
            missing.append(cursor)
            cursor = cursor.parent
        path.mkdir(parents=True, exist_ok=True)
        for created in reversed(missing):
            self._fsync_directory(created.parent)

    def _archive_root(self) -> Path:
        root = self.path.with_name(self.path.name + ".archive")
        self._ensure_archive_directory(root)
        return root

    def _archive_pack_path(self, kind: str, pack_id: str) -> Path:
        root = self._archive_root() / kind
        self._ensure_archive_directory(root)
        return root / f"{pack_id}.pack"

    def _archive_lock_path(self, kind: str) -> Path:
        root = self._archive_root() / kind
        self._ensure_archive_directory(root)
        return root / ".pack.lock"

    @contextmanager
    def _archive_lock(self, kind: str, *, exclusive: bool):
        lock = self._archive_lock_path(kind)
        with lock.open("a+b") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def _archive_current_pack(self, kind: str) -> str:
        key = f"archive_pack_v1:{kind}"
        row = self._db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        if row is not None:
            return row[0]
        pack_id = "0"
        self._db.execute(
            "INSERT OR IGNORE INTO meta(key,value) VALUES(?,?)", (key, pack_id))
        return pack_id

    def _archive_append(self, kind: str, digest: str, raw_bytes: int,
                        compressed: bytes) -> tuple[str, int]:
        row = self._archive_append_many(kind, ((digest, raw_bytes, compressed),))[0]
        return row[1], row[2]

    def _archive_append_many(self, kind: str, records) -> list[tuple[str, str, int, int, int]]:
        """Append one batch under one pack lock and one file descriptor."""
        records = tuple(records)
        if not records:
            return []
        pack_id = self._archive_current_pack(kind)
        path = self._archive_pack_path(kind, pack_id)
        result = []
        with self._archive_lock(kind, exclusive=True):
            with path.open("ab") as stream:
                for digest, raw_bytes, compressed in records:
                    offset = stream.tell()
                    stream.write(_HEADER.pack(
                        _MAGIC, bytes.fromhex(digest), raw_bytes, len(compressed)))
                    stream.write(compressed)
                    result.append((digest, pack_id, offset, raw_bytes, len(compressed)))
                stream.flush()
            self._archive_dirty_paths.add(path)
        return result

    def _archive_flush(self) -> None:
        for path in tuple(self._archive_dirty_paths):
            if not path.exists():
                continue
            with path.open("rb") as stream:
                os.fsync(stream.fileno())
            self._fsync_directory(path.parent)
        self._archive_dirty_paths.clear()

    def _archive_read(self, kind: str, pack_id: str, offset: int,
                      digest: str, raw_bytes: int, compressed_bytes: int) -> bytes:
        path = self.path.with_name(self.path.name + ".archive") / kind / f"{pack_id}.pack"
        with self._archive_lock(kind, exclusive=False):
            with path.open("rb") as stream:
                stream.seek(offset)
                header = stream.read(_HEADER.size)
                if len(header) != _HEADER.size:
                    raise ValueError(DataPlaneError.ARCHIVE_TRUNCATED.value)
                magic, encoded_digest, recorded_raw, recorded_compressed = _HEADER.unpack(header)
                if (magic != _MAGIC or encoded_digest.hex() != digest or
                        recorded_raw != raw_bytes or recorded_compressed != compressed_bytes):
                    raise ValueError(DataPlaneError.ARCHIVE_HEADER_DRIFT.value)
                compressed = stream.read(compressed_bytes)
        if len(compressed) != compressed_bytes:
            raise ValueError(DataPlaneError.ARCHIVE_TRUNCATED.value)
        raw = zlib.decompress(compressed)
        if len(raw) != raw_bytes or hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(DataPlaneError.ARCHIVE_CONTENT_DRIFT.value)
        return raw

    def compact_archive(self, kind: str) -> dict:
        """Rewrite one pack family to only metadata-reachable records."""
        if kind not in {"objects", "nodes"}:
            raise ValueError(DataPlaneError.ARCHIVE_KIND_INVALID.value)
        table = "archived_objects" if kind == "objects" else "archived_nodes"
        columns = ("sha256,pack_id,pack_offset,raw_bytes,compressed_bytes" if kind == "objects"
                   else "sha256,pack_id,pack_offset,raw_bytes,compressed_bytes")
        # Match normal writer lock order: SQLite write ownership first, pack lock second.
        # Otherwise a writer holding BEGIN IMMEDIATE and a compactor holding the pack
        # lock could wait on each other forever.
        with self._lock, self.transaction():
            with self._archive_lock(kind, exclusive=True):
                old_paths = set((self._archive_root() / kind).glob("*.pack"))
                pack_id = uuid.uuid4().hex
                target = self._archive_pack_path(kind, pack_id)
                reader = sqlite3.connect(
                    self.path.resolve().as_uri() + "?mode=ro", uri=True,
                    isolation_level=None)
                source_stream = None
                source_pack = None
                updates = []
                records = 0
                try:
                    rows = reader.execute(
                        f"SELECT {columns} FROM {table} ORDER BY pack_id,pack_offset")
                    with target.open("xb") as out:
                        for digest, old_pack, old_offset, _raw_bytes, compressed_bytes in rows:
                            if old_pack != source_pack:
                                if source_stream is not None:
                                    source_stream.close()
                                source_path = (
                                    self.path.with_name(self.path.name + ".archive")
                                    / kind / f"{old_pack}.pack")
                                source_stream = source_path.open("rb")
                                source_pack = old_pack
                            source_stream.seek(old_offset)
                            record = source_stream.read(_HEADER.size + compressed_bytes)
                            if len(record) != _HEADER.size + compressed_bytes:
                                raise ValueError(DataPlaneError.ARCHIVE_TRUNCATED.value)
                            offset = out.tell()
                            out.write(record)
                            updates.append((pack_id, offset, digest))
                            records += 1
                            if len(updates) >= _METADATA_UPDATE_BATCH_RECORDS:
                                self._db.executemany(
                                    f"UPDATE {table} SET pack_id=?,pack_offset=? WHERE sha256=?",
                                    updates)
                                updates.clear()
                        if updates:
                            self._db.executemany(
                                f"UPDATE {table} SET pack_id=?,pack_offset=? WHERE sha256=?",
                                updates)
                        out.flush()
                        os.fsync(out.fileno())
                finally:
                    if source_stream is not None:
                        source_stream.close()
                    reader.close()
                self._fsync_directory(target.parent)
                self._db.execute(
                    "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
                    (f"archive_pack_v1:{kind}", pack_id))
        for path in old_paths:
            if path != target and path.exists():
                path.unlink()
        self._fsync_directory(target.parent)
        return {"kind": kind, "records": records,
                "pack_bytes": target.stat().st_size}
