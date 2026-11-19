"""Temporary lawful teaching window after active-grade recovery exhaustion."""
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.autonomy import evidence_complete_capabilities
from bilqis_mlx.runtime.lawful_teaching_frontier_contracts import _issue_frontier
from bilqis_mlx.runtime.lawful_teaching_frontier_projection import (
    _recovery_yield_capabilities,
    _recovery_yield_exclusions,
)


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def issue_recovery_yield_teaching_frontier(
        active_frontier, epoch, cadence_authorization):
    """Open one temporary next-grade window without changing active-grade custody."""
    from bilqis_mlx.runtime.active_grade_cadence_contracts import (
        ActiveGradeCadenceAuthorization,
        ActiveGradeCadenceDisposition,
    )
    if (
        type(cadence_authorization) is not ActiveGradeCadenceAuthorization
        or cadence_authorization.disposition
           is not ActiveGradeCadenceDisposition.RECOVERY_EXHAUSTED
        or cadence_authorization.authorized_capability_ids
        or cadence_authorization.state.active_grade_activation_sha256
           != active_frontier.active_grade_activation_sha256
        or cadence_authorization.state.active_grade_definition_sha256
           != active_frontier.active_grade_definition_sha256
    ):
        _invalid("BAMF_RECOVERY_YIELD_AUTHORITY_REQUIRED")
    release = epoch.current_release
    mastered = evidence_complete_capabilities(
        release, epoch.evidence_ledger,
        plan=epoch.autonomy_plan,
        current_checkpoint_sha256=epoch.checkpoint.sha256,
        current_optimizer_step=epoch.checkpoint.optimizer_step,
    )
    active_capability_ids = tuple(dict.fromkeys(
        capability_id
        for capability_id, _semantic_id in active_frontier.active_grade_members
    ))
    capabilities = _recovery_yield_capabilities(
        release, epoch.snapshot, epoch.closure, epoch.autonomy_plan, mastered,
        active_capability_ids=active_capability_ids,
    )
    if not capabilities:
        return None
    return _issue_frontier(
        run_id=active_frontier.run_id,
        accepted_generation=active_frontier.accepted_generation,
        accepted_manifest_sha256=active_frontier.accepted_manifest_sha256,
        accepted_correction_frontier_sha256=(
            active_frontier.accepted_correction_frontier_sha256),
        accepted_checkpoint_sha256=active_frontier.accepted_checkpoint_sha256,
        accepted_optimizer_step=active_frontier.accepted_optimizer_step,
        candidate_identity_sha256=active_frontier.candidate_identity_sha256,
        admitted_release_sha256=active_frontier.admitted_release_sha256,
        admission_receipt_sha256=active_frontier.admission_receipt_sha256,
        a09_snapshot_sha256=active_frontier.a09_snapshot_sha256,
        a09_closure_sha256=active_frontier.a09_closure_sha256,
        prerequisite_evidence_sha256=active_frontier.prerequisite_evidence_sha256,
        autonomy_plan_sha256=active_frontier.autonomy_plan_sha256,
        autonomy_evidence_sha256=active_frontier.autonomy_evidence_sha256,
        rights_epoch=active_frontier.rights_epoch,
        correction_generation=active_frontier.correction_generation,
        policy_epoch=active_frontier.policy_epoch,
        source_authority_registry_sha256=(
            active_frontier.source_authority_registry_sha256),
        active_grade_activation_sha256=(
            active_frontier.active_grade_activation_sha256),
        active_grade_definition_sha256=(
            active_frontier.active_grade_definition_sha256),
        active_grade_members=active_frontier.active_grade_members,
        active_grade_state=active_frontier.active_grade_state,
        capabilities=capabilities,
        exclusions=_recovery_yield_exclusions(
            active_frontier, release, capabilities),
        _source_context=active_frontier._source_context,
        _parent=active_frontier._parent,
        _planning_generation=active_frontier._planning_generation,
        _autonomy_currentness=active_frontier._autonomy_currentness,
        _active_grade_currentness=active_frontier._active_grade_currentness,
    )
