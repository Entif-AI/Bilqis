"""B11 execution from replayed A05/A01 source inputs and retained B08 state."""
import mlx.core as mx

from ..atlas_engram import MotifManifest
from ..atlas_engram_reads.source_owner import (
    _B13_EXECUTION_SEAL, _read_retained_compiled_motifs,
)
from ..atlas_engram_reads.records import MotifReadResult
from ..atlas_plasticity import adapter_forward, adapter_parameter_view
from ...runtime.backbone_group_numerical import (
    BackboneTraceSession, UnadmittedBackboneSession, _content_digest,
)
from ...runtime.backbone_identity import (
    execution_generation_digest, require_execution_generation_binding,
)
from ...runtime.block_attnres import SOURCE_ORDER, depth_select, source_depth_select
from ...runtime.block_attnres import depth_parameter_view
from ...runtime.model_topology_v2 import ModelTopologySpecV2
from ...semantics.domains import contract_digest
from .backbone_receipts import (
    _invalid as _invalid_producer_receipt, _issue_from_producer,
)
from .backbone_identity import compiled_prefix_digest
from .encoding import encode_source_compiled, encode_source_compiled_with_handoffs


class _SourceBackboneProducerSession:
    """Own source h0 and the only legal sequential group-receipt construction."""

    def __init__(
        self, encoded, handoffs, parameters, compiled, artifact_owner, *,
        input_motif_read=None, execution_binding=None, trace=False,
    ):
        self._compiled = compiled
        self._encoded = encoded
        self._handoffs = tuple(handoffs)
        self._parameters = dict(parameters)
        self._sources = None
        self._feature_schema = None
        self._artifact_owner = artifact_owner
        self._source_digest = contract_digest(tuple(item.digest for item in handoffs))
        self._topology = ModelTopologySpecV2()
        self._execution_binding = execution_binding
        self._trace = trace
        self._generation = (
            execution_generation_digest(
                parameters, spec=self._topology, extents=compiled.extents)
            if execution_binding is None else require_execution_generation_binding(
                execution_binding, parameters,
                spec=self._topology, extents=compiled.extents).generation_digest)
        self._prefix = compiled_prefix_digest(compiled)
        valid = mx.array([[position is not None for position in row]
                          for row in encoded.handles], dtype=mx.bool_)
        if input_motif_read is not None and type(input_motif_read) is not MotifReadResult:
            _invalid_producer_receipt()
        self._input_motif_read = input_motif_read
        self._initial_hidden = (
            encoded.global_seeds
            if input_motif_read is None
            else input_motif_read.hidden
        )
        if (
            type(self._initial_hidden) is not mx.array
            or self._initial_hidden.shape != encoded.global_seeds.shape
            or self._initial_hidden.dtype != mx.float32
        ):
            _invalid_producer_receipt()
        session_type = BackboneTraceSession if trace else UnadmittedBackboneSession
        self._session = session_type(
            self._initial_hidden, self._parameters,
            spec=self._topology, extents=compiled.extents,
            scope_ids=mx.zeros(valid.shape, dtype=mx.int32), valid=valid,
            generation=self._generation, prefix_digest=self._prefix,
            execution_binding=self._execution_binding)
        self._trace_boundaries = (self._initial_hidden,)
        self._depth_inputs = ()
        self._receipts = ()
        self._receipt_refs = ()
        self._receipt_seals = ()
        self._result_refs = ()
        self._result_seals = ()
        self._motif_manifest = None
        self._motif_seal = None
        self._motif_read = None

    def _bind_authoritative_inputs(self, sources, feature_schema):
        self._sources = sources
        self._feature_schema = feature_schema

    def _receipt_replay(self):
        if self._sources is None or self._feature_schema is None:
            _invalid_producer_receipt()
        self._artifact_owner.require(self._compiled.features)
        encoded, handoffs = self._encoded, self._handoffs
        for handoff in handoffs:
            handoff.__post_init__()
        source_digest = contract_digest(tuple(item.digest for item in handoffs))
        topology = ModelTopologySpecV2()
        generation = self._generation
        prefix = compiled_prefix_digest(self._compiled)
        if (source_digest != self._source_digest or topology.digest != self._topology.digest
                or generation != self._generation or prefix != self._prefix):
            _invalid_producer_receipt()
        valid = mx.array([[position is not None for position in row]
                          for row in encoded.handles], dtype=mx.bool_)
        initial_hidden = encoded.global_seeds
        if self._motif_manifest is not None:
            motif = _read_retained_compiled_motifs(
                self._compiled, self._parameters, self._sources,
                self._motif_manifest, spec=topology,
                extents=self._compiled.extents, site_index=0,
                hidden=encoded.global_seeds, seal=self._motif_seal)
            if (
                self._input_motif_read is None
                or motif.dispositions != self._input_motif_read.dispositions
                or motif.participating_slots
                != self._input_motif_read.participating_slots
                or motif.context_digests != self._input_motif_read.context_digests
                or _content_digest(motif.hidden)
                != _content_digest(self._input_motif_read.hidden)
            ):
                _invalid_producer_receipt()
            initial_hidden = motif.hidden
        replay = UnadmittedBackboneSession(
            initial_hidden, self._parameters,
            spec=topology, extents=self._compiled.extents,
            scope_ids=mx.zeros(valid.shape, dtype=mx.int32), valid=valid,
            generation=generation, prefix_digest=prefix,
            execution_binding=self._execution_binding)
        return encoded, source_digest, topology, generation, prefix, replay

    def _validated_receipts(self, boundary_group):
        if self._trace:
            _invalid_producer_receipt()
        if (not isinstance(boundary_group, int) or isinstance(boundary_group, bool)
                or boundary_group < 1 or boundary_group > len(self._receipts) - 1):
            _invalid_producer_receipt()
        prefix = self._receipts[:boundary_group + 1]
        trusted = self._receipt_refs[:boundary_group + 1]
        seals = self._receipt_seals[:boundary_group + 1]
        if (len(trusted) != len(prefix)
                or len(seals) != len(prefix)
                or len(self._result_refs) < boundary_group
                or len(self._result_seals) < boundary_group
                or len(self._session.results) < boundary_group):
            _invalid_producer_receipt()
        verified = []
        for index, receipt in enumerate(prefix):
            receipt._validate_contents()
            seal = seals[index]
            if (receipt.receipt_digest != seal[0]
                    or receipt.output_digest != seal[1]):
                _invalid_producer_receipt()
            owned = trusted[index]
            owned._validate_contents()
            if (owned.receipt_digest != seal[0]
                    or owned.output_digest != seal[1]):
                _invalid_producer_receipt()
            if index:
                result = self._session.results[index - 1]
                result_seal = self._result_seals[index - 1]
                if (result is not self._result_refs[index - 1]
                        or result.execution_digest != result_seal[0]
                        or _content_digest(result.hidden) != result_seal[1]
                        or owned.numerical_execution_digest != result.execution_digest
                        or owned.parameter_tree_digest != result.full_parameter_tree_digest
                        or owned.cache_chain_digest != result.cache_chain_digest):
                    _invalid_producer_receipt()
            verified.append(owned)
        return tuple(verified)

    @property
    def receipts(self):
        return self._receipts

    def advance(self, frame_features=None, depth_parameters=None):
        completed = len(self._session.results)
        if completed:
            if depth_parameters is None:
                _invalid_producer_receipt()
            if ((frame_features is not None
                 and frame_features.boundary_group != completed)
                    or depth_parameters.boundary_group != completed):
                _invalid_producer_receipt()
            selected = (source_depth_select(self, depth_parameters) if frame_features is None
                        else depth_select(self, frame_features, depth_parameters))
            selected = adapter_forward(selected, adapter_parameter_view(
                self._parameters, spec=self._topology, extents=self._compiled.extents,
                group_index=completed - 1))
            result = self._session.advance(next_input=selected)
            self._depth_inputs += ((frame_features, depth_parameters),)
        else:
            if frame_features is not None or depth_parameters is not None:
                _invalid_producer_receipt()
            result = self._session.advance()
        trace_hidden = result.hidden
        trace = getattr(self, "_trace", False)
        if trace and completed == 0 and getattr(self, "_motif_manifest", None) is not None:
            motif = _read_retained_compiled_motifs(
                self._compiled, self._parameters, self._sources,
                self._motif_manifest, spec=self._topology,
                extents=self._compiled.extents, site_index=1,
                hidden=result.hidden, seal=self._motif_seal)
            self._motif_read = motif
            trace_hidden = motif.hidden
        if trace:
            self._trace_boundaries += (trace_hidden,)
            return result
        receipt = _issue_from_producer(self, result)
        self._receipts += (receipt,)
        self._receipt_refs += (receipt,)
        self._receipt_seals += ((receipt.receipt_digest, receipt.output_digest),)
        self._result_refs += (result,)
        self._result_seals += ((result.execution_digest, _content_digest(result.hidden)),)
        return receipt


def _b14_attention_caches(producer):
    """Return only the attention caches sealed inside one complete B11 producer."""
    if type(producer) is not _SourceBackboneProducerSession:
        _invalid_producer_receipt()
    if len(producer._session.results) != producer._topology.depth_groups:
        _invalid_producer_receipt()
    producer._validated_receipts(producer._topology.depth_groups)
    caches = tuple(
        cache
        for result, retained, seal in zip(
            producer._session.results,
            producer._result_refs,
            producer._result_seals,
            strict=True,
        )
        if result is retained
        and result.execution_digest == seal[0]
        and _content_digest(result.hidden) == seal[1]
        for cache in result.attention_caches
    )
    if len(caches) != producer._topology.layers:
        _invalid_producer_receipt()
    return caches


def start_source_backbone_numerical(
    compiled, parameters, sources, feature_schema, banks, artifact_owner,
):
    """Compute h0 and input coordinates internally before constructing a session.

    The accepted source encoder replays source, rights, prefix, feature and full
    B01 parameter checks. Each compiled row is one independent source sequence.
    Extent and prefix digests are observations, not B13 generation credentials.
    """
    encoding = encode_source_compiled(
        compiled, parameters, sources, feature_schema, banks, artifact_owner)
    valid = mx.array([[position is not None for position in row]
                      for row in encoding.handles], dtype=mx.bool_)
    return UnadmittedBackboneSession(
        encoding.global_seeds, parameters,
        spec=ModelTopologySpecV2(), extents=compiled.extents,
        scope_ids=mx.zeros(valid.shape, dtype=mx.int32), valid=valid,
        generation=compiled.extents.digest,
        prefix_digest=compiled_prefix_digest(compiled))


def start_source_backbone_producer(
    compiled, parameters, sources, feature_schema, banks, artifact_owner, *,
    execution_binding=None, trace=False,
):
    """Create the B11 producer only by replaying and revalidating actual source rows."""
    encoded, handoffs = encode_source_compiled_with_handoffs(
        compiled, parameters, sources, feature_schema, banks, artifact_owner)
    return _start_encoded_source_backbone_producer(
        encoded, handoffs, parameters, compiled, sources, feature_schema,
        artifact_owner, execution_binding=execution_binding, trace=trace)


def _start_encoded_source_backbone_producer(
    encoded, handoffs, parameters, compiled, sources, feature_schema,
    artifact_owner, *, motif_manifest=None, motif_seal=None,
    input_motif_read=None, execution_binding=None, trace=False,
):
    retained = (
        motif_manifest is not None,
        motif_seal is not None,
        input_motif_read is not None,
    )
    if any(retained) and not all(retained):
        _invalid_producer_receipt()
    if all(retained) and (
        type(motif_manifest) is not MotifManifest
        or motif_seal is not _B13_EXECUTION_SEAL
        or type(input_motif_read) is not MotifReadResult
    ):
        _invalid_producer_receipt()
    producer = _SourceBackboneProducerSession(
        encoded, handoffs, parameters, compiled, artifact_owner,
        input_motif_read=input_motif_read, execution_binding=execution_binding,
        trace=trace)
    producer._bind_authoritative_inputs(sources, feature_schema)
    producer._motif_manifest = motif_manifest
    producer._motif_seal = motif_seal
    producer._receipts = ()
    if trace:
        return producer
    receipt = _issue_from_producer(producer)
    producer._receipts = (receipt,)
    producer._receipt_refs = (receipt,)
    producer._receipt_seals = ((receipt.receipt_digest, receipt.output_digest),)
    return producer


def complete_source_backbone_producer(producer):
    """Advance the source-owned producer through the complete 12-layer backbone.

    The caller supplies no depth summaries, selected hidden states, parameter
    names, or execution labels.  B11 owns the ordered g1/g2/g3 execution and
    derives both depth-parameter views from the producer's already-bound B01
    tree and generation extents.
    """
    if type(producer) is not _SourceBackboneProducerSession:
        _invalid_producer_receipt()
    while len(producer._session.results) < producer._topology.depth_groups:
        completed = len(producer._session.results)
        if completed == 0:
            producer.advance()
            continue
        view = depth_parameter_view(
            producer._parameters,
            spec=producer._topology,
            extents=producer._compiled.extents,
            boundary_group=completed,
            execution_binding=producer._execution_binding,
        )
        producer.advance(depth_parameters=view)
    if (len(producer._session.results) != producer._topology.depth_groups
            or (not producer._trace and tuple(
                item.source_id for item in producer.receipts) != SOURCE_ORDER)
            or (producer._trace and len(producer._trace_boundaries)
                != producer._topology.depth_groups + 1)):
        _invalid_producer_receipt()
    return producer


def finalize_source_backbone_hidden(producer):
    """Return the final B11 hidden after g3 selection and adapter application."""
    complete_source_backbone_producer(producer)
    view = depth_parameter_view(
        producer._parameters,
        spec=producer._topology,
        extents=producer._compiled.extents,
        boundary_group=producer._topology.depth_groups,
        execution_binding=producer._execution_binding,
    )
    selected = source_depth_select(producer, view)
    return adapter_forward(
        selected,
        adapter_parameter_view(
            producer._parameters,
            spec=producer._topology,
            extents=producer._compiled.extents,
            group_index=producer._topology.depth_groups - 1,
        ),
    )


def start_retained_source_backbone_producer(
    compiled, parameters, sources, feature_schema, banks, manifest,
    artifact_owner, *, seal, execution_binding=None, trace=False,
):
    """B13-only B11 producer whose input and g1 boundaries execute B08 reads."""
    if seal is not _B13_EXECUTION_SEAL or type(manifest) is not MotifManifest:
        _invalid_producer_receipt()
    if manifest.digest != compiled.extents.motif_key_map_digest:
        _invalid_producer_receipt()
    encoded, handoffs = encode_source_compiled_with_handoffs(
        compiled, parameters, sources, feature_schema, banks, artifact_owner)
    topology = ModelTopologySpecV2()
    input_motif_read = _read_retained_compiled_motifs(
        compiled, parameters, sources, manifest,
        spec=topology, extents=compiled.extents, site_index=0,
        hidden=encoded.global_seeds, seal=seal)
    return _start_encoded_source_backbone_producer(
        encoded, handoffs, parameters, compiled, sources, feature_schema,
        artifact_owner, motif_manifest=manifest, motif_seal=seal,
        input_motif_read=input_motif_read, execution_binding=execution_binding,
        trace=trace)
