"""Run, school, capability, and curriculum snapshots for Admin Main Frame."""
from __future__ import annotations

from dataclasses import dataclass

from .model import (
    DataValue, RecordMeta, WireRecord, is_name, is_names, is_wire_integer, require,
)


@dataclass(frozen=True)
class RunContext(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.run-context/v1"
    meta: RecordMeta
    run_state: str
    optimizer_step: int
    stage: str

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_name(self.run_state) and is_name(self.stage), "RUN_CONTEXT_STATE")
        require(is_wire_integer(self.optimizer_step) and self.optimizer_step >= 0,
                "OPTIMIZER_STEP")


@dataclass(frozen=True)
class OperatorView(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.operator-view/v1"
    meta: RecordMeta
    learner_state: str
    stage: str
    active_capability_id: str | None
    related_record_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_name(self.learner_state) and is_name(self.stage), "OPERATOR_STATE")
        require(self.active_capability_id is None or is_name(self.active_capability_id),
                "ACTIVE_CAPABILITY")
        require(is_names(self.related_record_ids), "RELATED_RECORDS")


@dataclass(frozen=True)
class SchoolSnapshot(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.school-snapshot/v1"
    meta: RecordMeta
    school_state: str
    current_grade: str | None
    admitted_grades: tuple[str, ...]
    capability_count: DataValue
    mastered_count: DataValue

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_name(self.school_state), "SCHOOL_STATE")
        require(self.current_grade is None or is_name(self.current_grade), "CURRENT_GRADE")
        require(is_names(self.admitted_grades), "ADMITTED_GRADES")
        require(type(self.capability_count) is DataValue
                and type(self.mastered_count) is DataValue, "SCHOOL_VALUES")


@dataclass(frozen=True)
class CapabilitySnapshot(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.capability-snapshot/v1"
    meta: RecordMeta
    capability_id: str
    grade_id: str
    status: str
    score_correct: DataValue
    score_total: DataValue
    debt: DataValue

    def __post_init__(self) -> None:
        super().__post_init__()
        require(all(is_name(item) for item in (
            self.capability_id, self.grade_id, self.status)), "CAPABILITY_IDENTITY")
        require(all(type(item) is DataValue for item in (
            self.score_correct, self.score_total, self.debt)), "CAPABILITY_VALUES")


@dataclass(frozen=True)
class CurriculumFrontier(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.curriculum-frontier/v1"
    meta: RecordMeta
    frontier_id: str
    ready_capability_ids: tuple[str, ...]
    held_capability_ids: tuple[str, ...]
    admitted_capability_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        require(is_name(self.frontier_id), "FRONTIER_ID")
        require(all(is_names(items) for items in (
            self.ready_capability_ids, self.held_capability_ids,
            self.admitted_capability_ids)), "FRONTIER_CAPABILITIES")
