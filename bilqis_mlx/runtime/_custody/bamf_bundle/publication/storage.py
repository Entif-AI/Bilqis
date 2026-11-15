"""Private crash-safe filesystem primitives for BAMF generation publication."""
from __future__ import annotations

import contextlib
import fcntl
import json
import os
import shutil
import stat
import tempfile
import uuid
from pathlib import Path

from bilqis_mlx.data_plane import DataPlaneError, SHA256_HEX_LENGTH
from ..codec import validate_bamf_bundle_custody
from ..records import (
    BAMF_BUNDLE_SCHEMA, BAMF_POINTER_SCHEMA, LEGACY_BAMF_POINTER_SCHEMA,
    canonical, invalid,
)

ACCEPTANCE_DIR = "bamf-acceptance"


def _fsync_directory(path: Path) -> None:
    directory = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _require_run_root(run_dir: Path) -> None:
    if run_dir.is_symlink() or (run_dir.exists() and not run_dir.is_dir()):
        invalid(DataPlaneError.BUNDLE_ROOT_UNSAFE)
    created: list[Path] = []
    ancestor = run_dir
    while not ancestor.exists():
        created.append(ancestor)
        ancestor = ancestor.parent
    run_dir.mkdir(parents=True, exist_ok=True)
    if run_dir.is_symlink() or not run_dir.is_dir():
        invalid(DataPlaneError.BUNDLE_ROOT_UNSAFE)
    if created:
        for directory in created:
            _fsync_directory(directory)
        _fsync_directory(ancestor)


def _require_existing_run_root(run_dir: Path) -> None:
    if run_dir.is_symlink() or not run_dir.is_dir():
        invalid(DataPlaneError.BUNDLE_ROOT_UNSAFE)


def _require_bundle_root(run_dir: Path, *, create: bool) -> Path:
    root = run_dir / "bamf-bundles"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    existed = root.exists()
    if create:
        root.mkdir(exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    if create and not existed:
        _fsync_directory(root)
        _fsync_directory(run_dir)
    return root


@contextlib.contextmanager
def _pointer_lock(run_dir: Path, *, create: bool = False):
    run_dir = Path(run_dir)
    if create:
        _require_run_root(run_dir)
    else:
        _require_existing_run_root(run_dir)
    lock = run_dir / ".bamf-pointer.lock"
    if lock.is_symlink():
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if create:
        try:
            fd = os.open(
                lock, os.O_RDWR | os.O_CREAT | os.O_EXCL | nofollow, 0o600)
        except FileExistsError:
            try:
                fd = os.open(lock, os.O_RDWR | nofollow)
            except OSError:
                invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
        except OSError:
            invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    else:
        try:
            fd = os.open(lock, os.O_RDWR | nofollow)
        except OSError:
            invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    locked = False
    primary_error = None
    try:
        opened = os.fstat(fd)
        try:
            named = os.stat(lock, follow_symlinks=False)
        except OSError:
            invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
        if (not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(named.st_mode)
                or (opened.st_dev, opened.st_ino) != (named.st_dev, named.st_ino)):
            invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            invalid("BAMF_POINTER_WRITER_ACTIVE")
        locked = True
        os.fsync(fd)
        _fsync_directory(run_dir)
        try:
            yield
        except BaseException as error:
            primary_error = error
            raise
    except BaseException as error:
        if primary_error is None:
            primary_error = error
        raise
    finally:
        cleanup_error = None
        if locked:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError as error:
                cleanup_error = error
        try:
            os.close(fd)
        except OSError as error:
            if cleanup_error is None:
                cleanup_error = error
        if cleanup_error is not None:
            if primary_error is not None:
                primary_error.add_note(
                    "BAMF_POINTER_LOCK_RELEASE_FAILED:" + cleanup_error.__class__.__name__)
            else:
                raise cleanup_error


def _initial_generation_pointer_lock(run_dir: Path):
    """Generation-zero-only capability for first creation of the persistent lock."""
    return _pointer_lock(run_dir, create=True)


@contextlib.contextmanager
def _publication_pointer_lock(run_dir: Path):
    """Writer lock with one authenticated migration path for pre-lock v2 runs."""
    run_dir = Path(run_dir)
    lock = run_dir / ".bamf-pointer.lock"
    if lock.exists() or lock.is_symlink():
        with _pointer_lock(run_dir):
            yield
        return

    pointer_path = run_dir / "bamf-state.json"
    prior = _read_pointer(pointer_path)
    if prior is None:
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    manifest = _live_bundle_manifest(run_dir, prior)
    if manifest.get("schema") != BAMF_BUNDLE_SCHEMA:
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)

    with _pointer_lock(run_dir, create=True):
        current = _read_pointer(pointer_path)
        if current != prior:
            invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
        current_manifest = _live_bundle_manifest(run_dir, current)
        if current_manifest.get("schema") != BAMF_BUNDLE_SCHEMA:
            invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
        yield


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


def _stage(run_dir: Path) -> Path:
    _require_run_root(run_dir)
    root = run_dir / ".bamf-staging"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    existed = root.exists()
    root.mkdir(exist_ok=True)
    if not existed:
        _fsync_directory(root)
        _fsync_directory(run_dir)
    return root / ("generation-" + uuid.uuid4().hex)


def _remove_stage(stage: Path) -> None:
    """Remove one generation stage and durably retain the staging root."""
    stage = Path(stage)
    if stage.is_symlink():
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    if stage.exists():
        if not stage.is_dir():
            invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
        shutil.rmtree(stage)
        _fsync_directory(stage.parent)


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
            stream.flush()
            os.fsync(stream.fileno())
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
