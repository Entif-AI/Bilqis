"""Heavyweight BAMF file-object retention and garbage collection."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .contracts import DataPlaneError, _error
from .file_objects import _OWNER_KEY_PREFIX


def _valid_digest(value) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def _digests(value, found: set[str]) -> None:
    if _valid_digest(value):
        found.add(value)
    elif isinstance(value, dict):
        for child in value.values():
            _digests(child, found)
    elif isinstance(value, list):
        for child in value:
            _digests(child, found)


def _json_digests(raw: bytes) -> set[str]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return set()
    found: set[str] = set()
    _digests(value, found)
    return found


def file_inventory(plane) -> dict[str, tuple[Path, int]]:
    root = plane.path.with_name(plane.path.name + ".objects")
    result = {}
    if not root.is_dir():
        return result
    for path in root.glob("*/*.safetensors"):
        digest = path.stem
        if _valid_digest(digest) and path.is_file() and not path.is_symlink():
            result[digest] = (path, path.stat().st_size)
    return result


def _bamf_file_reachability(plane, scan_roots) -> tuple[set[str], dict[str, int]]:
    file_ids = set(file_inventory(plane))
    reachable: set[str] = set()
    tiers = {"bamf_current": 0, "bamf_ancestry": 0, "pinned": 0}
    for root in (Path(value).expanduser().resolve() for value in scan_roots):
        pointer_path = root / "bamf-state.json"
        if not pointer_path.is_file():
            continue
        try:
            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError(DataPlaneError.BAMF_POINTER_INVALID.value) from None
        current = pointer.get("manifest_sha256")
        bundle = pointer.get("bundle")
        canonical_bundle = f"bamf-bundles/{current}" if _valid_digest(current) else None
        if (not _valid_digest(current) or not isinstance(bundle, str)
                or bundle != canonical_bundle):
            raise ValueError(DataPlaneError.BAMF_POINTER_INVALID.value)
        digest = current
        first = True
        while _valid_digest(digest):
            manifest_path = root / "bamf-bundles" / digest / "manifest.json"
            if not manifest_path.is_file() or manifest_path.is_symlink():
                raise ValueError(_error(DataPlaneError.BAMF_MANIFEST_MISSING, digest))
            raw = manifest_path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError(_error(DataPlaneError.BAMF_MANIFEST_DRIFT, digest))
            try:
                manifest = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ValueError(_error(DataPlaneError.BAMF_MANIFEST_INVALID, digest)) from None
            found: set[str] = set()
            _digests(manifest, found)
            reachable.update(found & file_ids)
            sidecars = manifest.get("sidecars") if isinstance(manifest, dict) else None
            if isinstance(sidecars, dict):
                for binding in sidecars.values():
                    if not isinstance(binding, dict) or not isinstance(binding.get("filename"), str):
                        continue
                    filename = binding["filename"]
                    if Path(filename).name != filename:
                        raise ValueError(_error(
                            DataPlaneError.BAMF_SIDECAR_PATH_INVALID, digest))
                    sidecar_path = manifest_path.parent / filename
                    if not sidecar_path.is_file() or sidecar_path.is_symlink():
                        raise ValueError(_error(
                            DataPlaneError.BAMF_SIDECAR_MISSING, digest))
                    sidecar_raw = sidecar_path.read_bytes()
                    expected = binding.get("sha256")
                    if _valid_digest(expected) and hashlib.sha256(sidecar_raw).hexdigest() != expected:
                        raise ValueError(_error(
                            DataPlaneError.BAMF_SIDECAR_DRIFT, digest))
                    reachable.update(_json_digests(sidecar_raw) & file_ids)
            tiers["bamf_current" if first else "bamf_ancestry"] += 1
            parent = manifest.get("parent_manifest_sha256") if isinstance(manifest, dict) else None
            if not _valid_digest(parent):
                break
            digest = parent
            first = False
    for _key, object_digest in plane._db.execute(
            "SELECT key,value FROM meta WHERE key LIKE 'object_reference_v1:%'"):
        if not _valid_digest(object_digest):
            continue
        try:
            raw = plane.get_object(object_digest)
        except ValueError:
            raise ValueError(_error(
                DataPlaneError.NAMED_REFERENCE_MISSING, object_digest)) from None
        referenced = _json_digests(raw) & file_ids
        if referenced:
            reachable.update(referenced)
            tiers["named_reference"] = tiers.get("named_reference", 0) + 1
    for kind, digest in plane._db.execute("SELECT kind,sha256 FROM retention_pins"):
        if kind == "file" and digest in file_ids:
            reachable.add(digest)
            tiers["pinned"] += 1
    return reachable, tiers


def file_gc_report(plane, scan_roots, *, apply: bool = False) -> dict:
    """Collect only heavyweight file objects from a bounded custody root set."""
    reachable, tiers = _bamf_file_reachability(plane, scan_roots)
    files = file_inventory(plane)
    dead_files = set(files) - reachable
    report = {
        "reachable_file_objects": len(reachable),
        "unreachable_file_objects": len(dead_files),
        "reclaimable_file_bytes": sum(files[digest][1] for digest in dead_files),
        "root_tiers": tiers,
        "applied": apply,
    }
    if not apply:
        return report
    with plane.transaction():
        for digest in dead_files:
            plane._db.execute("DELETE FROM meta WHERE key=?", (_OWNER_KEY_PREFIX + digest,))
            plane._db.execute(
                "DELETE FROM verified_files WHERE path=?",
                (str(files[digest][0].resolve()),),
            )
    for digest in dead_files:
        path = files[digest][0]
        if path.exists() and not path.is_symlink():
            path.unlink()
    return report
