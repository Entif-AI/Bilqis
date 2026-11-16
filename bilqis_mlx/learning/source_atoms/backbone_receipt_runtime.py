"""Execution replay and receipt projection for the source-owned B11 producer."""
from __future__ import annotations

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.atlas_engram_reads.source_owner import (
    _read_retained_compiled_motifs,
)
from bilqis_mlx.learning.atlas_plasticity import (
    adapter_forward,
    adapter_parameter_view,
)
from bilqis_mlx.runtime.backbone_group_numerical import _content_digest
from bilqis_mlx.runtime.block_attnres import SOURCE_ORDER, depth_select, source_depth_select
from bilqis_mlx.semantics.domains import contract_digest


def _invalid() -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


def _motif_read_digest(
    motif, hidden, source_digest, prefix, generation, execution_digest, position,
):
    return contract_digest((
        "B08_SOURCE_QUALIFIED_READ_V1",
        motif.dispositions,
        motif.participating_slots,
        motif.context_digests,
        _content_digest(hidden),
        source_digest,
        prefix,
        generation,
        execution_digest,
        position,
    ))


def _h0_receipt_values(
    producer, source_digest, topology, generation, prefix, replay,
):
    from .backbone_receipts import (
        HIT, INPUT_MOTIF_POSITION, NOT_APPLICABLE, QUALIFIED_MISS,
    )
    hidden = producer._initial_hidden
    output = _content_digest(hidden)
    execution_digest = contract_digest(("h0", output, replay.parameter_tree_digest))
    motif = producer._input_motif_read
    if motif is None:
        motif_disposition = NOT_APPLICABLE
        motif_position = ""
        motif_read_digest = contract_digest(())
    else:
        motif_disposition = HIT if motif.participating_slots else QUALIFIED_MISS
        motif_position = INPUT_MOTIF_POSITION
        motif_read_digest = _motif_read_digest(
            motif, hidden, source_digest, prefix, generation,
            execution_digest, motif_position)
    return dict(
        source_id="h0", completed_layer=0, hidden=hidden,
        source_handoff_digest=source_digest, topology_digest=topology.digest,
        generation_digest=generation,
        parameter_tree_digest=replay.parameter_tree_digest,
        prefix_digest=prefix,
        scope_digest=contract_digest((source_digest, prefix, generation)),
        input_digest=source_digest, output_digest=output,
        output_shape=tuple(hidden.shape), output_dtype=str(hidden.dtype),
        cache_chain_digest=contract_digest(()),
        numerical_execution_digest=execution_digest,
        predecessor_receipt_digest=source_digest,
        motif_disposition=motif_disposition,
        motif_read_position=motif_position,
        motif_read_digest=motif_read_digest,
    )


def _replay_to_result(producer, replay, topology, result):
    target = result.group_index
    if (
        target < 1
        or target > len(producer._session.results)
        or result is not producer._session.results[target - 1]
        or len(producer._depth_inputs) < target - 1
    ):
        _invalid()
    expected = None
    for group_index in range(1, target + 1):
        if group_index == 1:
            expected = replay.advance()
        else:
            features, view = producer._depth_inputs[group_index - 2]
            selected = (
                source_depth_select(producer, view)
                if features is None
                else depth_select(producer, features, view)
            )
            selected = adapter_forward(
                selected,
                adapter_parameter_view(
                    producer._parameters,
                    spec=topology,
                    extents=producer._compiled.extents,
                    group_index=group_index - 2,
                ),
            )
            expected = replay.advance(next_input=selected)
    fields = (
        "group_index", "layer_start", "layer_end", "parameter_content_digest",
        "full_parameter_tree_digest", "scope_content_digest", "input_content_digest",
        "cache_chain_digest", "predecessor_digest", "execution_digest",
    )
    if (
        any(getattr(result, name) != getattr(expected, name) for name in fields)
        or result.hidden.shape != expected.hidden.shape
        or result.hidden.dtype != expected.hidden.dtype
        or _content_digest(result.hidden) != _content_digest(expected.hidden)
    ):
        _invalid()

    return target, expected


def _group_receipt_values(
    producer, result, source_digest, topology, generation, prefix, replay,
):
    from .backbone_receipts import (
        HIT, MOTIF_POSITION, NO_HIT, NOT_APPLICABLE, QUALIFIED_MISS,
    )
    target, expected = _replay_to_result(producer, replay, topology, result)
    source_id = SOURCE_ORDER[target]
    hidden = expected.hidden
    motif_disposition = NO_HIT if source_id == "g1" else NOT_APPLICABLE
    motif_position = MOTIF_POSITION if source_id == "g1" else ""
    if source_id == "g1" and producer._motif_manifest is not None:
        motif = _read_retained_compiled_motifs(
            producer._compiled,
            producer._parameters,
            producer._sources,
            producer._motif_manifest,
            spec=topology,
            extents=producer._compiled.extents,
            site_index=1,
            hidden=expected.hidden,
            seal=producer._motif_seal,
            source_execution_authorities=producer._source_execution_authorities,
        )
        producer._motif_read = motif
        hidden = motif.hidden
        motif_disposition = (
            HIT if motif.participating_slots else QUALIFIED_MISS)
        motif_read_digest = _motif_read_digest(
            motif, hidden, source_digest, prefix, generation,
            expected.execution_digest, MOTIF_POSITION)
    else:
        motif_read_digest = (
            contract_digest((
                "B08_QUARANTINED_NO_HIT", source_digest, prefix,
                generation, expected.execution_digest, MOTIF_POSITION,
            ))
            if source_id == "g1"
            else contract_digest(())
        )
    return dict(
        source_id=source_id, completed_layer=expected.layer_end,
        hidden=hidden, source_handoff_digest=source_digest,
        topology_digest=topology.digest, generation_digest=generation,
        parameter_tree_digest=expected.full_parameter_tree_digest,
        prefix_digest=prefix, scope_digest=expected.scope_content_digest,
        input_digest=expected.input_content_digest,
        output_digest=_content_digest(hidden),
        output_shape=tuple(hidden.shape), output_dtype=str(hidden.dtype),
        cache_chain_digest=expected.cache_chain_digest,
        numerical_execution_digest=expected.execution_digest,
        predecessor_receipt_digest=producer._receipts[target - 1].receipt_digest,
        motif_disposition=motif_disposition, motif_read_position=motif_position,
        motif_read_digest=motif_read_digest,
    )


def receipt_values(producer, result=None):
    """Replay owned execution and project the requested B11 boundary."""
    _encoded, source_digest, topology, generation, prefix, replay = (
        producer._receipt_replay())
    if result is None:
        return _h0_receipt_values(
            producer, source_digest, topology, generation, prefix, replay)
    return _group_receipt_values(
        producer, result, source_digest, topology, generation, prefix, replay)
