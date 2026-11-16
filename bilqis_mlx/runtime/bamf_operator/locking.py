"""BAMF-native single-writer lock for persistent human operation."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat

from bilqis_mlx.errors import ErrorBus, SCHOOL


LOCKFILE = ".bamf-operator.lock"


def bamf_operator_lock_held(run_dir: Path) -> bool | None:
    """Observe writer activity; return None when the lock cannot be inspected."""
    path = Path(run_dir) / LOCKFILE
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        return None
    if not stat.S_ISREG(observed.st_mode):
        return None
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, os.O_RDONLY | nofollow)
    except OSError:
        return None
    try:
        opened = os.fstat(fd)
        if ((opened.st_dev, opened.st_ino)
                != (observed.st_dev, observed.st_ino)):
            return None
        try:
            fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        else:
            fcntl.flock(fd, fcntl.LOCK_UN)
            return False
    finally:
        os.close(fd)


@contextmanager
def bamf_operator_lock(run_dir: Path):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    fd = os.open(run_dir / LOCKFILE, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            try:
                ErrorBus.raise_(
                    SCHOOL.BAMF_FIRST_STUDENT.INVALID,
                    reason="BAMF_OPERATOR_ANOTHER_WRITER_ACTIVE")
            except Exception as error:
                raise error from exc
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


__all__ = ("LOCKFILE", "bamf_operator_lock", "bamf_operator_lock_held")
