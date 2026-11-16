"""Learning experiment implementation extracted from the compatibility facade."""
from __future__ import annotations

from .retention_policy import retention_reason as _retention_reason, scaled_loss_allowance

from .source_selection import (
    COMPOSITION_DEPTH_POLICY_THRESHOLD, _choose_binary_rows, _choose_typed_rows,
    _fresh_support_rows,
)

from bilqis_mlx.errors import ErrorBus, SCHOOL

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import random
from typing import Mapping

import numpy as np
import bilqis_mlx.mature_debt as _mature_debt
import bilqis_mlx.learning.plasticity_escape as _plasticity_escape
import bilqis_mlx.learning.teacher_breeding as _teacher_breeding
from bilqis_mlx.learning.teacher_feedback import (
    LearningExperimentError, WeaknessTargetError, WeaknessTargetRequest,
    select_weakness_targets,
)
from bilqis_mlx.learning.teacher_strategy_population import BAMF_SUCCESSOR_SELECTION
from bilqis_mlx.learning.teacher_strategy_population import UCB_EXPLORATION_WEIGHT as TEACHER_UCB_EXPLORATION_WEIGHT, SELECTION_POLICY as TEACHER_SELECTION_POLICY, active_effective_strategy_keys as _active_effective_strategy_keys, checkpoint_active_effective_strategy_keys as _checkpoint_active_effective_strategies, effective_context_scope as _effective_context_scope_impl, effective_policy_key as _effective_policy_key_impl, pick_existing_active as _pick_existing_active, record_checkpoint_policy_outcome as _record_checkpoint_policy_outcome, sibling_cooldown_penalty as _sibling_cooldown_penalty
from bilqis_mlx.learning.teacher_realized_action import bind_record as _bind_realized_action_record, describe as realized_teacher_action, record_outcome as _record_realized_action_outcome

VERSION = "bilqis.mlx.causal-teacher-experiment/v1"
MAX_FAILURE_ARCHETYPES = 24
INTERFERENCE_REJECTIONS_FOR_HALF_BUDGET = 2
INTERFERENCE_REJECTIONS_FOR_QUARTER_BUDGET = 4
REJECTION_PRESSURE_CONTEXTUAL_START = 2
BESPOKE_EXPLORATION_START = 4


@dataclass(frozen=True)
class Settings:
    """Provisional, operator-selected trial budgets, not graduation criteria."""
    probe_each: int = 6
    mature_max_loss: int = 1
    introduction_extra_loss: int = 2
    protected_cap_limit: int = 8

    def __post_init__(self):
        if (type(self.probe_each) is not int or not 2 <= self.probe_each <= 48
                or type(self.mature_max_loss) is not int or
                not 0 <= self.mature_max_loss < self.probe_each or
                type(self.introduction_extra_loss) is not int or
                not 0 <= self.introduction_extra_loss <= self.probe_each or
                type(self.protected_cap_limit) is not int or
                not 1 <= self.protected_cap_limit <= 128):
            raise ValueError("LEARNING_EXPERIMENT_INVALID_SETTINGS")


def sampled_protection(admitted: set[str], current: str,
                       scores: dict, *, cap_limit: int, rotation: int) -> set[str]:
    """Bound the costly probe executions, preserving grade coverage over time.

    Poorly scoring capabilities are preferred, while rotation occasionally
    samples seemingly safe older capabilities. Scheduled full school exams
    remain the independent cumulative authority.
    """
    if current not in admitted or cap_limit < 1 or rotation < 0:
        raise ValueError("LEARNING_EXPERIMENT_PROBE_SELECTION_INVALID")
    eligible = admitted - {current}
    if len(eligible) <= cap_limit:
        return eligible
    groups = {}
    for cap in sorted(eligible):
        groups.setdefault(cap.partition(".")[0], []).append(cap)

    def weakness(cap):
        value = scores.get(cap) or {}
        correct, total = value.get("correct"), value.get("total")
        return (correct/total if type(correct) is int and type(total) is int
                and 0 <= correct <= total and total else 1.)

    result = set()
    # Coverage slot for each represented grade; oldest severe failures and a
    # moving rotation are both considered, without permanent whitelist tests.
    grade_names = sorted(groups)
    if len(grade_names) > cap_limit:
        shift = rotation % len(grade_names)
        grade_names = (grade_names[shift:] + grade_names[:shift])[:cap_limit]
    for grade in grade_names:
        caps = groups[grade]
        ordered = sorted(caps, key=lambda cap:(weakness(cap), cap))
        chosen = ordered[(rotation // max(1,cap_limit)) % len(ordered)]
        result.add(chosen)
        if len(result) >= cap_limit:
            return result
    # One rotational slot explicitly combats stale, apparently safe skills.
    rotated = sorted(eligible-result)
    if rotated and len(result) < cap_limit:
        result.add(rotated[rotation % len(rotated)])
    rest = sorted(eligible-result, key=lambda cap:(weakness(cap), cap))
    return result | set(rest[:max(0,cap_limit-len(result))])


def whole_grade_protection(admitted: set[str], current: str,
                           scores: dict, *, cap_limit: int, rotation: int) -> set[str]:
    """Always measure every admitted peer in the target grade.

    Same-grade completeness is mandatory, not constrained by the unrelated
    budget for optional rotating cross-grade sentinels. Keep two sentinel
    slots when other grades exist, even for a large target grade, so the work
    scales with the *target grade*, not the cumulative school.
    """
    own = {cap for cap in admitted if cap.partition(".")[0] ==
           current.partition(".")[0]}
    peers, other = own - {current}, admitted - own
    if current not in own or cap_limit < 1:
        raise ValueError("LEARNING_EXPERIMENT_FULL_GRADE_PROBE_SCOPE_INVALID")
    remaining = max(min(2, cap_limit), cap_limit-len(peers)) if other else 0
    sampled = (sampled_protection(other | {current}, current, scores,
                                 cap_limit=remaining, rotation=rotation)
               if remaining and other else set())
    return peers | sampled


def missing_grade_capabilities(grade_capabilities, scored_capabilities):
    """Return only unscored peers for a single candidate's qualification.

    The caller owns checkpoint and source-cohort provenance. A different
    checkpoint's scores must never be passed in as if they were cached.
    """
    grade = tuple(grade_capabilities)
    if (not grade or len(grade) != len(set(grade)) or
            any(not isinstance(cap, str) or not cap for cap in grade) or
            not isinstance(scored_capabilities, dict)):
        raise ValueError("LEARNING_EXPERIMENT_INVALID_GRADE_COMPLETION_SCOPE")
    return tuple(cap for cap in grade if cap not in scored_capabilities)


def paired_outcomes(rows, parent_predictions: Mapping[str, str],
                    candidate_predictions: Mapping[str, str]) -> dict:
    """Scores only paired, stable source-gold rows, per capability."""
    if not rows or any(
            r.get("id") not in parent_predictions or
            r.get("id") not in candidate_predictions or
            not r.get("capability") or not isinstance(r.get("gold"), str)
            for r in rows):
        raise ValueError("LEARNING_EXPERIMENT_INCOMPLETE_PAIRED_COHORT")
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("LEARNING_EXPERIMENT_DUPLICATE_ROW")
    counts: dict[str, dict] = {}
    for row in rows:
        entry = counts.setdefault(row["capability"], {"before": 0, "after": 0, "total": 0})
        entry["total"] += 1
        entry["before"] += int(parent_predictions[row["id"]] == row["gold"])
        entry["after"] += int(candidate_predictions[row["id"]] == row["gold"])
    return counts


def _prototype_similarity(delta: dict[str, float], prototypes: list[dict]) -> float | None:
    """Diagnostic cosine against measured protected-loss patterns, not veto."""
    highest = None
    for prototype in prototypes:
        old = prototype.get("delta", {})
        common = set(delta) & set(old)
        if not common:
            continue
        numerator = sum(delta[name] * old[name] for name in common)
        aa = sum(delta[name] ** 2 for name in common)
        bb = sum(old[name] ** 2 for name in common)
        if aa and bb:
            similarity = numerator / math.sqrt(aa * bb)
            highest = similarity if highest is None else max(highest, similarity)
    return None if highest is None else round(highest, 6)


def _same_grade_retention_evidence(paired, active_capability,
                                   same_grade_capabilities, fixed_grade_replay):
    grade = active_capability.partition(".")[0]
    required = (set(same_grade_capabilities) if same_grade_capabilities is not None
                else {cap for cap in paired if cap.partition(".")[0] == grade})
    if (not required or active_capability not in required or
            any(cap.partition(".")[0] != grade for cap in required) or
            not required <= set(paired) or
            (same_grade_capabilities is not None and
             len(set(same_grade_capabilities)) != len(same_grade_capabilities))):
        raise ValueError("LEARNING_EXPERIMENT_INCOMPLETE_SAME_GRADE_PROBE")
    net = sum(paired[cap]["after"] - paired[cap]["before"] for cap in required)
    fixed = fixed_grade_replay or {
        "status": "NOT_MEASURED",
        "reason": "NO_COMPARABLE_COMPLETE_GRADE_EXAM",
    }
    if fixed.get("status") == "MEASURED":
        before_grade, after_grade, total = (
            fixed.get(name) for name in ("before", "after", "total"))
        sha = fixed.get("cohort_sha256")
        if (fixed.get("grade") != grade or
                any(type(n) is not int for n in
                    (before_grade, after_grade, total)) or
                not 0 < total or not 0 <= before_grade <= total or
                not 0 <= after_grade <= total or
                not isinstance(sha, str) or len(sha) != 64 or
                any(c not in "0123456789abcdef" for c in sha)):
            raise ValueError("LEARNING_EXPERIMENT_INVALID_FIXED_GRADE_COHORT")
        fixed = {**fixed, "net_correct_delta": after_grade-before_grade}
    elif fixed.get("status") != "NOT_MEASURED":
        raise ValueError("LEARNING_EXPERIMENT_INVALID_FIXED_GRADE_STATUS")
    return required, net, fixed


def _paired_screen(paired, protected, active_capability):
    if protected - set(paired):
        raise ValueError("LEARNING_EXPERIMENT_PROTECTED_CAPABILITY_NOT_MEASURED")
    deltas, regressions = {}, {}
    for cap, counts in sorted(paired.items()):
        before, after, total = (counts[k] for k in ("before", "after", "total"))
        if (any(type(v) is not int for v in (before, after, total)) or
                not 0 < total or not 0 <= before <= total or
                not 0 <= after <= total):
            raise ValueError("LEARNING_EXPERIMENT_INVALID_PAIRED_SCORE")
        deltas[cap] = round((after-before)/total, 7)
        if cap in protected and cap != active_capability:
            regressions[cap] = max(0, before-after)
    return deltas, regressions


def _fixed_frontier_retention_evidence(value, protected_frontier_grade):
    frontier = value or {
        "status": "NOT_MEASURED",
        "reason": "NO_FIXED_WHOLE_SCHOOL_FRONTIER",
    }
    status = frontier.get("status")
    if status not in ("MEASURED", "NOT_MEASURED"):
        raise ValueError("LEARNING_EXPERIMENT_INVALID_FIXED_FRONTIER_STATUS")
    if status == "NOT_MEASURED":
        return frontier, False, False, None
    before, after, total = (
        frontier.get("before_correct"), frontier.get("after_correct"),
        frontier.get("rows"))
    regressions = frontier.get("regressions")
    repaired = frontier.get("repaired")
    if (any(type(number) is not int for number in (before, after, total)) or
            not 0 < total or not 0 <= before <= total or
            not 0 <= after <= total or
            not isinstance(regressions, list) or
            not isinstance(repaired, list)):
        raise ValueError("LEARNING_EXPERIMENT_INVALID_FIXED_FRONTIER_SCORE")
    active_grade_regression = False
    if protected_frontier_grade is not None:
        grades = frontier.get("grades")
        invalid = not isinstance(grades, dict)
        grade = None if invalid else grades.get(protected_frontier_grade)
        if grade is not None:
            invalid = (
                not isinstance(grade, dict) or
                any(type(grade.get(name)) is not int
                    for name in ("before", "after", "total")) or
                not 0 < grade["total"] or
                not 0 <= grade["before"] <= grade["total"] or
                not 0 <= grade["after"] <= grade["total"])
        if invalid:
            raise ValueError(
                "LEARNING_EXPERIMENT_INVALID_ACTIVE_GRADE_FRONTIER")
        if grade is not None:
            active_grade_regression = grade["after"] < grade["before"]
    return frontier, after < before, active_grade_regression, after - before
