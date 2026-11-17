"""Grade-neutral #1334 certification contract witnesses."""
from dataclasses import replace

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.grade_certification_contracts import (
    CertificationObligationScore,
    CertificationOutcome,
    _issue_certification_request,
    _issue_success_receipt,
    certification_policy,
    parse_certification_receipt,
    require_accepted_certification_receipt,
)


def _policy(
    *, policy_id="policy-a", entry_threshold=(92, 100),
    continuation_threshold=(87, 100), debt_authority=None,
):
    return certification_policy(
        policy_id=policy_id,
        policy_epoch=7,
        entry_threshold=entry_threshold,
        continuation_threshold=continuation_threshold,
        retry_comparator_version="adr-111-unweighted-blocker-mean/v1",
        debt_authority=debt_authority,
    )


def _request(
    policy=None, *, boundary_sha="b" * 64, checkpoint="c" * 64,
    protected_baselines=None,
):
    policy = policy or _policy()
    if protected_baselines is None:
        protected_baselines = (
            CertificationObligationScore("PROTECTED", "C.PRIOR", 9, 10),
        )
    return _issue_certification_request(
        run_id="run-fixture",
        boundary_disposition="GRADE_COMPLETE",
        boundary_sha256=boundary_sha,
        cadence_sha256="1" * 64,
        cadence_epoch=3,
        member_census_sha256="2" * 64,
        deficit_evidence_sha256="3" * 64,
        active_grade_activation_sha256="4" * 64,
        active_grade_definition_sha256="5" * 64,
        accepted_generation=11,
        accepted_manifest_sha256="6" * 64,
        accepted_acceptance_sha256="7" * 64,
        learner_checkpoint_sha256=checkpoint,
        optimizer_step=29,
        learner_evidence_epoch=13,
        factory_release_sha256="8" * 64,
        assessment_capabilities=("C.ZETA", "C.ALPHA", "C.PRIOR"),
        assessment_rubric_sha256="9" * 64,
        assessment_source_sha256="a" * 64,
        assessment_generator_version="generator/v2",
        semantic_catalog_sha256="d" * 64,
        policy=policy,
        active_obligations=("C.ZETA", "C.ALPHA"),
        protected_obligations=("C.PRIOR",),
        protected_baselines=protected_baselines,
    )


def test_unmeasured_protected_obligation_can_be_bound_without_regression_baseline():
    request = _request(protected_baselines=())
    assert request.protected_obligations == ("C.PRIOR",)
    assert request.protected_baselines == ()


def test_family_excludes_attempt_checkpoint_and_boundary_identity():
    first = _request()
    second = _request(boundary_sha="e" * 64, checkpoint="f" * 64)
    assert first.family_sha256 == second.family_sha256
    assert first.attempt_sha256 != second.attempt_sha256


def test_policy_identity_changes_family_without_grade_name_logic():
    first = _request(_policy(policy_id="policy-a"))
    second = _request(_policy(policy_id="policy-b"))
    assert first.family_sha256 != second.family_sha256


def test_success_receipt_is_live_issuer_only_and_preserves_debt_truth():
    request = _request(_policy(debt_authority="ADR-084"))
    scores = (
        CertificationObligationScore("ACTIVE", "C.ZETA", 9, 10),
        CertificationObligationScore("ACTIVE", "C.ALPHA", 10, 10),
        CertificationObligationScore("PROTECTED", "C.PRIOR", 10, 10),
    )
    receipt = _issue_success_receipt(
        request,
        outcome=CertificationOutcome.CERTIFIED_WITH_DEBT,
        scores=scores,
        debt=(scores[0],),
    )
    assert require_accepted_certification_receipt(receipt) is receipt
    parsed = parse_certification_receipt(receipt.to_record())
    with pytest.raises(BilqisError):
        require_accepted_certification_receipt(parsed)


def test_debt_success_requires_explicit_governing_authority():
    protected = CertificationObligationScore("PROTECTED", "C.PRIOR", 9, 10)
    active = CertificationObligationScore("ACTIVE", "C.ZETA", 9, 10)
    with pytest.raises(BilqisError) as failure:
        _issue_success_receipt(
            _request(),
            outcome=CertificationOutcome.CERTIFIED_WITH_DEBT,
            scores=(active, protected),
            debt=(active, protected),
        )
    assert failure.value.context.get("reason") == (
        "BAMF_GRADE_CERTIFICATION_DEBT_AUTHORITY_REQUIRED")


def test_policy_rejects_unimplemented_comparator_and_unaccepted_debt_authority():
    with pytest.raises(BilqisError):
        certification_policy(
            policy_id="bad-comparator", policy_epoch=1,
            entry_threshold=(92, 100), continuation_threshold=(87, 100),
            retry_comparator_version="not-adr-111",
        )
    with pytest.raises(BilqisError):
        certification_policy(
            policy_id="bad-protected-comparator", policy_epoch=1,
            entry_threshold=(92, 100), continuation_threshold=(87, 100),
            retry_comparator_version="adr-111-unweighted-blocker-mean/v1",
            protected_regression_version="not-adr-114-142",
        )
    with pytest.raises(BilqisError):
        certification_policy(
            policy_id="bad-debt", policy_epoch=1,
            entry_threshold=(92, 100), continuation_threshold=(87, 100),
            retry_comparator_version="adr-111-unweighted-blocker-mean/v1",
            debt_authority="NOT-A-GOVERNING-AUTHORITY",
        )


def test_debt_receipt_must_name_every_imperfect_active_obligation():
    request = _request(_policy(debt_authority="ADR-084"))
    first = CertificationObligationScore("ACTIVE", "C.ZETA", 9, 10)
    second = CertificationObligationScore("ACTIVE", "C.ALPHA", 8, 10)
    protected = CertificationObligationScore("PROTECTED", "C.PRIOR", 10, 10)
    with pytest.raises(BilqisError):
        _issue_success_receipt(
            request,
            outcome=CertificationOutcome.CERTIFIED_WITH_DEBT,
            scores=(first, second, protected),
            debt=(first,),
        )


def test_request_and_receipt_are_digest_tamper_evident():
    request = _request()
    with pytest.raises(BilqisError):
        replace(request, optimizer_step=request.optimizer_step + 1).verify()
    receipt = _issue_success_receipt(
        request,
        outcome=CertificationOutcome.CERTIFIED_CLEAN,
        scores=(
            CertificationObligationScore("ACTIVE", "C.ZETA", 10, 10),
            CertificationObligationScore("PROTECTED", "C.PRIOR", 10, 10),
        ),
        debt=(),
    )
    with pytest.raises(BilqisError):
        parse_certification_receipt({
            **receipt.to_record(),
            "request_sha256": "0" * 64,
        })
