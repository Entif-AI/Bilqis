"""A09.5 adapter from pure atlas planning to the existing JIT proposal surface.

The adapter owns no source, staging, admission, or learning authority.  It binds
A09.1-A09.4 decisions to already verified Factory candidate artifacts and lets
the existing JIT gate re-check current learner evidence before emitting a
proposal.  Persisted staging and admission remain with their existing owners.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib

from bilqis_mlx.errors import BilqisError
from .autonomy import AutonomyPlan, EvidenceLedger
from .candidate_frontier import CandidateFrontierRelease
from .candidate_staging import StagedCandidate
from .executable_release import ExecutableFactoryRelease
from .jit_curriculum import CurriculumDeltaProposal, ProposalDisposition, propose_curriculum_delta
from .atlas_frontier_closure import ClosureStatus, FrontierClosure
from .atlas_frontier_contracts import CurriculumSnapshot, _fail
from .atlas_frontier_progress import plan_frontier_progress
from .atlas_frontier_progress_validation import (
    credited_obligation_keys,
    current_obligations,
)
from .atlas_frontier_progress_contracts import (
    FrontierProgress, FrontierStatus, StagedSelectionReceipt,
)
from .atlas_frontier_selection import (
    FrontierDeltaSelection, ranked_frontier_target,
    select_frontier_delta_for_projection, validate_frontier_selection,
)
from .atlas_frontier_selection_validation import TargetDeltaProjection
from . import candidate_realizations


_SHA256_HEX_LENGTH = hashlib.sha256().digest_size * 2
_OBLIGATION_KEY_PARTS = 2
_ACCEPTED_CREDIT_ISSUER = object()


def _digest(value: object) -> bool:
    return (type(value) is str and len(value) == _SHA256_HEX_LENGTH
            and all(char in "0123456789abcdef" for char in value))


@dataclass(frozen=True)
class AcceptedObligationCredit:
    """Ephemeral planner capability minted only from authenticated B13 custody."""

    factory_release_sha256: str
    acceptance_sha256: str
    obligation_keys: tuple[tuple[str, str], ...]
    schema: str = "bilqis.factory-accepted-obligation-credit/v1"
    _issuance: object = field(init=False, default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if (getattr(self, "_issuance", None) is not _ACCEPTED_CREDIT_ISSUER
                or not _digest(self.factory_release_sha256)
                or not _digest(self.acceptance_sha256)
                or type(self.obligation_keys) is not tuple
                or self.obligation_keys != tuple(sorted(set(self.obligation_keys)))
                or any(type(item) is not tuple
                       or len(item) != _OBLIGATION_KEY_PARTS
                       or type(item[0]) is not str or not item[0]
                       or not _digest(item[1]) for item in self.obligation_keys)
                or self.schema != "bilqis.factory-accepted-obligation-credit/v1"):
            _fail("BAMF_PLANNER_ACCEPTED_CREDIT_INVALID")


def _issue_accepted_obligation_credit(
    factory_release_sha256: str,
    acceptance_sha256: str,
    obligation_keys: tuple[tuple[str, str], ...],
) -> AcceptedObligationCredit:
    """Mint planner credit after runtime has authenticated accepted B13 custody."""
    credit = object.__new__(AcceptedObligationCredit)
    for name, value in (
        ("factory_release_sha256", factory_release_sha256),
        ("acceptance_sha256", acceptance_sha256),
        ("obligation_keys", tuple(sorted(set(obligation_keys)))),
        ("schema", "bilqis.factory-accepted-obligation-credit/v1"),
        ("_issuance", _ACCEPTED_CREDIT_ISSUER),
    ):
        object.__setattr__(credit, name, value)
    credit.__post_init__()
    return credit


def bind_realized_snapshot(
    snapshot: CurriculumSnapshot,
    curriculum_candidate,
    candidate_frontier: CandidateFrontierRelease,
    current_release: ExecutableFactoryRelease,
    staged_candidates: tuple[StagedCandidate, ...],
) -> CurriculumSnapshot:
    """Overlay A09.5 realization evidence without changing the frozen A08 census."""
    if (type(snapshot) is not CurriculumSnapshot
            or snapshot.frozen_census_sha256 != curriculum_candidate.census.digest
            or snapshot.candidate_frontier_sha256 != candidate_frontier.release_sha256
            or snapshot.admitted_factory_release_sha256 != current_release.release_sha256):
        _fail("BAMF_PLANNER_REALIZATION_BRIDGE_INPUT_INVALID")
    coverage = candidate_realizations.realized_coverage_rows(
        curriculum_candidate, candidate_frontier, current_release, staged_candidates)
    frontier_edges = candidate_realizations.realized_prerequisite_edges(
        curriculum_candidate, candidate_frontier)
    edges = tuple(sorted(set((*snapshot.prerequisite_edges, *frontier_edges))))
    draft = replace(
        snapshot,
        coverage_rows=coverage,
        prerequisite_edges=edges,
        staged_factory_release_sha256s=tuple(sorted(
            item.successor.release_sha256 for item in staged_candidates)),
        snapshot_sha256="0" * 64,
    )
    result = replace(draft, snapshot_sha256=draft.expected_digest())
    result.verify()
    return result


@dataclass(frozen=True)
class AtlasCoverageEpoch:
    """Typed adapter view over existing authoritative artifacts, not new authority."""

    snapshot: CurriculumSnapshot
    closure: FrontierClosure
    candidate_frontier: CandidateFrontierRelease
    current_release: ExecutableFactoryRelease
    staged_candidates: tuple[StagedCandidate, ...]
    prior: FrontierProgress | None = None
    accepted_credit: AcceptedObligationCredit | None = None

    def verify(self) -> None:
        if (type(self.snapshot) is not CurriculumSnapshot
                or type(self.closure) is not FrontierClosure
                or type(self.candidate_frontier) is not CandidateFrontierRelease
                or not isinstance(self.current_release, ExecutableFactoryRelease)
                or type(self.staged_candidates) is not tuple
                or any(type(item) is not StagedCandidate for item in self.staged_candidates)
                or (self.prior is not None and type(self.prior) is not FrontierProgress)
                or (self.accepted_credit is not None
                    and type(self.accepted_credit) is not AcceptedObligationCredit)):
            _fail("BAMF_PLANNER_ADAPTER_INPUT_INVALID")
        self.snapshot.verify()
        self.closure.verify()
        self.candidate_frontier.verify()
        self.current_release.verify()
        if (self.closure.snapshot_sha256 != self.snapshot.snapshot_sha256
                or self.snapshot.candidate_frontier_sha256
                   != self.candidate_frontier.release_sha256
                or self.snapshot.admitted_factory_release_sha256
                   != self.current_release.release_sha256):
            _fail("BAMF_PLANNER_ADAPTER_EPOCH_MISMATCH")
        staged_sha256s = tuple(
            item.successor.release_sha256 for item in self.staged_candidates)
        if (len(set(staged_sha256s)) != len(staged_sha256s)
                or any(item not in self.snapshot.staged_factory_release_sha256s
                       for item in staged_sha256s)):
            _fail("BAMF_PLANNER_ADAPTER_STAGED_SET_INVALID")
        for item in self.staged_candidates:
            item.verify(self.candidate_frontier, self.current_release)
        if self.accepted_credit is not None:
            self.accepted_credit.__post_init__()
            if (self.accepted_credit.factory_release_sha256
                    != self.current_release.release_sha256):
                _fail("BAMF_PLANNER_ACCEPTED_CREDIT_RELEASE_DRIFT")
        if self.prior is not None:
            self.prior.verify()


@dataclass(frozen=True)
class AtlasLearnerEvidence:
    ledger: EvidenceLedger
    checkpoint_sha256: str
    optimizer_step: int

    def __post_init__(self) -> None:
        if (type(self.ledger) is not EvidenceLedger
                or type(self.checkpoint_sha256) is not str
                or len(self.checkpoint_sha256) != _SHA256_HEX_LENGTH
                or any(char not in "0123456789abcdef" for char in self.checkpoint_sha256)
                or type(self.optimizer_step) is not int or self.optimizer_step < 0):
            _fail("BAMF_PLANNER_ADAPTER_EVIDENCE_INVALID")


def _ready_rows(closure: FrontierClosure, semantic_id: str):
    rows = tuple(sorted(
        item for item in closure.candidates if item.semantic_id == semantic_id))
    return rows if rows and all(item.status is ClosureStatus.READY for item in rows) else ()


def _staged_for_projection(
    epoch: AtlasCoverageEpoch, projection: TargetDeltaProjection,
) -> StagedCandidate | None:
    try:
        expected_sense = candidate_realizations.realized_source_sense_id(
            projection.semantic_id)
    except ValueError:
        return None
    matches = []
    for staged in epoch.staged_candidates:
        transition = staged.successor.transition
        if transition is None:
            continue
        suffix = staged.successor.semantic_catalog[len(epoch.current_release.semantic_catalog):]
        if (staged.source_sense_id == expected_sense
                and staged.target_capability_id in projection.added_capability_ids
                and transition.added_capabilities == projection.added_capability_ids
                and tuple(suffix) == projection.introduced_semantic_ids):
            matches.append(staged)
    if len(matches) > 1:
        _fail("BAMF_PLANNER_ADAPTER_BINDING_AMBIGUOUS")
    return matches[0] if matches else None


def staged_selection_receipt(
    epoch: AtlasCoverageEpoch, selection: FrontierDeltaSelection,
    projection: TargetDeltaProjection, staged: StagedCandidate,
) -> StagedSelectionReceipt:
    """Build the existing A09.4/C07 handoff receipt for one persisted stage."""
    epoch.verify()
    staged.verify(epoch.candidate_frontier, epoch.current_release)
    validate_frontier_selection(
        epoch.snapshot, epoch.closure, selection,
        epoch.current_release, projection)
    provisional = StagedSelectionReceipt(
        selection, epoch.snapshot, projection, epoch.current_release,
        staged.successor, "0" * 64)
    receipt = replace(
        provisional, receipt_sha256=provisional.expected_digest())
    receipt.verify()
    return receipt


def _credited_requested_keys(coverage_epoch: AtlasCoverageEpoch) -> tuple[tuple[str, str], ...]:
    """Read compact authenticated historical credit before reranking."""
    if coverage_epoch.prior is None:
        return ()
    current = current_obligations(coverage_epoch.closure)
    return tuple(sorted(
        credited_obligation_keys(
            coverage_epoch.snapshot, coverage_epoch.closure,
            coverage_epoch.prior, current)))


def _accepted_requested_keys(
    coverage_epoch: AtlasCoverageEpoch,
) -> tuple[tuple[str, str], ...]:
    """Credit only exact obligation identities authenticated by B13 custody."""
    credit = coverage_epoch.accepted_credit
    if credit is None:
        return ()
    current = current_obligations(coverage_epoch.closure)
    return tuple(
        key for key in credit.obligation_keys
        if current.get(key[0]) == key[1]
    )


def next_atlas_delta(
    coverage_epoch: AtlasCoverageEpoch,
    learner_evidence: AtlasLearnerEvidence,
    existing_plan: AutonomyPlan,
) -> "AtlasDeltaScopeHandoff | FrontierStatus":
    """Return an authority-bound staged handoff or typed status without admission."""
    if (type(coverage_epoch) is not AtlasCoverageEpoch
            or type(learner_evidence) is not AtlasLearnerEvidence
            or type(existing_plan) is not AutonomyPlan):
        _fail("BAMF_PLANNER_ADAPTER_INPUT_INVALID")
    coverage_epoch.verify()

    # A persisted staged successor blocks reranking until the existing admission
    # owner resolves it.  A09.4 remains the authority for that replay decision.
    if (coverage_epoch.prior is not None
            and coverage_epoch.prior.pending_staged_successor_sha256 is not None):
        return plan_frontier_progress(
            coverage_epoch.snapshot, coverage_epoch.closure,
            prior=coverage_epoch.prior).status

    requested = tuple(sorted(set(
        (*_credited_requested_keys(coverage_epoch),
         *_accepted_requested_keys(coverage_epoch))
    )))
    try:
        semantic_id, rows = ranked_frontier_target(
            coverage_epoch.snapshot, coverage_epoch.closure, requested)
    except BilqisError as error:
        if error.context.get("reason") == "BAMF_PLANNER_NO_BOUNDED_READY_DELTA":
            return plan_frontier_progress(
                coverage_epoch.snapshot, coverage_epoch.closure,
                prior=coverage_epoch.prior).status
        raise
    try:
        projection = candidate_realizations.project_authoritative_target(
            semantic_id, coverage_epoch.current_release, rows)
    except ValueError:
        return FrontierStatus.IMPLEMENTATION_UNCOVERED
    selection = select_frontier_delta_for_projection(
        coverage_epoch.snapshot, coverage_epoch.closure,
        coverage_epoch.current_release, projection, requested)
    progress = plan_frontier_progress(
        coverage_epoch.snapshot, coverage_epoch.closure, selection,
        current_release=coverage_epoch.current_release,
        selected_projection=projection, prior=coverage_epoch.prior)
    if progress.status is not FrontierStatus.PROPOSAL:
        return progress.status

    staged = _staged_for_projection(coverage_epoch, projection)
    if staged is None:
        return FrontierStatus.IMPLEMENTATION_UNCOVERED
    receipt = staged_selection_receipt(
        coverage_epoch, selection, projection, staged)
    deferred = tuple(sorted(
        item.candidate_id for item in coverage_epoch.candidate_frontier.candidates
        if item.candidate_id != staged.candidate_id))
    proposal = propose_curriculum_delta(
        coverage_epoch.candidate_frontier, coverage_epoch.current_release,
        learner_evidence.ledger, existing_plan,
        learner_evidence.checkpoint_sha256, learner_evidence.optimizer_step,
        candidate_bindings=(staged.binding,), deferred_candidate_ids=deferred)
    if proposal.disposition is not ProposalDisposition.PROPOSAL:
        return FrontierStatus.WAITING_FOR_EVIDENCE
    if (proposal.selected_candidate_ids != (staged.candidate_id,)
            or proposal.selected_successor_sha256 != staged.successor.release_sha256):
        _fail("BAMF_PLANNER_ADAPTER_SELECTION_DRIFT")
    from .atlas_delta_scope import build_atlas_delta_scope_handoff
    return build_atlas_delta_scope_handoff(
        coverage_epoch.candidate_frontier, receipt, staged, proposal)
