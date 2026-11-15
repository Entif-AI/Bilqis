"""Final retention, teacher, checkpoint, and event persistence for an exam."""
from __future__ import annotations

from dataclasses import dataclass
import dataclasses as _dataclasses
from typing import Any

import bilqis_mlx.diagnostics.exam_events as _diagnostics_exam_events
import bilqis_mlx.generated_assessment as _bilqis_mlx_generated_assessment
import bilqis_mlx.learning.teacher_feedback as _learning_teacher_feedback
import bilqis_mlx.learning.whole_student_retention as _learning_whole_student_retention
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints

from .diagnostics import _score_parent_for_paired_s3
from .shared import _assessment_scope_sha256, _school_result_label


@dataclass(frozen=True)
class ExamFinalization:
    mx: Any
    run_dir: Any
    receipt: dict
    graph: Any
    school: Any
    full_scope: tuple
    blocked_before: tuple
    blocked_after: tuple
    routine_cohort: Any
    routine_file: str
    routine_measured: dict
    routine_guesses: Any
    parent_checkpoint: Any
    parent_routine_scores: Any
    parent_routine_issue: Any
    cohort: Any
    cohort_pointer: dict
    cohort_file: str
    rows: list
    guesses: Any
    measured: dict
    assessment: Any
    advanced: Any
    qualification: Any
    promotion_passed: bool
    frontier: dict
    roles: tuple
    compared: list
    stagnation: Any
    stagnation_events: tuple
    epoch: Any
    perfect: dict
    frozen_soups: dict
    soup_changes: tuple
    championship_roles: tuple
    championship_decisions: tuple
    generator: str
    scheduler_only: bool


def finalize_exam(state: ExamFinalization):
    s = state
    scores = {k: {"correct": v.correct, "total": v.total}
              for k, v in s.assessment.scores.items()}
    final_scope_sha = _assessment_scope_sha256(s.full_scope, scores)
    graduation_roles = ()
    last_exam = {
        **s.cohort_pointer,
        "assessment_grade": s.school.grade,
        "grade_exam_epoch": s.school.grade_exam_epoch,
        "exam_plane": (
            "PROMOTION" if s.qualification is not None else "ROUTINE"),
        "grade_test_lifecycle": (
            _bilqis_mlx_generated_assessment.PROMOTION_ATTEMPT_LIFECYCLE
            if s.qualification is not None else
            _bilqis_mlx_generated_assessment.ROUTINE_EVAL_LIFECYCLE),
        "assessment_scope_sha256": final_scope_sha,
        "evaluation_id": s.assessment.evaluation_id,
        "exam_rubric_sha256": s.assessment.rubric_digest,
        "cohort_sha256": s.cohort.digest,
        "cohort_file": s.cohort_file,
        "cohort_seed": s.cohort.seed,
        "routine_cohort_sha256": s.routine_cohort.digest,
        "routine_cohort_file": s.routine_file,
        "routine_cohort_seed": s.routine_cohort.seed,
        "routine_scores": s.routine_measured["scores"],
        "graduation_perfect_roles": list(graduation_roles),
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
    if s.receipt.get("_candidate_cohort_sha256") is not None:
        last_exam["candidate_cohort_sha256"] = s.receipt["_candidate_cohort_sha256"]
    if s.qualification is not None:
        last_exam["promotion_cohort_sha256"] = s.qualification["cohort_sha256"]
    peaks, retention_status = _learning_whole_student_retention.advance_peaks(
        s.receipt.get("whole_student_peaks", []),
        curriculum_mode=s.receipt["curriculum_mode"],
        numeric_maximum=s.receipt.get("numeric_maximum"),
        rubric_sha256=s.assessment.rubric_digest,
        cohort_sha256=s.cohort.digest,
        assessment_scope_sha256=last_exam["assessment_scope_sha256"],
        scores=scores, checkpoint=_dataclasses.asdict(s.school.current_student))
    last_exam["whole_student_retention"] = retention_status
    pending = (*s.receipt.get("_pending_visit_events", ()), *s.stagnation_events)
    _runtime_checkpoints._notify_viewer({
        "_runtime_phase": "DIAGNOSTICS", "_dashboard_redraw": True})
    exam_warnings = _diagnostics_exam_events.summarize_completed_exam_safely(
        s.run_dir, s.receipt, last_exam)
    if s.cohort.digest == s.routine_cohort.digest:
        paired_parent_scores = s.parent_routine_scores
        paired_parent_issue = s.parent_routine_issue
    else:
        paired_parent_scores, paired_parent_issue = _score_parent_for_paired_s3(
            s.mx, s.run_dir, s.receipt, s.parent_checkpoint, s.cohort,
            s.graph, scores)
    exam_warnings = _diagnostics_exam_events.apply_paired_checkpoint_s3(
        exam_warnings,
        parent_scores=paired_parent_scores,
        current_scores=scores,
        parent_sha256=s.parent_checkpoint.sha256,
        current_sha256=s.school.current_student.sha256,
        parent_step=s.parent_checkpoint.optimizer_step,
        current_step=s.school.current_student.optimizer_step,
        cohort_sha256=s.cohort.digest,
        unavailable_reason=paired_parent_issue)
    last_exam["learning_diagnostics"] = exam_warnings
    teacher_outcomes = _learning_teacher_feedback.summarize_teacher_outcomes(
        s.receipt.get("last_exam"), last_exam, pending)
    last_exam["teacher_outcomes"] = teacher_outcomes
    priority = _learning_teacher_feedback.reconcile_unresolved_misses(
        s.receipt.get("teacher_misses", ()), s.rows, s.guesses)
    if s.blocked_after:
        blocked_set = set(s.blocked_after)
        priority = [
            row for row in priority if row["capability"] not in blocked_set]
    unresolved_ids = {row["id"] for row in priority}
    miss_exposures = {
        identity: count for identity, count in
        s.receipt.get("teacher_miss_exposures", {}).items()
        if identity in unresolved_ids and type(count) is int and count >= 0
    }
    for identity in unresolved_ids:
        miss_exposures.setdefault(identity, 0)
    migrated_receipt = {
        **s.receipt,
        "teacher_misses": priority,
        "whole_student_peaks": peaks,
        "graduation_perfect": s.perfect,
        "grade_soups": s.frozen_soups,
        "teacher_miss_exposures": miss_exposures,
        "legacy_frontier_pending_replay": False,
        "live_rubric_sha256": s.assessment.rubric_digest,
    }
    migrated_receipt.pop("_routine_learning_diagnostics", None)
    migrated_receipt.pop("_candidate_cohort_sha256", None)
    if s.stagnation is not None:
        migrated_receipt["stagnation_session"] = s.stagnation
    if s.qualification is not None and not s.promotion_passed:
        migrated_receipt["qualification_cohort_v2"] = s.qualification
        migrated_receipt.pop("qualification_cohort", None)
    elif s.promotion_passed:
        migrated_receipt.pop("qualification_cohort_v2", None)
        migrated_receipt.pop("qualification_cohort", None)
    if s.epoch is not None:
        migrated_receipt["mentor_epoch"] = s.epoch
    migrated_receipt.pop("teacher_miss_cursor", None)
    result = _runtime_checkpoints._advance(
        s.run_dir, migrated_receipt, s.advanced, frontier=s.frontier,
        model_bundle=s.school.current_student.filename, last_exam=last_exam,
        result=_school_result_label(s.advanced), persist=False)
    exam_event = {
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
        "learning_diagnostics": exam_warnings,
        "teacher_outcomes": teacher_outcomes,
        "whole_student_retention": retention_status,
        "flash_scheduler_only": s.scheduler_only,
        "withheld_capabilities": list(s.blocked_before),
        "qualification_authority_changed": False if s.scheduler_only else None,
        "champions_changed": False if s.scheduler_only else None,
    }
    if s.qualification is not None:
        exam_event["qualification_cohort_sha256"] = (
            s.qualification["cohort_sha256"])
    if s.epoch is not None:
        exam_event["championship_epoch"] = {
            "baseline_sha256": s.epoch["baseline"]["sha256"],
            "earned_roles": (
                [] if s.scheduler_only else list(s.championship_roles)),
            "active_role_count": len(s.epoch.get("active_roles", {})),
            "active_soup_grades": sorted(
                s.epoch.get("active_grade_soups", {})),
            "cross_origin_decisions": (
                [] if s.scheduler_only else list(s.championship_decisions)),
        }
    result = _runtime_checkpoints._persist(
        s.run_dir,
        _runtime_checkpoints._with_delivery_outbox(
            result,
            _runtime_checkpoints._boundary_delivery_events(
                result, pending, s.roles, exam_event)))
    _runtime_checkpoints._publish_boundary(
        s.run_dir, result, pending, s.roles, exam_event=exam_event)
    return result
