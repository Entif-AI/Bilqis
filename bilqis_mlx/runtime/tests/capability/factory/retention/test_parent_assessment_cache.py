"""Generation-bound reuse contract for C05 fixed-school parent assessment."""
from dataclasses import replace
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_retention_decision import (
    issue_factory_retention_decision,
)
from bilqis_mlx.runtime.capability_retention import (
    CompleteSolver, DecisionStatus, EvidenceStage, evaluate_capabilities,
)
from bilqis_mlx.runtime.capability_retention_foundation import (
    FoundationRetentionPolicy, evaluate_foundation_fixed_school_candidate,
)
from bilqis_mlx.runtime._factory_parent_assessment_cache import (
    ParentAssessmentCacheIdentity,
    clear_parent_assessment_cache,
    use_parent_assessment,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    PARENT, _screen_inputs,
)
from bilqis_mlx.semantics.domains import contract_digest


def _identity(*, generation=7, policy="8" * 64, cohort="9" * 64,
              rubric="a" * 64, source="b" * 64):
    return ParentAssessmentCacheIdentity(
        run_id="run-parent-cache",
        accepted_generation=generation,
        accepted_manifest_sha256="1" * 64,
        accepted_generation_binding=PARENT,
        parent_generation_sha256=PARENT,
        parent_candidate_sha256="3" * 64,
        factory_release_sha256="4" * 64,
        semantic_catalog_sha256="5" * 64,
        source_authority_registry_sha256="6" * 64,
        fixed_cohort_sha256=cohort,
        rubric_sha256=rubric,
        source_sha256=source,
        policy_sha256=policy,
        implementation_sha256="c" * 64,
        topology_sha256="d" * 64,
        extents_sha256="e" * 64,
        correction_frontier_sha256="f" * 64,
        semantic_abi_sha256="0" * 64,
        compiler_features_sha256="7" * 64,
        evaluation_contract_sha256="8" * 64,
        evaluator_contract_sha256="9" * 64,
    )


class ParentAssessmentCacheTests(unittest.TestCase):
    def setUp(self):
        clear_parent_assessment_cache()

    def tearDown(self):
        clear_parent_assessment_cache()

    def test_exact_identity_reuses_parent_measurement_without_reexecution(self):
        parent_solver, _, _, _, cohorts = _screen_inputs()
        fixed = cohorts[2]
        calls = []

        def counted(goal, generation):
            calls.append(goal.goal_id)
            return parent_solver.context_for(goal, generation)

        solver = CompleteSolver(counted, parent_solver.budget)
        identity = _identity(cohort=contract_digest(fixed),
                             policy=fixed.policy_sha256,
                             rubric=fixed.rubric_sha256,
                             source=fixed.source_sha256)

        first, first_receipt = use_parent_assessment(
            identity, solver, fixed, PARENT)
        first_calls = tuple(calls)
        second, second_receipt = use_parent_assessment(
            identity, solver, fixed, PARENT)

        self.assertEqual(first.digest(), second.digest())
        self.assertEqual(tuple(calls), first_calls)
        self.assertEqual(len(first_calls), len(fixed.cases))
        self.assertFalse(first_receipt.reused)
        self.assertTrue(second_receipt.reused)
        self.assertEqual(first_receipt.cache_entry_sha256,
                         second_receipt.cache_entry_sha256)
        self.assertEqual(first_receipt.assessment_sha256, first.digest())
        with self.assertRaises(BilqisError):
            issue_factory_retention_decision(second_receipt)

    def test_rejected_then_new_candidate_reuses_parent_but_remeasures_candidate(self):
        parent_solver, candidate_solver, target, _, cohorts = _screen_inputs(
            protected_loss=12)
        fixed_source = cohorts[2]
        groups = fixed_source.capability_groups
        foundation_policy = FoundationRetentionPolicy(
            groups,
            tuple(dict.fromkeys(group for _, group in groups)),
            tuple((capability, 1) for capability, _ in groups
                  if capability != target),
            6,
            fixed_source.expected_case_digest,
        )
        fixed = replace(
            fixed_source,
            policy_sha256=foundation_policy.digest(),
            evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
        )
        uncached = evaluate_foundation_fixed_school_candidate(
            parent_solver, candidate_solver, target, foundation_policy, fixed,
            PARENT, "b" * 64)
        parent_calls, candidate_calls = [], []

        def count_parent(goal, generation):
            parent_calls.append(goal.goal_id)
            return parent_solver.context_for(goal, generation)

        def count_candidate(goal, generation):
            candidate_calls.append((generation, goal.goal_id))
            return candidate_solver.context_for(goal, generation)

        counted_parent = CompleteSolver(count_parent, parent_solver.budget)
        counted_candidate = CompleteSolver(
            count_candidate, candidate_solver.budget)
        identity = _identity(
            cohort=contract_digest(fixed),
            policy=fixed.policy_sha256,
            rubric=fixed.rubric_sha256,
            source=fixed.source_sha256,
        )
        parent_assessment, first_receipt = use_parent_assessment(
            identity, counted_parent, fixed, PARENT)
        first = evaluate_foundation_fixed_school_candidate(
            counted_parent, counted_candidate, target, foundation_policy, fixed,
            PARENT, "b" * 64, parent_assessment=parent_assessment)
        first_candidate_calls = len(candidate_calls)
        reused_parent, second_receipt = use_parent_assessment(
            identity, counted_parent, fixed, PARENT)
        second = evaluate_foundation_fixed_school_candidate(
            counted_parent, counted_candidate, target, foundation_policy, fixed,
            PARENT, "c" * 64, parent_assessment=reused_parent)

        self.assertEqual(first.status, DecisionStatus.REJECT)
        self.assertEqual(first, uncached)
        self.assertEqual(first.evidence_sha256, uncached.evidence_sha256)
        self.assertEqual(second.status, DecisionStatus.REJECT)
        self.assertFalse(first_receipt.reused)
        self.assertTrue(second_receipt.reused)
        self.assertEqual(len(parent_calls), len(fixed.cases))
        self.assertGreater(first_candidate_calls, 0)
        self.assertGreater(len(candidate_calls), first_candidate_calls)
        self.assertTrue(all(generation == "c" * 64
                            for generation, _ in
                            candidate_calls[first_candidate_calls:]))

    def test_any_authority_identity_drift_forces_parent_remeasurement(self):
        parent_solver, _, _, _, cohorts = _screen_inputs()
        fixed = cohorts[2]
        calls = []

        def counted(goal, generation):
            calls.append(goal.goal_id)
            return parent_solver.context_for(goal, generation)

        solver = CompleteSolver(counted, parent_solver.budget)
        base = _identity(cohort=contract_digest(fixed),
                         policy=fixed.policy_sha256,
                         rubric=fixed.rubric_sha256,
                         source=fixed.source_sha256)
        use_parent_assessment(base, solver, fixed, PARENT)
        baseline_calls = len(calls)

        source_changed = replace(fixed, source_sha256="c" * 64)
        rubric_changed = replace(fixed, rubric_sha256="d" * 64)
        policy_changed = replace(fixed, policy_sha256="e" * 64)
        cohort_changed = replace(
            fixed, training_episode_ids=("different-training-episode",))
        changed_contracts = (
            (replace(base, accepted_generation=8), fixed, PARENT),
            (replace(
                base,
                accepted_generation=8,
                accepted_generation_binding="2" * 64,
                parent_generation_sha256="2" * 64,
            ), fixed, "2" * 64),
            (replace(base, factory_release_sha256="a" * 64), fixed, PARENT),
            (replace(
                base,
                source_sha256=source_changed.source_sha256,
                fixed_cohort_sha256=contract_digest(source_changed),
            ), source_changed, PARENT),
            (replace(
                base,
                rubric_sha256=rubric_changed.rubric_sha256,
                fixed_cohort_sha256=contract_digest(rubric_changed),
            ), rubric_changed, PARENT),
            (replace(
                base,
                policy_sha256=policy_changed.policy_sha256,
                fixed_cohort_sha256=contract_digest(policy_changed),
            ), policy_changed, PARENT),
            (replace(base, correction_frontier_sha256="1" * 64), fixed, PARENT),
            (replace(
                base,
                fixed_cohort_sha256=contract_digest(cohort_changed),
            ), cohort_changed, PARENT),
            (replace(base, topology_sha256="3" * 64), fixed, PARENT),
            (replace(base, extents_sha256="4" * 64), fixed, PARENT),
            (replace(base, implementation_sha256="5" * 64), fixed, PARENT),
            (replace(base, evaluator_contract_sha256="6" * 64), fixed, PARENT),
        )
        for changed, changed_cohort, generation in changed_contracts:
            _, receipt = use_parent_assessment(
                changed, solver, changed_cohort, generation)
            self.assertFalse(receipt.reused)

        self.assertEqual(
            len(calls),
            baseline_calls + len(changed_contracts) * len(fixed.cases),
        )


if __name__ == "__main__":
    unittest.main()
