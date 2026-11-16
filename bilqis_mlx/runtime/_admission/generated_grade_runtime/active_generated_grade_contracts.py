"""Immutable #1314 active generated-grade authority contracts."""
from __future__ import annotations

from dataclasses import dataclass, field

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade.definition import (
    GeneratedGradeDefinition,
    GeneratedGradeMember,
)
from bilqis_mlx.runtime.state import _fingerprint


ACTIVE_GRADE_SCHEMA = "bilqis.bamf.active-generated-grade/v1"
ACTIVE_GRADE_POINTER_SCHEMA = "bilqis.bamf.active-generated-grade-pointer/v1"
_ISSUER = object()


def _fail(reason: str):
    ErrorBus.raise_(
        SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
        reason=reason,
    )


def _sha(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def definition_record(definition: GeneratedGradeDefinition) -> dict:
    definition.verify()
    return {
        "schema": definition.schema,
        "adopted_release_sha256": definition.adopted_release_sha256,
        "release_lineage_sha256s": list(definition.release_lineage_sha256s),
        "release_verification_sha256": definition.release_verification_sha256,
        "proposal_sha256": definition.proposal_sha256,
        "learner_foot_sha256": definition.learner_foot_sha256,
        "learner_evidence_epoch": definition.learner_evidence_epoch,
        "policy_epoch": definition.policy_epoch,
        "policy_sha256": definition.policy_sha256,
        "members": [
            {
                "semantic_id": item.semantic_id,
                "capability_id": item.capability_id,
                "source_anchor": item.source_anchor,
                "family_ids": list(item.family_ids),
                "proposal_disposition": item.proposal_disposition,
                "reason_codes": list(item.reason_codes),
            }
            for item in definition.members
        ],
        "definition_sha256": definition.definition_sha256,
    }


def definition_from_record(record: dict) -> GeneratedGradeDefinition:
    try:
        definition = GeneratedGradeDefinition(
            adopted_release_sha256=record["adopted_release_sha256"],
            release_lineage_sha256s=tuple(record["release_lineage_sha256s"]),
            release_verification_sha256=record["release_verification_sha256"],
            proposal_sha256=record["proposal_sha256"],
            learner_foot_sha256=record["learner_foot_sha256"],
            learner_evidence_epoch=record["learner_evidence_epoch"],
            policy_epoch=record["policy_epoch"],
            policy_sha256=record["policy_sha256"],
            members=tuple(
                GeneratedGradeMember(
                    semantic_id=item["semantic_id"],
                    capability_id=item["capability_id"],
                    source_anchor=item["source_anchor"],
                    family_ids=tuple(item["family_ids"]),
                    proposal_disposition=item["proposal_disposition"],
                    reason_codes=tuple(item["reason_codes"]),
                )
                for item in record["members"]
            ),
            definition_sha256=record["definition_sha256"],
            schema=record["schema"],
        )
    except (KeyError, TypeError, ValueError):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_DEFINITION_INVALID")
    definition.verify()
    if definition_record(definition) != record:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_DEFINITION_INVALID")
    return definition


@dataclass(frozen=True, init=False)
class ActiveGeneratedGrade:
    run_id: str
    activation_generation: int
    activation_manifest_sha256: str
    activation_acceptance_sha256: str
    generated_grade_id: str
    definition: GeneratedGradeDefinition
    proposal_sha256: str
    a09_snapshot_sha256: str
    a09_closure_sha256: str
    a09_proposal_sha256: str | None
    predecessor_activation_sha256: str | None
    predecessor_definition_sha256: str | None
    transition_kind: str
    transition_receipt_sha256: str | None
    transition_reason: str | None
    activation_sha256: str
    schema: str = ACTIVE_GRADE_SCHEMA
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CALLER_CONSTRUCTION_FORBIDDEN")

    @property
    def member_capability_ids(self) -> tuple[str, ...]:
        return tuple(item.capability_id for item in self.definition.members)

    @property
    def member_semantic_ids(self) -> tuple[str, ...]:
        return self.definition.member_semantic_ids

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "activation_generation": self.activation_generation,
            "activation_manifest_sha256": self.activation_manifest_sha256,
            "activation_acceptance_sha256": self.activation_acceptance_sha256,
            "generated_grade_id": self.generated_grade_id,
            "definition_sha256": self.definition.definition_sha256,
            "proposal_sha256": self.proposal_sha256,
            "a09_snapshot_sha256": self.a09_snapshot_sha256,
            "a09_closure_sha256": self.a09_closure_sha256,
            "a09_proposal_sha256": self.a09_proposal_sha256,
            "predecessor_activation_sha256":
                self.predecessor_activation_sha256,
            "predecessor_definition_sha256":
                self.predecessor_definition_sha256,
            "transition_kind": self.transition_kind,
            "transition_receipt_sha256": self.transition_receipt_sha256,
            "transition_reason": self.transition_reason,
            "activation_sha256": self.activation_sha256,
        }

    def expected_digest(self) -> str:
        record = self.to_record()
        record["activation_sha256"] = "0" * 64
        return _fingerprint(record)

    def verify(self) -> None:
        self.definition.verify()
        initial = self.transition_kind == "INITIAL"
        successor = self.transition_kind in {"CORRECTION", "CERTIFICATION"}
        if (
            self.schema != ACTIVE_GRADE_SCHEMA
            or not self.run_id
            or type(self.activation_generation) is not int
            or self.activation_generation < 0
            or not all(_sha(value) for value in (
                self.activation_manifest_sha256,
                self.activation_acceptance_sha256,
                self.generated_grade_id,
                self.proposal_sha256,
                self.a09_snapshot_sha256,
                self.a09_closure_sha256,
                self.activation_sha256,
            ))
            or (self.a09_proposal_sha256 is not None
                and not _sha(self.a09_proposal_sha256))
            or self.generated_grade_id != self.definition.definition_sha256
            or self.proposal_sha256 != self.definition.proposal_sha256
            or initial == successor
            or (initial and any(value is not None for value in (
                self.predecessor_activation_sha256,
                self.predecessor_definition_sha256,
                self.transition_receipt_sha256,
                self.transition_reason,
            )))
            or (successor and (
                not _sha(self.predecessor_activation_sha256)
                or not _sha(self.predecessor_definition_sha256)
                or not _sha(self.transition_receipt_sha256)
                or not self.transition_reason
            ))
            or self.activation_sha256 != self.expected_digest()
        ):
            _fail("BAMF_ACTIVE_GENERATED_GRADE_INVALID")


def issue_active_generated_grade(**values) -> ActiveGeneratedGrade:
    active = object.__new__(ActiveGeneratedGrade)
    for name, value in values.items():
        object.__setattr__(active, name, value)
    object.__setattr__(active, "schema", ACTIVE_GRADE_SCHEMA)
    object.__setattr__(active, "_issuance", _ISSUER)
    object.__setattr__(active, "activation_sha256", "0" * 64)
    object.__setattr__(
        active, "activation_sha256", active.expected_digest())
    active.verify()
    return active


def active_from_record(
    record: dict,
    definition: GeneratedGradeDefinition,
) -> ActiveGeneratedGrade:
    if not isinstance(record, dict):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_RECORD_INVALID")
    expected = {
        "schema", "run_id", "activation_generation",
        "activation_manifest_sha256", "activation_acceptance_sha256",
        "generated_grade_id", "definition_sha256", "proposal_sha256",
        "a09_snapshot_sha256", "a09_closure_sha256", "a09_proposal_sha256",
        "predecessor_activation_sha256", "predecessor_definition_sha256",
        "transition_kind", "transition_receipt_sha256", "transition_reason",
        "activation_sha256",
    }
    if set(record) != expected or record.get(
            "definition_sha256") != definition.definition_sha256:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_RECORD_INVALID")
    active = issue_active_generated_grade(
        **{key: record[key] for key in expected - {
            "schema", "definition_sha256", "activation_sha256"}},
        definition=definition,
    )
    if active.activation_sha256 != record["activation_sha256"]:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_RECORD_INVALID")
    return active
