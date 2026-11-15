"""Execution for the existing frame encoder contract."""
from __future__ import annotations

from bilqis_mlx.learning.frame_embeddings import empty_frame_factor_terms
from bilqis_mlx.semantics.frame_compiler import PositionKind
from bilqis_mlx.semantics.frame_schema import AtomicFrame
import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled
from .contracts import (
    COMPILED_VECTORS_SCHEMA, FrameEncoding, WIDTH, _invalid,
)
from .vectors import (
    AtomicFrameEmbedding, CompiledEmbeddingVectors, MemberEmbedding,
)
from .members import encode_group
from .kernel import (
    _norm, _validate_encoder_parameters,
)


def _compiled_execution_inputs(
    compiled, vectors, parameters, atlas_selections, source_execution_authorities,
):
    compiled.__post_init__()
    _validate_encoder_parameters(parameters, compiled.extents)
    if (type(vectors) is not CompiledEmbeddingVectors
            or vectors.schema_version != COMPILED_VECTORS_SCHEMA
            or type(vectors.atoms) is not tuple
            or type(vectors.members) is not tuple
            or type(vectors.atomic_frames) is not tuple
            or len(vectors.atoms) != len(compiled.compiled.rows)
            or len(vectors.members) != len(vectors.atoms)):
        _invalid()
    atomic_rows = vectors.atomic_frames or tuple(
        () for _ in compiled.compiled.rows)
    if len(atomic_rows) != len(vectors.atoms):
        _invalid()
    if atlas_selections is None:
        atlas_selections = (None,) * len(compiled.compiled.rows)
    if (type(atlas_selections) is not tuple
            or len(atlas_selections) != len(compiled.compiled.rows)):
        _invalid()
    if source_execution_authorities is None:
        source_execution_authorities = (None,) * len(compiled.compiled.rows)
    if (type(source_execution_authorities) is not tuple
            or len(source_execution_authorities) != len(compiled.compiled.rows)):
        _invalid()
    return atomic_rows, atlas_selections, source_execution_authorities


def _validate_compiled_row_vectors(
    row, atoms, supplied, expected, atomic_frames, atomic_handles,
):
    if (not isinstance(atoms, mx.array)
            or atoms.shape != (row.visible_end, WIDTH)
            or atoms.dtype != mx.float32
            or (host_tensor_validation_enabled()
                and not bool(mx.all(mx.isfinite(atoms))))
            or type(supplied) is not tuple
            or any(type(item) is not MemberEmbedding for item in supplied)
            or tuple(item.request for item in supplied) != expected
            or type(atomic_frames) is not tuple
            or any(type(item) is not AtomicFrameEmbedding
                   for item in atomic_frames)
            or tuple(item.handle for item in atomic_frames) != atomic_handles):
        _invalid()
    for item in supplied:
        item.__post_init__()
    for item in atomic_frames:
        item.__post_init__()


def _encode_compiled_row(
    compiled, row, groups, projection, atoms, supplied, atomic_frames,
    atlas_selection, source_execution_authority, parameters, width,
):
    cursor = atomic_cursor = 0
    closure_outputs = {}
    row_seeds, row_members, row_factors = [], [], []
    for position, group in zip(row.positions, groups):
        if position.kind is PositionKind.ATOM:
            matrix = atoms[position.source_index:position.source_index + 1]
            seed, factor = matrix[0], None
        elif group:
            seed, matrix, factor, cursor = encode_group(
                group, supplied, cursor, closure_outputs, compiled, parameters,
                atlas_selection=atlas_selection,
                source_execution_authority=source_execution_authority)
            closure_outputs[position.frame_handle] = seed
        elif type(projection.frame(position.frame_handle)) is AtomicFrame:
            seed = atomic_frames[atomic_cursor].vector
            atomic_cursor += 1
            closure_outputs[position.frame_handle] = seed
            factor, matrix = None, seed[None, :]
        else:
            _validate_encoder_parameters(parameters, compiled.extents)
            factor = empty_frame_factor_terms(
                parameters, projection, position.frame_handle,
                compiled.features, extents=compiled.extents)
            summary = (factor.schema128 + factor.mean_role128) / 2
            seed = _norm(
                parameters["frame.empty_seed"]
                + summary @ parameters["frame.project_summary"].T,
                parameters["frame.norm"])
            closure_outputs[position.frame_handle] = seed
            matrix = mx.zeros((0, WIDTH), dtype=mx.float32)
        row_seeds.append(seed)
        row_members.append(matrix)
        row_factors.append(factor)
    if cursor != len(supplied) or atomic_cursor != len(atomic_frames):
        _invalid()
    row_seeds.extend(
        mx.zeros((WIDTH,), dtype=mx.float32)
        for _ in range(width - len(row_seeds)))
    row_factors.extend(None for _ in range(width - len(row_factors)))
    seeds = (
        mx.stack(row_seeds)
        if row_seeds else mx.zeros((0, WIDTH), dtype=mx.float32))
    return seeds, tuple(row_members), tuple(row_factors)


def _encode_compiled(
        compiled, vectors, parameters, *, atlas_selections=None,
        source_execution_authorities=None):
    inputs = _compiled_execution_inputs(
        compiled, vectors, parameters, atlas_selections,
        source_execution_authorities)
    atomic_rows, atlas_selections, authorities = inputs
    seeds, members, factors = [], [], []
    width = len(compiled.compiled.padded_positions[0])
    rows = zip(
        compiled.compiled.rows, compiled._groups, compiled._projections,
        vectors.atoms, vectors.members, compiled.member_requests, atomic_rows,
        compiled.atomic_handles, atlas_selections, authorities)
    for (row, groups, projection, atoms, supplied, expected, atomic_frames,
         atomic_handles, atlas_selection, authority) in rows:
        _validate_compiled_row_vectors(
            row, atoms, supplied, expected, atomic_frames, atomic_handles)
        row_values = _encode_compiled_row(
            compiled, row, groups, projection, atoms, supplied, atomic_frames,
            atlas_selection, authority, parameters, width)
        row_seeds, row_members, row_factors = row_values
        seeds.append(row_seeds)
        members.append(row_members)
        factors.append(row_factors)
    return FrameEncoding(
        mx.stack(seeds), tuple(members), compiled.compiled.padded_positions,
        tuple(factors), compiled=compiled.compiled)

