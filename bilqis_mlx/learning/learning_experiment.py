"""Compatibility facade for candidate retention and contextual teacher evidence."""
from __future__ import annotations

from ._learning_experiment_retention import (
    VERSION, Settings, sampled_protection, whole_grade_protection,
    missing_grade_capabilities, paired_outcomes,
)
from ._learning_experiment_decision import (
    decide, _channel, _diagnostic_context, _effective_policy_key,
)
from ._learning_experiment_policy import candidate_step_budget, contextual_pick
from ._learning_experiment_feedback import (
    observe_context, selection_credit, fork_student, commit_trial,
    earlier_grade_capabilities,
)
from ._learning_experiment_lessons import reserve_weakness_targets, select_source_lesson
from .teacher_realized_action import describe as realized_teacher_action
from .teacher_strategy_population import active_effective_strategy_keys as _active_effective_strategy_keys

__all__ = [
    "VERSION", "Settings", "sampled_protection", "whole_grade_protection",
    "missing_grade_capabilities", "paired_outcomes", "decide",
    "candidate_step_budget", "contextual_pick", "observe_context",
    "selection_credit", "fork_student", "commit_trial",
    "earlier_grade_capabilities", "reserve_weakness_targets",
    "select_source_lesson", "realized_teacher_action",
]
