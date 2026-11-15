"""C16.3 persistent BAMF-native human session.

This coordinator composes existing owners.  It is not a curriculum, teacher,
retention, source, optimizer, or publication authority.
"""
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
import time

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.learning.atlas_candidate import resolve_candidate
from bilqis_mlx.learning.atlas_retention_decision import issue_factory_retention_decision
from bilqis_mlx.runtime.accepted_priority_visit import (
    accepted_priority_school, execute_accepted_priority_candidate,
)
from bilqis_mlx.runtime.bamf_bundle import record_bamf_rejection
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, bind_accepted_execution_cache, load_accepted_generation,
)
from bilqis_mlx.runtime.factory_candidate_training import FactoryDeliveryObservation
from bilqis_mlx.runtime.factory_retention_owner import evaluate_factory_retention_candidate
from bilqis_mlx.runtime.foundation_teacher_owner import (
    derive_accepted_teacher_successor, select_foundation_priority_visit,
)
from bilqis_mlx.runtime.priority_rejection_replay import (
    candidate_step_horizon, rejection_attempt_ordinals,
)
from .locking import bamf_operator_lock
from .telemetry import TrainerObservation
from .session_support import (
    BamfPreparedVisit, _Capture, _execution_context, _resource_observation, _step_seed,
)
from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
    VisitCurrentnessMetrics, currentness_metrics,
)
from .source_prefetch import (
    CandidateSourceLane, NATIVE_SOURCE_WORKER_COUNTS, SourcePrefetchMetrics,
)

_MAX_CANDIDATE_HORIZON = 16

def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_FIRST_STUDENT.INVALID, reason=reason)

@dataclass(frozen=True)
class BamfOperatorResult:
    status: str
    visits: int
    accepted: int
    rejected: int
    generation: int
    optimizer_step: int
    source_prefetch_workers: int = 0
    source_prefetch_wait_seconds: float = 0.0
    source_prefetch_overlap_seconds: float = 0.0
    source_prefetch_prepared_steps: int = 0
    source_prefetch_serial_steps: int = 0

def _emit_progress(progress, message: str) -> None:
    if progress is not None:
        progress(message)

def _execute_horizon(run_dir, selection, context, parent, atlas_path, feature_path,
                     rows, horizon, progress, source_prefetch_workers,
                     source_prefetch_executor, source_prefetch_metrics, observer):
    source_lane = None
    if source_prefetch_metrics is not None or source_prefetch_workers:
        metrics = source_prefetch_metrics or SourcePrefetchMetrics()
        source_lane = CandidateSourceLane(
            selection, context, parent, horizon, workers=source_prefetch_workers,
            executor=source_prefetch_executor, metrics=metrics)
    capture = _Capture(run_dir, selection)
    steps, candidate = [], None
    for ordinal in range(1, horizon + 1):
        source_rows = rows if source_lane is None else source_lane.rows(ordinal)
        observation = FactoryDeliveryObservation(
            capture, parent.retained_state.optimizer_step + ordinal,
            source_rows, selection.offer.source_seed)
        _emit_progress(progress, f"executing candidate step {ordinal}/{horizon}")
        step = execute_accepted_priority_candidate(
            selection, context, atlas_path, feature_path,
            teacher_hparams=parent.optimizer_hyperparameters,
            observation=observation,
            optimizer_step_seed=_step_seed(selection.visit.identity.visit_id, ordinal),
            max_norm=1.0, candidate=candidate,
            finalize_candidate=(ordinal == horizon),
            prepared_source_rows=(source_rows if source_lane is not None else None))
        candidate = step.transaction
        if candidate.update_steps != ordinal:
            _invalid("BAMF_C16_3_CANDIDATE_HORIZON_DRIFT")
        steps.append(step)
        if observer is not None:
            observer.update(candidate_step=candidate.update_steps,
                            candidate_optimizer_step=candidate.parent.optimizer_step + candidate.update_steps)
        if getattr(candidate, "motif_transition", None) is not None:
            break
    return steps

def prepare_bamf_visit(
        run_dir: Path, *, steps_per_visit: int = 16,
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
    school = accepted_priority_school(
        parent, program,
        candidate_identity_sha256=getattr(
            host_cache, "_candidate_identity_sha256", None))
    _emit_progress(progress, "planning current candidate frontier and teacher priority")
    selection = select_foundation_priority_visit(
        run_dir, context, atlas_path, program=program, school=school,
        progress=progress)
    if selection.status != "TEACHER_SELECTED":
        status = "ACTION_REQUIRED" if selection.status == "ACTION_REQUIRED" else "HELD"
        return BamfPreparedVisit(status, parent, selection=selection)
    rows = selection.offer.rows()
    _emit_progress(
        progress,
        f"selected {selection.offer.capability_id} with {len(rows)} source rows")
    capability = selection.offer.capability_id
    cache = host_cache if host_cache is not None else bind_accepted_execution_cache(run_dir)
    horizon = candidate_step_horizon(
        run_dir, parent, cache, capability, steps_per_visit)
    _emit_progress(
        progress,
        f"candidate horizon is atomic for up to {horizon} optimizer steps; "
        "the session time limit is checked between candidate visits")
    if observer is not None:
        observer.update(phase="TRAINING", capability_id=capability, candidate_step=0,
                        candidate_horizon=horizon, candidate_optimizer_step=parent.retained_state.optimizer_step)
    steps = _execute_horizon(
        run_dir, selection, context, parent, atlas_path, feature_path, rows, horizon,
        progress, source_prefetch_workers, source_prefetch_executor,
        source_prefetch_metrics, observer)
    if observer is not None:
        metrics = currentness_metrics(
            selection.offer._planning_generation._accepted_currentness)
        observer.update(
            currentness_deep_authentications=metrics["deep_authentication_count"],
            currentness_accepted_cache_checks=metrics[
                "accepted_cache_currentness_count"],
            currentness_full_candidate_identity_hashes=metrics[
                "full_candidate_identity_hashes"],
            currentness_bundle_tree_scans=metrics["bundle_tree_scans"],
        )
    step = steps[-1]
    if observer is not None:
        observer.update(phase="RETENTION")
    _emit_progress(progress, "evaluating retention evidence")
    evaluation = evaluate_factory_retention_candidate(
        context, step.transaction, atlas_path, capability, run_dir=run_dir,
        **({"observer": lambda fields: observer.update(**fields)} if observer is not None else {}))
    decision = issue_factory_retention_decision(evaluation)
    retained = resolve_candidate(step.transaction, accepted=decision.accepted)
    successor = None
    if decision.accepted:
        successor = derive_accepted_teacher_successor(
            run_dir, retained, selection.visit,
            delivery_events=({
                "event": "BAMF_C16_3_ACCEPTED",
                "optimizer_step": retained.optimizer_step,
                "capability": capability,
                "resource": _resource_observation(run_dir, tuple(steps)),
            },))
    return BamfPreparedVisit(
        "ACCEPTED" if decision.accepted else "REJECTED", parent,
        selection=selection, step=step, steps=tuple(steps), decision=decision,
        retained=retained, capability=capability, successor=successor)

def _visit(run_dir: Path, reserve_gib: float, *, steps_per_visit=16,
           progress=None, source_prefetch_workers=0,
           source_prefetch_executor=None, source_prefetch_metrics=None, observer=None):
    prepared = prepare_bamf_visit(
        run_dir, steps_per_visit=steps_per_visit, progress=progress,
        source_prefetch_workers=source_prefetch_workers,
        source_prefetch_executor=source_prefetch_executor,
        source_prefetch_metrics=source_prefetch_metrics,
        **({"observer": observer} if observer is not None else {}))
    if prepared.status in {"HELD", "ACTION_REQUIRED"}:
        return prepared.status
    parent = prepared.parent
    selection = prepared.selection
    step = prepared.step
    decision = prepared.decision
    retained = prepared.retained
    capability = prepared.capability
    if not decision.accepted:
        offer = getattr(selection, "offer", None)
        planning_generation = getattr(offer, "_planning_generation", None)
        cache = (
            planning_generation._cache
            if planning_generation is not None
            else bind_accepted_execution_cache(run_dir)
        )
        rejection_journal_ordinal, rejection_attempt_ordinal = rejection_attempt_ordinals(
            run_dir, parent, cache, capability)
        record_bamf_rejection(run_dir, parent, {
            "schema": "bilqis.bamf.c16.3-rejection/v2",
            "rejection_attempt_ordinal": rejection_attempt_ordinal,
            "rejection_journal_ordinal": rejection_journal_ordinal,
            "visit_id": selection.visit.identity.visit_id,
            "teacher_visit": selection.visit.identity.to_record(),
            "selected_option_id": selection.option_id,
            "selected_policy_key": selection.visit.identity.policy_key,
            "candidate_optimizer_step": (
                step.transaction.parent.optimizer_step + step.transaction.update_steps),
            "retained_optimizer_step": parent.retained_state.optimizer_step,
            "retention_reason": decision.reason,
            "capability": capability,
            "decision": decision.to_record(),
        })
        return "REJECTED"
    successor = prepared.successor
    if observer is not None:
        observer.update(phase="PUBLISHING")
    _emit_progress(progress, "publishing accepted successor checkpoint")
    accept_and_publish(
        run_dir, successor, retained, decision=decision,
        feature_sha256=successor.extents.factor_map_digest,
        reserve_gib=reserve_gib,
        training_authorities=step.transaction.training_authorities)
    return "ACCEPTED"

def operate_bamf(
    run_dir: Path, *, minutes: int = 90,
    max_visits: int = 0, steps_per_visit: int = 16,
    reserve_gib: float = 100.0,
    source_prefetch_workers: int = 2,
    progress=None,
) -> BamfOperatorResult:
    """Run the human-authorized BAMF lineage until a bounded stop condition."""
    if (type(minutes) is not int or minutes < 1 or type(max_visits) is not int
            or max_visits < 0 or type(steps_per_visit) is not int
            or not 1 <= steps_per_visit <= _MAX_CANDIDATE_HORIZON
            or type(source_prefetch_workers) is not int
            or source_prefetch_workers not in NATIVE_SOURCE_WORKER_COUNTS
            or reserve_gib < 0):
        _invalid("BAMF_OPERATOR_SESSION_BOUNDS_INVALID")
    run_dir = Path(run_dir).resolve()
    deadline = time.monotonic() + minutes * 60
    visits = accepted = rejected = 0
    status = "TIME_LIMIT"
    metrics = SourcePrefetchMetrics()
    if source_prefetch_workers:
        from bilqis_mlx.runtime.source_prefetch import source_prefetch_pool
        source_pool = source_prefetch_pool(source_prefetch_workers)
    else:
        source_pool = nullcontext(None)
    with source_pool as source_prefetch_executor, bamf_operator_lock(run_dir):
        while time.monotonic() < deadline and (not max_visits or visits < max_visits):
            _emit_progress(progress, f"starting visit {visits + 1}")
            with TrainerObservation(run_dir, visits + 1) as observer:
                outcome = _visit(
                    run_dir, reserve_gib, steps_per_visit=steps_per_visit,
                    progress=progress, source_prefetch_workers=source_prefetch_workers,
                    source_prefetch_executor=source_prefetch_executor,
                    source_prefetch_metrics=metrics, observer=observer)
                observer.finish(outcome)
            _emit_progress(progress, f"visit {visits + 1} outcome: {outcome}")
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
    current = load_accepted_generation(run_dir)
    return BamfOperatorResult(
        status, visits, accepted, rejected, current.generation,
        current.retained_state.optimizer_step,
        source_prefetch_workers=source_prefetch_workers,
        source_prefetch_wait_seconds=metrics.wait_seconds,
        source_prefetch_overlap_seconds=metrics.overlap_seconds,
        source_prefetch_prepared_steps=metrics.prepared_steps,
        source_prefetch_serial_steps=metrics.serial_steps)
