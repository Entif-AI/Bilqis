"""Compatibility surface for generic #1334 certification contracts."""
from .grade_certification_policy import (
    CertificationObligationScore, GradeCertificationPolicy, certification_policy,
)
from .grade_certification_request import (
    GradeCertificationRequest, _issue_certification_request, _request_from_record,
)
from .grade_certification_receipt import (
    AcceptedGradeCertificationReceipt, CertificationOutcome, _issue_success_receipt,
    parse_certification_receipt, require_accepted_certification_receipt,
)

__all__ = (
    "AcceptedGradeCertificationReceipt", "CertificationObligationScore",
    "CertificationOutcome", "GradeCertificationPolicy", "GradeCertificationRequest",
    "certification_policy", "parse_certification_receipt",
    "require_accepted_certification_receipt",
)
