"""Executable release, profile and JIT adoption transactions."""
from __future__ import annotations

from ..topology_lifecycle import topology_for_checkpoint as _topology_for_checkpoint

from bilqis_mlx.errors import ErrorBus, FACTORY, SCHOOL


import bilqis_mlx.compatibility.executable_projection as _compatibility_executable_projection
import bilqis_mlx.curriculum.scheduler as _curriculum_scheduler
import bilqis_mlx.factory.executable_release as _factory_executable_release
import bilqis_mlx.factory.live_answers as _factory_live_answers
import bilqis_mlx.factory.provider_dimensions as _factory_provider_dimensions
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

from .core import _UNSPECIFIED_DEBT_CADENCE_POLICY

def _profile_championship_state(
        receipt, predecessor, successor, school, next_state, *, appended,
        mastery_debt=None):
    exam = (receipt.get("debt_admission_boundary_exam") if mastery_debt is not None
            else receipt.get("last_exam")) or {}
    history = list(receipt.get("championship_epoch_history", ()))
    identity = _learning_championship_identity.build_school_identity(
        course_sha256=successor.execution_plan.curriculum_sha256,
        semantic_graph_sha256=receipt["semantic_graph_sha256"],
        parameter_shapes=receipt["parameter_shapes"],
        factory_release_sha256=successor.release_sha256)
    if appended:
        from bilqis_mlx.learning.mentor_epoch import begin_epoch, begin_debt_epoch
        boundary = {
            "checkpoint_sha256": exam.get("student_sha256"),
            "rubric_sha256": exam.get("exam_rubric_sha256"),
            "cohort_sha256": exam.get("cohort_sha256"),
            "scores": exam.get("scores"),
        }
        arguments = dict(
            admitted_baseline=_dataclasses.asdict(next_state.current_student),
            introduced_grade=next_state.grade,
            source_graph_sha256=receipt["semantic_graph_sha256"],
            previous_capabilities=tuple(
                item.capability_id for item in predecessor.execution_plan.capabilities))
        if mastery_debt is not None:
            epoch = begin_debt_epoch(**arguments,
                previous_checkpoint=_dataclasses.asdict(school.current_student),
                previous_boundary_exam=boundary, previous_mastery_debt=mastery_debt)
        else:
            epoch = begin_epoch(**arguments,
                previous_graduate=_dataclasses.asdict(school.current_student),
                previous_graduation_exam=boundary)
        if receipt.get("mentor_epoch") is not None:
            history.append(receipt["mentor_epoch"])
        # New semantics create a fresh championship epoch. Prior matchup receipts
        # stay in archived history, but their veto authority does not cross this boundary.
        epoch["settled_matchups"] = {}
        epoch["championship_school_identity"] = identity
        return identity, epoch, history
    epoch = receipt.get("mentor_epoch")
    if epoch is not None:
        epoch, identity_event = _learning_championship_identity.enforce_school_identity(
            epoch, identity,
            generation=receipt["generation"] + 1,
            student=_dataclasses.asdict(school.current_student))
        if identity_event:
            history.append(receipt["mentor_epoch"])
    return identity, epoch, history


def _profile_adoption_receipt(
        receipt, compatibility_course, successor, successor_program,
        release_file, admission, identity, epoch, history, revised_grade,
        graph, *, invalidate_assessment_evidence=False):
    heads = _factory_executable_release.answer_heads_from_executable_release(successor, graph)
    numeric_values = heads.get("numeric_active", {}).get("values")
    dimensions = _factory_provider_dimensions.provider_dimension_telemetry(successor)
    candidate = {
        **receipt,
        "curriculum_mode": compatibility_course.version,
        "config": {**receipt["config"], "answer_heads": heads},
        "live_rubric_sha256": successor_program.grades[-1].assessment_sha256,
        "factory_release_sha256": successor.release_sha256,
        "factory_release_file": release_file,
        "factory_release_schema": successor.schema,
        "factory_admission_v2": _dataclasses.asdict(admission),
        "championship_school_identity": identity,
        "mentor_epoch": epoch,
        "championship_epoch_history": history,
        "provider_dimensions": list(dimensions),
        "last_exam": (
            None if revised_grade is not None or invalidate_assessment_evidence
            else receipt.get("last_exam")),
    }
    if numeric_values is not None:
        candidate["numeric_maximum"] = len(numeric_values) - 1
    candidate.pop("qualification_cohort_v2", None)
    if invalidate_assessment_evidence:
        candidate.pop("fixed_frontier_exam", None)
        candidate.pop("last_generalization_cohort_v2", None)
    return candidate


def _adopt_executable_profile(
        run_dir, receipt, grade_a_course, source_root, graph, profile, *,
        compiled_successor=None, allow_mastery_debt=False,
        debt_cadence_policy=_UNSPECIFIED_DEBT_CADENCE_POLICY,
        invalidate_assessment_evidence=False, catalog_boundary_evidence,
        profile_transition, verify_profile_successor):
    """Adopt one same-ABI v2 profile change without release-name dispatch."""
    predecessor = _runtime_admission._require_executable_factory_admission(run_dir, receipt, graph)
    previous_program = _factory_schedule.schedule_program_from_executable_release(predecessor)
    school = _runtime_state._state_from_json(receipt["school"], previous_program)
    compatibility_course = _compatibility_executable_projection.legacy_course_for_profile(
        grade_a_course, source_root, profile)
    successor = compiled_successor or _factory_executable_release.compile_successor_profile_release(
        predecessor,
        profile,
        _source_adapters_school.live_source_registry(),
        _factory_live_answers.live_answer_registry(),
        source_root=source_root,
        graph=graph,
        verification_seed=2026101906)
    verify_profile_successor(predecessor, successor, graph, profile)
    successor_program = _factory_schedule.schedule_program_from_executable_release(successor)
    mastery_debt = None
    if allow_mastery_debt:
        _, mastery_debt = catalog_boundary_evidence(
            predecessor, previous_program, school, receipt, allow_mastery_debt=True)
    next_state, revised_grade, appended = profile_transition(
        previous_program, successor_program, school, mastery_debt=mastery_debt,
        debt_cadence_policy=debt_cadence_policy)
    successor, release_file, admission = _runtime_admission._executable_factory_admission(
        run_dir, successor, next_state.current_student,
        receipt["semantic_graph_sha256"], graph)
    identity, epoch, history = _profile_championship_state(
        receipt, predecessor, successor, school, next_state, appended=appended,
        mastery_debt=mastery_debt)
    candidate = _profile_adoption_receipt(
        receipt, compatibility_course, successor, successor_program,
        release_file, admission, identity, epoch, history, revised_grade, graph,
        invalidate_assessment_evidence=invalidate_assessment_evidence)
    if allow_mastery_debt:
        candidate["last_exam"] = receipt["debt_admission_boundary_exam"]
        candidate.pop("fixed_frontier_exam", None)
    record = _runtime_checkpoints._advance(
        run_dir, candidate, next_state,
        result="ACTIVE_GRADE_" + next_state.grade, persist=False)
    event = {
        "event": "SCHOOL_EXECUTION_PROFILE_ADOPTED",
        "generation": record["generation"],
        "grade": next_state.grade,
        "profile_id": successor.profile.profile_id,
        "transition_kind": (
            "APPEND_GRADE" if appended else
            "REVISE_SOURCE" if (
                revised_grade is None and successor.profile == predecessor.profile and
                previous_program == successor_program) else
            "REVISE_PROFILE"),
        "revised_grade": revised_grade,
        "debt_admission": allow_mastery_debt,
        "carried_mastery_debt": list(next_state.carried_mastery_debt),
        "previous_factory_release_sha256": predecessor.release_sha256,
        "factory_release_sha256": successor.release_sha256,
        "student_sha256": school.current_student.sha256,
        "optimizer_step": school.current_student.optimizer_step,
        "numeric_maximum": record.get("numeric_maximum"),
        "provider_dimensions": record.get("provider_dimensions", []),
        "actual_neural_updates": 0,
    }
    record = _runtime_checkpoints._persist(
        run_dir, _runtime_checkpoints._with_delivery_outbox(record, (event,)))
    _runtime_checkpoints._reconcile_delivery_outbox(run_dir, record)
    return record, compatibility_course, successor, successor_program


def _adopt_source_presentation_revision_if_needed(
        run_dir, receipt, grade_a_course, source_root, graph, predecessor, *,
        source_presentation_revision_required, adopt_executable_profile):
    """Adopt authorized source presentation revisions with zero neural updates."""
    program = _factory_schedule.schedule_program_from_executable_release(predecessor)
    compatibility_course = _compatibility_executable_projection.legacy_course_for_profile(
        grade_a_course, source_root, predecessor.profile)
    registry = _source_adapters_school.live_source_registry()
    if not source_presentation_revision_required(predecessor, registry):
        return receipt, compatibility_course, predecessor, program
    successor = _factory_executable_release.compile_successor_profile_release(
        predecessor, predecessor.profile, registry,
        _factory_live_answers.live_answer_registry(),
        source_root=source_root, graph=graph, verification_seed=2026102701)
    return adopt_executable_profile(
        run_dir, receipt, grade_a_course, source_root, graph,
        predecessor.profile, compiled_successor=successor,
        invalidate_assessment_evidence=True)
