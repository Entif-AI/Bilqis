"""One invariant BAMF operator contract over the current MLX device."""
from __future__ import annotations

from dataclasses import dataclass

import mlx.core as mx

from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2

from .atlas_model_contracts import _invalid


@dataclass(frozen=True)
class Backend:
    """Device placement under one topology and FP32 execution contract."""

    topology: ModelTopologySpecV2
    device: str
    precision: str = "FP32"
    schema_version: str = "bilqis.mlx.b11-backend/v1"

    def __post_init__(self) -> None:
        if (
            type(self.topology) is not ModelTopologySpecV2
            or not isinstance(self.device, str)
            or not self.device
            or self.precision != "FP32"
            or self.schema_version != "bilqis.mlx.b11-backend/v1"
        ):
            _invalid("B11_BACKEND_INVALID")

    def forward(
            self, params, compiled_batch, answer_plan, mode, cache=None, *,
            execution_binding=None):
        from .atlas_model_forward import _forward_bamf_impl

        return _forward_bamf_impl(
            self, params, compiled_batch, answer_plan, mode, cache,
            execution_binding=execution_binding)

    def value_and_grad(
            self, params, compiled_batch, answer_plan, targets, mask, cache=None, *,
            salience_supervision=None):
        from .atlas_model_training import _bamf_value_and_grad_impl

        return _bamf_value_and_grad_impl(
            self, params, compiled_batch, answer_plan, targets, mask, cache,
            salience_supervision=salience_supervision)

    def microbatch_value_and_grad(
            self, params, row_batches, answer_plans, targets, masks, cache=None, *,
            salience_supervision=None):
        from .atlas_model_microbatch import _bamf_microbatch_value_and_grad_impl

        return _bamf_microbatch_value_and_grad_impl(
            self, params, row_batches, answer_plans, targets, masks, cache,
            salience_supervision=salience_supervision)


def model_backend(topology) -> Backend:
    """Select the current MLX device without changing the model contract."""
    if type(topology) is not ModelTopologySpecV2:
        _invalid("B11_BACKEND_TOPOLOGY_REQUIRED")
    topology.__post_init__()
    return Backend(topology, str(mx.default_device()))


__all__ = ("Backend", "model_backend")
