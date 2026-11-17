"""Typed, versioned records for #1331 plasticity state."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..capability_evaluation import _invalid, _sha

ORDINARY_STARVATION_ATTEMPTS = 32
FRONTIER_STARVATION_ATTEMPTS = 16
SCHOOL_DROUGHT_ATTEMPTS = 24
REPAIR_THRESHOLD = 2
HARD_DEBT_LIMIT = 4
RELEASE_THRESHOLD = 1
STATE_SCHEMA = "bilqis.c05.plasticity-escape-state/v1"
SURFACE_SCHEMA = "bilqis.c05.certified-surface-id/v1"


class PlasticityActivationReason(str, Enum):
    LOCAL_STARVATION = "LOCAL_STARVATION"
    SCHOOL_RETENTION_DROUGHT_BELOW_MEAN = "SCHOOL_RETENTION_DROUGHT_BELOW_MEAN"


@dataclass(frozen=True)
class CertifiedSurfaceId:
    """Exact certified competence identity; never curriculum authority."""

    surface_id: str
    capability_id: str
    grade_definition_sha256: str
    factory_release_sha256: str
    rubric_sha256: str
    policy_epoch_sha256: str
    source_sha256: str
    fixed_cohort_sha256: str
    schema: str = SURFACE_SCHEMA

    def __post_init__(self):
        digests = (
            self.grade_definition_sha256, self.factory_release_sha256,
            self.rubric_sha256, self.policy_epoch_sha256,
            self.source_sha256, self.fixed_cohort_sha256)
        if (not isinstance(self.surface_id, str) or not self.surface_id
                or not isinstance(self.capability_id, str) or not self.capability_id
                or any(not _sha(value) for value in digests)
                or self.schema != SURFACE_SCHEMA):
            _invalid("BAMF_PLASTICITY_CERTIFIED_SURFACE_ID_INVALID")

    def to_record(self) -> dict:
        return {
            "schema": self.schema, "surface_id": self.surface_id,
            "capability_id": self.capability_id,
            "grade_definition_sha256": self.grade_definition_sha256,
            "factory_release_sha256": self.factory_release_sha256,
            "rubric_sha256": self.rubric_sha256,
            "policy_epoch_sha256": self.policy_epoch_sha256,
            "source_sha256": self.source_sha256,
            "fixed_cohort_sha256": self.fixed_cohort_sha256,
        }

    @classmethod
    def from_record(cls, record) -> "CertifiedSurfaceId":
        if not isinstance(record, dict):
            _invalid("BAMF_PLASTICITY_CERTIFIED_SURFACE_ID_INVALID")
        return cls(
            record.get("surface_id"), record.get("capability_id"),
            record.get("grade_definition_sha256"), record.get("factory_release_sha256"),
            record.get("rubric_sha256"), record.get("policy_epoch_sha256"),
            record.get("source_sha256"), record.get("fixed_cohort_sha256"),
            record.get("schema"))

    @classmethod
    def from_certified_surface(cls, surface):
        if not isinstance(surface, dict):
            return None
        required = (
            "surface_id", "capability_id", "grade_definition_sha256",
            "factory_release_sha256", "rubric_sha256", "policy_epoch_sha256",
            "source_sha256", "fixed_cohort_sha256")
        if any(surface.get(name) is None for name in required):
            return None
        return cls(
            surface["surface_id"], surface["capability_id"],
            surface["grade_definition_sha256"], surface["factory_release_sha256"],
            surface["rubric_sha256"], surface["policy_epoch_sha256"],
            surface["source_sha256"], surface["fixed_cohort_sha256"])


@dataclass(frozen=True)
class CertifiedSurfaceDebt:
    surface: CertifiedSurfaceId
    amount: int
    certified_correct: int
    total: int

    def __post_init__(self):
        if (type(self.surface) is not CertifiedSurfaceId
                or type(self.amount) is not int or self.amount < 0
                or type(self.certified_correct) is not int
                or type(self.total) is not int or self.total <= 0
                or not 0 <= self.certified_correct <= self.total):
            _invalid("BAMF_PLASTICITY_CERTIFIED_SURFACE_DEBT_INVALID")

    def to_record(self) -> dict:
        return {
            "surface": self.surface.to_record(), "amount": self.amount,
            "certified_correct": self.certified_correct, "total": self.total}

    @classmethod
    def from_record(cls, record) -> "CertifiedSurfaceDebt":
        if not isinstance(record, dict):
            _invalid("BAMF_PLASTICITY_CERTIFIED_SURFACE_DEBT_INVALID")
        return cls(
            CertifiedSurfaceId.from_record(record.get("surface")),
            record.get("amount"), record.get("certified_correct"), record.get("total"))


@dataclass(frozen=True)
class PlasticityEscapeState:
    policy_epoch_sha256: str
    target_capability_id: str
    active: bool
    activation_reasons: tuple[PlasticityActivationReason, ...] = ()
    attempts_since_retained: int = 0
    school_attempts_since_retained: int = 0
    debt: tuple[CertifiedSurfaceDebt, ...] = ()
    unqualified_debt_capability_ids: tuple[str, ...] = ()
    last_repair_opportunity: int | None = None
    deactivated: bool = False
    schema: str = STATE_SCHEMA

    def __post_init__(self):
        invalid = (
            not _sha(self.policy_epoch_sha256)
            or not isinstance(self.target_capability_id, str) or not self.target_capability_id
            or type(self.active) is not bool
            or not isinstance(self.activation_reasons, tuple)
            or any(not isinstance(item, PlasticityActivationReason)
                   for item in self.activation_reasons)
            or len(set(self.activation_reasons)) != len(self.activation_reasons)
            or (self.active and not self.activation_reasons)
            or type(self.attempts_since_retained) is not int
            or self.attempts_since_retained < 0
            or type(self.school_attempts_since_retained) is not int
            or self.school_attempts_since_retained < 0
            or not isinstance(self.debt, tuple)
            or any(type(item) is not CertifiedSurfaceDebt for item in self.debt)
            or len({item.surface for item in self.debt}) != len(self.debt)
            or not isinstance(self.unqualified_debt_capability_ids, tuple)
            or any(not isinstance(item, str) or not item
                   for item in self.unqualified_debt_capability_ids)
            or len(set(self.unqualified_debt_capability_ids))
            != len(self.unqualified_debt_capability_ids)
            or (self.last_repair_opportunity is not None
                and (type(self.last_repair_opportunity) is not int
                     or self.last_repair_opportunity < 0))
            or type(self.deactivated) is not bool
            or (self.active and self.deactivated)
            or self.schema != STATE_SCHEMA)
        if invalid:
            _invalid("BAMF_PLASTICITY_ESCAPE_STATE_INVALID")

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "policy_epoch_sha256": self.policy_epoch_sha256,
            "target_capability_id": self.target_capability_id,
            "active": self.active,
            "activation_reasons": [reason.value for reason in self.activation_reasons],
            "attempts_since_retained": self.attempts_since_retained,
            "school_attempts_since_retained": self.school_attempts_since_retained,
            "debt": [item.to_record() for item in self.debt],
            "unqualified_debt_capability_ids": list(
                self.unqualified_debt_capability_ids),
            "last_repair_opportunity": self.last_repair_opportunity,
            "deactivated": self.deactivated,
        }

    @classmethod
    def from_record(cls, record) -> "PlasticityEscapeState":
        if not isinstance(record, dict):
            _invalid("BAMF_PLASTICITY_ESCAPE_STATE_INVALID")
        try:
            reasons = tuple(PlasticityActivationReason(item)
                            for item in record.get("activation_reasons", ()))
        except (TypeError, ValueError):
            _invalid("BAMF_PLASTICITY_ESCAPE_STATE_INVALID")
        return cls(
            record.get("policy_epoch_sha256"), record.get("target_capability_id"),
            record.get("active"), reasons, record.get("attempts_since_retained", 0),
            record.get("school_attempts_since_retained", 0),
            tuple(CertifiedSurfaceDebt.from_record(item)
                  for item in record.get("debt", ())),
            tuple(record.get("unqualified_debt_capability_ids", ())),
            record.get("last_repair_opportunity"), record.get("deactivated", False),
            record.get("schema"))
