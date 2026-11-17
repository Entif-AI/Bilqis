"""Grade-neutral #1334 certification state machine over injected measurement."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL

from .grade_certification_contracts import (
    AcceptedGradeCertificationReceipt,
    CertificationObligationScore,
    CertificationOutcome,
    GradeCertificationPolicy,
    GradeCertificationRequest,
    _issue_success_receipt,
)
from .grade_certification_custody import (
    commit_certification_result,
    fail_certification_attempt,
    load_certification_attempt,
    load_certification_receipt,
    load_certification_request,
    policy_continuation_eligible,
    policy_entry_eligible,
    retry_certification_eligible,
    start_certification_attempt,
    succeed_certification_attempt,
    supersede_certification_attempt,
)
from .grade_certification_custody_common import _root
from .grade_certification_policy import protected_regression_eligible


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _sha(value: object) -> bool:
    return (
        type(value) is str and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


@dataclass(frozen=True)
class CertificationMeasurement:
    cohort_sha256: str
    scores: tuple[CertificationObligationScore, ...]

    def __post_init__(self) -> None:
        if (
            not _sha(self.cohort_sha256)
            or type(self.scores) is not tuple
            or not self.scores
            or any(type(item) is not CertificationObligationScore
                   for item in self.scores)
            or len({(item.owner, item.obligation_key)
                    for item in self.scores}) != len(self.scores)
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_MEASUREMENT_INVALID")


@dataclass(frozen=True)
class CertificationExecutionResult:
    status: str
    request_sha256: str
    receipt: AcceptedGradeCertificationReceipt | None = None
    blockers: tuple[CertificationObligationScore, ...] = ()
    supersession_reason: str | None = None


def _attempt_path(run_dir: Path, request: GradeCertificationRequest) -> Path:
    return (
        Path(run_dir) / "grade-certification" / "attempts"
        / request.attempt_sha256 / "attempt.json"
    )


def _trigger_matches_request(
    request: GradeCertificationRequest,
    measurement: CertificationMeasurement,
) -> bool:
    expected = {
        *[("ACTIVE", item) for item in request.active_obligations],
        *[("PROTECTED", item) for item in request.protected_obligations],
    }
    actual = {(item.owner, item.obligation_key) for item in measurement.scores}
    return expected == actual and len(actual) == len(measurement.scores)


def _blockers(request, scores) -> tuple[CertificationObligationScore, ...]:
    baselines = {
        item.obligation_key: item for item in request.protected_baselines
    }
    result = []
    for item in scores:
        if item.owner == "ACTIVE" and item.correct != item.total:
            result.append(item)
        elif item.owner == "PROTECTED":
            baseline = baselines.get(item.obligation_key)
            if baseline is None:
                continue
            if (
                item.correct * baseline.total
                < baseline.correct * item.total
            ):
                result.append(item)
    return tuple(result)


def _replace_active(
    scores: tuple[CertificationObligationScore, ...],
    replacement: CertificationObligationScore,
) -> tuple[CertificationObligationScore, ...]:
    found = False
    result = []
    for item in scores:
        if (
            item.owner == "ACTIVE"
            and item.obligation_key == replacement.obligation_key
        ):
            result.append(replacement)
            found = True
        else:
            result.append(item)
    if not found:
        _invalid("BAMF_GRADE_CERTIFICATION_REPLACEMENT_SCOPE_INVALID")
    return tuple(result)


def _terminal_result(run_dir: Path, view) -> CertificationExecutionResult:
    receipt = (
        load_certification_receipt(run_dir, view.receipt_sha256)
        if view.status == "SUCCEEDED" and view.receipt_sha256 is not None
        else None
    )
    return CertificationExecutionResult(
        view.status,
        view.request.request_sha256,
        receipt=receipt,
        blockers=view.blockers,
        supersession_reason=view.supersession_reason,
    )


def _current_or_supersede(
    run_dir: Path,
    request: GradeCertificationRequest,
    require_current: Callable[[], GradeCertificationRequest],
):
    try:
        current = require_current()
        if (
            type(current) is not GradeCertificationRequest
            or current.request_sha256 != request.request_sha256
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_CURRENTNESS_DRIFT")
        return current, None
    except BilqisError as error:
        reason = error.context.get("reason")
        superseding_reasons = {
            "BAMF_GRADE_CERTIFICATION_CURRENTNESS_DRIFT",
            "BAMF_GRADE_CERTIFICATION_POLICY_SELECTION_DRIFT",
            "BAMF_GRADE_CERTIFICATION_REQUEST_REISSUE_DRIFT",
        }
        if reason not in superseding_reasons:
            raise
        view = supersede_certification_attempt(
            run_dir, request, reason=reason)
        return None, _terminal_result(run_dir, view)


def _supersede_stale_running_attempts(root, request) -> None:
    attempts = _root(root) / "attempts"
    if not attempts.exists():
        return
    if attempts.is_symlink() or not attempts.is_dir():
        _invalid("BAMF_GRADE_CERTIFICATION_CUSTODY_UNSAFE")
    for path in sorted(attempts.iterdir(), key=lambda item: item.name):
        if path.is_symlink() or not path.is_dir():
            _invalid("BAMF_GRADE_CERTIFICATION_CUSTODY_UNSAFE")
        if path.name == request.attempt_sha256:
            continue
        terminal = path / "terminal.json"
        if terminal.is_symlink():
            _invalid("BAMF_GRADE_CERTIFICATION_CUSTODY_UNSAFE")
        if terminal.exists():
            continue
        stale_request = load_certification_request(root, path.name)
        stale = load_certification_attempt(root, stale_request)
        if stale.status == "RUNNING":
            supersede_certification_attempt(
                root, stale_request,
                reason="BAMF_GRADE_CERTIFICATION_CURRENTNESS_DRIFT")


def _start_or_resume(
        root, request, policy, trigger_measure, require_current):
    if _attempt_path(root, request).is_file():
        return load_certification_attempt(root, request)
    require_current()
    _supersede_stale_running_attempts(root, request)
    trigger = trigger_measure()
    if not _trigger_matches_request(request, trigger):
        _invalid("BAMF_GRADE_CERTIFICATION_TRIGGER_SCOPE_INVALID")
    require_current()
    return start_certification_attempt(
        root, request, policy,
        trigger_cohort_sha256=trigger.cohort_sha256,
        trigger_scores=trigger.scores)


def _initial_gate_result(root, request, policy, view, require_current):
    if not policy_entry_eligible(
            policy, view.trigger_scores, request.protected_baselines):
        require_current()
        failed = fail_certification_attempt(
            root, request, _blockers(request, view.trigger_scores))
        return _terminal_result(root, failed)
    if not retry_certification_eligible(
            root, request, policy, view.trigger_scores):
        require_current()
        failed = fail_certification_attempt(
            root, request, _blockers(request, view.trigger_scores),
            retry_baseline=False)
        return _terminal_result(root, failed)
    return None


def _running_scores(view):
    running = tuple(view.trigger_scores)
    for score in view.committed_scores:
        running = _replace_active(running, score)
    return running


def _resume_gate_result(root, request, policy, view, running, require_current):
    if not view.next_cursor or policy_continuation_eligible(
            policy, running, request.protected_baselines):
        return None
    _current, superseded = _current_or_supersede(
        root, request, require_current)
    if superseded is not None:
        return superseded
    failed = fail_certification_attempt(
        root, request, _blockers(request, running))
    return _terminal_result(root, failed)


def _measure_remaining(
        root, request, policy, view, running, obligation_measure,
        require_current):
    for key in request.active_obligations[view.next_cursor:]:
        _current, superseded = _current_or_supersede(
            root, request, require_current)
        if superseded is not None:
            return view, running, superseded
        measurement = obligation_measure(key)
        if (
            len(measurement.scores) != 1
            or measurement.scores[0].owner != "ACTIVE"
            or measurement.scores[0].obligation_key != key
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_OBLIGATION_SCOPE_INVALID")
        _current, superseded = _current_or_supersede(
            root, request, require_current)
        if superseded is not None:
            return view, running, superseded
        score = measurement.scores[0]
        view = commit_certification_result(
            root, request, score, cohort_sha256=measurement.cohort_sha256)
        running = _replace_active(running, score)
        if policy_continuation_eligible(
                policy, running, request.protected_baselines):
            continue
        _current, superseded = _current_or_supersede(
            root, request, require_current)
        if superseded is not None:
            return view, running, superseded
        failed = fail_certification_attempt(
            root, request, _blockers(request, running))
        return failed, running, _terminal_result(root, failed)
    return view, running, None


def _finish_attempt(root, request, view, running, require_current):
    debt = tuple(item for item in running if item.correct != item.total)
    if debt and request.debt_authority is None:
        _current, superseded = _current_or_supersede(
            root, request, require_current)
        if superseded is not None:
            return superseded
        failed = fail_certification_attempt(root, request, debt)
        return _terminal_result(root, failed)
    live_request, superseded = _current_or_supersede(
        root, request, require_current)
    if superseded is not None:
        return superseded
    outcome = (
        CertificationOutcome.CERTIFIED_WITH_DEBT
        if debt else CertificationOutcome.CERTIFIED_CLEAN)
    receipt = _issue_success_receipt(
        live_request, outcome=outcome, scores=running, debt=debt)
    succeeded = succeed_certification_attempt(root, request, receipt)
    return CertificationExecutionResult(
        succeeded.status, request.request_sha256, receipt=receipt)


def execute_grade_certification(
    run_dir: Path,
    request: GradeCertificationRequest,
    policy: GradeCertificationPolicy,
    *,
    trigger_measure: Callable[[], CertificationMeasurement],
    obligation_measure: Callable[[str], CertificationMeasurement],
    require_current: Callable[[], GradeCertificationRequest],
) -> CertificationExecutionResult:
    """Run or resume one passive certification attempt.

    Measurement is injected so the state machine remains independent of MLX,
    source adapters, teaching cadence, and optimizer ownership.
    """
    root = Path(run_dir)
    request.verify()
    policy.verify()
    if (
        request.policy_sha256 != policy.policy_sha256
        or request.policy_epoch != policy.policy_epoch
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_POLICY_DRIFT")

    view = _start_or_resume(
        root, request, policy, trigger_measure, require_current)
    if view.status != "RUNNING":
        return _terminal_result(root, view)
    gated = _initial_gate_result(root, request, policy, view, require_current)
    if gated is not None:
        return gated
    running = _running_scores(view)
    gated = _resume_gate_result(
        root, request, policy, view, running, require_current)
    if gated is not None:
        return gated
    view, running, measured = _measure_remaining(
        root, request, policy, view, running, obligation_measure, require_current)
    if measured is not None:
        return measured
    return _finish_attempt(root, request, view, running, require_current)


__all__ = (
    "CertificationExecutionResult", "CertificationMeasurement",
    "execute_grade_certification",
)
