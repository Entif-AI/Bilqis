"""  dispatch for the existing frame encoder contract."""
from __future__ import annotations

from bilqis_mlx.learning.frame_embeddings import frame_factor_terms
from bilqis_mlx.runtime.model_topology_v2 import GenerationExtents
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.runtime.model_topology_v2 import expected_bamf_shapes
from bilqis_mlx.runtime.model_topology_v2 import validate_bamf_parameters
from typing import Mapping
import mlx.core as mx
from .contracts import (
    AtomicEncoderInput, FrameEncoderInput, FrameEncoding, _invalid,
)
from .compiled import (
    CompiledEncoderInput,
)
from .vectors import (
    CompiledEmbeddingVectors,
)
from .kernel import (
    _encode_one, _validate_encoder_parameters, _validate_vectors,
)
from .execution import (
    _encode_compiled,
)


def frame_encoder_parameter_view(parameters: Mapping[str, mx.array], *, spec: ModelTopologySpecV2,
                                 extents: GenerationExtents) -> dict[str, mx.array]:
    """Borrow the canonical frame/shared-feature tensors from a complete B01 tree."""
    validate_bamf_parameters(spec, extents, parameters)
    return {item.name: parameters[item.name] for item in expected_bamf_shapes(spec, extents)
            if item.name.startswith(("frame.", "features."))}


def encode_frames(compiled: FrameEncoderInput | AtomicEncoderInput | CompiledEncoderInput,
                  atom_vectors: tuple[tuple[mx.array, ...], ...] | CompiledEmbeddingVectors,
                  parameters: Mapping[str, mx.array], *,
                  atlas_selections=None,
                  qualified_feature_rows_by_row=None) -> FrameEncoding:
    """Encode complete groups or preserve approved atomic vectors without detaching."""
    if not isinstance(parameters, Mapping):
        _invalid()
    if type(compiled) is CompiledEncoderInput:
        return _encode_compiled(
            compiled, atom_vectors, parameters, atlas_selections=atlas_selections,
            qualified_feature_rows_by_row=qualified_feature_rows_by_row)
    if atlas_selections is not None or qualified_feature_rows_by_row is not None:
        _invalid()
    if type(compiled) not in (FrameEncoderInput, AtomicEncoderInput):
        _invalid()
    compiled.__post_init__()
    if type(compiled) is AtomicEncoderInput:
        _validate_vectors(atom_vectors, tuple(tuple(1 for _ in row) for row in compiled.handles))
        seeds = mx.stack([mx.stack([members[0] for members in row]) for row in atom_vectors])
        return FrameEncoding(seeds, atom_vectors, compiled.handles,
                             tuple(tuple(None for _ in row) for row in compiled.handles))
    _validate_vectors(atom_vectors, tuple(tuple(len(group) for group in row) for row in compiled.requests))
    _validate_encoder_parameters(parameters, compiled.extents)
    factors = tuple(tuple(frame_factor_terms(parameters, group, compiled.features, extents=compiled.extents)
                          for group in row) for row in compiled.requests)
    seeds = mx.stack([mx.stack([_encode_one(members, terms, parameters)
                               for members, terms in zip(row, feature_row)])
                      for row, feature_row in zip(atom_vectors, factors)])
    return FrameEncoding(seeds, atom_vectors, compiled.requests, factors)
