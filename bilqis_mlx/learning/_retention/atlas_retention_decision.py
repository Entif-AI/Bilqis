"""C05-owned, custody-bound B13 retention decisions.

The runtime evaluator must execute the stage-authoritative C05 screen.
Caller-provided booleans and historical decision JSON cannot authorize generation
publication. Foundation acquisition authorizes from fixed-school preservation;
fresh/generalization cohorts remain non-authorizing measurements under ADR-134.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from bilqis_mlx.errors import ErrorBus, SCHOOL

LEGACY_DECISION_SCHEMA = "bilqis.mlx.candidate-retention-decision/v1"
PREVIOUS_DECISION_SCHEMA = "bilqis.mlx.candidate-retention-decision/v2"
PREVIOUS_BASELINE_DECISION_SCHEMA = "bilqis.mlx.candidate-retention-decision/v3"
PREVIOUS_SCOPE_DECISION_SCHEMA = "bilqis.mlx.candidate-retention-decision/v4"
DECISION_SCHEMA = "bilqis.mlx.candidate-retention-decision/v5"
BLOCKING_SCORE_BUDGET_WIDTH = 5
ACCEPTED_DECISION = "PROVISIONAL"
REJECTED_DECISION = "REJECT"
ACCEPTING_REASON = "PAIRED_SCREEN_WITHIN_BUDGET"
_V2_DECISION_FIELDS = (
    "decision", "reason", "parent_generation", "candidate_generation",
    "evidence_sha256", "policy_sha256", "schema_version",
)
_V3_DECISION_FIELDS = (
    "decision", "reason", "parent_generation", "candidate_generation",
    "evidence_sha256", "policy_sha256", "blocking_capability",
    "blocking_scope", "baseline_coverage", "schema_version",
)
_V4_DECISION_FIELDS = (
    *_V3_DECISION_FIELDS[:-1],
    "evaluated_capability_ids", "retention_protection_plan_sha256",
    "broad_certification_trigger", "schema_version",
)
_DECISION_FIELDS = (
    *_V4_DECISION_FIELDS[:-1], "blocking_score_budget", "schema_version",
)


def _new_decision_owner():
    """Track live C05 decisions by owner-issued object identity, not a token."""
    issued = {}
    generation_authority = {}
    finalized_generation_authority = set()
    baseline_ledger_sha256 = {}

    def require(value):
        if issued.get(id(value)) is not value:
            _invalid()
        return value

    def issue(values, *, generation_authority_sha256=None,
              expected_baseline_ledger_sha256=None):
        decision = object.__new__(CandidateRetentionDecision)
        for name, value in values:
            object.__setattr__(decision, name, value)
        issued[id(decision)] = decision
        generation_authority[id(decision)] = generation_authority_sha256
        baseline_ledger_sha256[id(decision)] = expected_baseline_ledger_sha256
        decision.__post_init__()
        return decision

    def require_generation_authority(value, expected):
        require(value)
        if (not _digest(expected)
                or generation_authority.get(id(value)) != expected):
            _invalid()
        return value

    def issued_generation_authority(value):
        return generation_authority.get(id(value))

    def finalize_generation_authority(value, expected, final):
        require(value)
        key = id(value)
        if (key in finalized_generation_authority
                or not _digest(expected) or not _digest(final)
                or generation_authority.get(key) != expected):
            _invalid()
        generation_authority[key] = final
        finalized_generation_authority.add(key)
        return value

    def issued_baseline_ledger_sha256(value):
        return baseline_ledger_sha256.get(id(value))

    return (require, require_generation_authority, issued_generation_authority,
            finalize_generation_authority, issued_baseline_ledger_sha256, issue)
_LEGACY_FIELDS = (
    "decision", "reason", "target_gain", "protected_net_gain", "schema_version",
)


def _invalid() -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


def _canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _digest(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def _valid_blocking_score_budget(value) -> bool:
    if value is None:
        return True
    if (not isinstance(value, (list, tuple))
            or len(value) != BLOCKING_SCORE_BUDGET_WIDTH):
        return False
    capability, before, after, total, allowed = value
    return (isinstance(capability, str) and bool(capability)
            and all(type(number) is int for number in (before, after, total, allowed))
            and 0 <= before <= total and 0 <= after <= total
            and 0 <= allowed <= total)


@dataclass(frozen=True)
class CandidateRetentionDecision:
    """Live token issued only after C05 runs its stage-authoritative evaluation."""

    decision: str
    reason: str
    parent_generation: str
    candidate_generation: str
    evidence_sha256: str
    policy_sha256: str
    blocking_capability: str | None = None
    blocking_scope: str | None = None
    baseline_coverage: dict | None = None
    evaluated_capability_ids: tuple[str, ...] = ()
    retention_protection_plan_sha256: str | None = None
    broad_certification_trigger: str | None = None
    blocking_score_budget: tuple[str, int, int, int, int] | None = None
    schema_version: str = DECISION_SCHEMA

    def __post_init__(self) -> None:
        _require_issued_decision(self)
        if (self.decision not in {ACCEPTED_DECISION, REJECTED_DECISION}
                or not isinstance(self.reason, str) or not self.reason
                or (self.decision == ACCEPTED_DECISION)
                != (self.reason == ACCEPTING_REASON)
                or any(not _digest(value) for value in (
                    self.parent_generation, self.candidate_generation,
                    self.evidence_sha256, self.policy_sha256))
                or (self.blocking_capability is not None
                    and (not isinstance(self.blocking_capability, str)
                         or not self.blocking_capability))
                or (self.blocking_scope is not None
                    and (not isinstance(self.blocking_scope, str)
                         or not self.blocking_scope))
                or (self.baseline_coverage is not None
                    and not _valid_baseline_coverage(self.baseline_coverage))
                or not isinstance(self.evaluated_capability_ids, tuple)
                or any(not isinstance(item, str) or not item
                       for item in self.evaluated_capability_ids)
                or len(set(self.evaluated_capability_ids))
                != len(self.evaluated_capability_ids)
                or (self.retention_protection_plan_sha256 is not None
                    and not _digest(self.retention_protection_plan_sha256))
                or (self.broad_certification_trigger is not None
                    and (not isinstance(self.broad_certification_trigger, str)
                         or not self.broad_certification_trigger))
                or (self.retention_protection_plan_sha256 is not None
                    and self.broad_certification_trigger is not None)
                or not _valid_blocking_score_budget(self.blocking_score_budget)
                or self.schema_version != DECISION_SCHEMA):
            _invalid()

    @property
    def accepted(self) -> bool:
        return self.decision == ACCEPTED_DECISION

    def _public_record(self) -> dict:
        return {name: getattr(self, name) for name in _DECISION_FIELDS}

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical(self._public_record())).hexdigest()

    def to_record(self) -> dict:
        return {**self._public_record(), "decision_sha256": self.digest}

    @classmethod
    def from_record(cls, record) -> "ParsedCandidateRetentionDecision":
        """Parse v1/v2 evidence for inspection without granting issuer authority."""
        if not isinstance(record, dict):
            _invalid()
        schema = record.get("schema_version")
        names = (_LEGACY_FIELDS if schema == LEGACY_DECISION_SCHEMA
                 else _V2_DECISION_FIELDS if schema == PREVIOUS_DECISION_SCHEMA
                 else _V3_DECISION_FIELDS
                 if schema == PREVIOUS_BASELINE_DECISION_SCHEMA
                 else _V4_DECISION_FIELDS
                 if schema == PREVIOUS_SCOPE_DECISION_SCHEMA
                 else _DECISION_FIELDS if schema == DECISION_SCHEMA else ())
        if not names or set(record) != set(names) | {"decision_sha256"}:
            _invalid()
        if (record["decision"] not in {ACCEPTED_DECISION, REJECTED_DECISION}
                or not isinstance(record["reason"], str) or not record["reason"]
                or (record["decision"] == ACCEPTED_DECISION)
                != (record["reason"] == ACCEPTING_REASON)):
            _invalid()
        if names == _LEGACY_FIELDS:
            if (type(record["target_gain"]) is not bool
                    or type(record["protected_net_gain"]) is not int):
                _invalid()
        elif any(not _digest(record[name]) for name in (
                "parent_generation", "candidate_generation",
                "evidence_sha256", "policy_sha256")):
            _invalid()
        if (names in {_V3_DECISION_FIELDS, _DECISION_FIELDS}
                and ((record["blocking_capability"] is not None
                      and (not isinstance(record["blocking_capability"], str)
                           or not record["blocking_capability"]))
                     or (record["blocking_scope"] is not None
                         and (not isinstance(record["blocking_scope"], str)
                              or not record["blocking_scope"]))
                     or (record["baseline_coverage"] is not None
                         and not _valid_baseline_coverage(record["baseline_coverage"])))):
            _invalid()
        if names in {_V4_DECISION_FIELDS, _DECISION_FIELDS}:
            evaluated = record["evaluated_capability_ids"]
            if (not isinstance(evaluated, (list, tuple))
                    or any(not isinstance(item, str) or not item for item in evaluated)
                    or len(set(evaluated)) != len(evaluated)
                    or (record["retention_protection_plan_sha256"] is not None
                        and not _digest(record["retention_protection_plan_sha256"]))
                    or (record["broad_certification_trigger"] is not None
                        and (not isinstance(record["broad_certification_trigger"], str)
                             or not record["broad_certification_trigger"]))
                    or (record["retention_protection_plan_sha256"] is not None
                        and record["broad_certification_trigger"] is not None)):
                _invalid()
        if names == _DECISION_FIELDS and not _valid_blocking_score_budget(
                record["blocking_score_budget"]):
            _invalid()
        payload = {name: record[name] for name in names}
        if record["decision_sha256"] != hashlib.sha256(_canonical(payload)).hexdigest():
            _invalid()
        return ParsedCandidateRetentionDecision(payload)


@dataclass(frozen=True)
class ParsedCandidateRetentionDecision:
    """Historical evidence is not a live acceptance capability."""
    fields: dict

    @property
    def decision(self) -> str:
        return self.fields["decision"]

    @property
    def reason(self) -> str:
        return self.fields["reason"]

    @property
    def accepted(self) -> bool:
        return self.decision == ACCEPTED_DECISION

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical(self.fields)).hexdigest()

    def to_record(self) -> dict:
        return {**self.fields, "decision_sha256": self.digest}


def _valid_baseline_coverage(record) -> bool:
    if record is None:
        return True
    try:
        from bilqis_mlx.runtime.baseline.currentness import BaselineCoverage
        BaselineCoverage.from_record(record)
    except Exception:
        return False
    return True


def decide_candidate_retention(
        *, parent_solver, candidate_solver, target_capability, policy, cohorts,
        parent_state, candidate_state) -> CandidateRetentionDecision:
    """Fail closed until Factory/source owns the complete C05 screen.

    C05 currently provides owner-run evaluation, but these arguments still
    include caller-supplied solvers, policy and cohorts. Their self-consistency
    cannot establish source provenance. Only an integrated Factory/backend
    evaluator may eventually authorize live B13 acceptance.
    """
    ErrorBus.Raise(
        SCHOOL.MODEL_TOPOLOGY.INVALID,
        reason="BAMF_C05_SOURCE_OWNER_REQUIRED",
    )


(_require_issued_decision, _require_issued_decision_generation_authority,
 _issued_decision_generation_authority, _finalize_issued_decision_generation_authority,
 _issued_decision_baseline_ledger_sha256, _raw_issue_decision) = _new_decision_owner()


def _make_factory_retention_issuer(raw_issue):
    def issue_factory_retention_decision(owner_evaluation) -> CandidateRetentionDecision:
        """Issue live acceptance authority only from the Factory C05 owner."""
        from bilqis_mlx.runtime.factory_retention_owner import (
            FactoryRetentionEvaluation, _require_factory_evaluation,
        )
        from bilqis_mlx.runtime.capability_retention import DecisionStatus

        if type(owner_evaluation) is not FactoryRetentionEvaluation:
            _invalid()
        _require_factory_evaluation(owner_evaluation)
        owner_evaluation.__post_init__()
        result = owner_evaluation.decision
        status = (ACCEPTED_DECISION if result.status is DecisionStatus.ELIGIBLE
                  else REJECTED_DECISION)
        return raw_issue((
            ("decision", status),
            ("reason", result.reason),
            ("parent_generation", owner_evaluation.parent_candidate_sha256),
            ("candidate_generation", owner_evaluation.candidate_candidate_sha256),
            ("evidence_sha256", result.evidence_sha256),
            ("policy_sha256", result.policy_sha256),
            ("blocking_capability", result.blocking_capability),
            ("blocking_scope", result.blocking_scope),
            ("baseline_coverage", (
                result.baseline_coverage.to_record()
                if result.baseline_coverage is not None else None)),
            ("evaluated_capability_ids", result.evaluated_capability_ids),
            ("retention_protection_plan_sha256",
             result.retention_protection_plan_sha256),
            ("broad_certification_trigger", result.broad_certification_trigger),
            ("blocking_score_budget", result.blocking_score_budget),
            ("schema_version", DECISION_SCHEMA),
        ), generation_authority_sha256=(
            owner_evaluation.candidate_generation_authority_sha256),
            expected_baseline_ledger_sha256=owner_evaluation.baseline_ledger.digest)

    return issue_factory_retention_decision


issue_factory_retention_decision = _make_factory_retention_issuer(
    _raw_issue_decision)
del _raw_issue_decision
