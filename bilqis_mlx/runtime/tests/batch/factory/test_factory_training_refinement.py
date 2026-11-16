"""B11 production composition and authority regressions for #471."""
from __future__ import annotations

import unittest
from dataclasses import replace
from types import SimpleNamespace

import mlx.core as mx

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_readout import ExecutionMode
from bilqis_mlx.runtime.atlas_model import bamf_value_and_grad, forward_bamf
import bilqis_mlx.runtime.atlas_model_contracts as model_contracts
import bilqis_mlx.runtime.atlas_model_forward as forward_impl
import bilqis_mlx.runtime.atlas_model_refinement as refinement_impl
from bilqis_mlx.runtime.factory_task_authority import (
    bind_factory_task_compiled_batch, factory_task_authority,
    factory_task_training_goal,
)
from bilqis_mlx.runtime.refinement_policy import RefinementChoice
from bilqis_mlx.runtime.refinement_request import (
    RefinementRequestDisposition, RefinementRequestKind,
)
from bilqis_mlx.runtime.task_goal_readout import (
    b11_task_goal_proposer, task_goal_route_plan, task_goal_training_targets,
)
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import (
    visit_provenance,
)
from bilqis_mlx.semantics.frame_compiler import PositionKind

from .factory_training_bridge_support import FactoryTrainingBridgeFixture


class FactoryTrainingRefinementTests(FactoryTrainingBridgeFixture):
    def owned(self, capability="A.IDENTITY", seed=37101, each=2):
        _rows, prepared = self.prepare(capability, seed, each)
        compiled = prepared.compiled_rows[0]
        authority = factory_task_authority(self.context, compiled)
        plan = task_goal_route_plan(
            authority.goal, compiled, self.b11_snapshot(compiled),
            self.generation)
        return bind_factory_task_compiled_batch(compiled, authority), authority, plan

    def gradient(self, seed):
        compiled, authority, plan = self.owned(seed=seed)
        resolved = factory_task_training_goal(self.context, compiled, authority)
        targets, mask = task_goal_training_targets(authority.goal, resolved)
        return bamf_value_and_grad(
            dict(self.candidate.retained_state.optimizer.parameters),
            compiled, plan, targets, mask, None)

    def test_b11_row_rejects_same_capability_visit_substitution(self):
        _rows, prepared = self.prepare("B.IDBOOLOPS", 37120, 1)
        compiled = prepared.compiled_rows[0]
        forged = visit_provenance(
            compiled.visit_provenance.capability_id,
            run_seed=compiled.visit_provenance.run_seed + 1,
            generation=compiled.visit_provenance.generation,
            selection_seed=compiled.visit_provenance.selection_seed,
            policy_key=compiled.visit_provenance.policy_key,
        )
        with self.assertRaises(BilqisError):
            replace(compiled, visit_provenance=forged)

    def test_b11_task_proposer_rejects_substituted_refinement_disposition(self):
        _rows, prepared = self.prepare("B.IDBOOLOPS", 37121, 1)
        compiled = prepared.compiled_rows[0]
        authority = factory_task_authority(self.context, compiled)
        plan = task_goal_route_plan(
            authority.goal, compiled, self.b11_snapshot(compiled),
            self.generation)
        forged = replace(
            plan,
            refinement_request=RefinementRequestDisposition(
                RefinementRequestKind.EXPLICIT_MEMBER, ("forged-role",)),
        )
        with self.assertRaises(BilqisError):
            b11_task_goal_proposer(
                self.candidate.retained_state.optimizer.parameters,
                compiled, forged, authority)

    def test_bound_b11_forward_rejects_substituted_refinement_disposition(self):
        compiled, _authority, plan = self.owned()
        forged = replace(
            plan,
            refinement_request=RefinementRequestDisposition(
                RefinementRequestKind.EXPLICIT_MEMBER, ("forged-role",)),
        )
        with self.assertRaises(BilqisError):
            forward_bamf(
                self.candidate.retained_state.optimizer.parameters,
                compiled, forged, ExecutionMode.INFERENCE, None)

    def test_visit_bearing_public_inference_uses_inference_refinement_mode(self):
        compiled, _authority, plan = self.owned()
        output = forward_bamf(
            self.candidate.retained_state.optimizer.parameters,
            compiled, plan, ExecutionMode.INFERENCE, None)
        record = model_contracts._FORWARD_ISSUANCE.require(output)
        self.assertFalse(any(
            name.startswith("refine.") for name in record.dense_parameter_names))

    def test_training_refinement_backpropagates_through_selected_source_frame(self):
        gradient = self.gradient(37101)
        for name in (
                "refine.query", "refine.key", "refine.value",
                "refine.output", "refine.norm", "refine.gate_vector",
                "refine.bias"):
            with self.subTest(name=name):
                self.assertGreater(float(mx.sum(mx.abs(gradient.gradients[name]))), 0.0)

    def test_pinned_a01_training_witness_keeps_b03_bindings_and_gradients(self):
        compiled, authority, plan = self.owned(seed=37101)
        params = dict(self.candidate.retained_state.optimizer.parameters)
        producer, _ = forward_impl._source_producer(
            params, compiled, self.generation, None)
        row = compiled.compiled.compiled.rows[0]
        index, position = next(
            (index, item) for index, item in enumerate(row.positions)
            if item.kind is PositionKind.CLOSURE)
        envelope = next(
            item for item in compiled.compiled.compiler_configs[0].approved.envelopes
            if item.frame_handle == position.frame_handle)
        requests = tuple(
            item for item in compiled.compiled.member_requests[0]
            if item.frame_handle == position.frame_handle)

        self.assertEqual(producer._encoded.handles[0][index], position)
        self.assertEqual(
            position.packed.sidecar.occurrence_id, envelope.frame.occurrence_id)
        self.assertEqual(
            tuple(item.member_handle for item in requests),
            tuple(item.source_handle for item in envelope.members))
        self.assertEqual(
            producer._encoded.members[0][index].shape[0], len(envelope.members))

        resolved = factory_task_training_goal(self.context, compiled, authority)
        targets, mask = task_goal_training_targets(authority.goal, resolved)
        execution = bamf_value_and_grad(
            params, compiled, plan, targets, mask, None)
        token_rows = mx.array(compiled.sources[0].source_row["tokens"])
        self.assertGreater(float(mx.sum(mx.abs(
            execution.gradients["identity.bank.0"][token_rows]))), 0.0)
        for name in ("features.project_type", "frame.project_output", "refine.output"):
            with self.subTest(name=name):
                self.assertGreater(
                    float(mx.sum(mx.abs(execution.gradients[name]))), 0.0)
        self.assertIn("refine.output", execution.execution.dense_parameter_names)

    def test_zero_pass_selection_keeps_refinement_gradient_dark(self):
        gradient = self.gradient(37103)
        for name in (
                "refine.query", "refine.key", "refine.value",
                "refine.output", "refine.norm", "refine.gate_vector",
                "refine.bias", "refine.route", "refine.route_bias"):
            with self.subTest(name=name):
                self.assertEqual(float(mx.sum(mx.abs(gradient.gradients[name]))), 0.0)

    def test_refinement_maps_by_frame_identity_not_source_rank(self):
        compiled, _authority, _plan = self.owned()
        producer, _ = forward_impl._source_producer(
            dict(self.candidate.retained_state.optimizer.parameters),
            compiled, self.generation, None)
        row = compiled.compiled.compiled.rows[0]
        closure_index, position = next(
            (index, item) for index, item in enumerate(row.positions)
            if item.kind is PositionKind.CLOSURE)
        occurrence = position.packed.sidecar.occurrence_id
        choice = RefinementChoice(
            position.frame_handle, occurrence, 999_999, 0, 0.0, 1,
            (self.generation, row.visible_end,
             compiled.sources[0].source_row["id"], occurrence),
        )
        self.assertEqual(
            refinement_impl._selected_frame_index(
                row, producer._encoded,
                compiled.compiled.compiler_configs[0], choice),
            closure_index,
        )

    def test_refinement_rejects_undefined_multi_role_pooling(self):
        compiled, _authority, _plan = self.owned()
        roles = tuple(
            role for role, _row in compiled.compiled.features.role_map
            if role not in ("NONE", "UNKNOWN")
        )[:2]
        request = RefinementRequestDisposition(
            RefinementRequestKind.EXPLICIT_MEMBER, tuple(sorted(roles)))
        self.assertEqual(len(roles), 2)
        with self.assertRaises(BilqisError):
            refinement_impl._refinement_role_vector(
                request, SimpleNamespace(features=compiled.compiled.features),
                self.candidate.retained_state.optimizer.parameters)


if __name__ == "__main__":
    unittest.main()
