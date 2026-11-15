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
from .backbone_producer_session import _SourceBackboneProducerSession


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
    compiled, parameters, sources, feature_schema, banks, artifact_owner, *, snapshot=None,
):
    """Compute h0 and input coordinates internally before constructing a session.

    The accepted source encoder replays source, rights, prefix, feature and full
    B01 parameter checks. Each compiled row is one independent source sequence.
    Extent and prefix digests are observations, not B13 generation credentials.
    """
    encoding = encode_source_compiled(
        compiled, parameters, sources, feature_schema, banks, artifact_owner,
        snapshot=snapshot)
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
    execution_binding=None, trace=False, snapshot=None,
):
    """Create the B11 producer only by replaying and revalidating actual source rows."""
    encoded, handoffs = encode_source_compiled_with_handoffs(
        compiled, parameters, sources, feature_schema, banks, artifact_owner,
        snapshot=snapshot)
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
    artifact_owner, *, seal, execution_binding=None, trace=False, snapshot=None,
):
    """B13-only B11 producer whose input and g1 boundaries execute B08 reads."""
    if seal is not _B13_EXECUTION_SEAL or type(manifest) is not MotifManifest:
        _invalid_producer_receipt()
    if manifest.digest != compiled.extents.motif_key_map_digest:
        _invalid_producer_receipt()
    encoded, handoffs = encode_source_compiled_with_handoffs(
        compiled, parameters, sources, feature_schema, banks, artifact_owner,
        snapshot=snapshot)
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
