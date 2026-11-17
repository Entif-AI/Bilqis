"""Versioned certification policy and obligation score contracts."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from bilqis_mlx.learning.retention_policy import MASTERY_DEBT_POWER

from .grade_certification_common import _digest, _invalid, _sha, _threshold

POLICY_SCHEMA = "bilqis.bamf.grade-certification-policy/v1"
ADR111_RETRY_COMPARATOR = "adr-111-unweighted-blocker-mean/v1"
ADR114_142_PROTECTED_COMPARATOR = "adr-114-142-quadratic-mastery-debt/v1"
ACCEPTED_DEBT_AUTHORITIES = frozenset({"ADR-084"})

@dataclass(frozen=True)
class GradeCertificationPolicy:
    policy_id: str
    policy_epoch: int
    entry_threshold: tuple[int, int]
    continuation_threshold: tuple[int, int]
    retry_comparator_version: str
    protected_regression_version: str
    debt_authority: str | None
    policy_sha256: str
    schema: str = POLICY_SCHEMA

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "policy_id": self.policy_id,
            "policy_epoch": self.policy_epoch,
            "entry_threshold": list(self.entry_threshold),
            "continuation_threshold": list(self.continuation_threshold),
            "retry_comparator_version": self.retry_comparator_version,
            "protected_regression_version": self.protected_regression_version,
            "debt_authority": self.debt_authority,
            "policy_sha256": self.policy_sha256,
        }

    def verify(self) -> None:
        record = self.to_record()
        claimed = record.pop("policy_sha256")
        if (
            self.schema != POLICY_SCHEMA or not self.policy_id
            or type(self.policy_epoch) is not int or self.policy_epoch < 0
            or not _threshold(self.entry_threshold)
            or not _threshold(self.continuation_threshold)
            or self.retry_comparator_version != ADR111_RETRY_COMPARATOR
            or self.protected_regression_version != ADR114_142_PROTECTED_COMPARATOR
            or (
                self.debt_authority is not None
                and self.debt_authority not in ACCEPTED_DEBT_AUTHORITIES
            )
            or not _sha(self.policy_sha256)
            or claimed != _digest(record)
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_POLICY_INVALID")


def certification_policy(
    *, policy_id: str, policy_epoch: int,
    entry_threshold: tuple[int, int],
    continuation_threshold: tuple[int, int],
    retry_comparator_version: str,
    protected_regression_version: str = ADR114_142_PROTECTED_COMPARATOR,
    debt_authority: str | None = None,
) -> GradeCertificationPolicy:
    values = {
        "schema": POLICY_SCHEMA,
        "policy_id": policy_id,
        "policy_epoch": policy_epoch,
        "entry_threshold": list(entry_threshold),
        "continuation_threshold": list(continuation_threshold),
        "retry_comparator_version": retry_comparator_version,
        "protected_regression_version": protected_regression_version,
        "debt_authority": debt_authority,
    }
    result = GradeCertificationPolicy(
        policy_id, policy_epoch, tuple(entry_threshold),
        tuple(continuation_threshold), retry_comparator_version,
        protected_regression_version, debt_authority, _digest(values))
    result.verify()
    return result


@dataclass(frozen=True, order=True)
class CertificationObligationScore:
    owner: str
    obligation_key: str
    correct: int
    total: int

    def __post_init__(self):
        if (
            self.owner not in {"ACTIVE", "PROTECTED"}
            or not self.obligation_key
            or type(self.correct) is not int or type(self.total) is not int
            or self.total <= 0 or not 0 <= self.correct <= self.total
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_SCORE_INVALID")

    def to_record(self) -> dict:
        return {
            "owner": self.owner,
            "obligation_key": self.obligation_key,
            "correct": self.correct,
            "total": self.total,
        }


def protected_regression_eligible(scores, baselines) -> bool:
    """Apply ADR-114/142 debt economics to exact prior-certified baselines.

    Exact ties and monotone improvement are eligible. If any protected obligation
    regresses, the complete comparable protected surface must still have strictly
    positive normalized quadratic mastery-debt utility.
    """
    current = {
        item.obligation_key: item
        for item in scores if item.owner == "PROTECTED"
    }
    baselines = tuple(baselines)
    baseline_keys = {item.obligation_key for item in baselines}
    if not baseline_keys <= set(current):
        return False
    if not baselines:
        return True
    regressed = False
    utility = Fraction(0, 1)
    for baseline in baselines:
        item = current[baseline.obligation_key]
        before = Fraction(baseline.correct, baseline.total)
        after = Fraction(item.correct, item.total)
        if after < before:
            regressed = True
        before_debt = Fraction(1, 1) - before
        after_debt = Fraction(1, 1) - after
        utility += before_debt ** MASTERY_DEBT_POWER - after_debt ** MASTERY_DEBT_POWER
    return not regressed or utility > 0
