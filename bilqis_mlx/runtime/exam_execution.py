"""Stable facade for developmental-school exam execution."""
from __future__ import annotations

from .exam.debt_admission import _measure_debt_admission_boundary
from .exam.diagnostics import (
    _paired_stagnation_progress,
    _score_parent_for_paired_s3,
)
from .exam.orchestration import _take_exam
from .exam.shared import (
    _assessment_scope_sha256,
    _promotion_due_after_routine,
    _school_result_label,
)

__all__ = (
    "_assessment_scope_sha256",
    "_measure_debt_admission_boundary",
    "_paired_stagnation_progress",
    "_promotion_due_after_routine",
    "_school_result_label",
    "_score_parent_for_paired_s3",
    "_take_exam",
)
