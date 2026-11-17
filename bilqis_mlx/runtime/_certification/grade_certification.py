"""Live #1334 authority composition for generic grade-boundary certification."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL
from .grade_certification_contracts import (
    GradeCertificationPolicy, GradeCertificationRequest,
    _issue_certification_request, _issue_success_receipt,
    require_accepted_certification_receipt)
from .grade_certification_custody import (
    inspect_certification_attempt, load_certification_receipt,
    load_certification_request)
from .grade_certification_authority import (
    _selected_progression_policy_sha256,
    current_components as _current_components,
    historical_mean_stability_policy,
    protected_components as _protected_components_impl,
    request_values as _request_values,
    resolve_grade_certification_policy as _resolve_grade_certification_policy)
def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def selected_grade_certification_policy(run_dir: Path) -> GradeCertificationPolicy:
    return _resolve_grade_certification_policy(
        _selected_progression_policy_sha256(Path(run_dir)))


def _protected_components(
        run_dir, active, active_obligations, release, policy, *, scope=None):
    return _protected_components_impl(
        run_dir, active, active_obligations, release, policy,
        scope=scope,
        load_receipt=load_certification_receipt, load_request=load_certification_request)


def issue_grade_certification_request(
    run_dir: Path,
    priority_result,
    policy: GradeCertificationPolicy,
) -> GradeCertificationRequest | None:
    """Issue only from one live #1333 boundary retained by an issued result."""
    from bilqis_mlx.runtime.active_grade_certification_handoff import (
        certification_boundary_from_priority_result,
        require_current_certification_boundary,
    )
    from bilqis_mlx.runtime.accepted_priority_visit_contracts import (
        require_priority_lawful_frontier,
    )
    from bilqis_mlx.runtime.lawful_teaching_frontier import (
        require_current_lawful_teaching_frontier,
    )
    root = Path(run_dir)
    boundary = certification_boundary_from_priority_result(priority_result)
    if boundary is None:
        return None
    if selected_grade_certification_policy(root) != policy:
        _invalid("BAMF_GRADE_CERTIFICATION_POLICY_SELECTION_DRIFT")
    require_current_certification_boundary(root, boundary)
    frontier = require_priority_lawful_frontier(priority_result)
    require_current_lawful_teaching_frontier(
        frontier, frontier._source_context, frontier._parent)
    (
        active, accepted, release, active_obligations, protected,
        protected_baselines, scope,
        learner_evidence_epoch,
    ) = (
        _current_components(root, policy))
    if (
        boundary.run_id != frontier.run_id
        or boundary.run_id != accepted["run_id"]
        or boundary.active_grade_activation_sha256 != active.activation_sha256
        or boundary.active_grade_definition_sha256
           != active.definition.definition_sha256
        or frontier.active_grade_activation_sha256 != active.activation_sha256
        or frontier.active_grade_definition_sha256
           != active.definition.definition_sha256
        or frontier.accepted_generation != accepted["generation"]
        or frontier.accepted_manifest_sha256 != accepted["manifest_sha256"]
        or frontier.accepted_checkpoint_sha256 != accepted["checkpoint_sha256"]
        or frontier.accepted_optimizer_step != accepted["optimizer_step"]
        or frontier.admitted_release_sha256 != release.release_sha256
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_UPSTREAM_AUTHORITY_DRIFT")
    return _issue_certification_request(
        run_id=boundary.run_id,
        boundary_disposition=boundary.disposition.value,
        boundary_sha256=boundary.boundary_sha256,
        cadence_sha256=boundary.cadence_sha256,
        cadence_epoch=boundary.cadence_epoch,
        member_census_sha256=boundary.member_census_sha256,
        deficit_evidence_sha256=boundary.deficit_evidence_sha256,
        active_grade_activation_sha256=active.activation_sha256,
        active_grade_definition_sha256=active.definition.definition_sha256,
        accepted_generation=accepted["generation"],
        accepted_manifest_sha256=accepted["manifest_sha256"],
        accepted_acceptance_sha256=accepted["acceptance_sha256"],
        learner_checkpoint_sha256=accepted["checkpoint_sha256"],
        optimizer_step=accepted["optimizer_step"],
        learner_evidence_epoch=learner_evidence_epoch,
        factory_release_sha256=release.release_sha256,
        assessment_capabilities=scope.capabilities,
        assessment_rubric_sha256=scope.rubric_sha256,
        assessment_source_sha256=scope.source_sha256,
        assessment_generator_version=scope.generator_version,
        semantic_catalog_sha256=scope.semantic_catalog_sha256,
        policy=policy,
        active_obligations=active_obligations,
        protected_obligations=protected,
        protected_baselines=protected_baselines,
    )


def require_current_grade_certification_request(
    run_dir: Path,
    request: GradeCertificationRequest,
    policy: GradeCertificationPolicy,
) -> GradeCertificationRequest:
    """Re-prove every mutable authority bound by one persisted attempt."""
    request.verify()
    if selected_grade_certification_policy(Path(run_dir)) != policy:
        _invalid("BAMF_GRADE_CERTIFICATION_POLICY_SELECTION_DRIFT")
    from bilqis_mlx.runtime.active_grade_cadence_custody import (
        read_current_cadence,
    )
    current_cadence = read_current_cadence(Path(run_dir))
    (
        active, accepted, release, active_obligations, protected,
        protected_baselines, scope,
        learner_evidence_epoch,
    ) = _current_components(Path(run_dir), policy)
    if (
        current_cadence is None
        or current_cadence.run_id != request.run_id
        or current_cadence.cadence_sha256 != request.cadence_sha256
        or current_cadence.cadence_epoch != request.cadence_epoch
        or current_cadence.member_census_sha256 != request.member_census_sha256
        or current_cadence.deficit_evidence_sha256
           != request.deficit_evidence_sha256
        or active.activation_sha256 != request.active_grade_activation_sha256
        or active.definition.definition_sha256
           != request.active_grade_definition_sha256
        or accepted["run_id"] != request.run_id
        or accepted["generation"] != request.accepted_generation
        or accepted["manifest_sha256"] != request.accepted_manifest_sha256
        or accepted["acceptance_sha256"] != request.accepted_acceptance_sha256
        or accepted["checkpoint_sha256"] != request.learner_checkpoint_sha256
        or accepted["optimizer_step"] != request.optimizer_step
        or learner_evidence_epoch != request.learner_evidence_epoch
        or release.release_sha256 != request.factory_release_sha256
        or scope.capabilities != request.assessment_capabilities
        or scope.rubric_sha256 != request.assessment_rubric_sha256
        or scope.source_sha256 != request.assessment_source_sha256
        or scope.generator_version != request.assessment_generator_version
        or scope.semantic_catalog_sha256 != request.semantic_catalog_sha256
        or policy.policy_epoch != request.policy_epoch
        or policy.policy_sha256 != request.policy_sha256
        or policy.debt_authority != request.debt_authority
        or active_obligations != request.active_obligations
        or protected != request.protected_obligations
        or protected_baselines != request.protected_baselines
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_CURRENTNESS_DRIFT")
    live = _issue_certification_request(
        **_request_values(request), policy=policy)
    if live.request_sha256 != request.request_sha256:
        _invalid("BAMF_GRADE_CERTIFICATION_REQUEST_REISSUE_DRIFT")
    return live


def require_current_accepted_certification_receipt(
    run_dir: Path,
    receipt_sha256: str,
):
    """Reconstitute live authority from accepted bytes only after currentness proof."""
    root = Path(run_dir)
    parsed_receipt = load_certification_receipt(root, receipt_sha256)
    parsed_request = load_certification_request(
        root, parsed_receipt.attempt_sha256)
    view = inspect_certification_attempt(root, parsed_request)
    if (
        view.status != "SUCCEEDED"
        or view.receipt_sha256 != receipt_sha256
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_SUCCESS_CUSTODY_REQUIRED")
    live_request = require_current_grade_certification_request(
        root, parsed_request, view.policy)
    live_receipt = _issue_success_receipt(
        live_request, outcome=parsed_receipt.outcome,
        scores=parsed_receipt.scores, debt=parsed_receipt.debt)
    if live_receipt.receipt_sha256 != parsed_receipt.receipt_sha256:
        _invalid("BAMF_GRADE_CERTIFICATION_RECEIPT_REISSUE_DRIFT")
    return require_accepted_certification_receipt(live_receipt)


def run_grade_boundary_certification(
    run_dir: Path,
    priority_result,
    source_context,
    accepted_student,
    artifact_path: str,
    *,
    policy: GradeCertificationPolicy | None = None,
):
    """Compose one live #1333 boundary through passive #1334 certification."""
    policy_source = (
        (lambda: selected_grade_certification_policy(Path(run_dir)))
        if policy is None else
        (lambda: policy)
    )
    selected_policy = policy_source()
    request = issue_grade_certification_request(
        run_dir, priority_result, selected_policy)
    if request is None:
        return None
    from .grade_certification_execution import execute_grade_certification
    from .grade_certification_measurement import (
        GradeCertificationMeasurementBackend,
    )
    backend = GradeCertificationMeasurementBackend(
        Path(run_dir), request, source_context, accepted_student, artifact_path)
    return execute_grade_certification(
        Path(run_dir),
        request,
        selected_policy,
        trigger_measure=backend.trigger,
        obligation_measure=backend.obligation,
        require_current=lambda: require_current_grade_certification_request(
            Path(run_dir), request, policy_source()),
    )


__all__ = (
    "historical_mean_stability_policy",
    "issue_grade_certification_request",
    "require_current_accepted_certification_receipt",
    "require_current_grade_certification_request",
    "run_grade_boundary_certification",
    "selected_grade_certification_policy",
)
