"""Run custody discovery and immutable bundle deduplication."""
from __future__ import annotations
import os
from pathlib import Path
from .contracts import MIN_DEDUPE_GROUP_SIZE, MIN_OPTIMIZER_STEP, SHA256_HEX_LENGTH, DataPlaneError, _error

def verify_file_digest(*args, **kwargs):
    import bilqis_mlx.data_plane as facade
    return facade.verify_file_digest(*args, **kwargs)

def live_grade_soups(receipt: dict) -> dict:
    """Return the only soup tensors that still carry live runtime custody."""
    epoch = receipt.get("mentor_epoch")
    if epoch is None:
        soups = receipt.get("grade_soups", {})
    elif isinstance(epoch, dict):
        soups = epoch.get("active_grade_soups", {})
    else:
        raise ValueError(DataPlaneError.SOUP_CUSTODY_MAP_DRIFT.value)
    if not isinstance(soups, dict):
        raise ValueError(DataPlaneError.SOUP_CUSTODY_MAP_DRIFT.value)
    return soups

def referenced_custody_files(run_dir: Path, receipt: dict) -> tuple[tuple[Path, str], ...]:
    """Resolve immutable bundle/soup payloads named by one logical school receipt."""
    root = Path(run_dir).resolve(strict=True)
    found: dict[str, tuple[Path, str]] = {}

    def visit(value, *, include_soups: bool) -> None:
        if isinstance(value, dict):
            filename = value.get("filename")
            digest = value.get("sha256")
            if isinstance(filename, str) and isinstance(digest, str) and len(digest) == SHA256_HEX_LENGTH:
                relative = Path(filename)
                if relative.parts and relative.parts[0] == "bundles":
                    target = root / relative / "model-and-own-adamw.safetensors"
                    found[str(target)] = (target, digest)
                elif (include_soups and relative.parts and
                      relative.parts[0] == "soups"):
                    target = root / relative
                    found[str(target)] = (target, digest)
            for member in value.values():
                visit(member, include_soups=include_soups)
        elif isinstance(value, (list, tuple)):
            for member in value:
                visit(member, include_soups=include_soups)

    # Bundle custody can legitimately be rooted by archival provenance, but
    # superseded soup tensors obey the bounded active+rollback retention rule.
    visit(receipt, include_soups=False)
    visit(live_grade_soups(receipt), include_soups=True)
    return tuple(found[key] for key in sorted(found))

def dedupe_bundle_payloads(run_dir: Path) -> dict:
    """Hardlink byte-identical immutable bundle payload aliases in one run."""
    import json
    root = Path(run_dir).resolve(strict=True)
    bundles = root / "bundles"
    if bundles.is_symlink() or not bundles.is_dir():
        raise ValueError(DataPlaneError.BUNDLE_ROOT_UNSAFE.value)
    groups: dict[str, list[Path]] = {}
    optimizer_step_by_digest: dict[str, int] = {}
    for folder in sorted(bundles.iterdir()):
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError(_error(DataPlaneError.BUNDLE_ENTRY_UNSAFE, folder))
        manifest_path = folder / "manifest.json"
        payload = folder / "model-and-own-adamw.safetensors"
        if (manifest_path.is_symlink() or payload.is_symlink() or
                not manifest_path.is_file() or not payload.is_file()):
            raise ValueError(_error(DataPlaneError.BUNDLE_ENTRY_UNSAFE, folder))
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(_error(DataPlaneError.BUNDLE_MANIFEST_INVALID, folder)) from exc
        digest = manifest.get("safetensors_sha256")
        step = manifest.get("optimizer_step")
        if (not isinstance(digest, str) or len(digest) != SHA256_HEX_LENGTH or
                type(step) is not int or step < MIN_OPTIMIZER_STEP):
            raise ValueError(_error(DataPlaneError.BUNDLE_MANIFEST_INVALID, folder))
        prior_step = optimizer_step_by_digest.setdefault(digest, step)
        if prior_step != step:
            raise ValueError(_error(DataPlaneError.BUNDLE_IDENTITY_CONFLICT, digest))
        if not verify_file_digest(payload, digest):
            raise ValueError(_error(DataPlaneError.BUNDLE_PAYLOAD_DRIFT, folder))
        groups.setdefault(digest, []).append(payload)

    linked = reclaimed = 0
    for paths in groups.values():
        if len(paths) < MIN_DEDUPE_GROUP_SIZE:
            continue
        canonical = paths[0]
        canonical_identity = (canonical.stat().st_dev, canonical.stat().st_ino)
        for target in paths[1:]:
            stat = target.stat()
            if (stat.st_dev, stat.st_ino) == canonical_identity:
                continue
            temporary = target.with_name("." + target.name + ".dedupe-link")
            if temporary.exists() or temporary.is_symlink():
                raise ValueError(_error(DataPlaneError.BUNDLE_DEDUPE_TEMP_COLLISION,
                                        temporary))
            os.link(canonical, temporary)
            try:
                os.replace(temporary, target)
                directory = os.open(target.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            finally:
                if temporary.exists() or temporary.is_symlink():
                    temporary.unlink()
            linked += 1
            reclaimed += stat.st_size
    return {
        "mode": "BUNDLE_PAYLOADS_DEDUPED",
        "bundle_payloads": sum(len(paths) for paths in groups.values()),
        "unique_payloads": len(groups),
        "linked_aliases": linked,
        "reclaimed_bytes": reclaimed,
    }
