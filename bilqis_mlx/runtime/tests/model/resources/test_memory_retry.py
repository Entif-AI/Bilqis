"""C08.1 pure resource and gradient-accumulation contract witnesses."""
from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, bamf_parameter_census,
)
from bilqis_mlx.runtime.atlas_training_contracts import (
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
from bilqis_mlx.runtime.training_objective import current_training_objective


GENERATION = "fixture:retained-generation"


from bilqis_mlx.runtime.tests.model.resources.helpers import AtlasResourcesFixture, GENERATION, _rows

class AtlasResourcesTests(AtlasResourcesFixture):
    def test_installed_mlx_memory_getters_are_snapshot_only(self):
        class FakeMLX:
            __version__ = "0.31.1"

            def get_active_memory(self):
                return 123

            def get_cache_memory(self):
                return 45

            def get_peak_memory(self):
                return 678

            def reset_peak_memory(self):
                raise AssertionError("snapshot must not mutate MLX telemetry")

        snapshot = snapshot_mlx_memory(FakeMLX(), observed_at=700)
        self.assertEqual(
            (snapshot.active_bytes, snapshot.cache_bytes,
             snapshot.peak_bytes, snapshot.mlx_version),
            (123, 45, 678, "0.31.1"))

    def test_one_oom_retry_preserves_rows_seed_and_parent_then_exhausts_safely(self):
        rows = _rows(32)
        plan = plan_microbatches(rows, self.topology, self.budget)
        state = RetryState.start(
            plan, retained_candidate_digest="a" * 64,
            optimizer_snapshot_digest="b" * 64)
        restores = []

        def restore(candidate_digest, optimizer_digest, generation):
            restores.append((candidate_digest, optimizer_digest, generation))
            return RestorationReceipt(
                candidate_digest, optimizer_digest, generation,
                restored=True)

        def oom(for_plan, attempt):
            return OOMReceipt(
                failure_id="oom:" + str(attempt),
                failed_microbatch_size=for_plan.microbatch_size,
                source_digest=for_plan.source_digest,
                generation_binding=for_plan.generation_binding,
                optimizer_step_seed=for_plan.optimizer_step_seed,
                peak_allocated_bytes=50 * 1024**3,
                cache_bytes=1024,
                observed_at=720 + attempt,
                exception_class="MemoryError",
            )

        retry = handle_oom(
            state, oom(plan, 0), rows, self.topology, self.budget,
            restore=restore)
        self.assertEqual(retry.status, RetryStatus.RETRY_PENDING)
        self.assertEqual(retry.current_plan.microbatch_size, 16)
        self.assertEqual(retry.current_plan.source_digest, plan.source_digest)
        self.assertEqual(retry.current_plan.logical_row_ids,
                         plan.logical_row_ids)
        self.assertEqual(retry.current_plan.optimizer_step_seed, 73)
        self.assertEqual(retry.retained_candidate_digest, "a" * 64)
        self.assertEqual(retry.optimizer_snapshot_digest, "b" * 64)
        exhausted = handle_oom(
            retry, oom(retry.current_plan, 1), rows,
            self.topology, self.budget, restore=restore)
        self.assertEqual(exhausted.status, RetryStatus.EXHAUSTED)
        self.assertIsNone(exhausted.current_plan)
        self.assertEqual(len(exhausted.failures), 2)
        self.assertEqual(len(restores), 2)
        self.assertEqual(restores[0],
                         ("a" * 64, "b" * 64, GENERATION))
        self.assertEqual(state.status, RetryStatus.PLANNED)
        restored_before_reject = []

        def restore_then_reject(candidate, optimizer, generation):
            restored_before_reject.append(candidate)
            return RestorationReceipt(candidate, optimizer, generation, True)

        with self.assertRaises(BilqisError) as caught:
            handle_oom(
                state, replace(oom(plan, 0), source_digest="0" * 64),
                rows, self.topology, self.budget,
                restore=restore_then_reject)
        self.assertEqual(caught.exception.context["reason"],
                         "BAMF_C08_OOM_SOURCE_DRIFT")
        self.assertEqual(restored_before_reject, ["a" * 64])

    def test_batch_one_oom_restores_parent_without_speculative_second_attempt(self):
        rows = _rows(2)
        row_bytes = estimate_row_activation_bytes(rows[0], self.topology)
        budget = replace(
            self.budget, allocation_bytes=(
                self.budget.resident_bytes + row_bytes
                * self.budget.activation_safety_factor))
        plan = plan_microbatches(rows, self.topology, budget)
        self.assertEqual(plan.microbatch_size, 1)
        state = RetryState.start(
            plan, retained_candidate_digest="a" * 64,
            optimizer_snapshot_digest="b" * 64)
        failure = OOMReceipt(
            "oom:batch1", 1, plan.source_digest, GENERATION, 73,
            50 * 1024**3, 0, 730, "MemoryError")
        restored = []

        def restore(candidate, optimizer, generation):
            restored.append(candidate)
            return RestorationReceipt(candidate, optimizer, generation, True)

        exhausted = handle_oom(
            state, failure, rows, self.topology, budget, restore=restore)
        self.assertEqual(exhausted.status, RetryStatus.EXHAUSTED)
        self.assertIsNone(exhausted.current_plan)
        self.assertEqual(restored, ["a" * 64])
        self.assertEqual(exhausted.retained_candidate_digest, "a" * 64)


class FactoryRetryRestorationTests(AtlasResourcesFixture):
    def test_factory_retry_rejects_optimizer_mutation_during_failed_attempt(self):
        import mlx.core as mx

        from bilqis_mlx.runtime.candidate import retry
        from bilqis_mlx.runtime.training_objective import current_training_objective

        weights = mx.array([1.0])
        optimizer = SimpleNamespace(
            parameters={"weight": weights}, m={}, v={}, update_counts={})
        parent = SimpleNamespace(
            topology=self.topology,
            retained_state=SimpleNamespace(
                optimizer=optimizer,
                optimizer_step=3,
                custody=SimpleNamespace(
                    training_objective_digest=current_training_objective().digest)))
        cache = SimpleNamespace(
            _candidate_identity_sha256="a" * 64, accepted_manifest_sha256="b" * 64)
        rows = _rows(2)
        plan = plan_microbatches(rows, self.topology, self.budget, max_microbatch_size=2)

        fail_allocation = Mock(
            side_effect=RuntimeError("[malloc] Unable to allocate 4096 bytes."))

        def corrupt_then_fail(_plan):
            weights[0] = 2.0
            fail_allocation()

        with patch.object(retry, "_resource_rows", return_value=rows), self.assertRaises(
                BilqisError) as caught:
            retry.execute_with_oom_retry(
                corrupt_then_fail, plan, parent=parent, candidate=None,
                prepared=None, budget=self.budget, cache=cache,
                require_current=lambda: (cache, GENERATION))
        self.assertEqual(caught.exception.context["reason"], "BAMF_C08_RESTORATION_FAILED")
