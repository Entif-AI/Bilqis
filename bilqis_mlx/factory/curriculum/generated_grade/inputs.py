"""Authority-bound #1320 inputs derived from the existing A09 state machine."""
from __future__ import annotations
import hashlib
from bilqis_mlx.factory.atlas_delta_scope import AtlasDeltaScopeHandoff
from bilqis_mlx.factory.atlas_frontier import AtlasCoverageEpoch, AtlasLearnerEvidence, next_atlas_delta
from bilqis_mlx.factory.atlas_frontier_progress import FrontierStatus, plan_frontier_progress
from bilqis_mlx.factory.atlas_frontier_progress_validation import credited_obligation_keys, current_obligations
from bilqis_mlx.factory.autonomy import AutonomyPlan, evidence_complete_capabilities
from bilqis_mlx.factory.atlas_frontier_contracts import _bytes, _fail
from .contracts import AcceptedLearnerFoot, GeneratedGradeInputs, GeneratedGradePolicy, _issue_inputs
from .proposal_contracts import GENERATED_GRADE_INPUTS_V1, GENERATED_GRADE_INPUTS_V2
from .cost_inputs import _measured_acquisition_cost, _measured_cost_profile
from .development_inputs import _development_evidence

def _a09_baselines(epoch: AtlasCoverageEpoch) -> tuple[str, ...]:
    current = current_obligations(epoch.closure)
    keys = set()
    if epoch.accepted_credit is not None:
        keys.update(key for key in epoch.accepted_credit.obligation_keys
                    if current.get(key[0]) == key[1])
    if epoch.prior is not None:
        keys.update(credited_obligation_keys(
            epoch.snapshot, epoch.closure, epoch.prior, current))
    return tuple(sorted(identity for identity, _digest in keys))

def _learner_foot(epoch, learner, plan) -> AcceptedLearnerFoot:
    mastered = evidence_complete_capabilities(
        epoch.current_release, learner.ledger, plan=plan,
        current_checkpoint_sha256=learner.checkpoint_sha256,
        current_optimizer_step=learner.optimizer_step)
    evidence_sha256 = hashlib.sha256(_bytes({
        "ledger": learner.ledger, "checkpoint": learner.checkpoint_sha256,
        "optimizer_step": learner.optimizer_step, "plan": plan.digest(),
        "baselines": _a09_baselines(epoch),
    })).hexdigest()
    return AcceptedLearnerFoot(
        learner.checkpoint_sha256, learner.optimizer_step,
        epoch.current_release.release_sha256, epoch.snapshot.policy_epoch,
        epoch.snapshot.qualification_epoch, _a09_baselines(epoch),
        tuple(sorted(mastered)), evidence_sha256)

def _a09_receipt(epoch, learner, plan):
    result = next_atlas_delta(epoch, learner, plan)
    if isinstance(result, AtlasDeltaScopeHandoff):
        result.verify()
        progress = plan_frontier_progress(
            epoch.snapshot, epoch.closure, result.receipt.selection,
            current_release=epoch.current_release,
            selected_projection=result.receipt.projection,
            prior=epoch.prior, staged_receipt=result.receipt)
        return (
            progress, progress.status.value, result.handoff_sha256,
            result.proposal.proposal_sha256,
        )
    status = result if isinstance(result, FrontierStatus) else FrontierStatus.FIXED_POINT
    return None, status.value, None, None


def _compile_generated_grade_inputs(
    epoch: AtlasCoverageEpoch,
    learner: AtlasLearnerEvidence,
    plan: AutonomyPlan,
    *,
    predecessor_certification_sha256: str | None = None,
) -> GeneratedGradeInputs:
    """Internal issuer; production callers enter through accepted runtime custody."""
    if (type(epoch) is not AtlasCoverageEpoch or type(learner) is not AtlasLearnerEvidence
            or type(plan) is not AutonomyPlan):
        _fail("BAMF_GENERATED_GRADE_AUTHORITY_INPUT_INVALID")
    epoch.verify()
    if (learner.ledger.factory_release_sha256 != epoch.current_release.release_sha256
            or learner.ledger.autonomy_plan_sha256 != plan.digest()
            or plan.factory_release_sha256 != epoch.current_release.release_sha256):
        _fail("BAMF_GENERATED_GRADE_AUTHORITY_MISMATCH")
    foot = _learner_foot(epoch, learner, plan)
    policy = GeneratedGradePolicy(
        "a09-393-pareto-cohort/v2",
        max(1, epoch.snapshot.budget.max_candidates),
        max(0, min(
            epoch.snapshot.budget.max_candidates,
            epoch.snapshot.budget.max_identity_rows,
        ) - 1),
        epoch.snapshot.policy_epoch)
    evidence = _development_evidence(epoch, foot, learner, plan)
    progress, status, handoff_sha256, a09_proposal_sha256 = _a09_receipt(
        epoch, learner, plan)
    progress_sha256 = progress.progress_sha256 if progress is not None else None
    schema = (
        GENERATED_GRADE_INPUTS_V2
        if predecessor_certification_sha256 is not None
        else GENERATED_GRADE_INPUTS_V1)
    common = dict(
        learner=foot, candidate_evidence=evidence, policy=policy,
        a09_progress_sha256=progress_sha256, a09_status=status,
        a09_handoff_sha256=handoff_sha256,
        a09_proposal_sha256=(a09_proposal_sha256 if handoff_sha256 else None),
        predecessor_certification_sha256=predecessor_certification_sha256,
        schema=schema)
    payload = {
        "learner": foot, "candidate_evidence": evidence, "policy": policy,
        "a09_progress_sha256": progress_sha256, "a09_status": status,
        "a09_handoff_sha256": handoff_sha256,
        "a09_proposal_sha256": (a09_proposal_sha256 if handoff_sha256 else None),
        "schema": schema,
    }
    if predecessor_certification_sha256 is not None:
        payload["predecessor_certification_sha256"] = predecessor_certification_sha256
    expected = hashlib.sha256(_bytes(payload)).hexdigest()
    return _issue_inputs(**common, input_sha256=expected)
