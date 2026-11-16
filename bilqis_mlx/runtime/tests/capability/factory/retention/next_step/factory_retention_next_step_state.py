"""Factory state receipts and visit selection for the B13.2 continuation witness."""
from __future__ import annotations

from dataclasses import asdict, replace
import json
import random

from bilqis_mlx import state_dag
from bilqis_mlx.compatibility import historical_teacher_policy as teacher_engine
from bilqis_mlx.curriculum.scheduler import (
    _enter_grade, assessment_capabilities, next_capability, start_new,
)
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.learning.teacher_strategy_population import BAMF_SUCCESSOR_SELECTION
from bilqis_mlx.learning.tests.test_teacher_vnext_replay import _teacher
from bilqis_mlx.runtime import admission as factory_admission, state as runtime_state
from bilqis_mlx.runtime.teacher_policy_selection import select_visit_policy
from bilqis_mlx.semantics.foundation.domains import contract_digest

from .factory_retention_next_step_evidence import _json_digest


FIXTURE_SCHEMA = "bilqis.mlx.b13.2-controlled-visit/v1"


def _teacher_fixture():
    teacher, _, _ = _teacher()
    teacher["selection_contract"] = BAMF_SUCCESSOR_SELECTION
    teacher["events"] = 100
    teacher["global_stats"] = {
        key: {"trials": 10, "reward_sum": index, "reward_ema": index}
        for index, key in enumerate(teacher["strategies"])
    }
    teacher["grade_stats"] = {}
    return teacher


def _controlled_school(program, school, target):
    grade_index = school.active_grades.index(target.split(".", 1)[0])
    controlled = _enter_grade(
        program, school, grade_index, stage="MAIN", first_recovery=())
    return replace(controlled, queue=(target,))


def _factory_state_payload(run_dir, source_context, published, student, school):
    previous = state_dag.read_current(run_dir)
    release_file = factory_admission._persist_executable_factory_release(
        run_dir, source_context.release)
    return {
        "run_id": student.run_id, "generation": student.generation,
        "school": asdict(school), "teacher": _teacher_fixture(),
        "factory_release_sha256": source_context.release.release_sha256,
        "factory_release_file": release_file, "curriculum_mode": "bamf-c05-source",
        "numeric_maximum": 7, "last_exam": previous.get("last_exam"),
    }


def _new_school(source_context, published, student):
    program = schedule_program_from_executable_release(source_context.release)
    school = start_new(program, Checkpoint(
        published["manifest_sha256"], published["bundle"],
        student.retained_state.optimizer_step, True))
    return program, school


def _selection_from_payload(receipt, context):
    program = schedule_program_from_executable_release(context.release)
    school = runtime_state._state_from_json(receipt["school"], program)
    capability = next_capability(school)
    seed = runtime_state._seed(receipt, capability=capability)
    teacher = json.loads(json.dumps(receipt["teacher"]))
    policy_key, policy, metadata = select_visit_policy(
        teacher_engine, teacher, capability, school, random.Random(seed), None,
        f"{receipt['curriculum_mode']}/{receipt['numeric_maximum']}", None,
        capability.split(".", 1)[0], len(assessment_capabilities(program, school)))
    return context, receipt, school, capability, seed, policy_key, policy, metadata


def _select_visit_from_payload(receipt, context):
    selected = _selection_from_payload(receipt, context)
    context, receipt, _school, capability, seed, policy_key, policy, metadata = selected
    row = context.draw_rows(seed=seed, capability=capability, each=1)[0]
    return context, receipt, capability, seed, row, policy_key, policy, metadata


def _selection_identity(selected):
    _context, _receipt, capability, seed, row, policy_key, policy, metadata = selected
    return {
        "capability": capability, "seed": seed, "row_id": row["id"],
        "row_sha256": _json_digest(row), "policy_key": policy_key,
        "policy_sha256": _json_digest(policy),
        "selection_reason": metadata["selection_reason"],
    }


def _controlled_visit_payload(run_dir, source_context, published, student, target):
    program, school = _new_school(source_context, published, student)
    controlled = _controlled_school(program, school, target)
    payload = _factory_state_payload(
        run_dir, source_context, published, student, controlled)
    selected = _select_visit_from_payload(payload, source_context)
    if selected[2] != target:
        raise AssertionError("B13.2 controlled capability selection drift")
    payload["continuation_fixture"] = {
        "schema": FIXTURE_SCHEMA,
        "controlled_optimizer_fixture": True, "scheduler_selected": False,
        **_selection_identity(selected),
    }
    return payload, selected


def _persist_unforced_visit(run_dir, source_context, published, student):
    _program, school = _new_school(source_context, published, student)
    return state_dag.persist(
        run_dir, _factory_state_payload(
            run_dir, source_context, published, student, school))


def _persist_controlled_visit(run_dir, source_context, published, student, target):
    payload, _selected = _controlled_visit_payload(
        run_dir, source_context, published, student, target)
    return state_dag.persist(run_dir, payload)


def _selection_from_receipt(run_dir, source_context):
    receipt = state_dag.read_current(run_dir)
    context = source_context.from_admitted_release(
        run_dir, receipt, graph=source_context.graph,
        source_root=source_context.source_root,
        source_registry=source_context.source_registry,
        answer_registry=source_context.answer_registry)
    return _selection_from_payload(receipt, context)


def natural_next_selection(run_dir, source_context):
    selected = _selection_from_receipt(run_dir, source_context)
    context, receipt, _school, capability, seed, policy_key, policy, metadata = selected
    return {
        "factory_release_sha256": context.release.release_sha256,
        "generation": receipt["generation"], "capability": capability, "seed": seed,
        "teacher_policy_key": policy_key, "teacher_policy_sha256": _json_digest(policy),
        "selection_reason": metadata["selection_reason"],
    }


def _select_visit(run_dir, source_context):
    selected = _selection_from_receipt(run_dir, source_context)
    context, receipt, _school, capability, seed, policy_key, policy, metadata = selected
    row = context.draw_rows(seed=seed, capability=capability, each=1)[0]
    return context, receipt, capability, seed, row, policy_key, policy, metadata


def _require_sealed_visit(selected):
    _context, receipt, _capability, _seed, _row, _policy_key, _policy, _metadata = selected
    fixture = receipt["continuation_fixture"]
    expected = {
        "schema": FIXTURE_SCHEMA,
        "controlled_optimizer_fixture": True, "scheduler_selected": False,
        **_selection_identity(selected),
    }
    if any(fixture.get(key) != value for key, value in expected.items()):
        raise AssertionError("B13.2 sealed visit drift")


def _verified_visit(run_dir, source_context):
    selected = _select_visit(run_dir, source_context)
    _require_sealed_visit(selected)
    return selected


def _execution_identity(plan, targets, mask):
    return {
        "plan_sha256": contract_digest((
            plan.modality_id, plan.input_prefix_end, plan.decisions,
            plan.generation_binding, plan.maximum_decisions)),
        "targets_sha256": contract_digest(targets),
        "mask_sha256": contract_digest(mask),
    }


def _seal_execution(receipt, plan, targets, mask):
    fixture = receipt["continuation_fixture"]
    identity = _execution_identity(plan, targets, mask)
    if any(key in fixture for key in identity):
        raise AssertionError("B13.2 execution seal already written")
    fixture.update(identity)
    return receipt


def _require_sealed_execution(receipt, plan, targets, mask):
    fixture = receipt["continuation_fixture"]
    expected = _execution_identity(plan, targets, mask)
    if any(fixture.get(key) != value for key, value in expected.items()):
        raise AssertionError("B13.2 sealed execution drift")


__all__ = ("natural_next_selection",)
