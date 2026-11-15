"""Pointer serialization and authenticated live-bundle reads."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from bilqis_mlx.data_plane import DataPlaneError, SHA256_HEX_LENGTH
from ..codec import validate_bamf_bundle_custody
from ..records import BAMF_BUNDLE_SCHEMA, BAMF_POINTER_SCHEMA, LEGACY_BAMF_POINTER_SCHEMA, canonical, invalid
from .storage import _fsync_directory, _require_bundle_root


def _read_pointer(path: Path) -> dict | None:
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file():
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    try:
        pointer = json.loads(path.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError):
        invalid()
    bundle_value = pointer.get("bundle") if isinstance(pointer, dict) else None
    bundle = Path(bundle_value) if isinstance(bundle_value, str) else Path()
    base_fields = {"schema", "run_id", "generation",
                   "parent_manifest_sha256", "bundle", "manifest_sha256"}
    schema = pointer.get("schema") if isinstance(pointer, dict) else None
    expected = (base_fields | {"acceptance_sha256"}
                if schema == BAMF_POINTER_SCHEMA else base_fields)
    if (not isinstance(pointer, dict) or set(pointer) != expected
            or schema not in {BAMF_POINTER_SCHEMA, LEGACY_BAMF_POINTER_SCHEMA}
            or (schema == BAMF_POINTER_SCHEMA
                and (not isinstance(pointer.get("acceptance_sha256"), str)
                     or len(pointer["acceptance_sha256"]) != SHA256_HEX_LENGTH
                     or any(c not in "0123456789abcdef"
                            for c in pointer["acceptance_sha256"])))
            or not isinstance(pointer.get("run_id"), str) or not pointer["run_id"]
            or type(pointer.get("generation")) is not int or bundle.is_absolute()
            or bundle_value != f"bamf-bundles/{pointer.get('manifest_sha256')}"
            or tuple(bundle.parts) != ("bamf-bundles", pointer.get("manifest_sha256"))
            or any(part in ("", ".", "..") for part in bundle.parts)):
        invalid()
    return pointer


def _live_bundle_manifest(run_dir: Path, pointer: dict) -> dict:
    root = _require_bundle_root(run_dir, create=False)
    bundle = root / pointer["manifest_sha256"]
    manifest = validate_bamf_bundle_custody(
        bundle, expected_manifest_sha256=pointer["manifest_sha256"])
    if (manifest["run_id"] != pointer["run_id"]
            or manifest["generation"] != pointer["generation"]
            or manifest["parent_manifest_sha256"] != pointer["parent_manifest_sha256"]):
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    return manifest


def _atomic_pointer(path: Path, pointer: dict) -> None:
    if path.is_symlink():
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    raw = canonical(pointer)
    fd, temporary = tempfile.mkstemp(prefix=".bamf-pointer-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
