"""Source-qualified #709/B13.2 continuation witness over accepted generation one."""
from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys

from bilqis_mlx import state_dag
from bilqis_mlx.learning.atlas_candidate import CandidateCustodyIdentity
from bilqis_mlx.learning.atlas_readout import DecisionOutput
from bilqis_mlx.runtime.atlas_model import (
    bamf_value_and_grad, bind_compiled_training_batch,
)
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.bamf_bundle.admission import (
    admit_candidate_step, admit_uninterrupted_candidate_step,
    bind_accepted_execution_cache, load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle import authenticate_bamf_execution_feature_context
from bilqis_mlx.runtime.bamf_bundle.records import CompleteStudent, sidecar_records
from bilqis_mlx.runtime.factory_complete_solver import factory_evaluation_instrument
from bilqis_mlx.runtime.factory_evaluation_compiler import compile_factory_evaluation_batch
from bilqis_mlx.runtime.factory_task_authority import factory_task_authority
from bilqis_mlx.runtime.task_goal_readout import task_goal_route_decisions, task_goal_route_plan

from .factory_retention_next_step_evidence import (
    FP32_ATOL, _assert_parent_unchanged, _assert_structural_parity,
    _compare_numeric_reference, _custody_hashes, _numeric_arrays,
    _parent_identity, _structural_evidence, _write_numeric_reference,
)
from .factory_retention_next_step_state import (
    _controlled_visit_payload, _persist_unforced_visit,
    _require_sealed_execution, _require_sealed_visit, _seal_execution,
    _verified_visit, natural_next_selection as _natural_next_selection,
)
from ..factory_retention_live_support import HP
from ..source_training_support import source_training_batch


def _in_memory_student(source, pointer):
    records = sidecar_records(source)
    retained = replace(
        source.retained_state,
        custody=CandidateCustodyIdentity(
            source.run_id, source.generation, pointer["manifest_sha256"],
            source.topology.digest, source.extents.digest))
    return CompleteStudent(
        source.run_id, source.generation, source.parent_manifest_sha256,
        source.implementation_sha256, source.topology, source.extents,
        retained, source.optimizer_hyperparameters, source.provenance,
        source.semantic_abi, source.compiler_features, source.correction_frontier,
        source.teacher_state, source.evaluation_contract, source.transition,
        tuple(records["outbox"]))


def _prepare_execution(run_dir, source_context, parent, artifact, visit):
    context, _receipt, capability, seed, row, _key, policy, _metadata = visit
    cache = bind_accepted_execution_cache(run_dir)
    generation = execution_generation_digest(
        parent.retained_state.optimizer.parameters,
        spec=parent.topology, extents=parent.extents)
    training = source_training_batch(
        context, parent, artifact, row, generation, capability=capability,
        source_seed=seed, optimizer_step_seed=parent.retained_state.optimizer_step,
        teacher_strategy=policy)
    compiled = compile_factory_evaluation_batch(
        context, parent, str(artifact), row, source_seed=seed, source_each=1)
    live_batch = bind_compiled_training_batch(
        training, compiled.compiled, compiled.sources, compiled.feature_schema,
        active_semantic_rows=compiled.active_semantic_rows)
    authority = factory_task_authority(context, live_batch)
    feature_context = authenticate_bamf_execution_feature_context(
        parent, str(artifact), run_dir)
    plan = task_goal_route_plan(
        authority.goal, live_batch, feature_context.snapshot, generation)
    targets, mask = _targets(context, parent, artifact, row, seed, authority)
    return training, live_batch, plan, targets, mask, cache, policy


def _targets(context, parent, artifact, row, seed, authority):
    expected = factory_evaluation_instrument(
        context, parent, str(artifact), row,
        source_seed=seed, source_each=1).case.gold
    route = task_goal_route_decisions(authority.goal)
    if len(route) != 1:
        raise AssertionError("B13.2 expected exactly one route decision")
    node = authority.goal.expression_or_holes.nodes[0]
    handle = next(
        item.typed.source_handle for item in authority.binding.operands
        if item.typed.type_name == expected.type_name
        and item.typed.value == expected.value)
    selected = next(
        item for item in node.candidate_operand_refs[0]
        if item.source_handle == handle)
    return (DecisionOutput(route[0].decision_id, selected.identity),), {
        route[0].decision_id: True}


def _candidate_step(run_dir, parent, gradient, policy, *, cold):
    kwargs = {
        "loss_bearing_target": True, "gradient_execution": gradient,
        "teacher_hparams": replace(HP, learning_rate=float(policy["lr"])),
        "max_norm": 1.0,
    }
    if cold:
        return admit_candidate_step(run_dir, **kwargs)
    return admit_uninterrupted_candidate_step(run_dir, parent, **kwargs)




def _execute_prepared(run_dir, parent, visit, prepared, *, cold):
    training, compiled_batch, plan, targets, mask, cache, policy = prepared
    gradient = bamf_value_and_grad(
        dict(parent.retained_state.optimizer.parameters),
        compiled_batch, plan, targets, mask, cache)
    transaction = _candidate_step(run_dir, parent, gradient, policy, cold=cold)
    if transaction.update_steps != 1 or len(transaction.step_proofs) != 1:
        raise AssertionError("B13.2 next step did not execute exactly once")
    evidence = _structural_evidence(
        parent, cache, visit, training, compiled_batch,
        plan, targets, mask, gradient, transaction)
    return evidence, _numeric_arrays(parent, gradient, transaction)


def _run_step(run_dir, source_context, artifact, *, parent, cold):
    visit = _verified_visit(run_dir, source_context)
    prepared = _prepare_execution(run_dir, source_context, parent, artifact, visit)
    _require_sealed_execution(visit[1], prepared[2], prepared[3], prepared[4])
    return _execute_prepared(run_dir, parent, visit, prepared, cold=cold)


def run_cold_destination(run_dir, source_context, artifact, reference_path):
    parent = load_accepted_generation(run_dir)
    evidence, arrays = _run_step(
        Path(run_dir), source_context, Path(artifact), parent=parent, cold=True)
    evidence["numeric_max_abs"] = _compare_numeric_reference(
        Path(reference_path), arrays)
    return evidence


def _spawn_cpu(run_dir, root, source, artifact, reference):
    process = subprocess.run(
        [sys.executable, "-m",
         "bilqis_mlx.runtime.tests.capability.factory.retention.next_step.factory_retention_next_step_probe",
         str(run_dir), str(root), str(source), str(artifact), str(reference)],
        cwd=str(root), capture_output=True, text=True, env=dict(os.environ), timeout=900)
    if process.returncode:
        raise AssertionError(process.stderr)
    return json.loads(process.stdout.strip().splitlines()[-1])


def _spawn_cpu_natural(run_dir, root, source):
    process = subprocess.run(
        [sys.executable, "-m",
         "bilqis_mlx.runtime.tests.capability.factory.retention.next_step.factory_retention_next_step_probe",
         "natural", str(run_dir), str(root), str(source)],
        cwd=str(root), capture_output=True, text=True, env=dict(os.environ), timeout=300)
    if process.returncode:
        raise AssertionError(process.stderr)
    return json.loads(process.stdout.strip().splitlines()[-1])


def prove_source_qualified_continuation(
        run_dir, source_context, artifact, successor, published, *, root, source, target):
    if published.get("generation") != 1:
        raise AssertionError("B13.2 witness requires published accepted generation one")
    held = _in_memory_student(successor, published)
    natural_run = Path(run_dir) / ".b13-2-natural-factory-state"
    state_dag.persist(natural_run, {
        "generation": 0,
        "factory_release_sha256": source_context.release.release_sha256,
        "last_exam": None,
    })
    _persist_unforced_visit(natural_run, source_context, published, held)
    natural = _natural_next_selection(natural_run, source_context)
    if natural["capability"] != "A.IDENTITY":
        raise AssertionError("B13.2 natural Factory next capability drift")
    cold_natural = _spawn_cpu_natural(natural_run, root, source)
    if natural != cold_natural:
        raise AssertionError("B13.2 natural Factory next-selection cold readback drift")
    payload, selected = _controlled_visit_payload(
        run_dir, source_context, published, held, target)
    prepared = _prepare_execution(
        run_dir, source_context, held, artifact, selected)
    _seal_execution(payload, prepared[2], prepared[3], prepared[4])
    state_dag.persist(run_dir, payload)
    sealed_visit = _verified_visit(run_dir, source_context)
    _require_sealed_visit(sealed_visit)
    _require_sealed_execution(
        sealed_visit[1], prepared[2], prepared[3], prepared[4])
    snapshot = (
        (Path(run_dir) / "bamf-state.json").read_bytes(),
        tuple(sorted(path.name for path in (Path(run_dir) / "bamf-bundles").iterdir())),
        _custody_hashes(run_dir, published), _parent_identity(held))
    source_evidence, arrays = _execute_prepared(
        run_dir, held, sealed_visit, prepared, cold=False)
    reference = Path(run_dir) / ".b13-2-source-reference.safetensors"
    source_evidence["reference"] = _write_numeric_reference(reference, arrays)
    destination = _spawn_cpu(run_dir, root, source, artifact, reference)
    committed_output_match = _assert_structural_parity(
        source_evidence, destination)
    if not committed_output_match:
        raise AssertionError("B13.2 committed semantic output drift")
    if destination["numeric_max_abs"]["overall"] > FP32_ATOL:
        raise AssertionError("B13.2 cross-backend FP32 parity exceeded tolerance")
    _assert_parent_unchanged(run_dir, published, held, snapshot)
    return {
        "schema": "bilqis.mlx.b13.2-backend-handoff-witness/v1",
        "source_backend": source_evidence["backend"],
        "destination_backend": destination["backend"],
        "numeric_max_abs": destination["numeric_max_abs"], "tolerance": FP32_ATOL,
        "committed_output_match": committed_output_match,
        "generation": 1, "manifest_sha256": published["manifest_sha256"],
        "natural_next_selection": natural,
        "controlled_optimizer_fixture": True,
        "scheduler_selected": source_evidence["visit"]["scheduler_selected"],
        "no_generation_2": True, "parent_unchanged": True,
    }


__all__ = (
    "FP32_ATOL", "prove_source_qualified_continuation", "run_cold_destination",
)
