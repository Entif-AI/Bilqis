"""Restart-safe production assembly for the accepted C07 admission flywheel."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import subprocess
import sys

from ..factory import candidate_realizations
from ..factory.atlas_frontier import (
    AtlasCoverageEpoch,
    AtlasLearnerEvidence,
    PlannerBudget,
)
from ..factory.atlas_frontier_closure import resolve_frontier_closure
from ..factory.atlas_runtime_snapshot import build_accepted_executable_snapshot
from ..factory.candidate_frontier import load_candidate_frontier
from ..factory.live_answers import live_answer_registry
from ..compatibility.source_adapter_resume import predecessor_compatible_source_registry
from ..factory.skos_curriculum import (
    LearnedFrontier,
    SOURCE_FAMILY_ADAPTERS,
    compile_semantic_curriculum,
    issue_source_context_transition_authority,
)
from ..errors import ErrorBus, SCHOOL
from ..learning.atlas_acceptance import candidate_identity_digest
from ..learning.champions import Checkpoint
from ..paths import LEGACY_SOURCE
from ..semantics.atlas.snapshot import (
    AtlasArtifactIdentity,
    resolve_atlas_artifact_selection,
)
from ..source_adapters.school import live_source_registry
from .accepted_corrections import AcceptedRuntimeHost
from .atlas_admission import (
    _accepted_run_lease_identity,
    _accepted_source_registry,
    read_accepted_atlas_factory_release,
    read_accepted_atlas_lease_v2,
    read_accepted_atlas_obligation_credit,
)
from .atlas_admission_policy import AtlasAdmissionContext
from .atlas_admission_policy_v2 import (
    AtlasAdmissionContextV2,
    AtlasDeltaEnvelopeV2,
)
from .atlas_adoption_v2 import (
    adopt_capability_only_atlas_successor_v2,
    adopt_parameter_extension_atlas_successor_v2,
)
from .atlas_flywheel import AdmissionFlywheelState, run_admission_flywheel
from .atlas_flywheel_runtime_context import AcceptedAtlasAdmissionRuntime
from .autonomy_live import build_live_autonomy_plan, reconcile_live_autonomy_state
from .bamf_bundle import (
    load_bamf_generation_authority,
    read_accepted_generation_feature_receipt,
    stage_vocabulary_extension_from_source_id,
)
from .candidate_staging import load_staged_candidates, persist_staged_candidate


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _candidate_frontier(run_dir: Path):
    root = _repo_root()
    builder = root / "lib/ithkuil/src/build_curriculum_frontier.py"
    output = Path(run_dir) / "candidate-frontier"
    subprocess.run(
        [sys.executable, str(builder)], check=True, capture_output=True, text=True,
        env={**os.environ, "BILQIS_CURRICULUM_FRONTIER_OUT": str(output)},
    )
    return load_candidate_frontier(
        output,
        root / "lib/ithkuil/_data/csv",
        expected_builder_sha256=hashlib.sha256(builder.read_bytes()).hexdigest(),
    )


def _accepted_selection(run_dir: Path):
    receipt = read_accepted_generation_feature_receipt(
        run_dir / "bamf-state.json")
    identity = AtlasArtifactIdentity(
        receipt.source_atlas_bundle_id,
        receipt.source_release_sha256,
        receipt.source_source_bundle_id,
    )
    return resolve_atlas_artifact_selection(identity), receipt


def _accepted_checkpoint(run_dir: Path) -> Checkpoint:
    student, manifest_sha256 = load_bamf_generation_authority(
        run_dir / "bamf-state.json")
    return Checkpoint(
        candidate_identity_digest(student.retained_state),
        f"bamf-bundles/{manifest_sha256}",
        student.retained_state.optimizer_step,
        True,
    )


def _replay_current_graph(current, parent_graph: dict) -> dict:
    from bilqis_mlx.source_adapters import event_frames
    from bilqis_mlx.source_adapters import copular_curriculum

    events = tuple(
        item.capability_id for item in current.execution_plan.capabilities
        if item.capability_id in event_frames.SOURCE_SPECS)
    if events:
        graph = event_frames.projected_graph(parent_graph, events)
    elif copular_curriculum.PROJECTION_ADMISSION_TOKEN in current.semantic_catalog:
        graph = copular_curriculum.expanded_graph(parent_graph)
    else:
        graph = parent_graph
    current.verify_semantic_catalog(graph)
    return graph


def _persist_ready_realizations(
        run_dir: Path, current, candidate, frontier, graph: dict) -> tuple:
    sources, answers = live_source_registry(), live_answer_registry()
    staging_sources = predecessor_compatible_source_registry(current, sources)
    staged = load_staged_candidates(
        run_dir, frontier, current,
        source_registry=sources, answer_registry=answers)
    known = {item.candidate_id for item in staged}
    for semantic_id in candidate.source_eligible_concept_ids:
        try:
            candidate_realizations.realized_capability_id(semantic_id)
        except ValueError:
            continue
        try:
            candidate_realizations.project_realized_target(semantic_id, current)
        except ValueError:
            continue
        realized = candidate_realizations.prepare_realized_candidate(
            frontier, current, graph, semantic_id,
            source_root=LEGACY_SOURCE,
            source_registry=staging_sources,
            answer_registry=answers,
        )
        if realized.candidate_id not in known:
            persist_staged_candidate(run_dir, realized, frontier, current)
            known.add(realized.candidate_id)
    return load_staged_candidates(
        run_dir, frontier, current,
        source_registry=sources, answer_registry=answers)


@dataclass(frozen=True)
class AcceptedAtlasFlywheelSupervisor:
    run_dir: Path
    parent_graph: dict
    reserve_gib: float = 100.0

    def __post_init__(self) -> None:
        if (not isinstance(self.run_dir, Path)
                or not isinstance(self.parent_graph, dict)
                or not isinstance(self.reserve_gib, (int, float))
                or self.reserve_gib < 0):
            ErrorBus.raise_legacy(
                SCHOOL.BAMF_ATLAS_ADMISSION.FLYWHEEL_RUNTIME_INVALID)

    def _authority(self):
        host = AcceptedRuntimeHost(self.run_dir)
        source_authority = host.source_authority()
        lease = read_accepted_atlas_lease_v2(
            self.run_dir, source_authority=source_authority)
        if lease is None:
            ErrorBus.raise_legacy(
                SCHOOL.BAMF_ATLAS_ADMISSION.ACCEPTED_LEASE_REQUIRED)
        registry = _accepted_source_registry(self.run_dir, source_authority)
        return source_authority, lease, registry

    def load_state(self) -> AdmissionFlywheelState:
        current = read_accepted_atlas_factory_release(self.run_dir)
        selection, feature_receipt = _accepted_selection(self.run_dir)
        candidate = compile_semantic_curriculum(
            selection, SOURCE_FAMILY_ADAPTERS,
            LearnedFrontier(selection.release_sha256))
        source = issue_source_context_transition_authority(selection)
        frontier = _candidate_frontier(self.run_dir)
        graph = _replay_current_graph(current, self.parent_graph)
        staged = _persist_ready_realizations(
            self.run_dir, current, candidate, frontier, graph)
        plan = build_live_autonomy_plan(current, LEGACY_SOURCE)
        ledger = reconcile_live_autonomy_state(
            self.run_dir, current, plan)
        checkpoint = _accepted_checkpoint(self.run_dir)
        _source_authority, lease, _registry = self._authority()
        delta = lease.source_approval.delta_budget_policy
        credit = read_accepted_atlas_obligation_credit(self.run_dir)
        snapshot = build_accepted_executable_snapshot(
            candidate, source.frontier, source.policy, frontier, current, staged,
            budget=PlannerBudget(
                delta.max_capabilities, delta.max_new_semantic_identities, 1000),
            admission_receipt_sha256=feature_receipt.acceptance_sha256,
            grade_labels=tuple(
                grade.grade_id for grade in current.execution_plan.grades),
        )
        closure = resolve_frontier_closure(
            snapshot, candidate.census,
            current_release=current,
            evidence_ledger=ledger,
            autonomy_plan=plan,
            checkpoint_sha256=checkpoint.sha256,
            optimizer_step=checkpoint.optimizer_step,
        )
        return AdmissionFlywheelState(
            AtlasCoverageEpoch(
                snapshot, closure, frontier, current, staged,
                accepted_credit=credit),
            AtlasLearnerEvidence(
                ledger, checkpoint.sha256, checkpoint.optimizer_step),
            plan,
        )

    def admit(self, handoff):
        current = read_accepted_atlas_factory_release(self.run_dir)
        if current.release_sha256 != handoff.receipt.predecessor_release.release_sha256:
            ErrorBus.raise_legacy(
                SCHOOL.BAMF_ATLAS_ADMISSION.FLYWHEEL_PREDECESSOR_DRIFT)
        graph = _replay_current_graph(current, self.parent_graph)
        checkpoint = _accepted_checkpoint(self.run_dir)
        plan = build_live_autonomy_plan(current, LEGACY_SOURCE)
        ledger = reconcile_live_autonomy_state(self.run_dir, current, plan)
        frontier = _candidate_frontier(self.run_dir)
        source_authority, lease, registry = self._authority()
        runtime = AcceptedAtlasAdmissionRuntime(
            self.run_dir, checkpoint, graph, self.reserve_gib)
        sources, answers = live_source_registry(), live_answer_registry()
        introduced = tuple(handoff.receipt.selection.introduced_semantic_ids)
        native = None
        if introduced:
            selection, _feature_receipt = _accepted_selection(self.run_dir)
            native_semantic_ids = tuple(
                candidate_realizations.realized_atlas_semantic_id(capability_id)
                for capability_id in
                handoff.receipt.selection.introduced_capability_ids
            )
            native = stage_vocabulary_extension_from_source_id(
                self.run_dir, selection.path, selection.source_bundle_id,
                native_semantic_ids)
        legacy = AtlasAdmissionContext(
            _accepted_run_lease_identity(self.run_dir), current, frontier,
            ledger, plan, checkpoint, lease.source_approval, registry,
            sources, answers,
            runtime if introduced else None,
            native if introduced else None,
            source_authority if introduced else None,
        )
        context = AtlasAdmissionContextV2(
            legacy, self.run_dir,
            None if introduced else runtime,
            None if introduced else source_authority,
        )
        delta = AtlasDeltaEnvelopeV2(handoff, native)
        return (
            adopt_parameter_extension_atlas_successor_v2(context, delta, lease)
            if introduced else
            adopt_capability_only_atlas_successor_v2(context, delta, lease)
        )


def run_accepted_atlas_flywheel(
        run_dir: Path, parent_graph: dict, *, reserve_gib: float = 100.0,
        max_advances: int = 16):
    """Advance only through accepted cold custody; never own neural updates."""
    supervisor = AcceptedAtlasFlywheelSupervisor(
        Path(run_dir), parent_graph, reserve_gib)
    return run_admission_flywheel(
        supervisor.load_state, supervisor.admit, max_advances=max_advances)
