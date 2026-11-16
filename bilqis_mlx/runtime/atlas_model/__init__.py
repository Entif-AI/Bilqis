"""Public B11 BAMF model execution surface.

Implementation is split by ownership under ``runtime/_model``. This module keeps
the established import path stable for callers and tests.
"""
from bilqis_mlx.runtime.atlas_model_backend import Backend, model_backend
from bilqis_mlx.runtime.atlas_model_contracts import (
    BamfCompiledBatch,
    BamfGradientExecution,
    BamfLossExecution,
    BamfMicrobatchGradientExecution,
    require_bamf_loss_execution,
)
from bilqis_mlx.runtime.atlas_model_forward import forward_bamf
from bilqis_mlx.runtime.atlas_model_training import (
    bamf_value_and_grad,
    loss_bearing_bamf,
)
from bilqis_mlx.runtime.atlas_model_microbatch import (
    bamf_microbatch_value_and_grad,
    microbatch_compatible,
)
from bilqis_mlx.runtime.atlas_training_authority import (
    BamfTrainingAuthority,
    bind_compiled_training_batch,
)

__all__ = (
    "Backend",
    "BamfCompiledBatch",
    "BamfLossExecution",
    "BamfGradientExecution",
    "BamfMicrobatchGradientExecution",
    "BamfTrainingAuthority",
    "model_backend",
    "forward_bamf",
    "loss_bearing_bamf",
    "bamf_value_and_grad",
    "bamf_microbatch_value_and_grad",
    "microbatch_compatible",
    "require_bamf_loss_execution",
    "bind_compiled_training_batch",
)
