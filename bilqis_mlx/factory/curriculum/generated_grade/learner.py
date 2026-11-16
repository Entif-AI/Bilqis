"""Project accepted autonomy evidence into the #1320 learner-relative foot."""
from __future__ import annotations

import hashlib

from bilqis_mlx.factory.atlas_delta_adapter import AtlasLearnerEvidence
from bilqis_mlx.factory.atlas_frontier_contracts import CurriculumSnapshot, _bytes, _fail
from bilqis_mlx.factory.autonomy import AutonomyPlan, evidence_complete_capabilities
from bilqis_mlx.factory.executable_release import ExecutableFactoryRelease

from .contracts import AcceptedLearnerFoot, CandidateDevelopmentEvidence


def accepted_learner_foot(
    snapshot: CurriculumSnapshot,
    release: ExecutableFactoryRelease,
    learner: AtlasLearnerEvidence,
    plan: AutonomyPlan,
    candidate_evidence: tuple[CandidateDevelopmentEvidence, ...],
) -> AcceptedLearnerFoot:
    """Derive mastery only from current accepted evidence, never self-assertion."""
    if (type(snapshot) is not CurriculumSnapshot
            or not isinstance(release, ExecutableFactoryRelease)
            or type(learner) is not AtlasLearnerEvidence
            or type(plan) is not AutonomyPlan
            or type(candidate_evidence) is not tuple
            or any(type(item) is not CandidateDevelopmentEvidence
                   for item in candidate_evidence)):
        _fail("BAMF_GENERATED_GRADE_LEARNER_INPUT_INVALID")
    snapshot.verify()
    release.verify()
    if (snapshot.admitted_factory_release_sha256 != release.release_sha256
            or learner.ledger.factory_release_sha256 != release.release_sha256
            or learner.ledger.autonomy_plan_sha256 != plan.digest()
            or plan.factory_release_sha256 != release.release_sha256):
        _fail("BAMF_GENERATED_GRADE_LEARNER_AUTHORITY_MISMATCH")
    mastered_capabilities = evidence_complete_capabilities(
        release,
        learner.ledger,
        plan=plan,
        current_checkpoint_sha256=learner.checkpoint_sha256,
        current_optimizer_step=learner.optimizer_step,
    )
    mastered_set = set(mastered_capabilities)
    mastered_semantics = tuple(sorted(
        item.semantic_id
        for item in candidate_evidence
        if item.compiled_capability_ids
        and set(item.compiled_capability_ids) <= mastered_set
    ))
    evidence_sha256 = hashlib.sha256(_bytes({
        "ledger": learner.ledger,
        "checkpoint_sha256": learner.checkpoint_sha256,
        "optimizer_step": learner.optimizer_step,
        "plan_sha256": plan.digest(),
    })).hexdigest()
    return AcceptedLearnerFoot(
        learner.checkpoint_sha256,
        learner.optimizer_step,
        release.release_sha256,
        snapshot.policy_epoch,
        snapshot.qualification_epoch,
        mastered_semantics,
        tuple(mastered_capabilities),
        evidence_sha256,
    )
