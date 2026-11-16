"""C08.1 pure resource and gradient-accumulation contract witnesses."""
from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

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


GENERATION = "fixture:retained-generation"


from bilqis_mlx.runtime.tests.model.resources.helpers import AtlasResourcesFixture, GENERATION, _rows

class AtlasResourcesTests(AtlasResourcesFixture):
    def test_two_cpu_workers_freeze_same_source_packet_without_neural_authority(self):
        packet = {
            "schema": SOURCE_PREFETCH_SCHEMA,
            "identity": "a" * 64,
            "fresh": [{"id": "row:1", "tokens": [1, 2, 3]}],
            "prior": [], "preservation": [],
            "retention_support": [], "teaching_enrichment_rows": [],
        }
        serial = freeze_source_packet(packet)
        with source_prefetch_pool(2) as pool:
            futures = tuple(
                pool.submit(freeze_source_packet, packet)
                for _ in range(2))
            parallel = tuple(future.result(timeout=15) for future in futures)
        self.assertEqual(parallel, (serial, serial))
        self.assertIsInstance(serial.payload, tuple)
        packet["fresh"][0]["tokens"].append(99)
        self.assertNotEqual(serial, freeze_source_packet(packet))
        with_source_receipt = freeze_source_packet({
            **packet, "fresh": [{
                "id": "row:1", "tokens": [1, 2, 3],
                "receipt": {"source_sha256": "f" * 64},
            }],
        })
        self.assertNotEqual(with_source_receipt.digest, serial.digest)
        with self.assertRaises(BilqisError) as caught:
            freeze_source_packet({
                **packet,
                "fresh": [{"id": "row:1", "model_state": "forbidden"}],
            })
        self.assertEqual(caught.exception.context["reason"],
                         "SOURCE_PREFETCH_FORBIDDEN_AUTHORITY")
        with self.assertRaises(BilqisError) as caught:
            source_prefetch_pool(3)
        self.assertEqual(caught.exception.context["reason"],
                         "SOURCE_PREFETCH_WORKER_COUNT_INVALID")

    def test_complete_next_bundle_budget_keeps_100_gib_floor_before_write(self):
        budget = estimate_next_bundle_bytes(
            self.census, manifest_bytes=1_000_000,
            publication_overhead_bytes=10_000_000)
        self.assertEqual(
            budget.total_bytes,
            budget.weights_bytes + budget.optimizer_moments_bytes
            + 1_000_000 + 10_000_000)
        free = budget.total_bytes + RETAINED_DISK_RESERVE_BYTES + 1
        with patch("bilqis_mlx.runtime.disk.shutil.disk_usage",
                   return_value=SimpleNamespace(free=free)):
            report = assert_bundle_headroom(Path("/tmp"), budget)
        self.assertEqual(report["reserve_bytes"],
                         RETAINED_DISK_RESERVE_BYTES)
        self.assertEqual(report["required_next_bundle_bytes"],
                         budget.total_bytes)
        with patch("bilqis_mlx.runtime.disk.shutil.disk_usage",
                   return_value=SimpleNamespace(free=free - 2)):
            with self.assertRaisesRegex(
                    RuntimeError, "DISK_BUDGET_EXHAUSTED"):
                assert_bundle_headroom(Path("/tmp"), budget)
