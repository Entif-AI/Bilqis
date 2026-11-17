"""Terminal state and receipt custody for #1334 certification."""
from __future__ import annotations

from pathlib import Path

from .grade_certification_contracts import (
    AcceptedGradeCertificationReceipt, CertificationOutcome,
    GradeCertificationRequest,
    parse_certification_receipt, require_accepted_certification_receipt,
    _request_from_record,
)
from .grade_certification_attempt import (
    inspect_certification_attempt, load_certification_attempt,
)
from .grade_certification_attempt_types import _attempt_dir
from .grade_certification_custody_common import (
    ATTEMPT_SCHEMA, TERMINAL_SCHEMA, _immutable, _invalid, _read, _root,
    _score_records, _scores_from_records,
)
from .grade_certification_common import _sha

def fail_certification_attempt(
    run_dir: Path,
    request: GradeCertificationRequest,
    blockers,
    *,
    retry_baseline: bool = True,
) -> CertificationAttemptView:
    view = load_certification_attempt(run_dir, request)
    if view.status == "FAILED":
        return view
    if view.status != "RUNNING":
        _invalid("BAMF_GRADE_CERTIFICATION_ATTEMPT_TERMINAL")
    blockers = tuple(blockers)
    if not blockers or len({
        (item.owner, item.obligation_key) for item in blockers}) != len(blockers):
        _invalid("BAMF_GRADE_CERTIFICATION_BLOCKERS_INVALID")
    if type(retry_baseline) is not bool:
        _invalid("BAMF_GRADE_CERTIFICATION_BLOCKERS_INVALID")
    record = {
        "schema": TERMINAL_SCHEMA,
        "attempt_sha256": request.attempt_sha256,
        "family_sha256": request.family_sha256,
        "request_sha256": request.request_sha256,
        "status": "FAILED",
        "blockers": _score_records(blockers),
        "retry_baseline": retry_baseline,
    }
    _immutable(
        _attempt_dir(run_dir, request) / "terminal.json", record,
        "BAMF_GRADE_CERTIFICATION_TERMINAL_COLLISION")
    return load_certification_attempt(run_dir, request)


def load_certification_receipt(
    run_dir: Path,
    receipt_sha256: str,
) -> AcceptedGradeCertificationReceipt:
    if not _sha(receipt_sha256):
        _invalid("BAMF_GRADE_CERTIFICATION_RECEIPT_ID_INVALID")
    record = _read(
        _root(run_dir) / "receipts" / f"{receipt_sha256}.json",
        "BAMF_GRADE_CERTIFICATION_RECEIPT_MISSING")
    receipt = parse_certification_receipt(record)
    if receipt.receipt_sha256 != receipt_sha256:
        _invalid("BAMF_GRADE_CERTIFICATION_RECEIPT_DRIFT")
    return receipt


def load_certification_request(
    run_dir: Path,
    attempt_sha256: str,
) -> GradeCertificationRequest:
    if not _sha(attempt_sha256):
        _invalid("BAMF_GRADE_CERTIFICATION_ATTEMPT_ID_INVALID")
    record = _read(
        _root(run_dir) / "attempts" / attempt_sha256 / "attempt.json",
        "BAMF_GRADE_CERTIFICATION_ATTEMPT_MISSING")
    if record.get("schema") != ATTEMPT_SCHEMA:
        _invalid("BAMF_GRADE_CERTIFICATION_ATTEMPT_INVALID")
    request = _request_from_record(record.get("request"))
    if request.attempt_sha256 != attempt_sha256:
        _invalid("BAMF_GRADE_CERTIFICATION_ATTEMPT_INVALID")
    return request


def certification_receipts_for_predecessor(
    run_dir: Path,
    *,
    activation_sha256: str,
    definition_sha256: str,
) -> tuple[AcceptedGradeCertificationReceipt, ...]:
    """Return all immutable successful receipts for one exact predecessor."""
    receipts = _root(run_dir) / "receipts"
    if not receipts.exists():
        return ()
    if receipts.is_symlink() or not receipts.is_dir():
        _invalid("BAMF_GRADE_CERTIFICATION_RECEIPT_CUSTODY_UNSAFE")
    matches = []
    for path in receipts.iterdir():
        if path.is_symlink() or not path.is_file() or path.suffix != ".json":
            _invalid("BAMF_GRADE_CERTIFICATION_RECEIPT_CUSTODY_UNSAFE")
        receipt = parse_certification_receipt(_read(
            path, "BAMF_GRADE_CERTIFICATION_RECEIPT_INVALID"))
        if path.name != f"{receipt.receipt_sha256}.json":
            _invalid("BAMF_GRADE_CERTIFICATION_RECEIPT_DRIFT")
        if (
            receipt.predecessor_activation_sha256 != activation_sha256
            or receipt.predecessor_definition_sha256 != definition_sha256
        ):
            continue
        request = load_certification_request(run_dir, receipt.attempt_sha256)
        view = inspect_certification_attempt(run_dir, request)
        if (
            view.status != "SUCCEEDED"
            or view.receipt_sha256 != receipt.receipt_sha256
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_SUCCESS_CUSTODY_REQUIRED")
        matches.append(receipt)
    return tuple(sorted(matches, key=lambda item: item.receipt_sha256))


def certification_receipt_for_predecessor(
    run_dir: Path,
    *,
    activation_sha256: str,
    definition_sha256: str,
    receipt_sha256: str | None = None,
) -> AcceptedGradeCertificationReceipt | None:
    """Resolve one predecessor receipt, optionally by exact immutable identity."""
    if receipt_sha256 is not None:
        receipt = load_certification_receipt(run_dir, receipt_sha256)
        if (
            receipt.predecessor_activation_sha256 != activation_sha256
            or receipt.predecessor_definition_sha256 != definition_sha256
        ):
            return None
        request = load_certification_request(run_dir, receipt.attempt_sha256)
        view = inspect_certification_attempt(run_dir, request)
        if (
            view.status != "SUCCEEDED"
            or view.receipt_sha256 != receipt.receipt_sha256
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_SUCCESS_CUSTODY_REQUIRED")
        return receipt
    matches = certification_receipts_for_predecessor(
        run_dir,
        activation_sha256=activation_sha256,
        definition_sha256=definition_sha256,
    )
    if not matches:
        return None
    if len(matches) != 1:
        _invalid("BAMF_GRADE_CERTIFICATION_SUCCESS_AMBIGUOUS")
    return matches[0]


def succeed_certification_attempt(
    run_dir: Path,
    request: GradeCertificationRequest,
    receipt: AcceptedGradeCertificationReceipt,
) -> CertificationAttemptView:
    view = load_certification_attempt(run_dir, request)
    if view.status == "SUCCEEDED":
        if view.receipt_sha256 != receipt.receipt_sha256:
            _invalid("BAMF_GRADE_CERTIFICATION_TERMINAL_COLLISION")
        return view
    if view.status != "RUNNING":
        _invalid("BAMF_GRADE_CERTIFICATION_ATTEMPT_TERMINAL")
    if (
        type(receipt) is not AcceptedGradeCertificationReceipt
        or receipt.request_sha256 != request.request_sha256
        or receipt.family_sha256 != request.family_sha256
        or receipt.attempt_sha256 != request.attempt_sha256
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_RECEIPT_ATTEMPT_MISMATCH")
    require_accepted_certification_receipt(receipt)
    if (
        view.next_cursor != len(request.active_obligations)
        or len(view.committed_scores) != len(request.active_obligations)
        or tuple(item.obligation_key for item in view.committed_scores)
           != request.active_obligations
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_SUCCESS_CUSTODY_REQUIRED")
    committed = {
        item.obligation_key: item for item in view.committed_scores}
    final_scores = tuple(
        committed[item.obligation_key]
        if item.owner == "ACTIVE" else item
        for item in view.trigger_scores
    )
    expected_debt = tuple(
        item for item in final_scores if item.correct != item.total)
    expected_outcome = (
        CertificationOutcome.CERTIFIED_WITH_DEBT
        if expected_debt else CertificationOutcome.CERTIFIED_CLEAN
    )
    if (
        receipt.scores != final_scores
        or receipt.debt != expected_debt
        or receipt.outcome is not expected_outcome
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_SUCCESS_CUSTODY_REQUIRED")
    _immutable(
        _root(run_dir) / "receipts" / f"{receipt.receipt_sha256}.json",
        receipt.to_record(), "BAMF_GRADE_CERTIFICATION_RECEIPT_COLLISION")
    record = {
        "schema": TERMINAL_SCHEMA,
        "attempt_sha256": request.attempt_sha256,
        "family_sha256": request.family_sha256,
        "request_sha256": request.request_sha256,
        "status": "SUCCEEDED",
        "blockers": [],
        "receipt_sha256": receipt.receipt_sha256,
    }
    _immutable(
        _attempt_dir(run_dir, request) / "terminal.json", record,
        "BAMF_GRADE_CERTIFICATION_TERMINAL_COLLISION")
    return load_certification_attempt(run_dir, request)


def supersede_certification_attempt(
    run_dir: Path,
    request: GradeCertificationRequest,
    *,
    reason: str,
) -> CertificationAttemptView:
    view = load_certification_attempt(run_dir, request)
    if view.status == "SUPERSEDED":
        if view.supersession_reason != reason:
            _invalid("BAMF_GRADE_CERTIFICATION_TERMINAL_COLLISION")
        return view
    if view.status != "RUNNING":
        _invalid("BAMF_GRADE_CERTIFICATION_ATTEMPT_TERMINAL")
    if type(reason) is not str or not reason:
        _invalid("BAMF_GRADE_CERTIFICATION_SUPERSESSION_INVALID")
    record = {
        "schema": TERMINAL_SCHEMA,
        "attempt_sha256": request.attempt_sha256,
        "family_sha256": request.family_sha256,
        "request_sha256": request.request_sha256,
        "status": "SUPERSEDED",
        "blockers": [],
        "supersession_reason": reason,
    }
    _immutable(
        _attempt_dir(run_dir, request) / "terminal.json", record,
        "BAMF_GRADE_CERTIFICATION_TERMINAL_COLLISION")
    return load_certification_attempt(run_dir, request)
