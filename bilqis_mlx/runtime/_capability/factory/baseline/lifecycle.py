"""ADR-142 durable baseline lifecycle: no baseline, no regression."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from bilqis_mlx.semantics.domains import contract_digest

from ..capability_evaluation import _invalid, _sha


LEGACY_COMPARISON_SCHEMA = "bilqis.mlx.c05-baseline-comparison/v1"
COMPARISON_SCHEMA = "bilqis.mlx.c05-baseline-comparison/v2"
MEASUREMENT_SCHEMA = "bilqis.mlx.c05-baseline-measurement/v1"
LEDGER_SCHEMA = "bilqis.mlx.c05-baseline-ledger/v1"


class BaselineLifecycleState(str, Enum):
    UNMEASURED = "UNMEASURED"
    BASELINE_ESTABLISHED = "BASELINE_ESTABLISHED"
    COMPARABLE_HISTORY = "COMPARABLE_HISTORY"


@dataclass(frozen=True)
class BaselineComparisonIdentity:
    capability_id: str
    factory_release_sha256: str
    semantic_catalog_sha256: str
    rubric_sha256: str
    scope_sha256: str
    policy_sha256: str
    source_sha256: str
    source_authority_registry_sha256: str | None
    correction_frontier_sha256: str
    evaluation_contract_sha256: str
    fixed_cohort_sha256: str
    evidence_stage: str
    schema: str = COMPARISON_SCHEMA

    def __post_init__(self):
        digests = (
            self.factory_release_sha256, self.semantic_catalog_sha256,
            self.rubric_sha256, self.scope_sha256, self.policy_sha256,
            self.source_sha256, self.correction_frontier_sha256,
            self.evaluation_contract_sha256, self.fixed_cohort_sha256,
        )
        if (not isinstance(self.capability_id, str) or not self.capability_id
                or any(not _sha(value) for value in digests)
                or (self.source_authority_registry_sha256 is not None
                    and not _sha(self.source_authority_registry_sha256))
                or not isinstance(self.evidence_stage, str) or not self.evidence_stage
                or self.schema not in {LEGACY_COMPARISON_SCHEMA, COMPARISON_SCHEMA}):
            _invalid("BAMF_C05_BASELINE_COMPARISON_IDENTITY_INVALID")

    @property
    def digest(self) -> str:
        return contract_digest(self)

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "capability_id": self.capability_id,
            "factory_release_sha256": self.factory_release_sha256,
            "semantic_catalog_sha256": self.semantic_catalog_sha256,
            "rubric_sha256": self.rubric_sha256,
            "scope_sha256": self.scope_sha256,
            "policy_sha256": self.policy_sha256,
            "source_sha256": self.source_sha256,
            "source_authority_registry_sha256": self.source_authority_registry_sha256,
            "correction_frontier_sha256": self.correction_frontier_sha256,
            "evaluation_contract_sha256": self.evaluation_contract_sha256,
            "fixed_cohort_sha256": self.fixed_cohort_sha256,
            "evidence_stage": self.evidence_stage,
        }

    @classmethod
    def from_record(cls, record) -> "BaselineComparisonIdentity":
        if not isinstance(record, dict) or set(record) != {
            "schema", "capability_id", "factory_release_sha256",
            "semantic_catalog_sha256", "rubric_sha256", "scope_sha256",
            "policy_sha256", "source_sha256", "source_authority_registry_sha256",
            "correction_frontier_sha256", "evaluation_contract_sha256",
            "fixed_cohort_sha256", "evidence_stage",
        }:
            _invalid("BAMF_C05_BASELINE_COMPARISON_IDENTITY_INVALID")
        return cls(**record)


@dataclass(frozen=True)
class BaselineMeasurement:
    comparison: BaselineComparisonIdentity
    run_id: str
    accepted_generation: int
    accepted_parent_manifest_sha256: str
    accepted_candidate_sha256: str
    decision_evidence_sha256: str
    schema: str = MEASUREMENT_SCHEMA

    def __post_init__(self):
        if (type(self.comparison) is not BaselineComparisonIdentity
                or not isinstance(self.run_id, str) or not self.run_id
                or type(self.accepted_generation) is not int
                or self.accepted_generation < 1
                or any(not _sha(value) for value in (
                    self.accepted_parent_manifest_sha256,
                    self.accepted_candidate_sha256,
                    self.decision_evidence_sha256,
                ))
                or self.schema != MEASUREMENT_SCHEMA):
            _invalid("BAMF_C05_BASELINE_MEASUREMENT_INVALID")

    @property
    def accepted_identity(self) -> tuple[str, int, str]:
        return self.run_id, self.accepted_generation, self.comparison.capability_id

    @property
    def digest(self) -> str:
        return contract_digest(self)

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "comparison": self.comparison.to_record(),
            "run_id": self.run_id,
            "accepted_generation": self.accepted_generation,
            "accepted_parent_manifest_sha256": self.accepted_parent_manifest_sha256,
            "accepted_candidate_sha256": self.accepted_candidate_sha256,
            "decision_evidence_sha256": self.decision_evidence_sha256,
        }

    @classmethod
    def from_record(cls, record) -> "BaselineMeasurement":
        if not isinstance(record, dict) or set(record) != {
            "schema", "comparison", "run_id", "accepted_generation",
            "accepted_parent_manifest_sha256", "accepted_candidate_sha256",
            "decision_evidence_sha256",
        }:
            _invalid("BAMF_C05_BASELINE_MEASUREMENT_INVALID")
        values = dict(record)
        values["comparison"] = BaselineComparisonIdentity.from_record(
            values["comparison"])
        return cls(**values)


@dataclass(frozen=True)
class BaselineLedger:
    measurements: tuple[BaselineMeasurement, ...]
    schema: str = LEDGER_SCHEMA

    def __post_init__(self):
        if (not isinstance(self.measurements, tuple)
                or any(type(item) is not BaselineMeasurement for item in self.measurements)
                or self.schema != LEDGER_SCHEMA):
            _invalid("BAMF_C05_BASELINE_LEDGER_INVALID")
        seen = {}
        run_id = None
        prior_generation = 0
        for item in self.measurements:
            if item.accepted_identity in seen:
                _invalid("BAMF_C05_BASELINE_DUPLICATE_RECORD")
            if ((run_id is not None and item.run_id != run_id)
                    or item.accepted_generation <= prior_generation):
                _invalid("BAMF_C05_BASELINE_HISTORY_ORDER_INVALID")
            seen[item.accepted_identity] = item
            run_id = item.run_id
            prior_generation = item.accepted_generation

    @classmethod
    def empty(cls) -> "BaselineLedger":
        return cls(())

    @classmethod
    def from_optional_record(cls, record) -> "BaselineLedger":
        return cls.empty() if record is None else cls.from_record(dict(record))

    @property
    def digest(self) -> str:
        return contract_digest(self)

    def state_for(self, identity: BaselineComparisonIdentity) -> BaselineLifecycleState:
        if type(identity) is not BaselineComparisonIdentity:
            _invalid("BAMF_C05_BASELINE_COMPARISON_IDENTITY_INVALID")
        count = sum(item.comparison == identity for item in self.measurements)
        if count == 0:
            return BaselineLifecycleState.UNMEASURED
        if count == 1:
            return BaselineLifecycleState.BASELINE_ESTABLISHED
        return BaselineLifecycleState.COMPARABLE_HISTORY

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "measurements": [item.to_record() for item in self.measurements],
        }

    @classmethod
    def from_record(cls, record) -> "BaselineLedger":
        if (not isinstance(record, dict)
                or set(record) != {"schema", "measurements"}
                or record.get("schema") != LEDGER_SCHEMA
                or not isinstance(record.get("measurements"), list)):
            _invalid("BAMF_C05_BASELINE_LEDGER_INVALID")
        return cls(tuple(BaselineMeasurement.from_record(item)
                         for item in record["measurements"]))


def _new_transition_owner():
    issued = {}

    def require(value):
        if issued.get(id(value)) is not value:
            _invalid("BAMF_C05_BASELINE_TRANSITION_INVALID")
        return value

    def issue(measurement, parent_ledger_sha256):
        item = object.__new__(FactoryBaselineTransition)
        object.__setattr__(item, "measurement", measurement)
        object.__setattr__(item, "parent_ledger_sha256", parent_ledger_sha256)
        issued[id(item)] = item
        item.__post_init__()
        return item

    return require, issue


@dataclass(frozen=True, init=False)
class FactoryBaselineTransition:
    measurement: BaselineMeasurement
    parent_ledger_sha256: str

    def __init__(self, *args, **kwargs):
        _invalid("BAMF_C05_BASELINE_TRANSITION_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self):
        _require_factory_baseline_transition(self)
        if (type(self.measurement) is not BaselineMeasurement
                or not _sha(self.parent_ledger_sha256)):
            _invalid("BAMF_C05_BASELINE_TRANSITION_INVALID")


_require_factory_baseline_transition, _raw_issue_factory_baseline_transition = (
    _new_transition_owner())


def _issue_factory_baseline_transition(identity, *, run_id, accepted_generation,
                                       accepted_parent_manifest_sha256,
                                       accepted_candidate_sha256,
                                       decision_evidence_sha256,
                                       parent_ledger_sha256):
    """Private C05 issuer; persistence remains contingent on accepted publication."""
    measurement = BaselineMeasurement(
        identity, run_id, accepted_generation, accepted_parent_manifest_sha256,
        accepted_candidate_sha256, decision_evidence_sha256)
    return _raw_issue_factory_baseline_transition(measurement, parent_ledger_sha256)


def apply_factory_baseline_transition(ledger, transition) -> BaselineLedger:
    """Apply one owner-issued accepted measurement without rewriting history."""
    if type(ledger) is not BaselineLedger:
        _invalid("BAMF_C05_BASELINE_LEDGER_INVALID")
    _require_factory_baseline_transition(transition)
    transition.__post_init__()
    item = transition.measurement
    for existing in ledger.measurements:
        if existing.accepted_identity == item.accepted_identity:
            if existing == item:
                return ledger
            _invalid("BAMF_C05_BASELINE_DIVERGENT_DUPLICATE")
    if ledger.digest != transition.parent_ledger_sha256:
        _invalid("BAMF_C05_BASELINE_PARENT_DRIFT")
    return BaselineLedger((*ledger.measurements, item))


__all__ = (
    "BaselineComparisonIdentity", "BaselineLedger", "BaselineLifecycleState",
    "BaselineMeasurement", "FactoryBaselineTransition",
    "apply_factory_baseline_transition",
)
