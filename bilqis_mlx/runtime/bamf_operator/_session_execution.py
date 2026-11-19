"""Compatibility exports and session loop for the BAMF operator coordinator."""
from __future__ import annotations

from ._session_visit import ResourceRejectedVisit
from .session_parts.candidate_execution import candidate_horizon_execution, execute_horizon
from .session_parts.retention import retention_result


def _validate_bounds(*, minutes, max_visits, steps_per_visit, reserve_gib,
                     source_prefetch_workers, max_horizon, worker_counts, invalid):
    if (type(minutes) is not int or minutes < 1 or type(max_visits) is not int
            or max_visits < 0 or type(steps_per_visit) is not int
            or not 1 <= steps_per_visit <= max_horizon
            or type(source_prefetch_workers) is not int
            or source_prefetch_workers not in worker_counts
            or reserve_gib < 0):
        invalid("BAMF_OPERATOR_SESSION_BOUNDS_INVALID")


def _assert_current(binding):
    if binding is not None:
        binding.assert_current()


def _source_pool(workers, source_pool_factory, null_context):
    return source_pool_factory(workers) if workers else null_context(None)


def _terminal_visit_status(outcome):
    return {
        "HELD": "PRIORITY_HOLD",
        "RESOURCE_HOLD": "RESOURCE_HOLD",
        "ACTION_REQUIRED": "ACTION_REQUIRED",
        "CERTIFICATION_FAILED": "CERTIFICATION_FAILED",
        "CERTIFICATION_SUPERSEDED": "CERTIFICATION_SUPERSEDED",
        "CERTIFICATION_POLICY_REQUIRED": "CERTIFICATION_POLICY_REQUIRED",
    }.get(outcome)


def _run_visits(
        run_dir, *, deadline, max_visits, steps_per_visit, reserve_gib,
        source_prefetch_workers, progress, source_prefetch_executor, metrics,
        run_authority_binding, resource_snapshot, monotonic, visit_fn,
        observer_type, emit_progress):
    visits = accepted = rejected = 0
    attempts = 0
    resource_holds = set()
    admission_status, admission_advances = None, 0
    status = "TIME_LIMIT"
    resource_witness = None
    while monotonic() < deadline and (not max_visits or visits < max_visits):
        _assert_current(run_authority_binding)
        if resource_snapshot is not None:
            resource_witness = resource_snapshot(run_dir, reserve_gib)
            if not resource_witness["sufficient"]:
                status = "DISK_RESERVE_REACHED"
                break
        attempts += 1
        emit_progress(progress, f"starting visit {attempts}")
        with observer_type(run_dir, attempts) as observer:
            def observed_progress(message):
                observer.update(activity=str(message)[:256])
                emit_progress(progress, message)

            outcome = visit_fn(
                run_dir, reserve_gib, steps_per_visit=steps_per_visit,
                progress=observed_progress, source_prefetch_workers=source_prefetch_workers,
                source_prefetch_executor=source_prefetch_executor,
                source_prefetch_metrics=metrics, observer=observer,
                run_authority_binding=run_authority_binding,
                **({"resource_holds": frozenset(resource_holds)} if resource_holds else {}))
            resource_rejected = isinstance(outcome, ResourceRejectedVisit)
            observer.finish("RESOURCE_REJECTED" if resource_rejected else outcome)
        if resource_rejected:
            resource_holds.add(outcome.capability)
            emit_progress(progress, f"visit {attempts} resource-held {outcome.capability}")
            continue
        emit_progress(progress, f"visit {attempts} outcome: {outcome}")
        stop_status = _terminal_visit_status(outcome)
        if stop_status is not None:
            status = stop_status
            break
        visits += 1
        if outcome == "GRADE_TRANSITIONED":
            continue
        if outcome == "REJECTED":
            rejected += 1
            continue
        accepted += 1
    else:
        status = "VISIT_LIMIT" if max_visits and visits >= max_visits else "TIME_LIMIT"
    return (
        status, visits, accepted, rejected, admission_status,
        admission_advances, resource_witness,
    )


def _finalize_stop(
        run_dir, *, status, minutes, max_visits, steps_per_visit, reserve_gib,
        source_prefetch_workers, visits, accepted, rejected, admission_status,
        admission_advances, resource_witness, resource_snapshot, elapsed_clock,
        elapsed_started, load_generation, record_stop):
    current = load_generation(run_dir)
    if resource_snapshot is not None and status != "DISK_RESERVE_REACHED":
        resource_witness = resource_snapshot(run_dir, reserve_gib)
    elapsed_seconds = (
        0.0 if elapsed_clock is None else
        max(0.0, float(elapsed_clock() - elapsed_started)))
    receipt_sha256 = None
    if record_stop is not None:
        receipt_sha256 = record_stop(
            run_dir, current, status=status, minutes=minutes,
            max_visits=max_visits, steps_per_visit=steps_per_visit,
            reserve_gib=reserve_gib,
            source_prefetch_workers=source_prefetch_workers,
            visits=visits, accepted=accepted, rejected=rejected,
            elapsed_seconds=elapsed_seconds, admission_status=admission_status,
            admission_advances=admission_advances,
            resource_witness=resource_witness or {})
    return current, elapsed_seconds, receipt_sha256


def operate(
        run_dir, *, minutes, max_visits, steps_per_visit, reserve_gib,
        source_prefetch_workers, progress, max_horizon, worker_counts,
        invalid, metrics_type, source_pool_factory, null_context,
        operator_lock, visit_fn, observer_type, emit_progress,
        monotonic, load_generation, result_type,
        bind_run_authority=None, before_visits=None, resource_snapshot=None,
        record_stop=None, elapsed_clock=None, training_memory_context=None):
    _validate_bounds(
        minutes=minutes, max_visits=max_visits, steps_per_visit=steps_per_visit,
        reserve_gib=reserve_gib, source_prefetch_workers=source_prefetch_workers,
        max_horizon=max_horizon, worker_counts=worker_counts, invalid=invalid)
    run_dir = run_dir.resolve()
    run_authority_binding = bind_run_authority(run_dir) if bind_run_authority else None
    elapsed_started = elapsed_clock() if elapsed_clock is not None else None
    deadline = monotonic() + minutes * 60
    metrics = metrics_type()
    source_pool = _source_pool(source_prefetch_workers, source_pool_factory, null_context)
    with (source_pool as source_prefetch_executor, operator_lock(run_dir),
          training_memory_context() if training_memory_context else null_context()):
        _assert_current(run_authority_binding)
        if before_visits is not None:
            before_visits(run_dir)
        (
            status, visits, accepted, rejected, admission_status,
            admission_advances, resource_witness,
        ) = _run_visits(
            run_dir, deadline=deadline, max_visits=max_visits,
            steps_per_visit=steps_per_visit, reserve_gib=reserve_gib,
            source_prefetch_workers=source_prefetch_workers, progress=progress,
            source_prefetch_executor=source_prefetch_executor, metrics=metrics,
            run_authority_binding=run_authority_binding,
            resource_snapshot=resource_snapshot, monotonic=monotonic,
            visit_fn=visit_fn, observer_type=observer_type,
            emit_progress=emit_progress)
        current, elapsed_seconds, stop_receipt_sha256 = _finalize_stop(
            run_dir, status=status, minutes=minutes, max_visits=max_visits,
            steps_per_visit=steps_per_visit, reserve_gib=reserve_gib,
            source_prefetch_workers=source_prefetch_workers, visits=visits,
            accepted=accepted, rejected=rejected, admission_status=admission_status,
            admission_advances=admission_advances,
            resource_witness=resource_witness, resource_snapshot=resource_snapshot,
            elapsed_clock=elapsed_clock, elapsed_started=elapsed_started,
            load_generation=load_generation, record_stop=record_stop)
    return result_type(
        status, visits, accepted, rejected, current.generation,
        current.retained_state.optimizer_step,
        source_prefetch_workers=source_prefetch_workers,
        source_prefetch_wait_seconds=metrics.wait_seconds,
        source_prefetch_overlap_seconds=metrics.overlap_seconds,
        source_prefetch_prepared_steps=metrics.prepared_steps,
        source_prefetch_serial_steps=metrics.serial_steps,
        admission_status=admission_status,
        admission_advances=admission_advances,
        elapsed_seconds=elapsed_seconds,
        stop_receipt_sha256=stop_receipt_sha256)
