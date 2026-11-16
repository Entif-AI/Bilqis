"""Factory gradient, candidate-step, and accepted C09 custody integration."""
from __future__ import annotations

BILQIS_LEAF_GATE_POLICY = "DETACHED_ONLY"

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import mlx.core as mx
from mlx.utils import tree_flatten

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.learning.atlas_readout import DecisionOutput
from bilqis_mlx.learning.tests.test_frame_encoder import FrameEncoderTests
from bilqis_mlx.learning.student_ops import train_bamf_factory_step
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.atlas_model import bamf_value_and_grad
import bilqis_mlx.runtime.b11_source_execution_authority as b11_authority_impl
from bilqis_mlx.runtime.atlas_resources import (
    MemoryBudget, ResourceRow, estimate_row_activation_bytes,
)
from bilqis_mlx.runtime.atlas_training_adapter import pad_microbatches
from bilqis_mlx.runtime.bamf_bundle import publish_initial_generation
from bilqis_mlx.runtime.bamf_bundle.admission import (
    load_accepted_generation,
)
from bilqis_mlx.runtime.factory_candidate_training import (
    FactoryDeliveryObservation, _frame_stats, execute_factory_candidate_step,
)
from bilqis_mlx.runtime.factory_complete_solver import factory_evaluation_instrument
from bilqis_mlx.runtime.factory_task_authority import (
    bind_factory_task_compiled_batch,
    factory_task_authority,
    factory_task_training_goal,
)
from bilqis_mlx.runtime.model_topology_v2 import bamf_parameter_census
from bilqis_mlx.runtime.task_goal_readout import (
    task_goal_route_decisions, task_goal_route_plan,
)
from bilqis_mlx.runtime.teacher_observation_capture import (
    ObservationCapture, read_sidecar, store_sidecar,
)
from bilqis_mlx.runtime.tests.capability.factory.retention.factory_retention_live_support import HP
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY, _event
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind, DependencyRef

from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import (
    visit_provenance,
)

from .factory_training_bridge_support import FactoryTrainingBridgeFixture
from .factory_training_execution_support import (
    assert_prepared_logical_rows,
    assert_split_step_result,
    draw,
    observation,
    publish,
    split_budget,
)


class FactoryResourcePlanningCustodyTests(unittest.TestCase):
    def test_held_packed_frame_cannot_feed_resource_stats(self):
        fixture = FrameEncoderTests()
        fixture.setUp()
        compiled, _vectors, _ast = fixture.compiled_inputs()
        owner = compiled.packed_frame_artifact_owner
        source = next(
            ref for node in owner.index.nodes
            for ref in node.immediate_dependencies
            if ref.kind is DependencyKind.SOURCE)
        owner.apply_correction(_event(source), AUTHORITY)

        with self.assertRaises(BilqisError) as caught:
            _frame_stats(SimpleNamespace(compiled=compiled))
        self.assertEqual(caught.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")


class FactoryTrainingExecutionTests(FactoryTrainingBridgeFixture):
    def route_context(self, compiled):
        authority = factory_task_authority(self.context, compiled)
        plan = task_goal_route_plan(
            authority.goal, compiled, self.b11_snapshot(compiled),
            self.generation)
        return authority, plan

    def test_disposable_gradient_is_finite_and_target_cannot_change_logits(self):
        seed = 37114
        rows, prepared = self.prepare("B.IDBOOLOPS", seed, 1)
        compiled = prepared.compiled_rows[0]
        authority, plan = self.route_context(compiled)
        route = task_goal_route_decisions(authority.goal)
        self.assertEqual(len(route), 1)
        case = factory_evaluation_instrument(
            self.context, self.candidate, str(self.artifact), rows[0],
            source_seed=seed, source_each=1).case
        node = authority.goal.expression_or_holes.nodes[0]
        handle = next(
            item.typed.source_handle for item in authority.binding.operands
            if item.typed.type_name == case.gold.type_name
            and item.typed.value == case.gold.value)
        correct = next(
            item.identity for item in node.candidate_operand_refs[0]
            if item.source_handle == handle)
        alternatives = tuple(value for value in route[0].legal_values if value != correct)
        self.assertTrue(alternatives)
        parameters = dict(self.candidate.retained_state.optimizer.parameters)
        mask = {route[0].decision_id: True}
        first = bamf_value_and_grad(
            parameters, compiled, plan,
            (DecisionOutput(route[0].decision_id, correct),), mask, None)
        second = bamf_value_and_grad(
            parameters, compiled, plan,
            (DecisionOutput(route[0].decision_id, alternatives[0]),), mask, None)
        self.assertTrue(bool(mx.array_equal(
            first.execution.output.decisions[0].logits,
            second.execution.output.decisions[0].logits)))
        self.assertNotEqual(float(first.loss_total.item()), float(second.loss_total.item()))
        for _, gradient in tree_flatten(first.gradients):
            self.assertTrue(bool(mx.all(mx.isfinite(gradient))))
        updated = {
            name: parameters[name] - mx.array(1e-6) * first.gradients[name]
            for name in parameters
        }
        mx.eval(updated)
        self.assertTrue(all(bool(mx.all(mx.isfinite(value))) for value in updated.values()))
        self.assertTrue(any(
            not bool(mx.array_equal(updated[name], parameters[name])) for name in parameters))

    def test_scalar_gradient_never_rehashes_source_inside_launch_trust(self):
        _rows, prepared = self.prepare("A.IDENTITY", 37128, 2)
        compiled = prepared.compiled_rows[0]
        _authority, plan = self.route_context(compiled)
        route = task_goal_route_decisions(_authority.goal)
        targets = tuple(
            DecisionOutput(item.decision_id, item.legal_values[0]) for item in route)
        mask = {item.decision_id: True for item in route}
        original_source_digest = b11_authority_impl._source_digest

        def source_digest_outside_launch(source):
            if b11_authority_impl._LAUNCH_TRUST.get():
                raise AssertionError("B11 rehashed source inside trusted scalar launch")
            return original_source_digest(source)

        with patch.object(
                b11_authority_impl, "_source_digest",
                side_effect=source_digest_outside_launch):
            result = bamf_value_and_grad(
                dict(self.candidate.retained_state.optimizer.parameters),
                compiled, plan, targets, mask, None)
        self.assertTrue(bool(mx.isfinite(result.loss_total)))

    def test_real_rows_pack_to_actual_maximum_without_identity_loss(self):
        rows, prepared = self.prepare("A.IDENTITY", 37101, 2)
        lengths = tuple(len(row.model_input.prefix.positions)
                        for row in prepared.training_batch.rows)
        packed = pad_microbatches(
            prepared.training_batch, {}, None,
            plan_microbatches=lambda batch_rows, topology, budget: ((0, 1),),
            indices_for_plan=lambda plan: plan,
            positions_for=lambda prefix: prefix.positions)
        self.assertEqual(len(packed), 1)
        self.assertEqual(len(packed[0].positions[0]), max(lengths))
        self.assertEqual(
            tuple(row.provenance.row_id for row in prepared.training_batch.rows),
            tuple(row["id"] for row in rows))
        self.assertEqual(tuple(sum(mask) for mask in packed[0].padding_mask), lengths)

    def test_student_ops_executes_one_real_factory_candidate_step_and_records_cost(self):
        rows, delivery = draw(self, "B.IDBOOLOPS", 37116, 1)
        with TemporaryDirectory() as run_dir_value:
            run_dir = Path(run_dir_value)
            publish(self, run_dir)
            source_context = self.accepted_source_context(run_dir)
            parent = load_accepted_generation(run_dir)
            capture, delivery_observation = observation(
                run_dir, "B.IDBOOLOPS", rows, 37116)
            result = train_bamf_factory_step(
                run_dir, source_context, parent, str(self.artifact),
                self.feature_receipt.path, rows,
                capability="B.IDBOOLOPS", delivery=delivery,
                requested_count=2, source_seed=37116, source_each=1,
                optimizer_step_seed=17,
                visit_provenance=visit_provenance("B.IDBOOLOPS"),
                teacher_strategy={"policy": "c02-parent-production"},
                teacher_hparams=HP, max_norm=1.0, observation=delivery_observation)
            self.assertEqual(result.transaction.update_steps, 1)
            self.assertEqual(result.resource_plan.groups, ((0,),))
            self.assertEqual(len(result.route_targets), 1)
            self.assertIsNone(result.diagnostics)
            self.assertEqual(result.realized_cost["optimizer_steps"], 1)
            self.assertEqual(result.realized_cost["atlas_reload_count"], 1)
            self.assertEqual(result.realized_cost["feature_manifest_rebuild_count"], 1)
            self.assertEqual(result.realized_cost["visit_atlas_reload_count"], 1)
            self.assertEqual(
                result.realized_cost["visit_feature_manifest_rebuild_count"], 1)
            payload = read_sidecar(run_dir, capture.steps[0])
            self.assertEqual(
                payload["positions"][0]["row"]["sha256"],
                store_sidecar(run_dir, rows[0])["sha256"])
            self.assertEqual(payload["controls"]["realized_cost"]["optimizer_steps"], 1)

    def test_candidate_continuation_executes_second_step_from_speculative_weights(self):
        rows, delivery = draw(self, "B.IDBOOLOPS", 37119, 1)
        with TemporaryDirectory() as run_dir_value:
            run_dir = Path(run_dir_value)
            publish(self, run_dir)
            source_context = self.accepted_source_context(run_dir)
            parent = load_accepted_generation(run_dir)
            capture, first_observation = observation(
                run_dir, "B.IDBOOLOPS", rows, 37119)
            first = execute_factory_candidate_step(
                run_dir, source_context, parent, str(self.artifact),
                self.feature_receipt.path, rows,
                capability="B.IDBOOLOPS", delivery=delivery,
                requested_count=2, source_seed=37119, source_each=1,
                optimizer_step_seed=21,
                visit_provenance=visit_provenance("B.IDBOOLOPS"),
                teacher_strategy={"policy": "candidate-horizon"},
                teacher_hparams=HP, max_norm=1.0,
                observation=first_observation, finalize_candidate=False)
            self.assertEqual(first.transaction.update_steps, 1)
            self.assertIsNone(first.transaction.motif_transition)
            second_observation = FactoryDeliveryObservation(
                capture, parent.retained_state.optimizer_step + 2,
                rows, 37119)
            with patch(
                    "bilqis_mlx.runtime.factory_candidate_microbatch.bamf_value_and_grad",
                    wraps=bamf_value_and_grad) as gradient:
                second = execute_factory_candidate_step(
                    run_dir, source_context, parent, str(self.artifact),
                    self.feature_receipt.path, rows,
                    capability="B.IDBOOLOPS", delivery=delivery,
                    requested_count=2, source_seed=37119, source_each=1,
                    optimizer_step_seed=22,
                    visit_provenance=visit_provenance("B.IDBOOLOPS"),
                    teacher_strategy={"policy": "candidate-horizon"},
                    teacher_hparams=HP, max_norm=1.0,
                    observation=second_observation,
                    candidate=first.transaction, finalize_candidate=True)
            second_params = gradient.call_args.args[0]
            for name, value in first.transaction.optimizer.parameters.items():
                self.assertTrue(bool(mx.array_equal(second_params[name], value)))
            self.assertEqual(second.transaction.update_steps, 2)
            self.assertEqual(len(second.transaction.step_proofs), 2)
            self.assertEqual(len(second.transaction.training_authorities), 2)
            self.assertEqual(
                tuple(proof.training_authority_sha256 for proof in second.transaction.step_proofs),
                tuple(authority.digest for authority in second.transaction.training_authorities))
            deltas = tuple(
                after - parent.retained_state.optimizer.update_counts[name]
                for name, after in second.transaction.optimizer.update_counts.items())
            self.assertTrue(any(bool(mx.any(delta == 2)) for delta in deltas))

    def test_persisted_correction_holds_training_batch_before_gradient_read(self):
        rows, delivery = draw(self, "B.IDBOOLOPS", 37118, 1)
        correction = _event(DependencyRef(
            DependencyKind.SOURCE,
            "source:" + self.feature_context.features.source_bundle_id))
        with TemporaryDirectory() as run_dir_value:
            run_dir = Path(run_dir_value)
            publish(self, run_dir)
            source_context = self.accepted_source_context(run_dir)
            AcceptedRuntimeHost(run_dir).record_correction(correction)
            parent = load_accepted_generation(run_dir)
            _, delivery_observation = observation(
                run_dir, "B.IDBOOLOPS", rows, 37118)
            with self.assertRaises(BilqisError) as caught:
                train_bamf_factory_step(
                    run_dir, source_context, parent, str(self.artifact),
                    self.feature_receipt.path, rows,
                    capability="B.IDBOOLOPS", delivery=delivery,
                    requested_count=2, source_seed=37118, source_each=1,
                    optimizer_step_seed=19,
                    visit_provenance=visit_provenance("B.IDBOOLOPS"),
                    teacher_strategy={"policy": "c09-correction-hold"},
                    teacher_hparams=HP, max_norm=1.0, observation=delivery_observation)
            self.assertEqual(caught.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")

    def test_production_step_accumulates_split_real_rows_into_one_optimizer_step(self):
        rows, delivery = draw(self, "A.IDENTITY", 37117, 2)
        with TemporaryDirectory() as run_dir_value:
            run_dir = Path(run_dir_value)
            publish(self, run_dir)
            source_context = self.accepted_source_context(run_dir)
            parent = load_accepted_generation(run_dir)
            prepared = self.prepare("A.IDENTITY", 37117, 2)[1]
            row_ids = tuple(row["id"] for row in rows)
            assert_prepared_logical_rows(self, prepared, row_ids)
            _, delivery_observation = observation(
                run_dir, "A.IDENTITY", rows, 37117)
            result = train_bamf_factory_step(
                run_dir, source_context, parent, str(self.artifact),
                self.feature_receipt.path, rows,
                capability="A.IDENTITY", delivery=delivery,
                requested_count=2, source_seed=37117, source_each=2,
                optimizer_step_seed=18,
                visit_provenance=visit_provenance("A.IDENTITY"),
                teacher_strategy={"policy": "c02-parent-production"},
                teacher_hparams=HP, max_norm=1.0, observation=delivery_observation,
                memory_budget=split_budget(parent, prepared),
                capture_diagnostics=True)
            assert_split_step_result(self, result, prepared, row_ids, parent)

if __name__ == "__main__":
    unittest.main()
