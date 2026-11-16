"""A09.3 pure semantic selection for the existing JIT delta boundary.

This module does not stage a successor, mutate the snapshot cursor, or admit
anything.  A09.5 owns translating this semantic selection into the existing
``CurriculumDeltaProposal`` candidate/binding surface.
"""
from __future__ import annotations

from dataclasses import replace
from .atlas_frontier_closure import CandidateClosure, ClosureReason, ClosureStatus, FrontierClosure
from .atlas_frontier_contracts import CurriculumSnapshot, _bytes, _fail
from .executable_release import ExecutableFactoryRelease
from .atlas_frontier_selection_validation import (
    TargetDeltaProjection,
    target_projections,
    validate_closure_structure,
    validate_target_projection,
)

from .atlas_frontier_ranking import (
    A09_FRONTIER_COMPARATOR_ORDER, DeferredClosure, FrontierDeltaSelection,
    _ancestors, _candidate_signature, _graph, _grouped, _marginal_unlocks,
    _ranked_ready_targets, frontier_target_metrics,
)


def ranked_frontier_target(
    snapshot: CurriculumSnapshot, closure: FrontierClosure,
    requested_obligation_keys: tuple[tuple[str, str], ...] = (),
) -> tuple[str, tuple[CandidateClosure, ...]]:
    """Return the exact #393 winner without requiring realization evidence."""
    snapshot.verify()
    closure.verify()
    validate_closure_structure(snapshot, closure)
    _, ranked = _ranked_ready_targets(
        snapshot, closure, requested_obligation_keys)
    if not ranked:
        _fail("BAMF_PLANNER_NO_BOUNDED_READY_DELTA")
    _, _, _, identity, rows = min(ranked)
    return identity, rows


def validate_frontier_selection(
    snapshot: CurriculumSnapshot,
    closure: FrontierClosure,
    selection: FrontierDeltaSelection,
    current_release: ExecutableFactoryRelease,
    selected_projection: TargetDeltaProjection,
) -> None:
    """Prove a supplied selection is the exact lawful A09.3 choice and projection."""
    snapshot.verify()
    closure.verify()
    selection.verify()
    current_release.verify()
    validate_closure_structure(snapshot, closure)
    if (closure.snapshot_sha256 != snapshot.snapshot_sha256
            or selection.snapshot_sha256 != snapshot.snapshot_sha256
            or selection.closure_sha256 != closure.closure_sha256
            or selection.admitted_release_sha256
               != snapshot.admitted_factory_release_sha256
            or current_release.release_sha256
               != snapshot.admitted_factory_release_sha256
            or selection.policy_epoch != snapshot.policy_epoch
            or selection.cursor != snapshot.cursor):
        _fail("BAMF_PLANNER_SELECTION_INVALID")
    _, ranked = _ranked_ready_targets(
        snapshot, closure, selection.requested_obligation_keys)
    if not ranked:
        _fail("BAMF_PLANNER_SELECTION_INVALID")
    slope, neg_unlocks, _, identity, rows = min(ranked)
    selected_keys = {(item.semantic_id, item.family_id) for item in rows}
    deferred = tuple(sorted(DeferredClosure(
        item.semantic_id,
        item.family_id,
        item.status,
        item.reasons,
    ) for item in closure.candidates
        if (item.semantic_id, item.family_id) not in selected_keys))
    signature = _candidate_signature(
        identity, rows,
        selection.introduced_capability_ids,
        selection.introduced_semantic_ids,
    )
    validate_target_projection(current_release, rows, selected_projection)
    capability_limit = min(9, snapshot.budget.max_candidates)
    if (selection.selected_semantic_id != identity
            or selection.selected_obligations != rows
            or selected_projection.semantic_id != identity
            or selection.introduced_capability_ids
               != selected_projection.added_capability_ids
            or selection.introduced_semantic_ids
               != selected_projection.introduced_semantic_ids
            or selection.prerequisite_slope != slope
            or selection.downstream_unlocks != -neg_unlocks
            or selection.deferred != deferred
            or selection.candidate_signature != signature
            or len(selection.introduced_capability_ids) > capability_limit
            or len(selection.introduced_semantic_ids) > snapshot.budget.max_identity_rows):
        _fail("BAMF_PLANNER_SELECTION_INVALID")


def select_frontier_delta_for_projection(
    snapshot: CurriculumSnapshot,
    closure: FrontierClosure,
    current_release: ExecutableFactoryRelease,
    projection: TargetDeltaProjection,
    requested_obligation_keys: tuple[tuple[str, str], ...] = (),
) -> FrontierDeltaSelection:
    """Apply the unchanged #393 comparator to one code-owned winner projection.

    This narrow A09.5 seam exists so an unavailable lower-ranked realization
    cannot force the adapter to invent a projection merely to prove which
    semantic target #393 ranks first.
    """
    if (type(snapshot) is not CurriculumSnapshot
            or type(closure) is not FrontierClosure
            or not isinstance(current_release, ExecutableFactoryRelease)
            or type(projection) is not TargetDeltaProjection):
        _fail("BAMF_PLANNER_SELECTION_INPUT_INVALID")
    snapshot.verify()
    closure.verify()
    current_release.verify()
    projection.verify()
    if (closure.snapshot_sha256 != snapshot.snapshot_sha256
            or snapshot.admitted_factory_release_sha256 != current_release.release_sha256):
        _fail("BAMF_PLANNER_SELECTION_PREDECESSOR_MISMATCH")
    validate_closure_structure(snapshot, closure)
    identity, rows = ranked_frontier_target(
        snapshot, closure, requested_obligation_keys)
    capability_limit = min(9, snapshot.budget.max_candidates)
    identity_limit = snapshot.budget.max_identity_rows
    if capability_limit < 1:
        _fail("BAMF_PLANNER_DELTA_BUDGET_EXHAUSTED")
    graph = _graph(closure)
    groups = _grouped(closure)
    slope = len(_ancestors(identity, graph))
    neg_unlocks = -_marginal_unlocks(identity, groups)
    if projection.semantic_id != identity:
        _fail("BAMF_PLANNER_SELECTION_INVALID")
    validate_target_projection(current_release, rows, projection)
    capabilities = projection.added_capability_ids
    introduced = projection.introduced_semantic_ids
    if len(capabilities) > capability_limit or len(introduced) > identity_limit:
        _fail("BAMF_PLANNER_CONSTITUENT_SPLIT_REQUIRED")
    selected_keys = {(item.semantic_id, item.family_id) for item in rows}
    deferred = tuple(sorted(DeferredClosure(
        item.semantic_id,
        item.family_id,
        item.status,
        item.reasons,
    ) for item in closure.candidates
        if (item.semantic_id, item.family_id) not in selected_keys))
    provisional = FrontierDeltaSelection(
        snapshot.snapshot_sha256,
        closure.closure_sha256,
        current_release.release_sha256,
        snapshot.policy_epoch,
        snapshot.cursor,
        identity,
        rows,
        capabilities,
        introduced,
        slope,
        -neg_unlocks,
        deferred,
        requested_obligation_keys,
        _candidate_signature(identity, rows, capabilities, introduced),
        "0" * 64,
    )
    result = replace(provisional, selection_sha256=provisional.expected_digest())
    result.verify()
    return result


def select_frontier_delta(
    snapshot: CurriculumSnapshot,
    closure: FrontierClosure,
    current_release: ExecutableFactoryRelease,
    projections: tuple[TargetDeltaProjection, ...],
) -> FrontierDeltaSelection:
    """Select one bounded semantic target without staging or adopting it."""
    if (type(snapshot) is not CurriculumSnapshot
            or type(closure) is not FrontierClosure
            or not isinstance(current_release, ExecutableFactoryRelease)):
        _fail("BAMF_PLANNER_SELECTION_INPUT_INVALID")
    snapshot.verify()
    closure.verify()
    current_release.verify()
    if (closure.snapshot_sha256 != snapshot.snapshot_sha256
            or snapshot.admitted_factory_release_sha256 != current_release.release_sha256):
        _fail("BAMF_PLANNER_SELECTION_PREDECESSOR_MISMATCH")
    validate_closure_structure(snapshot, closure)
    projections_by_identity = target_projections(closure, current_release, projections)
    _, ranked = _ranked_ready_targets(snapshot, closure)
    if not ranked:
        _fail("BAMF_PLANNER_NO_BOUNDED_READY_DELTA")
    identity = min(ranked)[3]
    return select_frontier_delta_for_projection(
        snapshot, closure, current_release, projections_by_identity[identity])
