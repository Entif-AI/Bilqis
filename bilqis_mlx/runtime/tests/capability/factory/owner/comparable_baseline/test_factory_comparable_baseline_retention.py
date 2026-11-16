"""#1298 C05 decisions use only established comparable baseline members."""
from dataclasses import replace
import unittest

from bilqis_mlx.runtime.baseline.currentness import BaselineCoverage
from bilqis_mlx.runtime.capability_retention import (
    EvidenceStage,
    case_census_digest,
    evaluate_retention_candidate,
)
from bilqis_mlx.runtime.capability_retention_foundation import (
    FoundationRetentionPolicy,
    evaluate_foundation_fixed_school_candidate,
)
from bilqis_mlx.runtime.retention.local_evaluation import (
    evaluate_foundation_local_candidate,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    CANDIDATE,
    PARENT,
    _screen_inputs,
)


def _coverage(measured):
    census = ("target", "protected", "other")
    measured = tuple(capability for capability in census if capability in measured)
    unmeasured = tuple(capability for capability in census if capability not in measured)
    measured_set = set(measured)
    return BaselineCoverage(
        measured,
        unmeasured,
        (
            ("amber", sum(item in measured_set for item in ("target", "protected")), 2),
            ("violet", int("other" in measured_set), 1),
        ),
        len(measured),
        3,
        "e" * 64,
    )


def _foundation_inputs(
        *, protected_loss, measured, target_gain=True,
        labels=("amber", "violet")):
    parent, candidate, target, base_policy, cohorts = _screen_inputs(
        protected_loss=protected_loss, labels=labels)
    if not target_gain:
        candidate = parent
    coverage = _coverage(measured)
    protected = coverage.protected_capabilities(target)
    policy = FoundationRetentionPolicy(
        base_policy.capability_groups,
        base_policy.protected_groups,
        tuple((capability, 1) for capability in protected),
        base_policy.probe_each,
        cohorts[2].expected_case_digest,
        coverage,
    )
    fixed = replace(
        cohorts[2],
        evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
        policy_sha256=policy.digest(),
    )
    return parent, candidate, target, policy, fixed


def _local_foundation_inputs(*, protected_loss, measured):
    parent, candidate, target, base_policy, cohorts = _screen_inputs(
        protected_loss=protected_loss)
    groups = base_policy.capability_groups[:2]
    measured = tuple(item for item in ("target", "protected") if item in measured)
    measured_set = set(measured)
    coverage = BaselineCoverage(
        measured,
        tuple(item for item in ("target", "protected") if item not in measured_set),
        (("amber", len(measured), 2),),
        len(measured),
        2,
        "e" * 64,
    )
    cases = tuple(
        case for case in cohorts[2].cases
        if case.capability_id in {"target", "protected"})
    policy = FoundationRetentionPolicy(
        groups,
        ("amber",),
        (("protected", 1),) if "protected" in measured_set else (),
        base_policy.probe_each,
        case_census_digest(cases),
        coverage,
    )
    fixed = replace(
        cohorts[2],
        cases=cases,
        capability_groups=groups,
        expected_case_digest=case_census_digest(cases),
        evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
        policy_sha256=policy.digest(),
    )
    return parent, candidate, target, policy, fixed


class FactoryComparableBaselineRetentionTests(unittest.TestCase):
    def test_first_zero_delta_target_measurement_establishes_baseline_candidate(self):
        for target_group in ("amber", "Z"):
            with self.subTest(target_group=target_group):
                args = _foundation_inputs(
                    protected_loss=0,
                    measured=(),
                    target_gain=False,
                    labels=(target_group, "violet"),
                )

                decision = evaluate_foundation_fixed_school_candidate(
                    *args, PARENT, CANDIDATE)

                self.assertEqual(decision.status.value, "ELIGIBLE")
                self.assertEqual(decision.reason, "PAIRED_SCREEN_WITHIN_BUDGET")
                self.assertEqual(decision.baseline_coverage.measured_denominator, 0)

    def test_first_target_measurement_ignores_unmeasured_peer_regressions(self):
        args = _foundation_inputs(protected_loss=12, measured=())

        decision = evaluate_foundation_fixed_school_candidate(
            *args, PARENT, CANDIDATE)

        self.assertEqual(decision.status.value, "ELIGIBLE")
        self.assertEqual(decision.reason, "PAIRED_SCREEN_WITHIN_BUDGET")
        self.assertEqual(decision.baseline_coverage.measured_denominator, 0)
        self.assertEqual(
            decision.baseline_coverage.unmeasured_capabilities,
            ("target", "protected", "other"),
        )

    def test_first_new_target_still_rejects_damage_to_established_protected_capability(self):
        args = _foundation_inputs(protected_loss=12, measured=("protected",))

        decision = evaluate_foundation_fixed_school_candidate(
            *args, PARENT, CANDIDATE)

        self.assertEqual(decision.status.value, "REJECT")
        self.assertEqual(decision.reason, "PROTECTED_CAPABILITY_REGRESSION")
        self.assertEqual(decision.blocking_capability, "protected")
        self.assertEqual(decision.baseline_coverage.measured_capabilities, ("protected",))

    def test_aggregate_veto_uses_only_measured_denominator(self):
        args = _foundation_inputs(protected_loss=3, measured=("protected",))

        decision = evaluate_foundation_fixed_school_candidate(
            *args, PARENT, CANDIDATE)

        self.assertEqual(decision.status.value, "REJECT")
        self.assertEqual(decision.reason, "FIXED_LESSON_GRADE_REGRESSION")
        self.assertEqual(decision.blocking_scope, "fixed_group:amber")
        self.assertEqual(
            decision.baseline_coverage.group_denominators,
            (("amber", 1, 2), ("violet", 0, 1)),
        )

    def test_strict_target_regression_remains_rejected_after_baseline(self):
        parent, candidate, target, policy, cohorts = _screen_inputs(protected_loss=0)
        coverage = _coverage(("target", "protected", "other"))
        policy = replace(policy, baseline_coverage=coverage)
        cohorts = tuple(replace(cohort, policy_sha256=policy.digest()) for cohort in cohorts)

        decision = evaluate_retention_candidate(
            candidate, parent, target, policy, cohorts, PARENT, CANDIDATE)

        self.assertEqual(decision.status.value, "REJECT")
        self.assertEqual(decision.reason, "TARGET_BASELINE_REGRESSION")
        self.assertEqual(decision.blocking_capability, target)

    def test_local_plan_reports_exact_evaluated_ids_and_protected_veto(self):
        args = _local_foundation_inputs(
            protected_loss=12, measured=("protected",))

        decision = evaluate_foundation_local_candidate(
            *args, PARENT, CANDIDATE,
            retention_protection_plan_sha256="1" * 64,
            evaluated_capability_ids=("target", "protected"))

        self.assertEqual(decision.reason, "PROTECTED_CAPABILITY_REGRESSION")
        self.assertEqual(decision.blocking_capability, "protected")
        self.assertEqual(
            decision.evaluated_capability_ids, ("target", "protected"))
        self.assertEqual(
            decision.retention_protection_plan_sha256, "1" * 64)

    def test_local_plan_does_not_apply_whole_grade_aggregate_veto(self):
        args = _local_foundation_inputs(
            protected_loss=3, measured=("protected",))

        decision = evaluate_foundation_local_candidate(
            *args, PARENT, CANDIDATE,
            retention_protection_plan_sha256="2" * 64,
            evaluated_capability_ids=("target", "protected"))

        self.assertEqual(decision.reason, "PAIRED_SCREEN_WITHIN_BUDGET")
        self.assertIsNone(decision.blocking_scope)


if __name__ == "__main__":
    unittest.main()
