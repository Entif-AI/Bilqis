"""Immutable pointers to the prior complete native FP32 checkpoint.

Nothing here loads, copies or mutates the historical checkpoint.
"""
from dataclasses import dataclass

from ..semantics.abi import HISTORICAL_ABI


@dataclass(frozen=True)
class SourceCheckpoint:
    basename: str
    sha256: str
    old_rubric_correct: int
    old_rubric_total: int
    optimizer_step: int


AUDITED_PARENT = SourceCheckpoint(
    basename="student-116760-7e9af4651f28.pt",
    sha256=HISTORICAL_ABI.checkpoint_sha256,
    old_rubric_correct=1052,
    old_rubric_total=1150,
    optimizer_step=116760,
)
