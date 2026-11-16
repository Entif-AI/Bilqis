"""Content identity for the complete declared BAMF parameter tree."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Mapping
import weakref

import mlx.core as mx
import numpy as np

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.errors import ErrorBus, SCHOOL
from .model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, expected_bamf_shapes,
    validate_bamf_parameters,
)


_EXECUTION_BINDING_ISSUER = object()


def _invalid(reason=None) -> None:
    if reason is None:
        ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def tensor_content_digest(value: mx.array) -> str:
    if type(value) is not mx.array:
        _invalid()
    return hashlib.sha256(np.asarray(mx.stop_gradient(value)).tobytes()).hexdigest()


def bamf_parameter_tree_digest(
    parameters: Mapping[str, mx.array], *, spec: ModelTopologySpecV2,
    extents: GenerationExtents,
) -> str:
    """Hash every declared BAMF tensor by name, shape, dtype and content."""
    if (type(spec) is not ModelTopologySpecV2
            or type(extents) is not GenerationExtents
            or not isinstance(parameters, Mapping)):
        _invalid()
    validate_bamf_parameters(spec, extents, parameters)
    names = tuple(item.name for item in expected_bamf_shapes(spec, extents))
    record = [
        (name, tuple(parameters[name].shape), str(parameters[name].dtype),
         tensor_content_digest(parameters[name]))
        for name in names
    ]
    return hashlib.sha256(json.dumps(
        record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _generation_digest(spec, extents, tree_digest: str) -> str:
    return hashlib.sha256(json.dumps((
        "bilqis.mlx.execution-generation/v2", spec.digest, extents.digest,
        tree_digest,
    ), separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True, init=False)
class ExecutionGenerationBinding:
    """One expensive content proof plus cheap exact-object currentness witnesses."""

    generation_digest: str
    parameter_tree_digest: str
    topology_digest: str
    extents_digest: str
    parameter_names: tuple[str, ...]
    schema_version: str = "bilqis.mlx.execution-generation-binding/v1"
    _parameter_refs: tuple = field(repr=False, compare=False)
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid()

    def __post_init__(self) -> None:
        if (self._issuance is not _EXECUTION_BINDING_ISSUER
                or any(not isinstance(value, str) or len(value) != SHA256_HEX_LENGTH
                       for value in (
                           self.generation_digest, self.parameter_tree_digest,
                           self.topology_digest, self.extents_digest))
                or type(self.parameter_names) is not tuple
                or not self.parameter_names
                or len(self.parameter_names) != len(self._parameter_refs)
                or self.schema_version
                != "bilqis.mlx.execution-generation-binding/v1"):
            _invalid()


def issue_execution_generation_binding(
    parameters: Mapping[str, mx.array], *, spec: ModelTopologySpecV2,
    extents: GenerationExtents, expected_generation: str | None = None,
) -> ExecutionGenerationBinding:
    """Hash one immutable executable state exactly once and bind its tensor objects."""
    validate_bamf_parameters(spec, extents, parameters)
    names = tuple(item.name for item in expected_bamf_shapes(spec, extents))
    tree = bamf_parameter_tree_digest(parameters, spec=spec, extents=extents)
    generation = _generation_digest(spec, extents, tree)
    if expected_generation is not None and generation != expected_generation:
        _invalid()
    binding = object.__new__(ExecutionGenerationBinding)
    for name, value in (
        ("generation_digest", generation),
        ("parameter_tree_digest", tree),
        ("topology_digest", spec.digest),
        ("extents_digest", extents.digest),
        ("parameter_names", names),
        ("schema_version", "bilqis.mlx.execution-generation-binding/v1"),
        ("_parameter_refs", tuple(weakref.ref(parameters[name]) for name in names)),
        ("_issuance", _EXECUTION_BINDING_ISSUER),
    ):
        object.__setattr__(binding, name, value)
    binding.__post_init__()
    return binding


def require_execution_generation_binding(
    binding: ExecutionGenerationBinding,
    parameters: Mapping[str, mx.array], *, spec: ModelTopologySpecV2,
    extents: GenerationExtents,
) -> ExecutionGenerationBinding:
    """Revalidate structure and exact tensor ownership without re-reading tensor bytes."""
    if type(binding) is not ExecutionGenerationBinding:
        _invalid()
    binding.__post_init__()
    validate_bamf_parameters(spec, extents, parameters)
    names = tuple(item.name for item in expected_bamf_shapes(spec, extents))
    if (binding.topology_digest != spec.digest
            or binding.extents_digest != extents.digest
            or binding.parameter_names != names
            or any(ref() is not parameters[name]
                   for name, ref in zip(names, binding._parameter_refs))):
        _invalid("EXECUTION_GENERATION_BINDING_CURRENTNESS_MISMATCH")
    return binding


def _execution_generation_autodiff_rebinder(
    binding: ExecutionGenerationBinding,
    parameters: Mapping[str, mx.array], *,
    spec: ModelTopologySpecV2,
    extents: GenerationExtents,
):
    """Rebind one already-proven immutable state to MLX autodiff trace tensors.

    ``mx.value_and_grad`` supplies the objective with fresh tensor objects for the
    exact input tree.  The expensive content proof therefore belongs outside the
    transform; inside it we only rebind that proof to the trace-owned objects.
    """
    owned = require_execution_generation_binding(
        binding, parameters, spec=spec, extents=extents)
    names = owned.parameter_names

    def rebind(current: Mapping[str, mx.array]) -> ExecutionGenerationBinding:
        validate_bamf_parameters(spec, extents, current)
        current_names = tuple(item.name for item in expected_bamf_shapes(spec, extents))
        if (current_names != names
                or owned.topology_digest != spec.digest
                or owned.extents_digest != extents.digest):
            _invalid()
        rebound = object.__new__(ExecutionGenerationBinding)
        for name, value in (
            ("generation_digest", owned.generation_digest),
            ("parameter_tree_digest", owned.parameter_tree_digest),
            ("topology_digest", owned.topology_digest),
            ("extents_digest", owned.extents_digest),
            ("parameter_names", names),
            ("schema_version", "bilqis.mlx.execution-generation-binding/v1"),
            ("_parameter_refs", tuple(weakref.ref(current[name]) for name in names)),
            ("_issuance", _EXECUTION_BINDING_ISSUER),
        ):
            object.__setattr__(rebound, name, value)
        rebound.__post_init__()
        return rebound

    return rebind


def execution_generation_object_key(
    parameters: Mapping[str, mx.array], *, spec: ModelTopologySpecV2,
    extents: GenerationExtents,
) -> tuple:
    """Cheap process-local lookup key; authority still comes from a binding proof."""
    validate_bamf_parameters(spec, extents, parameters)
    names = tuple(item.name for item in expected_bamf_shapes(spec, extents))
    return (spec.digest, extents.digest, tuple(id(parameters[name]) for name in names))


def execution_generation_digest(
    parameters: Mapping[str, mx.array], *, spec: ModelTopologySpecV2,
    extents: GenerationExtents,
) -> str:
    """Content identity of the current executable model, not retained custody."""
    tree = bamf_parameter_tree_digest(parameters, spec=spec, extents=extents)
    return _generation_digest(spec, extents, tree)
