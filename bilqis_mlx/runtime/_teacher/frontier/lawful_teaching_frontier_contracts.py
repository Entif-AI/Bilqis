"""Immutable contracts for the learner-relative lawful teaching frontier."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

from bilqis_mlx.errors import ErrorBus, SCHOOL


FRONTIER_SCHEMA = "bilqis.bamf.learner-teaching-frontier/v1"
_ISSUER = object()


class LawfulTeachingDisposition(str, Enum):
    READY = "READY"
    EVIDENCE_COMPLETE = "EVIDENCE_COMPLETE"
    HELD_PREREQUISITE_EVIDENCE = "HELD_PREREQUISITE_EVIDENCE"
    HELD_SOURCE_RIGHTS = "HELD_SOURCE_RIGHTS"
    IMPLEMENTATION_UNCOVERED = "IMPLEMENTATION_UNCOVERED"


class LawfulTeachingExclusionCode(str, Enum):
    FUTURE_GENERATED_GRADE = "FUTURE_GENERATED_GRADE"
    PREREQUISITE_HELD = "PREREQUISITE_HELD"
    SOURCE_HELD = "SOURCE_HELD"
    IMPLEMENTATION_UNCOVERED = "IMPLEMENTATION_UNCOVERED"
    ALREADY_COMPLETE = "ALREADY_COMPLETE"


class ActiveGeneratedGradeState(str, Enum):
    INCOMPLETE_READY = "INCOMPLETE_READY"
    INCOMPLETE_HELD = "INCOMPLETE_HELD"
    COMPLETE = "COMPLETE"
    GLOBAL_FIXED_POINT = "GLOBAL_FIXED_POINT"


@dataclass(frozen=True, order=True)
class LawfulTeachingHold:
    code: str
    owner: str
    dependency_id: str = ""


@dataclass(frozen=True, order=True)
class LawfulTeachingCapability:
    capability_id: str
    semantic_ids: tuple[str, ...]
    admitted_release_sha256: str
    source_binding_sha256: str
    prerequisites: tuple[str, ...]
    constituents: tuple[str, ...]
    semantic_prerequisites: tuple[str, ...]
    evidence_complete_prerequisites: tuple[str, ...]
    evidence_complete_constituents: tuple[str, ...]
    target_evidence_complete: bool
    disposition: LawfulTeachingDisposition
    holds: tuple[LawfulTeachingHold, ...]

    def to_record(self) -> dict:
        return {
            "capability_id": self.capability_id,
            "semantic_ids": list(self.semantic_ids),
            "admitted_release_sha256": self.admitted_release_sha256,
            "source_binding_sha256": self.source_binding_sha256,
            "prerequisites": list(self.prerequisites),
            "constituents": list(self.constituents),
            "semantic_prerequisites": list(self.semantic_prerequisites),
            "evidence_complete_prerequisites": list(
                self.evidence_complete_prerequisites),
            "evidence_complete_constituents": list(
                self.evidence_complete_constituents),
            "target_evidence_complete": self.target_evidence_complete,
            "disposition": self.disposition.value,
            "holds": [
                {
                    "code": item.code,
                    "owner": item.owner,
                    "dependency_id": item.dependency_id,
                }
                for item in self.holds
            ],
        }


@dataclass(frozen=True, order=True)
class LawfulTeachingExclusion:
    capability_id: str
    semantic_ids: tuple[str, ...]
    code: LawfulTeachingExclusionCode
    holds: tuple[LawfulTeachingHold, ...]

    def to_record(self) -> dict:
        return {
            "capability_id": self.capability_id,
            "semantic_ids": list(self.semantic_ids),
            "code": self.code.value,
            "holds": [
                {
                    "code": item.code,
                    "owner": item.owner,
                    "dependency_id": item.dependency_id,
                }
                for item in self.holds
            ],
        }


@dataclass(frozen=True, init=False, eq=False)
class LawfulTeachingFrontier:
    run_id: str
    accepted_generation: int
    accepted_manifest_sha256: str
    accepted_correction_frontier_sha256: str
    accepted_checkpoint_sha256: str
    accepted_optimizer_step: int
    candidate_identity_sha256: str
    admitted_release_sha256: str
    admission_receipt_sha256: str
    a09_snapshot_sha256: str
    a09_closure_sha256: str
    prerequisite_evidence_sha256: str
    autonomy_plan_sha256: str
    autonomy_evidence_sha256: str
    rights_epoch: int
    correction_generation: int
    policy_epoch: int
    source_authority_registry_sha256: str
    active_grade_activation_sha256: str
    active_grade_definition_sha256: str
    active_grade_members: tuple[tuple[str, str], ...]
    active_grade_state: ActiveGeneratedGradeState
    capabilities: tuple[LawfulTeachingCapability, ...]
    exclusions: tuple[LawfulTeachingExclusion, ...]
    frontier_sha256: str
    schema: str = FRONTIER_SCHEMA
    _source_context: object = field(repr=False, compare=False)
    _parent: object = field(repr=False, compare=False)
    _planning_generation: object = field(repr=False, compare=False)
    _autonomy_currentness: object = field(repr=False, compare=False)
    _active_grade_currentness: object = field(repr=False, compare=False)
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        ErrorBus.Raise(
            SCHOOL.MODEL_TOPOLOGY.INVALID,
            reason="BAMF_LEARNER_FRONTIER_CALLER_CONSTRUCTION_FORBIDDEN",
        )

    @property
    def ready_capability_ids(self) -> tuple[str, ...]:
        return tuple(
            item.capability_id for item in self.capabilities
            if item.disposition is LawfulTeachingDisposition.READY)

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "accepted_generation": self.accepted_generation,
            "accepted_manifest_sha256": self.accepted_manifest_sha256,
            "accepted_correction_frontier_sha256":
                self.accepted_correction_frontier_sha256,
            "accepted_checkpoint_sha256": self.accepted_checkpoint_sha256,
            "accepted_optimizer_step": self.accepted_optimizer_step,
            "candidate_identity_sha256": self.candidate_identity_sha256,
            "admitted_release_sha256": self.admitted_release_sha256,
            "admission_receipt_sha256": self.admission_receipt_sha256,
            "a09_snapshot_sha256": self.a09_snapshot_sha256,
            "a09_closure_sha256": self.a09_closure_sha256,
            "prerequisite_evidence_sha256": self.prerequisite_evidence_sha256,
            "autonomy_plan_sha256": self.autonomy_plan_sha256,
            "autonomy_evidence_sha256": self.autonomy_evidence_sha256,
            "rights_epoch": self.rights_epoch,
            "correction_generation": self.correction_generation,
            "policy_epoch": self.policy_epoch,
            "source_authority_registry_sha256":
                self.source_authority_registry_sha256,
            "active_grade_activation_sha256":
                self.active_grade_activation_sha256,
            "active_grade_definition_sha256":
                self.active_grade_definition_sha256,
            "active_grade_members": [
                [capability_id, semantic_id]
                for capability_id, semantic_id in self.active_grade_members
            ],
            "active_grade_state": self.active_grade_state.value,
            "capabilities": [item.to_record() for item in self.capabilities],
            "exclusions": [item.to_record() for item in self.exclusions],
            "frontier_sha256": self.frontier_sha256,
        }

    def expected_digest(self) -> str:
        record = self.to_record()
        record["frontier_sha256"] = "0" * 64
        payload = json.dumps(
            record, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False).encode()
        return hashlib.sha256(payload).hexdigest()


def _issue_frontier(**values) -> LawfulTeachingFrontier:
    frontier = object.__new__(LawfulTeachingFrontier)
    for name, value in values.items():
        object.__setattr__(frontier, name, value)
    object.__setattr__(frontier, "schema", FRONTIER_SCHEMA)
    object.__setattr__(frontier, "_issuance", _ISSUER)
    object.__setattr__(frontier, "frontier_sha256", "0" * 64)
    object.__setattr__(frontier, "frontier_sha256", frontier.expected_digest())
    return frontier


def _is_issued(frontier) -> bool:
    return (
        type(frontier) is LawfulTeachingFrontier
        and getattr(frontier, "_issuance", None) is _ISSUER
        and frontier.schema == FRONTIER_SCHEMA
        and frontier.frontier_sha256 == frontier.expected_digest()
    )
