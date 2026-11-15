"""A09.4 validation of direct and resumed frontier progress credit."""
from __future__ import annotations

from dataclasses import replace
import hashlib

from .atlas_frontier_closure import ClosureStatus, FrontierClosure
from .atlas_frontier_contracts import CurriculumSnapshot, _bytes, _fail
from .atlas_frontier_progress_contracts import (
    FrontierProgress, StagedSelectionReceipt, _history_owner,
)
from .atlas_frontier_selection import (
    FrontierDeltaSelection,
    _ranked_ready_targets,
    validate_frontier_selection,
)
from .atlas_frontier_selection_validation import TargetDeltaProjection
from .atlas_frontier_selection_validation import catalog_digest, obligation_signature
from .candidate_realizations import project_realized_target
from .executable_release import ExecutableFactoryRelease


def obligation_digest(rows) -> str:
    return hashlib.sha256(_bytes(tuple(
        (row.family_id, row.source_evidence_sha256, row.prerequisites)
        for row in sorted(rows)))).hexdigest()


def current_obligations(closure: FrontierClosure) -> dict[str, str]:
    return {
        identity: obligation_digest(tuple(
            row for row in closure.candidates if row.semantic_id == identity))
        for identity in closure.constituent_order
    }


def credited_obligation_keys(
    snapshot: CurriculumSnapshot,
    closure: FrontierClosure,
    prior: FrontierProgress,
    current: dict[str, str],
) -> set[tuple[str, str]]:
    """Revalidate compact historical credit against the current closure."""
    owner = _history_owner(prior)
    credited = set()
    for semantic_id, obligation_sha256 in current.items():
        credit = owner.matching_credit(
            prior.history_head, semantic_id, obligation_sha256)
        if credit is None:
            continue
        anchor = owner.snapshot_anchor(
            prior.history_head, credit.selection_snapshot_sha256)
        if (anchor is None
                or anchor[1] != credit.predecessor_release_sha256
                or anchor[2] != credit.policy_epoch
                or anchor[3] != credit.cursor):
            _fail("BAMF_PLANNER_HISTORY_RECEIPT_CREDIT_INVALID")
        bound_snapshot = replace(
            snapshot,
            admitted_factory_release_sha256=credit.predecessor_release_sha256,
            policy_epoch=credit.policy_epoch,
            cursor=credit.cursor,
            snapshot_sha256="0" * 64,
        )
        bound_snapshot = replace(
            bound_snapshot, snapshot_sha256=bound_snapshot.expected_digest())
        bound_closure = replace(
            closure,
            snapshot_sha256=bound_snapshot.snapshot_sha256,
            closure_sha256="0" * 64,
        )
        bound_closure = replace(
            bound_closure, closure_sha256=bound_closure.expected_digest())
        _, ranked = _ranked_ready_targets(
            bound_snapshot, bound_closure, credit.requested_obligation_keys)
        if (not ranked or min(ranked)[3] != semantic_id
                or credit.introduced_capability_count
                   > min(9, bound_snapshot.budget.max_candidates)
                or credit.introduced_semantic_count
                   > bound_snapshot.budget.max_identity_rows):
            continue
        credited.add((semantic_id, obligation_sha256))
    return credited


def validate_prior(snapshot: CurriculumSnapshot, prior: FrontierProgress | None) -> None:
    if prior is None:
        return
    if type(prior) is not FrontierProgress:
        _fail("BAMF_PLANNER_PROGRESS_PREDECESSOR_INVALID")
    prior.verify()
    if (snapshot.snapshot_sha256 != prior.planning_snapshot.snapshot_sha256
            and snapshot.predecessor_sha256
            != prior.planning_snapshot.snapshot_sha256):
        _fail("BAMF_PLANNER_PROGRESS_PREDECESSOR_MISMATCH")
    eligible = set(snapshot.source_eligible_concept_ids)
    if not set(prior.planning_snapshot.source_eligible_concept_ids) <= eligible:
        _fail("BAMF_PLANNER_PROGRESS_PREDECESSOR_SCOPE_DRIFT")


def validate_direct_selection(
    snapshot: CurriculumSnapshot,
    closure: FrontierClosure,
    selection: FrontierDeltaSelection | None,
    current_release: ExecutableFactoryRelease | None,
    selected_projection: TargetDeltaProjection | None,
    staged_receipt: StagedSelectionReceipt | None,
) -> tuple[ExecutableFactoryRelease | None, TargetDeltaProjection | None]:
    if selection is None:
        if current_release is not None or selected_projection is not None:
            _fail("BAMF_PLANNER_SELECTION_INPUT_INVALID")
        return None, None
    if (current_release is None and selected_projection is None
            and staged_receipt is not None):
        current_release = staged_receipt.predecessor_release
        selected_projection = staged_receipt.projection
    if current_release is None or selected_projection is None:
        _fail("BAMF_PLANNER_SELECTION_INPUT_INVALID")
    validate_projection_authority(
        selection, current_release, selected_projection)
    validate_frontier_selection(
        snapshot, closure, selection, current_release, selected_projection)
    return current_release, selected_projection


def validate_projection_authority(
    selection: FrontierDeltaSelection,
    current_release: ExecutableFactoryRelease,
    supplied: TargetDeltaProjection,
) -> None:
    """Rederive projection truth from source-owned realization authority."""
    try:
        capabilities, identities = project_realized_target(
            selection.selected_semantic_id, current_release)
    except (TypeError, ValueError):
        _fail("BAMF_PLANNER_PROJECTION_AUTHORITY_MISSING")
    provisional = TargetDeltaProjection(
        semantic_id=selection.selected_semantic_id,
        obligation_signature=obligation_signature(selection.selected_obligations),
        current_release_sha256=current_release.release_sha256,
        current_semantic_catalog_sha256=current_release.semantic_catalog_sha256,
        added_capability_ids=capabilities,
        introduced_semantic_ids=identities,
        projected_semantic_catalog_sha256=catalog_digest(
            current_release.semantic_catalog + identities),
        projection_sha256="0" * 64,
    )
    expected = replace(
        provisional, projection_sha256=provisional.expected_digest())
    if supplied != expected:
        _fail("BAMF_PLANNER_PROJECTION_AUTHORITY_MISMATCH")


def validate_staged_receipt(
    snapshot: CurriculumSnapshot,
    selection: FrontierDeltaSelection | None,
    receipt: StagedSelectionReceipt | None,
    current_release: ExecutableFactoryRelease | None,
    selected_projection: TargetDeltaProjection | None,
) -> None:
    if receipt is None:
        return
    receipt.verify()
    if (selection is None
            or receipt.selection != selection
            or receipt.predecessor_release != current_release
            or receipt.projection != selected_projection
            or receipt.staged_successor_sha256
               not in snapshot.staged_factory_release_sha256s):
        _fail("BAMF_PLANNER_STAGED_SELECTION_MISMATCH")


def requested_keys(
    receipts: tuple[StagedSelectionReceipt, ...] | list[StagedSelectionReceipt],
) -> set[tuple[str, str]]:
    return {(receipt.selected_semantic_id,
             obligation_digest(receipt.selection.selected_obligations))
            for receipt in receipts}


def has_unrequested_ready(
    closure: FrontierClosure,
    requested: set[tuple[str, str]],
    current: dict[str, str],
) -> bool:
    for semantic_id in closure.constituent_order:
        rows = tuple(
            row for row in closure.candidates if row.semantic_id == semantic_id)
        if (rows and all(row.status is ClosureStatus.READY for row in rows)
                and (semantic_id, current[semantic_id]) not in requested):
            return True
    return False
