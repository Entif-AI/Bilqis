"""Append-only cursor for one authenticated rejection projection."""
from __future__ import annotations

import json
import os
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Callable

from .priority_rejection_journal import (
    _TAINTED, _TRUSTED, _UNTRACKED, baseline_journal_state,
    journal_state_status,
)


class RejectionRows(Sequence):
    """O(1) immutable-length view over append-only projected rows."""

    __slots__ = ("_length", "_rows", "_start")

    def __init__(self, rows, length, start=0):
        self._rows = rows
        self._length = length
        self._start = start

    def __len__(self):
        return self._length

    def __iter__(self) -> Iterator:
        for index in range(self._start, self._start + self._length):
            yield self._rows[index]

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.indices(self._length)
            return tuple(
                self._rows[self._start + position]
                for position in range(start, stop, step))
        if index < 0:
            index += self._length
        if not 0 <= index < self._length:
            raise IndexError(index)
        return self._rows[self._start + index]

    def __eq__(self, other):
        if not isinstance(other, Sequence):
            return NotImplemented
        return len(self) == len(other) and all(
            left == right for left, right in zip(self, other))

    def __repr__(self):
        return repr(tuple(self))


@dataclass
class RejectionProjection:
    """Derived current-generation rows plus the verified journal position."""

    offset: int = 0
    rows: list[tuple[str, str, str, str]] = field(default_factory=list)
    seen_receipts: set[str] = field(default_factory=set)
    capability_counts: dict[str, int] = field(default_factory=dict)
    reason_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    consecutive_interference: dict[str, int] = field(default_factory=dict)
    last_positions: dict[str, int] = field(default_factory=dict)
    legacy_capabilities: set[str] = field(default_factory=set)
    global_order_started: bool = False
    global_order_start: int | None = None
    lock: Lock = field(default_factory=Lock, repr=False)

    def refresh(
        self,
        journal: Path,
        validate: Callable[
            [dict],
            tuple[str, tuple[str, str, str, str], int | None, int | None] | None,
        ],
        invalid: Callable[[str], None],
    ) -> RejectionRows:
        with self.lock:
            return self._refresh(journal, validate, invalid)

    def _refresh(self, journal, validate, invalid):
        if not journal.exists():
            if self.offset or self.rows:
                invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
            return self.rows_view()
        if journal.is_symlink() or not journal.is_file():
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        payload = self._journal_delta(journal, invalid)
        if payload is None:
            return self.rows_view()
        after, raw_lines = payload
        self._ingest(raw_lines, validate, invalid)
        self.offset = after.st_size
        if not baseline_journal_state(journal, after):
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        return self.rows_view()

    def _journal_delta(self, journal, invalid):
        with journal.open("rb") as stream:
            before = os.fstat(stream.fileno())
            status = journal_state_status(journal, before)
            if self._prepare_cursor(journal, before, status, invalid):
                return None
            stream.seek(self.offset)
            delta = stream.read()
            after = os.fstat(stream.fileno())
        if not self._stable_read(before, after, len(delta)):
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        if delta and not delta.endswith(b"\n"):
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        try:
            raw_lines = delta.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
            return None
        return after, raw_lines

    def _prepare_cursor(self, journal, before, status, invalid):
        if self.offset and status == _UNTRACKED:
            self._reset()
        elif self.offset and status != _TRUSTED:
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        if before.st_size < self.offset:
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        if before.st_size != self.offset:
            return False
        if status == _TAINTED:
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        if not self.offset and not baseline_journal_state(journal, before):
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        return True

    def _stable_read(self, before, after, delta_size):
        return (
            after.st_dev == before.st_dev
            and after.st_ino == before.st_ino
            and after.st_size == before.st_size
            and after.st_mtime_ns == before.st_mtime_ns
            and after.st_ctime_ns == before.st_ctime_ns
            and delta_size == after.st_size - self.offset
        )

    def _ingest(self, raw_lines, validate, invalid):
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
            self._accept(item, invalid)

    def _accept(self, item, invalid):
        receipt_sha256, row, ordinal, journal_ordinal = item
        if receipt_sha256 in self.seen_receipts:
            return
        capability = row[0]
        count = self.capability_counts.get(capability, 0)
        expected_global = len(self.rows) + 1
        self._require_order(
            capability, journal_ordinal, ordinal, expected_global, count, invalid)
        self.seen_receipts.add(receipt_sha256)
        self.capability_counts[capability] = count + 1
        reason = row[2]
        reasons = self.reason_counts.setdefault(capability, {})
        reasons[reason] = reasons.get(reason, 0) + 1
        self.consecutive_interference[capability] = (
            0 if reason == "NO_MEASURABLE_TARGET_GAIN"
            else self.consecutive_interference.get(capability, 0) + 1
        )
        if journal_ordinal is not None or len(self.legacy_capabilities) <= 1:
            self.last_positions[capability] = expected_global
        self.rows.append(row)

    def _require_order(
            self, capability, journal_ordinal, ordinal, expected_global, count, invalid):
        if journal_ordinal is not None:
            if journal_ordinal != expected_global:
                invalid("BAMF_PRIORITY_REJECTION_ORDER_INVALID")
            if not self.global_order_started:
                self.global_order_start = len(self.rows)
            self.global_order_started = True
        elif self.global_order_started:
            invalid("BAMF_PRIORITY_REJECTION_ORDER_INVALID")
        else:
            self.legacy_capabilities.add(capability)
            if len(self.legacy_capabilities) > 1:
                self.last_positions.clear()
            if ordinal is None and count:
                # Legacy rows without a global ordinal can still contribute one
                # independently authenticated rejection per capability. A second
                # row for that capability needs the per-capability attempt ordinal.
                invalid("BAMF_PRIORITY_REJECTION_ORDER_INVALID")
        if ordinal is not None and ordinal != count + 1:
            invalid("BAMF_PRIORITY_REJECTION_ORDER_INVALID")

    def rows_view(self):
        return RejectionRows(self.rows, len(self.rows))

    def ordered_rows_view(self):
        start = self.global_order_start
        if len(self.legacy_capabilities) <= 1:
            return RejectionRows(self.rows, len(self.rows))
        if start is None:
            return RejectionRows(self.rows, 0)
        return RejectionRows(self.rows, len(self.rows) - start, start)

    def next_ordinals(self, capability):
        with self.lock:
            return len(self.rows) + 1, self.capability_counts.get(capability, 0) + 1

    def pressure(self, capability):
        with self.lock:
            return (
                dict(self.reason_counts.get(capability, {})),
                self.consecutive_interference.get(capability, 0),
            )

    def recency(self):
        with self.lock:
            return len(self.rows), dict(self.last_positions)

    def _reset(self):
        self.offset = 0
        self.rows.clear()
        self.seen_receipts.clear()
        self.capability_counts.clear()
        self.reason_counts.clear()
        self.consecutive_interference.clear()
        self.last_positions.clear()
        self.legacy_capabilities.clear()
        self.global_order_started = False
        self.global_order_start = None


__all__ = ("RejectionProjection", "RejectionRows")
