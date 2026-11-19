"""Streaming legacy-payload migration for the shared data plane."""
from __future__ import annotations

import hashlib
import zlib


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def migrate_legacy_payloads(plane, *, max_records: int = 0) -> dict:
    """Move legacy SQLite BLOB rows into append-only archive packs."""
    if type(max_records) is not int or max_records < 0:
        raise ValueError("BILQIS_DATA_PLANE_MIGRATION_BUDGET_INVALID")
    moved_objects = moved_nodes = 0
    remaining = max_records
    while True:
        limit = 1000 if not max_records else min(1000, remaining)
        if limit <= 0:
            break
        rows = list(plane._db.execute(
            "SELECT sha256,payload,raw_bytes FROM objects LIMIT ?", (limit,)))
        if not rows:
            break
        with plane.transaction():
            pending = []
            for digest, compressed, raw_bytes in rows:
                raw = zlib.decompress(compressed)
                if len(raw) != raw_bytes or _sha(raw) != digest:
                    raise ValueError("BILQIS_DATA_PLANE_OBJECT_CORRUPTED:" + digest)
                if not plane._db.execute(
                        "SELECT 1 FROM archived_objects WHERE sha256=?", (digest,)).fetchone():
                    pending.append((digest, raw_bytes, compressed))
            for digest, pack_id, offset, raw_bytes, compressed_bytes in \
                    plane._archive_append_many("objects", pending):
                plane._db.execute(
                    "INSERT INTO archived_objects(sha256,pack_id,pack_offset,raw_bytes,compressed_bytes) "
                    "VALUES(?,?,?,?,?)",
                    (digest, pack_id, offset, raw_bytes, compressed_bytes))
            for digest, _compressed, _raw_bytes in rows:
                plane._db.execute("DELETE FROM objects WHERE sha256=?", (digest,))
                moved_objects += 1
        if max_records:
            remaining -= len(rows)
            if remaining <= 0:
                break
    while True:
        limit = 1000 if not max_records else min(1000, remaining)
        if max_records and limit <= 0:
            break
        rows = list(plane._db.execute(
            "SELECT sha256,payload,generation,parent_sha256 FROM nodes LIMIT ?", (limit,)))
        if not rows:
            break
        with plane.transaction():
            pending = []
            for digest, raw, generation, parent in rows:
                if _sha(raw) != digest:
                    raise ValueError("BILQIS_DATA_PLANE_NODE_CORRUPTED:" + digest)
                compressed = zlib.compress(raw, level=6)
                if not plane._db.execute(
                        "SELECT 1 FROM archived_nodes WHERE sha256=?", (digest,)).fetchone():
                    pending.append((digest, len(raw), compressed, generation, parent))
            archived = plane._archive_append_many(
                "nodes", ((digest, raw_bytes, compressed)
                          for digest, raw_bytes, compressed, _generation, _parent in pending))
            metadata = {digest: (generation, parent)
                        for digest, _raw_bytes, _compressed, generation, parent in pending}
            for digest, pack_id, offset, raw_bytes, compressed_bytes in archived:
                generation, parent = metadata[digest]
                plane._db.execute(
                    "INSERT INTO archived_nodes(sha256,pack_id,pack_offset,raw_bytes,"
                    "compressed_bytes,generation,parent_sha256) VALUES(?,?,?,?,?,?,?)",
                    (digest, pack_id, offset, raw_bytes, compressed_bytes, generation, parent))
            for digest, _raw, _generation, _parent in rows:
                plane._db.execute("DELETE FROM nodes WHERE sha256=?", (digest,))
                moved_nodes += 1
        if max_records:
            remaining -= len(rows)
            if remaining <= 0:
                break
    return {"migrated_objects": moved_objects, "migrated_nodes": moved_nodes}


def vacuum(plane) -> None:
    with plane._lock:
        if plane._db.in_transaction:
            raise ValueError("BILQIS_DATA_PLANE_VACUUM_TRANSACTION_ACTIVE")
        plane._db.execute("VACUUM")
