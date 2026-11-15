"""Final retention, teacher, checkpoint, and event persistence for an exam."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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


from .persistence import finalize_exam
