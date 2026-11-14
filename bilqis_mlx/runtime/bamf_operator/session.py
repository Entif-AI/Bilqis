"""C16.3 persistent BAMF-native human session.

This coordinator composes existing owners.  It is not a curriculum, teacher,
retention, source, optimizer, or publication authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import math
import shutil
import time

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.learning.atlas_candidate import resolve_candidate
from bilqis_mlx.learning.atlas_retention_decision import issue_factory_retention_decision
from bilqis_mlx.paths import LEGACY_SOURCE
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.accepted_priority_visit import (
    accepted_priority_school, execute_accepted_priority_candidate,
)
from bilqis_mlx.runtime.bamf_bundle import (
    authenticate_bamf_execution_feature_context,
    read_accepted_generation_feature_context, record_bamf_rejection,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, load_accepted_generation,
)
from bilqis_mlx.runtime.factory_candidate_training import FactoryDeliveryObservation
from bilqis_mlx.runtime.factory_retention_owner import evaluate_factory_retention_candidate
from bilqis_mlx.runtime.foundation_teacher_owner import (
    derive_accepted_teacher_successor, select_foundation_priority_visit,
)
from bilqis_mlx.semantics.atlas.feature_io import persist_feature_manifest
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactIdentity
import bilqis_mlx.semantics.atlas.snapshot as _atlas_snapshot
from .locking import bamf_operator_lock


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


@dataclass(frozen=True)
class BamfPreparedVisit:
    """One owner-composed candidate with no rejection/publication side effect."""

    status: str
    parent: object
    selection: object | None = None
    step: object | None = None
    decision: object | None = None
    retained: object | None = None
    capability: str | None = None
    successor: object | None = None


def _execution_context(run_dir: Path):
    parent = load_accepted_generation(run_dir)
    host = AcceptedRuntimeHost(run_dir)
    context = host.source_context(source_root=LEGACY_SOURCE.resolve())
    accepted = read_accepted_generation_feature_context(run_dir / "bamf-state.json")
    identity = accepted.receipt
    selection = _atlas_snapshot.resolve_atlas_artifact_selection(AtlasArtifactIdentity(
        identity.source_atlas_bundle_id,
        identity.source_release_sha256,
        identity.source_source_bundle_id,
    ))
    authenticated = authenticate_bamf_execution_feature_context(
        parent, selection.path, run_dir)
    predecessor = accepted.construction_predecessor
    feature = persist_feature_manifest(
        authenticated.features, run_dir / "operator-artifacts" / "features",
        predecessor=predecessor)
    return parent, context, selection.path, feature.path


class _Capture:
    """Minimal durable #545 delivery evidence; owns no teacher or source choice."""

    def __init__(self, run_dir: Path, selection):
        from bilqis_mlx.runtime.teacher_observation_capture import store_sidecar
        self.run_dir = run_dir
        self.selected_option = selection.option_id
        self.attempt_id = sha256(
            f"bamf-c16.3:{selection.visit.identity.visit_id}".encode()).hexdigest()
        self.proposal_id = store_sidecar(run_dir, {
            "schema": "bilqis.bamf.c16.3-priority-proposal/v1",
            "attempt_id": self.attempt_id,
            "visit_id": selection.visit.identity.visit_id,
            "selected_option": selection.option_id,
        })["sha256"]

    def delivery(self, _release, capability, step, rows, **evidence):
        from bilqis_mlx.runtime.teacher_observation_capture import store_sidecar
        store_sidecar(self.run_dir, {
            "schema": "bilqis.bamf.c16.3-priority-delivery/v1",
            "attempt_id": self.attempt_id,
            "proposal_id": self.proposal_id,
            "capability": capability,
            "step": step,
            "row_ids": [row["id"] for row in rows],
            "seed": evidence.get("seed"),
        })


def _step_seed(visit_id: str) -> int:
    return int.from_bytes(sha256(
        f"bilqis.bamf.c16.3-step-seed/v1|{visit_id}".encode()).digest()[:8], "big")


def _resource_observation(run_dir: Path, step) -> dict:
    """Capture only resource facts the accepted visit can truthfully support."""
    cost = getattr(step, "realized_cost", None)
    if not isinstance(cost, dict):
        _invalid("BAMF_C16_3_RESOURCE_OBSERVATION_INVALID")
    budget = cost.get("c08_memory_budget_bytes")
    wall_seconds = cost.get("wall_seconds")
    optimizer_steps = cost.get("optimizer_steps")
    if (type(budget) is not int or budget <= 0
            or type(wall_seconds) not in (int, float) or type(wall_seconds) is bool
            or not math.isfinite(wall_seconds) or wall_seconds <= 0
            or type(optimizer_steps) is not int or optimizer_steps < 1):
        _invalid("BAMF_C16_3_RESOURCE_OBSERVATION_INVALID")
    disk_used = shutil.disk_usage(Path(run_dir)).used
    return {
        "schema": "bilqis.bamf.c16.3-resource-observation/v1",
        "memory_budget_bytes": budget,
        "disk_used_bytes": disk_used,
        "optimizer_steps": optimizer_steps,
        "wall_seconds": float(wall_seconds),
    }


def _emit_progress(progress, message: str) -> None:
    if progress is not None:
        progress(message)


def prepare_bamf_visit(run_dir: Path, *, progress=None) -> BamfPreparedVisit:
    """Compose the production visit through retention without publishing it."""
    _emit_progress(progress, "validating accepted generation and source custody")
    parent, context, atlas_path, feature_path = _execution_context(run_dir)
    program = schedule_program_from_executable_release(context.release)
    school = accepted_priority_school(parent, program)
    _emit_progress(progress, "planning current candidate frontier and teacher priority")
    selection = select_foundation_priority_visit(
        run_dir, context, atlas_path, program=program, school=school)
    if selection.status != "TEACHER_SELECTED":
        status = "ACTION_REQUIRED" if selection.status == "ACTION_REQUIRED" else "HELD"
        return BamfPreparedVisit(status, parent, selection=selection)
    rows = selection.offer.rows()
    observation = FactoryDeliveryObservation(
        _Capture(run_dir, selection), parent.retained_state.optimizer_step + 1,
        rows, selection.offer.source_seed)
    _emit_progress(progress, "executing selected neural candidate")
    step = execute_accepted_priority_candidate(
        selection, context, atlas_path, feature_path,
        teacher_hparams=parent.optimizer_hyperparameters,
        observation=observation,
        optimizer_step_seed=_step_seed(selection.visit.identity.visit_id),
        max_norm=1.0)
    capability = selection.offer.capability_id
    _emit_progress(progress, "evaluating retention evidence")
    evaluation = evaluate_factory_retention_candidate(
        context, step.transaction, atlas_path, capability, run_dir=run_dir)
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
                "resource": _resource_observation(run_dir, step),
            },))
    return BamfPreparedVisit(
        "ACCEPTED" if decision.accepted else "REJECTED",
        parent, selection, step, decision, retained, capability, successor)


def _visit(run_dir: Path, reserve_gib: float, *, progress=None):
    prepared = prepare_bamf_visit(run_dir, progress=progress)
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
    _emit_progress(progress, "publishing accepted successor checkpoint")
    accept_and_publish(
        run_dir, successor, retained, decision=decision,
        feature_sha256=successor.extents.factor_map_digest,
        reserve_gib=reserve_gib,
        training_authorities=step.transaction.training_authorities)
    return "ACCEPTED"


def operate_bamf(
    run_dir: Path, *, minutes: int = 90,
    max_visits: int = 0, reserve_gib: float = 100.0,
    progress=None,
) -> BamfOperatorResult:
    """Run the human-authorized BAMF lineage until a bounded stop condition."""
    if (type(minutes) is not int or minutes < 1 or type(max_visits) is not int
            or max_visits < 0 or reserve_gib < 0):
        _invalid("BAMF_OPERATOR_SESSION_BOUNDS_INVALID")
    run_dir = Path(run_dir).resolve()
    deadline = time.monotonic() + minutes * 60
    visits = accepted = rejected = 0
    status = "TIME_LIMIT"
    with bamf_operator_lock(run_dir):
        while time.monotonic() < deadline and (not max_visits or visits < max_visits):
            _emit_progress(progress, f"starting visit {visits + 1}")
            outcome = _visit(run_dir, reserve_gib, progress=progress)
            _emit_progress(progress, f"visit {visits + 1} outcome: {outcome}")
            if outcome in {"HELD", "ACTION_REQUIRED"}:
                status = "PRIORITY_HOLD" if outcome == "HELD" else "ACTION_REQUIRED"
                break
            visits += 1
            if outcome == "REJECTED":
                rejected += 1
                status = "REJECTED_HOLD"
                break
            accepted += 1
        else:
            status = "VISIT_LIMIT" if max_visits and visits >= max_visits else "TIME_LIMIT"
    current = load_accepted_generation(run_dir)
    return BamfOperatorResult(
        status, visits, accepted, rejected, current.generation,
        current.retained_state.optimizer_step)
