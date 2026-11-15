"""Bounded phases for routine, promotion, and championship exam work."""
from __future__ import annotations

from dataclasses import dataclass
import dataclasses as _dataclasses
from typing import Any

import bilqis_mlx.curriculum.scheduler as _curriculum_scheduler
import bilqis_mlx.diagnostics.exam_events as _diagnostics_exam_events
import bilqis_mlx.factory.schedule as _factory_schedule
import bilqis_mlx.generated_assessment as _bilqis_mlx_generated_assessment
import bilqis_mlx.learning.championship_runtime as _learning_championship_runtime
import bilqis_mlx.learning.epoch_championships as _learning_epoch_championships
import bilqis_mlx.learning.lesson_guidance as _learning_lesson_guidance
import bilqis_mlx.learning.mentor_epoch as _learning_mentor_epoch
import bilqis_mlx.learning.stagnation_control as _learning_stagnation_control
import bilqis_mlx.learning.student_ops as _learning_student_ops
import bilqis_mlx.runtime.admission as _runtime_admission
import bilqis_mlx.runtime.assessment as _runtime_assessment
import bilqis_mlx.runtime.boundary_commit as _runtime_boundary_commit
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints
import bilqis_mlx.runtime.reconciliation as _runtime_reconciliation
import bilqis_mlx.runtime.state as _runtime_state
import bilqis_mlx.source_adapters.school as _source_adapters_school

from .diagnostics import (
    _paired_stagnation_progress,
    _score_parent_for_paired_s3,
)
from .shared import _assessment_scope_sha256, _promotion_due_after_routine


@dataclass(frozen=True)
class ExamSetup:
    release: Any
    program: Any
    school: Any
    receipt: dict
    stagnation: Any
    blocked_before: tuple
    full_scope: tuple
    active_scope: tuple
    parent_checkpoint: Any
    source_registry: Any
    routine_cohort: Any
    routine_pointer: dict
    routine_file: str
    rubric: str
    generator: str
    routine_rows: list
    frontier: dict
    roles: tuple
    compared: list
    candidate_cohort: Any
    candidate_measured: Any
    candidate_guesses: Any


@dataclass(frozen=True)
class RoutinePhase:
    guesses: Any
    measured: dict
    assessment: Any
    advanced: Any
    warnings: Any
    stagnation: Any
    stagnation_events: tuple
    blocked_after: tuple
    parent_scores: Any
    parent_issue: Any
    championship_exams: tuple


@dataclass(frozen=True)
class SelectedPhase:
    cohort: Any
    pointer: dict
    cohort_file: str
    rows: list
    guesses: Any
    measured: dict
    assessment: Any
    advanced: Any
    qualification: Any
    promotion_passed: bool
    championship_exams: tuple


@dataclass(frozen=True)
class ChampionshipPhase:
    epoch: Any
    roles: tuple
    decisions: tuple
    perfect: dict
    frozen_soups: dict
    soup_changes: tuple


def prepare_exam(
        mx, run_dir, receipt, manifest, course, source_root, parameters,
        optimizer, graph, *, reserve_gib, scheduler_only):
    release = _runtime_admission._read_executable_factory_release_artifact(
        run_dir, receipt)
    program = _factory_schedule.schedule_program_from_executable_release(release)
    school = _runtime_state._state_from_json(receipt["school"], program)
    if not school.stage.startswith("ASSESS_"):
        raise ValueError("HUMAN_TRAINER_EXAM_OUTSIDE_SCHEDULED_BOUNDARY")
    if receipt.get("championship_school_identity") != (
            _learning_championship_runtime._live_championship_identity(
                receipt, course, graph, parameters)):
        raise ValueError("CHAMPIONSHIP_SCHOOL_IDENTITY_RESET_REQUIRED")
    stagnation = receipt.get("stagnation_session")
    blocked = _learning_stagnation_control.quarantined_capabilities(stagnation)
    full_scope = _curriculum_scheduler.assessment_capabilities(program, school)
    active_scope = tuple(cap for cap in full_scope if cap not in set(blocked))
    _runtime_assessment._require_active_stagnation_scope(active_scope)
    parent_checkpoint = school.current_student
    source_registry = _source_adapters_school.live_source_registry()
    routine_cohort, routine_pointer = _runtime_assessment._routine_executable_cohort(
        run_dir, receipt, manifest, release, source_registry, source_root, graph,
        capabilities=active_scope, assessment_epoch=school.grade_exam_epoch)
    candidate_cohort = candidate_measured = candidate_guesses = None
    frontier = dict(receipt.get("capability_best", {}))
    roles, compared = (), []
    if scheduler_only:
        if int(optimizer.state["step"].item()) != school.current_student.optimizer_step:
            raise ValueError(
                "FLASH_SCHEDULER_EXAM_REQUIRES_CHECKPOINTED_STUDENT")
    else:
        candidate_cohort, _ = _runtime_assessment._candidate_executable_cohort(
            run_dir, receipt, manifest, release, source_registry, source_root,
            graph, capabilities=active_scope)
        candidate_guesses = _learning_student_ops._predictions(
            mx, parameters, list(candidate_cohort.rows),
            receipt["config"], receipt["answer_ids"])
        school, frontier, roles, compared = (
            _runtime_boundary_commit._commit_scored_student(
                mx, run_dir, receipt, manifest, course, school,
                candidate_cohort, candidate_guesses, parameters, optimizer,
                graph, reserve_gib=reserve_gib,
                allowed_capabilities=active_scope))
        receipt = _learning_championship_runtime._bind_checkpoint_origin(
            receipt, school.current_student)
        candidate_measured = _bilqis_mlx_generated_assessment.score(
            candidate_cohort, candidate_guesses,
            _dataclasses.asdict(school.current_student))
    return ExamSetup(
        release, program, school, receipt, stagnation, blocked, full_scope,
        active_scope, parent_checkpoint, source_registry, routine_cohort,
        routine_pointer, routine_pointer["cohort_file"],
        routine_pointer["rubric_sha256"], routine_cohort.generator_version,
        list(routine_cohort.rows), frontier, roles, compared, candidate_cohort,
        candidate_measured, candidate_guesses)


def _routine_assessment(s, measured):
    return _curriculum_scheduler.Assessment(
        checkpoint_sha256=s.school.current_student.sha256,
        optimizer_step=s.school.current_student.optimizer_step,
        course_digest=s.program.digest(),
        rubric_digest=s.rubric,
        scores={
            cap: _curriculum_scheduler.Score(**entry)
            for cap, entry in measured["scores"].items()
        },
        evaluation_id=(
            "source-oracled-routine-cohort/" + s.routine_cohort.digest + "/" +
            s.school.current_student.sha256))


def _routine_last_exam(s, measured, assessment):
    return {
        **s.routine_pointer,
        "assessment_grade": s.school.grade,
        "grade_exam_epoch": s.school.grade_exam_epoch,
        "exam_plane": "ROUTINE",
        "grade_test_lifecycle": _bilqis_mlx_generated_assessment.ROUTINE_EVAL_LIFECYCLE,
        "assessment_scope_sha256": _assessment_scope_sha256(
            s.full_scope, {cap: None for cap in s.active_scope}),
        "evaluation_id": assessment.evaluation_id,
        "exam_rubric_sha256": assessment.rubric_digest,
        "cohort_sha256": s.routine_cohort.digest,
        "cohort_file": s.routine_file,
        "cohort_seed": s.routine_cohort.seed,
        "generator_version": s.generator,
        "misses_for_teacher": list(measured["misses_for_teacher"]),
        "student_sha256": assessment.checkpoint_sha256,
        "optimizer_step": assessment.optimizer_step,
        "scores": measured["scores"],
    }


def _routine_advanced(s, assessment, scheduler_only):
    return (
        _curriculum_scheduler.assess_withheld(
            s.program, s.school, assessment, s.blocked_before)
        if s.blocked_before else
        _curriculum_scheduler.assess_flash(s.program, s.school, assessment)
        if scheduler_only else
        _curriculum_scheduler.assess(s.program, s.school, assessment))


def run_routine(
        mx, run_dir, setup, graph, parameters, *, scheduler_only,
        session_elapsed_seconds):
    s = setup
    guesses = _learning_student_ops._predictions(
        mx, parameters, s.routine_rows,
        s.receipt["config"], s.receipt["answer_ids"])
    measured = _bilqis_mlx_generated_assessment.score(
        s.routine_cohort, guesses, _dataclasses.asdict(s.school.current_student))
    progressed, usable = _paired_stagnation_progress(
        mx, run_dir, s.receipt, s.stagnation, s.routine_cohort, graph,
        s.school.current_student, measured["scores"])
    exams = (() if scheduler_only else (
        (s.candidate_cohort, s.candidate_measured, s.candidate_guesses),
        (s.routine_cohort, measured, guesses),
    ))
    parent_scores, parent_issue = _score_parent_for_paired_s3(
        mx, run_dir, s.receipt, s.parent_checkpoint, s.routine_cohort, graph,
        measured["scores"])
    assessment = _routine_assessment(s, measured)
    advanced = _routine_advanced(s, assessment, scheduler_only)
    last_exam = _routine_last_exam(s, measured, assessment)
    _runtime_checkpoints._notify_viewer({
        "_runtime_phase": "DIAGNOSTICS", "_dashboard_redraw": True})
    warnings = _diagnostics_exam_events.summarize_completed_exam_safely(
        run_dir, s.receipt, last_exam)
    warnings = _diagnostics_exam_events.apply_paired_checkpoint_s3(
        warnings, parent_scores=parent_scores, current_scores=measured["scores"],
        parent_sha256=s.parent_checkpoint.sha256,
        current_sha256=s.school.current_student.sha256,
        parent_step=s.parent_checkpoint.optimizer_step,
        current_step=s.school.current_student.optimizer_step,
        cohort_sha256=s.routine_cohort.digest,
        unavailable_reason=parent_issue)
    suppressed = _learning_stagnation_control.grace_suppressed_capabilities(
        s.receipt.get("stagnation_grace"), required_capabilities=s.full_scope,
        optimizer_step=assessment.optimizer_step)
    stagnation, events, advanced, blocked_after = (
        _runtime_reconciliation._advance_stagnation_after_routine(
            program=s.program, school=s.school, routine_assessment=assessment,
            routine_advanced=advanced, stagnation=s.stagnation,
            blocked_before=s.blocked_before, active_scope=s.active_scope,
            routine_measured=measured, routine_warnings=warnings,
            generation=s.receipt["generation"] + 1,
            quarantine_suppressed=suppressed,
            session_elapsed_seconds=session_elapsed_seconds,
            paired_progressed=progressed, paired_progress_usable=usable,
            progress_checkpoint=_dataclasses.asdict(s.school.current_student)))
    return RoutinePhase(
        guesses, measured, assessment, advanced, warnings, stagnation,
        tuple(events), blocked_after, parent_scores, parent_issue, exams)


def run_promotion(
        mx, run_dir, setup, routine, manifest, source_root, graph, parameters,
        *, scheduler_only):
    s, r = setup, routine
    selected = SelectedPhase(
        s.routine_cohort, s.routine_pointer, s.routine_file, s.routine_rows,
        r.guesses, r.measured, r.assessment, r.advanced, None, False,
        r.championship_exams)
    complete = (
        not s.blocked_before and not r.blocked_after
        and tuple(s.active_scope) == tuple(s.full_scope))
    if scheduler_only or not _promotion_due_after_routine(
            s.school, r.advanced, complete_assessment=complete):
        return selected
    cohort, qualification = _runtime_assessment._promotion_executable_cohort(
        run_dir, s.receipt, manifest, s.release, s.source_registry, source_root,
        graph, capabilities=s.active_scope,
        assessment_epoch=s.school.grade_exam_epoch)
    rows = list(cohort.rows)
    guesses = _learning_student_ops._predictions(
        mx, parameters, rows, s.receipt["config"], s.receipt["answer_ids"])
    measured = _bilqis_mlx_generated_assessment.score(
        cohort, guesses, _dataclasses.asdict(s.school.current_student))
    assessment = _curriculum_scheduler.Assessment(
        checkpoint_sha256=s.school.current_student.sha256,
        optimizer_step=s.school.current_student.optimizer_step,
        course_digest=s.program.digest(), rubric_digest=s.rubric,
        scores={
            cap: _curriculum_scheduler.Score(**entry)
            for cap, entry in measured["scores"].items()
        },
        evaluation_id=(
            "source-oracled-promotion-cohort/" + cohort.digest + "/" +
            s.school.current_student.sha256))
    advanced = _curriculum_scheduler.assess(s.program, s.school, assessment)
    passed = _promotion_due_after_routine(
        s.school, advanced, complete_assessment=complete)
    exams = (*r.championship_exams, (cohort, measured, guesses))
    return SelectedPhase(
        cohort, qualification, qualification["cohort_file"], rows, guesses,
        measured, assessment, advanced, qualification, passed, exams)


def run_championship(
        mx, run_dir, setup, selected, course, graph, parameters, *,
        reserve_gib, scheduler_only):
    s = setup
    epoch = s.receipt.get("mentor_epoch")
    if epoch is None and not scheduler_only:
        epoch = _learning_mentor_epoch.begin_initial_epoch(
            student=_dataclasses.asdict(s.school.current_student),
            introduced_grade=s.school.grade,
            source_graph_sha256=_runtime_state._fingerprint(graph),
            frontier=s.receipt.get("graduation_perfect", {}),
            soups=s.receipt.get("grade_soups", {}))
        epoch["settled_matchups"] = {}
        epoch["championship_school_identity"] = (
            s.receipt["championship_school_identity"])
    if scheduler_only:
        return ChampionshipPhase(
            epoch, (), (), s.receipt.get("graduation_perfect", {}),
            s.receipt.get("grade_soups", {}), ())
    epoch = _learning_championship_runtime._hydrate_championship_witnesses(
        mx, run_dir, s.receipt, epoch, graph)
    changed_roles, decisions = set(), []
    for cohort, result, predicted in selected.championship_exams:
        epoch, changed, verdicts = (
            _learning_championship_runtime._advance_exam_championships(
                mx, run_dir, s.receipt, epoch, course, s.school, cohort,
                result, predicted, parameters, graph))
        changed_roles.update(changed)
        decisions.extend(verdicts)
    new_soups, soup_changes = _learning_lesson_guidance._cook_new_grade_soups(
        mx, run_dir, s.receipt,
        _learning_epoch_championships.active_frontier(epoch), course, graph,
        existing=epoch.get("active_grade_soups", {}), reserve_gib=reserve_gib)
    epoch["active_grade_soups"] = new_soups
    return ChampionshipPhase(
        epoch, tuple(sorted(changed_roles)), tuple(decisions),
        s.receipt.get("graduation_perfect", {}),
        s.receipt.get("grade_soups", {}), tuple(soup_changes))
