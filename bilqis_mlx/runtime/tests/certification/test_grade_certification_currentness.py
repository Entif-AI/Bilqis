"""Currentness, protected-prior, and terminal #1334 execution witnesses."""
import pytest

from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL
from bilqis_mlx.runtime.grade_certification_contracts import CertificationOutcome
from bilqis_mlx.runtime.grade_certification_custody import load_certification_attempt
from bilqis_mlx.runtime.grade_certification_execution import execute_grade_certification
from bilqis_mlx.runtime.tests.certification.test_grade_certification_contracts import (
    _policy, _request,
)
from bilqis_mlx.runtime.tests.certification.test_grade_certification_execution import (
    _clean_score, _trigger,
)


def test_protected_prior_debt_may_hold_baseline_without_blocking_success(tmp_path):
    policy = _policy(debt_authority="ADR-084")
    request = _request(policy)
    result = execute_grade_certification(
        tmp_path, request, policy,
        trigger_measure=lambda: _trigger(prior=(9, 10)),
        obligation_measure=_clean_score,
        require_current=lambda: request,
    )
    assert result.status == "SUCCEEDED"
    assert result.receipt.outcome is CertificationOutcome.CERTIFIED_WITH_DEBT
    assert tuple(
        (item.owner, item.obligation_key) for item in result.receipt.debt
    ) == (("PROTECTED", "C.PRIOR"),)


def test_protected_prior_regression_is_a_typed_veto(tmp_path):
    policy = _policy(debt_authority="ADR-084")
    request = _request(policy)
    result = execute_grade_certification(
        tmp_path, request, policy,
        trigger_measure=lambda: _trigger(
            zeta=(10, 10), alpha=(10, 10), prior=(8, 10)),
        obligation_measure=lambda key: (_ for _ in ()).throw(
            AssertionError(f"protected regression must veto before {key}")),
        require_current=lambda: request,
    )
    assert result.status == "FAILED"
    assert tuple(
        (item.owner, item.obligation_key) for item in result.blockers
    ) == (("PROTECTED", "C.PRIOR"),)


def test_success_terminal_rejects_live_receipt_without_complete_results(tmp_path):
    request = _request()
    policy = _policy()
    from bilqis_mlx.runtime.grade_certification_contracts import (
        _issue_success_receipt,
    )
    from bilqis_mlx.runtime.grade_certification_custody import (
        start_certification_attempt,
        succeed_certification_attempt,
    )
    trigger = _trigger(zeta=(10, 10), alpha=(10, 10))
    start_certification_attempt(
        tmp_path, request, policy,
        trigger_cohort_sha256=trigger.cohort_sha256,
        trigger_scores=trigger.scores,
    )
    fabricated = _issue_success_receipt(
        request,
        outcome=CertificationOutcome.CERTIFIED_CLEAN,
        scores=trigger.scores,
        debt=(),
    )
    with pytest.raises(BilqisError):
        succeed_certification_attempt(tmp_path, request, fabricated)


def test_authority_drift_after_attempt_start_supersedes_without_next_write(tmp_path):
    request = _request()
    checks = 0

    def current():
        nonlocal checks
        checks += 1
        if checks >= 3:
            ErrorBus.Raise(
                SCHOOL.BAMF_CURRICULUM.INVALID,
                reason="BAMF_GRADE_CERTIFICATION_CURRENTNESS_DRIFT",
            )
        return request

    result = execute_grade_certification(
        tmp_path,
        request,
        _policy(),
        trigger_measure=lambda: _trigger(),
        obligation_measure=lambda key: _clean_score(key),
        require_current=current,
    )
    assert result.status == "SUPERSEDED"
    view = load_certification_attempt(tmp_path, request)
    assert view.next_cursor == 0
    assert view.supersession_reason == (
        "BAMF_GRADE_CERTIFICATION_CURRENTNESS_DRIFT")


def test_new_current_attempt_supersedes_stale_running_attempt_after_crash(tmp_path):
    stale = _request(checkpoint="c" * 64)
    current = _request(checkpoint="e" * 64)

    def crash_after_first_commit(key):
        if key == "C.ALPHA":
            return (_ for _ in ()).throw(
                RuntimeError("simulated authority-change crash"))
        return _clean_score(key)

    with pytest.raises(RuntimeError, match="authority-change crash"):
        execute_grade_certification(
            tmp_path, stale, _policy(), trigger_measure=lambda: _trigger(),
            obligation_measure=crash_after_first_commit,
            require_current=lambda: stale)
    assert load_certification_attempt(tmp_path, stale).status == "RUNNING"

    result = execute_grade_certification(
        tmp_path, current, _policy(), trigger_measure=lambda: _trigger(),
        obligation_measure=_clean_score, require_current=lambda: current)
    assert result.status == "SUCCEEDED"
    stale_view = load_certification_attempt(tmp_path, stale)
    assert stale_view.status == "SUPERSEDED"
    assert stale_view.supersession_reason == (
        "BAMF_GRADE_CERTIFICATION_CURRENTNESS_DRIFT")


def test_non_currentness_error_does_not_terminally_supersede_attempt(tmp_path):
    request = _request()
    checks = 0

    def current():
        nonlocal checks
        checks += 1
        if checks >= 3:
            ErrorBus.Raise(
                SCHOOL.BAMF_CURRICULUM.INVALID,
                reason="BAMF_GRADE_CERTIFICATION_CUSTODY_UNSAFE")
        return request

    with pytest.raises(BilqisError) as raised:
        execute_grade_certification(
            tmp_path, request, _policy(), trigger_measure=lambda: _trigger(),
            obligation_measure=_clean_score, require_current=current)
    assert raised.value.context["reason"] == (
        "BAMF_GRADE_CERTIFICATION_CUSTODY_UNSAFE")
    assert load_certification_attempt(tmp_path, request).status == "RUNNING"


def test_protected_prior_negative_utility_blocks_without_becoming_sweep_target(tmp_path):
    request = _request()
    result = execute_grade_certification(
        tmp_path,
        request,
        _policy(),
        trigger_measure=lambda: _trigger(
            zeta=(10, 10), alpha=(10, 10), prior=(8, 10)),
        obligation_measure=lambda key: (_ for _ in ()).throw(
            AssertionError(f"must not teach or sweep {key}")),
        require_current=lambda: request,
    )
    assert result.status == "FAILED"
    assert tuple(item.owner for item in result.blockers) == ("PROTECTED",)


def test_unbaselined_protected_obligation_never_becomes_regression_blocker(tmp_path):
    policy = _policy()
    request = _request(policy, protected_baselines=())
    result = execute_grade_certification(
        tmp_path,
        request,
        policy,
        trigger_measure=lambda: _trigger(
            zeta=(8, 10), alpha=(8, 10), prior=(1, 10)),
        obligation_measure=lambda key: (_ for _ in ()).throw(
            AssertionError(f"entry failure must stop before {key}")),
        require_current=lambda: request,
    )
    assert result.status == "FAILED"
    assert tuple(
        (item.owner, item.obligation_key) for item in result.blockers
    ) == (("ACTIVE", "C.ZETA"), ("ACTIVE", "C.ALPHA"))
