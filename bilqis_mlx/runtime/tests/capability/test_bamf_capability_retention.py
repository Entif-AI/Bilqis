"""Complete-solver assessment and advisory retention with source fixtures."""
from dataclasses import replace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.capability_retention import (
    AssessmentPair, CompleteSolver, EvaluationCase, EvaluationCohort,
    EvidenceKind, EvidenceStage, PairedRetentionEvidence, RetentionPolicy,
    candidate_work_disposition, case_census_digest, configuration_outcome, evaluate_capabilities, retain_candidate,
    evaluate_retention_candidate,
)
import bilqis_mlx.runtime.capability_retention_foundation as foundation_module
import bilqis_mlx.runtime.capability_retention as retention_module
from bilqis_mlx.runtime.cognitive_solver import NeuralProposal, SolveBudget, SolveContext
from bilqis_mlx.semantics.cognitive_dag import DAGBudget, DAGNode
from bilqis_mlx.semantics.cognitive_operators import TypedValue
from bilqis_mlx.semantics.tests.test_cognitive_dag import _goal, _literal, _program, _result
from bilqis_mlx.semantics.tests.test_cognitive_operators import RELEASE, SCOPE, _case, _with_frame, _grant
from bilqis_mlx.semantics.context_eligibility import frame_evidence_digest, member_evidence_digest
from bilqis_mlx.semantics.frame_schema import FrameSchema, RoleSpec, make_frame_instance

PARENT = "a" * 64
CANDIDATE = "b" * 64


from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    _cases, _solver, _evidence, _rescore, _repolicy, _screen_inputs,
)











class CapabilityRetentionTests(unittest.TestCase):
    def test_foundation_authorizing_screen_skips_measure_only_fresh_cohorts(self):
        parent_solver, candidate_solver, target, policy, cohorts = _screen_inputs(
            protected_loss=3)
        cohorts = tuple(replace(
            cohort, evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION)
            for cohort in cohorts)
        observed = []
        original = foundation_module.evaluate_capabilities

        def traced(solver, cohort, generation):
            observed.append(cohort.kind)
            return original(solver, cohort, generation)

        with patch.object(foundation_module, "evaluate_capabilities", side_effect=traced):
            decision = evaluate_retention_candidate(
                parent_solver, candidate_solver, target, policy, cohorts,
                PARENT, CANDIDATE)

        self.assertEqual(decision.reason, "PROTECTED_CAPABILITY_REGRESSION")
        self.assertEqual(observed, [EvidenceKind.FIXED_SCHOOL, EvidenceKind.FIXED_SCHOOL])
        self.assertEqual(decision.blocking_capability, "protected")

    def test_foundation_acceptance_uses_fixed_school_only(self):
        parent_solver, candidate_solver, target, policy, cohorts = _screen_inputs(
            protected_loss=0)
        cohorts = tuple(replace(
            cohort, evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION)
            for cohort in cohorts)
        observed = []
        original = foundation_module.evaluate_capabilities

        def traced(solver, cohort, generation):
            observed.append(cohort.kind)
            return original(solver, cohort, generation)

        with patch.object(foundation_module, "evaluate_capabilities", side_effect=traced):
            decision = evaluate_retention_candidate(
                parent_solver, candidate_solver, target, policy, cohorts,
                PARENT, CANDIDATE)

        self.assertEqual(decision.reason, "PAIRED_SCREEN_WITHIN_BUDGET")
        self.assertEqual(observed, [EvidenceKind.FIXED_SCHOOL] * 6)
        self.assertIsNone(decision.blocking_capability)

    def test_strict_generalization_keeps_complete_paired_screen(self):
        parent_solver, candidate_solver, target, policy, cohorts = _screen_inputs(
            protected_loss=3)
        observed = []
        original = retention_module.evaluate_capabilities

        def traced(solver, cohort, generation):
            observed.append(cohort.kind)
            return original(solver, cohort, generation)

        with patch.object(retention_module, "evaluate_capabilities", side_effect=traced):
            decision = evaluate_retention_candidate(
                parent_solver, candidate_solver, target, policy, cohorts,
                PARENT, CANDIDATE)

        self.assertEqual(decision.reason, "PROTECTED_CAPABILITY_REGRESSION")
        self.assertEqual(observed, [
            EvidenceKind.FRESH_TARGET, EvidenceKind.FRESH_TARGET,
            EvidenceKind.FRESH_LESSON, EvidenceKind.FRESH_LESSON,
            EvidenceKind.FIXED_SCHOOL, EvidenceKind.FIXED_SCHOOL,
        ])

    def test_fresh_protected_loss_cannot_hide_behind_target_gain(self):
        evidence = _evidence()
        fresh = _rescore(evidence.fresh_lesson,
                         {"target": 0, "protected": 3},
                         {"target": 3, "protected": 2})
        evidence = replace(evidence, fresh_lesson=fresh)
        self.assertEqual(retain_candidate(PARENT, CANDIDATE, evidence).reason,
                         "PROTECTED_CAPABILITY_REGRESSION")

    def test_bilateral_row_truncation_rejects_under_frozen_policy(self):
        evidence = _evidence()
        pair = evidence.fixed_school
        cases = pair.parent.cohort.cases[:4] + pair.parent.cohort.cases[-1:]
        with self.assertRaises(BilqisError):
            replace(pair.parent.cohort, cases=cases)
        truncated = replace(pair.parent.cohort, cases=cases,
                            expected_case_digest=case_census_digest(cases))
        results_before = pair.parent.results[:4] + pair.parent.results[-1:]
        results_after = pair.candidate.results[:4] + pair.candidate.results[-1:]
        contracts = pair.parent.solver_contracts[:4] + pair.parent.solver_contracts[-1:]
        shortened = AssessmentPair(
            replace(pair.parent, cohort=truncated, results=results_before,
                    solver_contracts=contracts),
            replace(pair.candidate, cohort=truncated, results=results_after,
                    solver_contracts=contracts))
        with self.assertRaises(BilqisError):
            replace(evidence, fixed_school=shortened)

    def test_each_aggregate_gate_preserves_native_reason_precedence(self):
        base = _evidence()
        policy = replace(base.policy, protected_reference_losses=(("other", 6), ("protected", 6)))
        base = _repolicy(base, policy)
        fresh = _rescore(base.fresh_lesson, {"protected": 3}, {"target": 1})
        self.assertEqual(retain_candidate(PARENT, CANDIDATE,
            replace(base, fresh_lesson=fresh)).reason, "SAME_GRADE_NET_REGRESSION")
        fixed = _rescore(base.fixed_school, {"protected": 12, "other": 1},
                         {"target": 3, "protected": 7, "other": 1})
        self.assertEqual(retain_candidate(PARENT, CANDIDATE,
            replace(base, fixed_school=fixed)).reason, "FIXED_LESSON_GRADE_REGRESSION")
        fixed = _rescore(base.fixed_school, {"protected": 12, "other": 1},
                         {"target": 3, "protected": 12})
        self.assertEqual(retain_candidate(PARENT, CANDIDATE,
            replace(base, fixed_school=fixed)).reason, "ACTIVE_SCHOOL_GRADE_REGRESSION")
        school = _repolicy(base, replace(policy, protected_groups=("amber",)))
        fixed = _rescore(school.fixed_school, {"protected": 12, "other": 1},
                         {"protected": 12})
        self.assertEqual(retain_candidate(PARENT, CANDIDATE,
            replace(school, fixed_school=fixed)).reason, "WHOLE_SCHOOL_NET_REGRESSION")



    def test_complete_solver_gain_and_scaled_protected_loss_allowance(self):
        evidence = _evidence()
        decision = retain_candidate(PARENT, CANDIDATE, evidence)
        self.assertEqual(decision.status, "ELIGIBLE")
        self.assertEqual(decision.reason, "PAIRED_SCREEN_WITHIN_BUDGET")
        self.assertEqual(evidence.target.parent.score("target"), (0, 3))
        self.assertEqual(evidence.target.candidate.score("target"), (3, 3))
        self.assertEqual(evidence.fixed_school.candidate.score("protected"), (10, 12))
        self.assertEqual(retain_candidate(PARENT, CANDIDATE, _evidence(3)).reason,
                         "PROTECTED_CAPABILITY_REGRESSION")

    def test_configuration_receipt_never_fabricates_optimizer_steps(self):
        evidence = _evidence()
        receipt = configuration_outcome(evidence.target)
        self.assertEqual(receipt.schema_version, "bilqis.c05.configuration-outcome/v1")
        self.assertEqual(receipt.net_correct_delta, 3)
        self.assertEqual(receipt.optimizer_steps, 0)
        self.assertFalse(hasattr(receipt, "retained"))

    def test_label_permutation_preserves_decision(self):
        left = retain_candidate(PARENT, CANDIDATE, _evidence())
        right = retain_candidate(PARENT, CANDIDATE, _evidence(labels=("violet", "amber")))
        self.assertEqual((left.status, left.reason), (right.status, right.reason))

    def test_no_fresh_gain_rejects_without_mutating_evidence(self):
        evidence = _evidence()
        same = replace(evidence.target.candidate,
                       results=tuple(replace(result, generation_digest=CANDIDATE)
                                     for result in evidence.target.parent.results))
        evidence = replace(evidence, target=AssessmentPair(evidence.target.parent, same))
        before = evidence.digest()
        self.assertEqual(retain_candidate(PARENT, CANDIDATE, evidence).reason,
                         "NO_MEASURABLE_TARGET_GAIN")
        self.assertEqual(evidence.digest(), before)

    def test_foundation_stage_does_not_require_fresh_target_gain(self):
        evidence = _evidence()
        same = replace(
            evidence.target.candidate,
            results=tuple(replace(result, generation_digest=CANDIDATE)
                          for result in evidence.target.parent.results),
        )
        target = AssessmentPair(evidence.target.parent, same)

        def staged(pair):
            cohort = replace(
                pair.parent.cohort,
                evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
            )
            return AssessmentPair(
                replace(pair.parent, cohort=cohort),
                replace(pair.candidate, cohort=cohort),
            )

        evidence = replace(
            evidence,
            target=staged(target),
            fresh_lesson=staged(evidence.fresh_lesson),
            fixed_school=staged(evidence.fixed_school),
        )
        decision = retain_candidate(PARENT, CANDIDATE, evidence)
        self.assertEqual(decision.status, "ELIGIBLE")
        self.assertEqual(decision.reason, "PAIRED_SCREEN_WITHIN_BUDGET")

    def test_foundation_stage_ignores_fresh_variant_regression_but_keeps_fixed_school(self):
        evidence = _evidence()

        def staged(pair):
            cohort = replace(
                pair.parent.cohort,
                evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
            )
            return AssessmentPair(
                replace(pair.parent, cohort=cohort),
                replace(pair.candidate, cohort=cohort),
            )

        fresh = _rescore(
            evidence.fresh_lesson,
            {"target": 0, "protected": 3},
            {"target": 0, "protected": 2},
        )
        foundation = replace(
            evidence,
            target=staged(evidence.target),
            fresh_lesson=staged(fresh),
            fixed_school=staged(evidence.fixed_school),
        )
        self.assertEqual(
            retain_candidate(PARENT, CANDIDATE, foundation).reason,
            "PAIRED_SCREEN_WITHIN_BUDGET",
        )

        fixed = _rescore(
            evidence.fixed_school,
            {"protected": 12},
            {"protected": 10},
        )
        foundation = replace(foundation, fixed_school=staged(fixed))
        self.assertNotEqual(
            retain_candidate(PARENT, CANDIDATE, foundation).reason,
            "PAIRED_SCREEN_WITHIN_BUDGET",
        )



    def test_perfect_exact_target_skips_optimizer_candidate(self):
        cases, contexts = _cases("target", "any-label", 3, "exact")
        exact = tuple(replace(case, goal=replace(case.goal, expression_or_holes=_program(
            replace(case.goal.expression_or_holes.nodes[0], operator_id="ADD",
                    candidate_operator_ids=())))) for case in cases)
        cohort = EvaluationCohort(
            EvidenceKind.FRESH_TARGET, exact, (("target", "any-label"),),
            "d" * 64, "e" * 64, "f" * 64, "0" * 64, (), (), case_census_digest(exact))
        solver = CompleteSolver(lambda goal, generation: SolveContext(contexts[goal.goal_id]),
                                SolveBudget(DAGBudget()))
        assessment = evaluate_capabilities(solver, cohort, PARENT)
        self.assertEqual(assessment.score("target"), (3, 3))
        self.assertEqual(candidate_work_disposition(assessment, "target"),
                         "REHEARSE_OR_ADVANCE")
        self.assertTrue(all(result.neural_calls == 0 for result in assessment.results))
