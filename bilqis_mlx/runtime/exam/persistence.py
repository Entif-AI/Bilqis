"""Persist exam diagnostics, teacher state, and boundary events."""
from __future__ import annotations

import dataclasses as _dataclasses

import bilqis_mlx.diagnostics.exam_events as _diagnostics_exam_events
import bilqis_mlx.generated_assessment as _bilqis_mlx_generated_assessment
import bilqis_mlx.learning.teacher_feedback as _learning_teacher_feedback
import bilqis_mlx.learning.whole_student_retention as _learning_whole_student_retention
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints

from .diagnostics import _score_parent_for_paired_s3
from .shared import _assessment_scope_sha256, _school_result_label


def _last_exam(state, scores):
    s = state
    record = {
        **s.cohort_pointer,
        "assessment_grade": s.school.grade,
        "grade_exam_epoch": s.school.grade_exam_epoch,
        "exam_plane": "PROMOTION" if s.qualification is not None else "ROUTINE",
        "grade_test_lifecycle": (
            _bilqis_mlx_generated_assessment.PROMOTION_ATTEMPT_LIFECYCLE
            if s.qualification is not None else
            _bilqis_mlx_generated_assessment.ROUTINE_EVAL_LIFECYCLE),
        "assessment_scope_sha256": _assessment_scope_sha256(
            s.full_scope, scores),
        "evaluation_id": s.assessment.evaluation_id,
        "exam_rubric_sha256": s.assessment.rubric_digest,
        "cohort_sha256": s.cohort.digest,
        "cohort_file": s.cohort_file,
        "cohort_seed": s.cohort.seed,
        "routine_cohort_sha256": s.routine_cohort.digest,
        "routine_cohort_file": s.routine_file,
        "routine_cohort_seed": s.routine_cohort.seed,
        "routine_scores": s.routine_measured["scores"],
        "graduation_perfect_roles": [],
        "championship_roles": list(s.championship_roles),
        "grade_soups_refreshed": list(s.soup_changes),
        "championship_decisions": list(s.championship_decisions),
        "generator_version": s.generator,
        "incumbent_comparisons": s.compared,
        "misses_for_teacher": list(s.measured["misses_for_teacher"]),
        "student_sha256": s.assessment.checkpoint_sha256,
        "optimizer_step": s.assessment.optimizer_step,
        "scores": scores,
        "withheld_capabilities": list(s.blocked_before),
        "stagnation_quarantined": list(s.blocked_after),
        "routine_learning_diagnostics": s.receipt["_routine_learning_diagnostics"],
        "flash_scheduler_only": s.scheduler_only,
    }
    candidate = s.receipt.get("_candidate_cohort_sha256")
    if candidate is not None:
        record["candidate_cohort_sha256"] = candidate
    if s.qualification is not None:
        record["promotion_cohort_sha256"] = s.qualification["cohort_sha256"]
    return record


def _retention(state, last_exam, scores):
    return _learning_whole_student_retention.advance_peaks(
        state.receipt.get("whole_student_peaks", []),
        curriculum_mode=state.receipt["curriculum_mode"],
        numeric_maximum=state.receipt.get("numeric_maximum"),
        rubric_sha256=state.assessment.rubric_digest,
        cohort_sha256=state.cohort.digest,
        assessment_scope_sha256=last_exam["assessment_scope_sha256"],
        scores=scores,
        checkpoint=_dataclasses.asdict(state.school.current_student),
    )


def _learning_diagnostics(state, last_exam, scores):
    s = state
    _runtime_checkpoints._notify_viewer({
        "_runtime_phase": "DIAGNOSTICS", "_dashboard_redraw": True})
    warnings = _diagnostics_exam_events.summarize_completed_exam_safely(
        s.run_dir, s.receipt, last_exam)
    if s.cohort.digest == s.routine_cohort.digest:
        parent_scores = s.parent_routine_scores
        parent_issue = s.parent_routine_issue
    else:
        parent_scores, parent_issue = _score_parent_for_paired_s3(
            s.mx, s.run_dir, s.receipt, s.parent_checkpoint, s.cohort,
            s.graph, scores)
    return _diagnostics_exam_events.apply_paired_checkpoint_s3(
        warnings,
        parent_scores=parent_scores,
        current_scores=scores,
        parent_sha256=s.parent_checkpoint.sha256,
        current_sha256=s.school.current_student.sha256,
        parent_step=s.parent_checkpoint.optimizer_step,
        current_step=s.school.current_student.optimizer_step,
        cohort_sha256=s.cohort.digest,
        unavailable_reason=parent_issue,
    )


def _teacher_state(state, last_exam, pending):
    s = state
    outcomes = _learning_teacher_feedback.summarize_teacher_outcomes(
        s.receipt.get("last_exam"), last_exam, pending)
    priority = _learning_teacher_feedback.reconcile_unresolved_misses(
        s.receipt.get("teacher_misses", ()), s.rows, s.guesses)
    if s.blocked_after:
        blocked = set(s.blocked_after)
        priority = [
            row for row in priority if row["capability"] not in blocked]
    unresolved_ids = {row["id"] for row in priority}
    exposures = {
        identity: count for identity, count in
        s.receipt.get("teacher_miss_exposures", {}).items()
        if identity in unresolved_ids and type(count) is int and count >= 0
    }
    for identity in unresolved_ids:
        exposures.setdefault(identity, 0)
    return outcomes, priority, exposures


def _migrated_receipt(state, peaks, priority, exposures):
    s = state
    receipt = {
        **s.receipt,
        "teacher_misses": priority,
        "whole_student_peaks": peaks,
        "graduation_perfect": s.perfect,
        "grade_soups": s.frozen_soups,
        "teacher_miss_exposures": exposures,
        "legacy_frontier_pending_replay": False,
        "live_rubric_sha256": s.assessment.rubric_digest,
    }
    receipt.pop("_routine_learning_diagnostics", None)
    receipt.pop("_candidate_cohort_sha256", None)
    if s.stagnation is not None:
        receipt["stagnation_session"] = s.stagnation
    if s.qualification is not None and not s.promotion_passed:
        receipt["qualification_cohort_v2"] = s.qualification
        receipt.pop("qualification_cohort", None)
    elif s.promotion_passed:
        receipt.pop("qualification_cohort_v2", None)
        receipt.pop("qualification_cohort", None)
    if s.epoch is not None:
        receipt["mentor_epoch"] = s.epoch
    receipt.pop("teacher_miss_cursor", None)
    return receipt


def _exam_event(
        state, result, last_exam, scores, priority, warnings,
        teacher_outcomes, retention_status,
):
    s = state
    event = {
        "event": ("SCHOOL_FLASH_ROUTINE_EXAM_COMMITTED" if s.scheduler_only
                  else "SCHOOL_LIVE_EXAM_COMMITTED"),
        "grade": s.school.grade,
        "generation": result["generation"],
        "grade_exam_epoch": s.school.grade_exam_epoch,
        "exam_plane": last_exam["exam_plane"],
        "grade_test_lifecycle": last_exam["grade_test_lifecycle"],
        "assessment_scope_sha256": last_exam["assessment_scope_sha256"],
        "introduction_stage": s.school.introduction_stage,
        "scores": scores,
        "phase": s.advanced.stage,
        "student_sha256": s.assessment.checkpoint_sha256,
        "optimizer_step": s.assessment.optimizer_step,
        "rubric": s.assessment.rubric_digest,
        "cohort_sha256": s.cohort.digest,
        "generator_version": s.generator,
        "cohort_seed": s.cohort.seed,
        "cohort_file": last_exam["cohort_file"],
        "routine_cohort_sha256": s.routine_cohort.digest,
        "incumbent_comparisons": s.compared,
        "teacher_miss_count": len(priority),
        "learning_diagnostics": warnings,
        "teacher_outcomes": teacher_outcomes,
        "whole_student_retention": retention_status,
        "flash_scheduler_only": s.scheduler_only,
        "withheld_capabilities": list(s.blocked_before),
        "qualification_authority_changed": False if s.scheduler_only else None,
        "champions_changed": False if s.scheduler_only else None,
    }
    if s.qualification is not None:
        event["qualification_cohort_sha256"] = (
            s.qualification["cohort_sha256"])
    if s.epoch is not None:
        event["championship_epoch"] = {
            "baseline_sha256": s.epoch["baseline"]["sha256"],
            "earned_roles": (
                [] if s.scheduler_only else list(s.championship_roles)),
            "active_role_count": len(s.epoch.get("active_roles", {})),
            "active_soup_grades": sorted(
                s.epoch.get("active_grade_soups", {})),
            "cross_origin_decisions": (
                [] if s.scheduler_only else list(s.championship_decisions)),
        }
    return event


def finalize_exam(state):
    scores = {
        key: {"correct": value.correct, "total": value.total}
        for key, value in state.assessment.scores.items()
    }
    last_exam = _last_exam(state, scores)
    peaks, retention_status = _retention(state, last_exam, scores)
    last_exam["whole_student_retention"] = retention_status
    pending = (
        *state.receipt.get("_pending_visit_events", ()),
        *state.stagnation_events,
    )
    warnings = _learning_diagnostics(state, last_exam, scores)
    last_exam["learning_diagnostics"] = warnings
    teacher_outcomes, priority, exposures = _teacher_state(
        state, last_exam, pending)
    last_exam["teacher_outcomes"] = teacher_outcomes
    receipt = _migrated_receipt(state, peaks, priority, exposures)
    result = _runtime_checkpoints._advance(
        state.run_dir, receipt, state.advanced, frontier=state.frontier,
        model_bundle=state.school.current_student.filename,
        last_exam=last_exam, result=_school_result_label(state.advanced),
        persist=False)
    event = _exam_event(
        state, result, last_exam, scores, priority, warnings,
        teacher_outcomes, retention_status)
    result = _runtime_checkpoints._persist(
        state.run_dir,
        _runtime_checkpoints._with_delivery_outbox(
            result,
            _runtime_checkpoints._boundary_delivery_events(
                result, pending, state.roles, event)))
    _runtime_checkpoints._publish_boundary(
        state.run_dir, result, pending, state.roles, exam_event=event)
    return result
