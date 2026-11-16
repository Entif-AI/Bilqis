"""Typed, observational #1318 visit and generated-grade evidence contracts."""
from __future__ import annotations
from dataclasses import dataclass
from .model import is_name, is_wire_integer, require
from .trainer_learning_health import (LearningHealthScore, LearningHealthWarning, LearningHealthEvidence)
from .trainer_visit_contract import (VisitCapabilityScore, VisitRankingEvidence, VisitRoleCount, RetentionStageTiming, VisitEvidence)


@dataclass(frozen=True)
class GeneratedGradeMemberEvidence:
    semantic_id: str
    developmental_cost_state: str
    a08_provenance: tuple[str, ...]
    a09_provenance: tuple[str, ...]
    acquisition_cost_ref: str | None

    def __post_init__(self):
        from .model import is_names
        require(is_name(self.semantic_id), 'GRADE_MEMBER_ID')
        require(self.developmental_cost_state in
                {'MEASURED', 'BOOTSTRAPPED', 'UNKNOWN'}, 'GRADE_MEMBER_COST_STATE')
        require(is_names(self.a08_provenance) and is_names(self.a09_provenance),
                'GRADE_MEMBER_PROVENANCE')
        require(self.acquisition_cost_ref is None or is_name(self.acquisition_cost_ref),
                'GRADE_MEMBER_COST_REF')


@dataclass(frozen=True)
class GradeSynthesisDimension:
    dimension: str
    state: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self):
        from .model import is_names
        require(is_name(self.dimension), 'GRADE_DIMENSION')
        require(self.state in {'PRESENT', 'UNKNOWN', 'NOT_APPLICABLE'},
                'GRADE_DIMENSION_STATE')
        require(is_names(self.evidence_refs), 'GRADE_DIMENSION_REFS')


@dataclass(frozen=True)
class DeferredGradeCandidate:
    semantic_id: str
    reasons: tuple[str, ...]

    def __post_init__(self):
        from .model import is_names
        require(is_name(self.semantic_id), 'GRADE_DEFERRED_ID')
        require(is_names(self.reasons, allow_empty=False), 'GRADE_DEFERRED_REASONS')


@dataclass(frozen=True)
class GeneratedGradeHold:
    code: str
    semantic_id: str | None
    detail: str | None

    def __post_init__(self):
        require(is_name(self.code), 'GRADE_HOLD_CODE')
        require(self.semantic_id is None or is_name(self.semantic_id), 'GRADE_HOLD_SEMANTIC')
        require(self.detail is None or is_name(self.detail), 'GRADE_HOLD_DETAIL')


@dataclass(frozen=True)
class GeneratedGradeEvidence:
    state: str
    grade_id: str | None
    proposal_id: str | None
    definition_id: str | None
    definition_version: str | None
    predecessor_definition_id: str | None
    learner_evidence_epoch: str | None
    factory_release_sha256: str | None
    policy_epoch: str | None
    a08_provenance: tuple[str, ...]
    a09_provenance: tuple[str, ...]
    selected_semantic_ids: tuple[str, ...]
    members: tuple[GeneratedGradeMemberEvidence, ...]
    developmental_slope_state: str
    synthesis_dimensions: tuple[GradeSynthesisDimension, ...]
    representative_coverage: str | None
    downstream_unlocks: int | None
    constituent_rationale: str | None
    required_bridges: tuple[str, ...]
    deferred_candidates: tuple[DeferredGradeCandidate, ...]
    holds: tuple[GeneratedGradeHold, ...]
    predecessor_certification_receipt: str | None

    def __post_init__(self):
        from .model import is_sha256, is_names
        require(self.state in {'MEASURED', 'BOOTSTRAPPED', 'UNKNOWN'},
                'GRADE_EVIDENCE_STATE')
        require(self.developmental_slope_state in
                {'MEASURED', 'BOOTSTRAPPED', 'UNKNOWN'}, 'GRADE_SLOPE_STATE')
        for value in (self.grade_id, self.proposal_id, self.definition_id, self.definition_version,
                      self.predecessor_definition_id, self.learner_evidence_epoch,
                      self.policy_epoch, self.representative_coverage,
                      self.constituent_rationale):
            require(value is None or is_name(value), 'GRADE_EVIDENCE_NAME')
        require(self.factory_release_sha256 is None
                or is_sha256(self.factory_release_sha256), 'GRADE_EVIDENCE_RELEASE')
        require(self.predecessor_certification_receipt is None
                or is_name(self.predecessor_certification_receipt),
                'GRADE_EVIDENCE_CERTIFICATION')
        for values in (self.a08_provenance, self.a09_provenance,
                       self.selected_semantic_ids, self.required_bridges):
            require(is_names(values), 'GRADE_EVIDENCE_NAMES')
        require(all(type(item) is GeneratedGradeMemberEvidence for item in self.members),
                'GRADE_EVIDENCE_MEMBERS')
        require(all(type(item) is GradeSynthesisDimension for item in self.synthesis_dimensions),
                'GRADE_EVIDENCE_DIMENSIONS')
        require(all(type(item) is DeferredGradeCandidate for item in self.deferred_candidates),
                'GRADE_EVIDENCE_DEFERRED')
        require(all(type(item) is GeneratedGradeHold for item in self.holds),
                'GRADE_EVIDENCE_HOLDS')
        require(self.downstream_unlocks is None or (
            is_wire_integer(self.downstream_unlocks) and self.downstream_unlocks >= 0),
            'GRADE_EVIDENCE_UNLOCKS')
