"""Append-only cursor for one authenticated rejection projection."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


_TAIL_ANCHOR_BYTES = 256


@dataclass
class RejectionProjection:
    """Derived current-generation rows plus the verified journal position."""

    offset: int = 0
    device: int | None = None
    inode: int | None = None
    mtime_ns: int | None = None
    ctime_ns: int | None = None
    tail_anchor: bytes = b""
    rows: list[tuple[str, str, str, str]] = field(default_factory=list)
    seen_receipts: set[str] = field(default_factory=set)
    capability_counts: dict[str, int] = field(default_factory=dict)

    def refresh(
        self,
        journal: Path,
        validate: Callable[[dict], tuple[str, tuple[str, str, str, str], int | None] | None],
        invalid: Callable[[str], None],
    ) -> tuple[tuple[str, str, str, str], ...]:
        if not journal.exists():
            if self.offset or self.rows:
                invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
            return tuple(self.rows)
        if journal.is_symlink() or not journal.is_file():
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")

        with journal.open("rb") as stream:
            before = os.fstat(stream.fileno())
            self._require_identity(before, invalid)
            if before.st_size < self.offset:
                invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
            if before.st_size == self.offset:
                if self.device is not None and (
                    before.st_mtime_ns != self.mtime_ns or before.st_ctime_ns != self.ctime_ns
                ):
                    invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
                self._remember_state(before)
                return tuple(self.rows)
            if self.tail_anchor:
                stream.seek(self.offset - len(self.tail_anchor))
                if stream.read(len(self.tail_anchor)) != self.tail_anchor:
                    invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
            stream.seek(self.offset)
            delta = stream.read()
            after = os.fstat(stream.fileno())

        self._require_identity(after, invalid)
        if after.st_size != before.st_size or len(delta) != after.st_size - self.offset:
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        if delta and not delta.endswith(b"\n"):
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        try:
            raw_lines = delta.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
            return tuple(self.rows)

        for raw in raw_lines:
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
                continue
            if not isinstance(event, dict):
                continue
            item = validate(event)
            if item is None:
                continue
            receipt_sha256, row, ordinal = item
            if receipt_sha256 in self.seen_receipts:
                continue
            capability = row[0]
            count = self.capability_counts.get(capability, 0)
            if ordinal is not None and ordinal != count + 1:
                invalid("BAMF_PRIORITY_REJECTION_ORDER_INVALID")
            self.seen_receipts.add(receipt_sha256)
            self.capability_counts[capability] = count + 1
            self.rows.append(row)

        self.offset = after.st_size
        self.tail_anchor = (self.tail_anchor + delta)[-_TAIL_ANCHOR_BYTES:]
        self._remember_state(after)
        return tuple(self.rows)

    def _require_identity(self, stat_result, invalid):
        if self.device is None:
            return
        if stat_result.st_dev != self.device or stat_result.st_ino != self.inode:
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")

    def _remember_state(self, stat_result):
        self.device = stat_result.st_dev
        self.inode = stat_result.st_ino
        self.mtime_ns = stat_result.st_mtime_ns
        self.ctime_ns = stat_result.st_ctime_ns


__all__ = ("RejectionProjection",)
