"""C05 #1167 fixed-school MLX batching equivalence and resource witnesses."""
from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
import bilqis_mlx.runtime.backbone_identity as backbone_identity
from bilqis_mlx.runtime.capability_retention import (
    EvidenceKind, EvaluationCohort, case_census_digest,
    candidate_work_disposition, evaluate_capabilities,
)
from bilqis_mlx.runtime.factory_complete_solver import (
    factory_complete_solver, factory_evaluation_instrument,
)
import bilqis_mlx.runtime.factory_evaluation_batching as batching
import bilqis_mlx.runtime.factory_complete_solver as complete_solver_module
from bilqis_mlx.runtime.factory_evaluation_batching import _capacity
from bilqis_mlx.runtime.factory_evaluation_compiler import compile_factory_evaluation_batch
from bilqis_mlx.runtime.tests.batch.factory.factory_training_bridge_support import (
    FactoryTrainingBridgeFixture,
)


class FactoryEvaluationBatchingTests(FactoryTrainingBridgeFixture):
    CAPABILITY = "A.IDENTITY"
    SEED = 37144
    EACH = 4

    def _instruments(self):
        rows = tuple(self.context.draw_rows(
            seed=self.SEED, capability=self.CAPABILITY, each=self.EACH))
        self.assertEqual(len(rows), self.EACH)
        return tuple(factory_evaluation_instrument(
            self.context, self.candidate, str(self.artifact), row,
            source_seed=self.SEED, source_each=self.EACH)
            for row in rows)

    def _solver_pair(self, instruments):
        scalar, generation = factory_complete_solver(
            self.context, self.candidate, str(self.artifact), instruments)
        batched, batch_generation = factory_complete_solver(
            self.context, self.candidate, str(self.artifact), instruments)
        self.assertEqual(generation, batch_generation)
        return replace(scalar, contexts_for=None), batched, generation

    @staticmethod
    def _cohort(instruments):
        cases = tuple(item.case for item in instruments)
        return EvaluationCohort(
            EvidenceKind.FIXED_SCHOOL,
            cases,
            ((cases[0].capability_id, cases[0].group_id),),
            "1" * 64,
            "2" * 64,
            "3" * 64,
            "4" * 64,
            ("training-family",),
            ("training-episode",),
            case_census_digest(cases),
        )

    def test_fixed_school_batch_matches_scalar_and_reduces_backbone_launches(self):
        instruments = self._instruments()
        scalar, batched, generation = self._solver_pair(instruments)
        goals = tuple(item.case.goal for item in instruments)
        widths = tuple(len(compile_factory_evaluation_batch(
            self.context, self.candidate, str(self.artifact), item.source_row,
            source_seed=item.source_seed,
            source_each=item.source_each,
        ).compiled.compiled.rows[0].positions) for item in instruments)
        self.assertGreater(len(set(widths)), 1)

        scalar_measurements = scalar.evaluate_cases(goals, generation)
        batch_measurements = batched.evaluate_cases(goals, generation)

        self.assertEqual(
            tuple((result.replay_record(), contract)
                  for result, contract in scalar_measurements),
            tuple((result.replay_record(), contract)
                  for result, contract in batch_measurements),
        )
        scalar_telemetry = scalar.telemetry_for()
        batch_telemetry = batched.telemetry_for()
        self.assertEqual(scalar_telemetry["scalar_neural_launches"], self.EACH)
        self.assertEqual(batch_telemetry["scalar_neural_launches"], 0)
        self.assertGreaterEqual(batch_telemetry["shared_backbone_rows"], 2)
        self.assertLess(batch_telemetry["shared_backbone_launches"], self.EACH)
        self.assertLessEqual(batch_telemetry["largest_shared_positions"], 96)

    def test_assessment_and_work_disposition_are_scalar_batch_identical(self):
        instruments = self._instruments()
        scalar, batched, generation = self._solver_pair(instruments)
        cohort = self._cohort(instruments)
        scalar_assessment = evaluate_capabilities(scalar, cohort, generation)
        batch_assessment = evaluate_capabilities(batched, cohort, generation)

        self.assertEqual(scalar_assessment.digest(), batch_assessment.digest())
        self.assertEqual(
            candidate_work_disposition(scalar_assessment, self.CAPABILITY),
            candidate_work_disposition(batch_assessment, self.CAPABILITY),
        )

    def test_repeated_batch_evaluation_does_not_prelaunch_after_composition_cache(self):
        instruments = self._instruments()
        _scalar, batched, generation = self._solver_pair(instruments)
        goals = tuple(item.case.goal for item in instruments)
        first = batched.evaluate_cases(goals, generation)
        before = batched.telemetry_for()
        second = batched.evaluate_cases(goals, generation)
        after = batched.telemetry_for()

        self.assertEqual(before, after)
        self.assertEqual(
            tuple(result.answer for result, _contract in first),
            tuple(result.answer for result, _contract in second),
        )

    def test_generation_digest_is_issued_once_for_batched_and_scalar_fallback(self):
        instruments = self._instruments()
        goals = tuple(item.case.goal for item in instruments)
        original = backbone_identity.bamf_parameter_tree_digest

        with patch.object(
                backbone_identity, "bamf_parameter_tree_digest",
                wraps=original) as digest:
            batched, generation = factory_complete_solver(
                self.context, self.candidate, str(self.artifact), instruments)
            self.assertEqual(digest.call_count, 1)
            batched.evaluate_cases(goals, generation)
            self.assertEqual(digest.call_count, 1)

        with patch.object(
                backbone_identity, "bamf_parameter_tree_digest",
                wraps=original) as digest, patch.object(
                batching, "_positions", return_value=97):
            scalar, generation = factory_complete_solver(
                self.context, self.candidate, str(self.artifact), instruments)
            self.assertEqual(digest.call_count, 1)
            scalar.evaluate_cases(goals, generation)
            self.assertEqual(digest.call_count, 1)

    def test_repeated_batch_evaluation_rejects_task_drift_for_cached_goal_id(self):
        instruments = self._instruments()
        _scalar, batched, generation = self._solver_pair(instruments)
        goals = tuple(item.case.goal for item in instruments)
        batched.evaluate_cases(goals, generation)
        drifted = replace(
            goals[0],
            source_visible_bindings=tuple(sorted((
                *goals[0].source_visible_bindings,
                "source:drift",
            ))),
        )

        with self.assertRaises(BilqisError) as caught:
            batched.evaluate_cases((drifted, *goals[1:]), generation)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C05_FACTORY_SOLVER_SOURCE_DRIFT",
        )

    def test_over_96_compiled_width_falls_back_to_scalar_without_semantic_drift(self):
        instruments = self._instruments()
        scalar, batched, generation = self._solver_pair(instruments)
        goals = tuple(item.case.goal for item in instruments)
        scalar_measurements = scalar.evaluate_cases(goals, generation)

        with patch.object(batching, "_positions", return_value=97):
            batch_measurements = batched.evaluate_cases(goals, generation)

        self.assertEqual(
            tuple((result.replay_record(), contract)
                  for result, contract in scalar_measurements),
            tuple((result.replay_record(), contract)
                  for result, contract in batch_measurements),
        )
        telemetry = batched.telemetry_for()
        self.assertEqual(telemetry["shared_backbone_launches"], 0)
        self.assertEqual(telemetry["scalar_neural_launches"], self.EACH)

    def test_bounded_chunk_splitting_is_deterministic(self):
        instruments = self._instruments()
        _scalar, batched, generation = self._solver_pair(instruments)
        goals = tuple(item.case.goal for item in instruments)

        with patch.object(
                batching, "_capacity",
                side_effect=lambda items: min(2, len(items))):
            batched.evaluate_cases(goals, generation)

        telemetry = batched.telemetry_for()
        self.assertEqual(telemetry["shared_backbone_launches"], 2)
        self.assertEqual(telemetry["shared_backbone_rows"], self.EACH)
        self.assertEqual(telemetry["largest_shared_rows"], 2)

    def test_batch_compatibility_failure_propagates_instead_of_falling_back(self):
        instruments = self._instruments()
        _scalar, batched, generation = self._solver_pair(instruments)
        goals = tuple(item.case.goal for item in instruments)

        with patch.object(
                batching, "_compatible",
                side_effect=RuntimeError("custody validation failed")):
            with self.assertRaisesRegex(RuntimeError, "custody validation failed"):
                batched.evaluate_cases(goals, generation)

    def test_b11_row_decode_rejects_task_plan_custody_drift(self):
        instruments = self._instruments()
        original = complete_solver_module.task_goal_route_plan

        def drifted_plan(*args, **kwargs):
            return replace(original(*args, **kwargs), refinement_request=None)

        with patch.object(complete_solver_module, "task_goal_route_plan", drifted_plan):
            _scalar, batched, generation = self._solver_pair(instruments)
            goals = tuple(item.case.goal for item in instruments)
            with self.assertRaises(BilqisError) as caught:
                batched.evaluate_cases(goals, generation)
        self.assertEqual(
            caught.exception.context["reason"],
            "B11_FORWARD_TASK_PLAN_CUSTODY_MISMATCH",
        )


class FactoryBatchResourcePolicyTests(unittest.TestCase):
    @staticmethod
    def _item(position_count):
        row = SimpleNamespace(positions=(None,) * position_count)
        compiled = SimpleNamespace(compiled=SimpleNamespace(rows=(row,)))
        return SimpleNamespace(batch=SimpleNamespace(compiled=compiled))

    def test_compiled_position_budget_falls_back_above_legacy_width(self):
        self.assertEqual(_capacity((self._item(97), self._item(97))), 1)

    def test_compiled_position_budget_bounds_activation_and_attention_work(self):
        items = tuple(self._item(96) for _ in range(30))
        self.assertEqual(_capacity(items), 24)
        items = tuple(self._item(48) for _ in range(60))
        self.assertEqual(_capacity(items), 48)


if __name__ == "__main__":
    unittest.main()
