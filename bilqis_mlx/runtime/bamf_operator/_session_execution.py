"""Compatibility exports and session loop for the BAMF operator coordinator."""
from __future__ import annotations

from .session_parts.candidate_execution import candidate_horizon_execution, execute_horizon
from .session_parts.retention import retention_result


def operate(
        run_dir, *, minutes, max_visits, steps_per_visit, reserve_gib,
        source_prefetch_workers, progress, max_horizon, worker_counts,
        invalid, metrics_type, source_pool_factory, null_context,
        operator_lock, visit_fn, observer_type, emit_progress,
        monotonic, load_generation, result_type, accepted_reentry=None,
        bind_run_authority=None, before_visits=None):
    if (type(minutes) is not int or minutes < 1 or type(max_visits) is not int
            or max_visits < 0 or type(steps_per_visit) is not int
            or not 1 <= steps_per_visit <= max_horizon
            or type(source_prefetch_workers) is not int
            or source_prefetch_workers not in worker_counts
            or reserve_gib < 0):
        invalid("BAMF_OPERATOR_SESSION_BOUNDS_INVALID")
    run_dir = run_dir.resolve()
    run_authority_binding = (
        bind_run_authority(run_dir) if bind_run_authority is not None else None)
    deadline = monotonic() + minutes * 60
    visits = accepted = rejected = 0
    admission_status, admission_advances = None, 0
    status = "TIME_LIMIT"
    metrics = metrics_type()
    source_pool = (
        source_pool_factory(source_prefetch_workers)
        if source_prefetch_workers else null_context(None))
    with source_pool as source_prefetch_executor, operator_lock(run_dir):
        if run_authority_binding is not None:
            run_authority_binding.assert_current()
        if before_visits is not None:
            before_visits(run_dir)
        while monotonic() < deadline and (not max_visits or visits < max_visits):
            if run_authority_binding is not None:
                run_authority_binding.assert_current()
            emit_progress(progress, f"starting visit {visits + 1}")
            with observer_type(run_dir, visits + 1) as observer:
                outcome = visit_fn(
                    run_dir, reserve_gib, steps_per_visit=steps_per_visit,
                    progress=progress,
                    source_prefetch_workers=source_prefetch_workers,
                    source_prefetch_executor=source_prefetch_executor,
                    source_prefetch_metrics=metrics, observer=observer,
                    run_authority_binding=run_authority_binding)
                observer.finish(outcome)
            emit_progress(progress, f"visit {visits + 1} outcome: {outcome}")
            if outcome in {
                "HELD", "ACTION_REQUIRED",
                "CERTIFICATION_FAILED", "CERTIFICATION_SUPERSEDED",
            }:
                status = {
                    "HELD": "PRIORITY_HOLD",
                    "ACTION_REQUIRED": "ACTION_REQUIRED",
                    "CERTIFICATION_FAILED": "CERTIFICATION_FAILED",
                    "CERTIFICATION_SUPERSEDED": "CERTIFICATION_SUPERSEDED",
                }[outcome]
                break
            visits += 1
            if outcome == "GRADE_TRANSITIONED":
                continue
            if outcome == "REJECTED":
                rejected += 1
                continue
            accepted += 1
            if accepted_reentry is not None:
                if run_authority_binding is not None:
                    run_authority_binding.assert_current()
                (
                    admission_status, advances, stop_status,
                ) = accepted_reentry(run_dir, reserve_gib, progress)
                admission_advances += advances
                if stop_status is not None:
                    status = stop_status
                    break
        else:
            status = "VISIT_LIMIT" if max_visits and visits >= max_visits else "TIME_LIMIT"
    current = load_generation(run_dir)
    return result_type(
        status, visits, accepted, rejected, current.generation,
        current.retained_state.optimizer_step,
        source_prefetch_workers=source_prefetch_workers,
        source_prefetch_wait_seconds=metrics.wait_seconds,
        source_prefetch_overlap_seconds=metrics.overlap_seconds,
        source_prefetch_prepared_steps=metrics.prepared_steps,
        source_prefetch_serial_steps=metrics.serial_steps,
        admission_status=admission_status,
        admission_advances=admission_advances)
