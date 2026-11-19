"""Retention and accepted-successor helpers for the BAMF operator session."""
from __future__ import annotations

import hashlib
import json


def _contract_digest(payload) -> str:
    wire = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(wire.encode()).hexdigest()


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


def _distributed_retention_metrics(steps, evaluation, decision, observer, resource):
    """Bind post-C05 retained-learning facts to distributed execution receipts."""
    costs = tuple(
        step.realized_cost for step in steps
        if isinstance(getattr(step, "realized_cost", None), dict)
        and "c08_distributed_manifest_digest" in step.realized_cost)
    if not costs:
        return
    record = getattr(observer, "record", {}) if observer is not None else {}
    evaluation_seconds = (
        record.get("retention_wall_seconds") if isinstance(record, dict) else None)
    if (type(evaluation_seconds) not in (int, float)
            or type(evaluation_seconds) is bool or evaluation_seconds < 0):
        return
    scores = getattr(getattr(evaluation, "decision", None), "outcome_scores", ())
    gains = tuple(
        (after - before) / total
        for _capability, before, after, total in scores
        if type(total) is int and total > 0)
    retained_gain = (
        sum(gains) / len(gains) if decision.accepted and gains else 0.0)
    candidate_wall_seconds = sum(float(
        cost.get("candidate_step_wall_seconds", cost.get("wall_seconds", 0.0)))
        for cost in costs)
    elapsed = candidate_wall_seconds + float(evaluation_seconds)
    source_contract_digest = _contract_digest([{
        "retained_generation": cost["c08_distributed_retained_generation"],
        "retained_manifest_sha256":
            cost["c08_distributed_retained_manifest_sha256"],
        "logical_batch_digest": cost["c08_distributed_logical_batch_digest"],
        "source_release": cost["c08_distributed_source_release"],
        "curriculum_release": cost["c08_distributed_curriculum_release"],
    } for cost in costs])
    evaluation_contract_digest = _contract_digest({
        "policy_sha256": evaluation.decision.policy_sha256,
        "retention_protection_plan_sha256": getattr(
            decision, "retention_protection_plan_sha256", None),
        "evaluated_capability_ids": tuple(
            getattr(decision, "evaluated_capability_ids", ())),
        "broad_certification_trigger": getattr(
            decision, "broad_certification_trigger", None),
    })
    resource.update({
        "c08_distributed_manifest_digests": tuple(
            cost["c08_distributed_manifest_digest"] for cost in costs),
        "c08_distributed_evaluation_seconds": float(evaluation_seconds),
        "c08_distributed_accepted_steps_per_hour": (
            resource["optimizer_steps"] * 3600.0 / elapsed
            if decision.accepted and elapsed > 0 else 0.0),
        "c08_distributed_retained_capability_gain": retained_gain,
        "c08_distributed_source_contract_digest": source_contract_digest,
        "c08_distributed_evaluation_contract_digest":
            evaluation_contract_digest,
    })


def _complete_observer_evidence(
        observer, capture, run_dir, candidate_evidence, decision):
    if observer is None:
        return
    try:
        methodology = getattr(capture, "learning_methodology", None)
        if callable(methodology):
            observer.update(learning_methodology=methodology())
        from ..evidence_projection import complete_visit_evidence
        record = getattr(observer, "record", {})
        current_visit = (
            record.get("visit_evidence") if isinstance(record, dict) else None
        ) or {"schema": "bilqis.bamf.visit-evidence/v1", "state": "PARTIAL"}
        observer.update(visit_evidence=complete_visit_evidence(
            run_dir, current_visit, candidate_evidence, decision))
    except Exception:
        # Projection is observation-only and must not gate C05/B13 completion.
        pass


def _retention_resource(
        run_dir, steps, context, identity_metrics, candidate_evidence,
        resource_observation):
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
    return resource


def retention_result(
        run_dir, parent, context, atlas_path, selection, capability, cache, steps,
        capture, rejection_journal_ordinal, rejection_attempt_ordinal,
        identity_before, progress, observer, *, evaluate_candidate,
        issue_decision, identity_delta, resource_observation,
        derive_successor, bind_baseline_successor, finalize_generation_authority,
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
    _complete_observer_evidence(
        observer, capture, run_dir, candidate_evidence, decision)
    resource = _retention_resource(
        run_dir, steps, context, identity_metrics, candidate_evidence,
        resource_observation)
    _distributed_retention_metrics(steps, evaluation, decision, observer, resource)
    from bilqis_mlx.runtime.outcomes.issuance import (
        build_outcome, carry_credit_to_successor, credited_visit,
    )
    how_outcome = build_outcome(run_dir, selection, evaluation, decision, candidate_evidence)
    structural_weaknesses = (() if decision.accepted else _rejected_structural_weaknesses(
        run_dir, context, selection, candidate_evidence, decision, how_outcome))
    successor, learning_health = _accepted_successor(
        decision, run_dir, parent, context, atlas_path, selection, capability,
        cache, retained, step.transaction, observer,
        rejection_journal_ordinal, resource, candidate_evidence, capture, how_outcome,
        derive_successor, bind_baseline_successor, evaluation,
        credited_visit, carry_credit_to_successor, plasticity_escape,
        finalize_generation_authority)
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
        cache, retained, candidate_transaction, observer,
        rejection_journal_ordinal, resource, candidate_evidence, capture, how_outcome,
        derive_successor, bind_baseline_successor, evaluation,
        credited_visit, carry_credit_to_successor, plasticity_escape,
        finalize_generation_authority):
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
        run_dir, retained, learned_visit, delivery_events=events,
        candidate_transaction=candidate_transaction)
    if health_state is not None:
        from dataclasses import replace
        successor = replace(successor, learning_health_state=health_state)
    successor = carry_credit_to_successor(learned_visit, successor, parent)
    successor = bind_baseline_successor(evaluation, successor)
    from ..championship import (
        bind_accepted_championship_successor,
        championship_boundary_capabilities,
    )
    championship_scope = championship_boundary_capabilities(selection, capability)
    if championship_scope:
        from bilqis_mlx.runtime._factory_retention_support import _training_exclusions
        from bilqis_mlx.runtime.factory_retention_owner import CURRENT_EVIDENCE_STAGE
        successor = bind_accepted_championship_successor(
            run_dir, parent, cache, successor, context, atlas_path,
            capability, evaluation,
            checkpoint_origin_group=getattr(selection, "lesson_grade", None),
            training=_training_exclusions(candidate_transaction),
            evidence_stage=CURRENT_EVIDENCE_STAGE,
            observer=(lambda fields: observer.update(**fields)) if observer is not None else None,
            boundary_capabilities=championship_scope)
    if (getattr(evaluation, "candidate_generation_authority_sha256", None) is not None
            and getattr(candidate_transaction, "motif_transition", None) is not None):
        finalize_generation_authority(
            evaluation, decision, parent, candidate_transaction, successor)
    return successor, learning_health


__all__ = ("retention_result",)
