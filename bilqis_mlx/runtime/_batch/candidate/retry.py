"""Bind C08 memory recovery to the Factory candidate's pre-step state."""
from __future__ import annotations

from copy import copy
import time
from types import SimpleNamespace
from uuid import uuid4

import mlx.core as mx

from bilqis_mlx.learning._atlas_candidate.identity import optimizer_snapshot_digest

from ..atlas_memory_retry import (
    CandidateMemoryExhausted, OOMReceipt, RestorationReceipt, RetryState,
    handle_oom, snapshot_mlx_memory,
)
from ..factory_candidate_components import _invalid, _resource_rows
from ..c08_distributed.c08_oom import is_mlx_oom


def _is_mlx_oom(error):
    return is_mlx_oom(error)


def execute_with_oom_retry(
        execute, plan, *, parent, candidate, prepared, budget, cache, require_current):
    """Repartition the same delivery against the untouched pre-step optimizer."""
    accepted = parent.retained_state
    optimizer = accepted.optimizer if candidate is None else candidate.optimizer
    optimizer_step = accepted.optimizer_step + (0 if candidate is None else candidate.update_steps)
    retained_digest = (
        cache._candidate_identity_sha256 if candidate is None
        else candidate._parent_identity_sha256)
    manifest = cache.accepted_manifest_sha256
    # MLX shallow copies retain the pre-step array descriptors without copying
    # buffers. Stream their numerical digest only after an allocator failure.
    snapshot = SimpleNamespace(**{
        group: {name: copy(value) for name, value in getattr(optimizer, group).items()}
        for group in ("parameters", "m", "v", "update_counts")
    })
    state = None

    def restore(retained_sha256, snapshot_sha256, generation):
        # No optimizer rollback is needed: B12 builds new trees out of place
        # and the failed attempt never returned a transaction to its caller.
        current_cache, current_generation = require_current()
        if (retained_sha256 != retained_digest
                or current_cache.accepted_manifest_sha256 != manifest
                or current_generation != generation
                or optimizer_snapshot_digest(optimizer, optimizer_step) != snapshot_sha256):
            _invalid("BAMF_C08_RESTORATION_FAILED")
        return RestorationReceipt(retained_digest, snapshot_sha256, generation, True)

    while True:
        try:
            return execute(plan), plan, state
        except RuntimeError as error:
            if not _is_mlx_oom(error):
                raise
            exception_class = type(error).__name__
        # Release the failed traceback and its partial gradient/optimizer graph
        # before reclaiming allocator cache or hashing the retained snapshot.
        telemetry = snapshot_mlx_memory(mx, observed_at=time.time_ns())
        mx.clear_cache()
        if state is None:
            state = RetryState.start(
                plan, retained_candidate_digest=retained_digest,
                optimizer_snapshot_digest=optimizer_snapshot_digest(snapshot, optimizer_step))
        failure = OOMReceipt(
            uuid4().hex, plan.microbatch_size, plan.source_digest, plan.generation_binding,
            plan.optimizer_step_seed, telemetry.peak_bytes, telemetry.cache_bytes,
            telemetry.observed_at, exception_class)
        state = handle_oom(
            state, failure, _resource_rows(prepared), parent.topology, budget,
            restore=restore)
        if state.current_plan is None:
            raise CandidateMemoryExhausted(state)
        plan = state.current_plan
