"""Shared workstation data plane for immutable state and integrity cache."""
from __future__ import annotations
import hashlib
from pathlib import Path
import threading

from ._data_plane.contracts import (
    SCHEMA_VERSION, SQLITE_BUSY_TIMEOUT_MS, SQLITE_MMAP_BYTES, SQLITE_CACHE_KIB,
    HASH_CHUNK_BYTES, SHA256_HEX_LENGTH, MIN_OPTIMIZER_STEP, MIN_DEDUPE_GROUP_SIZE,
    DataPlaneError, _error, _read_event_tail, default_path, event_payload_digest,
)
from ._data_plane.store import DataPlaneStoreMixin
from ._data_plane.events import DataPlaneEventMixin
from ._data_plane.file_objects import DataPlaneFileObjectMixin
from ._data_plane.archive import DataPlaneArchiveMixin
from ._data_plane.cache import DataPlaneCacheMixin

_CONNECTIONS: dict[str, "DataPlane"] = dict()
_CONNECTIONS_LOCK = threading.Lock()

class DataPlane(DataPlaneStoreMixin, DataPlaneEventMixin, DataPlaneFileObjectMixin,
                DataPlaneArchiveMixin, DataPlaneCacheMixin):
    pass

def data_plane() -> DataPlane:
    path = str(default_path())
    with _CONNECTIONS_LOCK:
        plane = _CONNECTIONS.get(path)
        if plane is None:
            plane = DataPlane(Path(path))
            _CONNECTIONS[path] = plane
        return plane

def close_data_planes() -> None:
    with _CONNECTIONS_LOCK:
        values = list(_CONNECTIONS.values())
        _CONNECTIONS.clear()
    for plane in values:
        plane.close()

def _digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(HASH_CHUNK_BYTES):
            h.update(chunk)
    return h.hexdigest()

def verify_file_digest(path: Path, expected_sha256: str, *, deep: bool = False) -> bool:
    """Verify immutable file content, reusing a workstation-local stat-bound proof."""
    if not isinstance(expected_sha256, str) or len(expected_sha256) != SHA256_HEX_LENGTH:
        raise ValueError(DataPlaneError.EXPECTED_DIGEST_INVALID.value)
    plane = data_plane()
    path = Path(path)
    if not deep and plane.verified_file(path, expected_sha256):
        return True
    actual = _digest_file(path)
    if actual != expected_sha256:
        return False
    plane.remember_verified_file(path, expected_sha256)
    return True

def sync_event_ledger(run_dir: Path) -> dict:
    return data_plane().sync_event_ledger(run_dir)

def event_observations(run_dir: Path, event_ids) -> dict:
    return data_plane().event_observations(run_dir, event_ids)

def indexed_event_tail(run_dir: Path, after_byte: int = 0) -> dict:
    return data_plane().indexed_event_tail(run_dir, after_byte)

def event_projection_state(run_dir: Path, projection_key: str, schema_version: str):
    return data_plane().event_projection_state(run_dir, projection_key, schema_version)

def remember_event_projection(run_dir: Path, projection_key: str, schema_version: str,
                              ledger_identity, indexed_bytes: int, payload: dict) -> None:
    data_plane().remember_event_projection(
        run_dir, projection_key, schema_version, ledger_identity, indexed_bytes, payload)

from ._data_plane.custody import live_grade_soups, referenced_custody_files, dedupe_bundle_payloads
from ._data_plane.cli import main

_PUBLIC_MODULE = "bilqis_mlx.data_plane"
for _public_object in (DataPlaneError, default_path, event_payload_digest,
                       live_grade_soups, referenced_custody_files,
                       dedupe_bundle_payloads, main):
    _public_object.__module__ = _PUBLIC_MODULE
del _public_object

if __name__ == "__main__":
    raise SystemExit(main())
