"""Typed, observational #1318 visit and generated-grade evidence contracts."""
from __future__ import annotations

from dataclasses import dataclass
import math

from .model import is_name, is_wire_integer, require

@dataclass(frozen=True)
class VisitCapabilityScore:
    capability_id: str | None
    state: str
    baseline: int | None
    before: int | None
    after: int | None
    total: int | None
    delta: int | None
    loss_allowance: int | None

    def __post_init__(self):
        require(self.capability_id is None or is_name(self.capability_id),
                'VISIT_SCORE_CAPABILITY')
        require(self.state in {'MEASURED', 'NOT_MEASURED', 'UNKNOWN'},
                'VISIT_SCORE_STATE')
        values = (self.baseline, self.before, self.after, self.total, self.delta,
                  self.loss_allowance)
        require(all(value is None or is_wire_integer(value) for value in values),
                'VISIT_SCORE_INTEGER')
        if self.state == 'MEASURED':
            require(all(value is not None for value in
                        (self.baseline, self.before, self.after, self.total, self.delta)),
                    'VISIT_SCORE_MEASURED')
            require(self.total >= 0 and 0 <= self.baseline <= self.total
                    and 0 <= self.before <= self.total
                    and 0 <= self.after <= self.total
                    and self.delta == self.after - self.before,
                    'VISIT_SCORE_RANGE')
        else:
            require(all(value is None for value in
                        (self.baseline, self.before, self.after, self.total, self.delta)),
                    'VISIT_SCORE_UNMEASURED')


@dataclass(frozen=True)
class VisitRankingEvidence:
    policy_sha256: str | None
    ordinals: tuple[int, ...]
    known: tuple[bool, ...]
    dispatch_tier: int | None
    eligible_since: int | None
    downstream_unlocks: int | None
    stable_id: str | None

    def __post_init__(self):
        from .model import is_sha256
        require(self.policy_sha256 is None or is_sha256(self.policy_sha256),
                'VISIT_RANK_POLICY')
        require(len(self.ordinals) == len(self.known), 'VISIT_RANK_WIDTH')
        require(all(is_wire_integer(value) for value in self.ordinals),
                'VISIT_RANK_ORDINAL')
        require(all(type(value) is bool for value in self.known), 'VISIT_RANK_KNOWN')
        require(self.dispatch_tier is None or (
            is_wire_integer(self.dispatch_tier) and self.dispatch_tier >= 0),
            'VISIT_RANK_TIER')
        for value in (self.eligible_since, self.downstream_unlocks):
            require(value is None or (is_wire_integer(value) and value >= 0),
                    'VISIT_RANK_NONNEGATIVE')
        require(self.stable_id is None or is_name(self.stable_id), 'VISIT_RANK_ID')


@dataclass(frozen=True)
class VisitRoleCount:
    role: str
    count: int

    def __post_init__(self):
        require(is_name(self.role), 'VISIT_ROLE')
        require(is_wire_integer(self.count) and self.count >= 0, 'VISIT_ROLE_COUNT')


@dataclass(frozen=True)
class RetentionStageTiming:
    subject: str
    role: str
    wall_seconds: float

    def __post_init__(self):
        require(is_name(self.subject) and is_name(self.role), 'RETENTION_TIMING_ID')
        require(type(self.wall_seconds) in (int, float)
                and math.isfinite(self.wall_seconds) and self.wall_seconds >= 0,
                'RETENTION_TIMING_SECONDS')


@dataclass(frozen=True)
class VisitEvidence:
    state: str
    grade_id: str | None
    grade_definition_id: str | None
    grade_definition_version: str | None
    capability_id: str | None
    semantic_ids: tuple[str, ...]
    prerequisites: tuple[str, ...]
    semantic_prerequisites: tuple[str, ...]
    constituents: tuple[str, ...]
    lawful_frontier_sha256: str | None
    a09_snapshot_sha256: str | None
    a09_closure_sha256: str | None
    ranking: VisitRankingEvidence
    teacher_visit_id: str | None
    teacher_policy_key: str | None
    selected_option_id: str | None
    lesson_roles: tuple[VisitRoleCount, ...]
    target: VisitCapabilityScore
    affected_scope_state: str
    affected: tuple[VisitCapabilityScore, ...]
    protected_scope_state: str
    protected: tuple[VisitCapabilityScore, ...]
    retention_economics_state: str
    retention_policy_sha256: str | None
    threshold_refs: tuple[str, ...]
    budget_refs: tuple[str, ...]
    probe_each: int | None
    baseline_measured_capabilities: tuple[str, ...]
    baseline_unmeasured_capabilities: tuple[str, ...]
    baseline_epoch_sha256: str | None
    decision: str | None
    blocking_capability: str | None
    blocking_scope: str | None
    reason: str | None
    human_reason: str | None
    candidate_evidence_sha256: str | None
    candidate_evidence_file: str | None

    def __post_init__(self):
        from .model import is_sha256, is_names
        require(self.state in {'PARTIAL', 'COMPLETE'}, 'VISIT_EVIDENCE_STATE')
        for value in (self.grade_id, self.grade_definition_id,
                      self.grade_definition_version, self.capability_id,
                      self.teacher_visit_id, self.teacher_policy_key,
                      self.selected_option_id, self.decision,
                      self.blocking_capability, self.blocking_scope,
                      self.reason, self.human_reason, self.candidate_evidence_file):
            require(value is None or is_name(value), 'VISIT_EVIDENCE_NAME')
        for values in (self.semantic_ids, self.prerequisites,
                       self.semantic_prerequisites, self.constituents,
                       self.baseline_measured_capabilities,
                       self.baseline_unmeasured_capabilities):
            require(is_names(values), 'VISIT_EVIDENCE_NAMES')
        for value in (self.lawful_frontier_sha256, self.a09_snapshot_sha256,
                      self.a09_closure_sha256, self.retention_policy_sha256,
                      self.baseline_epoch_sha256, self.candidate_evidence_sha256):
            require(value is None or is_sha256(value), 'VISIT_EVIDENCE_DIGEST')
        require(type(self.ranking) is VisitRankingEvidence, 'VISIT_EVIDENCE_RANKING')
        require(type(self.target) is VisitCapabilityScore, 'VISIT_EVIDENCE_TARGET')
        for state in (self.affected_scope_state, self.protected_scope_state,
                      self.retention_economics_state):
            require(state in {'MEASURED', 'PARTIAL', 'UNKNOWN'},
                    'VISIT_EVIDENCE_SCOPE_STATE')
        require(all(type(item) is VisitCapabilityScore for item in self.affected),
                'VISIT_EVIDENCE_AFFECTED')
        require(all(type(item) is VisitCapabilityScore for item in self.protected),
                'VISIT_EVIDENCE_PROTECTED')
        require(all(type(item) is VisitRoleCount for item in self.lesson_roles),
                'VISIT_EVIDENCE_ROLES')
        require(is_names(self.threshold_refs) and is_names(self.budget_refs),
                'VISIT_EVIDENCE_POLICY_REFS')
        require(self.probe_each is None or (
            is_wire_integer(self.probe_each) and self.probe_each >= 0),
            'VISIT_EVIDENCE_PROBE')


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
