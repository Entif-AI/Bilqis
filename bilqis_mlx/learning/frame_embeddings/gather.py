"""BAMF embedding gather owner."""
from __future__ import annotations
import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled
from .common import ATOM_EMBEDDING_RANK, CONSTITUENT_INDEX_RANK, INDEXED_LOGITS_SCHEMA, UINT32_MAX, WIDTH, _invalid
from .banks import IndexedLogits


def gather_constituents(embeddings: mx.array, indices: mx.array, valid: mx.array) -> mx.array:
    """Gather exact [B,F,M] sidecar addresses, leaving the float path differentiable."""
    if (not isinstance(embeddings, mx.array) or embeddings.ndim != ATOM_EMBEDDING_RANK or
            embeddings.shape[-1] != WIDTH or min(embeddings.shape) < 1 or embeddings.dtype != mx.float32 or
            not isinstance(indices, mx.array) or indices.ndim != CONSTITUENT_INDEX_RANK or
            not mx.issubdtype(indices.dtype, mx.integer) or indices.shape[0] != embeddings.shape[0] or
            min(indices.shape) < 1 or not isinstance(valid, mx.array) or valid.shape != indices.shape or
            valid.dtype != mx.bool_):
        _invalid()
    if (host_tensor_validation_enabled()
            and bool(mx.any(valid & ((indices < 0) | (indices >= embeddings.shape[1]))))):
        _invalid()
    batch, frames, members = indices.shape
    safe = mx.where(valid, indices, 0).astype(mx.int32).reshape(batch, frames*members)
    values = mx.take_along_axis(embeddings, safe[:, :, None], axis=1).reshape(batch, frames, members, WIDTH)
    return mx.where(valid[:, :, :, None], values, 0)

def masked_semantic_loss(indexed: IndexedLogits, targets: mx.array, legal: mx.array) -> mx.array:
    """Stable supervised loss; global target IDs never enter the inference feature path."""
    if (type(indexed) is not IndexedLogits or indexed.schema_version != INDEXED_LOGITS_SCHEMA or
            not isinstance(indexed.logits, mx.array) or indexed.logits.ndim < 1 or
            min(indexed.logits.shape) < 1 or
            indexed.logits.dtype != mx.float32 or type(indexed.indices) is not tuple or not indexed.indices or
            indexed.indices != tuple(sorted(set(indexed.indices))) or
            any(type(index) is not int or not 0 <= index <= UINT32_MAX for index in indexed.indices) or
            indexed.logits.shape[-1] != len(indexed.indices) or
            not isinstance(targets, mx.array) or not mx.issubdtype(targets.dtype, mx.integer) or
            targets.shape != indexed.logits.shape[:-1] or
            not isinstance(legal, mx.array) or legal.dtype != mx.bool_ or legal.shape != indexed.logits.shape):
        _invalid()
    target_ids = targets.astype(mx.int64)
    target_mask = target_ids[..., None] == mx.array(indexed.indices, dtype=mx.int64)
    if host_tensor_validation_enabled():
        checks = (mx.all((target_ids >= 0) & (target_ids <= UINT32_MAX)), mx.all(mx.any(legal, axis=-1)),
                  mx.all(mx.any(target_mask & legal, axis=-1)), mx.all(~legal | mx.isfinite(indexed.logits)))
        mx.eval(*checks)
        if not all(bool(check) for check in checks):
            _invalid()
    masked = mx.where(legal, indexed.logits, -mx.inf)
    shifted = masked - mx.max(masked, axis=-1, keepdims=True)
    target_score = mx.sum(mx.where(target_mask, shifted, 0), axis=-1)
    return mx.mean(mx.logsumexp(shifted, axis=-1) - target_score)
