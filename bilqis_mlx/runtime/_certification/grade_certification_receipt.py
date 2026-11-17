"""Live-only accepted grade certification receipt contract."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .grade_certification_common import _digest, _invalid, _sha
from .grade_certification_policy import (
    CertificationObligationScore, protected_regression_eligible,
)
from .grade_certification_request import (
    GradeCertificationRequest, _REQUEST_ISSUER,
)

RECEIPT_SCHEMA = "bilqis.bamf.accepted-grade-certification-receipt/v1"
_RECEIPT_ISSUER = object()

class CertificationOutcome(str, Enum):
    CERTIFIED_CLEAN = "CERTIFIED_CLEAN"
    CERTIFIED_WITH_DEBT = "CERTIFIED_WITH_DEBT"


@dataclass(frozen=True, init=False)
class AcceptedGradeCertificationReceipt:
    request_sha256: str
    family_sha256: str
    attempt_sha256: str
    predecessor_activation_sha256: str
    predecessor_definition_sha256: str
    outcome: CertificationOutcome
    scores: tuple[CertificationObligationScore, ...]
    debt: tuple[CertificationObligationScore, ...]
    receipt_sha256: str
    schema: str = RECEIPT_SCHEMA
    _issuance: object = field(repr=False, compare=False, default=None)

    def __init__(self, *args, **kwargs):
        _invalid("BAMF_GRADE_CERTIFICATION_RECEIPT_CALLER_CONSTRUCTION_FORBIDDEN")

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "request_sha256": self.request_sha256,
            "family_sha256": self.family_sha256,
            "attempt_sha256": self.attempt_sha256,
            "predecessor_activation_sha256": self.predecessor_activation_sha256,
            "predecessor_definition_sha256": self.predecessor_definition_sha256,
            "outcome": self.outcome.value,
            "scores": [item.to_record() for item in self.scores],
            "debt": [item.to_record() for item in self.debt],
            "receipt_sha256": self.receipt_sha256,
        }

    def verify(self) -> None:
        record = self.to_record()
        claimed = record.pop("receipt_sha256")
        if (
            self.schema != RECEIPT_SCHEMA
            or any(not _sha(value) for value in (
                self.request_sha256, self.family_sha256, self.attempt_sha256,
                self.predecessor_activation_sha256,
                self.predecessor_definition_sha256, self.receipt_sha256))
            or type(self.outcome) is not CertificationOutcome
            or type(self.scores) is not tuple or not self.scores
            or type(self.debt) is not tuple
            or len({(item.owner, item.obligation_key) for item in self.scores})
               != len(self.scores)
            or any(item not in self.scores for item in self.debt)
            or claimed != _digest(record)
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_RECEIPT_INVALID")


def _build_receipt(request, outcome, scores, debt, issuance):
    result = object.__new__(AcceptedGradeCertificationReceipt)
    values = {
        "request_sha256": request.request_sha256,
        "family_sha256": request.family_sha256,
        "attempt_sha256": request.attempt_sha256,
        "predecessor_activation_sha256": request.active_grade_activation_sha256,
        "predecessor_definition_sha256": request.active_grade_definition_sha256,
        "outcome": outcome,
        "scores": tuple(scores), "debt": tuple(debt),
        "receipt_sha256": "0" * 64, "schema": RECEIPT_SCHEMA,
        "_issuance": issuance,
    }
    for name, value in values.items():
        object.__setattr__(result, name, value)
    record = result.to_record()
    record.pop("receipt_sha256")
    object.__setattr__(result, "receipt_sha256", _digest(record))
    result.verify()
    return result


def _issue_success_receipt(request, *, outcome, scores, debt):
    if (
        type(request) is not GradeCertificationRequest
        or getattr(request, "_issuance", None) is not _REQUEST_ISSUER
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_REQUEST_REQUIRED")
    request.verify()
    if type(outcome) is not CertificationOutcome:
        _invalid("BAMF_GRADE_CERTIFICATION_OUTCOME_INVALID")
    scores, debt = tuple(scores), tuple(debt)
    expected_debt = tuple(
        item for item in scores if item.correct != item.total)
    if not protected_regression_eligible(scores, request.protected_baselines):
        _invalid("BAMF_GRADE_CERTIFICATION_PROTECTED_VETO")
    if (
        outcome is CertificationOutcome.CERTIFIED_CLEAN
        and (debt or any(item.correct != item.total for item in scores))
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_CLEAN_DEBT_INVALID")
    if outcome is CertificationOutcome.CERTIFIED_WITH_DEBT:
        if not debt or debt != expected_debt:
            _invalid("BAMF_GRADE_CERTIFICATION_DEBT_REQUIRED")
        if request.debt_authority is None:
            _invalid("BAMF_GRADE_CERTIFICATION_DEBT_AUTHORITY_REQUIRED")
    return _build_receipt(request, outcome, scores, debt, _RECEIPT_ISSUER)


def parse_certification_receipt(record: dict):
    try:
        result = object.__new__(AcceptedGradeCertificationReceipt)
        values = {
            "request_sha256": record["request_sha256"],
            "family_sha256": record["family_sha256"],
            "attempt_sha256": record["attempt_sha256"],
            "predecessor_activation_sha256": record["predecessor_activation_sha256"],
            "predecessor_definition_sha256": record["predecessor_definition_sha256"],
            "outcome": CertificationOutcome(record["outcome"]),
            "scores": tuple(CertificationObligationScore(**item) for item in record["scores"]),
            "debt": tuple(CertificationObligationScore(**item) for item in record["debt"]),
            "receipt_sha256": record["receipt_sha256"],
            "schema": record["schema"], "_issuance": None,
        }
        if set(record) != {
            "schema", "request_sha256", "family_sha256", "attempt_sha256",
            "predecessor_activation_sha256", "predecessor_definition_sha256",
            "outcome", "scores", "debt", "receipt_sha256"}:
            raise KeyError
        for name, value in values.items():
            object.__setattr__(result, name, value)
        result.verify()
        return result
    except (KeyError, TypeError, ValueError):
        _invalid("BAMF_GRADE_CERTIFICATION_RECEIPT_INVALID")


def require_accepted_certification_receipt(receipt):
    if (
        type(receipt) is not AcceptedGradeCertificationReceipt
        or getattr(receipt, "_issuance", None) is not _RECEIPT_ISSUER
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_RECEIPT_AUTHORITY_REQUIRED")
    receipt.verify()
    return receipt
