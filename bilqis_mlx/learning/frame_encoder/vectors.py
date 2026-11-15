"""Vectors for the existing frame encoder contract."""
from __future__ import annotations

from bilqis_mlx.learning.frame_embeddings import FeatureRequest
from dataclasses import dataclass
import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled
from .contracts import (
    AtomicSourceHandle, COMPILED_VECTORS_SCHEMA, WIDTH, _invalid,
)


@dataclass(frozen=True)
class MemberEmbedding:
    """One supplied B02 vector bound to its exact source occurrence request."""

    request: FeatureRequest
    vector: mx.array

    def __post_init__(self):
        if (type(self.request) is not FeatureRequest or not isinstance(self.vector, mx.array) or
                self.vector.shape != (WIDTH,) or self.vector.dtype != mx.float32 or
                (host_tensor_validation_enabled()
                 and not bool(mx.all(mx.isfinite(self.vector))))):
            _invalid()


@dataclass(frozen=True)
class AtomicFrameEmbedding:
    """One supplied atomic closure vector bound to its exact approved handle."""

    handle: AtomicSourceHandle
    vector: mx.array

    def __post_init__(self):
        if (type(self.handle) is not AtomicSourceHandle or not isinstance(self.vector, mx.array) or
                self.vector.shape != (WIDTH,) or self.vector.dtype != mx.float32 or
                (host_tensor_validation_enabled()
                 and not bool(mx.all(mx.isfinite(self.vector))))):
            _invalid()
        self.handle.__post_init__()


@dataclass(frozen=True)
class CompiledEmbeddingVectors:
    """Unpadded raw atom rows and exact ordered closure-member vectors."""

    atoms: tuple[mx.array, ...]
    members: tuple[tuple[MemberEmbedding, ...], ...]
    atomic_frames: tuple[tuple[AtomicFrameEmbedding, ...], ...] = ()
    schema_version: str = COMPILED_VECTORS_SCHEMA
