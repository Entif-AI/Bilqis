"""Live-vs-cold authority witnesses for #1334 currentness."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.grade_certification import (
    _protected_components,
    historical_mean_stability_policy,
    require_current_accepted_certification_receipt,
    require_current_grade_certification_request,
    selected_grade_certification_policy,
)
from bilqis_mlx.runtime.grade_certification_contracts import (
    CertificationObligationScore,
    CertificationOutcome,
    _issue_success_receipt,
    require_accepted_certification_receipt,
)
from bilqis_mlx.runtime.grade_certification_custody import (
    commit_certification_result,
    start_certification_attempt,
    succeed_certification_attempt,
)
from bilqis_mlx.runtime.tests.certification.test_grade_certification_contracts import (
    _policy,
    _request,
)


def test_c07_progression_digest_selects_exact_implemented_policy():
    policy = historical_mean_stability_policy()
    with patch(
        "bilqis_mlx.runtime.grade_certification._selected_progression_policy_sha256",
        return_value=policy.policy_sha256,
    ):
        assert selected_grade_certification_policy("/unused") == policy


def test_preselector_accepted_lineage_uses_versioned_compatibility_policy():
    policy = historical_mean_stability_policy()
    source_authority = object()
    with (
        patch(
            "bilqis_mlx.runtime.accepted_corrections.AcceptedRuntimeHost",
        ) as accepted_host,
        patch(
            "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_lease_v2",
            return_value=None,
        ) as read_lease,
    ):
        accepted_host.return_value.source_authority.return_value = source_authority
        assert selected_grade_certification_policy("/legacy-run") == policy
    read_lease.assert_called_once_with(
        Path("/legacy-run"), source_authority=source_authority)


def test_unknown_c07_progression_digest_does_not_default_historical_fixture():
    with pytest.raises(BilqisError) as failure:
        with patch(
            "bilqis_mlx.runtime.grade_certification._selected_progression_policy_sha256",
            return_value="f" * 64,
        ):
            selected_grade_certification_policy("/unused")
    assert failure.value.context.get("reason") == (
        "BAMF_GRADE_CERTIFICATION_POLICY_SELECTION_UNSUPPORTED")


def test_prior_certified_obligations_survive_when_regression_baseline_is_not_comparable():
    policy = _policy()
    active = SimpleNamespace(definition=SimpleNamespace(
        predecessor_certification_sha256="a" * 64))
    receipt = SimpleNamespace(
        attempt_sha256="b" * 64,
        scores=(
            CertificationObligationScore("ACTIVE", "C.PRIOR", 9, 10),
            CertificationObligationScore("ACTIVE", "C.NOW", 10, 10),
        ),
    )
    predecessor = SimpleNamespace(
        assessment_capabilities=("C.PRIOR", "C.NOW"),
        assessment_rubric_sha256="4" * 64,
        assessment_source_sha256="5" * 64,
        assessment_generator_version="generator/v2",
        factory_release_sha256="1" * 64,
        semantic_catalog_sha256="2" * 64,
        policy_epoch=policy.policy_epoch,
        policy_sha256=policy.policy_sha256,
    )
    release = SimpleNamespace(
        release_sha256="3" * 64,
        semantic_catalog_sha256="2" * 64,
    )
    scope = SimpleNamespace(
        capabilities=("C.NOW", "C.PRIOR"), rubric_sha256="4" * 64,
        source_sha256="5" * 64, generator_version="generator/v2",
        semantic_catalog_sha256="2" * 64)
    with (
        patch(
            "bilqis_mlx.runtime.grade_certification.load_certification_receipt",
            return_value=receipt,
        ),
        patch(
            "bilqis_mlx.runtime.grade_certification.load_certification_request",
            return_value=predecessor,
        ),
    ):
        protected, baselines = _protected_components(
            "/unused", active, ("C.NOW",), release, policy, scope=scope)
    assert protected == ("C.PRIOR",)
    assert baselines == ()


def test_comparable_prior_certified_obligation_becomes_quadratic_baseline():
    policy = _policy()
    active = SimpleNamespace(definition=SimpleNamespace(
        predecessor_certification_sha256="a" * 64))
    receipt = SimpleNamespace(
        attempt_sha256="b" * 64,
        scores=(CertificationObligationScore("ACTIVE", "C.PRIOR", 9, 10),),
    )
    predecessor = SimpleNamespace(
        assessment_capabilities=("C.PRIOR",),
        assessment_rubric_sha256="4" * 64,
        assessment_source_sha256="5" * 64,
        assessment_generator_version="generator/v2",
        factory_release_sha256="1" * 64,
        semantic_catalog_sha256="2" * 64,
        policy_epoch=policy.policy_epoch,
        policy_sha256=policy.policy_sha256,
    )
    release = SimpleNamespace(
        release_sha256="1" * 64,
        semantic_catalog_sha256="2" * 64,
    )
    scope = SimpleNamespace(
        capabilities=("C.PRIOR",), rubric_sha256="4" * 64,
        source_sha256="5" * 64, generator_version="generator/v2",
        semantic_catalog_sha256="2" * 64)
    with (
        patch(
            "bilqis_mlx.runtime.grade_certification.load_certification_receipt",
            return_value=receipt,
        ),
        patch(
            "bilqis_mlx.runtime.grade_certification.load_certification_request",
            return_value=predecessor,
        ),
    ):
        protected, baselines = _protected_components(
            "/unused", active, (), release, policy, scope=scope)
    assert protected == ("C.PRIOR",)
    assert baselines == (
        CertificationObligationScore("PROTECTED", "C.PRIOR", 9, 10),)


def test_noncomparable_assessment_identity_never_becomes_regression_baseline():
    policy = _policy()
    active = SimpleNamespace(definition=SimpleNamespace(
        predecessor_certification_sha256="a" * 64))
    receipt = SimpleNamespace(
        attempt_sha256="b" * 64,
        scores=(CertificationObligationScore("ACTIVE", "C.PRIOR", 9, 10),))
    predecessor = SimpleNamespace(
        assessment_capabilities=("C.PRIOR",),
        assessment_rubric_sha256="4" * 64,
        assessment_source_sha256="5" * 64,
        assessment_generator_version="generator/v2",
        factory_release_sha256="1" * 64,
        semantic_catalog_sha256="2" * 64,
        policy_epoch=policy.policy_epoch,
        policy_sha256=policy.policy_sha256)
    release = SimpleNamespace(
        release_sha256="1" * 64, semantic_catalog_sha256="2" * 64)
    drifted_scope = SimpleNamespace(
        capabilities=("C.PRIOR",), rubric_sha256="6" * 64,
        source_sha256="5" * 64, generator_version="generator/v2",
        semantic_catalog_sha256="2" * 64)
    with (
        patch(
            "bilqis_mlx.runtime.grade_certification.load_certification_receipt",
            return_value=receipt),
        patch(
            "bilqis_mlx.runtime.grade_certification.load_certification_request",
            return_value=predecessor),
    ):
        protected, baselines = _protected_components(
            "/unused", active, (), release, policy, scope=drifted_scope)
    assert protected == ("C.PRIOR",)
    assert baselines == ()


def _components(request):
    active = SimpleNamespace(
        activation_sha256=request.active_grade_activation_sha256,
        definition=SimpleNamespace(
            definition_sha256=request.active_grade_definition_sha256,
            learner_evidence_epoch=request.learner_evidence_epoch,
        ),
    )
    accepted = {
        "run_id": request.run_id,
        "generation": request.accepted_generation,
        "manifest_sha256": request.accepted_manifest_sha256,
        "acceptance_sha256": request.accepted_acceptance_sha256,
        "checkpoint_sha256": request.learner_checkpoint_sha256,
        "optimizer_step": request.optimizer_step,
    }
    release = SimpleNamespace(release_sha256=request.factory_release_sha256)
    scope = SimpleNamespace(
        capabilities=request.assessment_capabilities,
        rubric_sha256=request.assessment_rubric_sha256,
        source_sha256=request.assessment_source_sha256,
        generator_version=request.assessment_generator_version,
        semantic_catalog_sha256=request.semantic_catalog_sha256,
    )
    return (
        active, accepted, release, request.active_obligations,
        request.protected_obligations, request.protected_baselines,
        scope, request.learner_evidence_epoch,
    )


def _cadence(request):
    return SimpleNamespace(
        run_id=request.run_id,
        cadence_sha256=request.cadence_sha256,
        cadence_epoch=request.cadence_epoch,
        member_census_sha256=request.member_census_sha256,
        deficit_evidence_sha256=request.deficit_evidence_sha256,
    )


def test_current_request_reissues_live_authority_only_when_every_owner_matches():
    request = _request()
    with (
        patch(
            "bilqis_mlx.runtime.grade_certification._current_components",
            return_value=_components(request),
        ),
        patch(
            "bilqis_mlx.runtime.active_grade_cadence_custody.read_current_cadence",
            return_value=_cadence(request),
        ),
        patch(
            "bilqis_mlx.runtime.grade_certification.selected_grade_certification_policy",
            return_value=_policy(),
        ),
    ):
        live = require_current_grade_certification_request(
            "/unused", request, _policy())
    assert live.request_sha256 == request.request_sha256
    assert getattr(live, "_issuance", None) is not None


def test_current_request_rejects_checkpoint_or_boundary_drift():
    request = _request()
    drifted = list(_components(request))
    drifted[1] = {**drifted[1], "checkpoint_sha256": "0" * 64}
    with (
        patch(
            "bilqis_mlx.runtime.grade_certification._current_components",
            return_value=tuple(drifted),
        ),
        patch(
            "bilqis_mlx.runtime.active_grade_cadence_custody.read_current_cadence",
            return_value=_cadence(request),
        ),
        patch(
            "bilqis_mlx.runtime.grade_certification.selected_grade_certification_policy",
            return_value=_policy(),
        ),
        pytest.raises(BilqisError) as failure,
    ):
        require_current_grade_certification_request(
            "/unused", request, _policy())
    assert failure.value.context.get("reason") == (
        "BAMF_GRADE_CERTIFICATION_CURRENTNESS_DRIFT")


def test_cold_success_receipt_requires_currentness_before_live_reissue(tmp_path):
    request = _request()
    policy = _policy()
    scores = (
        CertificationObligationScore("ACTIVE", "C.ZETA", 10, 10),
        CertificationObligationScore("ACTIVE", "C.ALPHA", 10, 10),
        CertificationObligationScore("PROTECTED", "C.PRIOR", 10, 10),
    )
    start_certification_attempt(
        tmp_path, request, policy, trigger_cohort_sha256="1" * 64,
        trigger_scores=scores)
    for score in scores:
        if score.owner == "ACTIVE":
            commit_certification_result(
                tmp_path, request, score, cohort_sha256="3" * 64)
    receipt = _issue_success_receipt(
        request, outcome=CertificationOutcome.CERTIFIED_CLEAN,
        scores=scores, debt=())
    succeed_certification_attempt(tmp_path, request, receipt)

    with (
        patch(
            "bilqis_mlx.runtime.grade_certification._current_components",
            return_value=_components(request),
        ),
        patch(
            "bilqis_mlx.runtime.active_grade_cadence_custody.read_current_cadence",
            return_value=_cadence(request),
        ),
        patch(
            "bilqis_mlx.runtime.grade_certification.selected_grade_certification_policy",
            return_value=policy,
        ),
    ):
        live = require_current_accepted_certification_receipt(
            tmp_path, receipt.receipt_sha256)
    assert require_accepted_certification_receipt(live) is live

    bad = _cadence(request)
    bad.cadence_sha256 = "0" * 64
    with (
        patch(
            "bilqis_mlx.runtime.grade_certification._current_components",
            return_value=_components(request),
        ),
        patch(
            "bilqis_mlx.runtime.active_grade_cadence_custody.read_current_cadence",
            return_value=bad,
        ),
        patch(
            "bilqis_mlx.runtime.grade_certification.selected_grade_certification_policy",
            return_value=policy,
        ),
        pytest.raises(BilqisError),
    ):
        require_current_accepted_certification_receipt(
            tmp_path, receipt.receipt_sha256)
