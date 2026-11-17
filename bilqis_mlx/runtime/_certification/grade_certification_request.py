"""Certification family/attempt/request identity contracts."""
from __future__ import annotations

from dataclasses import dataclass, field

from .grade_certification_common import _digest, _invalid, _sha
from .grade_certification_policy import (
    CertificationObligationScore, GradeCertificationPolicy,
)

REQUEST_SCHEMA = "bilqis.bamf.grade-certification-request/v2"
FAMILY_SCHEMA = "bilqis.bamf.grade-certification-family/v2"
_REQUEST_ISSUER = object()

@dataclass(frozen=True, init=False)
class GradeCertificationRequest:
    run_id: str
    boundary_disposition: str
    boundary_sha256: str
    cadence_sha256: str
    cadence_epoch: int
    member_census_sha256: str
    deficit_evidence_sha256: str
    active_grade_activation_sha256: str
    active_grade_definition_sha256: str
    accepted_generation: int
    accepted_manifest_sha256: str
    accepted_acceptance_sha256: str
    learner_checkpoint_sha256: str
    optimizer_step: int
    learner_evidence_epoch: int
    factory_release_sha256: str
    assessment_capabilities: tuple[str, ...]
    assessment_rubric_sha256: str
    assessment_source_sha256: str
    assessment_generator_version: str
    semantic_catalog_sha256: str
    policy_epoch: int
    policy_sha256: str
    debt_authority: str | None
    active_obligations: tuple[str, ...]
    protected_obligations: tuple[str, ...]
    protected_baselines: tuple[CertificationObligationScore, ...]
    family_sha256: str
    attempt_sha256: str
    request_sha256: str
    schema: str = REQUEST_SCHEMA
    _issuance: object = field(repr=False, compare=False, default=None)

    def __init__(self, *args, **kwargs):
        _invalid("BAMF_GRADE_CERTIFICATION_REQUEST_CALLER_CONSTRUCTION_FORBIDDEN")

    def _base_record(self) -> dict:
        return {
            "schema": self.schema, "run_id": self.run_id,
            "boundary_disposition": self.boundary_disposition,
            "boundary_sha256": self.boundary_sha256,
            "cadence_sha256": self.cadence_sha256,
            "cadence_epoch": self.cadence_epoch,
            "member_census_sha256": self.member_census_sha256,
            "deficit_evidence_sha256": self.deficit_evidence_sha256,
            "active_grade_activation_sha256": self.active_grade_activation_sha256,
            "active_grade_definition_sha256": self.active_grade_definition_sha256,
            "accepted_generation": self.accepted_generation,
            "accepted_manifest_sha256": self.accepted_manifest_sha256,
            "accepted_acceptance_sha256": self.accepted_acceptance_sha256,
            "learner_checkpoint_sha256": self.learner_checkpoint_sha256,
            "optimizer_step": self.optimizer_step,
            "learner_evidence_epoch": self.learner_evidence_epoch,
            "factory_release_sha256": self.factory_release_sha256,
            "assessment_capabilities": list(self.assessment_capabilities),
            "assessment_rubric_sha256": self.assessment_rubric_sha256,
            "assessment_source_sha256": self.assessment_source_sha256,
            "assessment_generator_version": self.assessment_generator_version,
            "semantic_catalog_sha256": self.semantic_catalog_sha256,
            "policy_epoch": self.policy_epoch,
            "policy_sha256": self.policy_sha256,
            "debt_authority": self.debt_authority,
            "active_obligations": list(self.active_obligations),
            "protected_obligations": list(self.protected_obligations),
            "protected_baselines": [
                item.to_record() for item in self.protected_baselines],
        }

    def to_record(self) -> dict:
        return {
            **self._base_record(),
            "family_sha256": self.family_sha256,
            "attempt_sha256": self.attempt_sha256,
            "request_sha256": self.request_sha256,
        }

    def expected_family_digest(self) -> str:
        return _digest({
            "schema": FAMILY_SCHEMA,
            "boundary_disposition": self.boundary_disposition,
            "active_grade_activation_sha256": self.active_grade_activation_sha256,
            "active_grade_definition_sha256": self.active_grade_definition_sha256,
            "factory_release_sha256": self.factory_release_sha256,
            "member_census_sha256": self.member_census_sha256,
            "assessment_capabilities": list(self.assessment_capabilities),
            "assessment_rubric_sha256": self.assessment_rubric_sha256,
            "assessment_source_sha256": self.assessment_source_sha256,
            "assessment_generator_version": self.assessment_generator_version,
            "semantic_catalog_sha256": self.semantic_catalog_sha256,
            "policy_sha256": self.policy_sha256,
            "protected_obligations": list(self.protected_obligations),
            "protected_baselines": [
                item.to_record() for item in self.protected_baselines],
        })

    def expected_attempt_digest(self) -> str:
        return _digest({
            "schema": "bilqis.bamf.grade-certification-attempt/v1",
            "family_sha256": self.family_sha256,
            "boundary_sha256": self.boundary_sha256,
            "cadence_sha256": self.cadence_sha256,
            "cadence_epoch": self.cadence_epoch,
            "deficit_evidence_sha256": self.deficit_evidence_sha256,
            "accepted_generation": self.accepted_generation,
            "accepted_manifest_sha256": self.accepted_manifest_sha256,
            "accepted_acceptance_sha256": self.accepted_acceptance_sha256,
            "learner_checkpoint_sha256": self.learner_checkpoint_sha256,
            "optimizer_step": self.optimizer_step,
            "learner_evidence_epoch": self.learner_evidence_epoch,
        })

    def verify(self) -> None:
        digests = (
            self.boundary_sha256, self.cadence_sha256,
            self.member_census_sha256, self.deficit_evidence_sha256,
            self.active_grade_activation_sha256,
            self.active_grade_definition_sha256,
            self.accepted_manifest_sha256, self.accepted_acceptance_sha256,
            self.learner_checkpoint_sha256, self.factory_release_sha256,
            self.assessment_rubric_sha256, self.assessment_source_sha256,
            self.semantic_catalog_sha256, self.policy_sha256,
            self.family_sha256, self.attempt_sha256, self.request_sha256,
        )
        if (
            self.schema != REQUEST_SCHEMA or not self.run_id
            or self.boundary_disposition not in {
                "GRADE_COMPLETE", "RECOVERY_EXHAUSTED"}
            or any(not _sha(value) for value in digests)
            or type(self.cadence_epoch) is not int or self.cadence_epoch < 0
            or type(self.accepted_generation) is not int or self.accepted_generation < 0
            or type(self.optimizer_step) is not int or self.optimizer_step < 0
            or type(self.learner_evidence_epoch) is not int
            or self.learner_evidence_epoch < 0
            or type(self.policy_epoch) is not int or self.policy_epoch < 0
            or (self.debt_authority is not None and not self.debt_authority)
            or not self.assessment_capabilities
            or len(set(self.assessment_capabilities)) != len(self.assessment_capabilities)
            or set(self.assessment_capabilities) != set(
                (*self.active_obligations, *self.protected_obligations))
            or not self.assessment_generator_version
            or not self.active_obligations
            or len(set(self.active_obligations)) != len(self.active_obligations)
            or len(set(self.protected_obligations)) != len(self.protected_obligations)
            or type(self.protected_baselines) is not tuple
            or any(
                type(item) is not CertificationObligationScore
                or item.owner != "PROTECTED"
                for item in self.protected_baselines
            )
            or len({item.obligation_key for item in self.protected_baselines})
               != len(self.protected_baselines)
            or not {
                item.obligation_key for item in self.protected_baselines
            } <= set(self.protected_obligations)
            or tuple(
                item.obligation_key for item in self.protected_baselines
            ) != tuple(
                key for key in self.protected_obligations
                if key in {item.obligation_key for item in self.protected_baselines}
            )
            or self.family_sha256 != self.expected_family_digest()
            or self.attempt_sha256 != self.expected_attempt_digest()
            or self.request_sha256 != _digest({
                **self._base_record(),
                "family_sha256": self.family_sha256,
                "attempt_sha256": self.attempt_sha256,
            })
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_REQUEST_INVALID")


def _request_object(**values) -> GradeCertificationRequest:
    request = object.__new__(GradeCertificationRequest)
    for name, value in values.items():
        object.__setattr__(request, name, value)
    object.__setattr__(request, "_issuance", _REQUEST_ISSUER)
    return request


def _request_from_record(record: dict) -> GradeCertificationRequest:
    expected = {
        "schema", "run_id", "boundary_disposition", "boundary_sha256",
        "cadence_sha256", "cadence_epoch", "member_census_sha256",
        "deficit_evidence_sha256", "active_grade_activation_sha256",
        "active_grade_definition_sha256", "accepted_generation",
        "accepted_manifest_sha256", "accepted_acceptance_sha256",
        "learner_checkpoint_sha256", "optimizer_step",
        "learner_evidence_epoch", "factory_release_sha256",
        "assessment_capabilities", "assessment_rubric_sha256",
        "assessment_source_sha256", "assessment_generator_version",
        "semantic_catalog_sha256", "policy_epoch", "policy_sha256",
        "debt_authority", "active_obligations", "protected_obligations",
        "protected_baselines",
        "family_sha256", "attempt_sha256", "request_sha256",
    }
    if not isinstance(record, dict) or set(record) != expected:
        _invalid("BAMF_GRADE_CERTIFICATION_REQUEST_RECORD_INVALID")
    try:
        values = dict(record)
        values["assessment_capabilities"] = tuple(
            record["assessment_capabilities"])
        values["active_obligations"] = tuple(record["active_obligations"])
        values["protected_obligations"] = tuple(record["protected_obligations"])
        values["protected_baselines"] = tuple(
            CertificationObligationScore(**item)
            for item in record["protected_baselines"])
        request = object.__new__(GradeCertificationRequest)
        for name, value in values.items():
            object.__setattr__(request, name, value)
        object.__setattr__(request, "_issuance", None)
        request.verify()
        return request
    except (KeyError, TypeError, ValueError):
        _invalid("BAMF_GRADE_CERTIFICATION_REQUEST_RECORD_INVALID")


def _issue_certification_request(**values) -> GradeCertificationRequest:
    policy = values.pop("policy", None)
    if type(policy) is not GradeCertificationPolicy:
        _invalid("BAMF_GRADE_CERTIFICATION_POLICY_REQUIRED")
    policy.verify()
    common = {
        **values,
        "assessment_capabilities": tuple(values["assessment_capabilities"]),
        "active_obligations": tuple(values["active_obligations"]),
        "protected_obligations": tuple(values["protected_obligations"]),
        "protected_baselines": tuple(values["protected_baselines"]),
        "policy_epoch": policy.policy_epoch,
        "policy_sha256": policy.policy_sha256,
        "debt_authority": policy.debt_authority,
        "family_sha256": "0" * 64,
        "attempt_sha256": "0" * 64,
        "request_sha256": "0" * 64,
        "schema": REQUEST_SCHEMA,
    }
    draft = _request_object(**common)
    family = draft.expected_family_digest()
    draft = _request_object(**{
        **common, "family_sha256": family})
    attempt = draft.expected_attempt_digest()
    draft = _request_object(**{
        **common, "family_sha256": family, "attempt_sha256": attempt})
    request_sha = _digest({
        **draft._base_record(),
        "family_sha256": family,
        "attempt_sha256": attempt,
    })
    result = _request_object(**{
        **common, "family_sha256": family, "attempt_sha256": attempt,
        "request_sha256": request_sha})
    result.verify()
    return result
