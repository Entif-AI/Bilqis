"""Crash/retry custody witnesses for #1334."""
import json

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.grade_certification_contracts import (
    CertificationObligationScore,
    CertificationOutcome,
    _issue_success_receipt,
    parse_certification_receipt,
)
from bilqis_mlx.runtime.grade_certification_custody import (
    certification_receipt_for_predecessor,
    certification_receipts_for_predecessor,
    commit_certification_result,
    fail_certification_attempt,
    load_certification_attempt,
    load_certification_receipt,
    policy_entry_eligible,
    retry_certification_eligible,
    start_certification_attempt,
    succeed_certification_attempt,
    supersede_certification_attempt,
)
from bilqis_mlx.runtime.tests.certification.test_grade_certification_contracts import (
    _policy,
    _request,
)


def _scores(active=(9, 10), protected=(10, 10)):
    return (
        CertificationObligationScore("ACTIVE", "C.ZETA", *active),
        CertificationObligationScore("ACTIVE", "C.ALPHA", 10, 10),
        CertificationObligationScore("PROTECTED", "C.PRIOR", *protected),
    )


def test_crash_after_result_custody_heals_cursor_without_rescoring(tmp_path):
    request = _request()
    start_certification_attempt(
        tmp_path, request, _policy(), trigger_cohort_sha256="1" * 64,
        trigger_scores=_scores())
    first = CertificationObligationScore("ACTIVE", "C.ZETA", 10, 10)
    commit_certification_result(
        tmp_path, request, first, cohort_sha256="2" * 64)

    pointer = tmp_path / "grade-certification" / "current.json"
    payload = json.loads(pointer.read_text())
    payload["next_cursor"] = 0
    pointer.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")

    resumed = load_certification_attempt(tmp_path, request)
    assert resumed.next_cursor == 1
    assert resumed.committed_scores == (first,)
    assert json.loads(pointer.read_text())["next_cursor"] == 1

    # Duplicate replay is idempotent; a different score at the same cursor is not.
    assert commit_certification_result(
        tmp_path, request, first, cohort_sha256="2" * 64).next_cursor == 1
    with pytest.raises(BilqisError):
        commit_certification_result(
            tmp_path, request,
            CertificationObligationScore("ACTIVE", "C.ZETA", 9, 10),
            cohort_sha256="2" * 64)


def test_same_family_retry_ignores_checkpoint_churn_until_blocker_mean_improves(tmp_path):
    failed_request = _request(checkpoint="c" * 64)
    policy = _policy()
    start_certification_attempt(
        tmp_path, failed_request, policy, trigger_cohort_sha256="1" * 64,
        trigger_scores=_scores())
    blockers = (
        CertificationObligationScore("ACTIVE", "C.ZETA", 8, 10),
        CertificationObligationScore("ACTIVE", "C.ALPHA", 9, 10),
    )
    fail_certification_attempt(tmp_path, failed_request, blockers)

    changed_checkpoint = _request(
        checkpoint="f" * 64, boundary_sha="e" * 64)
    assert changed_checkpoint.family_sha256 == failed_request.family_sha256
    assert not retry_certification_eligible(
        tmp_path, changed_checkpoint, policy, (
            CertificationObligationScore("ACTIVE", "C.ZETA", 8, 10),
            CertificationObligationScore("ACTIVE", "C.ALPHA", 9, 10),
            CertificationObligationScore("PROTECTED", "C.PRIOR", 10, 10),
        ))
    assert retry_certification_eligible(
        tmp_path, changed_checkpoint, policy, (
            CertificationObligationScore("ACTIVE", "C.ZETA", 10, 10),
            CertificationObligationScore("ACTIVE", "C.ALPHA", 9, 10),
            CertificationObligationScore("PROTECTED", "C.PRIOR", 10, 10),
        ))


def test_ineligible_retry_failure_does_not_poison_adr111_baseline(tmp_path):
    policy = _policy()
    original = _request(checkpoint="c" * 64)
    start_certification_attempt(
        tmp_path, original, policy, trigger_cohort_sha256="1" * 64,
        trigger_scores=_scores())
    fail_certification_attempt(
        tmp_path, original, (
            CertificationObligationScore("ACTIVE", "C.ZETA", 9, 10),
            CertificationObligationScore("ACTIVE", "C.ALPHA", 9, 10),
        ))

    denied = _request(checkpoint="d" * 64, boundary_sha="e" * 64)
    start_certification_attempt(
        tmp_path, denied, policy, trigger_cohort_sha256="2" * 64,
        trigger_scores=(
            CertificationObligationScore("ACTIVE", "C.ZETA", 8, 10),
            CertificationObligationScore("ACTIVE", "C.ALPHA", 10, 10),
            CertificationObligationScore("PROTECTED", "C.PRIOR", 10, 10),
        ))
    fail_certification_attempt(
        tmp_path, denied, (
            CertificationObligationScore("ACTIVE", "C.ZETA", 8, 10),
        ), retry_baseline=False)

    third = _request(checkpoint="f" * 64, boundary_sha="a" * 64)
    assert not retry_certification_eligible(
        tmp_path, third, policy, (
            CertificationObligationScore("ACTIVE", "C.ZETA", 9, 10),
            CertificationObligationScore("ACTIVE", "C.ALPHA", 9, 10),
            CertificationObligationScore("PROTECTED", "C.PRIOR", 10, 10),
        ))


def test_protected_prior_uses_quadratic_debt_utility_for_entry():
    policy = _policy(debt_authority="ADR-084")
    baselines = (
        CertificationObligationScore("PROTECTED", "C.PRIOR", 99, 100),
        CertificationObligationScore("PROTECTED", "C.WEAK", 70, 100),
    )
    assert policy_entry_eligible(
        policy, (
            CertificationObligationScore("ACTIVE", "C.ZETA", 10, 10),
            CertificationObligationScore("PROTECTED", "C.PRIOR", 97, 100),
            CertificationObligationScore("PROTECTED", "C.WEAK", 80, 100),
        ), baselines)
    assert not policy_entry_eligible(
        policy, (
            CertificationObligationScore("ACTIVE", "C.ZETA", 10, 10),
            CertificationObligationScore("PROTECTED", "C.PRIOR", 97, 100),
            CertificationObligationScore("PROTECTED", "C.WEAK", 69, 100),
        ), baselines)
    assert policy_entry_eligible(
        policy, (
            CertificationObligationScore("ACTIVE", "C.ZETA", 10, 10),
            CertificationObligationScore("PROTECTED", "C.PRIOR", 1, 10),
        ), ())


def test_different_policy_family_does_not_compare_old_retry_baseline(tmp_path):
    first = _request(_policy(policy_id="old"))
    start_certification_attempt(
        tmp_path, first, _policy(policy_id="old"),
        trigger_cohort_sha256="1" * 64, trigger_scores=_scores())
    fail_certification_attempt(
        tmp_path, first,
        (CertificationObligationScore("ACTIVE", "C.ZETA", 8, 10),))

    changed = _request(_policy(policy_id="new"))
    assert changed.family_sha256 != first.family_sha256
    assert retry_certification_eligible(
        tmp_path, changed, _policy(policy_id="new"), _scores())


def test_success_terminal_persists_receipt_but_cold_bytes_are_not_live_authority(tmp_path):
    request = _request()
    policy = _policy()
    trigger = _scores(active=(10, 10))
    start_certification_attempt(
        tmp_path, request, policy, trigger_cohort_sha256="1" * 64,
        trigger_scores=trigger)
    for score in trigger:
        if score.owner == "ACTIVE":
            commit_certification_result(
                tmp_path, request, score, cohort_sha256="3" * 64)
    receipt = _issue_success_receipt(
        request, outcome=CertificationOutcome.CERTIFIED_CLEAN,
        scores=trigger, debt=())

    terminal = succeed_certification_attempt(tmp_path, request, receipt)
    assert terminal.status == "SUCCEEDED"
    assert terminal.receipt_sha256 == receipt.receipt_sha256

    parsed = load_certification_receipt(
        tmp_path, receipt.receipt_sha256)
    assert parsed.to_record() == receipt.to_record()
    assert getattr(parsed, "_issuance", None) is None


def test_parsed_historical_receipt_cannot_terminalize_success(tmp_path):
    request = _request()
    policy = _policy()
    trigger = _scores(active=(10, 10))
    start_certification_attempt(
        tmp_path, request, policy, trigger_cohort_sha256="1" * 64,
        trigger_scores=trigger)
    for score in trigger:
        if score.owner == "ACTIVE":
            commit_certification_result(
                tmp_path, request, score, cohort_sha256="3" * 64)
    live = _issue_success_receipt(
        request, outcome=CertificationOutcome.CERTIFIED_CLEAN,
        scores=trigger, debt=())
    parsed = parse_certification_receipt(live.to_record())
    with pytest.raises(BilqisError) as failure:
        succeed_certification_attempt(tmp_path, request, parsed)
    assert failure.value.context.get("reason") == (
        "BAMF_GRADE_CERTIFICATION_RECEIPT_AUTHORITY_REQUIRED")


def test_exact_predecessor_receipt_remains_resolvable_with_multiple_historical_successes(
    tmp_path,
):
    policy = _policy()
    receipts = []
    for request, cohort in (
        (_request(boundary_sha="b" * 64, checkpoint="c" * 64), "1" * 64),
        (_request(boundary_sha="e" * 64, checkpoint="f" * 64), "2" * 64),
    ):
        trigger = _scores(active=(10, 10))
        start_certification_attempt(
            tmp_path, request, policy,
            trigger_cohort_sha256=cohort, trigger_scores=trigger)
        for score in trigger:
            if score.owner == "ACTIVE":
                commit_certification_result(
                    tmp_path, request, score, cohort_sha256="3" * 64)
        receipt = _issue_success_receipt(
            request, outcome=CertificationOutcome.CERTIFIED_CLEAN,
            scores=trigger, debt=())
        succeed_certification_attempt(tmp_path, request, receipt)
        receipts.append(receipt)

    found = certification_receipts_for_predecessor(
        tmp_path,
        activation_sha256=receipts[0].predecessor_activation_sha256,
        definition_sha256=receipts[0].predecessor_definition_sha256,
    )
    assert {item.receipt_sha256 for item in found} == {
        item.receipt_sha256 for item in receipts}
    with pytest.raises(BilqisError):
        certification_receipt_for_predecessor(
            tmp_path,
            activation_sha256=receipts[0].predecessor_activation_sha256,
            definition_sha256=receipts[0].predecessor_definition_sha256,
        )
    exact = certification_receipt_for_predecessor(
        tmp_path,
        activation_sha256=receipts[0].predecessor_activation_sha256,
        definition_sha256=receipts[0].predecessor_definition_sha256,
        receipt_sha256=receipts[1].receipt_sha256,
    )
    assert exact.receipt_sha256 == receipts[1].receipt_sha256


def test_supersession_is_terminal_and_preserves_committed_results(tmp_path):
    request = _request()
    start_certification_attempt(
        tmp_path, request, _policy(), trigger_cohort_sha256="1" * 64,
        trigger_scores=_scores())
    first = CertificationObligationScore("ACTIVE", "C.ZETA", 10, 10)
    commit_certification_result(
        tmp_path, request, first, cohort_sha256="4" * 64)
    superseded = supersede_certification_attempt(
        tmp_path, request, reason="ACTIVE_GRADE_DRIFT")

    assert superseded.status == "SUPERSEDED"
    assert superseded.committed_scores == (first,)
    with pytest.raises(BilqisError):
        commit_certification_result(
            tmp_path, request,
            CertificationObligationScore("ACTIVE", "C.ALPHA", 10, 10),
            cohort_sha256="5" * 64)
