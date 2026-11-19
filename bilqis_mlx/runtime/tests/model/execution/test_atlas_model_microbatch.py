"""#1172 true B11/C08 MLX microbatch parity witnesses."""
from __future__ import annotations

from types import SimpleNamespace
import unittest
from types import SimpleNamespace
from unittest import skipUnless
from unittest.mock import patch

import mlx.core as mx
import numpy as np

import bilqis_mlx.runtime.backbone_identity as backbone_identity
import bilqis_mlx.runtime.atlas_model_microbatch as microbatch_impl
from bilqis_mlx.learning.atlas_readout import (
    AnswerPlan, ControlAction, DecisionKind, DecisionOutput, DecisionSpec,
    compile_frame_output,
)
from bilqis_mlx.learning.atlas_readout.causal_training import encode_feedback_value
from bilqis_mlx.learning.atlas_readout.decoder.feedback import occurrence_vector
from bilqis_mlx.learning.atlas_engram_reads import MotifReadResult
from bilqis_mlx.learning.source_atoms.tests.backbone_test_support import (
    SourceBackboneTestBase,
)
from bilqis_mlx.runtime.atlas_model import (
    BamfCompiledBatch, bamf_microbatch_value_and_grad, bamf_value_and_grad,
)
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.runtime.atlas_model_participation import _row_motif_read
from bilqis_mlx.runtime.microbatch.route_kernel import (
    RouteMicrobatchKernel, prepare_route_microbatch_kernel,
    route_microbatch_compatible, route_microbatch_mean_loss,
)
from bilqis_mlx.runtime.tests.model.execution.active_semantic_rows_support import (
    active_semantic_rows,
)
from bilqis_mlx.semantics.frame_codec import SchemaTagMap
from bilqis_mlx.semantics.frame_schema import FrameSchema, RoleSpec, SourceSpan
from bilqis_mlx.semantics.released_frame_schemas import (
    load_released_frame_schemas, seal_released_frame_schemas,
)
from bilqis_mlx.source_adapters.tests.atoms.helpers import REAL_BUNDLE


FP32_ATOL = 2e-5
FP32_RTOL = 3e-5


class RouteMicrobatchKernelTests(unittest.TestCase):
    def _parameters(self):
        width, inner = ModelTopologySpecV2.width, 192
        return {
            "features.role": mx.stack((
                mx.zeros((width,), dtype=mx.float32),
                mx.arange(width, dtype=mx.float32) / 1000.0,
            )),
            "features.gates": mx.zeros((4,), dtype=mx.float32),
            "features.project_role": mx.eye(width, dtype=mx.float32),
            "readout.feedback": mx.eye(width, dtype=mx.float32) * 0.02,
            "readout.state_norm": mx.ones((width,), dtype=mx.float32),
            "readout.output_norm": mx.ones((width,), dtype=mx.float32),
            "readout.key": mx.eye(inner, width, dtype=mx.float32),
            "readout.value": mx.eye(inner, width, dtype=mx.float32),
            "readout.query": mx.eye(inner, width, dtype=mx.float32),
            "readout.output": mx.eye(width, inner, dtype=mx.float32),
        }

    def _kernel(self):
        width = ModelTopologySpecV2.width
        candidates = (
            (("op.a", "op.b"), ("op.x", "op.y")),
            (("arg.a", "arg.b", "arg.c"), ("arg.x", "arg.y", "arg.z")),
        )
        candidate_vectors = tuple(mx.stack(tuple(
            mx.stack(tuple(encode_feedback_value(value) for value in row))
            for row in decision)) for decision in candidates)
        candidate_masks = tuple(
            mx.ones(value.shape[:2], dtype=mx.bool_) for value in candidate_vectors)
        feedback = (
            mx.zeros((2, width), dtype=mx.float32),
            mx.stack((encode_feedback_value("op.b"), encode_feedback_value("op.x"))),
        )
        inactive = (
            mx.zeros((2,), dtype=mx.int32), mx.zeros((2,), dtype=mx.bool_))
        return RouteMicrobatchKernel(
            mx.array((3, 2), dtype=mx.int32),
            (mx.array((True, True), dtype=mx.bool_),
             mx.array((False, False), dtype=mx.bool_)),
            (mx.array((False, False), dtype=mx.bool_),
             mx.array((True, True), dtype=mx.bool_)),
            (
                mx.stack((occurrence_vector(0), occurrence_vector(0))),
                mx.stack((occurrence_vector(1), occurrence_vector(1))),
            ),
            feedback, candidate_vectors, candidate_masks,
            (mx.array((1, 0), dtype=mx.int32),
             mx.array((2, 1), dtype=mx.int32)),
            mx.array((1, 1), dtype=mx.int32),
            mx.array((1, 1), dtype=mx.int32),
            (inactive, inactive, inactive), False,
            SimpleNamespace(role_map=(("UNKNOWN", 0), ("NONE", 1))),
            SimpleNamespace())

    def _slice_kernel(self, kernel, index):
        return RouteMicrobatchKernel(
            kernel.lengths[index:index + 1],
            tuple(value[index:index + 1] for value in kernel.operator_masks),
            tuple(value[index:index + 1] for value in kernel.operand_masks),
            tuple(value[index:index + 1] for value in kernel.occurrences),
            tuple(value[index:index + 1] for value in kernel.feedback),
            tuple(value[index:index + 1] for value in kernel.candidate_vectors),
            tuple(value[index:index + 1] for value in kernel.candidate_masks),
            tuple(value[index:index + 1] for value in kernel.target_indices),
            kernel.operator_counts[index:index + 1],
            kernel.operand_counts[index:index + 1],
            tuple((targets[index:index + 1], active[index:index + 1])
                  for targets, active in kernel.salience_targets),
            kernel.has_salience, kernel.features, kernel.extents)

    def test_batched_route_loss_and_gradients_match_scalar_rows_with_padding(self):
        params = self._parameters()
        kernel = self._kernel()
        width = ModelTopologySpecV2.width
        hidden = (mx.arange(2 * 3 * width, dtype=mx.float32)
                  .reshape(2, 3, width) / 10000.0)
        batched_loss, batched_gradients = mx.value_and_grad(
            lambda values: route_microbatch_mean_loss(values, hidden, kernel))(params)
        scalar = tuple(mx.value_and_grad(
            lambda values, row=index: route_microbatch_mean_loss(
                values, hidden[row:row + 1], self._slice_kernel(kernel, row)))(params)
            for index in range(2))
        expected_loss = mx.mean(mx.stack(tuple(item[0] for item in scalar)))
        np.testing.assert_allclose(
            np.asarray(batched_loss), np.asarray(expected_loss), atol=FP32_ATOL, rtol=FP32_RTOL)
        for name in params:
            with self.subTest(name=name):
                expected = mx.mean(mx.stack(tuple(item[1][name] for item in scalar)), axis=0)
                np.testing.assert_allclose(
                    np.asarray(batched_gradients[name]), np.asarray(expected),
                    atol=FP32_ATOL, rtol=FP32_RTOL)

    def test_ragged_route_plans_remain_vector_compatible(self):
        first = (
            DecisionSpec("op.1", None, 0, DecisionKind.OPERATOR, ("a", "b")),
            DecisionSpec("arg.1", None, 1, DecisionKind.OPERAND, ("x", "y"), ("op.1",)),
        )
        second = (
            DecisionSpec("op.2", None, 0, DecisionKind.OPERATOR, ("c", "d")),
        )
        plans = (
            SimpleNamespace(route_only=True, decisions=first,
                            execution_order=("op.1", "arg.1")),
            SimpleNamespace(route_only=True, decisions=second,
                            execution_order=("op.2",)),
        )
        targets = (
            (DecisionOutput("op.1", "b"), DecisionOutput("arg.1", "x")),
            (DecisionOutput("op.2", "c"),),
        )
        masks = ({"op.1": True, "arg.1": True}, {"op.2": True})
        features = SimpleNamespace(role_map=(("UNKNOWN", 0), ("NONE", 1)))
        extents = SimpleNamespace()
        rows = tuple(SimpleNamespace(compiled=SimpleNamespace(
            compiled=SimpleNamespace(rows=(SimpleNamespace(positions=(None,) * length),)),
            features=features, extents=extents)) for length in (3, 2))
        preflight = (
            SimpleNamespace(output=SimpleNamespace(committed=targets[0])),
            SimpleNamespace(output=SimpleNamespace(committed=targets[1])),
        )
        self.assertTrue(route_microbatch_compatible(rows, plans, targets, masks))
        kernel = prepare_route_microbatch_kernel(
            rows, plans, targets, masks, preflight)
        np.testing.assert_array_equal(
            np.asarray(kernel.operand_masks[1]), np.asarray((True, False)))
        np.testing.assert_array_equal(
            np.asarray(kernel.operator_counts), np.asarray((1, 1)))
        np.testing.assert_array_equal(
            np.asarray(kernel.operand_counts), np.asarray((1, 0)))


class MicrobatchParticipationProjectionTests(unittest.TestCase):
    def test_batched_motif_read_projects_exact_row_slots(self):
        read = MotifReadResult(
            mx.zeros((2, 1, 768), dtype=mx.float32),
            (("EXACT",), ("STRUCTURAL",)), (3, 7),
            ("a" * 64, "b" * 64), ((3,), (7,)))
        first = _row_motif_read(read, 0)
        second = _row_motif_read(read, 1)
        self.assertEqual(first.participating_slots, (3,))
        self.assertEqual(second.participating_slots, (7,))
        self.assertEqual(first.hidden.shape, (1, 1, 768))
        self.assertEqual(second.hidden.shape, (1, 1, 768))

    def test_vectorized_microbatch_threads_one_bound_snapshot_through_preflight_and_autodiff(self):
        snapshot = object()
        plans = tuple(
            SimpleNamespace(generation_binding="generation", snapshot=snapshot)
            for _ in range(2))
        row_batches = (object(), object())
        batch = SimpleNamespace(compiled=SimpleNamespace(extents=object()))
        seen = {"preflight": None, "autodiff": None}

        class Backend:
            topology = object()

            def __post_init__(self):
                return None

        def preflight(*args):
            seen["preflight"] = args[-1]
            return (SimpleNamespace(output=None),) * 2

        def producer(*_args, **kwargs):
            seen["autodiff"] = kwargs.get("snapshot")
            return object(), None, False

        with patch.object(microbatch_impl, "_compiled_microbatch", return_value=batch), patch.object(
                microbatch_impl, "_require_finite_tensor_tree"), patch.object(
                    microbatch_impl, "_gradient_execution_rebinder",
                    return_value=lambda current: object()), patch.object(
                        microbatch_impl, "prepare_refinement_selections",
                        return_value=(None, None)), patch.object(
                            microbatch_impl, "microbatch_trace_preflight",
                        side_effect=preflight), patch.object(
                            microbatch_impl, "_source_producer", side_effect=producer), patch.object(
                                microbatch_impl, "_finalize_source_hidden",
                                return_value=mx.zeros((2, 1, 1), dtype=mx.float32)), patch.object(
                                    microbatch_impl, "_decode_bamf_producer_row",
                                    side_effect=lambda _backend, current, *_args, **_kwargs: current["x"]), patch.object(
                                        microbatch_impl, "loss_bearing_bamf",
                                        side_effect=lambda output, *_args, **_kwargs: SimpleNamespace(
                                            loss=SimpleNamespace(total=output))), patch.object(
                                                microbatch_impl, "finalize_microbatch_gradient",
                                                return_value="done"):
            result = microbatch_impl._bamf_microbatch_value_and_grad_impl(
                Backend(), {"x": mx.array(1.0, dtype=mx.float32)}, row_batches,
                plans, ((), ()), ({}, {}), None)
        self.assertEqual(result, "done")
        self.assertIs(seen["preflight"], snapshot)
        self.assertIs(seen["autodiff"], snapshot)


@skipUnless(REAL_BUNDLE, "real pinned A01 artifact not mounted")
class AtlasModelMicrobatchTests(SourceBackboneTestBase):
    def _answer_plan(self, parameters):
        role_id = next(
            role for role, _row in self.compiled.features.role_map
            if role not in ("UNKNOWN", "NONE"))
        schema = FrameSchema(
            "frame:test-b11-microbatch", 1, "test:b11-microbatch",
            (RoleSpec(role_id, ("Entity",), 0, 1),), "ORDERED", "test")
        manifest = seal_released_frame_schemas(
            (schema,), SchemaTagMap.from_schemas(
                self.snapshot.release_sha256, (schema,)), self.snapshot)
        released = load_released_frame_schemas(
            manifest.canonical_bytes(), expected_sha256=manifest.digest,
            snapshot=self.snapshot)
        domain = compile_frame_output(schema, released, self.compiled.features)
        generation = execution_generation_digest(
            parameters, spec=ModelTopologySpecV2(), extents=self.compiled.extents)
        row = self.compiled.compiled.rows[0]
        return AnswerPlan(
            domain.modality_id, len(row.positions),
            (DecisionSpec(
                "finish", None, 0, DecisionKind.CONTROL,
                (ControlAction.END_FRAME,),
            ),),
            domain, self.snapshot, SourceSpan(0, 0), generation)

    def _batch(self):
        return BamfCompiledBatch(
            self.compiled, (self.source,), self.schema,
            active_semantic_rows(
                self.compiled, self.active_indices,
                run_id="b11-microbatch-parity", generation=0))

    def test_four_row_microbatch_matches_scalar_fp32_reference_in_one_gradient_launch(self):
        parameters = dict(self.parameters)
        batch = self._batch()
        plan = self._answer_plan(parameters)
        targets = (DecisionOutput("finish", ControlAction.END_FRAME),)
        mask = {"finish": True}
        scalar = tuple(bamf_value_and_grad(
            parameters, batch, plan, targets, mask, None) for _ in range(4))
        expected_loss = mx.mean(mx.stack(tuple(item.loss_total for item in scalar)))
        expected_gradients = {
            name: mx.mean(mx.stack(tuple(item.gradients[name] for item in scalar)), axis=0)
            for name in scalar[0].gradients
        }
        original_digest = backbone_identity.bamf_parameter_tree_digest
        with patch.object(
                backbone_identity, "bamf_parameter_tree_digest",
                wraps=original_digest) as tree_digest, patch.object(
                mx, "value_and_grad", wraps=mx.value_and_grad) as value_and_grad:
            vector = bamf_microbatch_value_and_grad(
                parameters, (batch,) * 4, (plan,) * 4,
                (targets,) * 4, (mask,) * 4, None)
        self.assertEqual(value_and_grad.call_count, 1)
        self.assertEqual(tree_digest.call_count, 1)
        self.assertEqual(len(vector.executions), 4)
        self.assertEqual(
            tuple(item.output.committed for item in vector.executions),
            tuple(item.execution.output.committed for item in scalar))
        np.testing.assert_allclose(
            np.asarray(vector.mean_loss), np.asarray(expected_loss),
            atol=FP32_ATOL, rtol=FP32_RTOL)
        for name, expected in expected_gradients.items():
            with self.subTest(name=name):
                np.testing.assert_allclose(
                    np.asarray(vector.gradients[name]), np.asarray(expected),
                    atol=FP32_ATOL, rtol=FP32_RTOL)


if __name__ == "__main__":
    unittest.main()
