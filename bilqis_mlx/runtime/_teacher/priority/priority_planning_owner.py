"""Accepted A09 planning projection consumed by C03.4 priority authority."""
from dataclasses import dataclass
from pathlib import Path

from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _emit_progress(progress, message):
    if progress is not None:
        progress(message)


@dataclass(frozen=True)
class PriorityPlanningEpoch:
    current_release: object
    candidate_set: object
    snapshot: object
    closure: object
    requested_keys: tuple
    autonomy_plan: object
    evidence_ledger: object
    checkpoint: object
    source_authority: object


def build_priority_planning_epoch(
        run_dir, source_context, atlas_artifact_path, progress=None, *,
        authenticated_features=None):
    """Derive the exact accepted A09 epoch once for planning/frontier consumers."""
    from bilqis_mlx.factory.atlas_delta_adapter import (
        AtlasCoverageEpoch, _accepted_requested_keys,
    )
    from bilqis_mlx.factory.atlas_frontier import PlannerBudget
    from bilqis_mlx.factory.atlas_frontier_closure import resolve_frontier_closure
    from bilqis_mlx.factory.atlas_runtime_snapshot import build_accepted_executable_snapshot
    from bilqis_mlx.factory.skos_curriculum import (
        LearnedFrontier, SOURCE_FAMILY_ADAPTERS,
        _compile_semantic_curriculum_snapshot, compile_semantic_curriculum,
        issue_source_context_transition_authority,
    )
    from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_obligation_credit
    from bilqis_mlx.runtime.atlas_flywheel_runtime import (
        _accepted_checkpoint, _accepted_selection, _candidate_frontier,
        _persist_ready_realizations,
    )
    from bilqis_mlx.runtime._autonomy_live.planning import (
        build_live_autonomy_plan, reconcile_live_autonomy_state,
    )

    _emit_progress(progress, "planner: resolving accepted atlas selection")
    if authenticated_features is None:
        selection, feature_receipt = _accepted_selection(run_dir)
        atlas_snapshot = None
    else:
        selection = authenticated_features.selection
        feature_receipt = authenticated_features.receipt
        atlas_snapshot = authenticated_features.snapshot
    if Path(selection.path).resolve() != Path(atlas_artifact_path).resolve():
        _invalid("BAMF_PRIORITY_ATLAS_SELECTION_DRIFT")
    current = source_context.release
    if selection.release_sha256 != feature_receipt.source_release_sha256:
        _invalid("BAMF_PRIORITY_ATLAS_RELEASE_DRIFT")
    _emit_progress(progress, "planner: compiling semantic curriculum")
    frontier_state = LearnedFrontier(selection.release_sha256)
    candidate = (_compile_semantic_curriculum_snapshot(
        atlas_snapshot, SOURCE_FAMILY_ADAPTERS, frontier_state)
        if atlas_snapshot is not None else compile_semantic_curriculum(
            selection, SOURCE_FAMILY_ADAPTERS, frontier_state))
    source = issue_source_context_transition_authority(selection)
    frontier = _candidate_frontier(
        run_dir, current.release_sha256, progress=progress)
    _emit_progress(progress, "planner: staging source-valid candidate realizations")
    staged = _persist_ready_realizations(
        run_dir, current, candidate, frontier, source_context.graph)
    _emit_progress(progress, "planner: reconciling accepted planning state")
    plan = build_live_autonomy_plan(current, source_context.source_root)
    ledger = reconcile_live_autonomy_state(run_dir, current, plan)
    checkpoint = _accepted_checkpoint(run_dir)
    _emit_progress(progress, "planner: building bounded executable snapshot")
    snapshot = build_accepted_executable_snapshot(
        candidate, source.frontier, source.policy, frontier, current, staged,
        budget=PlannerBudget(9, 16, 1000),
        admission_receipt_sha256=feature_receipt.acceptance_sha256,
        grade_labels=tuple(grade.grade_id for grade in current.execution_plan.grades),
    )
    _emit_progress(progress, "planner: resolving frontier closure")
    closure = resolve_frontier_closure(
        snapshot, candidate.census, current_release=current,
        evidence_ledger=ledger, autonomy_plan=plan,
        checkpoint_sha256=checkpoint.sha256,
        optimizer_step=checkpoint.optimizer_step,
    )
    epoch = AtlasCoverageEpoch(
        snapshot, closure, frontier, current, staged,
        accepted_credit=read_accepted_atlas_obligation_credit(run_dir))
    epoch.verify()
    return PriorityPlanningEpoch(
        current, candidate, snapshot, closure, _accepted_requested_keys(epoch),
        plan, ledger, checkpoint, source)


def priority_planning_from_epoch(epoch, *, progress=None):
    """Project C03 planning from one already-derived accepted A09 epoch."""
    from bilqis_mlx.factory import candidate_realizations
    from bilqis_mlx.factory.atlas_frontier_progress import plan_frontier_progress
    from bilqis_mlx.factory.atlas_frontier_selection import (
        ranked_frontier_target, select_frontier_delta_for_projection,
    )
    from bilqis_mlx.runtime.priority_qualification import PriorityPlanningInput

    if type(epoch) is not PriorityPlanningEpoch:
        _invalid("BAMF_PRIORITY_PLANNING_EPOCH_INVALID")
    current = epoch.current_release
    candidate = epoch.candidate_set
    snapshot = epoch.snapshot
    closure = epoch.closure
    requested = epoch.requested_keys
    selected = projection = None
    _emit_progress(progress, "planner: ranking next bounded target")
    try:
        semantic_id, rows = ranked_frontier_target(snapshot, closure, requested)
    except BilqisError as error:
        if error.context.get("reason") != "BAMF_PLANNER_NO_BOUNDED_READY_DELTA":
            raise
    else:
        try:
            projection = candidate_realizations.project_authoritative_target(
                semantic_id, current, rows)
        except ValueError:
            _invalid("BAMF_PRIORITY_A09_REALIZATION_MISSING")
        selected = select_frontier_delta_for_projection(
            snapshot, closure, current, projection, requested)
    planning_progress = plan_frontier_progress(
        snapshot, closure, selected,
        current_release=current if selected is not None else None,
        selected_projection=projection)
    _emit_progress(progress, "planner: candidate frontier ready")
    return PriorityPlanningInput(planning_progress, closure, selected, projection)


def priority_planning(run_dir, source_context, atlas_artifact_path, *, progress=None):
    """Project current A09 state from accepted custody without requiring a C07 lease."""
    epoch = build_priority_planning_epoch(
        Path(run_dir), source_context, atlas_artifact_path, progress)
    return priority_planning_from_epoch(epoch, progress=progress)


__all__ = (
    "PriorityPlanningEpoch",
    "build_priority_planning_epoch",
    "priority_planning",
    "priority_planning_from_epoch",
)
