"""B11 mixed-frame, tensor-ownership, and downstream causal witnesses."""
import hashlib
import unittest

import mlx.core as mx
import numpy as np

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.frame_embeddings import embedding_parameter_view
from bilqis_mlx.learning.frame_encoder import frame_encoder_parameter_view
from bilqis_mlx.learning.tests.frames.nested_fixtures import _case
from bilqis_mlx.runtime.atlas_attention import (
    ATTENTION_PARAMETER_NAMES, AttentionScope, ccgqa,
)
from bilqis_mlx.runtime.atlas_refinement import refinement_parameter_view
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.backbone_group_numerical import (
    _norm, run_backbone_group_numerical,
)
from bilqis_mlx.runtime.backbone_source_bridge import compute_compiled_h0
from bilqis_mlx.runtime.block_attnres import depth_parameter_view
from bilqis_mlx.runtime.model_topology_v2 import (
    ModelTopologySpecV2, expected_bamf_shapes,
)
from bilqis_mlx.runtime.topology_v2.construction import create_unbound_bamf_state
from bilqis_mlx.semantics.frame_codec import PackDisposition
from bilqis_mlx.semantics.frame_compiler import PositionKind


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AtlasModelMixedFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ast, _, compiled, vectors, _ = _case()
        cls.ast = ast
        cls.compiled = compiled
        cls.vectors = vectors
        cls.spec = ModelTopologySpecV2()
        cls.parameters, optimizer, cls.manifest = create_unbound_bamf_state(
            cls.spec, compiled.extents, run_seed=473)
        del optimizer

    @classmethod
    def _group_parameters(cls, group_index):
        start = (group_index - 1) * 4
        prefixes = tuple(
            f"blocks.{layer}." for layer in range(start, start + 4))
        return {
            name: value for name, value in cls.parameters.items()
            if name.startswith(prefixes)
        }

    @classmethod
    def _stack(cls, hidden):
        valid = mx.array([
            [position is not None for position in row]
            for row in cls.compiled.compiled.padded_positions
        ], dtype=mx.bool_)
        scope = mx.zeros(valid.shape, dtype=mx.int32)
        current = hidden
        for group_index in (1, 2, 3):
            current = run_backbone_group_numerical(
                current, cls._group_parameters(group_index),
                group_index=group_index, spec=cls.spec,
                extents=cls.compiled.extents, scope_ids=scope, valid=valid,
                generation="4" * 64, prefix_digest="5" * 64).hidden
        return current

    @classmethod
    def _control_logits(cls, hidden):
        return (
            hidden @ cls.parameters["readout.control"].T
            + cls.parameters["readout.control_bias"]
        )

    @classmethod
    def _attention_parameters(cls, layer=0):
        return {
            name: cls.parameters[f"blocks.{layer}.{name}"]
            for name in ATTENTION_PARAMETER_NAMES
        }

    @classmethod
    def _incremental_12_layer_stack(
            cls, hidden, *, scope_ids, valid, generation, cuts,
            initial_caches=None):
        caches = [None] * cls.spec.layers if initial_caches is None else list(initial_caches)
        left = 0
        parent = None
        outputs = []
        for right in cuts:
            current = hidden[:, left:right]
            prefix_name = f"prefix-{right}"
            for layer in range(cls.spec.layers):
                prefix = f"blocks.{layer}."
                attn_input = _norm(
                    current, cls.parameters[prefix + "attn_norm"],
                    cls.spec.rms_norm_epsilon)
                scope = AttentionScope(
                    scope_ids[:, left:right], layer, generation,
                    _digest(prefix_name),
                    None if parent is None else _digest(parent))
                attention, caches[layer] = ccgqa(
                    cls._attention_parameters(layer), attn_input,
                    valid[:, left:right], scope, cache=caches[layer], offset=left)
                current = current + attention
                feed_input = _norm(
                    current, cls.parameters[prefix + "ffn_norm"],
                    cls.spec.rms_norm_epsilon)
                activated = mx.maximum(
                    feed_input @ cls.parameters[prefix + "ffn_in"].T, 0)
                current = current + (
                    (activated * activated)
                    @ cls.parameters[prefix + "ffn_out"].T)
                if (layer + 1) % 4 == 0:
                    # Production fingerprints each four-layer B11.1a group,
                    # which materializes MLX's lazy graph at the group
                    # boundary. Match that evaluation schedule so this
                    # witness compares equations rather than fusion choices.
                    mx.eval(current)
            outputs.append(current)
            left = right
            parent = prefix_name
        return mx.concatenate(outputs, axis=1), tuple(caches)

    def test_constructor_and_views_use_only_the_expanded_b01_parameter_specs(self):
        declared = expected_bamf_shapes(self.spec, self.compiled.extents)
        names = tuple(item.name for item in declared)
        self.assertEqual(tuple(self.parameters), names)
        self.assertEqual(
            tuple(item["name"] for item in self.manifest["parameters"]), names)
        self.assertEqual(
            {name.split(".")[0] for name in names},
            {"identity", "features", "frame", "blocks", "depth", "motif",
             "plastic", "refine", "readout"})

        frame = frame_encoder_parameter_view(
            self.parameters, spec=self.spec, extents=self.compiled.extents)
        embedding = embedding_parameter_view(
            self.parameters, spec=self.spec, extents=self.compiled.extents)
        depth = depth_parameter_view(
            self.parameters, spec=self.spec, extents=self.compiled.extents,
            boundary_group=1)
        refinement = refinement_parameter_view(
            self.parameters, spec=self.spec, extents=self.compiled.extents)
        self.assertTrue(all(
            name.startswith(("frame.", "features."))
            and value is self.parameters[name]
            for name, value in frame.items()))
        self.assertTrue(all(
            name.startswith(("identity.bank.", "features."))
            and value is self.parameters[name]
            for name, value in embedding.items()))
        self.assertIs(frame["features.type"], embedding["features.type"])
        self.assertIs(depth["norm"], self.parameters["depth.norm"])
        self.assertIs(refinement["refine.norm"], self.parameters["refine.norm"])

    def test_mixed_atomic_packed_nested_batch_runs_12_layer_forward_and_backward(self):
        row = self.compiled.compiled.rows[1]
        closures = tuple(
            (index, position) for index, position in enumerate(row.positions)
            if position.kind is PositionKind.CLOSURE)
        dispositions = tuple(position.packed.disposition for _, position in closures)
        self.assertEqual(
            dispositions,
            (PackDisposition.EXTENDED, PackDisposition.ATOMIC,
             PackDisposition.EXTENDED))
        child, _atomic, parent = (position.packed.sidecar for _, position in closures)
        self.assertEqual(child.parent_occurrence_id, parent.occurrence_id)

        h0 = compute_compiled_h0(
            self.compiled, self.vectors, self.parameters,
            spec=self.spec, extents=self.compiled.extents).hidden
        final = self._stack(h0)
        self.assertEqual(final.shape, h0.shape)
        self.assertTrue(bool(mx.all(mx.isfinite(final))))

        weights = mx.arange(self.spec.width, dtype=mx.float32)
        gradient = mx.grad(
            lambda hidden: mx.sum(self._stack(hidden) * weights))(h0)
        mx.eval(gradient)
        self.assertTrue(bool(mx.all(mx.isfinite(gradient))))
        self.assertGreater(float(mx.sum(mx.abs(gradient))), 0)
        for index, _position in closures:
            self.assertGreater(float(mx.sum(mx.abs(gradient[1, index]))), 0)

        name = "blocks.0.query"
        def parameter_loss(value):
            current = h0
            valid = mx.array([
                [position is not None for position in padded]
                for padded in self.compiled.compiled.padded_positions
            ], dtype=mx.bool_)
            scope = mx.zeros(valid.shape, dtype=mx.int32)
            for group_index in (1, 2, 3):
                parameters = self._group_parameters(group_index)
                if group_index == 1:
                    parameters[name] = value
                current = run_backbone_group_numerical(
                    current, parameters, group_index=group_index,
                    spec=self.spec, extents=self.compiled.extents,
                    scope_ids=scope, valid=valid, generation="4" * 64,
                    prefix_digest="5" * 64).hidden
            return mx.sum(current * weights)
        parameter_gradient = mx.grad(parameter_loss)(self.parameters[name])
        mx.eval(parameter_gradient)
        self.assertTrue(bool(mx.all(mx.isfinite(parameter_gradient))))
        self.assertGreater(float(mx.sum(mx.abs(parameter_gradient))), 0)

    def test_actual_12_layer_prefix_logits_and_cache_paths_are_causal(self):
        h0 = compute_compiled_h0(
            self.compiled, self.vectors, self.parameters,
            spec=self.spec, extents=self.compiled.extents).hidden
        row_index = 1
        row = self.compiled.compiled.rows[row_index]
        prefix = max(2, len(row.positions) // 2)
        self.assertLess(prefix, len(row.positions))
        prefix_handles = tuple(
            position.cache_identity for position in row.positions[:prefix])
        self.assertEqual(len(prefix_handles), prefix)
        self.assertEqual(len(set(prefix_handles)), prefix)
        self.assertEqual(
            (self.spec.layers, self.spec.depth_groups,
             self.spec.query_heads, self.spec.kv_heads, self.spec.head_dimension),
            (12, 3, 16, 8, 24))

        first = h0.at[row_index, prefix:].add(
            mx.array(3.0, dtype=mx.float32))
        second = h0.at[row_index, prefix:].subtract(
            mx.array(5.0, dtype=mx.float32))
        first_logits = self._control_logits(self._stack(first))[row_index, :prefix]
        second_logits = self._control_logits(self._stack(second))[row_index, :prefix]
        mx.eval(first_logits, second_logits)
        delta = float(mx.max(mx.abs(first_logits - second_logits)))
        self.assertLessEqual(delta, 2e-5)
        np.testing.assert_allclose(
            np.asarray(first_logits), np.asarray(second_logits),
            atol=2e-5, rtol=3e-5)

        hidden = h0[row_index:row_index + 1]
        valid = mx.ones(hidden.shape[:2], dtype=mx.bool_)
        ids = mx.zeros(hidden.shape[:2], dtype=mx.int32)
        generation = execution_generation_digest(
            self.parameters, spec=self.spec, extents=self.compiled.extents)

        production_full = self._stack(h0)[row_index:row_index + 1]
        full, later_caches = self._incremental_12_layer_stack(
            hidden, scope_ids=ids, valid=valid, generation=generation,
            cuts=(hidden.shape[1],))
        np.testing.assert_allclose(
            np.asarray(full), np.asarray(production_full),
            atol=2e-5, rtol=3e-5)
        full_logits = self._control_logits(production_full)

        for cuts in (
            tuple(range(1, hidden.shape[1] + 1)),
            (prefix, hidden.shape[1]),
        ):
            incremental, _ = self._incremental_12_layer_stack(
                hidden, scope_ids=ids, valid=valid, generation=generation,
                cuts=cuts)
            incremental_logits = self._control_logits(incremental)
            np.testing.assert_allclose(
                np.asarray(incremental_logits), np.asarray(full_logits),
                atol=2e-5, rtol=3e-5)

        with self.assertRaises(BilqisError):
            self._incremental_12_layer_stack(
                hidden[:, :prefix], scope_ids=ids[:, :prefix],
                valid=valid[:, :prefix], generation=generation,
                cuts=(prefix,), initial_caches=later_caches)
        fresh_early, _ = self._incremental_12_layer_stack(
            hidden[:, :prefix], scope_ids=ids[:, :prefix],
            valid=valid[:, :prefix], generation=generation,
            cuts=(prefix,))
        fresh_early_logits = self._control_logits(fresh_early)
        np.testing.assert_allclose(
            np.asarray(fresh_early_logits),
            np.asarray(full_logits[:, :prefix]),
            atol=2e-5, rtol=3e-5)


if __name__ == "__main__":
    unittest.main()
