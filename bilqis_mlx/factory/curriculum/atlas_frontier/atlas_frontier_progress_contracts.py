"""A09.4 immutable progress/status contracts and verified staging bridge."""
from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
import hashlib

from .atlas_frontier_contracts import CurriculumSnapshot, _bytes, _fail
from .atlas_frontier_progress_index import FrontierHistoryHead, FrontierHistoryOwner
from .atlas_frontier_progress_metrics import note_snapshot_rehash
from .atlas_frontier_selection import FrontierDeltaSelection
from .atlas_frontier_selection_validation import (
    TargetDeltaProjection,
    snapshot_graph,
    validate_target_projection,
)
from .executable_release import ExecutableFactoryRelease


class FrontierStatus(str, Enum):
    PROPOSAL = "PROPOSAL"
    REPLAN_REQUIRED = "REPLAN_REQUIRED"
    FIXED_POINT = "FIXED_POINT"
    WAITING_FOR_EVIDENCE = "WAITING_FOR_EVIDENCE"
    SOURCE_HELD = "SOURCE_HELD"
    IMPLEMENTATION_UNCOVERED = "IMPLEMENTATION_UNCOVERED"
    LEASE_REQUIRED = "LEASE_REQUIRED"
    COMPLETE_ATLAS_COVERAGE = "COMPLETE_ATLAS_COVERAGE"


@dataclass(frozen=True, order=True)
class FrontierRemediation:
    semantic_id: str
    family_id: str
    status: FrontierStatus
    code: str
    owner: str
    dependency_id: str = ""


@dataclass(frozen=True)
class StagedSelectionReceipt:
    """Proof that one exact A09.3 selection became one verified staged successor."""

    selection: FrontierDeltaSelection
    selection_snapshot: CurriculumSnapshot
    projection: TargetDeltaProjection
    predecessor_release: ExecutableFactoryRelease
    staged_successor: ExecutableFactoryRelease
    receipt_sha256: str
    schema: str = "bilqis.factory-staged-selection-receipt/v1"

    @property
    def staged_successor_sha256(self) -> str:
        return self.staged_successor.release_sha256

    @property
    def selected_semantic_id(self) -> str:
        return self.selection.selected_semantic_id

    def expected_digest(self) -> str:
        return hashlib.sha256(_bytes({
            field.name: getattr(self, field.name)
            for field in fields(self) if field.name != "receipt_sha256"
        })).hexdigest()

    def verify(self) -> None:
        self.selection.verify()
        self.selection_snapshot.verify()
        _verify_selection_obligation_identity(
            self.selection_snapshot, self.selection)
        self.predecessor_release.verify()
        validate_target_projection(
            self.predecessor_release,
            self.selection.selected_obligations,
            self.projection,
        )
        self.staged_successor.verify_successor_of(self.predecessor_release)
        transition = self.staged_successor.transition
        previous = self.predecessor_release.semantic_catalog
        current = self.staged_successor.semantic_catalog
        if (self.schema != "bilqis.factory-staged-selection-receipt/v1"
                or self.selection.snapshot_sha256
                   != self.selection_snapshot.snapshot_sha256
                or self.selection.policy_epoch != self.selection_snapshot.policy_epoch
                or self.selection.cursor != self.selection_snapshot.cursor
                or self.selection_snapshot.admitted_factory_release_sha256
                   != self.predecessor_release.release_sha256
                or self.staged_successor_sha256
                   not in self.selection_snapshot.staged_factory_release_sha256s
                or self.projection.semantic_id != self.selection.selected_semantic_id
                or self.projection.added_capability_ids
                   != self.selection.introduced_capability_ids
                or self.projection.introduced_semantic_ids
                   != self.selection.introduced_semantic_ids
                or self.selection.admitted_release_sha256
                != self.predecessor_release.release_sha256
                or transition is None
                or transition.added_capabilities
                   != self.selection.introduced_capability_ids
                or transition.removed_capabilities
                or transition.changed_capabilities
                or current[:len(previous)] != previous
                or tuple(current[len(previous):])
                   != self.selection.introduced_semantic_ids
                or self.receipt_sha256 != self.expected_digest()):
            _fail("BAMF_PLANNER_STAGED_SELECTION_INVALID")


def _verify_selection_obligation_identity(
    snapshot: CurriculumSnapshot,
    selection: FrontierDeltaSelection,
) -> None:
    """Bind receipt obligation identity to the frozen source/prerequisite census."""
    graph = snapshot_graph(snapshot)
    semantic_id = selection.selected_semantic_id
    prerequisites = graph.get(semantic_id)
    if prerequisites is None:
        _fail("BAMF_PLANNER_STAGED_SELECTION_INVALID")
    expected = tuple(sorted(
        (row.semantic_id, row.family_id, row.source_evidence_sha256, prerequisites)
        for row in snapshot.coverage_rows
        if row.semantic_id == semantic_id
    ))
    actual = tuple(sorted(
        (row.semantic_id, row.family_id, row.source_evidence_sha256, row.prerequisites)
        for row in selection.selected_obligations
    ))
    if not expected or actual != expected:
        _fail("BAMF_PLANNER_STAGED_SELECTION_INVALID")


_PROGRESS_ISSUER = object()


@dataclass(frozen=True)
class FrontierProgress:
    input_snapshot: CurriculumSnapshot
    planning_snapshot: CurriculumSnapshot
    history_head: FrontierHistoryHead
    status: FrontierStatus
    proposal_selection_sha256: str | None
    pending_receipt: StagedSelectionReceipt | None
    source_held_count: int
    implementation_uncovered_count: int
    waiting_for_evidence_count: int
    ready_count: int
    remediation: tuple[FrontierRemediation, ...]
    progress_sha256: str
    schema: str = "bilqis.factory-atlas-frontier-progress/v2"

    @property
    def input_snapshot_sha256(self) -> str:
        return self.input_snapshot.snapshot_sha256

    @property
    def snapshot_sha256(self) -> str:
        return self.planning_snapshot.snapshot_sha256

    @property
    def coverage_epoch_sha256(self) -> str:
        return self.planning_snapshot.snapshot_sha256

    @property
    def cursor(self) -> int:
        return self.planning_snapshot.cursor

    @property
    def requested_semantic_ids(self) -> tuple[str, ...]:
        return _history_owner(self).receipt_semantic_ids(self.history_head)

    @property
    def pending_staged_receipt_sha256(self) -> str | None:
        return None if self.pending_receipt is None else self.pending_receipt.receipt_sha256

    @property
    def pending_staged_successor_sha256(self) -> str | None:
        receipt = self.pending_receipt
        return None if receipt is None else receipt.staged_successor_sha256

    @property
    def pending_semantic_id(self) -> str | None:
        receipt = self.pending_receipt
        return None if receipt is None else receipt.selected_semantic_id

    def requested_obligation_keys(
            self, current: dict[str, str],
            ready_semantic_ids: set[str] | None = None,
    ) -> set[tuple[str, str]]:
        return _history_owner(self).requested_keys(
            self.history_head, current, ready_semantic_ids)

    def all_requested_obligation_keys(self) -> tuple[tuple[str, str], ...]:
        """Enumerate compact credit only for explicit cold/audit operations."""
        return _history_owner(self).all_requested_keys(self.history_head)

    def expected_digest(self) -> str:
        return hashlib.sha256(_bytes({
            "input_snapshot_sha256": self.input_snapshot.snapshot_sha256,
            "planning_snapshot_sha256": self.planning_snapshot.snapshot_sha256,
            "history_sha256": self.history_head.history_sha256,
            "status": self.status,
            "proposal_selection_sha256": self.proposal_selection_sha256,
            "pending_staged_receipt_sha256": self.pending_staged_receipt_sha256,
            "source_held_count": self.source_held_count,
            "implementation_uncovered_count": self.implementation_uncovered_count,
            "waiting_for_evidence_count": self.waiting_for_evidence_count,
            "ready_count": self.ready_count,
            "remediation": self.remediation,
            "schema": self.schema,
        })).hexdigest()

    def verify(self) -> None:
        owner = _history_owner(self)
        owner.require(self.history_head)
        note_snapshot_rehash()
        self.input_snapshot.verify()
        if self.planning_snapshot.snapshot_sha256 != self.input_snapshot.snapshot_sha256:
            note_snapshot_rehash()
            self.planning_snapshot.verify()
        if (self.schema != "bilqis.factory-atlas-frontier-progress/v2"
                or self.history_head.head_snapshot_sha256
                   != self.planning_snapshot.snapshot_sha256
                or owner.snapshot_anchor(
                    self.history_head, self.input_snapshot.snapshot_sha256) is None
                or (self.planning_snapshot.snapshot_sha256
                    != self.input_snapshot.snapshot_sha256
                    and self.planning_snapshot.predecessor_sha256
                    != self.input_snapshot.snapshot_sha256)
                or min(self.source_held_count, self.implementation_uncovered_count,
                       self.waiting_for_evidence_count, self.ready_count) < 0):
            _fail("BAMF_PLANNER_PROGRESS_INVALID")
        if self.pending_receipt is not None:
            note_snapshot_rehash()
            self.pending_receipt.verify()
            if (self.status is not FrontierStatus.LEASE_REQUIRED
                    or not owner.contains_receipt(
                        self.history_head, self.pending_receipt.receipt_sha256)
                    or self.pending_receipt.staged_successor_sha256
                       not in self.planning_snapshot.staged_factory_release_sha256s
                    or self.pending_receipt.staged_successor_sha256
                       == self.planning_snapshot.admitted_factory_release_sha256):
                _fail("BAMF_PLANNER_PROGRESS_PENDING_RECEIPT_INVALID")
        elif self.status is FrontierStatus.LEASE_REQUIRED:
            _fail("BAMF_PLANNER_PROGRESS_PENDING_RECEIPT_REQUIRED")
        if self.progress_sha256 != self.expected_digest():
            _fail("BAMF_PLANNER_PROGRESS_DIGEST_MISMATCH")


def _issue_frontier_progress(
        progress: FrontierProgress, owner: FrontierHistoryOwner) -> FrontierProgress:
    object.__setattr__(progress, "_history_owner", owner)
    object.__setattr__(progress, "_issuance", _PROGRESS_ISSUER)
    return progress


def _history_owner(progress: FrontierProgress) -> FrontierHistoryOwner:
    owner = getattr(progress, "_history_owner", None)
    if (getattr(progress, "_issuance", None) is not _PROGRESS_ISSUER
            or type(owner) is not FrontierHistoryOwner):
        _fail("BAMF_PLANNER_PROGRESS_OWNER_REQUIRED")
    return owner
