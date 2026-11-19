"""Revalidate learner-relative lawful teaching frontier currentness."""
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.lawful_teaching_frontier_contracts import _is_issued
from bilqis_mlx.runtime.lawful_teaching_frontier_projection import _evidence_digest

from .lawful_teaching_frontier_issue import _source_authority


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def _frontier_checkpoint_identity(
        source_context, parent, planning_generation, currentness_step):
    if currentness_step is not None:
        return (
            planning_generation.parent_candidate_identity_sha256,
            parent.retained_state.optimizer_step,
        )
    from bilqis_mlx.runtime.atlas_flywheel_runtime import _accepted_checkpoint
    checkpoint = _accepted_checkpoint(Path(source_context.run_dir))
    return checkpoint.sha256, checkpoint.optimizer_step


def _frontier_autonomy_identity(frontier, source_context, currentness_step):
    if currentness_step is None:
        from bilqis_mlx.runtime.autonomy_state import read_autonomy_state
        plan, ledger = read_autonomy_state(
            Path(source_context.run_dir), source_context.release)
        return plan.digest(), _evidence_digest(plan, ledger)
    from bilqis_mlx.runtime.frontier_autonomy_currentness import (
        _require_autonomy_currentness,
    )
    try:
        _require_autonomy_currentness(
            frontier._autonomy_currentness, source_context.release)
    except ValueError:
        _invalid("BAMF_LEARNER_FRONTIER_STALE")
    return frontier.autonomy_plan_sha256, frontier.autonomy_evidence_sha256


def _frontier_active_grade(
        frontier, source_context, parent, planning_generation, currentness_step):
    root = Path(source_context.run_dir)
    if currentness_step is None or frontier._active_grade_currentness is None:
        from bilqis_mlx.runtime.active_generated_grade import (
            read_active_generated_grade,
        )
        return read_active_generated_grade(root)
    from bilqis_mlx.runtime.active_generated_grade import (
        _read_bound_active_generated_grade,
    )
    return _read_bound_active_generated_grade(
        root,
        expected_activation_sha256=frontier.active_grade_activation_sha256,
        expected_definition_sha256=frontier.active_grade_definition_sha256,
        currentness_step=currentness_step,
        currentness_transaction=planning_generation._accepted_currentness,
        parent=parent,
        active_currentness=frontier._active_grade_currentness,
    )


def _require_lawful_teaching_frontier(
        frontier, source_context, parent, *, refresh_accepted,
        currentness_step=None):
    """Validate frontier derivation; optionally refresh mutable B13 custody."""
    if (
        not _is_issued(frontier)
        or frontier._source_context is not source_context
        or frontier._parent is not parent
    ):
        _invalid("BAMF_LEARNER_FRONTIER_INVALID")
    planning_generation = frontier._planning_generation
    if refresh_accepted:
        from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
            refresh_accepted_currentness,
        )
        currentness_step = refresh_accepted_currentness(
            planning_generation._accepted_currentness, parent)
    if currentness_step is not None:
        from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
            require_accepted_currentness_step,
        )
        require_accepted_currentness_step(
            currentness_step, planning_generation._accepted_currentness, parent)
    from bilqis_mlx.runtime.priority_source_offer import (
        _require_planning_generation,
    )
    _require_planning_generation(planning_generation, source_context, parent)
    checkpoint_sha256, optimizer_step = _frontier_checkpoint_identity(
        source_context, parent, planning_generation, currentness_step)
    autonomy_plan_sha256, autonomy_evidence_sha256 = _frontier_autonomy_identity(
        frontier, source_context, currentness_step)
    source = _source_authority(planning_generation)
    active_grade = _frontier_active_grade(
        frontier, source_context, parent, planning_generation, currentness_step)
    if (
        frontier.run_id != parent.run_id
        or frontier.accepted_generation != parent.generation
        or frontier.accepted_manifest_sha256
           != planning_generation.accepted_manifest_sha256
        or frontier.accepted_correction_frontier_sha256
           != planning_generation.correction_frontier_sha256
        or frontier.candidate_identity_sha256
           != planning_generation.parent_candidate_identity_sha256
        or frontier.admitted_release_sha256
           != source_context.release.release_sha256
        or frontier.accepted_checkpoint_sha256 != checkpoint_sha256
        or frontier.accepted_optimizer_step != optimizer_step
        or frontier.autonomy_plan_sha256 != autonomy_plan_sha256
        or frontier.autonomy_evidence_sha256 != autonomy_evidence_sha256
        or frontier.policy_epoch != source.policy.policy_epoch
        or frontier.rights_epoch != source.frontier.rights_epoch
        or frontier.correction_generation
           != source.frontier.correction_generation
        or frontier.source_authority_registry_sha256
           != source.authority_registry_sha256
        or frontier.active_grade_activation_sha256
           != active_grade.activation_sha256
        or frontier.active_grade_definition_sha256
           != active_grade.definition.definition_sha256
        or frontier.active_grade_members != tuple(
            (member.capability_id, member.semantic_id)
            for member in active_grade.definition.members)
    ):
        _invalid("BAMF_LEARNER_FRONTIER_STALE")
    return frontier


def require_bound_lawful_teaching_frontier(
        frontier, source_context, parent, *, currentness_step=None):
    """Revalidate non-neural frontier owners without a full B13 refresh."""
    return _require_lawful_teaching_frontier(
        frontier, source_context, parent, refresh_accepted=False,
        currentness_step=currentness_step)


def require_current_lawful_teaching_frontier(
        frontier, source_context, parent):
    """Fail closed if any accepted learner/source/policy/evidence owner moved."""
    return _require_lawful_teaching_frontier(
        frontier, source_context, parent, refresh_accepted=True)
