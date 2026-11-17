"""Retention and accepted-successor helpers for the BAMF operator session."""
from __future__ import annotations


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


def _rejected_structural_weaknesses(
        run_dir, context, selection, candidate_evidence, decision, how_outcome):
    from bilqis_mlx.runtime.source_execution import SourceExecutionContext
    if not isinstance(context, SourceExecutionContext):
        return ()
    from bilqis_mlx.runtime.structural_weakness_replay import (
        derive_rejected_weaknesses,
    )
    return derive_rejected_weaknesses(
        run_dir, context, selection, candidate_evidence,
        rejection_reason=decision.reason,
        outcome_sha256=how_outcome["outcome_sha256"])


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
            from ..evidence_projection import complete_visit_evidence
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
        run_dir, tuple(steps), getattr(context, "_source_preparation_metrics", None),
        identity_metrics=identity_metrics)
    resource.update({
        "evidence_bytes_written": candidate_evidence["persistence"]["bytes_written"],
        "evidence_file_fsyncs": candidate_evidence["persistence"]["file_fsyncs"],
        "evidence_directory_fsyncs": candidate_evidence["persistence"]["directory_fsyncs"],
        "evidence_objects": candidate_evidence["persistence"]["evidence_objects"],
        "evidence_persistence_seconds": candidate_evidence["persistence"]["persistence_seconds"],
    })
    from bilqis_mlx.runtime.outcomes.issuance import (
        build_outcome, carry_credit_to_successor, credited_visit,
    )
    how_outcome = build_outcome(run_dir, selection, evaluation, decision, candidate_evidence)
    structural_weaknesses = (() if decision.accepted else _rejected_structural_weaknesses(
        run_dir, context, selection, candidate_evidence, decision, how_outcome))
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
        structural_weaknesses=structural_weaknesses,
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
        from ..learning_health_runtime import accepted_learning_health_state
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
        **({"cadence": getattr(selection, "metadata", {}).get("cadence")}
           if isinstance(getattr(selection, "metadata", None), dict)
           and selection.metadata.get("cadence") is not None else {}),
    }, instruction_event)
    successor = derive_successor(
        run_dir, retained, learned_visit, delivery_events=events)
    if health_state is not None:
        from dataclasses import replace
        successor = replace(successor, learning_health_state=health_state)
    successor = carry_credit_to_successor(learned_visit, successor, parent)
    successor = bind_baseline_successor(evaluation, successor)
    from ..championship import bind_accepted_championship_successor
    successor = bind_accepted_championship_successor(
        run_dir, parent, cache, successor, context, atlas_path,
        capability, evaluation,
        checkpoint_origin_group=getattr(selection, "lesson_grade", None))
    return successor, learning_health


__all__ = ("retention_result",)
