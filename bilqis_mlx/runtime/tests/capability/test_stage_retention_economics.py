"""#1330 stage-authoritative C05 retention economics."""
from dataclasses import replace

from bilqis_mlx.runtime.capability_retention import (
    AssessmentPair,
    EvidenceStage,
    retain_candidate,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    CANDIDATE,
    PARENT,
    _evidence,
)
from bilqis_mlx.learning.retention_policy import mastery_debt_utility
from bilqis_mlx.learning.retention_policy import (
    RetentionDecisionLaw,
    decision_law_for_stage,
    stage_retention_policy,
)
from bilqis_mlx.runtime.retention.protection_plan_compiler import policy_epoch_sha256


def _with_stage(evidence, stage):
    def staged(pair):
        cohort = replace(pair.parent.cohort, evidence_stage=stage)
        return AssessmentPair(
            replace(pair.parent, cohort=cohort),
            replace(pair.candidate, cohort=cohort),
        )

    return replace(
        evidence,
        target=staged(evidence.target),
        fresh_lesson=staged(evidence.fresh_lesson),
        fixed_school=staged(evidence.fixed_school),
    )


def test_same_candidate_evidence_obeys_declared_stage_law_for_future_grade():
    evidence = _evidence(3, labels=("future-grade-z", "prior-grade"))

    strict = retain_candidate(PARENT, CANDIDATE, evidence)
    foundation = retain_candidate(
        PARENT,
        CANDIDATE,
        _with_stage(evidence, EvidenceStage.FOUNDATION_ACQUISITION),
    )

    assert strict.reason == "PROTECTED_CAPABILITY_REGRESSION"
    assert foundation.reason == "PAIRED_SCREEN_WITHIN_BUDGET"
    assert strict.evaluated_capability_ids == ("target", "protected", "other")
    assert strict.blocking_score_budget == ("protected", 12, 9, 12, 2)


def test_stage_policy_is_versioned_and_bound_into_policy_epoch():
    policy = stage_retention_policy()

    assert policy.schema_version == "bilqis.c05.stage-retention-policy/v1"
    assert decision_law_for_stage(EvidenceStage.FOUNDATION_ACQUISITION) is (
        RetentionDecisionLaw.FOUNDATION_MASTERY_DEBT)
    assert decision_law_for_stage(EvidenceStage.STRICT_GENERALIZATION) is (
        RetentionDecisionLaw.STRICT_PROPORTIONAL)
    assert policy_epoch_sha256(EvidenceStage.FOUNDATION_ACQUISITION) != (
        policy_epoch_sha256(EvidenceStage.STRICT_GENERALIZATION))


def test_foundation_utility_negative_trade_rejects():
    evidence = _with_stage(
        _evidence(12, labels=("future-grade-z", "prior-grade")),
        EvidenceStage.FOUNDATION_ACQUISITION,
    )

    decision = retain_candidate(PARENT, CANDIDATE, evidence)

    assert decision.reason == "PROTECTED_CAPABILITY_REGRESSION"
    assert decision.blocking_capability == "protected"


def test_foundation_stage_does_not_require_fresh_target_gain():
    evidence = _evidence()
    same = replace(
        evidence.target.candidate,
        results=tuple(replace(result, generation_digest=CANDIDATE)
                      for result in evidence.target.parent.results),
    )
    target = AssessmentPair(evidence.target.parent, same)
    foundation = _with_stage(
        replace(evidence, target=target), EvidenceStage.FOUNDATION_ACQUISITION)

    decision = retain_candidate(PARENT, CANDIDATE, foundation)

    assert decision.status.value == "ELIGIBLE"
    assert decision.reason == "PAIRED_SCREEN_WITHIN_BUDGET"


def test_quadratic_mastery_debt_values_weak_gain_over_near_mastery_loss():
    trade = mastery_debt_utility({
        "weak": {"before": 57, "after": 60, "total": 100},
        "near_mastery": {"before": 98, "after": 93, "total": 100},
    })
    assert trade["net"] > 0
    assert trade["capabilities"]["weak"]["utility_delta"] == 0.0249
    assert trade["capabilities"]["near_mastery"]["utility_delta"] == -0.0045


def test_quadratic_mastery_debt_rejects_same_raw_trade_against_weak_donor():
    trade = mastery_debt_utility({
        "weak": {"before": 57, "after": 60, "total": 100},
        "donor": {"before": 70, "after": 65, "total": 100},
    })
    assert trade["net"] < 0
