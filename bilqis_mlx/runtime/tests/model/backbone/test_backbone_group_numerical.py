"""B11.1a fixed group execution, without producer admission."""
from dataclasses import replace
import unittest
from unittest.mock import patch

import mlx.core as mx
import numpy as np

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.backbone_group_numerical import (
    BackboneGroupTrace, UnadmittedGroupNumerical, UnadmittedBackboneSession,
    run_backbone_group_numerical, run_backbone_group_trace,
)
from bilqis_mlx.runtime import backbone_group_numerical as backbone_numerical
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, expected_bamf_shapes,
)
from bilqis_mlx.runtime.autodiff_trace import defer_host_tensor_validation
from .autodiff_hot_path_probe import HotPathProbe


SPEC = ModelTopologySpecV2()
EXTENTS = GenerationExtents(1, 1, "a" * 64, "b" * 64, "c" * 64)


def _params():
    rng = np.random.default_rng(587)
    values = {}
    for item in expected_bamf_shapes(SPEC, EXTENTS):
        if not item.name.startswith("blocks."):
            continue
        if int(item.name.split(".")[1]) >= 8:
            continue
        if item.name.endswith("_norm"):
            values[item.name] = mx.ones(item.shape, dtype=mx.float32)
        else:
            values[item.name] = mx.array(
                rng.normal(0, 0.01, item.shape).astype(np.float32))
    return values


def _run(hidden, params, group_index=1):
    return run_backbone_group_numerical(
        hidden, params, group_index=group_index,
        spec=SPEC, extents=EXTENTS,
        scope_ids=mx.zeros(hidden.shape[:2], dtype=mx.int32),
        valid=mx.ones(hidden.shape[:2], dtype=mx.bool_),
        generation="d" * 64, prefix_digest="e" * 64)


class BackboneGroupNumericalTests(unittest.TestCase):
    def test_live_trace_keeps_tensor_content_attestation_out_of_autodiff(self):
        params = _params()
        hidden = mx.arange(4 * SPEC.width, dtype=mx.float32).reshape(
            1, 4, SPEC.width) / 1000

        def objective(input_hidden):
            with patch(
                "bilqis_mlx.runtime.backbone_group_numerical._content_digest",
                side_effect=AssertionError("forensic content digest entered live trace"),
            ):
                result = run_backbone_group_trace(
                    input_hidden, params, group_index=1, spec=SPEC, extents=EXTENTS,
                    scope_ids=mx.zeros(input_hidden.shape[:2], dtype=mx.int32),
                    valid=mx.ones(input_hidden.shape[:2], dtype=mx.bool_),
                    generation="d" * 64, prefix_digest="e" * 64)
                self.assertIs(type(result), BackboneGroupTrace)
                return mx.sum(result.hidden)

        gradient = mx.grad(objective)(hidden)
        self.assertEqual(gradient.shape, hidden.shape)
        self.assertTrue(bool(mx.all(mx.isfinite(gradient))))

    def test_disposable_hot_path_probe_reports_trace_cost_classes(self):
        params = _params()
        hidden = mx.arange(4 * SPEC.width, dtype=mx.float32).reshape(
            1, 4, SPEC.width) / 1000

        def synthetic_step():
            with defer_host_tensor_validation():
                return backbone_numerical.run_backbone_group_trace(
                    hidden, params, group_index=1, spec=SPEC, extents=EXTENTS,
                    scope_ids=mx.zeros(hidden.shape[:2], dtype=mx.int32),
                    valid=mx.ones(hidden.shape[:2], dtype=mx.bool_),
                    generation="d" * 64, prefix_digest="e" * 64)

        result, report = HotPathProbe().measure_step(synthetic_step)
        self.assertIs(type(result), BackboneGroupTrace)
        self.assertEqual(report.forward_group_executions, 1)
        self.assertEqual(report.host_readbacks, 0)
        self.assertEqual(report.full_tree_hashes, 0)
        self.assertEqual(report.validation_synchronizations, 0)
        self.assertGreater(report.wall_seconds, 0.0)

    def test_four_real_layers_emit_only_unadmitted_numerical_result(self):
        params = _params()
        hidden = mx.arange(4 * SPEC.width, dtype=mx.float32).reshape(
            1, 4, SPEC.width) / 1000
        first = _run(hidden, params)
        self.assertIs(type(first), UnadmittedGroupNumerical)
        self.assertEqual(first.admission_status, "UNADMITTED_NUMERICAL")
        self.assertEqual((first.group_index, first.layer_start, first.layer_end),
                         (1, 0, 4))
        self.assertEqual(first.hidden.shape, hidden.shape)
        self.assertEqual(len(first.attention_caches), 4)
        self.assertTrue(bool(mx.all(mx.isfinite(first.hidden))))
        self.assertGreater(float(mx.sum(mx.abs(first.hidden-hidden))), 0)
        second = _run(first.hidden, params, group_index=2)
        self.assertEqual((second.layer_start, second.layer_end), (4, 8))
        self.assertEqual(len(second.attention_caches), 4)
        self.assertTrue(bool(mx.all(mx.isfinite(second.hidden))))

    def test_causal_prefix_isolation_and_source_gradients(self):
        params = _params()
        hidden = mx.arange(4 * SPEC.width, dtype=mx.float32).reshape(
            1, 4, SPEC.width) / 1000
        future = mx.ones((1, 1, SPEC.width), dtype=mx.float32) * 100
        prefix = _run(hidden, params).hidden
        extended = _run(mx.concatenate((hidden, future), axis=1), params).hidden
        self.assertTrue(bool(mx.all(mx.abs(prefix-extended[:, :4]) < 1e-4)))
        def loss(input_hidden):
            return mx.sum(_run(input_hidden, params).hidden
                          * mx.arange(SPEC.width, dtype=mx.float32))
        derivative = mx.grad(loss)(hidden)
        self.assertTrue(bool(mx.all(mx.isfinite(derivative))))
        self.assertGreater(float(mx.sum(mx.abs(derivative))), 0)
        for name in ("blocks.0.query", "blocks.0.ffn_in"):
            with self.subTest(parameter=name):
                def parameter_loss(value):
                    changed = dict(params)
                    changed[name] = value
                    return mx.sum(_run(hidden, changed).hidden
                                  * mx.arange(
                                      SPEC.width, dtype=mx.float32))
                parameter_grad = mx.grad(parameter_loss)(params[name])
                self.assertTrue(bool(mx.all(mx.isfinite(parameter_grad))))
                self.assertGreater(
                    float(mx.sum(mx.abs(parameter_grad))), 0)

    def test_executed_parameter_content_and_cache_chain_distinguish_models(self):
        params = _params()
        hidden = mx.arange(4*SPEC.width, dtype=mx.float32).reshape(1, 4, SPEC.width)/1000
        first = _run(hidden, params)
        again = _run(hidden, params)
        self.assertEqual(first.execution_digest, again.execution_digest)
        reloaded = _run(hidden, _params())
        self.assertEqual(first.cache_chain_digest, reloaded.cache_chain_digest)
        self.assertEqual(first.execution_digest, reloaded.execution_digest)
        self.assertEqual(len(first.parameter_content_digest), 64)
        self.assertEqual(len(first.cache_chain_digest), 64)
        changed = dict(params)
        changed["blocks.0.query"] = changed["blocks.0.query"].at[0, 0].add(.01)
        other = _run(hidden, changed)
        self.assertNotEqual(first.parameter_content_digest, other.parameter_content_digest)
        self.assertNotEqual(first.execution_digest, other.execution_digest)
        self.assertEqual(first.admission_status, "UNADMITTED_NUMERICAL")
        session = UnadmittedBackboneSession(hidden, params, spec=SPEC, extents=EXTENTS,
            scope_ids=mx.zeros((1,4),dtype=mx.int32), valid=mx.ones((1,4),dtype=mx.bool_),
            generation="d"*64, prefix_digest="e"*64)
        session_first = session.advance()
        second = session.advance()
        self.assertEqual(second.predecessor_digest, session_first.execution_digest)
        self.assertEqual(second.layer_start, 4)
        with self.assertRaises(BilqisError):
            run_backbone_group_numerical(first.hidden, params, group_index=2,
                spec=SPEC, extents=EXTENTS, scope_ids=mx.zeros((1,4),dtype=mx.int32),
                valid=mx.ones((1,4),dtype=mx.bool_),generation="d"*64,
                prefix_digest="e"*64,prior=first)

    def test_sequence_starts_match_direct_b04_and_break_history(self):
        from bilqis_mlx.runtime.atlas_attention import AttentionScope, ccgqa
        params = _params()
        hidden = mx.arange(4*SPEC.width, dtype=mx.float32).reshape(1, 4, SPEC.width)/1000
        starts = mx.array([[False, False, True, False]])
        scope = mx.zeros((1,4), dtype=mx.int32)
        valid = mx.ones((1,4), dtype=mx.bool_)
        result = run_backbone_group_numerical(hidden, params, group_index=1,
            spec=SPEC, extents=EXTENTS, scope_ids=scope, valid=valid,
            sequence_starts=starts, generation="d"*64, prefix_digest="e"*64)
        direct_scope = AttentionScope(scope, 0, "d"*64, "e"*64, sequence_starts=starts)
        prefix = "blocks.0."
        normed = hidden * mx.rsqrt(mx.mean(hidden*hidden, axis=-1,keepdims=True)+SPEC.rms_norm_epsilon)*params[prefix+"attn_norm"]
        direct, _ = ccgqa({name:params[prefix+name] for name in
            ("query","key","value","output","conv_q","conv_k","conv_v")}, normed, valid, direct_scope)
        self.assertEqual(result.attention_caches[0].prefix_digest, "e"*64)
        self.assertTrue(bool(mx.all(mx.isfinite(direct))))
        no_starts = run_backbone_group_numerical(hidden, params, group_index=1,
            spec=SPEC, extents=EXTENTS, scope_ids=scope, valid=valid,
            generation="d"*64, prefix_digest="e"*64)
        self.assertGreater(float(mx.max(mx.abs(result.hidden-no_starts.hidden))), 1e-7)
        self.assertNotEqual(result.execution_digest, no_starts.execution_digest)

    def test_forged_predecessor_and_mixed_tree_fail(self):
        params = _params()
        hidden = mx.arange(4*SPEC.width,dtype=mx.float32).reshape(1,4,SPEC.width)/1000
        session = UnadmittedBackboneSession(hidden,params,spec=SPEC,extents=EXTENTS,
            scope_ids=mx.zeros((1,4),dtype=mx.int32),valid=mx.ones((1,4),dtype=mx.bool_),
            generation="d"*64,prefix_digest="e"*64)
        first = session.advance()
        forged = replace(first,execution_digest="f"*64,
                         full_parameter_tree_digest="f"*64)
        with self.assertRaises(BilqisError):
            run_backbone_group_numerical(first.hidden, params,group_index=2,
                spec=SPEC,extents=EXTENTS,scope_ids=mx.zeros((1,4),dtype=mx.int32),
                valid=mx.ones((1,4),dtype=mx.bool_),generation="d"*64,
                prefix_digest="e"*64,prior=forged)
        changed = dict(params)
        changed["blocks.4.query"] = changed["blocks.4.query"].at[0,0].add(.01)
        session._parameters["blocks.4.query"] = changed["blocks.4.query"]
        with self.assertRaises(BilqisError):
            session.advance()
        self.assertEqual(len(session.results),1)



if __name__ == "__main__":
    unittest.main()
