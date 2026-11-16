"""Compact authenticated A09 history head and process-local membership index."""
from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib

from .atlas_frontier_contracts import CurriculumSnapshot, _bytes, _fail
from .atlas_frontier_progress_metrics import (
    note_receipt_history_lookup, note_snapshot_rehash,
)
from .atlas_frontier_progress_tree import (
    IndexNode, ZERO_DIGEST, insert, keys, lookup, root_digest,
)

_ZERO = ZERO_DIGEST
_SCHEMA = "bilqis.factory-frontier-history-head/v1"


def _digest(value) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


@dataclass(frozen=True)
class FrontierHistoryHead:
    root_snapshot_sha256: str
    head_snapshot_sha256: str
    snapshot_chain_sha256: str
    snapshot_index_sha256: str
    snapshot_count: int
    receipt_index_sha256: str
    successor_index_sha256: str
    requested_index_sha256: str
    requested_semantic_index_sha256: str
    requested_semantic_count: int
    receipt_count: int
    history_sha256: str
    schema: str = _SCHEMA

    def expected_digest(self) -> str:
        return _digest({
            field.name: getattr(self, field.name)
            for field in fields(self) if field.name != "history_sha256"
        })

    def verify(self) -> None:
        digests = (
            self.root_snapshot_sha256, self.head_snapshot_sha256,
            self.snapshot_chain_sha256, self.snapshot_index_sha256,
            self.receipt_index_sha256, self.successor_index_sha256,
            self.requested_index_sha256, self.requested_semantic_index_sha256,
            self.history_sha256,
        )
        if (self.schema != _SCHEMA
                or any(type(item) is not str or len(item) != len(_ZERO)
                       or any(char not in "0123456789abcdef" for char in item)
                       for item in digests)
                or type(self.snapshot_count) is not int or self.snapshot_count < 1
                or type(self.requested_semantic_count) is not int
                or self.requested_semantic_count < 0
                or type(self.receipt_count) is not int or self.receipt_count < 0
                or self.history_sha256 != self.expected_digest()):
            _fail("BAMF_PLANNER_HISTORY_HEAD_INVALID")


def _snapshot_value(snapshot: CurriculumSnapshot, ordinal: int) -> tuple:
    return (
        snapshot.predecessor_sha256 or "",
        snapshot.admitted_factory_release_sha256 or "",
        snapshot.policy_epoch,
        snapshot.cursor,
        ordinal,
    )


def _receipt_value(receipt, anchor: tuple) -> tuple:
    from .atlas_frontier_progress_validation import obligation_digest
    return (
        receipt.selection.snapshot_sha256,
        receipt.selected_semantic_id,
        obligation_digest(receipt.selection.selected_obligations),
        receipt.staged_successor_sha256,
        receipt.predecessor_release.release_sha256,
        anchor[2],
        anchor[3],
        len(receipt.selection.introduced_capability_ids),
        len(receipt.selection.introduced_semantic_ids),
        receipt.selection.requested_obligation_keys,
    )


@dataclass(frozen=True)
class CompactReceiptCredit:
    receipt_sha256: str
    selection_snapshot_sha256: str
    selected_semantic_id: str
    obligation_sha256: str
    staged_successor_sha256: str
    predecessor_release_sha256: str
    policy_epoch: int
    cursor: int
    introduced_capability_count: int
    introduced_semantic_count: int
    requested_obligation_keys: tuple[tuple[str, str], ...]

    @property
    def index_value(self) -> tuple:
        return (
            self.selection_snapshot_sha256,
            self.selected_semantic_id,
            self.obligation_sha256,
            self.staged_successor_sha256,
            self.predecessor_release_sha256,
            self.policy_epoch,
            self.cursor,
            self.introduced_capability_count,
            self.introduced_semantic_count,
            self.requested_obligation_keys,
        )


@dataclass(frozen=True)
class _State:
    head: FrontierHistoryHead
    snapshots: IndexNode | None
    receipts: IndexNode | None
    successors: IndexNode | None
    requested: IndexNode | None
    requested_semantics: IndexNode | None


class FrontierHistoryOwner:
    """Append-only compact owner; full historical payloads never live here."""

    def __init__(self, snapshot: CurriculumSnapshot, *, historical: bool = False):
        if type(snapshot) is not CurriculumSnapshot:
            _fail("BAMF_PLANNER_HISTORY_SNAPSHOT_INVALID")
        note_snapshot_rehash(
            historical_bytes=(len(snapshot.digest_bytes()) if historical else 0))
        snapshot.verify()
        snapshots = insert(
            None, snapshot.snapshot_sha256, _snapshot_value(snapshot, 1))
        chain = _digest(("root", snapshot.predecessor_sha256, snapshot.snapshot_sha256))
        head = _make_head(
            snapshot.snapshot_sha256, snapshot.snapshot_sha256, chain,
            snapshots, None, None, None, None, 1, 0, 0)
        self._states = {head.history_sha256: _State(
            head, snapshots, None, None, None, None)}
        self._receipt_credits: dict[str, CompactReceiptCredit] = {}

    @property
    def initial_head(self) -> FrontierHistoryHead:
        return next(iter(self._states.values())).head

    def require(self, head: FrontierHistoryHead) -> _State:
        head.verify()
        state = self._states.get(head.history_sha256)
        if state is None or state.head != head:
            _fail("BAMF_PLANNER_HISTORY_OWNER_REQUIRED")
        return state

    def append_snapshot(
            self, head: FrontierHistoryHead,
            snapshot: CurriculumSnapshot, *, strict_duplicate: bool = False,
            historical: bool = False,
    ) -> FrontierHistoryHead:
        state = self.require(head)
        if type(snapshot) is not CurriculumSnapshot:
            _fail("BAMF_PLANNER_HISTORY_SNAPSHOT_INVALID")
        note_snapshot_rehash(
            historical_bytes=(len(snapshot.digest_bytes()) if historical else 0))
        snapshot.verify()
        if snapshot.snapshot_sha256 == head.head_snapshot_sha256:
            if strict_duplicate:
                _fail("BAMF_PLANNER_HISTORY_SNAPSHOT_DUPLICATE")
            return head
        if snapshot.predecessor_sha256 != head.head_snapshot_sha256:
            _fail("BAMF_PLANNER_HISTORY_PREDECESSOR_MISMATCH")
        if lookup(state.snapshots, snapshot.snapshot_sha256) is not None:
            _fail("BAMF_PLANNER_HISTORY_SNAPSHOT_DUPLICATE")
        snapshots = insert(
            state.snapshots, snapshot.snapshot_sha256,
            _snapshot_value(snapshot, head.snapshot_count + 1))
        chain = _digest((
            "append", head.snapshot_chain_sha256,
            snapshot.predecessor_sha256, snapshot.snapshot_sha256,
        ))
        next_head = _make_head(
            head.root_snapshot_sha256, snapshot.snapshot_sha256, chain,
            snapshots, state.receipts, state.successors,
            state.requested, state.requested_semantics,
            head.snapshot_count + 1, head.requested_semantic_count,
            head.receipt_count)
        self._states[next_head.history_sha256] = _State(
            next_head, snapshots, state.receipts, state.successors,
            state.requested, state.requested_semantics)
        return next_head

    def append_receipt(
            self, head: FrontierHistoryHead, receipt, *,
            verified: bool = False, historical: bool = False,
    ) -> FrontierHistoryHead:
        from .atlas_frontier_progress_contracts import StagedSelectionReceipt
        if type(receipt) is not StagedSelectionReceipt:
            _fail("BAMF_PLANNER_HISTORY_RECEIPT_INVALID")
        state = self.require(head)
        if not verified:
            note_snapshot_rehash(
                historical_bytes=(
                    len(receipt.selection_snapshot.digest_bytes())
                    if historical else 0))
            receipt.verify()
        note_receipt_history_lookup()
        anchor = lookup(state.snapshots, receipt.selection.snapshot_sha256)
        if anchor is None:
            _fail("BAMF_PLANNER_HISTORY_RECEIPT_ANCESTOR_MISSING")
        value = _receipt_value(receipt, anchor)
        existing = lookup(state.receipts, receipt.receipt_sha256)
        if existing is not None:
            if existing != value:
                _fail("BAMF_PLANNER_HISTORY_RECEIPT_CONFLICT")
            return head
        if lookup(state.successors, receipt.staged_successor_sha256) is not None:
            _fail("BAMF_PLANNER_HISTORY_SUCCESSOR_DUPLICATE")
        receipts = insert(state.receipts, receipt.receipt_sha256, value)
        successors = insert(
            state.successors, receipt.staged_successor_sha256,
            (receipt.receipt_sha256,))
        request_key = _request_key(value[1], value[2])
        requested = insert(
            state.requested, request_key, (receipt.receipt_sha256,))
        semantic_seen = lookup(
            state.requested_semantics, receipt.selected_semantic_id) is not None
        requested_semantics = insert(
            state.requested_semantics, receipt.selected_semantic_id,
            ("requested",))
        self._receipt_credits[receipt.receipt_sha256] = CompactReceiptCredit(
            receipt.receipt_sha256, *value)
        next_head = _make_head(
            head.root_snapshot_sha256, head.head_snapshot_sha256,
            head.snapshot_chain_sha256, state.snapshots,
            receipts, successors, requested, requested_semantics,
            head.snapshot_count,
            head.requested_semantic_count + (0 if semantic_seen else 1),
            head.receipt_count + 1)
        self._states[next_head.history_sha256] = _State(
            next_head, state.snapshots, receipts, successors, requested,
            requested_semantics)
        return next_head

    def snapshot_anchor(self, head: FrontierHistoryHead, snapshot_sha256: str):
        return lookup(self.require(head).snapshots, snapshot_sha256)

    def requested_keys(
            self, head: FrontierHistoryHead, current: dict[str, str],
            ready_semantic_ids: set[str] | None = None,
    ):
        root = self.require(head).requested
        result = set()
        for semantic_id, obligation_sha256 in current.items():
            if (ready_semantic_ids is not None
                    and semantic_id not in ready_semantic_ids):
                continue
            note_receipt_history_lookup()
            if lookup(root, _request_key(semantic_id, obligation_sha256)) is not None:
                result.add((semantic_id, obligation_sha256))
        return result

    def matching_credit(
            self, head: FrontierHistoryHead,
            semantic_id: str, obligation_sha256: str,
    ) -> CompactReceiptCredit | None:
        state = self.require(head)
        note_receipt_history_lookup()
        value = lookup(
            state.requested, _request_key(semantic_id, obligation_sha256))
        if value is None:
            return None
        return self._require_credit(state, value[0])

    def receipt_credit(
            self, head: FrontierHistoryHead,
            receipt_sha256: str,
    ) -> CompactReceiptCredit | None:
        state = self.require(head)
        note_receipt_history_lookup()
        if lookup(state.receipts, receipt_sha256) is None:
            return None
        return self._require_credit(state, receipt_sha256)

    def _require_credit(
            self, state: _State, receipt_sha256: str,
    ) -> CompactReceiptCredit:
        credit = self._receipt_credits.get(receipt_sha256)
        if (credit is None
                or lookup(state.receipts, credit.receipt_sha256)
                   != credit.index_value):
            _fail("BAMF_PLANNER_HISTORY_RECEIPT_CREDIT_MISSING")
        return credit

    def receipt_semantic_ids(self, head: FrontierHistoryHead) -> tuple[str, ...]:
        return tuple(sorted(keys(self.require(head).requested_semantics)))

    def requested_semantics_within(
            self, head: FrontierHistoryHead, eligible: set[str]) -> bool:
        state = self.require(head)
        matched = sum(
            lookup(state.requested_semantics, semantic_id) is not None
            for semantic_id in eligible)
        return matched == head.requested_semantic_count

    def all_requested_keys(
            self, head: FrontierHistoryHead) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(
            tuple(key.split("\x00", 1))
            for key in keys(self.require(head).requested)))

    def contains_receipt(self, head: FrontierHistoryHead, receipt_sha256: str) -> bool:
        note_receipt_history_lookup()
        return lookup(self.require(head).receipts, receipt_sha256) is not None


def _request_key(semantic_id: str, obligation_sha256: str) -> str:
    return f"{semantic_id}\x00{obligation_sha256}"


def _make_head(root_snapshot_sha256, head_snapshot_sha256, chain, snapshots,
               receipts, successors, requested, requested_semantics,
               snapshot_count, requested_semantic_count, receipt_count):
    draft = FrontierHistoryHead(
        root_snapshot_sha256=root_snapshot_sha256,
        head_snapshot_sha256=head_snapshot_sha256,
        snapshot_chain_sha256=chain,
        snapshot_index_sha256=root_digest(snapshots),
        snapshot_count=snapshot_count,
        receipt_index_sha256=root_digest(receipts),
        successor_index_sha256=root_digest(successors),
        requested_index_sha256=root_digest(requested),
        requested_semantic_index_sha256=root_digest(requested_semantics),
        requested_semantic_count=requested_semantic_count,
        receipt_count=receipt_count,
        history_sha256=_ZERO,
    )
    result = FrontierHistoryHead(
        **{
            field.name: (
                draft.expected_digest()
                if field.name == "history_sha256" else getattr(draft, field.name))
            for field in fields(draft)
        }
    )
    result.verify()
    return result
