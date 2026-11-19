"""One terminal BAMF visit, separated from the session coordinator."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceRejectedVisit:
    capability: str


def visit(
        run_dir, reserve_gib, *, steps_per_visit, progress,
        source_prefetch_workers, source_prefetch_executor,
        source_prefetch_metrics, observer, run_authority_binding,
        prepare_visit, record_rejection,
        accept_publish, load_generation, measure_phase, emit_progress,
        record_cadence_attempt=None, resource_holds=frozenset()):
    prepared = prepare_visit(
        run_dir, steps_per_visit=steps_per_visit, reserve_gib=reserve_gib,
        progress=progress,
        source_prefetch_workers=source_prefetch_workers,
        source_prefetch_executor=source_prefetch_executor,
        source_prefetch_metrics=source_prefetch_metrics,
        **({"observer": observer} if observer is not None else {}),
        **({"resource_holds": resource_holds} if resource_holds else {}))
    if prepared.status in {
        "HELD", "RESOURCE_HOLD", "ACTION_REQUIRED", "GRADE_TRANSITIONED",
        "CERTIFICATION_FAILED", "CERTIFICATION_SUPERSEDED",
    }:
        return prepared.status
    parent, selection = prepared.parent, prepared.selection
    if prepared.status == "RESOURCE_REJECTED":
        if run_authority_binding is not None:
            run_authority_binding.assert_current()
        identity = selection.visit.identity
        record_rejection(run_dir, parent, {
            **prepared.resource,
            "capability": prepared.capability,
            "visit_id": identity.visit_id,
            "teacher_visit": identity.to_record(),
            "selected_policy_key": identity.policy_key,
        })
        return ResourceRejectedVisit(prepared.capability)
    step, decision, retained = prepared.step, prepared.decision, prepared.retained
    if not decision.accepted:
        cadence = (getattr(selection, "metadata", None) or {}).get("cadence")
        record_rejection(run_dir, parent, {
            "schema": "bilqis.bamf.c16.3-rejection/v2",
            "rejection_attempt_ordinal": prepared.rejection_attempt_ordinal,
            "rejection_journal_ordinal": prepared.rejection_journal_ordinal,
            "visit_id": selection.visit.identity.visit_id,
            "teacher_visit": selection.visit.identity.to_record(),
            "selected_option_id": selection.option_id,
            "selected_policy_key": selection.visit.identity.policy_key,
            "candidate_optimizer_step": (
                step.transaction.parent.optimizer_step + step.transaction.update_steps),
            "retained_optimizer_step": parent.retained_state.optimizer_step,
            "retention_reason": decision.reason,
            "capability": prepared.capability,
            "decision": decision.to_record(),
            "resource": prepared.resource,
            "candidate_evidence": prepared.candidate_evidence,
            "how_outcome": prepared.how_outcome,
            "structural_weaknesses": list(prepared.structural_weaknesses),
            **({"cadence": cadence} if cadence is not None else {}),
        })
        if cadence is not None and record_cadence_attempt is not None:
            record_cadence_attempt(run_dir, cadence, prepared.capability)
        return "REJECTED"
    successor = prepared.successor
    if observer is not None:
        observer.update(phase="PUBLISHING")
    emit_progress(progress, "publishing accepted successor checkpoint")
    if run_authority_binding is not None:
        run_authority_binding.assert_current()
    with measure_phase(observer, "publishing_wall_seconds"):
        accept_publish(
            run_dir, successor, retained, decision=decision,
            feature_sha256=successor.extents.factor_map_digest,
            reserve_gib=reserve_gib,
            training_authorities=step.transaction.training_authorities,
            publication_observer=(
                (lambda metrics: observer.update(**{
                    "publication_" + key: value
                    for key, value in metrics.to_record().items()}))
                if observer is not None else None))
    cadence = (getattr(selection, "metadata", None) or {}).get("cadence")
    if cadence is not None and record_cadence_attempt is not None:
        record_cadence_attempt(run_dir, cadence, prepared.capability)
    health = getattr(prepared, "learning_health", None)
    if observer is not None and isinstance(health, dict):
        observer.learning_health_by_capability[
            health["capability_id"]] = health
        observer.update(learning_health=health)
    return "ACCEPTED"


__all__ = ("visit",)
