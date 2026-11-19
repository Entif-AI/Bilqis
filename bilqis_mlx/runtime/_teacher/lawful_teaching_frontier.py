"""Issue and revalidate the current learner-relative teaching frontier."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL
from bilqis_mlx.factory.autonomy import evidence_complete_capabilities

from bilqis_mlx.runtime.lawful_teaching_frontier_contracts import (
    ActiveGeneratedGradeState,
    LawfulTeachingFrontier,
    LawfulTeachingCapability,
    LawfulTeachingDisposition,
    LawfulTeachingExclusion,
    LawfulTeachingExclusionCode,
    LawfulTeachingHold,
    _is_issued,
    _issue_frontier,
)
from bilqis_mlx.runtime.lawful_teaching_frontier_projection import (
    _active_grade_state,
    _active_member_projection,
    _capabilities,
    _evidence_digest,
    _exclusions,
)


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def _source_authority(planning_generation):
    from bilqis_mlx.factory.skos_curriculum import (
        issue_source_context_transition_authority,
    )
    return issue_source_context_transition_authority(
        planning_generation._authenticated_features.selection)


def _validate_epoch(epoch, planning_generation, source_context, parent):
    release = source_context.release
    snapshot, closure = epoch.snapshot, epoch.closure
    release.verify()
    snapshot.verify()
    closure.verify()
    source = _source_authority(planning_generation)
    if (
        epoch.current_release.release_sha256 != release.release_sha256
        or snapshot.admitted_factory_release_sha256 != release.release_sha256
        or closure.snapshot_sha256 != snapshot.snapshot_sha256
        or snapshot.rights_epoch != source.frontier.rights_epoch
        or snapshot.correction_generation
           != source.frontier.correction_generation
        or snapshot.policy_epoch != source.policy.policy_epoch
        or epoch.checkpoint.sha256
           != planning_generation.parent_candidate_identity_sha256
        or epoch.checkpoint.optimizer_step
           != parent.retained_state.optimizer_step
    ):
        _invalid("BAMF_LEARNER_FRONTIER_EPOCH_DRIFT")
    return source


def _bind_frontier_currentness(root, epoch, active_grade):
    from bilqis_mlx.runtime.frontier_autonomy_currentness import (
        _bind_autonomy_currentness,
    )
    from bilqis_mlx.runtime.active_generated_grade import (
        _bind_active_generated_grade_currentness,
    )
    autonomy = _bind_autonomy_currentness(
        root, epoch.current_release, plan=epoch.autonomy_plan,
        ledger=epoch.evidence_ledger)
    active_grade_witness = _bind_active_generated_grade_currentness(
        root, active_grade)
    return autonomy, active_grade_witness


def _issue_lawful_teaching_frontier_from_epoch(
        epoch, source_context, parent, planning_generation):
    """Seal one already-derived accepted A09 epoch for an internal consumer."""
    from bilqis_mlx.runtime.priority_planning_owner import PriorityPlanningEpoch
    if type(epoch) is not PriorityPlanningEpoch:
        _invalid("BAMF_LEARNER_FRONTIER_EPOCH_INVALID")
    source = _validate_epoch(
        epoch, planning_generation, source_context, parent)
    from bilqis_mlx.runtime.active_generated_grade import ensure_active_generated_grade
    root = Path(source_context.run_dir)
    try:
        active_grade = ensure_active_generated_grade(root)
    except BilqisError as failure:
        if (failure.context.get("reason")
                != "BAMF_ACTIVE_GENERATED_GRADE_ADMITTED_PROPOSAL_REQUIRED"):
            raise
        from bilqis_mlx.runtime.initial_grade_bootstrap import (
            activate_initial_grade_bootstrap,
        )
        active_grade = activate_initial_grade_bootstrap(root, epoch)
    active_grade_members = tuple(
        (member.capability_id, member.semantic_id)
        for member in active_grade.definition.members
    )
    autonomy_currentness, active_grade_currentness = _bind_frontier_currentness(
        root, epoch, active_grade)
    active_members = _active_member_projection(
        epoch.current_release, active_grade)
    mastered = evidence_complete_capabilities(
        epoch.current_release, epoch.evidence_ledger,
        plan=epoch.autonomy_plan,
        current_checkpoint_sha256=epoch.checkpoint.sha256,
        current_optimizer_step=epoch.checkpoint.optimizer_step)
    capabilities = _capabilities(
        epoch.current_release, epoch.snapshot, epoch.closure,
        epoch.autonomy_plan, mastered,
        active_members=active_members)
    planning_status = None
    if capabilities and all(
            item.disposition is LawfulTeachingDisposition.EVIDENCE_COMPLETE
            for item in capabilities):
        from bilqis_mlx.runtime.priority_planning_owner import (
            priority_planning_from_epoch,
        )
        planning_status = priority_planning_from_epoch(epoch).progress.status
    snapshot = epoch.snapshot
    if snapshot.admission_receipt_sha256 is None:
        _invalid("BAMF_LEARNER_FRONTIER_ADMISSION_RECEIPT_REQUIRED")
    return _issue_frontier(
        run_id=parent.run_id,
        accepted_generation=parent.generation,
        accepted_manifest_sha256=planning_generation.accepted_manifest_sha256,
        accepted_correction_frontier_sha256=(
            planning_generation.correction_frontier_sha256),
        accepted_checkpoint_sha256=epoch.checkpoint.sha256,
        accepted_optimizer_step=epoch.checkpoint.optimizer_step,
        candidate_identity_sha256=(
            planning_generation.parent_candidate_identity_sha256),
        admitted_release_sha256=epoch.current_release.release_sha256,
        admission_receipt_sha256=snapshot.admission_receipt_sha256,
        a09_snapshot_sha256=snapshot.snapshot_sha256,
        a09_closure_sha256=epoch.closure.closure_sha256,
        prerequisite_evidence_sha256=(
            epoch.closure.prerequisite_evidence_sha256),
        autonomy_plan_sha256=epoch.autonomy_plan.digest(),
        autonomy_evidence_sha256=_evidence_digest(
            epoch.autonomy_plan, epoch.evidence_ledger),
        rights_epoch=snapshot.rights_epoch,
        correction_generation=snapshot.correction_generation,
        policy_epoch=snapshot.policy_epoch,
        source_authority_registry_sha256=source.authority_registry_sha256,
        active_grade_activation_sha256=active_grade.activation_sha256,
        active_grade_definition_sha256=(
            active_grade.definition.definition_sha256),
        active_grade_members=active_grade_members,
        active_grade_state=_active_grade_state(capabilities, planning_status),
        capabilities=capabilities,
        exclusions=_exclusions(epoch.current_release, capabilities),
        _source_context=source_context,
        _parent=parent,
        _planning_generation=planning_generation,
        _autonomy_currentness=autonomy_currentness,
        _active_grade_currentness=active_grade_currentness,
    )


def issue_lawful_teaching_frontier(
        run_dir, source_context, parent, atlas_artifact_path, *,
        planning_generation=None, progress=None):
    """Issue a sealed frontier from current accepted learner/source/A09 owners."""
    from bilqis_mlx.runtime.priority_source_offer import (
        _require_planning_generation,
        bind_priority_planning_generation,
    )
    if planning_generation is None:
        planning_generation = bind_priority_planning_generation(
            source_context, parent, atlas_artifact_path)
    _require_planning_generation(planning_generation, source_context, parent)
    from bilqis_mlx.runtime.priority_planning_owner import (
        build_priority_planning_epoch,
    )
    epoch = build_priority_planning_epoch(
        run_dir, source_context, atlas_artifact_path, progress)
    return _issue_lawful_teaching_frontier_from_epoch(
        epoch, source_context, parent, planning_generation)


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


__all__ = (
    "ActiveGeneratedGradeState",
    "LawfulTeachingCapability",
    "LawfulTeachingDisposition",
    "LawfulTeachingExclusion",
    "LawfulTeachingExclusionCode",
    "LawfulTeachingFrontier",
    "LawfulTeachingHold",
    "issue_lawful_teaching_frontier",
    "require_bound_lawful_teaching_frontier",
    "require_current_lawful_teaching_frontier",
)
