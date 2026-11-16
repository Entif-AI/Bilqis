"""Autonomy work and routing contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .evidence_contracts import EvidenceObligation, EvidenceReceipt


@dataclass(frozen=True)
class CurriculumWorkItem:
    capability_id: str
    obligation: EvidenceObligation
    teaching_option_ids: tuple[str, ...]
    evidence_complete_prerequisites: tuple[str, ...]

    def __post_init__(self) -> None:
        if (not self.capability_id or self.obligation.capability_id != self.capability_id or
                not self.teaching_option_ids or
                len(set(self.teaching_option_ids)) != len(self.teaching_option_ids)):
            raise ValueError("AUTONOMY_WORK_ITEM_INVALID")


@dataclass(frozen=True)
class TeachingWorkItem:
    capability_id: str
    obligation: EvidenceObligation
    teaching_option_ids: tuple[str, ...]
    failed_evidence: EvidenceReceipt

    def __post_init__(self) -> None:
        if (not self.capability_id or
                self.obligation.capability_id != self.capability_id or
                self.failed_evidence.obligation_id != self.obligation.obligation_id or
                not self.teaching_option_ids or
                len(set(self.teaching_option_ids)) != len(self.teaching_option_ids)):
            raise ValueError("AUTONOMY_TEACHING_WORK_ITEM_INVALID")


class AutonomyActionKind(str, Enum):
    SOURCE_COVERAGE = "SOURCE_COVERAGE"
    TEACHING = "TEACHING"
    LEARNING_EVIDENCE = "LEARNING_EVIDENCE"
    SAFE_HOLD = "SAFE_HOLD"
    QUALIFICATION = "QUALIFICATION"


@dataclass(frozen=True)
class AutonomyAction:
    kind: AutonomyActionKind
    source_coverage_debt: str | None = None
    evidence_work: CurriculumWorkItem | None = None
    teaching_work: TeachingWorkItem | None = None
    deferred_obligation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AutonomyActionKind):
            raise ValueError("AUTONOMY_ACTION_KIND_INVALID")
        if (len(set(self.deferred_obligation_ids)) != len(self.deferred_obligation_ids) or
                any(not isinstance(item, str) or not item
                    for item in self.deferred_obligation_ids)):
            raise ValueError("AUTONOMY_ACTION_DEFERRAL_INVALID")
        if self.kind is AutonomyActionKind.SOURCE_COVERAGE:
            if (not self.source_coverage_debt or self.evidence_work is not None or
                    self.teaching_work is not None or self.deferred_obligation_ids):
                raise ValueError("AUTONOMY_SOURCE_ACTION_INVALID")
        elif self.kind is AutonomyActionKind.TEACHING:
            if (self.source_coverage_debt is not None or self.evidence_work is not None or
                    self.teaching_work is None):
                raise ValueError("AUTONOMY_TEACHING_ACTION_INVALID")
        elif self.kind is AutonomyActionKind.LEARNING_EVIDENCE:
            if (self.source_coverage_debt is not None or self.evidence_work is None or
                    self.teaching_work is not None):
                raise ValueError("AUTONOMY_LEARNING_ACTION_INVALID")
        elif self.kind is AutonomyActionKind.SAFE_HOLD:
            if (self.source_coverage_debt is not None or self.evidence_work is not None or
                    self.teaching_work is not None or not self.deferred_obligation_ids):
                raise ValueError("AUTONOMY_SAFE_HOLD_ACTION_INVALID")
        elif (self.source_coverage_debt is not None or self.evidence_work is not None or
              self.teaching_work is not None or self.deferred_obligation_ids):
            raise ValueError("AUTONOMY_QUALIFICATION_ACTION_INVALID")
