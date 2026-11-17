"""Generic #1334 state-machine witnesses independent of the MLX scorer."""
from dataclasses import dataclass

import pytest

from bilqis_mlx.runtime.grade_certification_contracts import (
    CertificationObligationScore,
    CertificationOutcome,
)
from bilqis_mlx.runtime.grade_certification_custody import (
    load_certification_attempt,
)
from bilqis_mlx.runtime.grade_certification_execution import (
    CertificationMeasurement,
    execute_grade_certification,
)
from bilqis_mlx.runtime.tests.certification.test_grade_certification_contracts import (
    _policy,
    _request,
)


def _trigger(*, zeta=(9, 10), alpha=(10, 10), prior=(10, 10)):
    return CertificationMeasurement(
        "1" * 64,
        (
            CertificationObligationScore("ACTIVE", "C.ZETA", *zeta),
            CertificationObligationScore("ACTIVE", "C.ALPHA", *alpha),
            CertificationObligationScore("PROTECTED", "C.PRIOR", *prior),
        ),
    )


def _clean_score(key):
    return CertificationMeasurement(
        ("2" if key == "C.ZETA" else "3") * 64,
        (CertificationObligationScore("ACTIVE", key, 10, 10),),
    )


def test_clean_attempt_sweeps_one_active_obligation_at_a_time(tmp_path):
    request = _request()
    seen = []
    result = execute_grade_certification(
        tmp_path,
        request,
        _policy(),
        trigger_measure=lambda: _trigger(),
        obligation_measure=lambda key: (seen.append(key) or _clean_score(key)),
        require_current=lambda: request,
    )
    assert result.status == "SUCCEEDED"
    assert result.receipt.outcome is CertificationOutcome.CERTIFIED_CLEAN
    assert seen == ["C.ZETA", "C.ALPHA"]
    view = load_certification_attempt(tmp_path, request)
    assert view.next_cursor == 2
    assert view.committed_cohort_sha256s == ("2" * 64, "3" * 64)


def test_same_engine_obeys_distinct_versioned_policy_thresholds(tmp_path):
    permissive = _policy(
        policy_id="generated-policy-permissive/v1",
        entry_threshold=(90, 100), continuation_threshold=(85, 100),
    )
    strict = _policy(
        policy_id="generated-policy-strict/v1",
        entry_threshold=(100, 100), continuation_threshold=(100, 100),
    )
    permissive_request = _request(permissive)
    strict_request = _request(strict)
    trigger = lambda: _trigger(zeta=(9, 10), alpha=(10, 10), prior=(10, 10))

    accepted = execute_grade_certification(
        tmp_path / "permissive", permissive_request, permissive,
        trigger_measure=trigger,
        obligation_measure=_clean_score,
        require_current=lambda: permissive_request,
    )
    rejected = execute_grade_certification(
        tmp_path / "strict", strict_request, strict,
        trigger_measure=trigger,
        obligation_measure=lambda key: (_ for _ in ()).throw(
            AssertionError(f"strict entry failure must stop before {key}")),
        require_current=lambda: strict_request,
    )
    assert accepted.status == "SUCCEEDED"
    assert rejected.status == "FAILED"


def test_crash_resume_never_rescores_committed_obligation(tmp_path):
    request = _request()
    calls = []

    def crashing(key):
        calls.append(key)
        if key == "C.ALPHA":
            return (_ for _ in ()).throw(RuntimeError("simulated crash"))
        return _clean_score(key)

    with pytest.raises(RuntimeError, match="simulated crash"):
        execute_grade_certification(
            tmp_path,
            request,
            _policy(),
            trigger_measure=lambda: _trigger(),
            obligation_measure=crashing,
            require_current=lambda: request,
        )
    assert calls == ["C.ZETA", "C.ALPHA"]

    resumed = []
    result = execute_grade_certification(
        tmp_path,
        request,
        _policy(),
        trigger_measure=lambda: (_ for _ in ()).throw(
            AssertionError("trigger must not redraw")),
        obligation_measure=lambda key: (
            resumed.append(key) or _clean_score(key)),
        require_current=lambda: request,
    )
    assert result.status == "SUCCEEDED"
    assert resumed == ["C.ALPHA"]


def test_resume_reapplies_entry_gate_after_crash_at_attempt_start(tmp_path):
    request = _request()
    policy = _policy()

    from bilqis_mlx.runtime.grade_certification_custody import (
        start_certification_attempt,
    )
    start_certification_attempt(
        tmp_path, request, policy,
        trigger_cohort_sha256="1" * 64,
        trigger_scores=_trigger(zeta=(1, 10), alpha=(1, 10)).scores,
    )

    result = execute_grade_certification(
        tmp_path, request, policy,
        trigger_measure=lambda: (_ for _ in ()).throw(
            AssertionError("resume must not redraw trigger")),
        obligation_measure=lambda key: (_ for _ in ()).throw(
            AssertionError(f"entry-ineligible resume must not score {key}")),
        require_current=lambda: request,
    )
    assert result.status == "FAILED"


def test_resume_reapplies_continuation_to_committed_prefix(tmp_path):
    request = _request()
    policy = _policy()
    from bilqis_mlx.runtime.grade_certification_custody import (
        commit_certification_result,
        start_certification_attempt,
    )
    start_certification_attempt(
        tmp_path, request, policy,
        trigger_cohort_sha256="1" * 64,
        trigger_scores=_trigger(zeta=(10, 10), alpha=(9, 10)).scores,
    )
    commit_certification_result(
        tmp_path, request,
        CertificationObligationScore("ACTIVE", "C.ZETA", 1, 10),
        cohort_sha256="4" * 64,
    )

    result = execute_grade_certification(
        tmp_path, request, policy,
        trigger_measure=lambda: (_ for _ in ()).throw(
            AssertionError("resume must not redraw trigger")),
        obligation_measure=lambda key: (_ for _ in ()).throw(
            AssertionError(f"failed prefix must not score {key}")),
        require_current=lambda: request,
    )
    assert result.status == "FAILED"


def test_continuation_failure_stops_before_next_obligation(tmp_path):
    request = _request()
    seen = []

    def score(key):
        seen.append(key)
        assert key == "C.ZETA"
        return CertificationMeasurement(
            "4" * 64,
            (CertificationObligationScore("ACTIVE", key, 1, 10),),
        )

    result = execute_grade_certification(
        tmp_path,
        request,
        _policy(),
        trigger_measure=lambda: _trigger(zeta=(10, 10), alpha=(9, 10)),
        obligation_measure=score,
        require_current=lambda: request,
    )
    assert result.status == "FAILED"
    assert seen == ["C.ZETA"]
    assert {item.obligation_key for item in result.blockers} == {
        "C.ZETA", "C.ALPHA"}


def test_imperfect_terminal_success_requires_policy_debt_authority(tmp_path):
    request = _request(_policy(debt_authority="ADR-084"))
    policy = _policy(debt_authority="ADR-084")

    def score(key):
        value = (9, 10) if key == "C.ZETA" else (10, 10)
        return CertificationMeasurement(
            ("5" if key == "C.ZETA" else "6") * 64,
            (CertificationObligationScore("ACTIVE", key, *value),),
        )

    result = execute_grade_certification(
        tmp_path,
        request,
        policy,
        trigger_measure=lambda: _trigger(),
        obligation_measure=score,
        require_current=lambda: request,
    )
    assert result.status == "SUCCEEDED"
    assert result.receipt.outcome is CertificationOutcome.CERTIFIED_WITH_DEBT
    assert tuple(item.obligation_key for item in result.receipt.debt) == (
        "C.ZETA",)
