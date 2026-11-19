"""MLX collective reduction for C08.4 rank-local mean gradients."""
from __future__ import annotations

import time
from typing import Mapping

import mlx.core as mx

from .c08_gradient_accumulation import _invalid
def all_reduce_fp32_rank_mean(
    gradients: Mapping,
    mean_loss: mx.array,
    *,
    local_rows: int,
    total_rows: int,
    group=None,
) -> tuple[dict, mx.array, float]:
    """Reduce one weighted rank mean into the global logical FP32 mean."""
    if (not isinstance(gradients, Mapping) or not gradients
            or any(not isinstance(value, mx.array) for value in gradients.values())
            or not isinstance(mean_loss, mx.array)
            or type(local_rows) is not int or local_rows < 1
            or type(total_rows) is not int or total_rows < local_rows):
        _invalid("C08_DISTRIBUTED_LOGICAL_ROW_COUNT_INVALID")
    if group is not None and group.size() < 1:
        _invalid("C08_DISTRIBUTED_GROUP_INVALID")
    weight = local_rows / total_rows
    started = time.perf_counter()
    reduced = {
        name: mx.distributed.all_sum(
            value.astype(mx.float32) * weight, group=group)
        for name, value in sorted(gradients.items())
    }
    loss = mx.distributed.all_sum(
        mean_loss.astype(mx.float32) * weight, group=group)
    mx.eval(reduced, loss)
    return reduced, loss, float(time.perf_counter() - started)


def require_collective_matches_reference(
    reference_gradients: Mapping,
    reference_loss: mx.array,
    collective_gradients: Mapping,
    collective_loss: mx.array,
    *,
    atol: float = 1e-6,
) -> None:
    """Reject a collective result that disagrees with deterministic reduction."""
    if (not isinstance(reference_gradients, Mapping)
            or not isinstance(collective_gradients, Mapping)
            or tuple(sorted(reference_gradients))
               != tuple(sorted(collective_gradients))
            or type(atol) is not float or atol < 0.0):
        _invalid("C08_DISTRIBUTED_COLLECTIVE_SHAPE_DRIFT")
    for name in sorted(reference_gradients):
        if not bool(mx.allclose(
                reference_gradients[name], collective_gradients[name],
                rtol=0.0, atol=atol)):
            _invalid("C08_DISTRIBUTED_COLLECTIVE_GRADIENT_DRIFT")
    if not bool(mx.allclose(
            reference_loss, collective_loss, rtol=0.0, atol=atol)):
        _invalid("C08_DISTRIBUTED_COLLECTIVE_LOSS_DRIFT")


__all__ = (
    "all_reduce_fp32_rank_mean", "require_collective_matches_reference",
)
