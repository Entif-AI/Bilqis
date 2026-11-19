"""Shared data-plane constants, errors, and event parsing."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sys
from enum import Enum

SCHEMA_VERSION = 2
LEGACY_SCHEMA_VERSION = 1
SQLITE_BUSY_TIMEOUT_MS = 30_000
SQLITE_MMAP_BYTES = 256 * 1024 * 1024
SQLITE_CACHE_KIB = 64 * 1024
HASH_CHUNK_BYTES = 4 * 1024 * 1024
SHA256_HEX_LENGTH = hashlib.sha256().digest_size * 2
MIN_OPTIMIZER_STEP = 0
MIN_DEDUPE_GROUP_SIZE = 2

class DataPlaneError(str, Enum):
    SCHEMA_UNSUPPORTED = "BILQIS_DATA_PLANE_SCHEMA_UNSUPPORTED"
    OBJECT_DIGEST_INVALID = "BILQIS_DATA_PLANE_OBJECT_DIGEST_INVALID"
    OBJECT_MISSING = "BILQIS_DATA_PLANE_OBJECT_MISSING"
    OBJECT_CORRUPTED = "BILQIS_DATA_PLANE_OBJECT_CORRUPTED"
    NODE_DIGEST_INVALID = "BILQIS_DATA_PLANE_NODE_DIGEST_INVALID"
    NODE_MISSING = "BILQIS_DATA_PLANE_NODE_MISSING"
    NODE_CORRUPTED = "BILQIS_DATA_PLANE_NODE_CORRUPTED"
    ARCHIVE_TRUNCATED = "BILQIS_DATA_PLANE_ARCHIVE_TRUNCATED"
    ARCHIVE_HEADER_DRIFT = "BILQIS_DATA_PLANE_ARCHIVE_HEADER_DRIFT"
    ARCHIVE_CONTENT_DRIFT = "BILQIS_DATA_PLANE_ARCHIVE_CONTENT_DRIFT"
    ARCHIVE_KIND_INVALID = "BILQIS_DATA_PLANE_ARCHIVE_KIND_INVALID"
    BAMF_POINTER_INVALID = "BILQIS_DATA_PLANE_BAMF_POINTER_INVALID"
    BAMF_MANIFEST_MISSING = "BILQIS_DATA_PLANE_BAMF_MANIFEST_MISSING"
    BAMF_MANIFEST_DRIFT = "BILQIS_DATA_PLANE_BAMF_MANIFEST_DRIFT"
    BAMF_MANIFEST_INVALID = "BILQIS_DATA_PLANE_BAMF_MANIFEST_INVALID"
    BAMF_SIDECAR_PATH_INVALID = "BILQIS_DATA_PLANE_BAMF_SIDECAR_PATH_INVALID"
    BAMF_SIDECAR_MISSING = "BILQIS_DATA_PLANE_BAMF_SIDECAR_MISSING"
    BAMF_SIDECAR_DRIFT = "BILQIS_DATA_PLANE_BAMF_SIDECAR_DRIFT"
    NAMED_REFERENCE_MISSING = "BILQIS_DATA_PLANE_NAMED_REFERENCE_MISSING"
    STATE_POINTER_INVALID = "BILQIS_DATA_PLANE_STATE_POINTER_INVALID"
    RETENTION_PIN_INVALID = "BILQIS_DATA_PLANE_RETENTION_PIN_INVALID"
    RETENTION_TIER_INVALID = "BILQIS_DATA_PLANE_RETENTION_TIER_INVALID"
    MIGRATION_BUDGET_INVALID = "BILQIS_DATA_PLANE_MIGRATION_BUDGET_INVALID"
    VACUUM_TRANSACTION_ACTIVE = "BILQIS_DATA_PLANE_VACUUM_TRANSACTION_ACTIVE"
    MAINTENANCE_ROOT_INVALID = "DATA_PLANE_MAINTENANCE_ROOT_INVALID"
    MAINTENANCE_ROOT_UNRECOGNIZED = "DATA_PLANE_MAINTENANCE_ROOT_UNRECOGNIZED"
    MAINTENANCE_SCAN_ROOT_REQUIRED = "DATA_PLANE_MAINTENANCE_SCAN_ROOT_REQUIRED"
    EXPECTED_DIGEST_INVALID = "BILQIS_DATA_PLANE_EXPECTED_DIGEST_INVALID"
    OPERATOR_LOCK_UNSAFE = "DATA_PLANE_OPERATOR_LOCK_UNSAFE"
    HUMAN_TRAINING_ACTIVE = "DATA_PLANE_WARM_HUMAN_TRAINING_ACTIVE"
    CUSTODY_ARTIFACT_MISSING = "DATA_PLANE_WARM_CUSTODY_ARTIFACT_MISSING"
    CUSTODY_DIGEST_DRIFT = "DATA_PLANE_WARM_CUSTODY_DIGEST_DRIFT"
    BUNDLE_ROOT_UNSAFE = "DATA_PLANE_BUNDLE_ROOT_UNSAFE"
    BUNDLE_ENTRY_UNSAFE = "DATA_PLANE_BUNDLE_ENTRY_UNSAFE"
    BUNDLE_MANIFEST_INVALID = "DATA_PLANE_BUNDLE_MANIFEST_INVALID"
    BUNDLE_PAYLOAD_DRIFT = "DATA_PLANE_BUNDLE_PAYLOAD_DRIFT"
    BUNDLE_IDENTITY_CONFLICT = "DATA_PLANE_BUNDLE_IDENTITY_CONFLICT"
    BUNDLE_DEDUPE_TEMP_COLLISION = "DATA_PLANE_BUNDLE_DEDUPE_TEMP_COLLISION"
    EVENT_LEDGER_UNSAFE = "DATA_PLANE_EVENT_LEDGER_UNSAFE"
    EVENT_LEDGER_TRUNCATED = "DATA_PLANE_EVENT_LEDGER_TRUNCATED"
    EVENT_LEDGER_JSON_INVALID = "DATA_PLANE_EVENT_LEDGER_JSON_INVALID"
    EVENT_CURSOR_INVALID = "DATA_PLANE_EVENT_CURSOR_INVALID"
    EVENT_PROJECTION_FRONTIER_DRIFT = "DATA_PLANE_EVENT_PROJECTION_FRONTIER_DRIFT"
    SOUP_CUSTODY_MAP_DRIFT = "GRADE_SOUP_CUSTODY_MAP_DRIFT"

def _error(code: DataPlaneError, detail=None) -> str:
    return code.value if detail is None else code.value + ":" + str(detail)

def event_payload_digest(event: dict) -> str:
    raw = json.dumps(event, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def _read_event_tail(ledger: Path, start: int) -> tuple[list[tuple], int]:
    observed = []
    with ledger.open("rb") as stream:
        stream.seek(start)
        while line := stream.readline():
            line_start = stream.tell() - len(line)
            if not line.endswith(b"\n"):
                raise ValueError(_error(DataPlaneError.EVENT_LEDGER_TRUNCATED, ledger))
            try:
                item = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(_error(
                    DataPlaneError.EVENT_LEDGER_JSON_INVALID, ledger)) from exc
            event_id = item.get("event_id") if isinstance(item, dict) else None
            digest = None
            if (isinstance(event_id, str)
                    and len(event_id) == SHA256_HEX_LENGTH):
                digest = event_payload_digest(item)
            payload = json.dumps(
                item, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False).encode("utf-8")
            observed.append((event_id, digest, line_start, stream.tell(), payload))
        return observed, stream.tell()

def default_path() -> Path:
    configured = os.environ.get("BILQIS_DATA_PLANE", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    home = Path.home()
    if sys.platform == "darwin":
        root = home / "Library" / "Application Support" / "Bilqis-MLX"
    elif os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local")) / "Bilqis-MLX"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share")) / "bilqis-mlx"
    return root / "data-plane.sqlite3"
