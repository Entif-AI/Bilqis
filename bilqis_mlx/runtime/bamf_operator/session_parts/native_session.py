"""Native BAMF session bindings kept outside the top-level coordinator."""
from __future__ import annotations

from functools import partial
from pathlib import Path
import json

from bilqis_mlx.errors import BilqisError, SCHOOL
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_metrics_delta, candidate_identity_metrics_snapshot,
)
from bilqis_mlx.learning.atlas_retention_decision import issue_factory_retention_decision
from bilqis_mlx.runtime.accepted_priority_visit import execute_accepted_priority_candidate
from bilqis_mlx.runtime.bamf_bundle.admission import bind_accepted_execution_cache
from bilqis_mlx.runtime.factory_candidate_training import FactoryDeliveryObservation
from bilqis_mlx.runtime.factory_retention_owner import (
    bind_current_retention_source_rows, bind_factory_baseline_successor,
    derive_current_plasticity_escape_state, evaluate_factory_retention_candidate,
)
from bilqis_mlx.runtime._factory_identity_evaluation import (
    _finalize_factory_generation_authority,
)
from bilqis_mlx.runtime.foundation_teacher_owner import derive_accepted_teacher_successor
from bilqis_mlx.runtime.priority_rejection_replay import (
    candidate_step_horizon, rejection_attempt_ordinals,
)
from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import currentness_metrics

from ..evidence import CandidateEvidenceCapture as _Capture, prepare_candidate_evidence_root
from ..performance import measure_observed_phase, observe_completed_step
from ..session_support import BamfPreparedVisit, _resource_observation, _step_seed
from ..source_prefetch import CandidateSourceLane, SourcePrefetchMetrics
from .rehearsal import compile_rehearsal_plan
from .candidate_execution import (
    candidate_horizon_execution as _candidate_horizon_execution_impl,
    execute_horizon as _execute_horizon_impl,
)


def adopt_and_activate_certified_successor(
    run_dir: Path, context, *, certification_receipt_sha256: str,
    reserve_gib: float,
) -> bool:
    """Compose #1320 -> C07/B13 -> #1314 without acquiring any authority."""
    from bilqis_mlx.runtime.atlas_flywheel_runtime import run_accepted_atlas_flywheel
    result = run_accepted_atlas_flywheel(
        Path(run_dir), context.graph, reserve_gib=reserve_gib, max_advances=1)
    if result.advances != 1:
        return False
    from bilqis_mlx.runtime.active_generated_grade import activate_certified_generated_grade
    activate_certified_generated_grade(
        Path(run_dir), certification_receipt_sha256=certification_receipt_sha256)
    return True


def priority_hold_result(
        run_dir, selection, context, parent, atlas_path, reserve_gib, progress,
        *, emit_progress):
    status = "ACTION_REQUIRED" if selection.status == "ACTION_REQUIRED" else "HELD"
    metadata = getattr(selection, "metadata", None) or {}
    cadence = metadata.get("cadence")
    payload = {
        "holds": getattr(selection, "holds", ()),
        "exclusions": [item.to_record() for item in getattr(selection, "exclusions", ())],
        **({"cadence": cadence} if cadence is not None else {}),
    }
    emit_progress(progress, "priority holds: " + json.dumps(
        payload, sort_keys=True, ensure_ascii=True))
    boundary_disposition = cadence.get("disposition") if isinstance(cadence, dict) else None
    certification = None
    if boundary_disposition in {"GRADE_COMPLETE", "RECOVERY_EXHAUSTED"}:
        from bilqis_mlx.runtime.grade_certification import run_grade_boundary_certification
        certification = run_grade_boundary_certification(
            Path(run_dir), selection, context, parent, str(atlas_path))
    if certification is None:
        return BamfPreparedVisit(status, parent, selection=selection)
    if certification.status == "SUCCEEDED":
        if not adopt_and_activate_certified_successor(
                Path(run_dir), context,
                certification_receipt_sha256=certification.receipt.receipt_sha256,
                reserve_gib=reserve_gib):
            emit_progress(
                progress, "grade certification succeeded; successor admission "
                "did not advance C07/B13")
            return BamfPreparedVisit("HELD", parent, selection=selection)
        emit_progress(
            progress, "grade certification succeeded; activated exact "
            "receipt-bound generated successor")
        return BamfPreparedVisit("GRADE_TRANSITIONED", parent, selection=selection)
    if certification.status == "SUPERSEDED":
        return BamfPreparedVisit("CERTIFICATION_SUPERSEDED", parent, selection=selection)
    if certification.status == "FAILED":
        return BamfPreparedVisit("CERTIFICATION_FAILED", parent, selection=selection)
    return BamfPreparedVisit(status, parent, selection=selection)


def execute_horizon(
        run_dir, selection, context, parent, atlas_path, feature_path, rows, horizon,
        cache, candidate_attempt_ordinal, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer, adviser_pool,
        *, emit_progress, invalid, rehearsal_plan=None,
        distributed_profile=None, distributed_executor=None):
    return _execute_horizon_impl(
        run_dir, selection, context, parent, atlas_path, feature_path,
        rows, horizon, cache, candidate_attempt_ordinal, progress,
        source_prefetch_workers, source_prefetch_executor,
        source_prefetch_metrics, observer, adviser_pool,
        source_lane_cls=CandidateSourceLane, source_metrics_cls=SourcePrefetchMetrics,
        prepare_evidence_root=prepare_candidate_evidence_root, capture_cls=_Capture,
        delivery_observation_cls=FactoryDeliveryObservation,
        execute_candidate=partial(
            execute_accepted_priority_candidate,
            distributed_profile=distributed_profile,
            distributed_executor=distributed_executor),
        step_seed=_step_seed,
        emit_progress=emit_progress, invalid=invalid,
        observe_completed_step_fn=observe_completed_step,
        rehearsal_plan=rehearsal_plan)


def candidate_horizon_execution(
        run_dir, parent, context, atlas_path, feature_path, selection, rows,
        capability, host_cache, steps_per_visit, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer, adviser_pool,
        *, emit_progress, invalid,
        distributed_profile=None, distributed_executor=None):
    cache = host_cache if host_cache is not None else bind_accepted_execution_cache(run_dir)
    from bilqis_mlx.runtime.bamf_bundle.execution_cache import AcceptedExecutionCache
    rehearsal_plan = (
        compile_rehearsal_plan(run_dir, parent, cache, context, selection)
        if type(cache) is AcceptedExecutionCache else None)
    return _candidate_horizon_execution_impl(
        run_dir, parent, context, atlas_path, feature_path, selection, rows,
        capability, host_cache, steps_per_visit, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer, adviser_pool,
        bind_cache=bind_accepted_execution_cache, horizon_for=candidate_step_horizon,
        rejection_ordinals=rejection_attempt_ordinals,
        execute_horizon_fn=lambda *args, **kwargs: execute_horizon(
            *args, **kwargs, emit_progress=emit_progress, invalid=invalid,
            rehearsal_plan=rehearsal_plan, distributed_profile=distributed_profile,
            distributed_executor=distributed_executor),
        currentness_metrics_fn=currentness_metrics, emit_progress=emit_progress,
        identity_snapshot=candidate_identity_metrics_snapshot)


def retention_result(
        run_dir, parent, context, atlas_path, selection, capability, cache, steps,
        capture, rejection_journal_ordinal, rejection_attempt_ordinal,
        identity_before, progress, observer, *, emit_progress):
    from .._session_execution import retention_result as _retention_result_impl
    return _retention_result_impl(
        run_dir, parent, context, atlas_path, selection, capability, cache, steps,
        capture, rejection_journal_ordinal, rejection_attempt_ordinal,
        identity_before, progress, observer,
        evaluate_candidate=evaluate_factory_retention_candidate,
        issue_decision=issue_factory_retention_decision,
        identity_delta=candidate_identity_metrics_delta,
        resource_observation=_resource_observation,
        derive_successor=derive_accepted_teacher_successor,
        bind_baseline_successor=bind_factory_baseline_successor,
        finalize_generation_authority=_finalize_factory_generation_authority,
        derive_plasticity_escape=derive_current_plasticity_escape_state,
        prepared_visit_type=BamfPreparedVisit, emit_progress=emit_progress,
        measure_observed_phase_fn=measure_observed_phase)


def execute_selected_visit(
        run_dir, parent, context, atlas_path, feature_path, selection, host_cache,
        steps_per_visit, reserve_gib, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer,
        *, emit_progress, invalid,
        distributed_profile=None, distributed_executor=None):
    rows = selection.offer.rows()
    if observer is not None:
        from ..evidence_projection import selected_visit_evidence, unknown_generated_grade_evidence
        visit_evidence = selected_visit_evidence(selection)
        observer.update(
            visit_evidence=visit_evidence,
            generated_grade_evidence=unknown_generated_grade_evidence(
                visit_evidence.get("grade_id")))
    emit_progress(
        progress, f"selected {selection.offer.capability_id} with {len(rows)} source rows")
    capability = selection.offer.capability_id
    adviser_cache = host_cache if host_cache is not None else bind_accepted_execution_cache(run_dir)
    if host_cache is not None:
        bind_current_retention_source_rows(context, host_cache, capability)
    from bilqis_mlx.runtime.championship_advisers import prepare_championship_adviser_pool
    adviser_pool = prepare_championship_adviser_pool(
        run_dir, parent, context, atlas_path, adviser_cache, reserve_gib=reserve_gib)
    horizon_state = candidate_horizon_execution(
        run_dir, parent, context, atlas_path, feature_path, selection, rows,
        capability, adviser_cache, steps_per_visit, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer, adviser_pool,
        emit_progress=emit_progress, invalid=invalid,
        distributed_profile=distributed_profile,
        distributed_executor=distributed_executor)
    cache, steps, capture, journal_ordinal, attempt_ordinal, identity_before = horizon_state
    return retention_result(
        run_dir, parent, context, atlas_path, selection, capability, cache, steps,
        capture, journal_ordinal, attempt_ordinal, identity_before, progress, observer,
        emit_progress=emit_progress)


def accepted_admission_reentry(
        run_dir: Path, parent_graph: dict, reserve_gib: float, progress=None,
        *, emit_progress, invalid):
    from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_factory_release
    from bilqis_mlx.runtime.atlas_flywheel import AdmissionFlywheelStatus
    from bilqis_mlx.runtime.atlas_flywheel_runtime import run_accepted_atlas_flywheel
    if not isinstance(parent_graph, dict):
        invalid("BAMF_OPERATOR_ADMISSION_PARENT_GRAPH_INVALID")
    before = read_accepted_atlas_factory_release(run_dir)
    emit_progress(progress, "re-entering accepted C07 admission flywheel")
    try:
        result = run_accepted_atlas_flywheel(run_dir, parent_graph, reserve_gib=reserve_gib)
    except BilqisError as error:
        reason = error.context.get("reason")
        lease_boundary = (
            error.spec is SCHOOL.BAMF_ATLAS_ADMISSION.ACCEPTED_LEASE_REQUIRED
            or (error.spec is SCHOOL.BAMF_ATLAS_ADMISSION.INVALID
                and isinstance(reason, str) and "LEASE" in reason))
        if not lease_boundary:
            raise
        return AdmissionFlywheelStatus.LEASE_REQUIRED.value, 0, "ADMISSION_LEASE_REQUIRED"
    after = read_accepted_atlas_factory_release(run_dir)
    if after.release_sha256 != result.final_state.epoch.current_release.release_sha256:
        invalid("BAMF_OPERATOR_ADMISSION_REFRESH_DRIFT")
    if after.release_sha256 != before.release_sha256:
        emit_progress(progress, "C07 adopted a successor; next visit must cold-refresh accepted custody")
    emit_progress(
        progress, f"admission flywheel outcome: {result.status.value} after {result.advances} advance(s)")
    stop_status = {
        AdmissionFlywheelStatus.FIXED_POINT: "FIXED_POINT",
        AdmissionFlywheelStatus.HELD: "ADMISSION_HOLD",
        AdmissionFlywheelStatus.LEASE_REQUIRED: "ADMISSION_LEASE_REQUIRED",
    }.get(result.status)
    return result.status.value, result.advances, stop_status


def accepted_learning_reentry(
        run_dir: Path, parent_graph: dict, reserve_gib: float, progress=None,
        *, emit_progress, invalid):
    """Compose evidence refresh and C07 only for an explicit admission boundary."""
    from ..accepted_learning_evidence import refresh_accepted_learning_evidence
    evidence = refresh_accepted_learning_evidence(Path(run_dir), progress=progress)
    emit_progress(
        progress, "accepted learner evidence refresh: "
        f"{evidence.measured} measured, {evidence.passed} passed; next {evidence.final_action}")
    return accepted_admission_reentry(
        run_dir, parent_graph, reserve_gib, progress,
        emit_progress=emit_progress, invalid=invalid)
