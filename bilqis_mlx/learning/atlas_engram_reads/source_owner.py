"""Private B08 execution owner over A05/A13 replay and retained B01 state."""
from __future__ import annotations

from dataclasses import replace

import mlx.core as mx

from bilqis_mlx.learning.atlas_engram_source import (
    _source_family, source_qualified_motif_context,
)
from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.learning.atlas_engram_parameters import motif_parameter_view
from bilqis_mlx.learning.frame_embeddings import motif_gate_features
from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.learning.source_atoms import SourceAtomRow
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, validate_bamf_parameters,
)
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, ContextHold, project_context,
)
from bilqis_mlx.semantics.frame_compiler import PositionKind
from bilqis_mlx.semantics.frame_schema import AtomicFrame, FrameInstance
from bilqis_mlx.semantics.released_frame_schemas import (
    lookup_source_pinned_frame_schema,
)
from bilqis_mlx.source_adapters.school import live_source_registry

from .numerical import _read_motif_unqualified_candidate
from .records import MOTIF_WIDTH, MotifReadPosition, MotifReadResult, _invalid


_B13_EXECUTION_SEAL = object()
_MOTIF_ROW_FEATURE_RANK = 2


def _canonical_adapter(source: SourceAtomRow):
    row = source.source_row
    if type(row) is not dict or not isinstance(row.get("generator"), str):
        _invalid()
    try:
        adapter = live_source_registry().resolve_owner(row["generator"])
    except (KeyError, TypeError, ValueError):
        _invalid()
    return adapter


def _execution_projection(compiled_row, config, replayed, frontier):
    handles = tuple(
        position.frame_handle for position in compiled_row.positions
        if position.kind is PositionKind.CLOSURE)
    if not handles:
        return None
    if len(set(handles)) != len(handles):
        _invalid()
    envelopes = tuple(
        envelope for envelope in replayed.envelopes
        if envelope.frame_handle in set(handles))
    if len(envelopes) != len(handles):
        _invalid()
    projected = project_context(
        envelopes, replace(config.task, causal_prefix_end=compiled_row.visible_end),
        frontier, config.policy)
    if (type(projected) is not ApprovedContextProjection
            or projected.digest != compiled_row.context_digest):
        _invalid()
    return projected


def _row_read_inputs(
    compiled_row, config, projection, adapter, source, parameters, features,
    extents,
):
    positions, vectors = [], []
    family = _source_family(adapter.descriptor.adapter_id)
    for position in compiled_row.positions:
        if position.kind is not PositionKind.CLOSURE:
            positions.append(None)
            vectors.append(mx.zeros((MOTIF_WIDTH,), dtype=mx.float32))
            continue
        envelope = next((
            item for item in projection.envelopes
            if item.frame_handle == position.frame_handle), None)
        if envelope is None:
            _invalid()
        if type(envelope.frame) is AtomicFrame:
            positions.append(MotifReadPosition(envelope, None, family))
            vectors.append(mx.zeros((MOTIF_WIDTH,), dtype=mx.float32))
            continue
        if type(envelope.frame) is not FrameInstance:
            _invalid()
        schema, _witness = lookup_source_pinned_frame_schema(
            envelope.frame.frame_schema_id, envelope.frame.frame_schema_revision,
            source_family=family, atlas_selection=source.selection)
        positions.append(MotifReadPosition(envelope, schema, family))
        vectors.append(motif_gate_features(
            parameters, projection, position.frame_handle, features,
            extents=extents, atlas_selection=source.selection).vector128)
    return tuple(positions), mx.stack(tuple(vectors))


def _pad_motif_read_row(positions, features, width):
    """Pad one source-owned motif row to the already-issued hidden width."""
    if (type(positions) is not tuple
            or not isinstance(features, mx.array)
            or features.ndim != _MOTIF_ROW_FEATURE_RANK
            or features.shape != (len(positions), MOTIF_WIDTH)
            or features.dtype != mx.float32
            or type(width) is not int
            or width < len(positions)):
        _invalid()
    padding = width - len(positions)
    if not padding:
        return positions, features
    return (
        positions + (None,) * padding,
        mx.concatenate((
            features,
            mx.zeros((padding, MOTIF_WIDTH), dtype=mx.float32),
        ), axis=0),
    )


def _read_retained_compiled_motifs(
    compiled: CompiledEncoderInput,
    parameters,
    sources: tuple[SourceAtomRow, ...],
    manifest: MotifManifest,
    *,
    spec: ModelTopologySpecV2,
    extents: GenerationExtents,
    site_index: int,
    hidden: mx.array,
    seal,
) -> MotifReadResult:
    """Execute B08 only for a B13-admitted caller holding the private seal."""
    if (seal is not _B13_EXECUTION_SEAL
            or type(compiled) is not CompiledEncoderInput
            or type(sources) is not tuple
            or len(sources) != len(compiled.compiled.rows)
            or type(manifest) is not MotifManifest
            or type(spec) is not ModelTopologySpecV2
            or type(extents) is not GenerationExtents
            or manifest.digest != extents.motif_key_map_digest
            or extents != compiled.extents):
        _invalid()
    validate_bamf_parameters(spec, extents, parameters)
    row_positions, row_features = [], []
    padded_width = hidden.shape[1]
    tasks, frontiers, policies = [], [], []
    for row, config, source in zip(
            compiled.compiled.rows, compiled.compiler_configs, sources):
        if type(source) is not SourceAtomRow:
            _invalid()
        adapter = _canonical_adapter(source)
        replayed = source_qualified_motif_context(
            adapter, source.source_row, source.selection,
            source_root=source.source_root, graph=source.graph,
            task_scope=replace(config.task, causal_prefix_end=row.visible_end),
            source_frontier=config.frontier, policy=config.policy,
            source_seed=source.source_seed, source_each=source.source_each,
            source_profile_parameters=source.source_profile_parameters,
            course=source.course)
        if isinstance(replayed, ContextHold):
            _invalid()
        projection, _motifs, issued_frontier = replayed
        projection = _execution_projection(row, config, projection, issued_frontier)
        if projection is None:
            positions = (None,) * len(row.positions)
            features = mx.zeros(
                (len(row.positions), MOTIF_WIDTH), dtype=mx.float32)
        else:
            positions, vectors = _row_read_inputs(
                row, config, projection, adapter, source, parameters,
                compiled.features, extents)
            features = vectors
        positions, features = _pad_motif_read_row(
            positions, features, padded_width)
        row_positions.append(positions)
        row_features.append(features)
        task = replace(config.task, causal_prefix_end=row.visible_end)
        tasks.append(task)
        frontiers.append(issued_frontier)
        policies.append(config.policy)
    return _read_motif_unqualified_candidate(
        site_index=site_index, hidden=hidden,
        features=mx.stack(tuple(row_features)), positions=tuple(row_positions),
        tasks=tuple(tasks), frontiers=tuple(frontiers), policies=tuple(policies),
        manifest=manifest,
        parameters=motif_parameter_view(
            parameters, spec=spec, extents=extents, site_index=site_index))
