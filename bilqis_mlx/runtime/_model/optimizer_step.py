"""Bounded MLX-native AdamW leaf math for one qualified optimizer step."""
from __future__ import annotations

from dataclasses import dataclass, field

import mlx.core as mx


ROW_COUNT_RANK = 1
_PARENT_WITNESS_SEAL = object()


@dataclass(frozen=True)
class OptimizerParentWitness:
    """Ephemeral proof that one exact parent passed numerical validation."""

    parent: object
    _seal: object = field(repr=False, compare=False)


def issue_optimizer_parent_witness(parent) -> OptimizerParentWitness:
    return OptimizerParentWitness(parent, _PARENT_WITNESS_SEAL)


def optimizer_parent_witness_matches(witness, parent) -> bool:
    return (type(witness) is OptimizerParentWitness
            and witness._seal is _PARENT_WITNESS_SEAL
            and witness.parent is parent)


def _broadcast_row(value: mx.array, parameter: mx.array) -> mx.array:
    return value.reshape((-1,) + (1,) * (parameter.ndim - 1))


def _adamw_math(
    parameter, first, second, next_count, gradient, *,
    learning_rate, betas, eps, weight_decay,
):
    b1, b2 = betas
    next_first = b1 * first + (1 - b1) * gradient
    next_second = b2 * second + (1 - b2) * mx.square(gradient)
    step = _broadcast_row(next_count, parameter) if next_count.ndim else next_count
    lr = mx.array(learning_rate, dtype=gradient.dtype)
    c1 = (lr / (1 - b1**step)).astype(gradient.dtype)
    c2 = mx.rsqrt(1 - b2**step).astype(gradient.dtype)
    decayed = parameter * (1 - lr * weight_decay)
    updated = decayed - (c1 * next_first) / (mx.sqrt(next_second) * c2 + eps)
    return updated, next_first, next_second


def adamw_leaf_update(
    parameter: mx.array,
    first: mx.array,
    second: mx.array,
    count: mx.array,
    gradient: mx.array,
    mask: mx.array,
    *,
    learning_rate: float,
    betas: tuple[float, float],
    eps: float,
    weight_decay: float,
) -> tuple[mx.array, mx.array, mx.array, mx.array]:
    """Apply exact bias-corrected AdamW without optimizer objects or host indices."""
    rowwise = count.ndim == ROW_COUNT_RANK
    next_count = count + mask.astype(mx.uint64)
    effective_count = mx.where(mask, next_count, mx.ones_like(next_count))
    expanded_mask = _broadcast_row(mask, parameter) if rowwise else mask
    updated, next_first, next_second = _adamw_math(
        parameter, first, second, effective_count, gradient,
        learning_rate=learning_rate, betas=betas, eps=eps,
        weight_decay=weight_decay)

    return (
        mx.where(expanded_mask, updated, parameter),
        mx.where(expanded_mask, next_first, first),
        mx.where(expanded_mask, next_second, second),
        next_count,
    )


def adamw_selected_rows_update(
    parameter, first, second, count, gradient, mask, row_indices, *,
    learning_rate, betas, eps, weight_decay,
):
    """Update only authority-selected rows without evaluating frozen-row AdamW."""
    indices = mx.array(row_indices, dtype=mx.uint32)
    selected_count = count[indices] + 1
    updated, next_first, next_second = _adamw_math(
        parameter[indices], first[indices], second[indices], selected_count,
        gradient[indices], learning_rate=learning_rate, betas=betas, eps=eps,
        weight_decay=weight_decay)
    next_parameter = parameter.at[indices].add(updated - parameter[indices])
    next_m = first.at[indices].add(next_first - first[indices])
    next_v = second.at[indices].add(next_second - second[indices])
    # MLX GPU scatter does not support uint64. The already-authoritative device
    # mask updates the small clock vector without any host row extraction.
    next_counts = count + mask.astype(mx.uint64)
    return next_parameter, next_m, next_v, next_counts


__all__ = (
    "OptimizerParentWitness", "adamw_leaf_update", "adamw_selected_rows_update",
    "issue_optimizer_parent_witness", "optimizer_parent_witness_matches",
)
