"""Policy selection and live authority snapshot helpers for #1334."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory import assessment_scope_contract

from .grade_certification_contracts import (
    CertificationObligationScore,
    GradeCertificationPolicy,
    GradeCertificationRequest,
    certification_policy,
)
from .grade_certification_custody import (
    load_certification_receipt,
    load_certification_request,
)


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def historical_mean_stability_policy() -> GradeCertificationPolicy:
    """One explicitly versioned ADR-084/111 fixture, never universal grade law."""
    return certification_policy(
        policy_id="adr-084-mean-stability/v1",
        policy_epoch=1,
        entry_threshold=(92, 100),
        continuation_threshold=(87, 100),
        retry_comparator_version="adr-111-unweighted-blocker-mean/v1",
        debt_authority="ADR-084",
    )


def _selected_progression_policy_sha256(run_dir: Path) -> str:
    """Read the C07 selector, preserving pre-selector accepted lineages."""
    from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
    from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_lease_v2

    root = Path(run_dir)
    source_authority = AcceptedRuntimeHost(root).source_authority()
    lease = read_accepted_atlas_lease_v2(
        root, source_authority=source_authority)
    if lease is None:
        # Accepted lineages created before #1334 had no C07 v2 policy selector.
        # They already trained under this explicitly versioned progression law;
        # absence of the later selector must not brick the retained learner.
        return historical_mean_stability_policy().policy_sha256
    return lease.source_approval.progression_policy_sha256


def resolve_grade_certification_policy(selected_sha256: str) -> GradeCertificationPolicy:
    """Resolve one signed C07 progression digest to an implemented policy body."""
    policies = (historical_mean_stability_policy(),)
    matches = tuple(
        policy for policy in policies
        if policy.policy_sha256 == selected_sha256)
    if len(matches) != 1:
        _invalid("BAMF_GRADE_CERTIFICATION_POLICY_SELECTION_UNSUPPORTED")
    return matches[0]


def _accepted_snapshot(run_dir: Path):
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest,
        accepted_generation,
    )
    root = Path(run_dir)
    pointer, student = accepted_generation(root / "bamf-state.json")
    manifest = pointer["manifest_sha256"]
    acceptance = pointer["acceptance_sha256"]
    accepted_binding_for_manifest(
        root, manifest, student,
        expected_acceptance_sha256=acceptance)
    from bilqis_mlx.runtime.atlas_flywheel_runtime import _accepted_checkpoint
    checkpoint = _accepted_checkpoint(root)
    return {
        "run_id": student.run_id,
        "generation": student.generation,
        "manifest_sha256": manifest,
        "acceptance_sha256": acceptance,
        "checkpoint_sha256": checkpoint.sha256,
        "optimizer_step": checkpoint.optimizer_step,
        "student": student,
    }


def _protected_evidence(
        run_dir: Path, active, active_obligations: tuple[str, ...], *,
        load_receipt=load_certification_receipt,
        load_request=load_certification_request):
    receipt_sha = active.definition.predecessor_certification_sha256
    if receipt_sha is None:
        return (), (), None
    receipt = load_receipt(run_dir, receipt_sha)
    predecessor = load_request(run_dir, receipt.attempt_sha256)
    active_keys = set(active_obligations)
    ordered = []
    seen = set()
    for score in receipt.scores:
        if score.obligation_key in active_keys or score.obligation_key in seen:
            continue
        seen.add(score.obligation_key)
        ordered.append(CertificationObligationScore(
            "PROTECTED", score.obligation_key, score.correct, score.total))
    protected = tuple(item.obligation_key for item in ordered)
    if not set(protected) <= set(predecessor.assessment_capabilities):
        _invalid("BAMF_GRADE_CERTIFICATION_PROTECTED_PROVENANCE_DRIFT")
    return protected, tuple(ordered), predecessor


def _comparable_baselines(ordered, predecessor, release, policy, scope):
    if predecessor is None or scope is None:
        return ()
    comparable = (
        predecessor.factory_release_sha256 == release.release_sha256
        and predecessor.semantic_catalog_sha256 == release.semantic_catalog_sha256
        and predecessor.policy_epoch == policy.policy_epoch
        and predecessor.policy_sha256 == policy.policy_sha256
        and predecessor.assessment_capabilities == scope.capabilities
        and predecessor.assessment_rubric_sha256 == scope.rubric_sha256
        and predecessor.assessment_source_sha256 == scope.source_sha256
        and predecessor.assessment_generator_version == scope.generator_version
        and predecessor.semantic_catalog_sha256 == scope.semantic_catalog_sha256)
    return ordered if comparable else ()


def protected_components(
        run_dir: Path, active, active_obligations: tuple[str, ...], release,
        policy: GradeCertificationPolicy, *, scope=None,
        load_receipt=load_certification_receipt,
        load_request=load_certification_request,
) -> tuple[tuple[str, ...], tuple[CertificationObligationScore, ...]]:
    """Return prior obligations and baselines only under exact measurement identity."""
    protected, ordered, predecessor = _protected_evidence(
        run_dir, active, active_obligations,
        load_receipt=load_receipt, load_request=load_request)
    return protected, _comparable_baselines(
        ordered, predecessor, release, policy, scope)


def request_values(request: GradeCertificationRequest) -> dict:
    return {
        "run_id": request.run_id,
        "boundary_disposition": request.boundary_disposition,
        "boundary_sha256": request.boundary_sha256,
        "cadence_sha256": request.cadence_sha256,
        "cadence_epoch": request.cadence_epoch,
        "member_census_sha256": request.member_census_sha256,
        "deficit_evidence_sha256": request.deficit_evidence_sha256,
        "active_grade_activation_sha256": request.active_grade_activation_sha256,
        "active_grade_definition_sha256": request.active_grade_definition_sha256,
        "accepted_generation": request.accepted_generation,
        "accepted_manifest_sha256": request.accepted_manifest_sha256,
        "accepted_acceptance_sha256": request.accepted_acceptance_sha256,
        "learner_checkpoint_sha256": request.learner_checkpoint_sha256,
        "optimizer_step": request.optimizer_step,
        "learner_evidence_epoch": request.learner_evidence_epoch,
        "factory_release_sha256": request.factory_release_sha256,
        "assessment_capabilities": request.assessment_capabilities,
        "assessment_rubric_sha256": request.assessment_rubric_sha256,
        "assessment_source_sha256": request.assessment_source_sha256,
        "assessment_generator_version": request.assessment_generator_version,
        "semantic_catalog_sha256": request.semantic_catalog_sha256,
        "active_obligations": request.active_obligations,
        "protected_obligations": request.protected_obligations,
        "protected_baselines": request.protected_baselines,
    }


def current_components(run_dir: Path, policy: GradeCertificationPolicy):
    from bilqis_mlx.runtime.active_generated_grade import read_active_generated_grade
    from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_factory_release
    from bilqis_mlx.runtime.atlas_flywheel_runtime import AcceptedAtlasFlywheelSupervisor

    active = read_active_generated_grade(Path(run_dir))
    accepted = _accepted_snapshot(Path(run_dir))
    release = read_accepted_atlas_factory_release(Path(run_dir))
    state = AcceptedAtlasFlywheelSupervisor(Path(run_dir), None).load_state()
    if (
        state.epoch.current_release.release_sha256 != release.release_sha256
        or state.learner_evidence.checkpoint_sha256 != accepted["checkpoint_sha256"]
        or state.learner_evidence.optimizer_step != accepted["optimizer_step"]
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_LEARNER_EVIDENCE_DRIFT")
    learner_evidence_epoch = state.epoch.snapshot.qualification_epoch
    active_obligations = tuple(
        member.capability_id for member in active.definition.members)
    protected, ordered, predecessor = _protected_evidence(
        Path(run_dir), active, active_obligations)
    requested_scope = tuple(dict.fromkeys((*active_obligations, *protected)))
    try:
        scope = assessment_scope_contract(release, requested_scope)
    except (TypeError, ValueError):
        _invalid("BAMF_GRADE_CERTIFICATION_ASSESSMENT_SCOPE_DRIFT")
    protected_baselines = _comparable_baselines(
        ordered, predecessor, release, policy, scope)
    policy.verify()
    return (
        active, accepted, release, active_obligations, protected,
        protected_baselines, scope, learner_evidence_epoch,
    )
