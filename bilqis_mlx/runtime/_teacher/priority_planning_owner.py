"""Accepted A09 planning projection consumed by C03.4 priority authority."""
from pathlib import Path

from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def priority_planning(run_dir, source_context, atlas_artifact_path):
    """Project current A09 state from accepted custody without requiring a C07 lease."""
    from bilqis_mlx.factory import candidate_realizations
    from bilqis_mlx.factory.atlas_delta_adapter import (
        AtlasCoverageEpoch, _accepted_requested_keys,
    )
    from bilqis_mlx.factory.atlas_frontier import PlannerBudget
    from bilqis_mlx.factory.atlas_frontier_closure import resolve_frontier_closure
    from bilqis_mlx.factory.atlas_frontier_progress import plan_frontier_progress
    from bilqis_mlx.factory.atlas_frontier_selection import (
        ranked_frontier_target, select_frontier_delta_for_projection,
    )
    from bilqis_mlx.factory.atlas_runtime_snapshot import build_accepted_executable_snapshot
    from bilqis_mlx.factory.skos_curriculum import (
        LearnedFrontier, SOURCE_FAMILY_ADAPTERS, compile_semantic_curriculum,
        issue_source_context_transition_authority,
    )
    from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_obligation_credit
    from bilqis_mlx.runtime.atlas_flywheel_runtime import (
        _accepted_checkpoint, _accepted_selection, _candidate_frontier,
        _persist_ready_realizations,
    )
    from bilqis_mlx.runtime.autonomy_live import (
        build_live_autonomy_plan, reconcile_live_autonomy_state,
    )
    from bilqis_mlx.runtime.priority_qualification import PriorityPlanningInput

    run_dir = Path(run_dir)
    selection, feature_receipt = _accepted_selection(run_dir)
    if Path(selection.path).resolve() != Path(atlas_artifact_path).resolve():
        _invalid("BAMF_PRIORITY_ATLAS_SELECTION_DRIFT")
    current = source_context.release
    if selection.release_sha256 != feature_receipt.source_release_sha256:
        _invalid("BAMF_PRIORITY_ATLAS_RELEASE_DRIFT")
    candidate = compile_semantic_curriculum(
        selection, SOURCE_FAMILY_ADAPTERS,
        LearnedFrontier(selection.release_sha256))
    source = issue_source_context_transition_authority(selection)
    frontier = _candidate_frontier(run_dir)
    staged = _persist_ready_realizations(
        run_dir, current, candidate, frontier, source_context.graph)
    plan = build_live_autonomy_plan(current, source_context.source_root)
    ledger = reconcile_live_autonomy_state(run_dir, current, plan)
    checkpoint = _accepted_checkpoint(run_dir)
    snapshot = build_accepted_executable_snapshot(
        candidate, source.frontier, source.policy, frontier, current, staged,
        budget=PlannerBudget(9, 16, 1000),
        admission_receipt_sha256=feature_receipt.acceptance_sha256,
        grade_labels=tuple(grade.grade_id for grade in current.execution_plan.grades),
    )
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
    requested = _accepted_requested_keys(epoch)
    selected = projection = None
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
    progress = plan_frontier_progress(
        snapshot, closure, selected,
        current_release=current if selected is not None else None,
        selected_projection=projection)
    return PriorityPlanningInput(progress, closure, selected, projection)


__all__ = ("priority_planning",)
