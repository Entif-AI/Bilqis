"""Private crash-safe filesystem primitives for BAMF generation publication."""
from __future__ import annotations

import contextlib
import fcntl
import os
import shutil
import stat
import uuid
from pathlib import Path

from bilqis_mlx.data_plane import DataPlaneError
from ..records import invalid

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


from .pointer_storage import (
    _atomic_pointer, _live_bundle_manifest, _read_pointer,
)


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


from .initial_storage import (
    _acceptance_path, _classify_initial_generation_target,
    _reclaim_empty_initial_staging_root,
    _validate_initial_generation_lifecycle_markers,
    _write_acceptance, _write_acceptance_record,
    _write_parsed_initial_generation_acceptance,
)
