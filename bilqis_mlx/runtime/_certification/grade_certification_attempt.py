"""Immutable #1334 attempt journal, result custody, and crash recovery."""
from __future__ import annotations

from pathlib import Path

from .grade_certification_contracts import (
    CertificationObligationScore, GradeCertificationPolicy, GradeCertificationRequest,
)
from .grade_certification_attempt_types import (
    CertificationAttemptView, _attempt_dir, _pointer_payload, _write_pointer,
)
from .grade_certification_custody_common import (
    ATTEMPT_SCHEMA, RESULT_SCHEMA, TERMINAL_SCHEMA, _immutable, _invalid, _read,
    _root, _score_records, _scores_from_records,
)
from .grade_certification_common import _sha
from .grade_certification_retry import _validate_snapshot

def start_certification_attempt(
    run_dir: Path,
    request: GradeCertificationRequest,
    policy: GradeCertificationPolicy,
    *,
    trigger_cohort_sha256: str,
    trigger_scores,
) -> CertificationAttemptView:
    scores = _validate_snapshot(request, policy, trigger_scores)
    if not _sha(trigger_cohort_sha256):
        _invalid("BAMF_GRADE_CERTIFICATION_TRIGGER_COHORT_INVALID")
    attempt = _attempt_dir(run_dir, request)
    payload = {
        "schema": ATTEMPT_SCHEMA,
        "request": request.to_record(),
        "policy": policy.to_record(),
        "trigger_cohort_sha256": trigger_cohort_sha256,
        "trigger_scores": _score_records(scores),
        "issued_status": "ISSUED",
    }
    _immutable(
        attempt / "attempt.json", payload,
        "BAMF_GRADE_CERTIFICATION_ATTEMPT_COLLISION")
    view = load_certification_attempt(run_dir, request)
    if view.status not in {"RUNNING", "FAILED", "SUCCEEDED", "SUPERSEDED"}:
        _invalid("BAMF_GRADE_CERTIFICATION_ATTEMPT_STATE_INVALID")
    if view.status == "RUNNING":
        _write_pointer(
            run_dir, request, status="RUNNING", next_cursor=view.next_cursor)
    return view


def _load_attempt_header(run_dir, request):
    request.verify()
    payload = _read(
        _attempt_dir(run_dir, request) / "attempt.json",
        "BAMF_GRADE_CERTIFICATION_ATTEMPT_MISSING")
    if (
        payload.get("schema") != ATTEMPT_SCHEMA
        or payload.get("request") != request.to_record()
        or payload.get("issued_status") != "ISSUED"
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_ATTEMPT_INVALID")
    policy_record = payload.get("policy")
    try:
        policy = GradeCertificationPolicy(
            policy_id=policy_record["policy_id"],
            policy_epoch=policy_record["policy_epoch"],
            entry_threshold=tuple(policy_record["entry_threshold"]),
            continuation_threshold=tuple(policy_record["continuation_threshold"]),
            retry_comparator_version=policy_record["retry_comparator_version"],
            protected_regression_version=policy_record[
                "protected_regression_version"],
            debt_authority=policy_record["debt_authority"],
            policy_sha256=policy_record["policy_sha256"],
            schema=policy_record["schema"],
        )
    except (KeyError, TypeError):
        _invalid("BAMF_GRADE_CERTIFICATION_POLICY_CUSTODY_INVALID")
    policy.verify()
    scores = _scores_from_records(payload.get("trigger_scores", ()))
    _validate_snapshot(request, policy, scores)
    return payload, policy, scores


def _committed(run_dir, request):
    results = _attempt_dir(run_dir, request) / "results"
    if not results.exists():
        return (), ()
    if results.is_symlink() or not results.is_dir():
        _invalid("BAMF_GRADE_CERTIFICATION_RESULT_CUSTODY_UNSAFE")
    entries = tuple(results.iterdir())
    if any(item.is_symlink() or not item.is_file() for item in entries):
        _invalid("BAMF_GRADE_CERTIFICATION_RESULT_CUSTODY_UNSAFE")
    rows, cohorts = [], []
    for ordinal, key in enumerate(request.active_obligations):
        path = results / f"{ordinal:06d}.json"
        if not path.exists():
            if any(item.name > path.name for item in entries):
                _invalid("BAMF_GRADE_CERTIFICATION_RESULT_GAP")
            break
        record = _read(path, "BAMF_GRADE_CERTIFICATION_RESULT_INVALID")
        if (
            record.get("schema") != RESULT_SCHEMA
            or record.get("attempt_sha256") != request.attempt_sha256
            or record.get("ordinal") != ordinal
            or not _sha(record.get("cohort_sha256"))
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_RESULT_INVALID")
        score = _scores_from_records((record.get("score"),))[0]
        if score.owner != "ACTIVE" or score.obligation_key != key:
            _invalid("BAMF_GRADE_CERTIFICATION_RESULT_INVALID")
        rows.append(score)
        cohorts.append(record["cohort_sha256"])
    if len(entries) != len(rows):
        _invalid("BAMF_GRADE_CERTIFICATION_RESULT_CUSTODY_UNSAFE")
    return tuple(rows), tuple(cohorts)


def _terminal(run_dir, request):
    path = _attempt_dir(run_dir, request) / "terminal.json"
    if not path.exists() and not path.is_symlink():
        return None
    record = _read(path, "BAMF_GRADE_CERTIFICATION_TERMINAL_INVALID")
    if (
        record.get("schema") != TERMINAL_SCHEMA
        or record.get("attempt_sha256") != request.attempt_sha256
        or record.get("family_sha256") != request.family_sha256
        or record.get("request_sha256") != request.request_sha256
        or record.get("status") not in {"FAILED", "SUCCEEDED", "SUPERSEDED"}
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_TERMINAL_INVALID")
    return record


def _load_certification_attempt(
    run_dir: Path,
    request: GradeCertificationRequest,
    *,
    update_pointer: bool,
) -> CertificationAttemptView:
    payload, policy, trigger = _load_attempt_header(run_dir, request)
    committed, committed_cohorts = _committed(run_dir, request)
    terminal = _terminal(run_dir, request)
    status = "RUNNING" if terminal is None else terminal["status"]
    blockers = (
        () if terminal is None
        else _scores_from_records(terminal.get("blockers", ())))
    receipt_sha256 = (
        None if terminal is None else terminal.get("receipt_sha256"))
    supersession_reason = (
        None if terminal is None else terminal.get("supersession_reason"))
    next_cursor = len(committed)
    pointer_path = _root(run_dir) / "current.json"
    expected = _pointer_payload(
        request, status=status, next_cursor=next_cursor)
    current = None
    if pointer_path.exists() or pointer_path.is_symlink():
        current = _read(
            pointer_path, "BAMF_GRADE_CERTIFICATION_POINTER_INVALID")
    if update_pointer and current != expected:
        _write_pointer(
            run_dir, request, status=status, next_cursor=next_cursor)
    return CertificationAttemptView(
        request, policy, payload["trigger_cohort_sha256"], trigger,
        committed, committed_cohorts, next_cursor, status, blockers,
        receipt_sha256, supersession_reason)


def load_certification_attempt(
    run_dir: Path,
    request: GradeCertificationRequest,
) -> CertificationAttemptView:
    return _load_certification_attempt(run_dir, request, update_pointer=True)


def inspect_certification_attempt(
    run_dir: Path,
    request: GradeCertificationRequest,
) -> CertificationAttemptView:
    """Verify historical attempt custody without mutating the live pointer."""
    return _load_certification_attempt(run_dir, request, update_pointer=False)


def commit_certification_result(
    run_dir: Path,
    request: GradeCertificationRequest,
    score: CertificationObligationScore,
    *,
    cohort_sha256: str,
) -> CertificationAttemptView:
    view = load_certification_attempt(run_dir, request)
    if view.status != "RUNNING":
        _invalid("BAMF_GRADE_CERTIFICATION_ATTEMPT_TERMINAL")
    if type(score) is not CertificationObligationScore or score.owner != "ACTIVE":
        _invalid("BAMF_GRADE_CERTIFICATION_RESULT_INVALID")
    if not _sha(cohort_sha256):
        _invalid("BAMF_GRADE_CERTIFICATION_RESULT_COHORT_INVALID")
    for existing in view.committed_scores:
        if existing.obligation_key == score.obligation_key:
            index = view.committed_scores.index(existing)
            if (
                existing != score
                or view.committed_cohort_sha256s[index] != cohort_sha256
            ):
                _invalid("BAMF_GRADE_CERTIFICATION_RESULT_COLLISION")
            return view
    if (
        view.next_cursor >= len(request.active_obligations)
        or request.active_obligations[view.next_cursor] != score.obligation_key
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_RESULT_OUT_OF_ORDER")
    record = {
        "schema": RESULT_SCHEMA,
        "attempt_sha256": request.attempt_sha256,
        "ordinal": view.next_cursor,
        "cohort_sha256": cohort_sha256,
        "score": score.to_record(),
    }
    _immutable(
        _attempt_dir(run_dir, request) / "results"
        / f"{view.next_cursor:06d}.json",
        record, "BAMF_GRADE_CERTIFICATION_RESULT_COLLISION")
    return load_certification_attempt(run_dir, request)
