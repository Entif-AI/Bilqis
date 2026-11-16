"""Generation-bound local protection authority for ordinary C05 retention."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from bilqis_mlx.semantics.domains import contract_digest

from ..capability_evaluation import _invalid, _sha


PLAN_SCHEMA = "bilqis.mlx.c05-retention-protection-plan/v1"
TARGET_SCHEMA = "bilqis.mlx.c05-retention-target-plan/v1"
EDGE_SCHEMA = "bilqis.mlx.c05-retention-protection-edge/v1"


class ProtectionReason(str, Enum):
    PREREQUISITE = "PREREQUISITE"
    CONSTITUENT = "CONSTITUENT"
    DEPENDENT = "DEPENDENT"
    SHARED_CONSTITUENT = "SHARED_CONSTITUENT"


class BroadCertificationTrigger(str, Enum):
    GRADE_BOUNDARY = "GRADE_BOUNDARY"
    MATERIAL_PROTECTION_CHANGE = "MATERIAL_PROTECTION_CHANGE"
    CONFIGURED_INTERVAL = "CONFIGURED_INTERVAL"
    DECLARED_BROAD_BLAST_RADIUS = "DECLARED_BROAD_BLAST_RADIUS"
    COLD_REVIEW = "COLD_REVIEW"


@dataclass(frozen=True)
class ProtectionEdge:
    capability_id: str
    reason: ProtectionReason
    via_capability_id: str
    schema: str = EDGE_SCHEMA

    def __post_init__(self):
        if (not all(isinstance(value, str) and value for value in (
                self.capability_id, self.via_capability_id))
                or not isinstance(self.reason, ProtectionReason)
                or self.schema != EDGE_SCHEMA):
            _invalid("BAMF_C05_RETENTION_PROTECTION_EDGE_INVALID")

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "capability_id": self.capability_id,
            "reason": self.reason.value,
            "via_capability_id": self.via_capability_id,
        }

    @classmethod
    def from_record(cls, record):
        if not isinstance(record, dict) or set(record) != {
                "schema", "capability_id", "reason", "via_capability_id"}:
            _invalid("BAMF_C05_RETENTION_PROTECTION_EDGE_INVALID")
        try:
            reason = ProtectionReason(record["reason"])
        except (TypeError, ValueError):
            _invalid("BAMF_C05_RETENTION_PROTECTION_EDGE_INVALID")
            raise AssertionError
        return cls(
            record["capability_id"], reason, record["via_capability_id"],
            record["schema"])


@dataclass(frozen=True)
class RetentionTargetPlan:
    target_capability_id: str
    target_grade_id: str
    affected_edges: tuple[ProtectionEdge, ...]
    protected_capability_ids: tuple[str, ...]
    evaluated_capability_groups: tuple[tuple[str, str], ...]
    evaluation_scope_sha256: str
    comparison_scope_sha256: str
    schema: str = TARGET_SCHEMA

    def __post_init__(self):
        evaluated = tuple(capability for capability, _grade
                          in self.evaluated_capability_groups)
        if (not isinstance(self.target_capability_id, str)
                or not self.target_capability_id
                or not isinstance(self.target_grade_id, str) or not self.target_grade_id
                or not isinstance(self.affected_edges, tuple)
                or any(type(item) is not ProtectionEdge for item in self.affected_edges)
                or not isinstance(self.protected_capability_ids, tuple)
                or any(not isinstance(item, str) or not item
                       for item in self.protected_capability_ids)
                or len(set(self.protected_capability_ids))
                != len(self.protected_capability_ids)
                or self.target_capability_id in self.protected_capability_ids
                or not isinstance(self.evaluated_capability_groups, tuple)
                or evaluated != (
                    self.target_capability_id, *self.protected_capability_ids)
                or len(set(evaluated)) != len(evaluated)
                or any(not isinstance(group, str) or not group
                       for _capability, group in self.evaluated_capability_groups)
                or not _sha(self.evaluation_scope_sha256)
                or not _sha(self.comparison_scope_sha256)
                or self.schema != TARGET_SCHEMA):
            _invalid("BAMF_C05_RETENTION_TARGET_PLAN_INVALID")

    @property
    def evaluated_capability_ids(self) -> tuple[str, ...]:
        return tuple(capability for capability, _grade
                     in self.evaluated_capability_groups)

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "target_capability_id": self.target_capability_id,
            "target_grade_id": self.target_grade_id,
            "affected_edges": [item.to_record() for item in self.affected_edges],
            "protected_capability_ids": list(self.protected_capability_ids),
            "evaluated_capability_groups": [
                list(item) for item in self.evaluated_capability_groups],
            "evaluation_scope_sha256": self.evaluation_scope_sha256,
            "comparison_scope_sha256": self.comparison_scope_sha256,
        }

    @classmethod
    def from_record(cls, record):
        if not isinstance(record, dict) or set(record) != {
                "schema", "target_capability_id", "target_grade_id",
                "affected_edges", "protected_capability_ids",
                "evaluated_capability_groups", "evaluation_scope_sha256",
                "comparison_scope_sha256"}:
            _invalid("BAMF_C05_RETENTION_TARGET_PLAN_INVALID")
        return cls(
            record["target_capability_id"],
            record["target_grade_id"],
            tuple(ProtectionEdge.from_record(item)
                  for item in record["affected_edges"]),
            tuple(record["protected_capability_ids"]),
            tuple(tuple(item) for item in record["evaluated_capability_groups"]),
            record["evaluation_scope_sha256"],
            record["comparison_scope_sha256"],
            record["schema"],
        )


@dataclass(frozen=True)
class RetentionProtectionPlan:
    factory_release_sha256: str
    execution_plan_sha256: str
    grade_definition_sha256: str
    retained_evidence_sha256: str
    policy_epoch_sha256: str
    rubric_sha256: str
    source_sha256: str
    accepted_generation: int
    accepted_manifest_sha256: str
    evidence_stage: str
    established_capability_ids: tuple[str, ...]
    targets: tuple[RetentionTargetPlan, ...]
    schema: str = PLAN_SCHEMA
    _by_target: dict[str, RetentionTargetPlan] = field(
        init=False, repr=False, compare=False)

    def __post_init__(self):
        digests = (
            self.factory_release_sha256, self.execution_plan_sha256,
            self.grade_definition_sha256, self.retained_evidence_sha256,
            self.policy_epoch_sha256, self.rubric_sha256, self.source_sha256,
            self.accepted_manifest_sha256,
        )
        target_ids = tuple(item.target_capability_id for item in self.targets)
        if (any(not _sha(value) for value in digests)
                or type(self.accepted_generation) is not int
                or self.accepted_generation < 0
                or not isinstance(self.evidence_stage, str) or not self.evidence_stage
                or not isinstance(self.established_capability_ids, tuple)
                or any(not isinstance(item, str) or not item
                       for item in self.established_capability_ids)
                or len(set(self.established_capability_ids))
                != len(self.established_capability_ids)
                or not isinstance(self.targets, tuple) or not self.targets
                or any(type(item) is not RetentionTargetPlan for item in self.targets)
                or len(set(target_ids)) != len(target_ids)
                or self.schema != PLAN_SCHEMA):
            _invalid("BAMF_C05_RETENTION_PROTECTION_PLAN_INVALID")
        object.__setattr__(
            self, "_by_target", {item.target_capability_id: item
                                for item in self.targets})

    @property
    def digest(self) -> str:
        return contract_digest(self._payload_record())

    def for_target(self, capability_id: str) -> RetentionTargetPlan:
        item = self._by_target.get(capability_id)
        if item is None:
            _invalid("BAMF_C05_TARGET_CAPABILITY_NOT_ADMITTED")
        return item

    def _payload_record(self) -> dict:
        return {
            "schema": self.schema,
            "factory_release_sha256": self.factory_release_sha256,
            "execution_plan_sha256": self.execution_plan_sha256,
            "grade_definition_sha256": self.grade_definition_sha256,
            "retained_evidence_sha256": self.retained_evidence_sha256,
            "policy_epoch_sha256": self.policy_epoch_sha256,
            "rubric_sha256": self.rubric_sha256,
            "source_sha256": self.source_sha256,
            "accepted_generation": self.accepted_generation,
            "accepted_manifest_sha256": self.accepted_manifest_sha256,
            "evidence_stage": self.evidence_stage,
            "established_capability_ids": list(self.established_capability_ids),
            "targets": [item.to_record() for item in self.targets],
        }

    def to_record(self) -> dict:
        return {**self._payload_record(), "plan_sha256": self.digest}

    @classmethod
    def from_record(cls, record):
        if not isinstance(record, dict) or set(record) != {
                "schema", "factory_release_sha256", "execution_plan_sha256",
                "grade_definition_sha256", "retained_evidence_sha256",
                "policy_epoch_sha256", "rubric_sha256", "source_sha256",
                "accepted_generation", "accepted_manifest_sha256",
                "evidence_stage", "established_capability_ids", "targets",
                "plan_sha256"}:
            _invalid("BAMF_C05_RETENTION_PROTECTION_PLAN_INVALID")
        item = cls(
            record["factory_release_sha256"],
            record["execution_plan_sha256"],
            record["grade_definition_sha256"],
            record["retained_evidence_sha256"],
            record["policy_epoch_sha256"],
            record["rubric_sha256"],
            record["source_sha256"],
            record["accepted_generation"],
            record["accepted_manifest_sha256"],
            record["evidence_stage"],
            tuple(record["established_capability_ids"]),
            tuple(RetentionTargetPlan.from_record(value)
                  for value in record["targets"]),
            record["schema"],
        )
        if item.digest != record["plan_sha256"]:
            _invalid("BAMF_C05_RETENTION_PROTECTION_PLAN_DRIFT")
        return item


__all__ = (
    "BroadCertificationTrigger", "ProtectionReason", "RetentionProtectionPlan",
    "RetentionTargetPlan",
)
