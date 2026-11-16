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
    bind_factory_baseline_successor, evaluate_factory_retention_candidate,
)
from bilqis_mlx.runtime.foundation_teacher_owner import (
    derive_accepted_teacher_successor, select_foundation_priority_visit,
)
from bilqis_mlx.runtime.priority_rejection_replay import (
    candidate_step_horizon, rejection_attempt_ordinals,
)
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
from ._session_execution import candidate_horizon_execution as _candidate_horizon_execution_impl
from ._session_execution import execute_horizon as _execute_horizon_impl
from ._session_execution import operate as _operate_impl
from ._session_execution import retention_result as _retention_result_impl

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
                     rows, horizon, cache, candidate_attempt_ordinal, progress,
                     source_prefetch_workers,
                     source_prefetch_executor, source_prefetch_metrics, observer):
    return _execute_horizon_impl(
        run_dir, selection, context, parent, atlas_path, feature_path,
        rows, horizon, cache, candidate_attempt_ordinal, progress,
        source_prefetch_workers, source_prefetch_executor,
        source_prefetch_metrics, observer,
        source_lane_cls=CandidateSourceLane, source_metrics_cls=SourcePrefetchMetrics,
        prepare_evidence_root=prepare_candidate_evidence_root, capture_cls=_Capture,
        delivery_observation_cls=FactoryDeliveryObservation,
        execute_candidate=execute_accepted_priority_candidate, step_seed=_step_seed,
        emit_progress=_emit_progress, invalid=_invalid,
        observe_completed_step_fn=observe_completed_step)


def _candidate_horizon_execution(
        run_dir, parent, context, atlas_path, feature_path, selection, rows,
        capability, host_cache, steps_per_visit, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer):
    return _candidate_horizon_execution_impl(
        run_dir, parent, context, atlas_path, feature_path, selection, rows,
        capability, host_cache, steps_per_visit, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer,
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
        prepared_visit_type=BamfPreparedVisit, emit_progress=_emit_progress,
        measure_observed_phase_fn=measure_observed_phase)


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
    horizon_state = _candidate_horizon_execution(
        run_dir, parent, context, atlas_path, feature_path, selection, rows,
        capability, host_cache, steps_per_visit, progress, source_prefetch_workers,
        source_prefetch_executor, source_prefetch_metrics, observer)
    (
        cache, steps, capture, rejection_journal_ordinal,
        rejection_attempt_ordinal, identity_before,
    ) = horizon_state
    return _retention_result(
        run_dir, parent, context, atlas_path, selection, capability, cache, steps,
        capture, rejection_journal_ordinal, rejection_attempt_ordinal,
        identity_before, progress, observer)

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
        record_bamf_rejection(run_dir, parent, {
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
            "capability": capability,
            "decision": decision.to_record(),
            "resource": prepared.resource,
            "candidate_evidence": prepared.candidate_evidence,
        })
        return "REJECTED"
    successor = prepared.successor
    if observer is not None:
        observer.update(phase="PUBLISHING")
    _emit_progress(progress, "publishing accepted successor checkpoint")
    with measure_observed_phase(observer, "publishing_wall_seconds"):
        accept_and_publish(
            run_dir, successor, retained, decision=decision,
            feature_sha256=successor.extents.factor_map_digest,
            reserve_gib=reserve_gib,
            training_authorities=step.transaction.training_authorities,
            publication_observer=(
                (lambda metrics: observer.update(**{
                    "publication_" + key: value
                    for key, value in metrics.to_record().items()}))
                if observer is not None else None))
    return "ACCEPTED"

def operate_bamf(
    run_dir: Path, *, minutes: int = 90,
    max_visits: int = 0, steps_per_visit: int = 16,
    reserve_gib: float = 100.0,
    source_prefetch_workers: int = 2,
    progress=None,
) -> BamfOperatorResult:
    """Run the human-authorized BAMF lineage until a bounded stop condition."""
    from bilqis_mlx.runtime.source_prefetch import source_prefetch_pool
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
        load_generation=load_accepted_generation, result_type=BamfOperatorResult)
