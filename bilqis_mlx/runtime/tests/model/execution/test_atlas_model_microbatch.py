"""#1172 true B11/C08 MLX microbatch parity witnesses."""
from __future__ import annotations

from types import SimpleNamespace
import unittest
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
