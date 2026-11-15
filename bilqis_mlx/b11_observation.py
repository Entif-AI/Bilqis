"""Process-local, non-authoritative B11 performance observation."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar


_ACTIVE = ContextVar("bilqis_b11_observation", default=None)


@contextmanager
def source_replay_observation():
    state = {"provider_draws": 0, "atlas_reloads": 0}
    token = _ACTIVE.set(state)
    try:
        yield state
    finally:
        _ACTIVE.reset(token)


def note_provider_draw() -> None:
    state = _ACTIVE.get()
    if state is not None:
        state["provider_draws"] += 1


def note_atlas_reload() -> None:
    state = _ACTIVE.get()
    if state is not None:
        state["atlas_reloads"] += 1


def attach_performance_observation(target, observation: dict):
    """Attach optional telemetry without granting it execution authority."""
    try:
        object.__setattr__(target, "_performance_observation", observation)
    except (AttributeError, TypeError):
        pass
    return target


__all__ = (
    "attach_performance_observation", "note_atlas_reload", "note_provider_draw",
    "source_replay_observation",
)
