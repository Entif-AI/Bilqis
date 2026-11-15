"""B11.1a fixed four-layer numerical group; deliberately not a producer seal.

This module executes the selected B01/B04 equations. It does not authenticate
source h0, model generation, motif ordering or B13 custody. B05 must not
accept its result as completed-backbone provenance.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
import hashlib
import json
import numpy as np
from typing import Mapping

import mlx.core as mx

from bilqis_mlx.errors import ErrorBus, SCHOOL
from .atlas_attention import AttentionCache, AttentionScope, ccgqa
from .backbone_identity import (
    bamf_parameter_tree_digest, require_execution_generation_binding,
    tensor_content_digest,
)
from .backbone_group_inputs import validated_group_parameters
from .model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, expected_bamf_shapes,
)


UNADMITTED_NUMERICAL = "UNADMITTED_NUMERICAL"
_ATTENTION_PARAMETERS = (
    "query", "key", "value", "output", "conv_q", "conv_k", "conv_v")


def _invalid() -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


def _norm(hidden: mx.array, scale: mx.array, epsilon: float) -> mx.array:
    return (hidden * mx.rsqrt(
        mx.mean(hidden * hidden, axis=-1, keepdims=True) + epsilon)
        * scale)


@dataclass(frozen=True)
class UnadmittedGroupNumerical:
    hidden: mx.array
    group_index: int
    layer_start: int
    layer_end: int
    attention_caches: tuple[AttentionCache, ...]
    parameter_content_digest: str = ""
    full_parameter_tree_digest: str = ""
    scope_content_digest: str = ""
    input_content_digest: str = ""
    cache_chain_digest: str = ""
    predecessor_digest: str = ""
    execution_digest: str = ""
    admission_status: str = UNADMITTED_NUMERICAL

    def __post_init__(self) -> None:
        if (type(self.hidden) is not mx.array
                or self.hidden.dtype != mx.float32
                or self.hidden.ndim != 3
                or type(self.group_index) is not int
                or type(self.layer_start) is not int
                or type(self.layer_end) is not int
                or self.layer_start < 0
                or self.layer_end <= self.layer_start
                or type(self.attention_caches) is not tuple
                or len(self.attention_caches)
                != self.layer_end - self.layer_start
                or self.admission_status != UNADMITTED_NUMERICAL
                or any(len(value) != 64 for value in (self.parameter_content_digest, self.full_parameter_tree_digest,
                    self.scope_content_digest, self.input_content_digest, self.cache_chain_digest, self.predecessor_digest, self.execution_digest))):
            _invalid()


def _hash_record(record: object) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _content_digest(value: mx.array) -> str:
    # Fingerprints never replace the differentiable original tensor.
    return tensor_content_digest(value)


def _group_parameter_digest(parameters: Mapping[str, mx.array], names: tuple[str, ...]) -> str:
    return _hash_record([(name, tuple(parameters[name].shape), str(parameters[name].dtype),
                          _content_digest(parameters[name])) for name in names])


def _owned_parameter_tree_digest(parameters, spec, extents, execution_binding=None) -> str:
    """Use full-model identity when present; preserve B04's local numerical slice."""
    expected = tuple(item.name for item in expected_bamf_shapes(spec, extents))
    if set(parameters) == set(expected):
        if execution_binding is not None:
            return require_execution_generation_binding(
                execution_binding, parameters, spec=spec, extents=extents,
            ).parameter_tree_digest
        return bamf_parameter_tree_digest(parameters, spec=spec, extents=extents)
    if execution_binding is not None:
        _invalid()
    return _group_parameter_digest(parameters, tuple(sorted(parameters)))


def _cache_chain_digest(caches: tuple[AttentionCache, ...]) -> str:
    return _hash_record([dict(cache.to_record(), key=_content_digest(cache.key),
                              value=_content_digest(cache.value)) for cache in caches])


def run_backbone_group_numerical(
    hidden: mx.array,
    parameters: Mapping[str, mx.array],
    *,
    group_index: int,
    spec: ModelTopologySpecV2,
    extents: GenerationExtents,
    scope_ids: mx.array,
    valid: mx.array,
    generation: str,
    prefix_digest: str,
    prior: UnadmittedGroupNumerical | None = None,
    sequence_starts: mx.array | None = None,
    execution_binding=None,
) -> UnadmittedGroupNumerical:
    """Execute standalone numerical group; caller predecessors are never authority."""
    if prior is not None:
        _invalid()
    start, end, required = validated_group_parameters(
        hidden, parameters, group_index, spec, extents, scope_ids, valid, sequence_starts)
    parameter_digest = _group_parameter_digest(parameters, tuple(sorted(required)))
    full_digest = _owned_parameter_tree_digest(
        parameters, spec, extents, execution_binding)
    if (execution_binding is not None
            and execution_binding.generation_digest != generation):
        _invalid()
    scope_digest = _hash_record({"scope": _content_digest(scope_ids),
                                 "valid": _content_digest(valid),
                                 "starts": None if sequence_starts is None else _content_digest(sequence_starts),
                                 "generation": generation, "prefix": prefix_digest})
    caches = []
    current = hidden
    for layer in range(start, end):
        prefix = f"blocks.{layer}."
        attn_input = _norm(
            current, parameters[prefix + "attn_norm"],
            spec.rms_norm_epsilon)
        scope = AttentionScope(
            scope_ids, layer, generation, prefix_digest, sequence_starts=sequence_starts)
        attention, cache = ccgqa({
                name: parameters[prefix + name]
                for name in _ATTENTION_PARAMETERS},
            attn_input, valid, scope)
        current = current + attention
        feed_input = _norm(
            current, parameters[prefix + "ffn_norm"],
            spec.rms_norm_epsilon)
        activated = mx.maximum(
            feed_input @ parameters[prefix + "ffn_in"].T, 0)
        current = current + (
            (activated * activated) @ parameters[prefix + "ffn_out"].T)
        caches.append(cache)
    cache_digest = _cache_chain_digest(tuple(caches))
    predecessor = prior.execution_digest if prior is not None else _content_digest(hidden)
    execution_digest = _hash_record({
        "group": group_index, "layer_start": start, "layer_end": end,
        "topology": spec.digest, "extents": extents.digest,
        "generation_claim": generation, "prefix_claim": prefix_digest,
        "parameters": parameter_digest, "full_parameters": full_digest,
        "scope": scope_digest, "caches": cache_digest,
        "input": _content_digest(hidden), "output": _content_digest(current),
        "predecessor": predecessor, "status": UNADMITTED_NUMERICAL,
    })
    return UnadmittedGroupNumerical(current, group_index, start, end, tuple(caches),
                                    parameter_digest, full_digest, scope_digest,
                                    _content_digest(hidden), cache_digest, predecessor, execution_digest)


class UnadmittedBackboneSession:
    """Own a single sequential numerical execution, never a B05 credential.

    No API accepts a predecessor result, group number or output tensor once
    created. The session owns current hidden and the exact parameter mapping.
    """

    def __init__(self, hidden, parameters, *, spec, extents, scope_ids, valid,
                 generation, prefix_digest, sequence_starts=None,
                 execution_binding=None):
        if type(spec) is not ModelTopologySpecV2 or type(extents) is not GenerationExtents:
            _invalid()
        self._hidden = hidden
        self._parameters = dict(parameters)
        self._spec = spec
        self._extents = extents
        self._scope_ids = scope_ids
        self._valid = valid
        self._generation = generation
        self._prefix_digest = prefix_digest
        self._sequence_starts = sequence_starts
        self._execution_binding = execution_binding
        self._results = ()
        self._tree_digest = _owned_parameter_tree_digest(
            self._parameters, self._spec, self._extents, self._execution_binding)
        if (self._execution_binding is not None
                and self._execution_binding.generation_digest != self._generation):
            _invalid()

    @property
    def results(self):
        return self._results

    @property
    def parameter_tree_digest(self):
        """Observed content identity of the exact B01 block tree this session owns."""
        return self._tree_digest

    def advance(self, *, next_input=None):
        if len(self._results) >= self._spec.depth_groups:
            _invalid()
        if next_input is not None:
            if (not self._results or type(next_input) is not mx.array
                    or next_input.shape != self._hidden.shape
                    or next_input.dtype != mx.float32
                    or not bool(mx.all(mx.isfinite(next_input)))):
                _invalid()
            self._hidden = next_input
        if _owned_parameter_tree_digest(
                self._parameters, self._spec, self._extents,
                self._execution_binding) != self._tree_digest:
            _invalid()
        group_index = len(self._results) + 1
        result = run_backbone_group_numerical(
            self._hidden, self._parameters, group_index=group_index,
            spec=self._spec, extents=self._extents,
            scope_ids=self._scope_ids, valid=self._valid,
            generation=self._generation, prefix_digest=self._prefix_digest,
            sequence_starts=self._sequence_starts,
            execution_binding=self._execution_binding)
        if result.full_parameter_tree_digest != self._tree_digest:
            _invalid()
        if self._results:
            previous = self._results[-1]
            result = dataclasses.replace(result, predecessor_digest=previous.execution_digest)
            result = dataclasses.replace(result, execution_digest=_hash_record({
                "group": result.group_index, "layer_start": result.layer_start,
                "layer_end": result.layer_end, "topology": self._spec.digest,
                "extents": self._extents.digest, "generation_claim": self._generation,
                "prefix_claim": self._prefix_digest, "parameters": result.parameter_content_digest,
                "full_parameters": result.full_parameter_tree_digest,
                "scope": result.scope_content_digest, "caches": result.cache_chain_digest,
                "input": result.input_content_digest, "output": _content_digest(result.hidden),
                "predecessor": previous.execution_digest, "status": UNADMITTED_NUMERICAL}))
        self._hidden = result.hidden
        self._results += (result,)
        return result
