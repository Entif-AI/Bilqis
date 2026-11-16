"""Disposable synchronization witness for BAMF optimizer-step verification."""
from __future__ import annotations

from dataclasses import dataclass
import time
from unittest.mock import patch

import mlx.core as mx
import mlx.optimizers as optim
import numpy as np

from bilqis_mlx.runtime import atlas_optimizer
from bilqis_mlx.runtime.atlas_optimizer import (
    AdamWHyperparameters, AdamWStateTree, _adamw_update,
)


@dataclass(frozen=True)
class OptimizerStepReport:
    leaf_count: int
    full_state_validations: int
    explicit_eval_batches: int
    numpy_mask_readbacks: int
    optimizer_instances: int
    wall_seconds: float


def realistic_step_report(leaf_count: int = 214) -> OptimizerStepReport:
    """Run a disposable mixed dense/rowwise step and count host boundaries."""
    parameters = {}
    first = {}
    second = {}
    counts = {}
    gradients = {}
    masks = {}
    authority = {}
    decay = {}
    for index in range(leaf_count):
        name = f"fixture.{index}"
        value = mx.full((4, 4), .1 + index / 10000, dtype=mx.float32)
        parameters[name] = value
        first[name] = mx.zeros_like(value)
        second[name] = mx.zeros_like(value)
        rowwise = index % 2 == 0
        counts[name] = (
            mx.zeros((4,), dtype=mx.uint64) if rowwise
            else mx.array(0, dtype=mx.uint64))
        gradients[name] = mx.full(value.shape, .01, dtype=mx.float32)
        masks[name] = (
            mx.array([True, False, True, False]) if rowwise else mx.array(True))
        authority[name] = (False, (0, 2)) if rowwise else (True, ())
        decay[name] = index % 3 != 0
    parent = AdamWStateTree(parameters, first, second, counts)
    hp = AdamWHyperparameters(.001, (.9, .95), 1e-8, .01)

    validation_calls = 0
    eval_calls = 0
    readbacks = 0
    optimizer_instances = 0
    original_validate = AdamWStateTree.validate
    original_eval = mx.eval
    original_asarray = np.asarray
    original_optimizer = optim.AdamW

    def counted_validate(state):
        nonlocal validation_calls
        validation_calls += 1
        return original_validate(state)

    def counted_eval(*args, **kwargs):
        nonlocal eval_calls
        eval_calls += 1
        return original_eval(*args, **kwargs)

    def counted_asarray(*args, **kwargs):
        nonlocal readbacks
        readbacks += 1
        return original_asarray(*args, **kwargs)

    def counted_optimizer(*args, **kwargs):
        nonlocal optimizer_instances
        optimizer_instances += 1
        return original_optimizer(*args, **kwargs)

    started = time.perf_counter()
    with (patch.object(AdamWStateTree, "validate", counted_validate),
          patch.object(mx, "eval", counted_eval),
          patch.object(atlas_optimizer.np, "asarray", counted_asarray),
          patch.object(optim, "AdamW", counted_optimizer)):
        _adamw_update(
            parent, gradients, masks, hp, decay=decay,
            loss_bearing=True, max_norm=1.,
            participation_authority=authority)
    return OptimizerStepReport(
        leaf_count, validation_calls, eval_calls, readbacks,
        optimizer_instances, time.perf_counter() - started)


__all__ = ("OptimizerStepReport", "realistic_step_report")
