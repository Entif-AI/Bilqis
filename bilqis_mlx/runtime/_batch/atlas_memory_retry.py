"""C08.2 read-only MLX memory telemetry and one bounded OOM recovery.

The retained neural/optimizer owner supplies the restoration callback. This
module never draws new examples, mutates MLX or promotes a checkpoint.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import re
from typing import Callable

from ..errors import ErrorBus, SCHOOL
from .atlas_resources import (
    BatchPlan, MemoryBudget, MICROBATCH_SIZES, ResourceRow,
    plan_microbatches,
)
from .model_topology_v2 import ModelTopologySpecV2


MEMORY_TELEMETRY_SCHEMA = "bilqis.c08.memory-telemetry/v1"
OOM_RECEIPT_SCHEMA = "bilqis.c08.oom-receipt/v1"
RESTORATION_RECEIPT_SCHEMA = "bilqis.c08.restoration-receipt/v1"
RETRY_STATE_SCHEMA = "bilqis.c08.retry-state/v1"
RESOURCE_REJECTION_SCHEMA = "bilqis.c08.candidate-resource-rejection/v1"
OOM_EXHAUSTED = "BAMF_C08_OOM_EXHAUSTED"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.BAMF_RESOURCES.INVALID, reason=reason)


def _sha(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value))


def _name(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _count(value: object) -> bool:
    return type(value) is int and value >= 0


@dataclass(frozen=True)
class MemoryTelemetry:
    active_bytes: int
    cache_bytes: int
    peak_bytes: int
    observed_at: int
    mlx_version: str
    schema_version: str = MEMORY_TELEMETRY_SCHEMA

    def __post_init__(self) -> None:
        if (not all(_count(item) for item in (
                    self.active_bytes, self.cache_bytes,
                    self.peak_bytes, self.observed_at))
                or self.peak_bytes < self.active_bytes
                or not _name(self.mlx_version)
                or self.schema_version != MEMORY_TELEMETRY_SCHEMA):
            _invalid("BAMF_C08_MEMORY_TELEMETRY_INVALID")


def snapshot_mlx_memory(mx: object, *, observed_at: int) -> MemoryTelemetry:
    """Read installed MLX's active/cache/peak getters without resetting state."""
    getters = tuple(
        getattr(mx, name, None) for name in (
            "get_active_memory", "get_cache_memory", "get_peak_memory"))
    if (not all(callable(getter) for getter in getters)
            or not _count(observed_at)
            or not _name(getattr(mx, "__version__", None))):
        _invalid("BAMF_C08_MLX_MEMORY_API_UNAVAILABLE")
    active, cache, peak = (getter() for getter in getters)
    return MemoryTelemetry(
        active, cache, peak, observed_at, mx.__version__)


@dataclass(frozen=True)
class OOMReceipt:
    failure_id: str
    failed_microbatch_size: int
    source_digest: str
    generation_binding: str
    optimizer_step_seed: int
    peak_allocated_bytes: int
    cache_bytes: int
    observed_at: int
    exception_class: str
    schema_version: str = OOM_RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        if (not _name(self.failure_id)
                or self.failed_microbatch_size not in MICROBATCH_SIZES
                or not _sha(self.source_digest)
                or not _name(self.generation_binding)
                or not all(_count(item) for item in (
                    self.optimizer_step_seed, self.peak_allocated_bytes,
                    self.cache_bytes, self.observed_at))
                or not _name(self.exception_class)
                or self.schema_version != OOM_RECEIPT_SCHEMA):
            _invalid("BAMF_C08_OOM_RECEIPT_INVALID")


@dataclass(frozen=True)
class RestorationReceipt:
    retained_candidate_digest: str
    optimizer_snapshot_digest: str
    generation_binding: str
    restored: bool
    schema_version: str = RESTORATION_RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        if (not _sha(self.retained_candidate_digest)
                or not _sha(self.optimizer_snapshot_digest)
                or not _name(self.generation_binding)
                or type(self.restored) is not bool
                or self.schema_version != RESTORATION_RECEIPT_SCHEMA):
            _invalid("BAMF_C08_RESTORATION_RECEIPT_INVALID")


class RetryStatus(str, Enum):
    PLANNED = "PLANNED"
    RETRY_PENDING = "RETRY_PENDING"
    EXHAUSTED = "EXHAUSTED"


@dataclass(frozen=True)
class RetryState:
    original_plan: BatchPlan
    current_plan: BatchPlan | None
    retained_candidate_digest: str
    optimizer_snapshot_digest: str
    retries_used: int
    status: RetryStatus
    failures: tuple[OOMReceipt, ...] = ()
    restorations: tuple[RestorationReceipt, ...] = ()
    schema_version: str = RETRY_STATE_SCHEMA

    def __post_init__(self) -> None:
        if (not isinstance(self.original_plan, BatchPlan)
                or (self.current_plan is not None
                    and not isinstance(self.current_plan, BatchPlan))
                or not _sha(self.retained_candidate_digest)
                or not _sha(self.optimizer_snapshot_digest)
                or type(self.retries_used) is not int
                or self.retries_used not in (0, 1)
                or not isinstance(self.status, RetryStatus)
                or (self.status is RetryStatus.EXHAUSTED)
                != (self.current_plan is None)
                or (self.status is RetryStatus.PLANNED
                    and self.retries_used != 0)
                or (self.status is RetryStatus.RETRY_PENDING
                    and self.retries_used != 1)
                or not isinstance(self.failures, tuple)
                or any(not isinstance(item, OOMReceipt)
                       for item in self.failures)
                or not isinstance(self.restorations, tuple)
                or any(not isinstance(item, RestorationReceipt)
                       for item in self.restorations)
                or len(self.failures) != len(self.restorations)
                or len(self.failures) > 2
                or (self.current_plan is not None
                    and (self.current_plan.source_digest
                         != self.original_plan.source_digest
                         or self.current_plan.logical_row_ids
                         != self.original_plan.logical_row_ids
                         or self.current_plan.optimizer_step_seed
                         != self.original_plan.optimizer_step_seed
                         or self.current_plan.generation_binding
                         != self.original_plan.generation_binding))
                or self.schema_version != RETRY_STATE_SCHEMA):
            _invalid("BAMF_C08_RETRY_STATE_INVALID")

    @classmethod
    def start(
        cls, plan: BatchPlan, *, retained_candidate_digest: str,
        optimizer_snapshot_digest: str,
    ) -> "RetryState":
        return cls(
            original_plan=plan, current_plan=plan,
            retained_candidate_digest=retained_candidate_digest,
            optimizer_snapshot_digest=optimizer_snapshot_digest,
            retries_used=0, status=RetryStatus.PLANNED)


class CandidateMemoryExhausted(RuntimeError):
    """The provisional candidate was discarded after C08 exhaustion."""

    def __init__(self, state: RetryState):
        if state.status is not RetryStatus.EXHAUSTED:
            _invalid("BAMF_C08_RETRY_STATE_INVALID")
        super().__init__(OOM_EXHAUSTED)
        self.state = state

    def to_record(self) -> dict:
        return {
            "schema": RESOURCE_REJECTION_SCHEMA,
            "reason": OOM_EXHAUSTED,
            "status": self.state.status.value,
            "retries_used": self.state.retries_used,
            "logical_row_ids": list(self.state.original_plan.logical_row_ids),
            "failures": [asdict(item) for item in self.state.failures],
            "restorations": [asdict(item) for item in self.state.restorations],
        }


def handle_oom(
    state: RetryState,
    failure: OOMReceipt,
    delivered_rows: tuple[ResourceRow, ...],
    topology: ModelTopologySpecV2,
    memory_budget: MemoryBudget,
    *,
    restore: Callable[[str, str, str], RestorationReceipt],
) -> RetryState:
    """Restore first; retry once at the next smaller size, else stop safely."""
    if (not isinstance(state, RetryState)
            or not isinstance(failure, OOMReceipt)
            or state.current_plan is None
            or not callable(restore)):
        _invalid("BAMF_C08_OOM_ARGUMENT_INVALID")
    current = state.current_plan
    # Restoration takes precedence over diagnostic or source replay checks:
    # an OOM may have interrupted a partially evaluated gradient graph.
    restored = restore(
        state.retained_candidate_digest,
        state.optimizer_snapshot_digest,
        current.generation_binding)
    if (not isinstance(restored, RestorationReceipt)
            or not restored.restored
            or restored.retained_candidate_digest
            != state.retained_candidate_digest
            or restored.optimizer_snapshot_digest
            != state.optimizer_snapshot_digest
            or restored.generation_binding != current.generation_binding):
        _invalid("BAMF_C08_RESTORATION_FAILED")
    if (failure.failed_microbatch_size != current.microbatch_size
            or failure.source_digest != current.source_digest
            or failure.optimizer_step_seed != current.optimizer_step_seed
            or failure.generation_binding != current.generation_binding):
        _invalid("BAMF_C08_OOM_SOURCE_DRIFT")
    expected = plan_microbatches(
        delivered_rows, topology, memory_budget,
        max_microbatch_size=current.microbatch_size)
    if expected != current:
        _invalid("BAMF_C08_OOM_DELIVERY_REPLAY_DRIFT")
    history = (*state.failures, failure)
    restoration_history = (*state.restorations, restored)
    if state.retries_used >= 1 or current.microbatch_size == 1:
        return RetryState(
            state.original_plan, None,
            state.retained_candidate_digest,
            state.optimizer_snapshot_digest,
            state.retries_used, RetryStatus.EXHAUSTED,
            history, restoration_history)
    next_size = MICROBATCH_SIZES[
        MICROBATCH_SIZES.index(current.microbatch_size) + 1]
    smaller = plan_microbatches(
        delivered_rows, topology, memory_budget,
        max_microbatch_size=next_size)
    if (smaller.source_digest != current.source_digest
            or smaller.optimizer_step_seed != current.optimizer_step_seed
            or smaller.generation_binding != current.generation_binding
            or smaller.logical_row_ids != current.logical_row_ids):
        _invalid("BAMF_C08_RETRY_SOURCE_DRIFT")
    return RetryState(
        state.original_plan, smaller,
        state.retained_candidate_digest,
        state.optimizer_snapshot_digest,
        1, RetryStatus.RETRY_PENDING,
        history, restoration_history)
