"""C08.1 pure resource and gradient-accumulation contract witnesses."""
from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, bamf_parameter_census,
)
from bilqis_mlx.runtime.atlas_training_adapter import (
    BamfDeliveryProvenance, BamfModelInput, BamfTarget, BamfTrainingRow,
)
from bilqis_mlx.runtime.atlas_resources import (
    BackendStepReceipt, FrameStats, GradientChunk, MemoryBudget, ResourceRow,
    accumulate_gradients, apply_one_adamw_step, estimate_row_activation_bytes,
    indices_for_plan, plan_microbatches,
)
from bilqis_mlx.runtime.atlas_memory_retry import (
    OOMReceipt, RestorationReceipt, RetryState, RetryStatus,
    handle_oom, snapshot_mlx_memory,
)
from bilqis_mlx.runtime.disk import (
    RETAINED_DISK_RESERVE_BYTES, assert_bundle_headroom,
    estimate_next_bundle_bytes,
)
from bilqis_mlx.runtime.source_prefetch import (
    SCHEMA as SOURCE_PREFETCH_SCHEMA,
    freeze_source_packet, source_prefetch_pool,
)
from bilqis_mlx.runtime.c08_gradient_accumulation import (
    accumulate_logical_batch_gradients,
)
from bilqis_mlx.runtime.atlas_model import (
    BamfGradientExecution, BamfMicrobatchGradientExecution,
)


GENERATION = "fixture:retained-generation"


from bilqis_mlx.runtime.tests.model.resources.helpers import AtlasResourcesFixture, GENERATION, _rows

class AtlasResourcesTests(AtlasResourcesFixture):
    def test_real_mlx_tree_accumulation_weights_split_groups_without_clipping(self):
        rows = _rows(3)
        row_bytes = estimate_row_activation_bytes(rows[0], self.topology)
        constrained = replace(
            self.budget, allocation_bytes=(
                self.budget.resident_bytes + 2 * row_bytes
                * self.budget.activation_safety_factor))
        plan = plan_microbatches(rows, self.topology, constrained)
        self.assertEqual(plan.groups, ((0, 1), (2,)))
        values = (1.0, 3.0, 9.0)
        seen = []

        def execute_row(index):
            seen.append(index)
            execution = object.__new__(BamfGradientExecution)
            object.__setattr__(execution, "execution", SimpleNamespace(
                output=SimpleNamespace(generation_binding=GENERATION)))
            object.__setattr__(
                execution, "gradients",
                {"weight": mx.array([values[index], values[index] + 2.0])})
            object.__setattr__(execution, "loss_total", mx.array(values[index]))
            return execution

        with patch.object(BamfGradientExecution, "__post_init__", return_value=None):
            result = accumulate_logical_batch_gradients(plan, execute_row)
        self.assertEqual(seen, [0, 1, 2])
        self.assertTrue(bool(mx.allclose(
            result.gradients["weight"],
            mx.array([13.0 / 3.0, 19.0 / 3.0]),
            rtol=0.0, atol=1e-6)))
        self.assertAlmostEqual(
            float(result.weighted_mean_loss.item()), 13.0 / 3.0, places=6)
        self.assertEqual(result.source_digest, plan.source_digest)
        self.assertEqual(result.generation_binding, GENERATION)

    def test_vectorized_group_counts_one_gradient_launch_and_preserves_group_mean(self):
        rows = _rows(4)
        plan = plan_microbatches(rows, self.topology, self.budget)
        self.assertEqual(plan.groups, ((0, 1, 2, 3),))
        microbatch = object.__new__(BamfMicrobatchGradientExecution)
        object.__setattr__(microbatch, "executions", tuple(
            SimpleNamespace(output=SimpleNamespace(generation_binding=GENERATION))
            for _ in rows))
        object.__setattr__(microbatch, "gradients", {
            "weight": mx.array([4.0, 6.0], dtype=mx.float32)})
        object.__setattr__(microbatch, "mean_loss", mx.array(2.5, dtype=mx.float32))
        seen = []

        def execute_group(group):
            seen.append(group)
            return microbatch

        with patch.object(
                BamfMicrobatchGradientExecution, "__post_init__", return_value=None), \
                patch.object(mx, "eval", wraps=mx.eval) as evaluate:
            result = accumulate_logical_batch_gradients(
                plan, lambda _index: self.fail("scalar fallback launched"),
                execute_group=execute_group)
        self.assertEqual(seen, [(0, 1, 2, 3)])
        self.assertEqual(result.gradient_launches, 1)
        self.assertEqual(result.vectorized_microbatches, 1)
        self.assertEqual(result.materialization_barriers, 1)
        self.assertEqual(result.scalar_fallback_rows, 0)
        self.assertGreaterEqual(result.wall_seconds, 0.0)
        self.assertEqual(evaluate.call_count, 1)
        self.assertEqual(result.loss_executions, microbatch.executions)
        self.assertTrue(bool(mx.array_equal(
            result.gradients["weight"], microbatch.gradients["weight"])))
        self.assertEqual(float(result.weighted_mean_loss.item()), 2.5)

    def test_incompatible_group_reports_scalar_fallback_without_extra_barriers(self):
        rows = _rows(4)
        plan = plan_microbatches(rows, self.topology, self.budget)
        values = (1.0, 2.0, 3.0, 4.0)

        def execute_row(index):
            execution = object.__new__(BamfGradientExecution)
            object.__setattr__(execution, "execution", SimpleNamespace(
                output=SimpleNamespace(generation_binding=GENERATION)))
            object.__setattr__(
                execution, "gradients",
                {"weight": mx.array([values[index]], dtype=mx.float32)})
            object.__setattr__(
                execution, "loss_total", mx.array(values[index], dtype=mx.float32))
            return execution

        with patch.object(BamfGradientExecution, "__post_init__", return_value=None), \
                patch.object(mx, "eval", wraps=mx.eval) as evaluate:
            result = accumulate_logical_batch_gradients(
                plan, execute_row, execute_group=lambda _group: None)
        self.assertEqual(result.gradient_launches, 4)
        self.assertEqual(result.vectorized_microbatches, 0)
        self.assertEqual(result.scalar_fallback_rows, 4)
        self.assertEqual(result.materialization_barriers, 1)
        self.assertEqual(evaluate.call_count, 1)

    def test_weighted_split_gradient_matches_unsplit_and_applies_one_step(self):
        rows = _rows(3)
        row_bytes = estimate_row_activation_bytes(rows[0], self.topology)
        constrained = replace(
            self.budget, allocation_bytes=(
                self.budget.resident_bytes + 2 * row_bytes
                * self.budget.activation_safety_factor))
        split = plan_microbatches(rows, self.topology, constrained)
        whole = plan_microbatches(rows, self.topology, self.budget)
        self.assertEqual(split.groups, ((0, 1), (2,)))
        chunks = (
            GradientChunk((0, 1), (2.0, 4.0), 0.5, 73, GENERATION),
            GradientChunk((2,), (9.0, 11.0), 1.0, 73, GENERATION),
        )
        split_grad = accumulate_gradients(split, chunks, clip_norm=1.0)
        whole_grad = accumulate_gradients(
            whole, (GradientChunk(
                (0, 1, 2), (13.0 / 3.0, 19.0 / 3.0),
                2.0 / 3.0, 73, GENERATION),),
            clip_norm=1.0)
        self.assertEqual(split_grad.gradient, whole_grad.gradient)
        self.assertAlmostEqual(split_grad.weighted_mean_loss, 2.0 / 3.0)
        self.assertAlmostEqual(
            split_grad.gradient[0], 13.0 / math.sqrt(530.0), places=7)
        self.assertAlmostEqual(
            split_grad.gradient[1], 19.0 / math.sqrt(530.0), places=7)
        calls = []

        def backend_apply(gradient, generation_binding, source_digest):
            calls.append((gradient, generation_binding, source_digest))
            return BackendStepReceipt(
                optimizer_steps_applied=1,
                generation_binding=generation_binding,
                source_digest=source_digest,
                gradient_digest=split_grad.gradient_digest,
                new_state_digest="f" * 64,
            )

        receipt = apply_one_adamw_step(split_grad, backend_apply)
        self.assertEqual(len(calls), 1)
        self.assertEqual(receipt.optimizer_steps_applied, 1)
        self.assertEqual(receipt.new_state_digest, "f" * 64)
        with self.assertRaises(BilqisError) as caught:
            apply_one_adamw_step(
                split_grad,
                lambda gradient, generation, source: replace(
                    receipt, gradient_digest="0" * 64))
        self.assertEqual(caught.exception.context["reason"],
                         "BAMF_C08_BACKEND_STEP_DRIFT")

    def test_wrong_generation_seed_or_group_rejects_before_backend_call(self):
        rows = _rows(4)
        plan = plan_microbatches(rows, self.topology, self.budget)
        valid = GradientChunk((0, 1, 2, 3), (1.0,), 0.5, 73, GENERATION)
        for bad in (
            replace(valid, optimizer_step_seed=74),
            replace(valid, generation_binding="foreign:generation"),
            replace(valid, row_indices=(0, 1, 2)),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(BilqisError):
                    accumulate_gradients(plan, (bad,), clip_norm=1.0)
