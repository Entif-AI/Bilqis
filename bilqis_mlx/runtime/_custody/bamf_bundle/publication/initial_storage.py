"""Generation-zero filesystem classification and acceptance records."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from bilqis_mlx.data_plane import DataPlaneError
from ..records import canonical, invalid
from .storage import ACCEPTANCE_DIR, _fsync_directory
from .instrumentation import note_fsync, note_write


def _classify_initial_generation_target(run_dir: Path) -> str:
    """Classify only the target shapes relevant to fresh gen0 publication/recovery."""
    run_dir = Path(run_dir)
    if not run_dir.exists() and not run_dir.is_symlink():
        return "empty"
    if run_dir.is_symlink() or not run_dir.is_dir():
        invalid(DataPlaneError.BUNDLE_ROOT_UNSAFE)
    entries = {path.name: path for path in run_dir.iterdir()}
    if not entries:
        return "empty"

    lock = entries.get(".bamf-pointer.lock")
    stage = entries.get(".bamf-staging")
    factory_releases = entries.get("factory-releases")
    if lock is not None:
        if lock.is_symlink() or not lock.is_file():
            invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    if stage is not None:
        if stage.is_symlink() or not stage.is_dir():
            invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
        if any(stage.iterdir()):
            invalid("BAMF_FIRST_STUDENT_PRESEAL_STAGING_RESIDUE")
    if factory_releases is not None:
        if factory_releases.is_symlink() or not factory_releases.is_dir():
            invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)

    if lock is None:
        if stage is not None:
            invalid("BAMF_FIRST_STUDENT_PRESEAL_STAGING_RESIDUE")
        return "occupied"

    names = set(entries)
    if names == {".bamf-pointer.lock"}:
        return "lock-only"
    if names == {".bamf-pointer.lock", ".bamf-staging"}:
        return "lock-stage"

    allowed_recovery = {
        ".bamf-pointer.lock", ".bamf-staging",
        "bamf-bundles", "bamf-acceptance", "factory-releases",
    }
    if not names <= allowed_recovery:
        invalid("BAMF_FIRST_STUDENT_PRESEAL_STAGING_RESIDUE")
    if "bamf-bundles" not in names:
        invalid("BAMF_FIRST_STUDENT_PRESEAL_STAGING_RESIDUE")
    return "recovery"


def _validate_initial_generation_lifecycle_markers(run_dir: Path) -> None:
    """Validate marker shapes for read-only pointerless-resume interception."""
    run_dir = Path(run_dir)
    lock = run_dir / ".bamf-pointer.lock"
    stage = run_dir / ".bamf-staging"
    if lock.exists() or lock.is_symlink():
        if lock.is_symlink() or not lock.is_file():
            invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    if stage.exists() or stage.is_symlink():
        if stage.is_symlink() or not stage.is_dir():
            invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)


def _reclaim_empty_initial_staging_root(run_dir: Path) -> None:
    """Remove only the exact empty pre-seal staging root and durably retain the run root."""
    run_dir = Path(run_dir)
    stage = run_dir / ".bamf-staging"
    if stage.is_symlink() or not stage.is_dir() or any(stage.iterdir()):
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    stage.rmdir()
    _fsync_directory(run_dir)


def _acceptance_path(run_dir: Path, manifest_sha256: str) -> Path:
    root = run_dir / ACCEPTANCE_DIR
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    existed = root.exists()
    root.mkdir(exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    if not existed:
        _fsync_directory(root)
        _fsync_directory(run_dir)
    return root / f"{manifest_sha256}.json"


def _write_acceptance_record(run_dir: Path, manifest_sha256: str,
                             record: dict) -> None:
    path = _acceptance_path(run_dir, manifest_sha256)
    raw = canonical(record)
    if path.is_symlink():
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    if path.exists():
        if not path.is_file() or path.read_bytes() != raw:
            invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
        _fsync_directory(path.parent)
        return
    fd, temporary = tempfile.mkstemp(prefix=".bamf-acceptance-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            note_write(len(raw))
            stream.flush()
            os.fsync(stream.fileno())
            note_fsync(len(raw))
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_acceptance(run_dir: Path, manifest_sha256: str,
                      acceptance) -> None:
    _write_acceptance_record(
        run_dir, manifest_sha256, acceptance.to_record())


def _write_parsed_initial_generation_acceptance(
        run_dir: Path, manifest_sha256: str, binding, *,
        expected_acceptance_sha256: str) -> None:
    """Restore only already-authenticated historical generation-zero evidence."""
    from ..genesis.records import ParsedInitialGenerationBinding

    if (type(binding) is not ParsedInitialGenerationBinding
            or binding.digest != expected_acceptance_sha256):
        invalid("BAMF_INITIAL_GENERATION_BINDING_INVALID")
    _write_acceptance_record(run_dir, manifest_sha256, {
        **binding.fields,
        "binding_sha256": binding.digest,
    })
