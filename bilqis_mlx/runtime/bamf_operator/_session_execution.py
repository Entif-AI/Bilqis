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
    introductory = None
    try:
        from bilqis_mlx.learning.teacher_lineage import instruction_history
        from bilqis_mlx.runtime.priority_rejection_replay import rejection_recency
        projected_teacher = getattr(
            getattr(getattr(selection, "visit", None), "projection", None),
            "teacher_state", None)
        history_state, seen = instruction_history(
            projected_teacher if projected_teacher is not None else parent.teacher_state)
        _, rejected = rejection_recency(run_dir, parent, cache)
        capability = selection.offer.capability_id
        introductory = (
            False if capability in set(seen) | set(rejected)
            else True if history_state == "COMPLETE"
            else None)
    except (AttributeError, TypeError, ValueError, KeyError):
        introductory = None
    capture_kwargs = dict(
        generation=cache.generation,
        accepted_manifest_sha256=cache.accepted_manifest_sha256,
        candidate_attempt_ordinal=candidate_attempt_ordinal,
        parent_optimizer_step=parent.retained_state.optimizer_step,
    )
    if introductory is not None:
        capture_kwargs["introductory"] = introductory
    capture = capture_cls(run_dir, selection, **capture_kwargs)
    steps, candidate = [], None
    for ordinal in range(1, horizon + 1):
        candidate_step_started_at = time.perf_counter()
        begin_step = getattr(observer, 'begin_step', None)
        if callable(begin_step):
            begin_step(ordinal, parent.retained_state.optimizer_step + ordinal)
        source_prepare_started = candidate_step_started_at
        lesson = None if source_lane is None else source_lane.lesson(ordinal)
        source_rows = rows if lesson is None else lesson.direct
        enrichment_rows = () if lesson is None else lesson.enrichment
        source_prepare_wall_seconds = time.perf_counter() - source_prepare_started
        observation = delivery_observation_cls(
            capture, parent.retained_state.optimizer_step + ordinal,
            source_rows, selection.offer.source_seed, enrichment=enrichment_rows)
        emit_progress(progress, f"executing candidate step {ordinal}/{horizon}")
        step = execute_candidate(
            selection, context, atlas_path, feature_path,
            teacher_hparams=parent.optimizer_hyperparameters,
            observation=observation,
            optimizer_step_seed=step_seed(selection.visit.identity.visit_id, ordinal),
            max_norm=1.0, candidate=candidate,
            finalize_candidate=(ordinal == horizon),
            prepared_source_rows=(source_rows if source_lane is not None else None),
            prepared_enrichment_rows=enrichment_rows,
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


def _observe_retention_scope(observer, decision):
    if observer is None:
        return
    fields = {
        "retention_evaluated_capability_count": len(
            getattr(decision, "evaluated_capability_ids", ())),
        "retention_protection_plan_sha256": getattr(
            decision, "retention_protection_plan_sha256", None),
        "retention_broad_certification_trigger": getattr(
            decision, "broad_certification_trigger", None),
    }
    stage = getattr(observer, "stage", None)
    (stage if callable(stage) else observer.update)(**fields)


def retention_result(
        run_dir, parent, context, atlas_path, selection, capability, cache, steps,
        capture, rejection_journal_ordinal, rejection_attempt_ordinal,
        identity_before, progress, observer, *, evaluate_candidate,
        issue_decision, identity_delta, resource_observation,
        derive_successor, bind_baseline_successor,
        prepared_visit_type, emit_progress,
        measure_observed_phase_fn, derive_plasticity_escape=None):
    step = steps[-1]
    if observer is not None:
        observer.update(phase="RETENTION")
    emit_progress(progress, "evaluating retention evidence")
    with measure_observed_phase_fn(observer, "retention_wall_seconds"):
        release = getattr(context, "release", None)
        plasticity_escape = (
            derive_plasticity_escape(parent, selection, release)
            if derive_plasticity_escape is not None and release is not None else None)
        evaluation = evaluate_candidate(
            context, step.transaction, atlas_path, capability, run_dir=run_dir,
            **({"plasticity_escape": plasticity_escape}
               if plasticity_escape is not None else {}),
            **({"observer": lambda fields: observer.update(**fields)}
               if observer is not None else {}))
        decision = issue_decision(evaluation)
        _observe_retention_scope(observer, decision)
        if not decision.accepted:
            from bilqis_mlx.errors.authority import authority_label
            emit_progress(progress, "retention decision: " + authority_label(
                getattr(decision, "reason", None), blocking_capability=getattr(
                    getattr(evaluation, "decision", None), "blocking_capability", None),
                blocking_scope=getattr(
                    getattr(evaluation, "decision", None), "blocking_scope", None)))
        identity_metrics = identity_delta(identity_before)
        retained = (
            evaluation.candidate_state if decision.accepted else evaluation.parent_state)
    with measure_observed_phase_fn(observer, "evidence_finalization_wall_seconds"):
        candidate_evidence = capture.finalize(
            accepted=decision.accepted, decision=decision.to_record())
    if observer is not None:
        try:
            methodology = getattr(capture, "learning_methodology", None)
            if callable(methodology):
                observer.update(learning_methodology=methodology())
            from .evidence_projection import complete_visit_evidence
            record = getattr(observer, "record", {})
            current_visit = (record.get("visit_evidence")
                             if isinstance(record, dict) else None) or {
                "schema": "bilqis.bamf.visit-evidence/v1", "state": "PARTIAL"}
            observer.update(visit_evidence=complete_visit_evidence(
                run_dir, current_visit, candidate_evidence, decision))
        except Exception:
            # Projection is observation-only and must not gate C05/B13 completion.
            pass
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
    from bilqis_mlx.runtime.outcomes.issuance import build_outcome, credited_visit, carry_credit_to_successor
    how_outcome = build_outcome(run_dir, selection, evaluation, decision, candidate_evidence)
    successor, learning_health = _accepted_successor(
        decision, run_dir, parent, context, atlas_path, selection, capability,
        cache, retained,
        rejection_journal_ordinal, resource, candidate_evidence, capture, how_outcome,
        derive_successor, bind_baseline_successor, evaluation,
        credited_visit, carry_credit_to_successor, plasticity_escape)
    return prepared_visit_type(
        "ACCEPTED" if decision.accepted else "REJECTED", parent,
        selection=selection, step=step, steps=tuple(steps), decision=decision,
        retained=retained, capability=capability, successor=successor,
        identity_metrics=identity_metrics, resource=resource,
        candidate_evidence=candidate_evidence, how_outcome=how_outcome,
        learning_health=learning_health,
        rejection_journal_ordinal=rejection_journal_ordinal,
        rejection_attempt_ordinal=rejection_attempt_ordinal)


def _instruction_event(run_dir, parent, cache, capability):
    try:
        from bilqis_mlx.learning.teacher_lineage import instruction_history
        from bilqis_mlx.runtime.priority_rejection_replay import rejection_recency
        history_state, seen = instruction_history(parent.teacher_state)
        _, rejected = rejection_recency(run_dir, parent, cache)
        return {
            "event": "BAMF_INSTRUCTION_HISTORY",
            "schema": "bilqis.bamf.instruction-history/v1",
            "state": history_state,
            "capability_ids": sorted(set(seen) | set(rejected) | {capability}),
        }
    except (AttributeError, TypeError, ValueError, KeyError):
        return {
            "event": "BAMF_INSTRUCTION_HISTORY",
            "schema": "bilqis.bamf.instruction-history/v1",
            "state": "PARTIAL", "capability_ids": [capability],
        }


def _accepted_successor(
        decision, run_dir, parent, context, atlas_path, selection, capability,
        cache, retained,
        rejection_journal_ordinal, resource, candidate_evidence, capture, how_outcome,
        derive_successor, bind_baseline_successor, evaluation,
        credited_visit, carry_credit_to_successor, plasticity_escape):
    if not decision.accepted:
        return None, None
    learned_visit = credited_visit(selection.visit, how_outcome)
    instruction_event = _instruction_event(run_dir, parent, cache, capability)
    learning_health = None
    try:
        from .learning_health_runtime import accepted_learning_health_state
        health_state, learning_health = accepted_learning_health_state(
            run_dir, parent, selection, candidate_evidence, decision, retained, capture,
            plasticity_escape=plasticity_escape)
    except (AttributeError, TypeError, ValueError, KeyError):
        health_state = None
    events = ({
        "event": "BAMF_C16_3_ACCEPTED",
        "optimizer_step": retained.optimizer_step,
        "parent_generation": cache.generation,
        "accepted_manifest_sha256": cache.accepted_manifest_sha256,
        "candidate_attempt_ordinal": rejection_journal_ordinal,
        "capability": capability,
        "visit_id": selection.visit.identity.visit_id,
        "selected_policy_key": selection.visit.identity.policy_key,
        "selected_option_id": selection.option_id,
        "resource": resource, "candidate_evidence": candidate_evidence,
        "how_outcome": how_outcome,
    }, instruction_event)
    successor = derive_successor(
        run_dir, retained, learned_visit, delivery_events=events)
    if health_state is not None:
        from dataclasses import replace
        successor = replace(successor, learning_health_state=health_state)
    successor = carry_credit_to_successor(learned_visit, successor, parent)
    successor = bind_baseline_successor(evaluation, successor)
    from .championship import bind_accepted_championship_successor
    successor = bind_accepted_championship_successor(
        run_dir, parent, cache, successor, context, atlas_path,
        capability, evaluation,
        checkpoint_origin_group=getattr(selection, "lesson_grade", None))
    return successor, learning_health


def operate(
        run_dir, *, minutes, max_visits, steps_per_visit, reserve_gib,
        source_prefetch_workers, progress, max_horizon, worker_counts,
        invalid, metrics_type, source_pool_factory, null_context,
        operator_lock, visit_fn, observer_type, emit_progress,
        monotonic, load_generation, result_type, accepted_reentry=None):
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
    admission_status = None
    admission_advances = 0
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
            if accepted_reentry is not None:
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
