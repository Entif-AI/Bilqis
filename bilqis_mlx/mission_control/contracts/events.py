"""Episode, decision, compiler, salience, and correction records."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .model import (
    DataValue, RecordMeta, WireRecord, is_name, is_sha256, is_time, is_wire_integer,
    require,
)


class CandidateOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    HELD = "HELD"
    ACTION_REQUIRED = "ACTION_REQUIRED"


@dataclass(frozen=True)
class LearningEpisode(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.learning-episode/v1"
    meta: RecordMeta
    episode_id: str
    capability_id: str
    visit_id: str
    state: str
    started_at: int
    completed_at: int | None

    def __post_init__(self) -> None:
        super().__post_init__()
        require(all(is_name(item) for item in (
            self.episode_id, self.capability_id, self.visit_id, self.state)), "EPISODE_ID")
        require(is_time(self.started_at), "EPISODE_START")
        require(self.completed_at is None or (
            is_time(self.completed_at) and self.completed_at >= self.started_at), "EPISODE_END")


@dataclass(frozen=True)
class CandidateDecision(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.candidate-decision/v1"
    meta: RecordMeta
    candidate_id: str
    capability_id: str
    outcome: CandidateOutcome
    reason_code: str

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_name(self.candidate_id) and is_name(self.capability_id), "CANDIDATE_ID")
        require(type(self.outcome) is CandidateOutcome and is_name(self.reason_code), "CANDIDATE_OUTCOME")


@dataclass(frozen=True)
class FrameCompileReceipt(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.frame-compile-receipt/v1"
    meta: RecordMeta
    frame_id: str
    source_frame_sha256: str
    compiled_frame_sha256: str
    fallback_used: bool
    constituent_expansions: int

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_name(self.frame_id), "FRAME_ID")
        require(is_sha256(self.source_frame_sha256)
                and is_sha256(self.compiled_frame_sha256), "FRAME_DIGEST")
        require(type(self.fallback_used) is bool, "FRAME_FALLBACK")
        require(is_wire_integer(self.constituent_expansions)
                and self.constituent_expansions >= 0, "FRAME_EXPANSIONS")


@dataclass(frozen=True)
class SalienceEvent(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.salience-event/v1"
    meta: RecordMeta
    salience_id: str
    capability_id: str
    impact: DataValue
    exigency: DataValue
    novelty: DataValue
    action_kind: str

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_name(self.salience_id) and is_name(self.capability_id)
                and is_name(self.action_kind), "SALIENCE_ID")
        require(all(type(item) is DataValue for item in (
            self.impact, self.exigency, self.novelty)), "SALIENCE_VALUES")


@dataclass(frozen=True)
class CorrectionEvent(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.correction-event/v1"
    meta: RecordMeta
    correction_id: str
    correction_generation: int
    target_ref: str
    old_digest: str
    new_digest: str
    state: str

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_name(self.correction_id) and is_name(self.target_ref)
                and is_name(self.state), "CORRECTION_ID")
        require(is_wire_integer(self.correction_generation)
                and self.correction_generation >= 0, "CORRECTION_GENERATION")
        require(is_sha256(self.old_digest) and is_sha256(self.new_digest), "CORRECTION_DIGEST")
