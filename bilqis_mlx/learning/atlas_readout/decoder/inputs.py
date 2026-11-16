"""Causal memory and source-bound semantic inputs; no producer admission."""
from dataclasses import dataclass
from collections.abc import Mapping
import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled
from bilqis_mlx.runtime.model_topology_v2 import GenerationExtents
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.context_eligibility import ApprovedContextProjection
from bilqis_mlx.semantics.frame_compiler import CompiledFrameBatch
from bilqis_mlx.learning.frame_embeddings.banks import SemanticBankView, _validate_banks
from ..plan import AnswerPlan, DecisionKind
from ..records import ValueHeadBinding, invalid
from ..roles import _validate_domain
from ..values import value_logits


_DECODER_HIDDEN_RANK = 2
_DECODER_HIDDEN_WIDTH = 768
_ANCHOR_ARITY = 2
_EPISTEMIC_VALUE_COUNT = 5


@dataclass(frozen=True)
class DecoderMemory:
    hidden: mx.array
    row_identities: tuple[tuple, ...]
    compiled: CompiledFrameBatch
    generation_binding: str
    anchors: tuple[tuple[str, int], ...] = ()
    schema_version: str = 'bilqis.mlx.decoder-memory/v1'

    def __post_init__(self):
        if (self.schema_version != 'bilqis.mlx.decoder-memory/v1'
                or type(self.compiled) is not CompiledFrameBatch
                or type(self.generation_binding) is not str or not self.generation_binding
                or not isinstance(self.hidden, mx.array) or self.hidden.ndim != _DECODER_HIDDEN_RANK
                or self.hidden.shape[1] != _DECODER_HIDDEN_WIDTH or self.hidden.dtype != mx.float32
                or type(self.row_identities) is not tuple
                or len(self.row_identities) != self.hidden.shape[0]
                or type(self.anchors) is not tuple):
            invalid()
        self.compiled.__post_init__()
        count = len(self.compiled.positions)
        if (not 0 < count <= self.hidden.shape[0]
                or self.row_identities[:count] != tuple(p.cache_identity for p in self.compiled.positions)
                or (host_tensor_validation_enabled()
                    and not bool(mx.all(mx.isfinite(self.hidden[:count]))))):
            invalid()
        for pair in self.anchors:
            if (type(pair) is not tuple or len(pair) != _ANCHOR_ARITY
                    or type(pair[0]) is not str or not pair[0]
                    or type(pair[1]) is not int or not 0 <= pair[1] < count):
                invalid()
        if len({pair[0] for pair in self.anchors}) != len(self.anchors):
            invalid()


@dataclass(frozen=True)
class ReadoutSemantics:
    features: AtlasFeatures
    banks: tuple[SemanticBankView, ...]
    extents: GenerationExtents
    epistemic_binding: ValueHeadBinding | None = None
    schema_version: str = 'bilqis.mlx.readout-semantics/v1'

    def __post_init__(self):
        if (self.schema_version != 'bilqis.mlx.readout-semantics/v1'
                or type(self.features) is not AtlasFeatures
                or type(self.extents) is not GenerationExtents
                or self.extents.factor_map_digest != self.features.digest
                or "NONE" not in dict(self.features.role_map)
                or self.epistemic_binding is not None
                and type(self.epistemic_binding) is not ValueHeadBinding):
            invalid()
        _validate_banks(self.banks)
        for bank in self.banks:
            bank.__post_init__()
        if (len(self.banks) != self.extents.semantic_bank_count
                or any(b.semantic_release != self.features.semantic_release
                       or b.active_semantic_digest != self.extents.active_semantic_digest
                       for b in self.banks)):
            invalid()


def _epistemic(semantics, plan):
    decisions = tuple(d for d in plan.decisions if d.kind is DecisionKind.EPISTEMIC)
    if not decisions:
        return
    binding = semantics.epistemic_binding
    if (binding is None or binding.kind == 'semantic_token'
            or len(binding.values) != _EPISTEMIC_VALUE_COUNT
            or binding.snapshot.bundle_id != plan.snapshot.bundle_id
            or binding.snapshot.source_bundle_id != plan.snapshot.source_bundle_id
            or binding.semantic_release != plan.snapshot.release_sha256
            or binding.active_semantic_digest != plan.snapshot.active_set_sha256
            or any(not set(d.legal_values) <= set(binding.values) for d in decisions)):
        invalid()
    value_logits(mx.zeros((_DECODER_HIDDEN_WIDTH,),dtype=mx.float32), binding, semantics.banks)


def validate_decoder_inputs(memory, context, plan, semantics, parameters):
    if (type(memory) is not DecoderMemory
            or (context is not None and type(context) is not ApprovedContextProjection)
            or type(plan) is not AnswerPlan or type(semantics) is not ReadoutSemantics
            or not isinstance(parameters, Mapping)):
        invalid()
    memory.__post_init__()
    if context is not None:
        context.__post_init__()
    plan.__post_init__()
    semantics.__post_init__()
    if not plan.route_only:
        _validate_domain(plan.allowed_output_schema, semantics.features)
    if (memory.generation_binding != plan.generation_binding
            or len(memory.compiled.positions) != plan.input_prefix_end
            or memory.compiled.semantic_release != plan.snapshot.release_sha256
            or (context is None) != (memory.compiled.context_digest is None)
            or (context is not None and context.digest != memory.compiled.context_digest)
            or plan.source_span.end > memory.compiled.visible_end
            or semantics.extents.active_semantic_digest != plan.snapshot.active_set_sha256
            or not {key for key, _ in memory.anchors} <= {d.decision_id for d in plan.decisions}
            or any(parameters.get(f'identity.bank.{b.bank_index}') is not b.weights
                   for b in semantics.banks)):
        invalid()
    _epistemic(semantics, plan)
