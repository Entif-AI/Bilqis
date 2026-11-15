"""Directory-fd anchored projection I/O for C05 fixed-school custody."""
from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
import stat
import uuid

from bilqis_mlx.runtime.capability_evaluation import _invalid


def _open_root(run_dir: Path) -> tuple[int, tuple[int, int]]:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = None
    try:
        # Canonicalize the already-accepted path once (macOS commonly exposes
        # /var through /private/var), then walk every canonical component by fd.
        # The fd is retained for the whole C05 operation; later path swaps are
        # detected by _require_same_root and cannot redirect child I/O.
        absolute = Path(os.path.realpath(os.fspath(run_dir)))
        fd = os.open(os.sep, flags)
        for component in absolute.parts[1:]:
            next_fd = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        info = os.fstat(fd)
    except OSError:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        _invalid("BAMF_C05_FIXED_SCHOOL_RUN_ROOT_UNSAFE")
        raise AssertionError
    if not stat.S_ISDIR(info.st_mode):
        os.close(fd)
        _invalid("BAMF_C05_FIXED_SCHOOL_RUN_ROOT_UNSAFE")
    return fd, (info.st_dev, info.st_ino)


def _require_same_root(run_dir: Path, identity: tuple[int, int]) -> None:
    fd = None
    try:
        fd, current = _open_root(run_dir)
    except Exception:
        _invalid("BAMF_C05_FIXED_SCHOOL_RUN_ROOT_DRIFT")
        return
    finally:
        if fd is not None:
            os.close(fd)
    if current != identity:
        _invalid("BAMF_C05_FIXED_SCHOOL_RUN_ROOT_DRIFT")


@contextlib.contextmanager
def fixed_school_root(run_dir: Path):
    """Hold the accepted run root open across auth, projection, and reauth."""
    fd, identity = _open_root(run_dir)
    try:
        yield fd, identity
        _require_same_root(run_dir, identity)
    finally:
        os.close(fd)


def _open_child_dir(root_fd: int, name: str) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        try:
            os.mkdir(name, mode=0o700, dir_fd=root_fd)
        except FileExistsError:
            pass
        fd = os.open(name, flags, dir_fd=root_fd)
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError
        return fd
    except OSError:
        _invalid("BAMF_C05_FIXED_SCHOOL_PROJECTION_UNSAFE")
        raise AssertionError


def project_bytes(root_fd: int, directory: str, filename: str, raw: bytes) -> None:
    """Atomically materialize trusted bytes without following path swaps."""
    child_fd = None
    tmp = f".{filename}.{uuid.uuid4().hex}.tmp"
    try:
        child_fd = _open_child_dir(root_fd, directory)
        fd = os.open(
            tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600, dir_fd=child_fd)
        try:
            view = memoryview(raw)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
        os.rename(tmp, filename, src_dir_fd=child_fd, dst_dir_fd=child_fd)
        os.fsync(child_fd)
    except OSError:
        _invalid("BAMF_C05_FIXED_SCHOOL_PROJECTION_UNSAFE")
    finally:
        if child_fd is not None:
            try:
                os.unlink(tmp, dir_fd=child_fd)
            except OSError:
                pass
            os.close(child_fd)


def read_projection(root_fd: int, directory: str, filename: str) -> bytes | None:
    """Read a projection by anchored dirfd; missing is repairable from trust."""
    child_fd = None
    try:
        child_fd = _open_child_dir(root_fd, directory)
        try:
            fd = os.open(
                filename, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=child_fd)
        except FileNotFoundError:
            return None
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                _invalid("BAMF_C05_FIXED_SCHOOL_PROJECTION_UNSAFE")
            chunks = []
            while True:
                chunk = os.read(fd, 1 << 20)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(fd)
        return b"".join(chunks)
    finally:
        if child_fd is not None:
            os.close(child_fd)


def projection_names(root_fd: int, directory: str) -> tuple[str, ...]:
    """List one anchored projection directory without following path indirection."""
    child_fd = None
    try:
        child_fd = _open_child_dir(root_fd, directory)
        names = os.listdir(child_fd)
        if any(not isinstance(name, str) or name in (".", "..") for name in names):
            _invalid("BAMF_C05_FIXED_SCHOOL_PROJECTION_UNSAFE")
        return tuple(sorted(names))
    except OSError:
        _invalid("BAMF_C05_FIXED_SCHOOL_PROJECTION_UNSAFE")
        raise AssertionError
    finally:
        if child_fd is not None:
            os.close(child_fd)


def require_projection_json(
        root_fd: int, directory: str, filename: str, raw: bytes) -> None:
    """Repair one mutable projection from immutable authority and verify readback."""
    existing = read_projection(root_fd, directory, filename)
    if existing != raw:
        project_bytes(root_fd, directory, filename, raw)
    if read_projection(root_fd, directory, filename) != raw:
        _invalid("BAMF_C05_FIXED_SCHOOL_PROJECTION_DRIFT")
    try:
        json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        _invalid("BAMF_C05_FIXED_SCHOOL_PROJECTION_INVALID")


__all__ = ()
