"""C16.3 persistent BAMF-native human session.

This coordinator composes existing owners.  It is not a curriculum, teacher,
retention, source, optimizer, or publication authority.
"""
from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
import time

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.runtime.atlas_memory_retry import CandidateMemoryExhausted, OOM_EXHAUSTED
from bilqis_mlx.runtime.accepted_priority_visit import (
    accepted_priority_school,
)
from bilqis_mlx.runtime.bamf_bundle import record_bamf_rejection
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, bind_accepted_execution_cache, load_accepted_generation,
)
from bilqis_mlx.runtime.factory_retention_owner import (
    bind_current_retention_protection_plan,
)
from bilqis_mlx.runtime.foundation_teacher_owner import select_foundation_priority_visit
from bilqis_mlx.runtime.active_grade_cadence import record_active_grade_cadence_attempt
from .locking import bamf_operator_lock
from .performance import measure_observed_phase
from .telemetry import TrainerObservation
from .session_support import (
    BamfPreparedVisit, _execution_context, _resource_observation, _step_seed,
)
from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import VisitCurrentnessMetrics
from .source_prefetch import (
    NATIVE_SOURCE_WORKER_COUNTS, SourcePrefetchMetrics,
)
from .evidence import CandidateEvidenceCapture as _Capture
from .session_parts.stop_receipt import (
    record_normal_stop_receipt, stop_resource_witness,
)
from ._session_execution import operate as _operate_impl
from ._session_visit import visit as _visit_impl
from .session_parts.native_session import (
    accepted_admission_reentry as _accepted_admission_reentry_impl,
    adopt_and_activate_certified_successor as _adopt_and_activate_certified_successor,
    execute_selected_visit as _execute_selected_visit_impl,
    priority_hold_result as _priority_hold_result,
)

_MAX_CANDIDATE_HORIZON = 16
def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_FIRST_STUDENT.INVALID, reason=reason)
from .session_support import BamfOperatorResult
def _emit_progress(progress, message: str) -> None:
    if progress is not None:
        progress(message)


def _execute_selected_visit(
        run_dir, parent, context, atlas_path, feature_path, selection, host_cache,
        steps_per_visit, reserve_gib, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer,
        distributed_profile=None, distributed_executor=None):
    return _execute_selected_visit_impl(
        run_dir, parent, context, atlas_path, feature_path, selection, host_cache,
        steps_per_visit, reserve_gib, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer,
        emit_progress=_emit_progress, invalid=_invalid,
        distributed_profile=distributed_profile,
        distributed_executor=distributed_executor)


def _accepted_admission_reentry(
        run_dir: Path, parent_graph: dict, reserve_gib: float, progress=None):
    return _accepted_admission_reentry_impl(
        run_dir, parent_graph, reserve_gib, progress,
        emit_progress=_emit_progress, invalid=_invalid)


def _accepted_learning_reentry(
        run_dir: Path, parent_graph: dict, reserve_gib: float, progress=None):
    """Compose evidence refresh and C07 only for an explicit admission boundary."""
    from .accepted_learning_evidence import refresh_accepted_learning_evidence
    evidence = refresh_accepted_learning_evidence(Path(run_dir), progress=progress)
    _emit_progress(progress, "accepted learner evidence refresh: "
                   f"{evidence.measured} measured, {evidence.passed} passed; "
                   f"next {evidence.final_action}")
    return _accepted_admission_reentry(run_dir, parent_graph, reserve_gib, progress)


def prepare_bamf_visit(
        run_dir: Path, *, steps_per_visit: int = 16,
        reserve_gib: float = 100.0,
        progress=None, source_prefetch_workers: int = 0,
        source_prefetch_executor=None,
        source_prefetch_metrics: SourcePrefetchMetrics | None = None, observer=None,
        resource_holds=frozenset(), distributed_profile=None,
        distributed_executor=None) -> BamfPreparedVisit:
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
        progress=progress, resource_holds=resource_holds)
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
        if (selection.status == "NO_ADMISSIBLE_TEACHING"
                and any(reason == OOM_EXHAUSTED for _, reason in selection.holds)):
            return BamfPreparedVisit("RESOURCE_HOLD", parent, selection=selection)
        return _priority_hold_result(
            run_dir, selection, context, parent, atlas_path, reserve_gib, progress,
            emit_progress=_emit_progress)
    try:
        return _execute_selected_visit(
            run_dir, parent, context, atlas_path, feature_path, selection, host_cache,
            steps_per_visit, reserve_gib, progress, source_prefetch_workers,
            source_prefetch_executor, source_prefetch_metrics, observer,
            distributed_profile, distributed_executor)
    except CandidateMemoryExhausted as error:
        return BamfPreparedVisit(
            "RESOURCE_REJECTED", parent, selection=selection,
            capability=selection.offer.capability_id, resource=error.to_record())


def _visit(run_dir: Path, reserve_gib: float, *, steps_per_visit=16,
           progress=None, source_prefetch_workers=0,
           source_prefetch_executor=None, source_prefetch_metrics=None, observer=None,
           run_authority_binding=None, resource_holds=frozenset(),
           distributed_profile=None, distributed_executor=None):
    def prepare_visit(*args, **kwargs):
        return prepare_bamf_visit(
            *args, **kwargs, distributed_profile=distributed_profile,
            distributed_executor=distributed_executor)
    return _visit_impl(
        run_dir, reserve_gib, steps_per_visit=steps_per_visit, progress=progress,
        source_prefetch_workers=source_prefetch_workers,
        source_prefetch_executor=source_prefetch_executor,
        source_prefetch_metrics=source_prefetch_metrics, observer=observer,
        run_authority_binding=run_authority_binding, resource_holds=resource_holds,
        prepare_visit=prepare_visit, record_rejection=record_bamf_rejection,
        accept_publish=accept_and_publish, load_generation=load_accepted_generation,
        measure_phase=measure_observed_phase, emit_progress=_emit_progress,
        record_cadence_attempt=record_active_grade_cadence_attempt)


def _training_memory_context():
    import mlx.core as mx
    from bilqis_mlx.runtime.mlx_memory import training_memory_policy
    return training_memory_policy(mx)


def operate_bamf(
    run_dir: Path, *, minutes: int = 90,
    max_visits: int = 0, steps_per_visit: int = 16,
    reserve_gib: float = 100.0,
    source_prefetch_workers: int = 2,
    parent_graph: dict | None = None,
    profile_release=None,
    run_authority=None,
    distributed_profile=None,
    distributed_executor=None,
    progress=None,
) -> BamfOperatorResult:
    """Run the human-authorized BAMF lineage until a bounded stop condition."""
    from bilqis_mlx.runtime.c08_distributed_executor import DistributedExecutorBinding
    from bilqis_mlx.runtime.run_authority import bind_native_run_authority
    from bilqis_mlx.runtime.source_prefetch import source_prefetch_pool
    if (distributed_profile is None
            and type(distributed_executor) is DistributedExecutorBinding):
        distributed_profile = distributed_executor.profile
    def before_visits(root):
        if profile_release is not None:
            from bilqis_mlx.runtime._release_adoption.native_profile import adopt_profile_release
            adopt_profile_release(root, profile_release, reserve_gib=reserve_gib)
    def visit_fn(*args, **kwargs):
        if distributed_profile is None and distributed_executor is None:
            return _visit(*args, **kwargs)
        return _visit(
            *args, **kwargs, distributed_profile=distributed_profile,
            distributed_executor=distributed_executor)
    return _operate_impl(
        Path(run_dir), minutes=minutes, max_visits=max_visits,
        steps_per_visit=steps_per_visit, reserve_gib=reserve_gib,
        source_prefetch_workers=source_prefetch_workers, progress=progress,
        max_horizon=_MAX_CANDIDATE_HORIZON,
        worker_counts=NATIVE_SOURCE_WORKER_COUNTS, invalid=_invalid,
        metrics_type=SourcePrefetchMetrics, source_pool_factory=source_prefetch_pool,
        null_context=nullcontext, operator_lock=bamf_operator_lock,
        visit_fn=visit_fn, observer_type=TrainerObservation,
        emit_progress=_emit_progress, monotonic=time.monotonic,
        load_generation=load_accepted_generation, result_type=BamfOperatorResult,
        resource_snapshot=stop_resource_witness,
        record_stop=record_normal_stop_receipt, elapsed_clock=time.perf_counter,
        before_visits=before_visits,
        training_memory_context=_training_memory_context,
        bind_run_authority=(
            lambda current_run_dir:
            bind_native_run_authority(current_run_dir, run_authority)))
