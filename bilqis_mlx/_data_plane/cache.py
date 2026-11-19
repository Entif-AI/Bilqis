"""Integrity-cache and data-plane statistics helpers."""
from __future__ import annotations

import time
from pathlib import Path


class DataPlaneCacheMixin:
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
                "LIMIT 1", (expected_sha256, *identity)).fetchone()
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
            legacy_objects = self._db.execute(
                "SELECT COUNT(*),COALESCE(SUM(length(payload)),0),COALESCE(SUM(raw_bytes),0) "
                "FROM objects").fetchone()
            archived_objects = self._db.execute(
                "SELECT COUNT(*),COALESCE(SUM(compressed_bytes),0),COALESCE(SUM(raw_bytes),0) "
                "FROM archived_objects").fetchone()
            legacy_nodes = self._db.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            archived_nodes = self._db.execute(
                "SELECT COUNT(*),COALESCE(SUM(compressed_bytes),0) "
                "FROM archived_nodes").fetchone()
            verified = self._db.execute("SELECT COUNT(*) FROM verified_files").fetchone()[0]
            event_ledgers = self._db.execute("SELECT COUNT(*) FROM event_ledgers").fetchone()[0]
            indexed_events = self._db.execute("SELECT COUNT(*) FROM event_index").fetchone()[0]
        return {
            "path": str(self.path),
            "objects": legacy_objects[0] + archived_objects[0],
            "compressed_object_bytes": legacy_objects[1] + archived_objects[1],
            "raw_object_bytes": legacy_objects[2] + archived_objects[2],
            "legacy_objects": legacy_objects[0], "archived_objects": archived_objects[0],
            "legacy_nodes": legacy_nodes, "archived_nodes": archived_nodes[0],
            "archived_node_bytes": archived_nodes[1],
            "nodes": legacy_nodes + archived_nodes[0], "verified_files": verified,
            "event_ledgers": event_ledgers, "indexed_events": indexed_events,
        }
