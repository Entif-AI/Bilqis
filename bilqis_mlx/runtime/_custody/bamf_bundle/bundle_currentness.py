"""Process-live B13 currentness proof after one full accepted-bundle custody check."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from bilqis_mlx.data_plane import DataPlaneError, data_plane

from .codec import validate_bamf_bundle_custody
from .records import invalid


_ISSUER = object()


def _stat_identity(path: Path) -> tuple[int, int, int, int, int]:
    info = path.stat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _tree_snapshot(root: Path) -> tuple:
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        invalid(DataPlaneError.BUNDLE_ROOT_UNSAFE)
    root = root.resolve()
    values = [(".", "dir", *_stat_identity(root))]
    try:
        for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
            if path.is_symlink():
                invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
            kind = "dir" if path.is_dir() else "file" if path.is_file() else "other"
            if kind == "other":
                invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
            values.append((path.relative_to(root).as_posix(), kind, *_stat_identity(path)))
    except OSError:
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    return tuple(values)


def _require_bound_tree(root: Path, snapshot: tuple) -> None:
    """Re-stat the already discovered tree without another recursive walk."""
    try:
        for relative, kind, *expected in snapshot:
            path = root if relative == "." else root / relative
            if path.is_symlink():
                invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
            actual_kind = "dir" if path.is_dir() else "file" if path.is_file() else "other"
            if actual_kind != kind or tuple(expected) != _stat_identity(path):
                invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    except OSError:
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)


def _external_objects(manifest: dict) -> tuple[tuple[str, ...], str | None]:
    sidecars = manifest.get("sidecars", {})
    sidecar_objects = tuple(sorted(
        binding["object_sha256"] for binding in sidecars.values()
    ))
    tensor = manifest.get("tensors", {})
    tensor_object = tensor.get("object_sha256")
    return sidecar_objects, tensor_object


@dataclass(frozen=True, init=False, eq=False)
class BamfBundleCurrentness:
    """Non-serializable B13 proof tied to one deeply validated bundle state."""

    manifest_sha256: str
    _root: Path = field(repr=False)
    _tree: tuple = field(repr=False)
    _sidecar_objects: tuple[str, ...] = field(repr=False)
    _tensor_object: str | None = field(repr=False)
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)


def _require_external_objects(witness: BamfBundleCurrentness) -> None:
    plane = data_plane()
    try:
        plane.get_node(witness.manifest_sha256)
        for digest in witness._sidecar_objects:
            plane.get_object(digest)
        if witness._tensor_object is not None:
            plane.require_file_object(witness._tensor_object)
    except (OSError, ValueError):
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)


def bind_bamf_bundle_currentness(
    root: Path, *, expected_manifest_sha256: str,
) -> BamfBundleCurrentness:
    """Deep-validate once, then issue the exact cheaper B13 currentness witness."""
    root = Path(root)
    if root.is_symlink():
        invalid(DataPlaneError.BUNDLE_ROOT_UNSAFE)
    root = root.resolve()
    before = _tree_snapshot(root)
    manifest = validate_bamf_bundle_custody(
        root, expected_manifest_sha256=expected_manifest_sha256)
    after = _tree_snapshot(root)
    if before != after:
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    sidecar_objects, tensor_object = _external_objects(manifest)
    result = object.__new__(BamfBundleCurrentness)
    for name, value in (
        ("manifest_sha256", expected_manifest_sha256),
        ("_root", root),
        ("_tree", after),
        ("_sidecar_objects", sidecar_objects),
        ("_tensor_object", tensor_object),
        ("_issuance", _ISSUER),
    ):
        object.__setattr__(result, name, value)
    _require_external_objects(result)
    return result


def require_bamf_bundle_currentness(witness) -> BamfBundleCurrentness:
    """Reject local drift without repeating discovery or content verification."""
    if (type(witness) is not BamfBundleCurrentness
            or getattr(witness, "_issuance", None) is not _ISSUER):
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    _require_bound_tree(witness._root, witness._tree)
    _require_external_objects(witness)
    return witness


__all__ = (
    "BamfBundleCurrentness",
    "bind_bamf_bundle_currentness",
    "require_bamf_bundle_currentness",
)
