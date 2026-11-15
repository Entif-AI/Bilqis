"""Immutable motif read records and shared geometry validation."""
from __future__ import annotations

from dataclasses import dataclass
import re

import mlx.core as mx

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.semantics.context_eligibility import ContextEligibility
from bilqis_mlx.semantics.frame_schema import AtomicFrame, FrameInstance, FrameSchema
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2


READ_SCHEMA = "bilqis.mlx.motif-read-result/v1"
POSITION_SCHEMA = "bilqis.mlx.motif-read-position/v1"
WIDTH = ModelTopologySpecV2.width
MOTIF_WIDTH = 128
READ_TENSOR_RANK = 3
FEATURE_AXIS = 2
BATCH_PREFIX_AXES = 2
DISPOSITIONS = frozenset({
    "EXACT", "STRUCTURAL", "MISS", "HELD", "FOREIGN_RELEASE",
    "QUARANTINED_NO_HIT",
})
_SHA = re.compile(r"[0-9a-f]{64}\Z")


def _invalid() -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


@dataclass(frozen=True)
class MotifReadPosition:
    envelope: ContextEligibility
    schema: FrameSchema | None
    source_family: str | None = None
    schema_version: str = POSITION_SCHEMA

    def __post_init__(self) -> None:
        if (type(self.envelope) is not ContextEligibility
                or (self.schema is not None and type(self.schema) is not FrameSchema)
                or (type(self.envelope.frame) is FrameInstance
                    and (self.schema is None
                         or self.schema.schema_id
                         != self.envelope.frame.frame_schema_id
                         or self.schema.revision
                         != self.envelope.frame.frame_schema_revision))
                or (type(self.envelope.frame) is AtomicFrame
                    and self.schema is not None)
                or (self.source_family is not None
                    and (not isinstance(self.source_family, str)
                         or not self.source_family))
                or self.schema_version != POSITION_SCHEMA):
            _invalid()


@dataclass(frozen=True)
class MotifReadResult:
    hidden: mx.array
    dispositions: tuple[tuple[str, ...], ...]
    participating_slots: tuple[int, ...]
    context_digests: tuple[str | None, ...]
    row_participating_slots: tuple[tuple[int, ...], ...] = ()
    schema_version: str = READ_SCHEMA

    def __post_init__(self) -> None:
        if (not isinstance(self.hidden, mx.array)
                or self.hidden.ndim != READ_TENSOR_RANK
                or self.hidden.shape[FEATURE_AXIS] != WIDTH
                or self.hidden.dtype != mx.float32
                or not isinstance(self.dispositions, tuple)
                or len(self.dispositions) != self.hidden.shape[0]
                or any(not isinstance(row, tuple)
                       or len(row) != self.hidden.shape[1]
                       or any(item not in DISPOSITIONS for item in row)
                       for row in self.dispositions)
                or not isinstance(self.participating_slots, tuple)
                or any(type(slot) is not int or slot < 0
                       for slot in self.participating_slots)
                or self.participating_slots
                != tuple(sorted(set(self.participating_slots)))
                or not isinstance(self.context_digests, tuple)
                or len(self.context_digests) != self.hidden.shape[0]
                or any(item is not None
                       and (not isinstance(item, str)
                            or not _SHA.fullmatch(item))
                       for item in self.context_digests)
                or (self.row_participating_slots
                    and (len(self.row_participating_slots) != self.hidden.shape[0]
                         or any(type(row) is not tuple
                                or row != tuple(sorted(set(row)))
                                or any(type(slot) is not int or slot < 0 for slot in row)
                                for row in self.row_participating_slots)
                         or tuple(sorted({
                             slot for row in self.row_participating_slots for slot in row
                         })) != self.participating_slots))
                or self.schema_version != READ_SCHEMA):
            _invalid()
