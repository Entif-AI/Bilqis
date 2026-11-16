"""Executable release, profile and JIT adoption transactions."""
from __future__ import annotations

from ..topology_lifecycle import topology_for_checkpoint as _topology_for_checkpoint

from bilqis_mlx.errors import ErrorBus, FACTORY, SCHOOL


import bilqis_mlx.compatibility.executable_projection as _compatibility_executable_projection
import bilqis_mlx.curriculum.scheduler as _curriculum_scheduler
import bilqis_mlx.factory.executable_release as _factory_executable_release
import bilqis_mlx.factory.live_answers as _factory_live_answers
import bilqis_mlx.factory.schedule as _factory_schedule
import bilqis_mlx.learning.championship_identity as _learning_championship_identity
import bilqis_mlx.profiles.catalog as _profiles_catalog
import bilqis_mlx.runtime.admission as _runtime_admission
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints
import bilqis_mlx.runtime.state as _runtime_state
import bilqis_mlx.source_adapters.school as _source_adapters_school
import bilqis_mlx.vocabulary_growth as _bilqis_mlx_vocabulary_growth
import copy as _copy
import dataclasses as _dataclasses
import functools as _functools
import pathlib as _pathlib
import uuid as _uuid

def _require_complete_profile_boundary(program, school, receipt):
    """Require one complete perfect cumulative exam for the admitted prefix."""
    if school.stage != "AWAITING_NEXT_GRADE":
        raise ValueError("FACTORY_PROFILE_EXPANSION_NOT_AT_GRADE_BOUNDARY")
    exam = receipt.get("last_exam") or {}
    expected = {
        capability.id: capability.exam_item_count
        for grade in program.grades for capability in grade.capabilities
    }
    if (exam.get("student_sha256") != school.current_student.sha256 or
            exam.get("optimizer_step") != school.current_student.optimizer_step or
            exam.get("scores") != {
                capability: {"correct": count, "total": count}
                for capability, count in expected.items()}):
        raise ValueError(
            "FACTORY_PROFILE_EXPANSION_REQUIRES_COMPLETE_PERFECT_PREFIX")


def _catalog_boundary_evidence(
        predecessor, previous_program, school, receipt, *, allow_mastery_debt):
    if not allow_mastery_debt:
        _require_complete_profile_boundary(previous_program, school, receipt)
        return receipt.get("last_exam") or {}, ()
    exam = receipt.get("debt_admission_boundary_exam") or {}
    expected = {
        cap.id: cap.exam_item_count
        for grade in previous_program.grades for cap in grade.capabilities
    }
    from bilqis_mlx.factory.assessment import assessment_scope_contract
    contract = assessment_scope_contract(predecessor, tuple(expected))
    if (exam.get("student_sha256") != school.current_student.sha256 or
            exam.get("optimizer_step") != school.current_student.optimizer_step or
            exam.get("factory_release_sha256") != predecessor.release_sha256 or
            exam.get("exam_rubric_sha256") != contract.rubric_sha256 or
            set(exam.get("scores", {})) != set(expected) or
            any(score.get("total") != expected[cap]
                for cap, score in exam.get("scores", {}).items())):
        raise ValueError("DEBT_ADMISSION_REQUIRES_EXACT_COMPLETE_BOUNDARY")
    mastery_debt = tuple(
        cap for cap in expected
        if exam["scores"][cap]["correct"] != expected[cap])
    return exam, mastery_debt


def _catalog_epoch_state(
        receipt, predecessor, successor, school, next_state,
        transition, grown, mastery_debt, *, allow_mastery_debt, appended,
        profile_championship_state):
    graph_receipt = {
        **receipt,
        "semantic_graph_sha256": _runtime_state._fingerprint(transition.graph),
        "parameter_shapes": {name: list(value.shape) for name, value in grown.items()},
    }
    identity, epoch, history = profile_championship_state(
        graph_receipt, predecessor, successor, school, next_state,
        appended=appended,
        mastery_debt=mastery_debt if allow_mastery_debt else None)
    return epoch, history, identity


def _catalog_adoption_receipt(
        receipt, compatibility_course, successor, successor_program,
        release_file, admission, transition, grown, epoch, history,
        identity):
    graph_sha = _runtime_state._fingerprint(transition.graph)
    heads = _factory_executable_release.answer_heads_from_executable_release(successor, transition.graph)
    numeric_values = heads.get("numeric_active", {}).get("values")
    updated = {
        **receipt,
        "curriculum_mode": compatibility_course.version,
        "semantic_graph_sha256": graph_sha,
        "factory_release_sha256": successor.release_sha256,
        "factory_release_file": release_file,
        "factory_release_schema": successor.schema,
        "factory_admission_v2": _dataclasses.asdict(admission),
        "parameter_shapes": {
            name: list(value.shape) for name, value in grown.items()},
        "championship_school_identity": identity,
        "config": {
            **receipt["config"],
            "vocab_size": len(transition.graph["tokens"]),
            "answer_heads": heads,
        },
        "live_rubric_sha256": successor_program.grades[-1].assessment_sha256,
        "numeric_maximum": (
            len(numeric_values) - 1 if numeric_values is not None else
            receipt.get("numeric_maximum")),
        "numeric_scope_final_maximum": transition.numeric_scope_final_maximum,
        "mentor_epoch": epoch,
        "championship_epoch_history": history,
        "last_exam": None,
    }
    updated.pop("qualification_cohort_v2", None)
    return updated


def _catalog_adoption_event(
        record, school, pointer, successor, growth, grade: str) -> dict:
    return {
        "event": "SCHOOL_SEMANTIC_CATALOG_PROFILE_ADOPTED",
        "generation": record["generation"],
        "grade": grade,
        "profile_id": successor.profile.profile_id,
        "semantic_geometry": successor.transition.semantic_geometry,
        "growth": growth,
        "previous_student_sha256": school.current_student.sha256,
        "student_sha256": pointer.sha256,
        "optimizer_step": pointer.optimizer_step,
        "numeric_maximum": record.get("numeric_maximum"),
        "factory_release_sha256": successor.release_sha256,
        "actual_neural_updates": 0,
    }


def _adopt_catalog_profile(
        mx, run_dir, receipt, grade_a_course, source_root, graph,
        parameters, optimizer, transition, *, reserve_gib, allow_mastery_debt=False,
        compiled_successor=None, verify_profile_successor, profile_transition,
        materialize_prepared_successor, profile_championship_state):
    """Adopt one append-only semantic ABI/profile expansion with zero updates."""
    predecessor = _runtime_admission._require_executable_factory_admission(run_dir, receipt, graph)
    previous_program = _factory_schedule.schedule_program_from_executable_release(predecessor)
    school = _runtime_state._state_from_json(receipt["school"], previous_program)
    exam, mastery_debt = _catalog_boundary_evidence(
        predecessor, previous_program, school, receipt,
        allow_mastery_debt=allow_mastery_debt)
    compatibility_course = _compatibility_executable_projection.legacy_course_for_profile(
        grade_a_course, source_root, transition.profile)
    successor = compiled_successor or _factory_executable_release.compile_successor_profile_release(
        predecessor,
        transition.profile,
        _source_adapters_school.live_source_registry(),
        _factory_live_answers.live_answer_registry(),
        source_root=source_root,
        graph=transition.graph,
        verification_seed=2026101907)
    verify_profile_successor(predecessor, successor, transition.graph, transition.profile)
    if (successor.transition is None or
            successor.transition.semantic_geometry != "APPEND_ONLY_EXPANSION"):
        raise ValueError("FACTORY_CATALOG_TRANSITION_NOT_APPEND_ONLY")
    successor_program = _factory_schedule.schedule_program_from_executable_release(successor)
    next_state, _, appended = profile_transition(
        previous_program, successor_program, school,
        mastery_debt=mastery_debt if allow_mastery_debt else None)

    materialized = materialize_prepared_successor(
        mx, run_dir, {**receipt, "last_exam": exam}, school.current_student, successor,
        graph, parameters, optimizer, transition.graph, reserve_gib=reserve_gib)
    grown, own_optimizer, growth = (
        materialized.parameters, materialized.optimizer, materialized.growth)
    pointer = materialized.student
    next_state = _dataclasses.replace(next_state, current_student=pointer)
    successor, release_file, admission = _runtime_admission._executable_factory_admission(
        run_dir, successor, pointer, _runtime_state._fingerprint(transition.graph),
        transition.graph)
    epoch, history, identity = _catalog_epoch_state(
        receipt, predecessor, successor, school, next_state,
        transition, grown, mastery_debt,
        allow_mastery_debt=allow_mastery_debt, appended=appended,
        profile_championship_state=profile_championship_state)
    updated = _catalog_adoption_receipt(
        receipt, compatibility_course, successor, successor_program,
        release_file, admission, transition, grown, epoch, history,
        identity)
    updated["last_exam"] = materialized.rebaselined_exam
    record = _runtime_checkpoints._advance(
        run_dir, updated, next_state, model_bundle=pointer.filename,
        result="ACTIVE_GRADE_" + next_state.grade, persist=False)
    event = _catalog_adoption_event(
        record, school, pointer, successor, growth, next_state.grade)
    record = _runtime_checkpoints._persist(
        run_dir, _runtime_checkpoints._with_delivery_outbox(record, (event,)))
    _runtime_checkpoints._reconcile_delivery_outbox(run_dir, record)
    return grown, own_optimizer, transition.graph, record, compatibility_course
