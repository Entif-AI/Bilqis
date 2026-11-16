"""Private execution helpers for the BAMF operator session coordinator."""
from __future__ import annotations

import time


def execute_horizon(
        run_dir, selection, context, parent, atlas_path, feature_path,
        rows, horizon, cache, candidate_attempt_ordinal, progress,
        source_prefetch_workers, source_prefetch_executor,
        source_prefetch_metrics, observer, *, source_lane_cls,
        source_metrics_cls, prepare_evidence_root, capture_cls,
        delivery_observation_cls, execute_candidate, step_seed,
        emit_progress, invalid, observe_completed_step_fn):
    source_lane = None
    if source_prefetch_metrics is not None or source_prefetch_workers:
        metrics = source_prefetch_metrics or source_metrics_cls()
        source_lane = source_lane_cls(
            selection, context, parent, horizon, workers=source_prefetch_workers,
            executor=source_prefetch_executor, metrics=metrics)
    prepare_evidence_root(run_dir)
    capture = capture_cls(
        run_dir, selection,
        generation=cache.generation,
        accepted_manifest_sha256=cache.accepted_manifest_sha256,
        candidate_attempt_ordinal=candidate_attempt_ordinal,
        parent_optimizer_step=parent.retained_state.optimizer_step,
    )
    steps, candidate = [], None
    for ordinal in range(1, horizon + 1):
        candidate_step_started_at = time.perf_counter()
        source_prepare_started = candidate_step_started_at
        source_rows = rows if source_lane is None else source_lane.rows(ordinal)
        source_prepare_wall_seconds = time.perf_counter() - source_prepare_started
        observation = delivery_observation_cls(
            capture, parent.retained_state.optimizer_step + ordinal,
            source_rows, selection.offer.source_seed)
        emit_progress(progress, f"executing candidate step {ordinal}/{horizon}")
        step = execute_candidate(
            selection, context, atlas_path, feature_path,
            teacher_hparams=parent.optimizer_hyperparameters,
            observation=observation,
            optimizer_step_seed=step_seed(selection.visit.identity.visit_id, ordinal),
            max_norm=1.0, candidate=candidate,
            finalize_candidate=(ordinal == horizon),
            prepared_source_rows=(source_rows if source_lane is not None else None),
            candidate_step_started_at=candidate_step_started_at,
            source_prepare_wall_seconds=source_prepare_wall_seconds)
        candidate = step.transaction
        if candidate.update_steps != ordinal:
            invalid("BAMF_C16_3_CANDIDATE_HORIZON_DRIFT")
        steps.append(step)
        observe_completed_step_fn(observer, step, candidate)
        if getattr(candidate, "motif_transition", None) is not None:
            break
    return steps, capture


def candidate_horizon_execution(
        run_dir, parent, context, atlas_path, feature_path, selection, rows,
        capability, host_cache, steps_per_visit, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer, *,
        bind_cache, horizon_for, rejection_ordinals, execute_horizon_fn,
        currentness_metrics_fn, emit_progress, identity_snapshot):
    cache = host_cache if host_cache is not None else bind_cache(run_dir)
    horizon = horizon_for(run_dir, parent, cache, capability, steps_per_visit)
    rejection_journal_ordinal, rejection_attempt_ordinal = rejection_ordinals(
        run_dir, parent, cache, capability)
    emit_progress(
        progress,
        f"candidate horizon is atomic for up to {horizon} optimizer steps; "
        "the session time limit is checked between candidate visits")
    if observer is not None:
        observer.update(
            phase="TRAINING", capability_id=capability, candidate_step=0,
            candidate_horizon=horizon,
            candidate_optimizer_step=parent.retained_state.optimizer_step)
    identity_before = identity_snapshot()
    steps, capture = execute_horizon_fn(
        run_dir, selection, context, parent, atlas_path, feature_path, rows, horizon,
        cache, rejection_journal_ordinal, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer)
    if observer is not None:
        metrics = currentness_metrics_fn(
            selection.offer._planning_generation._accepted_currentness)
        observer.update(
            currentness_deep_authentications=metrics["deep_authentication_count"],
            currentness_accepted_cache_checks=metrics[
                "accepted_cache_currentness_count"],
            currentness_full_candidate_identity_hashes=metrics[
                "full_candidate_identity_hashes"],
            currentness_bundle_tree_scans=metrics["bundle_tree_scans"],
        )
    return (
        cache, steps, capture, rejection_journal_ordinal,
        rejection_attempt_ordinal, identity_before,
    )


def retention_result(
        run_dir, parent, context, atlas_path, selection, capability, cache, steps,
        capture, rejection_journal_ordinal, rejection_attempt_ordinal,
        identity_before, progress, observer, *, evaluate_candidate,
        issue_decision, identity_delta, resource_observation,
        derive_successor, prepared_visit_type, emit_progress,
        measure_observed_phase_fn):
    step = steps[-1]
    if observer is not None:
        observer.update(phase="RETENTION")
    emit_progress(progress, "evaluating retention evidence")
    with measure_observed_phase_fn(observer, "retention_wall_seconds"):
        evaluation = evaluate_candidate(
            context, step.transaction, atlas_path, capability, run_dir=run_dir,
            **({"observer": lambda fields: observer.update(**fields)}
               if observer is not None else {}))
        decision = issue_decision(evaluation)
        identity_metrics = identity_delta(identity_before)
        retained = (
            evaluation.candidate_state if decision.accepted else evaluation.parent_state)
    with measure_observed_phase_fn(observer, "evidence_finalization_wall_seconds"):
        candidate_evidence = capture.finalize(
            accepted=decision.accepted, decision=decision.to_record())
    resource = resource_observation(
        run_dir, tuple(steps),
        getattr(context, "_source_preparation_metrics", None),
        identity_metrics=identity_metrics)
    resource.update({
        "evidence_bytes_written": candidate_evidence["persistence"]["bytes_written"],
        "evidence_file_fsyncs": candidate_evidence["persistence"]["file_fsyncs"],
        "evidence_directory_fsyncs": candidate_evidence["persistence"]["directory_fsyncs"],
        "evidence_objects": candidate_evidence["persistence"]["evidence_objects"],
        "evidence_persistence_seconds": candidate_evidence["persistence"]["persistence_seconds"],
    })
    successor = None
    if decision.accepted:
        successor = derive_successor(
            run_dir, retained, selection.visit,
            delivery_events=({
                "event": "BAMF_C16_3_ACCEPTED",
                "optimizer_step": retained.optimizer_step,
                "parent_generation": cache.generation,
                "accepted_manifest_sha256": cache.accepted_manifest_sha256,
                "candidate_attempt_ordinal": rejection_journal_ordinal,
                "capability": capability,
                "visit_id": selection.visit.identity.visit_id,
                "selected_policy_key": selection.visit.identity.policy_key,
                "selected_option_id": selection.option_id,
                "resource": resource,
                "candidate_evidence": candidate_evidence,
            },))
    return prepared_visit_type(
        "ACCEPTED" if decision.accepted else "REJECTED", parent,
        selection=selection, step=step, steps=tuple(steps), decision=decision,
        retained=retained, capability=capability, successor=successor,
        identity_metrics=identity_metrics, resource=resource,
        candidate_evidence=candidate_evidence,
        rejection_journal_ordinal=rejection_journal_ordinal,
        rejection_attempt_ordinal=rejection_attempt_ordinal)


def operate(
        run_dir, *, minutes, max_visits, steps_per_visit, reserve_gib,
        source_prefetch_workers, progress, max_horizon, worker_counts,
        invalid, metrics_type, source_pool_factory, null_context,
        operator_lock, visit_fn, observer_type, emit_progress,
        monotonic, load_generation, result_type):
    if (type(minutes) is not int or minutes < 1 or type(max_visits) is not int
            or max_visits < 0 or type(steps_per_visit) is not int
            or not 1 <= steps_per_visit <= max_horizon
            or type(source_prefetch_workers) is not int
            or source_prefetch_workers not in worker_counts
            or reserve_gib < 0):
        invalid("BAMF_OPERATOR_SESSION_BOUNDS_INVALID")
    run_dir = run_dir.resolve()
    deadline = monotonic() + minutes * 60
    visits = accepted = rejected = 0
    status = "TIME_LIMIT"
    metrics = metrics_type()
    source_pool = (
        source_pool_factory(source_prefetch_workers)
        if source_prefetch_workers else null_context(None))
    with source_pool as source_prefetch_executor, operator_lock(run_dir):
        while monotonic() < deadline and (not max_visits or visits < max_visits):
            emit_progress(progress, f"starting visit {visits + 1}")
            with observer_type(run_dir, visits + 1) as observer:
                outcome = visit_fn(
                    run_dir, reserve_gib, steps_per_visit=steps_per_visit,
                    progress=progress,
                    source_prefetch_workers=source_prefetch_workers,
                    source_prefetch_executor=source_prefetch_executor,
                    source_prefetch_metrics=metrics, observer=observer)
                observer.finish(outcome)
            emit_progress(progress, f"visit {visits + 1} outcome: {outcome}")
            if outcome in {"HELD", "ACTION_REQUIRED"}:
                status = "PRIORITY_HOLD" if outcome == "HELD" else "ACTION_REQUIRED"
                break
            visits += 1
            if outcome == "REJECTED":
                rejected += 1
                continue
            accepted += 1
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
        source_prefetch_serial_steps=metrics.serial_steps)
