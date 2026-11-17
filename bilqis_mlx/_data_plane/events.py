"""Append-only event ledger indexing owner."""
from __future__ import annotations
import json
from pathlib import Path
from .contracts import DataPlaneError, _error, _read_event_tail

class DataPlaneEventMixin:
    def _event_ledger_state(self, key, stat):
        with self._lock:
            prior = self._db.execute(
                "SELECT st_dev,st_ino,indexed_bytes,mtime_ns,ctime_ns "
                "FROM event_ledgers WHERE run_dir=?", (key,)).fetchone()
            stream_frontier = self._db.execute(
                "SELECT COALESCE(MAX(end_byte),0) FROM event_stream WHERE run_dir=?",
                (key,)).fetchone()[0]
        rebuild = (
            prior is None or prior[0] != stat.st_dev or prior[1] != stat.st_ino or
            prior[2] > stat.st_size or
            (prior[2] == stat.st_size and
             (prior[3] != stat.st_mtime_ns or prior[4] != stat.st_ctime_ns)) or
            (prior is not None and prior[2] != stream_frontier)
        )
        return prior, rebuild

    def _event_count(self, key):
        with self._lock:
            return self._db.execute(
                "SELECT COUNT(*) FROM event_index WHERE run_dir=?", (key,)
            ).fetchone()[0]

    def _clear_event_projection(self, key):
        self._db.execute("DELETE FROM event_index WHERE run_dir=?", (key,))
        self._db.execute("DELETE FROM event_stream WHERE run_dir=?", (key,))
        self._db.execute("DELETE FROM event_projections WHERE run_dir=?", (key,))

    def _index_event_observation(self, key, event_id, digest):
        row = self._db.execute(
            "SELECT payload_sha256,occurrences,conflicted FROM event_index "
            "WHERE run_dir=? AND event_id=?", (key, event_id)).fetchone()
        if row is None:
            self._db.execute(
                "INSERT INTO event_index(run_dir,event_id,payload_sha256,"
                "occurrences,conflicted) VALUES(?,?,?,?,?)",
                (key, event_id, digest, 1, False))
            return
        conflicted = bool(row[2]) or row[0] != digest
        self._db.execute(
            "UPDATE event_index SET occurrences=?,conflicted=? "
            "WHERE run_dir=? AND event_id=?",
            (row[1] + 1, conflicted, key, event_id))

    def _commit_event_tail(self, key, observed, end, fresh, rebuild):
        with self.transaction():
            if rebuild:
                self._clear_event_projection(key)
            sequence = self._db.execute(
                "SELECT COALESCE(MAX(sequence),0) FROM event_stream WHERE run_dir=?",
                (key,)).fetchone()[0]
            for event_id, digest, line_start, line_end, payload in observed:
                sequence += 1
                self._db.execute(
                    "INSERT INTO event_stream(run_dir,sequence,start_byte,end_byte,event_id,"
                    "payload_sha256,payload) VALUES(?,?,?,?,?,?,?)",
                    (key, sequence, line_start, line_end, event_id, digest, payload))
                if digest is not None:
                    self._index_event_observation(key, event_id, digest)
            self._db.execute(
                "INSERT OR REPLACE INTO event_ledgers("
                "run_dir,st_dev,st_ino,indexed_bytes,mtime_ns,ctime_ns"
                ") VALUES(?,?,?,?,?,?)",
                (key, fresh.st_dev, fresh.st_ino, end,
                 fresh.st_mtime_ns, fresh.st_ctime_ns))
            return self._event_count(key)

    def sync_event_ledger(self, run_dir: Path) -> dict:
        """Index only the unseen append-only JSONL tail for one run."""
        root = Path(run_dir).resolve(strict=True)
        key = str(root)
        ledger = root / "events.jsonl"
        if ledger.is_symlink():
            raise ValueError(_error(DataPlaneError.EVENT_LEDGER_UNSAFE, ledger))
        if not ledger.exists():
            with self.transaction():
                self._clear_event_projection(key)
                self._db.execute("DELETE FROM event_ledgers WHERE run_dir=?", (key,))
            return {"run_dir": key, "indexed_bytes": 0, "scanned_bytes": 0,
                    "indexed_events": 0, "rebuilt": False}
        if not ledger.is_file():
            raise ValueError(_error(DataPlaneError.EVENT_LEDGER_UNSAFE, ledger))
        stat = ledger.stat()
        prior, rebuild = self._event_ledger_state(key, stat)
        start = 0 if rebuild else prior[2]
        if start == stat.st_size and not rebuild:
            count = self._event_count(key)
            return {"run_dir": key, "indexed_bytes": start, "scanned_bytes": 0,
                    "indexed_events": count, "rebuilt": False}

        observed, end = _read_event_tail(ledger, start)
        fresh = ledger.stat()
        count = self._commit_event_tail(key, observed, end, fresh, rebuild)
        return {"run_dir": key, "indexed_bytes": end,
                "scanned_bytes": end - start, "indexed_events": count,
                "rebuilt": rebuild}

    def indexed_event_tail(self, run_dir: Path, after_byte: int = 0) -> dict:
        """Return ordered indexed payloads after one durable byte frontier."""
        if type(after_byte) is not int or after_byte < 0:
            raise ValueError("DATA_PLANE_EVENT_CURSOR_INVALID")
        synced = self.sync_event_ledger(run_dir)
        key = synced["run_dir"]
        with self._lock:
            identity = self._db.execute(
                "SELECT st_dev,st_ino,indexed_bytes FROM event_ledgers WHERE run_dir=?",
                (key,)).fetchone()
            rows = self._db.execute(
                "SELECT sequence,start_byte,end_byte,payload FROM event_stream "
                "WHERE run_dir=? AND end_byte>? ORDER BY sequence",
                (key, after_byte)).fetchall()
        events = tuple(json.loads(row[3]) for row in rows)
        return {
            **synced,
            "ledger_identity": None if identity is None else (identity[0], identity[1]),
            "events": events,
            "event_count": len(events),
        }

    def event_projection_state(
            self, run_dir: Path, projection_key: str, schema_version: str) -> dict | None:
        key = str(Path(run_dir).resolve(strict=True))
        with self._lock:
            row = self._db.execute(
                "SELECT st_dev,st_ino,indexed_bytes,payload FROM event_projections "
                "WHERE run_dir=? AND projection_key=? AND schema_version=?",
                (key, projection_key, schema_version)).fetchone()
        if row is None:
            return None
        return {
            "ledger_identity": (row[0], row[1]),
            "indexed_bytes": row[2],
            "payload": json.loads(row[3]),
        }

    def remember_event_projection(
            self, run_dir: Path, projection_key: str, schema_version: str,
            ledger_identity: tuple[int, int], indexed_bytes: int, payload: dict) -> None:
        key = str(Path(run_dir).resolve(strict=True))
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with self._lock:
            current = self._db.execute(
                "SELECT st_dev,st_ino,indexed_bytes FROM event_ledgers WHERE run_dir=?",
                (key,)).fetchone()
        expected = (ledger_identity[0], ledger_identity[1], indexed_bytes)
        if current is None or current != expected:
            raise ValueError("DATA_PLANE_EVENT_PROJECTION_FRONTIER_DRIFT")
        with self.transaction():
            self._db.execute(
                "INSERT OR REPLACE INTO event_projections("
                "run_dir,projection_key,schema_version,st_dev,st_ino,indexed_bytes,payload"
                ") VALUES(?,?,?,?,?,?,?)",
                (key, projection_key, schema_version, ledger_identity[0],
                 ledger_identity[1], indexed_bytes, raw))

    def event_observations(self, run_dir: Path, event_ids) -> dict:
        self.sync_event_ledger(run_dir)
        key = str(Path(run_dir).resolve(strict=True))
        result = {}
        with self._lock:
            for event_id in event_ids:
                row = self._db.execute(
                    "SELECT payload_sha256,occurrences,conflicted FROM event_index "
                    "WHERE run_dir=? AND event_id=?", (key, event_id)).fetchone()
                if row is not None:
                    result[event_id] = (row[0], row[1], bool(row[2]))
        return result
