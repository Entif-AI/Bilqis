"""Non-authoritative instrumentation for A09 frontier-history verification."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class FrontierVerificationMetrics:
    snapshots_rehashed: int = 0
    historical_bytes_serialized: int = 0
    receipt_history_lookups: int = 0
    history_index_nodes_written: int = 0


_ACTIVE = ContextVar("bilqis_frontier_verification_metrics", default=None)


def note_snapshot_rehash(*, historical_bytes: int = 0) -> None:
    state = _ACTIVE.get()
    if state is not None:
        state["snapshots_rehashed"] += 1
        state["historical_bytes_serialized"] += historical_bytes


def note_receipt_history_lookup() -> None:
    state = _ACTIVE.get()
    if state is not None:
        state["receipt_history_lookups"] += 1


def note_history_index_node_write() -> None:
    state = _ACTIVE.get()
    if state is not None:
        state["history_index_nodes_written"] += 1


@contextmanager
def frontier_verification_measurement(observer):
    """Measure planner verification work without granting the metrics authority."""
    if observer is None:
        yield
        return
    state = {
        "snapshots_rehashed": 0,
        "historical_bytes_serialized": 0,
        "receipt_history_lookups": 0,
        "history_index_nodes_written": 0,
    }
    token = _ACTIVE.set(state)
    try:
        yield
    finally:
        _ACTIVE.reset(token)
        metrics = FrontierVerificationMetrics(**state)
        try:
            observer(metrics)
        except Exception:
            pass


__all__ = (
    "FrontierVerificationMetrics", "frontier_verification_measurement",
    "note_history_index_node_write", "note_receipt_history_lookup",
    "note_snapshot_rehash",
)
