"""C08.1 public resource-planning facade.

Implementation is split by cohesive owner under ``_atlas_resources`` while this
module preserves the historical public import surface.
"""
from bilqis_mlx.semantics._public_identity.module_identity import (
    restore_public_module as _restore_public_module,
)

from .._atlas_resources.contracts import (
    FRAME_STATS_SCHEMA, RESOURCE_ROW_SCHEMA, MEMORY_BUDGET_SCHEMA,
    BATCH_PLAN_SCHEMA, GRADIENT_CHUNK_SCHEMA, ACCUMULATED_GRADIENT_SCHEMA,
    BACKEND_STEP_SCHEMA, TRAINER_ALLOCATION_BYTES, DEFAULT_POSITION_BUDGET,
    MICROBATCH_SIZES, FP32_BYTES, FrameStats, ResourceRow, MemoryBudget, BatchPlan,
)
from .._atlas_resources.planning import (
    estimate_row_activation_bytes, plan_microbatches, indices_for_plan,
)
from .._atlas_resources.gradients import (
    GradientChunk, AccumulatedGradient, BackendStepReceipt,
    accumulate_gradients, apply_one_adamw_step,
)
from .._atlas_resources.distributed_contracts import (
    DistributedExecutionProfile, DistributedPartition, DistributedRank,
    DistributedStepManifest,
)
from .._atlas_resources.distributed import partition_logical_batch
from .._atlas_resources.distributed_backend import (
    DistributedBackendCapability, core_backend_name,
    inspect_distributed_backends, require_distributed_backend,
    validate_distributed_resume, validate_runtime_rank,
)
from .._atlas_resources.distributed_telemetry import (
    DistributedStepTelemetry, TopologyObservation, TopologyUnavailable,
    best_topology,
)
from .._atlas_resources.distributed_receipt import (
    distributed_manifest_path, distributed_manifest_record,
    load_distributed_manifest, load_persisted_distributed_manifest,
    persist_distributed_manifest,
)

for _public in (
    FrameStats, ResourceRow, MemoryBudget, BatchPlan, estimate_row_activation_bytes,
    plan_microbatches, indices_for_plan, GradientChunk, AccumulatedGradient,
    BackendStepReceipt, accumulate_gradients, apply_one_adamw_step,
    DistributedExecutionProfile, DistributedPartition, DistributedRank,
    DistributedStepManifest, partition_logical_batch,
    DistributedBackendCapability, core_backend_name,
    inspect_distributed_backends, require_distributed_backend,
    validate_distributed_resume, validate_runtime_rank, DistributedStepTelemetry,
    TopologyObservation, TopologyUnavailable, best_topology, distributed_manifest_path,
    distributed_manifest_record, load_distributed_manifest,
    load_persisted_distributed_manifest, persist_distributed_manifest,
):
    _restore_public_module(_public, __name__)
