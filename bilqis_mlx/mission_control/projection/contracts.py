"""Versioned CP06 projection contracts and operator-visible state."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from bilqis_mlx.errors import ErrorBus, SCHOOL


PROJECTION_SCHEMA = "bilqis.bamf.mission-control.projection-index/v1"
PROJECTION_SCHEMA_VERSION = 1


def projection_invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID, reason=reason)


class ProjectionFrontierState(StrEnum):
    EMPTY = "EMPTY"
    CURRENT = "CURRENT"
    STALE = "STALE"
    DIVERGED = "DIVERGED"


@dataclass(frozen=True)
class ProjectionStats:
    active_records: int
    revisions: int
    references: int
    events: int


@dataclass(frozen=True)
class ProjectionFrontierStatus:
    state: ProjectionFrontierState
    stream_id: str
    projected_epoch_id: str | None
    projected_next_ordinal: int | None
    authoritative_epoch_id: str
    authoritative_next_ordinal: int
