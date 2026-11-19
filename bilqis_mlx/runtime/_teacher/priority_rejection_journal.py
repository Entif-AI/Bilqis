"""Process-local fencing for trusted append-only event-journal growth."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from threading import Lock


_UNTRACKED = "UNTRACKED"
_TRUSTED = "TRUSTED"
_DIVERGED = "DIVERGED"
_TAINTED = "TAINTED"


@dataclass
class _JournalAppendState:
    initialized: bool = False
    tainted: bool = False
    device: int | None = None
    inode: int | None = None
    size: int = 0
    mtime_ns: int | None = None
    ctime_ns: int | None = None
    lock: Lock = field(default_factory=Lock, repr=False)

    def status(self, stat_result) -> str:
        with self.lock:
            if self.tainted:
                return _TAINTED
            if not self.initialized:
                return _UNTRACKED
            return _TRUSTED if self._matches(stat_result) else _DIVERGED

    def baseline(self, stat_result) -> bool:
        with self.lock:
            if self.tainted:
                return False
            if self.initialized:
                return self._matches(stat_result)
            self.initialized = True
            self._remember(stat_result)
            return True

    def note_append(self, before, after, appended_bytes: int) -> None:
        with self.lock:
            if not self.initialized or self.tainted:
                return
            if (not self._matches(before)
                    or appended_bytes <= 0
                    or after.st_dev != before.st_dev
                    or after.st_ino != before.st_ino
                    or after.st_size != before.st_size + appended_bytes):
                self.tainted = True
                return
            self._remember(after)

    def _matches(self, stat_result) -> bool:
        return (
            stat_result.st_dev == self.device
            and stat_result.st_ino == self.inode
            and stat_result.st_size == self.size
            and stat_result.st_mtime_ns == self.mtime_ns
            and stat_result.st_ctime_ns == self.ctime_ns
        )

    def _remember(self, stat_result) -> None:
        self.device = stat_result.st_dev
        self.inode = stat_result.st_ino
        self.size = stat_result.st_size
        self.mtime_ns = stat_result.st_mtime_ns
        self.ctime_ns = stat_result.st_ctime_ns


def _path_key(path: Path) -> str:
    return str(Path(path).resolve(strict=False))


@lru_cache(maxsize=32)
def _state(_key: str) -> _JournalAppendState:
    return _JournalAppendState()


def journal_state_status(path: Path, stat_result) -> str:
    return _state(_path_key(path)).status(stat_result)


def baseline_journal_state(path: Path, stat_result) -> bool:
    return _state(_path_key(path)).baseline(stat_result)


def note_journal_append(path: Path, before, after, appended_bytes: int) -> None:
    """Advance a hydrated cursor fence only across the repository's trusted writer."""
    _state(_path_key(path)).note_append(before, after, appended_bytes)


__all__ = (
    "_DIVERGED", "_TAINTED", "_TRUSTED", "_UNTRACKED",
    "baseline_journal_state", "journal_state_status", "note_journal_append",
)
