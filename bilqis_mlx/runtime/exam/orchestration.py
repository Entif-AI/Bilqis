"""Routine and promotion exam orchestration."""
from __future__ import annotations

import dataclasses as _dataclasses

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
from .finalize import ExamFinalization, finalize_exam
from .shared import _assessment_scope_sha256, _promotion_due_after_routine


def _take_exam(mx, run_dir, receipt, manifest, course, source_root,
               source_checkpoint, parameters, optimizer, graph, *, reserve_gib,
               scheduler_only: bool = False,
               session_elapsed_seconds=None):
    executable_release = (
        _runtime_admission._read_executable_factory_release_artifact(
            run_dir, receipt))
    program = _factory_schedule.schedule_program_from_executable_release(
        executable_release)
    school = _runtime_state._state_from_json(receipt["school"], program)
    if not school.stage.startswith("ASSESS_"):
        raise ValueError("HUMAN_TRAINER_EXAM_OUTSIDE_SCHEDULED_BOUNDARY")
    if (receipt.get("championship_school_identity") !=
            _learning_championship_runtime._live_championship_identity(
                receipt, course, graph, parameters)):
        raise ValueError("CHAMPIONSHIP_SCHOOL_IDENTITY_RESET_REQUIRED")
    stagnation = receipt.get("stagnation_session")
    blocked_before = _learning_stagnation_control.quarantined_capabilities(
        stagnation)
    full_scope = _curriculum_scheduler.assessment_capabilities(program, school)
    active_scope = tuple(
        cap for cap in full_scope if cap not in set(blocked_before))
    _runtime_assessment._require_active_stagnation_scope(active_scope)
    parent_checkpoint = school.current_student
    source_registry = _source_adapters_school.live_source_registry()
    routine_cohort, routine_pointer = _runtime_assessment._routine_executable_cohort(
        run_dir, receipt, manifest, executable_release, source_registry,
        source_root, graph, capabilities=active_scope,
        assessment_epoch=school.grade_exam_epoch)
    routine_file = routine_pointer["cohort_file"]
    rubric = routine_pointer["rubric_sha256"]
    generator = routine_cohort.generator_version
    routine_rows = list(routine_cohort.rows)
    routine_scope_sha = _assessment_scope_sha256(
        full_scope, {cap: None for cap in active_scope})
    candidate_cohort = None
    candidate_measured = None
    frontier = dict(receipt.get("capability_best", {}))
    roles = ()
    compared = []
    if scheduler_only:
        if int(optimizer.state["step"].item()) != (
                school.current_student.optimizer_step):
            raise ValueError(
                "FLASH_SCHEDULER_EXAM_REQUIRES_CHECKPOINTED_STUDENT")
    else:
        candidate_cohort, _ = _runtime_assessment._candidate_executable_cohort(
            run_dir, receipt, manifest, executable_release, source_registry,
            source_root, graph, capabilities=active_scope)
        candidate_guesses = _learning_student_ops._predictions(
            mx, parameters, list(candidate_cohort.rows),
            receipt["config"], receipt["answer_ids"])
        school, frontier, roles, compared = (
            _runtime_boundary_commit._commit_scored_student(
                mx, run_dir, receipt, manifest, course, school,
                candidate_cohort, candidate_guesses,
                parameters, optimizer, graph, reserve_gib=reserve_gib,
                allowed_capabilities=active_scope))
        receipt = _learning_championship_runtime._bind_checkpoint_origin(
            receipt, school.current_student)
        candidate_measured = _bilqis_mlx_generated_assessment.score(
            candidate_cohort, candidate_guesses,
            _dataclasses.asdict(school.current_student))

    routine_guesses = _learning_student_ops._predictions(
        mx, parameters, routine_rows,
        receipt["config"], receipt["answer_ids"])
    routine_measured = _bilqis_mlx_generated_assessment.score(
        routine_cohort, routine_guesses,
        _dataclasses.asdict(school.current_student))
    paired_progressed, paired_progress_usable = _paired_stagnation_progress(
        mx, run_dir, receipt, stagnation, routine_cohort, graph,
        school.current_student, routine_measured["scores"])
    championship_exams = ([] if scheduler_only else [
        (candidate_cohort, candidate_measured, candidate_guesses),
        (routine_cohort, routine_measured, routine_guesses)])
    parent_routine_scores, parent_routine_issue = _score_parent_for_paired_s3(
        mx, run_dir, receipt, parent_checkpoint, routine_cohort, graph,
        routine_measured["scores"])
    routine_assessment = _curriculum_scheduler.Assessment(
        checkpoint_sha256=school.current_student.sha256,
        optimizer_step=school.current_student.optimizer_step,
        course_digest=program.digest(),
        rubric_digest=rubric,
        scores={
            cap: _curriculum_scheduler.Score(**entry)
            for cap, entry in routine_measured["scores"].items()
        },
        evaluation_id=(
            "source-oracled-routine-cohort/" + routine_cohort.digest + "/" +
            school.current_student.sha256))
    routine_advanced = (
        _curriculum_scheduler.assess_withheld(
            program, school, routine_assessment, blocked_before)
        if blocked_before else
        _curriculum_scheduler.assess_flash(program, school, routine_assessment)
        if scheduler_only else
        _curriculum_scheduler.assess(program, school, routine_assessment))
    routine_last_exam = {
        **routine_pointer,
        "assessment_grade": school.grade,
        "grade_exam_epoch": school.grade_exam_epoch,
        "exam_plane": "ROUTINE",
        "grade_test_lifecycle": (
            _bilqis_mlx_generated_assessment.ROUTINE_EVAL_LIFECYCLE),
        "assessment_scope_sha256": routine_scope_sha,
        "evaluation_id": routine_assessment.evaluation_id,
        "exam_rubric_sha256": routine_assessment.rubric_digest,
        "cohort_sha256": routine_cohort.digest,
        "cohort_file": routine_file,
        "cohort_seed": routine_cohort.seed,
        "generator_version": generator,
        "misses_for_teacher": list(
            routine_measured["misses_for_teacher"]),
        "student_sha256": routine_assessment.checkpoint_sha256,
        "optimizer_step": routine_assessment.optimizer_step,
        "scores": routine_measured["scores"],
    }
    _runtime_checkpoints._notify_viewer({
        "_runtime_phase": "DIAGNOSTICS", "_dashboard_redraw": True})
    routine_warnings = (
        _diagnostics_exam_events.summarize_completed_exam_safely(
            run_dir, receipt, routine_last_exam))
    routine_warnings = _diagnostics_exam_events.apply_paired_checkpoint_s3(
        routine_warnings,
        parent_scores=parent_routine_scores,
        current_scores=routine_measured["scores"],
        parent_sha256=parent_checkpoint.sha256,
        current_sha256=school.current_student.sha256,
        parent_step=parent_checkpoint.optimizer_step,
        current_step=school.current_student.optimizer_step,
        cohort_sha256=routine_cohort.digest,
        unavailable_reason=parent_routine_issue)
    quarantine_suppressed = (
        _learning_stagnation_control.grace_suppressed_capabilities(
            receipt.get("stagnation_grace"),
            required_capabilities=full_scope,
            optimizer_step=routine_assessment.optimizer_step))
    stagnation, stagnation_events, routine_advanced, blocked_after = (
        _runtime_reconciliation._advance_stagnation_after_routine(
            program=program,
            school=school,
            routine_assessment=routine_assessment,
            routine_advanced=routine_advanced,
            stagnation=stagnation,
            blocked_before=blocked_before,
            active_scope=active_scope,
            routine_measured=routine_measured,
            routine_warnings=routine_warnings,
            generation=receipt["generation"] + 1,
            quarantine_suppressed=quarantine_suppressed,
            session_elapsed_seconds=session_elapsed_seconds,
            paired_progressed=paired_progressed,
            paired_progress_usable=paired_progress_usable,
            progress_checkpoint=_dataclasses.asdict(school.current_student)))

    qualification = None
    promotion_passed = False
    cohort = routine_cohort
    cohort_pointer = routine_pointer
    cohort_file = routine_file
    rows = routine_rows
    guesses = routine_guesses
    measured = routine_measured
    assessment = routine_assessment
    advanced = routine_advanced
    complete_assessment = (
        not blocked_before and not blocked_after and
        tuple(active_scope) == tuple(full_scope))
    if (not scheduler_only and
            _promotion_due_after_routine(
                school, routine_advanced,
                complete_assessment=complete_assessment)):
        promotion_cohort, qualification = (
            _runtime_assessment._promotion_executable_cohort(
                run_dir, receipt, manifest, executable_release,
                source_registry, source_root, graph,
                capabilities=active_scope,
                assessment_epoch=school.grade_exam_epoch))
        promotion_rows = list(promotion_cohort.rows)
        promotion_guesses = _learning_student_ops._predictions(
            mx, parameters, promotion_rows,
            receipt["config"], receipt["answer_ids"])
        promotion_measured = _bilqis_mlx_generated_assessment.score(
            promotion_cohort, promotion_guesses,
            _dataclasses.asdict(school.current_student))
        championship_exams.append(
            (promotion_cohort, promotion_measured, promotion_guesses))
        promotion_assessment = _curriculum_scheduler.Assessment(
            checkpoint_sha256=school.current_student.sha256,
            optimizer_step=school.current_student.optimizer_step,
            course_digest=program.digest(),
            rubric_digest=rubric,
            scores={
                cap: _curriculum_scheduler.Score(**entry)
                for cap, entry in promotion_measured["scores"].items()
            },
            evaluation_id=(
                "source-oracled-promotion-cohort/" +
                promotion_cohort.digest + "/" +
                school.current_student.sha256))
        cohort = promotion_cohort
        cohort_pointer = qualification
        cohort_file = qualification["cohort_file"]
        rows = promotion_rows
        guesses = promotion_guesses
        measured = promotion_measured
        assessment = promotion_assessment
        promotion_advanced = _curriculum_scheduler.assess(
            program, school, promotion_assessment)
        advanced = promotion_advanced
        promotion_passed = _promotion_due_after_routine(
            school, promotion_advanced,
            complete_assessment=complete_assessment)

    epoch = receipt.get("mentor_epoch")
    championship_decisions = ()
    championship_roles = ()
    if epoch is None and not scheduler_only:
        epoch = _learning_mentor_epoch.begin_initial_epoch(
            student=_dataclasses.asdict(school.current_student),
            introduced_grade=school.grade,
            source_graph_sha256=_runtime_state._fingerprint(graph),
            frontier=receipt.get("graduation_perfect", {}),
            soups=receipt.get("grade_soups", {}))
        epoch["settled_matchups"] = {}
        epoch["championship_school_identity"] = (
            receipt["championship_school_identity"])
    if scheduler_only:
        perfect = receipt.get("graduation_perfect", {})
        frozen_soups = receipt.get("grade_soups", {})
        soup_changes = ()
    else:
        epoch = (
            _learning_championship_runtime._hydrate_championship_witnesses(
                mx, run_dir, receipt, epoch, graph))
        changed_roles, decisions = set(), []
        for examined, result, predicted in championship_exams:
            epoch, changed, verdicts = (
                _learning_championship_runtime._advance_exam_championships(
                    mx, run_dir, receipt, epoch, course, school,
                    examined, result, predicted, parameters, graph))
            changed_roles.update(changed)
            decisions.extend(verdicts)
        championship_roles = tuple(sorted(changed_roles))
        championship_decisions = tuple(decisions)
        new_soups, soup_changes = (
            _learning_lesson_guidance._cook_new_grade_soups(
                mx, run_dir, receipt,
                _learning_epoch_championships.active_frontier(epoch),
                course, graph,
                existing=epoch.get("active_grade_soups", {}),
                reserve_gib=reserve_gib))
        epoch["active_grade_soups"] = new_soups
        perfect = receipt.get("graduation_perfect", {})
        frozen_soups = receipt.get("grade_soups", {})

    final_receipt = {
        **receipt,
        "_routine_learning_diagnostics": routine_warnings,
        "_candidate_cohort_sha256": (
            candidate_cohort.digest if candidate_cohort is not None else None),
    }
    return finalize_exam(ExamFinalization(
        mx=mx,
        run_dir=run_dir,
        receipt=final_receipt,
        graph=graph,
        school=school,
        full_scope=full_scope,
        blocked_before=blocked_before,
        blocked_after=blocked_after,
        routine_cohort=routine_cohort,
        routine_file=routine_file,
        routine_measured=routine_measured,
        routine_guesses=routine_guesses,
        parent_checkpoint=parent_checkpoint,
        parent_routine_scores=parent_routine_scores,
        parent_routine_issue=parent_routine_issue,
        cohort=cohort,
        cohort_pointer=cohort_pointer,
        cohort_file=cohort_file,
        rows=rows,
        guesses=guesses,
        measured=measured,
        assessment=assessment,
        advanced=advanced,
        qualification=qualification,
        promotion_passed=promotion_passed,
        frontier=frontier,
        roles=roles,
        compared=compared,
        stagnation=stagnation,
        stagnation_events=tuple(stagnation_events),
        epoch=epoch,
        perfect=perfect,
        frozen_soups=frozen_soups,
        soup_changes=tuple(soup_changes),
        championship_roles=championship_roles,
        championship_decisions=championship_decisions,
        generator=generator,
        scheduler_only=scheduler_only,
    ))
