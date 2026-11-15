"""Small shared exam-state contracts."""
from __future__ import annotations

import bilqis_mlx.runtime.state as _runtime_state


def _school_result_label(school):
    return (("GRADE_" + school.grade + "_MASTERED_AWAITING_NEXT_GRADE")
            if school.stage == "AWAITING_NEXT_GRADE" else
            ("GRADE_" + school.grade + "_PROMOTED_WITH_DEBT_AWAITING_NEXT_GRADE")
            if school.stage == "AWAITING_NEXT_GRADE_WITH_DEBT" else
            ("GRADE_" + school.revalidation_target_grade +
             "_REVALIDATING_" + school.grade)
            if school.revalidation_target_grade else
            "ACTIVE_GRADE_" + school.grade)


def _promotion_due_after_routine(
        before, after, *, complete_assessment: bool = True) -> bool:
    """Whether the scheduler recorded a real grade qualification."""
    before_epoch = getattr(before, "grade_exam_epoch", None)
    after_epoch = getattr(after, "grade_exam_epoch", None)
    return (
        complete_assessment
        and type(before_epoch) is int
        and type(after_epoch) is int
        and after_epoch == before_epoch + 1
    )


def _assessment_scope_sha256(full_scope, scores) -> str:
    """Bind an assessment scope to the capabilities actually represented."""
    score_ids = set(scores)
    selected = tuple(cap for cap in full_scope if cap in score_ids)
    if not selected or set(selected) != score_ids:
        raise ValueError("HUMAN_TRAINER_EXAM_SCORE_SCOPE_DRIFT")
    return _runtime_state._fingerprint(selected)
