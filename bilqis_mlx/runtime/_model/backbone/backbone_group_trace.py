"""Live differentiable B11 group execution without forensic byte attestation."""
from dataclasses import dataclass
from typing import Mapping

import mlx.core as mx

from bilqis_mlx.errors import ErrorBus, SCHOOL
from .atlas_attention import AttentionCache, AttentionScope, ccgqa
from .backbone_group_inputs import validated_group_parameters
from .backbone_identity import require_execution_generation_binding
from .model_topology_v2 import GenerationExtents, ModelTopologySpecV2


UNADMITTED_TRACE = "UNADMITTED_TRACE"
_ATTENTION_PARAMETERS = (
    "query", "key", "value", "output", "conv_q", "conv_k", "conv_v")


def _invalid() -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


def _norm(hidden: mx.array, scale: mx.array, epsilon: float) -> mx.array:
    return (hidden * mx.rsqrt(
        mx.mean(hidden * hidden, axis=-1, keepdims=True) + epsilon)
        * scale)


@dataclass(frozen=True)
class BackboneGroupTrace:
    """One live differentiable group result with no forensic byte attestation."""

    hidden: mx.array
    group_index: int
    layer_start: int
    layer_end: int
    attention_caches: tuple[AttentionCache, ...]
    admission_status: str = UNADMITTED_TRACE

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
                or len(self.attention_caches) != self.layer_end - self.layer_start
                or self.admission_status != UNADMITTED_TRACE):
            _invalid()


def run_backbone_group_trace(
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
    sequence_starts: mx.array | None = None,
) -> BackboneGroupTrace:
    """Execute one group without reading tensor bytes back to the host."""
    start, end, _required = validated_group_parameters(
        hidden, parameters, group_index, spec, extents, scope_ids, valid,
        sequence_starts)
    caches = []
    current = hidden
    for layer in range(start, end):
        prefix = f"blocks.{layer}."
        attn_input = _norm(
            current, parameters[prefix + "attn_norm"], spec.rms_norm_epsilon)
        scope = AttentionScope(
            scope_ids, layer, generation, prefix_digest,
            sequence_starts=sequence_starts)
        attention, cache = ccgqa({
                name: parameters[prefix + name]
                for name in _ATTENTION_PARAMETERS},
            attn_input, valid, scope)
        current = current + attention
        feed_input = _norm(
            current, parameters[prefix + "ffn_norm"], spec.rms_norm_epsilon)
        activated = mx.maximum(
            feed_input @ parameters[prefix + "ffn_in"].T, 0)
        current = current + (
            (activated * activated) @ parameters[prefix + "ffn_out"].T)
        caches.append(cache)
    return BackboneGroupTrace(current, group_index, start, end, tuple(caches))


class BackboneTraceSession:
    """Sequential live B11 execution bound to one already-proven generation."""

    def __init__(self, hidden, parameters, *, spec, extents, scope_ids, valid,
                 generation, prefix_digest, sequence_starts=None,
                 execution_binding=None):
        if (type(spec) is not ModelTopologySpecV2
                or type(extents) is not GenerationExtents
                or execution_binding is None):
            _invalid()
        owned = require_execution_generation_binding(
            execution_binding, parameters, spec=spec, extents=extents)
        if owned.generation_digest != generation:
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

    @property
    def results(self):
        return self._results

    def advance(self, *, next_input=None):
        if len(self._results) >= self._spec.depth_groups:
            _invalid()
        require_execution_generation_binding(
            self._execution_binding, self._parameters,
            spec=self._spec, extents=self._extents)
        if next_input is not None:
            if (not self._results or type(next_input) is not mx.array
                    or next_input.shape != self._hidden.shape
                    or next_input.dtype != mx.float32):
                _invalid()
            self._hidden = next_input
        result = run_backbone_group_trace(
            self._hidden, self._parameters, group_index=len(self._results) + 1,
            spec=self._spec, extents=self._extents, scope_ids=self._scope_ids,
            valid=self._valid, generation=self._generation,
            prefix_digest=self._prefix_digest,
            sequence_starts=self._sequence_starts)
        self._hidden = result.hidden
        self._results += (result,)
        return result
