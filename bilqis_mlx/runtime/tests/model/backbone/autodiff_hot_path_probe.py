"""Disposable counters for #1228 hot-path verification.

The probe is test-only. It counts work only while the BAMF autodiff validation
deferment is active, so the one permitted pre-transform generation binding and
the post-transform ``mx.eval`` materialization are not mislabeled as hot-path
work.
"""
from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
import time
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled


@dataclass(frozen=True)
class HotPathReport:
    forward_group_executions: int
    host_readbacks: int
    full_tree_hashes: int
    validation_synchronizations: int
    wall_seconds: float


class HotPathProbe:
    """Instrument one disposable optimizer-step callable without changing runtime."""

    def __init__(self):
        self.groups = 0
        self.readbacks = 0
        self.tree_hashes = 0
        self.syncs = 0

    def _inside_trace(self):
        return not host_tensor_validation_enabled()

    def measure_step(self, step):
        from bilqis_mlx.runtime import backbone_group_numerical as group
        from bilqis_mlx.runtime import backbone_identity as identity
        from bilqis_mlx.runtime import depth_contracts as depth
        from bilqis_mlx.learning.atlas_readout.decoder import prediction

        group_trace = group.run_backbone_group_trace
        content_digest = group._content_digest
        tree_digest = identity.bamf_parameter_tree_digest
        depth_tree_digest = depth.bamf_parameter_tree_digest
        generation_digest = depth.execution_generation_digest
        logit_fingerprint = prediction._logit_fingerprint
        mx_eval = mx.eval

        def counted_group(*args, **kwargs):
            if self._inside_trace():
                self.groups += 1
            return group_trace(*args, **kwargs)

        def counted_readback(fn):
            def wrapped(*args, **kwargs):
                if self._inside_trace():
                    self.readbacks += 1
                return fn(*args, **kwargs)
            return wrapped

        def counted_tree(fn):
            def wrapped(*args, **kwargs):
                if self._inside_trace():
                    self.tree_hashes += 1
                return fn(*args, **kwargs)
            return wrapped

        def counted_eval(*args, **kwargs):
            if self._inside_trace():
                self.syncs += 1
            return mx_eval(*args, **kwargs)

        started = time.perf_counter()
        with ExitStack() as stack:
            stack.enter_context(patch.object(group, "run_backbone_group_trace", counted_group))
            stack.enter_context(patch.object(group, "_content_digest", counted_readback(content_digest)))
            stack.enter_context(patch.object(identity, "bamf_parameter_tree_digest", counted_tree(tree_digest)))
            stack.enter_context(patch.object(depth, "bamf_parameter_tree_digest", counted_tree(depth_tree_digest)))
            stack.enter_context(patch.object(depth, "execution_generation_digest", counted_tree(generation_digest)))
            stack.enter_context(patch.object(prediction, "_logit_fingerprint", counted_readback(logit_fingerprint)))
            stack.enter_context(patch.object(mx, "eval", counted_eval))
            result = step()
        elapsed = time.perf_counter() - started
        return result, HotPathReport(
            self.groups, self.readbacks, self.tree_hashes, self.syncs, elapsed)


__all__ = ("HotPathProbe", "HotPathReport")
