"""Pure and durable planning helpers for the human-run autonomy bridge."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from ...curriculum_compiler import compile_ast
from ...curriculum.scheduler import (
    SchoolState,
    assessment_capabilities,
    next_capability,
    verify_state,
    visit,
)
from ...factory.autonomy import (
    AutonomyPlan,
    CurriculumWorkItem,
    EvidenceLedger,
    compile_autonomy_plan,
    evidence_complete_capabilities,
    initial_evidence_ledger,
    rebind_evidence_ledger,
    reconcile_successor_evidence,
)
from ...factory.evidence import measure_evidence
from ...factory.model import FactoryRelease
from ...registry_ast import load_registry
from ...semantic_coverage import (
    audit_pinned_micro_generator,
    discover_composition_obligations,
)
from ...source_adapters.school import live_source_registry
from ..autonomy_state import persist_autonomy_state, read_autonomy_state


REGISTRY_SNAPSHOT = (
    Path(__file__).resolve().parents[3]
    / "docs/provenance/CURRICULUM_REGISTRY_SNAPSHOT_20261015.json"
)


def reconcile_successor_evidence_or_reset(
        previous_release, release, ledger, *, previous_plan, current_plan):
    """Carry only evidence whose projection identity is actually available."""
    previous_projection = {
        item.capability_id
        for item in previous_release.execution_plan.capability_projection_digests}
    current_projection = {
        item.capability_id
        for item in release.execution_plan.capability_projection_digests}
    shared = (
        set(previous_release.curriculum.capability_map)
        & set(release.curriculum.capability_map))
    if not shared <= (previous_projection & current_projection):
        return initial_evidence_ledger(release, plan=current_plan)
    return reconcile_successor_evidence(
        previous_release, release, ledger,
        previous_plan=previous_plan, current_plan=current_plan)


def build_live_autonomy_plan(
    release: FactoryRelease, source_root: Path,
) -> AutonomyPlan:
    """Compile the strongest currently source-proven autonomy plan."""
    release.verify()
    if not isinstance(release, FactoryRelease):
        source_registry = live_source_registry()
        return compile_autonomy_plan(
            release, supplemental_evidence=source_registry.evidence_dependencies(
                None, release=release))
    registry = load_registry(REGISTRY_SNAPSHOT)
    source_registry = live_source_registry()
    discovered = discover_composition_obligations(
        compile_ast(release.course), registry)
    if any(
            edge["status"] == "AWAITING_SOURCE_WITNESS"
            for edge in discovered["obligations"]):
        discovered = audit_pinned_micro_generator(
            discovered, Path(source_root), max_rounds=8, each=24)
    return compile_autonomy_plan(
        release, discovered,
        supplemental_evidence=source_registry.evidence_dependencies(
            release.course),
    )


def reconcile_live_autonomy_state(
    run_dir: Path, release: FactoryRelease, plan: AutonomyPlan,
) -> EvidenceLedger:
    """Restore same-release autonomy state or initialize a new release epoch."""
    root = Path(run_dir)
    pointer = root / "autonomy/current.json"
    if not pointer.exists():
        ledger = initial_evidence_ledger(release, plan=plan)
        persist_autonomy_state(root, release, plan=plan, ledger=ledger)
        return ledger
    if pointer.is_symlink() or not pointer.is_file():
        raise ValueError("AUTONOMY_STATE_POINTER_UNSAFE")
    raw = json.loads(pointer.read_text())
    if raw.get("factory_release_sha256") != release.release_sha256:
        from ...factory.executable_release import ExecutableFactoryRelease
        if isinstance(release, ExecutableFactoryRelease):
            previous_sha256 = raw.get("factory_release_sha256")
            previous_file = root / "factory-releases" / (
                str(previous_sha256) + ".json")
            if previous_file.is_file() and not previous_file.is_symlink():
                previous_payload = json.loads(
                    previous_file.read_text(encoding="utf-8"))
                if previous_payload.get("schema") == release.schema:
                    from ..admission import _read_executable_factory_release_artifact
                    previous_release = _read_executable_factory_release_artifact(
                        root, {
                            "factory_release_sha256": previous_sha256,
                            "factory_release_file": (
                                "factory-releases/" + previous_sha256 + ".json"),
                        })
                    old_plan, old_ledger = read_autonomy_state(
                        root, previous_release)
                    ledger = reconcile_successor_evidence_or_reset(
                        previous_release, release, old_ledger,
                        previous_plan=old_plan, current_plan=plan)
                    persist_autonomy_state(
                        root, release, plan=plan, ledger=ledger)
                    return ledger
        ledger = initial_evidence_ledger(release, plan=plan)
        persist_autonomy_state(root, release, plan=plan, ledger=ledger)
        return ledger
    old_plan, ledger = read_autonomy_state(root, release)
    if old_plan.digest() != plan.digest():
        ledger = rebind_evidence_ledger(
            release, ledger, old_plan=old_plan, new_plan=plan)
        persist_autonomy_state(root, release, plan=plan, ledger=ledger)
    return ledger


def measure_live_evidence(
    source_root, graph, release: FactoryRelease, work: CurriculumWorkItem, *,
    checkpoint: dict, seed: int, predictor=None, source_bound_predictor=None,
):
    """Measure one obligation against the exact durable checkpoint supplied."""
    return measure_evidence(
        source_root, graph, release, live_source_registry(), work.obligation,
        checkpoint=checkpoint, seed=seed, predictor=predictor,
        source_bound_predictor=source_bound_predictor)


def scheduled_teaching_matches(
    school: SchoolState, capability_id: str,
) -> bool:
    """Never target optimizer work outside the scheduler's legal queue head."""
    return next_capability(school) == capability_id


def reroute_failed_teaching(
    release: FactoryRelease, school: SchoolState, capability_id: str,
) -> SchoolState:
    """Neural-inertly put a still-legal failed proof back at queue head."""
    from ...factory.schedule import schedule_program_from_executable_release
    program = (release.course if isinstance(release, FactoryRelease) else
               schedule_program_from_executable_release(release))
    verify_state(program, school)
    if capability_id not in assessment_capabilities(program, school):
        raise ValueError("AUTONOMY_TEACHING_REROUTE_OUTSIDE_SCHEDULER_SCOPE")
    queue = (capability_id, *(
        item for item in school.queue if item != capability_id))
    rerouted = replace(school, queue=queue)
    verify_state(program, rerouted)
    return rerouted


def advance_if_scheduled_evidence_complete(
    release: FactoryRelease, plan: AutonomyPlan, ledger: EvidenceLedger,
    school: SchoolState, capability_id: str,
) -> SchoolState:
    """Treat complete evidence as a zero-update scheduled visit when aligned."""
    if not scheduled_teaching_matches(school, capability_id):
        return school
    if capability_id not in set(
            evidence_complete_capabilities(
                release, ledger, plan=plan,
                current_checkpoint_sha256=school.current_student.sha256,
                current_optimizer_step=school.current_student.optimizer_step)):
        return school
    from ...factory.schedule import schedule_program_from_executable_release
    program = (release.course if isinstance(release, FactoryRelease) else
               schedule_program_from_executable_release(release))
    return visit(program, school, capability_id, school.current_student)
