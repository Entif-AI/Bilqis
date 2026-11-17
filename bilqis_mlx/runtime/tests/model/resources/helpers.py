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


def _rows(count: int, *, positions: int = 64,
          raw_frame_length: int | None = None) -> tuple[ResourceRow, ...]:
    return tuple(ResourceRow(
        row_id="row:" + str(index),
        frame_stats=FrameStats(
            compiled_positions=positions,
            frame_lengths=(raw_frame_length or positions,),
            constituent_expansions=max(1, positions // 4),
            depth_summaries=3,
        ),
        target_decisions=2,
        optimizer_step_seed=73,
        generation_binding=GENERATION,
        training_row_sha256="a" * 64, delivered_content_sha256="b" * 64,
    ) for index in range(count))


class AtlasResourcesFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.topology = ModelTopologySpecV2()
        cls.extents = GenerationExtents(
            1, 1, "a" * 64, "b" * 64, "c" * 64)
        cls.census = bamf_parameter_census(cls.topology, cls.extents)
        cls.budget = MemoryBudget(census=cls.census)
