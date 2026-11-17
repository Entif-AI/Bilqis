"""C16.3 persistent BAMF-native human session.

This coordinator composes existing owners.  It is not a curriculum, teacher,
retention, source, optimizer, or publication authority.
"""
from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
import time
import json

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.learning.atlas_retention_decision import issue_factory_retention_decision
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_metrics_delta, candidate_identity_metrics_snapshot,
)
from bilqis_mlx.runtime.accepted_priority_visit import (
    accepted_priority_school, execute_accepted_priority_candidate,
)
from bilqis_mlx.runtime.bamf_bundle import record_bamf_rejection
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, bind_accepted_execution_cache, load_accepted_generation,
)
from bilqis_mlx.runtime.factory_candidate_training import FactoryDeliveryObservation
from bilqis_mlx.runtime.factory_retention_owner import (
    bind_current_retention_protection_plan, bind_current_retention_source_rows,
    bind_factory_baseline_successor,
    derive_current_plasticity_escape_state,
    evaluate_factory_retention_candidate,
)
from bilqis_mlx.runtime.foundation_teacher_owner import (
    derive_accepted_teacher_successor, select_foundation_priority_visit,
)
from bilqis_mlx.runtime.priority_rejection_replay import (
    candidate_step_horizon, rejection_attempt_ordinals,
)
from bilqis_mlx.runtime.active_grade_cadence import record_active_grade_cadence_attempt
from .evidence import CandidateEvidenceCapture as _Capture, prepare_candidate_evidence_root
from .locking import bamf_operator_lock
from .performance import measure_observed_phase, observe_completed_step
from .telemetry import TrainerObservation
from .session_support import (
    BamfPreparedVisit, _execution_context, _resource_observation, _step_seed,
)
from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
    VisitCurrentnessMetrics, currentness_metrics,
)
from .source_prefetch import (
    CandidateSourceLane, NATIVE_SOURCE_WORKER_COUNTS, SourcePrefetchMetrics,
)
from .session_parts.candidate_execution import (
    candidate_horizon_execution as _candidate_horizon_execution_impl,
)
from .session_parts.candidate_execution import execute_horizon as _execute_horizon_impl
from .session_parts.stop_receipt import (
    record_normal_stop_receipt, stop_resource_witness,
)
from ._session_execution import operate as _operate_impl
from ._session_execution import retention_result as _retention_result_impl
from ._session_visit import visit as _visit_impl

_MAX_CANDIDATE_HORIZON = 16
def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_FIRST_STUDENT.INVALID, reason=reason)
from .session_support import BamfOperatorResult
def _emit_progress(progress, message: str) -> None:
    if progress is not None:
        progress(message)

def _execute_horizon(run_dir, selection, context, parent, atlas_path, feature_path,
                     rows, horizon, cache, candidate_attempt_ordinal, progress,
                     source_prefetch_workers,
                     source_prefetch_executor, source_prefetch_metrics, observer,
                     adviser_pool=None):
    return _execute_horizon_impl(
        run_dir, selection, context, parent, atlas_path, feature_path,
        rows, horizon, cache, candidate_attempt_ordinal, progress,
        source_prefetch_workers, source_prefetch_executor,
        source_prefetch_metrics, observer, adviser_pool,
        source_lane_cls=CandidateSourceLane, source_metrics_cls=SourcePrefetchMetrics,
        prepare_evidence_root=prepare_candidate_evidence_root, capture_cls=_Capture,
        delivery_observation_cls=FactoryDeliveryObservation,
        execute_candidate=execute_accepted_priority_candidate, step_seed=_step_seed,
        emit_progress=_emit_progress, invalid=_invalid,
        observe_completed_step_fn=observe_completed_step)


def _candidate_horizon_execution(
        run_dir, parent, context, atlas_path, feature_path, selection, rows,
        capability, host_cache, steps_per_visit, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer, adviser_pool):
    return _candidate_horizon_execution_impl(
        run_dir, parent, context, atlas_path, feature_path, selection, rows,
        capability, host_cache, steps_per_visit, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer, adviser_pool,
        bind_cache=bind_accepted_execution_cache, horizon_for=candidate_step_horizon,
        rejection_ordinals=rejection_attempt_ordinals,
        execute_horizon_fn=_execute_horizon, currentness_metrics_fn=currentness_metrics,
        emit_progress=_emit_progress,
        identity_snapshot=candidate_identity_metrics_snapshot)


def _retention_result(
        run_dir, parent, context, atlas_path, selection, capability, cache, steps,
        capture, rejection_journal_ordinal, rejection_attempt_ordinal,
        identity_before, progress, observer):
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
        derive_plasticity_escape=derive_current_plasticity_escape_state,
        prepared_visit_type=BamfPreparedVisit, emit_progress=_emit_progress,
        measure_observed_phase_fn=measure_observed_phase)


def _execute_selected_visit(
        run_dir, parent, context, atlas_path, feature_path, selection, host_cache,
        steps_per_visit, reserve_gib, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer):
    rows = selection.offer.rows()
    if observer is not None:
        from .evidence_projection import (
            selected_visit_evidence, unknown_generated_grade_evidence,
        )
        visit_evidence = selected_visit_evidence(selection)
        observer.update(
            visit_evidence=visit_evidence,
            generated_grade_evidence=unknown_generated_grade_evidence(
                visit_evidence.get("grade_id")),
        )
    _emit_progress(
        progress,
        f"selected {selection.offer.capability_id} with {len(rows)} source rows")
    capability = selection.offer.capability_id
    if host_cache is not None:
        bind_current_retention_source_rows(context, host_cache, capability)
    adviser_cache = (
        host_cache if host_cache is not None
        else bind_accepted_execution_cache(run_dir))
    from bilqis_mlx.runtime.championship_advisers import (
        prepare_championship_adviser_pool,
    )
    adviser_pool = prepare_championship_adviser_pool(
        run_dir, parent, context, atlas_path, adviser_cache,
        reserve_gib=reserve_gib)
    horizon_state = _candidate_horizon_execution(
        run_dir, parent, context, atlas_path, feature_path, selection, rows,
        capability, host_cache, steps_per_visit, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer, adviser_pool)
    (
        cache, steps, capture, rejection_journal_ordinal,
        rejection_attempt_ordinal, identity_before,
    ) = horizon_state
    return _retention_result(
        run_dir, parent, context, atlas_path, selection, capability, cache, steps,
        capture, rejection_journal_ordinal, rejection_attempt_ordinal,
        identity_before, progress, observer)


def prepare_bamf_visit(
        run_dir: Path, *, steps_per_visit: int = 16,
        reserve_gib: float = 100.0,
        progress=None, source_prefetch_workers: int = 0,
        source_prefetch_executor=None,
        source_prefetch_metrics: SourcePrefetchMetrics | None = None, observer=None) -> BamfPreparedVisit:
    """Compose the production visit through retention without publishing it."""
    if (type(steps_per_visit) is not int
            or not 1 <= steps_per_visit <= _MAX_CANDIDATE_HORIZON):
        _invalid("BAMF_OPERATOR_SESSION_BOUNDS_INVALID")
    _emit_progress(progress, "validating accepted generation and source custody")
    visit_currentness_metrics = VisitCurrentnessMetrics()
    parent, context, atlas_path, feature_path = _execution_context(
        run_dir, currentness_metrics=visit_currentness_metrics)
    if observer is not None:
        observer.bind_parent(parent)
        observer.update(phase="SELECTING")
    program = schedule_program_from_executable_release(context.release)
    accepted_host = getattr(context, "_accepted_runtime_host", None)
    host_cache = getattr(accepted_host, "_accepted_cache", None)
    if host_cache is not None:
        bind_current_retention_protection_plan(context, parent, host_cache)
    school = accepted_priority_school(
        parent, program,
        candidate_identity_sha256=getattr(
            host_cache, "_candidate_identity_sha256", None))
    _emit_progress(progress, "planning current candidate frontier and teacher priority")
    planning_started = time.perf_counter()
    selection = select_foundation_priority_visit(
        run_dir, context, atlas_path, program=program, school=school,
        progress=progress)
    planning_total = max(0.0, time.perf_counter() - planning_started)
    source_materialization_wall_seconds = float(
        getattr(selection, "source_materialization_wall_seconds", None) or 0.0)
    if observer is not None:
        observer.update(
            planning_wall_seconds=max(
                0.0, planning_total - source_materialization_wall_seconds),
            source_materialization_wall_seconds=(
                source_materialization_wall_seconds or None))
    if selection.status != "TEACHER_SELECTED":
        status = "ACTION_REQUIRED" if selection.status == "ACTION_REQUIRED" else "HELD"
        payload = {
            "holds": getattr(selection, "holds", ()),
            "exclusions": [
                item.to_record() for item in getattr(selection, "exclusions", ())
            ],
            **({"cadence": (getattr(selection, "metadata", None) or {}).get("cadence")}
               if (getattr(selection, "metadata", None) or {}).get("cadence") is not None
               else {}),
        }
        _emit_progress(progress, "priority holds: " + json.dumps(
            payload, sort_keys=True, ensure_ascii=True))
        return BamfPreparedVisit(status, parent, selection=selection)
    return _execute_selected_visit(
        run_dir, parent, context, atlas_path, feature_path, selection, host_cache,
        steps_per_visit, reserve_gib, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer)

def _visit(run_dir: Path, reserve_gib: float, *, steps_per_visit=16,
           progress=None, source_prefetch_workers=0,
           source_prefetch_executor=None, source_prefetch_metrics=None, observer=None,
           run_authority_binding=None):
    return _visit_impl(
        run_dir, reserve_gib, steps_per_visit=steps_per_visit, progress=progress,
        source_prefetch_workers=source_prefetch_workers,
        source_prefetch_executor=source_prefetch_executor,
        source_prefetch_metrics=source_prefetch_metrics, observer=observer,
        run_authority_binding=run_authority_binding,
        prepare_visit=prepare_bamf_visit, record_rejection=record_bamf_rejection,
        accept_publish=accept_and_publish, load_generation=load_accepted_generation,
        measure_phase=measure_observed_phase, emit_progress=_emit_progress,
        record_cadence_attempt=record_active_grade_cadence_attempt)


def _accepted_admission_reentry(
        run_dir: Path, parent_graph: dict, reserve_gib: float, progress=None):
    """Re-enter C07 after retained learning before another cold neural visit."""
    from bilqis_mlx.errors import BilqisError
    from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_factory_release
    from bilqis_mlx.runtime.atlas_flywheel import AdmissionFlywheelStatus
    from bilqis_mlx.runtime.atlas_flywheel_runtime import run_accepted_atlas_flywheel

    if not isinstance(parent_graph, dict):
        _invalid("BAMF_OPERATOR_ADMISSION_PARENT_GRAPH_INVALID")
    before = read_accepted_atlas_factory_release(run_dir)
    _emit_progress(progress, "re-entering accepted C07 admission flywheel")
    try:
        result = run_accepted_atlas_flywheel(
            run_dir, parent_graph, reserve_gib=reserve_gib)
    except BilqisError as error:
        reason = error.context.get("reason")
        lease_boundary = (
            error.spec is SCHOOL.BAMF_ATLAS_ADMISSION.ACCEPTED_LEASE_REQUIRED
            or (error.spec is SCHOOL.BAMF_ATLAS_ADMISSION.INVALID
                and isinstance(reason, str) and "LEASE" in reason)
        )
        if not lease_boundary:
            raise
        return AdmissionFlywheelStatus.LEASE_REQUIRED.value, 0, "ADMISSION_LEASE_REQUIRED"
    after = read_accepted_atlas_factory_release(run_dir)
    if after.release_sha256 != result.final_state.epoch.current_release.release_sha256:
        _invalid("BAMF_OPERATOR_ADMISSION_REFRESH_DRIFT")
    if after.release_sha256 != before.release_sha256:
        _emit_progress(
            progress,
            "C07 adopted a successor; next visit must cold-refresh accepted custody")
    _emit_progress(
        progress,
        f"admission flywheel outcome: {result.status.value} "
        f"after {result.advances} advance(s)")
    stop_status = {
        AdmissionFlywheelStatus.HELD: "ADMISSION_HOLD",
        AdmissionFlywheelStatus.LEASE_REQUIRED: "ADMISSION_LEASE_REQUIRED",
    }.get(result.status)
    return result.status.value, result.advances, stop_status

def _accepted_learning_reentry(
        run_dir: Path, parent_graph: dict, reserve_gib: float, progress=None):
    """Refresh accepted learner evidence before C07 considers another successor."""
    from .accepted_learning_evidence import refresh_accepted_learning_evidence

    evidence = refresh_accepted_learning_evidence(
        Path(run_dir), progress=progress)
    _emit_progress(
        progress,
        "accepted learner evidence refresh: "
        f"{evidence.measured} measured, {evidence.passed} passed; "
        f"next {evidence.final_action}",
    )
    return _accepted_admission_reentry(
        run_dir, parent_graph, reserve_gib, progress)

def operate_bamf(
    run_dir: Path, *, minutes: int = 90,
    max_visits: int = 0, steps_per_visit: int = 16,
    reserve_gib: float = 100.0,
    source_prefetch_workers: int = 2,
    parent_graph: dict | None = None,
    profile_release=None,
    run_authority=None,
    progress=None,
) -> BamfOperatorResult:
    """Run the human-authorized BAMF lineage until a bounded stop condition."""
    from bilqis_mlx.runtime.run_authority import bind_native_run_authority
    from bilqis_mlx.runtime.source_prefetch import source_prefetch_pool
    def before_visits(root):
        if profile_release is not None:
            from bilqis_mlx.runtime._release_adoption.native_profile import adopt_profile_release
            adopt_profile_release(root, profile_release, reserve_gib=reserve_gib)
    return _operate_impl(
        Path(run_dir), minutes=minutes, max_visits=max_visits,
        steps_per_visit=steps_per_visit, reserve_gib=reserve_gib,
        source_prefetch_workers=source_prefetch_workers, progress=progress,
        max_horizon=_MAX_CANDIDATE_HORIZON,
        worker_counts=NATIVE_SOURCE_WORKER_COUNTS, invalid=_invalid,
        metrics_type=SourcePrefetchMetrics, source_pool_factory=source_prefetch_pool,
        null_context=nullcontext, operator_lock=bamf_operator_lock,
        visit_fn=_visit, observer_type=TrainerObservation,
        emit_progress=_emit_progress, monotonic=time.monotonic,
        load_generation=load_accepted_generation, result_type=BamfOperatorResult,
        resource_snapshot=stop_resource_witness,
        record_stop=record_normal_stop_receipt, elapsed_clock=time.perf_counter,
        before_visits=before_visits,
        bind_run_authority=(
            lambda current_run_dir:
            bind_native_run_authority(current_run_dir, run_authority)),
        accepted_reentry=(
            None if parent_graph is None else
            lambda current_run_dir, current_reserve_gib, current_progress:
            _accepted_learning_reentry(
                current_run_dir, parent_graph, current_reserve_gib,
                current_progress)))
