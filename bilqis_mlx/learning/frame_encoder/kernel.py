"""Kernel for the existing frame encoder contract."""
from __future__ import annotations

from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.runtime.model_topology_v2 import expected_bamf_shapes
import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled
from .contracts import (
    INNER, WIDTH, _invalid,
)


def _norm(value, gamma):
    return value * mx.rsqrt(mx.mean(value*value, axis=-1, keepdims=True) +
                           ModelTopologySpecV2.rms_norm_epsilon) * gamma


def _encode_one(members, factors, parameters):
    u = members @ parameters["frame.member_value"].T
    q = factors.schema128 @ parameters["frame.query_schema"].T
    k = members @ parameters["frame.member_key"].T
    attention = mx.softmax((q @ k.T) / INNER**.5, axis=-1)
    query = u @ parameters["frame.interact_query"].T
    key = u @ parameters["frame.interact_key"].T
    value = u @ parameters["frame.interact_value"].T
    interaction = mx.softmax((query @ key.T) / INNER**.5, axis=-1) @ value
    v = _norm(u + interaction @ parameters["frame.interact_output"].T,
              parameters["frame.interact_norm"])
    pooled = attention @ u + mx.sigmoid(parameters["frame.pool_gate"]) * (attention @ v)
    summary = (factors.schema128 + factors.mean_role128) / 2
    return _norm(pooled @ parameters["frame.project_output"].T +
                 summary @ parameters["frame.project_summary"].T, parameters["frame.norm"])


def _validate_vectors(atom_vectors, counts):
    if (type(atom_vectors) is not tuple or len(atom_vectors) != len(counts) or
            any(type(row) is not tuple or len(row) != len(count_row)
                for row, count_row in zip(atom_vectors, counts))):
        _invalid()
    for row, count_row in zip(atom_vectors, counts):
        for members, count in zip(row, count_row):
            if (not isinstance(members, mx.array) or members.shape != (count, WIDTH) or
                    members.dtype != mx.float32 or (host_tensor_validation_enabled()
                    and not bool(mx.all(mx.isfinite(members))))):
                _invalid()


def _validate_encoder_parameters(parameters, extents):
    declarations = tuple(item for item in expected_bamf_shapes(ModelTopologySpecV2(), extents)
                         if item.name.startswith(("frame.", "features.")))
    if ({name for name in parameters if name.startswith(("frame.", "features."))} !=
            {item.name for item in declarations}):
        _invalid()
    for item in declarations:
        tensor = parameters[item.name]
        if not isinstance(tensor, mx.array) or tensor.shape != item.shape or tensor.dtype != mx.float32:
            _invalid()
    values = tuple(parameters[item.name] for item in declarations)
    if (host_tensor_validation_enabled()
            and not all(bool(mx.all(mx.isfinite(value))) for value in values)):
        _invalid()
