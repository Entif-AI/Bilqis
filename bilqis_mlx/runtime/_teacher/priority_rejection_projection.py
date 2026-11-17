"""Append-only cursor for one authenticated rejection projection."""
from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Callable

from .priority_rejection_journal import (
    _DIVERGED, _TAINTED, _UNTRACKED, baseline_journal_state,
    journal_state_status,
)
from .priority_rejection_projection_state import SCHEMA, encode, restore


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
    weakness_rows: list[dict] = field(default_factory=list)
    seen_receipts: set[str] = field(default_factory=set)
    capability_counts: dict[str, int] = field(default_factory=dict)
    reason_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    consecutive_interference: dict[str, int] = field(default_factory=dict)
    last_positions: dict[str, int] = field(default_factory=dict)
    legacy_capabilities: set[str] = field(default_factory=set)
    global_order_started: bool = False
    global_order_start: int | None = None
    ledger_identity: tuple[int, int] | None = None
    hydrated: bool = False
    lock: Lock = field(default_factory=Lock, repr=False)

    def refresh(
        self,
        run_dir: Path,
        projection_key: str,
        plane,
        validate: Callable[
            [dict],
            tuple[
                str, tuple[str, str, str, str], int | None, int | None,
                tuple[dict, ...],
            ] | None,
        ],
        invalid: Callable[[str], None],
    ) -> RejectionRows:
        with self.lock:
            return self._refresh(run_dir, projection_key, plane, validate, invalid)

    def _refresh(self, run_dir, projection_key, plane, validate, invalid):
        journal = Path(run_dir) / "events.jsonl"
        if not journal.exists():
            if self.offset or self.rows:
                self._reset()
            plane.sync_event_ledger(run_dir)
            return self.rows_view()
        if journal.is_symlink() or not journal.is_file():
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        before = journal.stat()
        status = journal_state_status(journal, before)
        if status in (_DIVERGED, _TAINTED):
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        if status == _UNTRACKED and not baseline_journal_state(journal, before):
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        if not self.hydrated:
            state = plane.event_projection_state(run_dir, projection_key, SCHEMA)
            if state is not None and restore(self, state["payload"]):
                self.offset = state["indexed_bytes"]
                self.ledger_identity = state["ledger_identity"]
            self.hydrated = True
        payload = plane.indexed_event_tail(run_dir, self.offset)
        identity = payload["ledger_identity"]
        if payload["rebuilt"] or (
                self.ledger_identity is not None and identity != self.ledger_identity):
            self._reset(keep_hydrated=True)
            payload = plane.indexed_event_tail(run_dir, 0)
            identity = payload["ledger_identity"]
        self._ingest(payload["events"], validate, invalid)
        self.offset = payload["indexed_bytes"]
        self.ledger_identity = identity
        if identity is not None:
            plane.remember_event_projection(
                run_dir, projection_key, SCHEMA, identity, self.offset, encode(self))
        after = journal.stat()
        after_status = journal_state_status(journal, after)
        if after_status == _UNTRACKED:
            baseline_journal_state(journal, after)
        elif after_status in (_DIVERGED, _TAINTED):
            invalid("BAMF_PRIORITY_REJECTION_JOURNAL_INVALID")
        return self.rows_view()

    def _ingest(self, events, validate, invalid):
        for event in events:
            if not isinstance(event, dict):
                continue
            item = validate(event)
            if item is None:
                continue
            self._accept(item, invalid)

    def _accept(self, item, invalid):
        receipt_sha256, row, ordinal, journal_ordinal, *extra = item
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
        if extra:
            self.weakness_rows.extend(extra[0])

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

    def weaknesses_view(self):
        with self.lock:
            return tuple(self.weakness_rows)

    def _reset(self, *, keep_hydrated=False):
        self.offset = 0
        self.rows.clear()
        self.weakness_rows.clear()
        self.seen_receipts.clear()
        self.capability_counts.clear()
        self.reason_counts.clear()
        self.consecutive_interference.clear()
        self.last_positions.clear()
        self.legacy_capabilities.clear()
        self.global_order_started = False
        self.global_order_start = None
        self.ledger_identity = None
        self.hydrated = keep_hydrated


__all__ = ("RejectionProjection", "RejectionRows")
