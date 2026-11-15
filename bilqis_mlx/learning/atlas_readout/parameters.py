"""B10 readout view projected from B01's normative parameter ledger."""
from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled

from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents,
    ModelTopologySpecV2,
    expected_bamf_shapes,
)
from .records import invalid


READOUT_PREFIX = "readout."


def readout_parameter_specs(
        spec: ModelTopologySpecV2,
        extents: GenerationExtents):
    """Return B01-declared readout rows without defining a second tensor ledger."""
    if type(spec) is not ModelTopologySpecV2 or type(extents) is not GenerationExtents:
        invalid()
    return tuple(
        item for item in expected_bamf_shapes(spec, extents)
        if item.name.startswith(READOUT_PREFIX))


def bind_readout_parameters(
        parameters: Mapping[str, mx.array],
        spec: ModelTopologySpecV2,
        extents: GenerationExtents):
    """Validate an exact B10-owned readout view against B01 names/shapes/dtypes."""
    if not isinstance(parameters, Mapping):
        invalid()
    declared = readout_parameter_specs(spec, extents)
    if set(parameters) != {item.name for item in declared}:
        invalid()
    for item in declared:
        value = parameters[item.name]
        if (not isinstance(value, mx.array) or value.dtype != mx.float32
                or tuple(value.shape) != item.shape
                or (host_tensor_validation_enabled()
                    and not bool(mx.all(mx.isfinite(value))))):
            invalid()
    return MappingProxyType(dict((item.name, parameters[item.name]) for item in declared))
