"""C08.1 public resource-planning facade.

Implementation is split by cohesive owner under ``_atlas_resources`` while this
module preserves the historical public import surface.
"""
from bilqis_mlx.semantics._public_identity.module_identity import (
    restore_public_module as _restore_public_module,
)

from ._atlas_resources.contracts import (
    FRAME_STATS_SCHEMA, RESOURCE_ROW_SCHEMA, MEMORY_BUDGET_SCHEMA,
    BATCH_PLAN_SCHEMA, GRADIENT_CHUNK_SCHEMA, ACCUMULATED_GRADIENT_SCHEMA,
    BACKEND_STEP_SCHEMA, TRAINER_ALLOCATION_BYTES, DEFAULT_POSITION_BUDGET,
    MICROBATCH_SIZES, FP32_BYTES, FrameStats, ResourceRow, MemoryBudget, BatchPlan,
)
from ._atlas_resources.planning import (
    estimate_row_activation_bytes, plan_microbatches, indices_for_plan,
)
from ._atlas_resources.gradients import (
    GradientChunk, AccumulatedGradient, BackendStepReceipt,
    accumulate_gradients, apply_one_adamw_step,
)

for _public in (
    FrameStats, ResourceRow, MemoryBudget, BatchPlan, estimate_row_activation_bytes,
    plan_microbatches, indices_for_plan, GradientChunk, AccumulatedGradient,
    BackendStepReceipt, accumulate_gradients, apply_one_adamw_step,
):
    _restore_public_module(_public, __name__)
