"""Policy entry, continuation, and ADR-111 retry law."""
from __future__ import annotations

from fractions import Fraction

from .grade_certification_contracts import (
    CertificationObligationScore, GradeCertificationPolicy, GradeCertificationRequest,
)
from .grade_certification_policy import protected_regression_eligible
from .grade_certification_custody_common import (
    ATTEMPT_SCHEMA, _invalid, _read, _root, _scores_from_records,
)

def _mean(scores) -> Fraction:
    scores = tuple(scores)
    if not scores:
        return Fraction(0, 1)
    return sum(
        (Fraction(item.correct, item.total) for item in scores),
        Fraction(0, 1),
    ) / len(scores)


def policy_entry_eligible(
    policy: GradeCertificationPolicy,
    scores,
    protected_baselines=(),
) -> bool:
    policy.verify()
    scores = tuple(scores)
    active = tuple(item for item in scores if item.owner == "ACTIVE")
    if not active or not protected_regression_eligible(scores, protected_baselines):
        return False
    return _mean(active) >= Fraction(*policy.entry_threshold)


def policy_continuation_eligible(
    policy: GradeCertificationPolicy,
    scores,
    protected_baselines=(),
) -> bool:
    policy.verify()
    scores = tuple(scores)
    active = tuple(item for item in scores if item.owner == "ACTIVE")
    if not active or not protected_regression_eligible(scores, protected_baselines):
        return False
    return _mean(active) >= Fraction(*policy.continuation_threshold)


def _validate_snapshot(request, policy, scores) -> tuple[CertificationObligationScore, ...]:
    request.verify()
    policy.verify()
    if (
        request.policy_sha256 != policy.policy_sha256
        or request.policy_epoch != policy.policy_epoch
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_POLICY_DRIFT")
    scores = tuple(scores)
    keys = tuple((item.owner, item.obligation_key) for item in scores)
    expected = tuple(
        [("ACTIVE", item) for item in request.active_obligations]
        + [("PROTECTED", item) for item in request.protected_obligations])
    if len(set(keys)) != len(keys) or set(keys) != set(expected):
        _invalid("BAMF_GRADE_CERTIFICATION_TRIGGER_SCOPE_INVALID")
    return scores



def _failed_family_records(run_dir, family_sha256):
    attempts = _root(run_dir) / "attempts"
    if not attempts.exists():
        return ()
    found = []
    for directory in attempts.iterdir():
        if directory.is_symlink() or not directory.is_dir():
            _invalid("BAMF_GRADE_CERTIFICATION_CUSTODY_UNSAFE")
        terminal = directory / "terminal.json"
        if not terminal.exists():
            continue
        record = _read(
            terminal, "BAMF_GRADE_CERTIFICATION_TERMINAL_INVALID")
        if (
            record.get("family_sha256") == family_sha256
            and record.get("status") == "FAILED"
            and record.get("retry_baseline", True) is True
        ):
            attempt = _read(
                directory / "attempt.json",
                "BAMF_GRADE_CERTIFICATION_ATTEMPT_INVALID")
            request = attempt.get("request", {})
            found.append((request.get("cadence_epoch", -1), record))
    return tuple(sorted(found, key=lambda item: item[0]))


def retry_certification_eligible(
    run_dir: Path,
    request: GradeCertificationRequest,
    policy: GradeCertificationPolicy,
    current_scores,
) -> bool:
    current_scores = _validate_snapshot(request, policy, current_scores)
    if not policy_entry_eligible(
        policy, current_scores, request.protected_baselines):
        return False
    failures = _failed_family_records(run_dir, request.family_sha256)
    if not failures:
        return True
    baseline = _scores_from_records(failures[-1][1].get("blockers", ()))
    by_key = {
        (item.owner, item.obligation_key): item for item in current_scores}
    try:
        compared = tuple(
            by_key[(item.owner, item.obligation_key)] for item in baseline)
    except KeyError:
        return False
    return _mean(compared) > _mean(baseline)
