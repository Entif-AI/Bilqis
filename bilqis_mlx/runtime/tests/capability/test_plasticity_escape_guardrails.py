"""#1331 conditional strict plasticity and certified-surface debt guardrails."""
from dataclasses import replace

from bilqis_mlx.runtime.baseline.currentness import BaselineCoverage
from bilqis_mlx.runtime.capability_retention import retain_candidate
from bilqis_mlx.runtime.plasticity_escape import (
    CertifiedSurfaceDebt,
    CertifiedSurfaceId,
    PlasticityActivationReason,
    PlasticityEscapeState,
    derive_plasticity_escape_state,
    settle_accepted_escape,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    CANDIDATE,
    PARENT,
    _evidence,
    _repolicy,
    _rescore,
)
from bilqis_mlx.runtime.retention.protection_plan_compiler import policy_epoch_sha256
from bilqis_mlx.runtime.capability_retention import EvidenceStage


def _active_state():
    return PlasticityEscapeState(
        policy_epoch_sha256=policy_epoch_sha256(EvidenceStage.STRICT_GENERALIZATION),
        target_capability_id="target",
        active=True,
        activation_reasons=(PlasticityActivationReason.LOCAL_STARVATION,),
        attempts_since_retained=32,
        school_attempts_since_retained=7,
    )


def _surface(capability="protected"):
    return CertifiedSurfaceId(
        "certification:future-surface",
        capability,
        "3" * 64,
        "4" * 64,
        "5" * 64,
        policy_epoch_sha256(EvidenceStage.STRICT_GENERALIZATION),
        "6" * 64,
        "7" * 64,
    )


def test_strict_escape_is_conditional_and_can_relax_positive_mastery_debt_trade():
    evidence = _evidence(3, labels=("future-grade-z", "prior-certified-surface"))

    ordinary = retain_candidate(PARENT, CANDIDATE, evidence)
    escaped = retain_candidate(
        PARENT, CANDIDATE, evidence, plasticity_escape=_active_state())

    assert ordinary.reason == "PROTECTED_CAPABILITY_REGRESSION"
    assert escaped.reason == "PAIRED_SCREEN_WITHIN_BUDGET"


def test_strict_escape_cannot_bootstrap_an_unmeasured_target_baseline():
    evidence = _evidence(3, labels=("future-grade-z", "prior-certified-surface"))
    coverage = BaselineCoverage(
        ("protected", "other"),
        ("target",),
        (("future-grade-z", 1, 2), ("prior-certified-surface", 1, 1)),
        2,
        3,
        "2" * 64,
    )
    evidence = _repolicy(evidence, replace(evidence.policy, baseline_coverage=coverage))

    decision = retain_candidate(
        PARENT, CANDIDATE, evidence, plasticity_escape=_active_state())

    assert decision.reason == "PLASTICITY_TARGET_BASELINE_UNMEASURED"


def test_hard_certified_surface_debt_ceiling_remains_a_veto_during_escape():
    evidence = _evidence(3, labels=("future-grade-z", "prior-certified-surface"))
    evidence = replace(
        evidence,
        fixed_school=_rescore(
            evidence.fixed_school,
            {"target": 0, "protected": 8, "other": 1},
            {"target": 3, "protected": 5, "other": 1},
        ),
    )
    active = replace(
        _active_state(), debt=(CertifiedSurfaceDebt(_surface(), 4, 12, 12),))

    decision = retain_candidate(
        PARENT, CANDIDATE, evidence, plasticity_escape=active)

    assert decision.reason == "CERTIFIED_SURFACE_DEBT_LIMIT"


def test_debt_at_or_above_ceiling_may_repair_without_blocking_escape():
    evidence = _evidence(3, labels=("future-grade-z", "prior-certified-surface"))
    active = replace(
        _active_state(), debt=(CertifiedSurfaceDebt(_surface("target"), 5, 3, 3),))

    decision = retain_candidate(
        PARENT, CANDIDATE, evidence, plasticity_escape=active)

    assert decision.reason == "PAIRED_SCREEN_WITHIN_BUDGET"


def test_repair_threshold_blocks_repeated_escape_without_debt_progress():
    evidence = _evidence(3, labels=("future-grade-z", "prior-certified-surface"))
    active = replace(
        _active_state(),
        debt=(CertifiedSurfaceDebt(_surface("other"), 2, 3, 3),))

    decision = retain_candidate(
        PARENT, CANDIDATE, evidence, plasticity_escape=active)

    assert decision.reason == "CERTIFIED_SURFACE_REPAIR_DUE"


def test_future_grade_activation_is_policy_data_driven_and_measured():
    scope = "factory/future"
    health = {
        "by_capability": {
            "target": {"latest": {"correct": 4, "total": 10}},
            "peer": {"latest": {"correct": 8, "total": 10}},
        }
    }
    teacher = {"causal_experiment": {
        "capability_stagnation": {
            "target|" + scope: {"attempts_since_retained": 16},
        },
        "school_attempts_since_retained": 24,
    }}
    state = derive_plasticity_escape_state(
        teacher, health,
        target_capability_id="target",
        target_group_id="grade:future",
        frontier_group_id="grade:future",
        phase="MAIN",
        curriculum_scope=scope,
        policy_epoch_sha256=policy_epoch_sha256(
            EvidenceStage.STRICT_GENERALIZATION),
    )

    assert state.active is True
    assert state.activation_reasons == (
        PlasticityActivationReason.LOCAL_STARVATION,
        PlasticityActivationReason.SCHOOL_RETENTION_DROUGHT_BELOW_MEAN,
    )
    assert state.attempts_since_retained == 16
    assert state.school_attempts_since_retained == 24


def test_activation_fails_closed_without_authoritative_measured_target():
    scope = "factory/future"
    teacher = {"causal_experiment": {
        "capability_stagnation": {
            "target|" + scope: {"attempts_since_retained": 99},
        },
        "school_attempts_since_retained": 99,
    }}
    state = derive_plasticity_escape_state(
        teacher, {"by_capability": {"peer": {
            "latest": {"correct": 8, "total": 10}}}},
        target_capability_id="target",
        target_group_id="grade:future",
        frontier_group_id="grade:future",
        phase="RECOVERY_1",
        curriculum_scope=scope,
        policy_epoch_sha256=policy_epoch_sha256(
            EvidenceStage.STRICT_GENERALIZATION),
    )

    assert state.active is False
    assert state.activation_reasons == ()


def test_legacy_underidentified_certified_surface_cannot_be_borrowed_against():
    scope = "factory/future"
    teacher = {"causal_experiment": {
        "capability_stagnation": {
            "target|" + scope: {"attempts_since_retained": 16},
        },
    }}
    health = {
        "by_capability": {
            "target": {"latest": {"correct": 4, "total": 10}},
            "protected": {"latest": {"correct": 12, "total": 12}},
        },
        "certified_surfaces": [{
            "surface_id": "legacy:certification",
            "capability_id": "protected",
            "rubric_sha256": "5" * 64,
            "source_sha256": "6" * 64,
            "fixed_cohort_sha256": "7" * 64,
            "retention_policy_sha256": "8" * 64,
            "certified_checkpoint_sha256": "9" * 64,
            "state": "MEASURED", "after": 12, "total": 12,
        }],
    }
    active = derive_plasticity_escape_state(
        teacher, health, target_capability_id="target",
        target_group_id="grade:future", frontier_group_id="grade:future",
        phase="MAIN", curriculum_scope=scope,
        policy_epoch_sha256=policy_epoch_sha256(
            EvidenceStage.STRICT_GENERALIZATION))
    evidence = _evidence(3, labels=("grade:future", "prior:certified"))

    decision = retain_candidate(
        PARENT, CANDIDATE, evidence, plasticity_escape=active)

    assert active.unqualified_debt_capability_ids == ("protected",)
    assert decision.reason == "CERTIFIED_SURFACE_DEBT_IDENTITY_REQUIRED"


def test_foundation_retention_remains_independent_of_escape_state():
    evidence = _evidence(3, labels=("future-grade-z", "prior-certified-surface"))

    def staged(pair):
        cohort = replace(
            pair.parent.cohort,
            evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION)
        return type(pair)(
            replace(pair.parent, cohort=cohort),
            replace(pair.candidate, cohort=cohort))

    foundation = replace(
        evidence,
        target=staged(evidence.target),
        fresh_lesson=staged(evidence.fresh_lesson),
        fixed_school=staged(evidence.fixed_school),
    )
    ordinary = retain_candidate(PARENT, CANDIDATE, foundation)
    with_escape = retain_candidate(
        PARENT, CANDIDATE, foundation, plasticity_escape=_active_state())

    assert ordinary == with_escape


def test_accepted_escape_persists_certified_surface_debt_then_deactivates():
    active = _active_state()
    certified = {
        "surface_id": "certification:future-surface",
        "capability_id": "protected",
        "grade_definition_sha256": "3" * 64,
        "factory_release_sha256": "4" * 64,
        "rubric_sha256": "5" * 64,
        "policy_epoch_sha256": policy_epoch_sha256(
            EvidenceStage.STRICT_GENERALIZATION),
        "source_sha256": "6" * 64,
        "fixed_cohort_sha256": "7" * 64,
        "retention_policy_sha256": "8" * 64,
        "certified_checkpoint_sha256": "9" * 64,
        "state": "MEASURED",
        "after": 12,
        "total": 12,
    }
    visit = {
        "capability_id": "target",
        "rubric_sha256": "5" * 64,
        "source_sha256": "6" * 64,
        "fixed_cohort_sha256": "7" * 64,
        "retention_policy_sha256": "8" * 64,
        "learning_target": {"state": "MEASURED", "after": 3, "total": 3},
        "protected": [{
            "capability_id": "protected", "state": "MEASURED",
            "after": 9, "total": 12, "delta": -3,
        }],
    }

    settled = settle_accepted_escape(
        active, visit, (certified,), accepted_optimizer_step=42)

    assert settled.active is False
    assert settled.deactivated is True
    assert settled.attempts_since_retained == 0
    assert settled.school_attempts_since_retained == 0
    assert settled.last_repair_opportunity == 42
    assert len(settled.debt) == 1
    assert settled.debt[0].amount == 3
    assert settled.debt[0].surface.capability_id == "protected"
    assert PlasticityEscapeState.from_record(settled.to_record()) == settled

    evidence = _evidence(3, labels=("future-grade-z", "prior-certified-surface"))
    next_decision = retain_candidate(
        PARENT, CANDIDATE, evidence, plasticity_escape=settled)
    assert next_decision.reason == "PROTECTED_CAPABILITY_REGRESSION"


def test_later_measured_repair_reduces_certified_surface_debt():
    active = _active_state()
    certified = {
        "surface_id": "certification:future-surface",
        "capability_id": "protected",
        "grade_definition_sha256": "3" * 64,
        "factory_release_sha256": "4" * 64,
        "rubric_sha256": "5" * 64,
        "policy_epoch_sha256": policy_epoch_sha256(
            EvidenceStage.STRICT_GENERALIZATION),
        "source_sha256": "6" * 64,
        "fixed_cohort_sha256": "7" * 64,
        "retention_policy_sha256": "8" * 64,
        "certified_checkpoint_sha256": "9" * 64,
        "state": "MEASURED", "after": 12, "total": 12,
    }
    regression = {
        "capability_id": "target",
        "rubric_sha256": "5" * 64, "source_sha256": "6" * 64,
        "fixed_cohort_sha256": "7" * 64,
        "retention_policy_sha256": "8" * 64,
        "protected": [{
            "capability_id": "protected", "after": 9, "total": 12, "delta": -3,
        }],
    }
    debt = settle_accepted_escape(
        active, regression, (certified,), accepted_optimizer_step=42)
    repair = replace(debt, deactivated=False)
    repaired_visit = {
        **regression,
        "protected": [{
            "capability_id": "protected", "after": 11, "total": 12, "delta": 2,
        }],
    }

    repaired = settle_accepted_escape(
        repair, repaired_visit, (certified,), accepted_optimizer_step=43)

    assert repaired.debt[0].amount == 1
    assert repaired.last_repair_opportunity == 43
