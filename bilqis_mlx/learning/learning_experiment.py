"""Default-on parent-relative candidate safety and contextual teacher evidence.

Neither historical teacher statistics nor frozen qualification receipts are
rewritten. These experimentally learned outcomes use matched, source-oracled
parent/challenger questions; an approximate failure signature is never gold.
"""
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


def _protected_diagnostics(paired, protected, active_capability, phase,
                           settings, mature_grades):
    deltas, regressions = _paired_screen(
        paired, protected, active_capability)
    introduction = phase == "MAIN"
    allowed = settings.mature_max_loss + (
        settings.introduction_extra_loss if introduction else 0)
    reference_losses = {
        cap: (settings.mature_max_loss
              if cap.partition(".")[0] in mature_grades else allowed)
        for cap in sorted(regressions)
    }
    # Loss budgets are rates expressed against the configured reference probe,
    # not absolute answer counts. Preserve the original 1/6 (or MAIN 3/6)
    # risk appetite when a capability is measured on a larger paired panel.
    tolerances = {
        cap: scaled_loss_allowance(
            paired[cap]["total"], reference_losses[cap], settings.probe_each)
        for cap in sorted(regressions)
    }
    exceeded = {
        cap: loss for cap, loss in regressions.items()
        if loss > tolerances[cap]
    }
    protected_net_gain = sum(
        paired[cap]["after"] - paired[cap]["before"]
        for cap in protected if cap != active_capability)
    return (deltas, regressions, allowed, tolerances, exceeded,
            protected_net_gain)


def _validate_source_cohort_sha256(value):
    if (value is not None and
            (len(value) != 64 or
             any(char not in "0123456789abcdef" for char in value))):
        raise ValueError("LEARNING_EXPERIMENT_COHORT_DIGEST_INVALID")
def decide(paired: dict, *, active_capability: str, phase: str,
           protected: set[str], settings: Settings,
           mature_grades: frozenset[str] = frozenset(), mature_grade_debt: dict[str, int] | None = None,
           negative_prototypes: list[dict] | None = None,
           source_cohort_sha256: str | None = None,
           fragile_replay: dict | None = None,
           same_grade_capabilities: tuple[str, ...] | None = None,
           fixed_grade_replay: dict | None = None,
           fixed_frontier_replay: dict | None = None,
           protected_frontier_grade: str | None = None,
           plasticity_escape: dict | None = None) -> dict:
    """Retain only target gains that do not sacrifice their own grade.

    The parent/student and native AdamW remain untouched on rejection.
    A MAIN scheduler pass is not equivalent to introduction of a new skill.
    """
    if active_capability not in paired or not phase:
        raise ValueError("LEARNING_EXPERIMENT_MISSING_ACTIVE_CAPABILITY")
    (deltas, regressions, allowed, tolerances, exceeded,
     protected_net_gain) = _protected_diagnostics(
         paired, protected, active_capability, phase, settings,
         mature_grades)
    active = paired[active_capability]
    active_gain = active["after"] - active["before"]
    required, same_grade_net_gain, fixed = _same_grade_retention_evidence(
        paired, active_capability, same_grade_capabilities, fixed_grade_replay)
    # Local lesson training reward is not evidence of improved capability.
    # The same, source-oracled parent/challenger probe must improve strictly.
    no_target_gain = active_gain <= 0
    frontier, whole_school_regression, active_grade_regression, frontier_net = (
        _fixed_frontier_retention_evidence(fixed_frontier_replay, protected_frontier_grade))
    frontier_measured = frontier.get("status") == "MEASURED"
    protected_frontier_delta = None
    if frontier_measured and protected_frontier_grade is not None:
        grades = frontier.get("grades")
        grade = grades.get(protected_frontier_grade) if isinstance(grades, dict) else None
        if isinstance(grade, dict):
            protected_frontier_delta = grade["after"] - grade["before"]
    fixed_grade_regression = (fixed.get("status") == "MEASURED" and fixed["net_correct_delta"] < 0)
    fragile_losses = bool(fragile_replay and fragile_replay.get("regressions"))
    if fragile_replay is not None and fragile_replay.get("status") not in ("MEASURED", "NOT_MEASURED"):
        raise ValueError("LEARNING_EXPERIMENT_INVALID_FRAGILE_REPLAY")
    fingerprint = json.dumps(paired, sort_keys=True, separators=(",", ":"))
    _validate_source_cohort_sha256(source_cohort_sha256)
    reason = _retention_reason(
        no_target_gain=no_target_gain, same_grade_net_gain=same_grade_net_gain,
        fixed_grade_regression=fixed_grade_regression, active_grade_regression=active_grade_regression,
        whole_school_regression=whole_school_regression, frontier_measured=frontier_measured,
        fragile_losses=fragile_losses, exceeded=exceeded)
    reason, plasticity = _plasticity_escape.maybe_relax(
        reason, state=plasticity_escape, no_target_gain=no_target_gain,
        paired=paired, same_grade_capabilities=required,
        fixed_grade_scores=(fixed.get("capabilities")
                            if fixed.get("status") == "MEASURED" else None),
        frontier_scores=(frontier.get("capabilities")
                         if frontier.get("status") == "MEASURED" else None),
        protected_frontier_grade=protected_frontier_grade,
        fixed_grade_net_gain=(fixed.get("net_correct_delta")
                              if fixed.get("status") == "MEASURED" else None),
        active_frontier_grade_net_gain=protected_frontier_delta,
        whole_school_net_gain=frontier_net if frontier_measured else None,
        fragile_losses=fragile_losses)
    projected_mature_debt, reason = _mature_debt.retention_reason(reason, frontier, mature_grades, mature_grade_debt or {})
    return {
        "version": VERSION,
        "decision": ("REJECT" if reason != "PAIRED_SCREEN_WITHIN_BUDGET"
                     else "PROVISIONAL"),
        "reason": reason,
        "fragile_replay": fragile_replay,
        "fixed_grade_replay": fixed,
        "fixed_frontier_replay": frontier,
        "fixed_whole_school_net_correct_delta": frontier_net,
        "protected_frontier_grade": protected_frontier_grade,
        "protected_frontier_grade_net_correct_delta": protected_frontier_delta,
        "phase": phase, "active_capability": active_capability,
        "active_probe_before": active["before"],
        "active_probe_after": active["after"],
        "active_probe_total": active["total"],
        "protected_capabilities": sorted(protected),
        "max_tolerated_wrong_answer_delta": allowed,
        "protected_tolerances": tolerances,
        "mature_protected_capabilities": sorted(cap for cap in regressions
                                                 if cap.partition(".")[0] in mature_grades),
        "projected_mature_grade_debt": projected_mature_debt, "mature_grade_debt_hard_limit": _mature_debt.HARD_LIMIT,
        "plasticity_escape": plasticity,
        "exceeded": exceeded,
        "worst_protected_loss": max(regressions.values(), default=0),
        "local_correct_delta": active_gain,
        "same_grade_net_correct_delta": same_grade_net_gain,
        "same_grade_probed_capabilities": sorted(required),
        "protected_net_correct_delta": protected_net_gain,
        "paired_scores_sha256": hashlib.sha256(fingerprint.encode()).hexdigest(),
        "source_cohort_sha256": source_cohort_sha256,
        "deltas": deltas,
        "discordance_similarity": _prototype_similarity(deltas, negative_prototypes or []),
        "exact_complete_exam_qualification": False,
    }


def _channel(teacher: dict) -> dict:
    channel = teacher.setdefault("causal_experiment", {
        "version": VERSION, "contexts": {}, "negative_archetypes": [], "events": 0})
    if teacher.get("selection_contract") == BAMF_SUCCESSOR_SELECTION:
        channel["selection_contract"] = BAMF_SUCCESSOR_SELECTION
    if channel.get("version") != VERSION:
        raise ValueError("LEARNING_EXPERIMENT_CHANNEL_VERSION_DRIFT")
    return channel


def _stagnation_key(capability: str, curriculum_scope: str) -> str:
    return capability+"|"+curriculum_scope


def _shared_no_gain_streak(channel: dict, capability: str,
                           curriculum_scope: str, policy_key: str) -> int:
    return int(channel.get("stagnation", {})
                      .get(_stagnation_key(capability, curriculum_scope), {})
                      .get(policy_key, {})
                      .get("no_target_gain_streak", 0))


def _shared_stagnation_record(channel: dict, capability: str,
                              curriculum_scope: str, policy_key: str) -> dict:
    scope = channel.setdefault("stagnation", {}).setdefault(
        _stagnation_key(capability, curriculum_scope), {})
    return scope.setdefault(policy_key, {"no_target_gain_streak": 0})


def _capability_stagnation(channel: dict, capability: str,
                           curriculum_scope: str) -> dict:
    return channel.get("capability_stagnation", {}).get(
        _stagnation_key(capability, curriculum_scope), {})


def _capability_stagnation_record(channel: dict, capability: str,
                                  curriculum_scope: str) -> dict:
    record = channel.setdefault("capability_stagnation", {}).setdefault(
        _stagnation_key(capability, curriculum_scope), {
            "rejection_streak": 0,
            "consecutive_interference_rejections": 0,
            "no_target_gain_streak": 0,
            "attempts_since_retained": 0,
            "total_rejections": 0,
            "total_retained": 0,
            "current_rejection_reasons": {},
        })
    record.setdefault("current_rejection_reasons", {})
    record.setdefault("consecutive_interference_rejections", 0)
    return record


def _inherited_exploration(teacher: dict, grade: str, policy_key: str) -> float:
    local = {} if teacher.get("selection_contract") == BAMF_SUCCESSOR_SELECTION else teacher.get("grade_stats", {}).get(str(grade), {})
    info = local.get(policy_key) or teacher.get("global_stats", {}).get(policy_key)
    if not info or not info.get("trials"):
        return 0.
    total = int(teacher.get("events", 0)) + 1
    return TEACHER_UCB_EXPLORATION_WEIGHT * math.sqrt(
        math.log(total+2)/(1+info["trials"]))


def _effective_policy_key(policy: dict) -> str:
    return _effective_policy_key_impl(policy)


def _effective_context_scope(teacher: dict, scope: dict) -> dict:
    return _effective_context_scope_impl(teacher, scope)


def _diagnostic_context(channel: dict, capability: str, curriculum_scope: str,
                        diagnostics: dict | None) -> tuple[str, dict]:
    diagnostics = diagnostics or {}
    warnings = diagnostics.get("warnings", ())
    normalized_warnings = sorted({
        str(getattr(value, "value", value)) for value in warnings
    })
    stagnation = _capability_stagnation(
        channel, capability, curriculum_scope)
    reasons = stagnation.get("current_rejection_reasons", {})
    if not isinstance(reasons, dict) or any(
            not isinstance(key, str) or type(value) is not int or value < 0
            for key, value in reasons.items()):
        raise ValueError(LearningExperimentError.DIAGNOSTIC_REASON_DRIFT.value)
    dominant = (
        max(reasons, key=lambda reason: (reasons[reason], reason))
        if reasons and int(stagnation.get("rejection_streak", 0)) > 0
        else None
    )
    payload = {
        "warnings": normalized_warnings,
        "unresolved_misses": bool(diagnostics.get("unresolved_miss_count", 0)),
        "champion_candidates": bool(
            diagnostics.get("champion_candidate_count", 0)),
        "rejection_pressure": int(stagnation.get("rejection_streak", 0)) > 0,
        "dominant_rejection_reason": dominant,
    }
    if (channel.get("selection_contract") == BAMF_SUCCESSOR_SELECTION
            and "salience_evidence" in diagnostics):
        from .atlas_salience import salience_priority_features
        payload["salience"] = salience_priority_features(
            diagnostics["salience_evidence"], capability, curriculum_scope,
            diagnostics.get("teacher_epoch_digest"))
    identity = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    known = channel.setdefault("diagnostic_contexts", {})
    previous = known.get(identity)
    if previous is not None and previous != payload:
        raise ValueError(LearningExperimentError.DIAGNOSTIC_CONTEXT_COLLISION.value)
    known[identity] = payload
    return identity, payload


def _diagnostic_effective_scope(teacher: dict, scope: dict,
                                diagnostic_key: str) -> dict:
    groups = {}
    strategies = teacher.get("strategies", {})
    for policy_key, record in scope.items():
        policy = strategies.get(policy_key)
        if policy is None:
            raise ValueError(LearningExperimentError.STRATEGY_ID_DRIFT.value)
        diagnostic = record.get("diagnostic_stats", {}).get(diagnostic_key)
        if not isinstance(diagnostic, dict) or not diagnostic.get("trials"):
            continue
        effective_key = _effective_policy_key(policy)
        group = groups.setdefault(effective_key, {
            "trials": 0,
            "reward_sum": 0.,
            "unsafe": 0,
            "retained": 0,
            "no_target_gain_streak": 0,
            "members": [],
        })
        group["trials"] += int(diagnostic.get("trials", 0))
        group["reward_sum"] += float(diagnostic.get("reward_sum", 0.))
        group["unsafe"] += int(diagnostic.get("unsafe", 0))
        group["retained"] += int(diagnostic.get("retained", 0))
        group["members"].append(policy_key)
    return groups


def _learning_rate_prior_scope(teacher: dict, channel: dict, capability: str,
                               curriculum_scope: str,
                               current_context_key: str) -> dict:
    """Pool same-capability reward evidence by LR across sibling phases."""
    priors = {}
    strategies = teacher.get("strategies", {})
    for context_key, scope in channel.get("contexts", {}).items():
        if context_key == current_context_key:
            continue
        try:
            context_capability, _phase, context_scope = context_key.split("|", 2)
        except ValueError:
            raise ValueError(LearningExperimentError.CONTEXT_ID_DRIFT.value)
        if (context_capability != capability or
                context_scope != curriculum_scope or
                not isinstance(scope, dict)):
            continue
        for policy_key, record in scope.items():
            policy = strategies.get(policy_key)
            if policy is None:
                raise ValueError(LearningExperimentError.STRATEGY_ID_DRIFT.value)
            lr = policy.get("lr")
            if not isinstance(lr, (int, float)) or not math.isfinite(lr) or lr <= 0:
                raise ValueError(LearningExperimentError.POLICY_LR_INVALID.value)
            prior = priors.setdefault(float(lr), {
                "trials": 0, "reward_sum": 0.,
            })
            prior["trials"] += int(record.get("trials", 0))
            prior["reward_sum"] += float(record.get("reward_sum", 0.))
    return priors


def candidate_step_budget(default_steps: int, teacher: dict, capability: str,
                          *, curriculum_scope: str = "") -> int:
    """Shrink disposable candidate horizon under sustained retention failure.

    The configured horizon remains authoritative in the healthy regime.
    Candidate attempts and optimizer steps are different units: a rejected
    16-step candidate is one failed candidate, not one sixteenth of a failure.
    After two consecutive interference-rejected candidates, halve the next
    disposable trial. After four, quarter it. A no-target-gain outcome breaks
    the interference streak, while a retained candidate resets all current
    rejection pressure through the existing capability-stagnation owner.
    """
    if type(default_steps) is not int or default_steps < 1:
        raise ValueError(LearningExperimentError.CANDIDATE_STEPS_INVALID.value)
    channel = teacher.get("causal_experiment")
    if not isinstance(channel, dict):
        return default_steps
    stagnation = _capability_stagnation(
        channel, capability, curriculum_scope)
    reasons = stagnation.get("current_rejection_reasons", {})
    interference_rejections = stagnation.get(
        "consecutive_interference_rejections", 0)
    if (not isinstance(reasons, dict) or any(
            not isinstance(reason, str) or type(count) is not int or count < 0
            for reason, count in reasons.items()) or
            type(interference_rejections) is not int or
            interference_rejections < 0):
        raise ValueError(LearningExperimentError.CANDIDATE_STAGNATION_INVALID.value)
    half = max(1, default_steps // 2)
    quarter = max(1, default_steps // 4)
    if interference_rejections >= INTERFERENCE_REJECTIONS_FOR_QUARTER_BUDGET:
        return quarter
    if interference_rejections >= INTERFERENCE_REJECTIONS_FOR_HALF_BUDGET:
        return half
    return default_steps


def contextual_pick(engine, teacher: dict, capability: str, phase: str, rng,
                    *, curriculum_scope: str = "", diagnostics: dict | None = None,
                    return_metadata: bool = False,
                    student_checkpoint_sha256: str | None = None,
                    total_capabilities: int | None = None,
                    plasticity_active: bool = False):
    """Preserve the inherited bandit's exploration; prefer proven safe context."""
    grade = capability.partition(".")[0]
    channel = _channel(teacher)
    diagnostic_key, _diagnostic_payload = _diagnostic_context(
        channel, capability, curriculum_scope, diagnostics)

    context_key = capability+"|"+phase+"|"+curriculum_scope
    scope = channel["contexts"].get(context_key, {})
    active_effective, inventory, retired_effective = _teacher_breeding.selection_population(
        teacher, grade=grade, capability=capability, curriculum_scope=curriculum_scope,
        scope=scope, channel=channel, context_key=context_key,
        student_checkpoint_sha256=student_checkpoint_sha256, total_capabilities=total_capabilities)
    active_set = set(active_effective)
    capability_stagnation = _capability_stagnation(channel, capability, curriculum_scope)
    rejection_pressure = int(capability_stagnation.get("rejection_streak", 0))
    def result(key, policy, *, diagnostic_context_consumed=False, selection_reason="INHERITED_FALLBACK", selection_detail=None):
        if return_metadata:
            return key, policy, _teacher_breeding.selection_metadata(
                teacher, channel=channel, inventory=inventory,
                active_effective=active_effective, checkpoint_retired=retired_effective,
                total_capabilities=total_capabilities,
                diagnostic_context_consumed=diagnostic_context_consumed,
                diagnostic_context_key=diagnostic_key,
                selection_reason=selection_reason, selection_policy=TEACHER_SELECTION_POLICY,
                selection_detail=selection_detail)
        return key, policy
    if plasticity_active and scope:
        retryable = []
        for policy_key, record in scope.items():
            policy = teacher.get("strategies", {}).get(policy_key)
            if policy is None or not isinstance(record, dict):
                continue
            if _effective_policy_key(policy) not in active_set:
                continue
            if (int(record.get("unsafe", 0)) < 1 or
                    int(record.get("retained", 0)) > 0 or
                    int(record.get("no_target_gain_streak", 0)) > 0 or
                    bool(record.get("last_plasticity_active", False))):
                continue
            trials = int(record.get("trials", 0))
            if trials < 1:
                continue
            retryable.append((
                float(record.get("latest", float("-inf"))),
                float(record.get("reward_sum", 0.)) / trials,
                -int(record.get("unsafe", 0)), policy_key,
            ))
        if retryable:
            _latest, _mean, _unsafe, policy_key = max(retryable)
            return result(policy_key, teacher["strategies"][policy_key],
                          selection_reason="PLASTICITY_RETRY")
    effective_scope = {
        key: record
        for key, record in _effective_context_scope(teacher, scope).items()
        if key in active_set
    } if scope else {}
    active_retained_context = any(
        int(record.get("retained", 0)) > 0
        for record in effective_scope.values())
    if (rejection_pressure >= BESPOKE_EXPLORATION_START and
            not active_retained_context):
        challenger = _teacher_breeding.pressure_challenger(
            engine, teacher, rng, capability=capability, phase=phase,
            curriculum_scope=curriculum_scope, diagnostic_key=diagnostic_key,
            total_capabilities=total_capabilities or 1)
        if challenger is not None:
            return result(challenger[0], challenger[1],
                          selection_reason=challenger[2], selection_detail=challenger[3])
    if not scope:
        original_key, original_policy = _pick_existing_active(
            engine, teacher, grade, rng, active_effective, inventory)
        return result(original_key, original_policy, selection_reason="INHERITED_NO_CONTEXT")
    if not effective_scope:
        original_key, original_policy = _pick_existing_active(
            engine, teacher, grade, rng, active_effective, inventory)
        return result(
            original_key, original_policy,
            selection_reason="FRESH_ACTIVE_CHALLENGER")
    diagnostic_scope = _diagnostic_effective_scope(
        teacher, scope, diagnostic_key)
    diagnostic_scope = {
        key: record for key, record in diagnostic_scope.items()
        if key in active_set
    }
    usable_diagnostic = {
        key: record for key, record in diagnostic_scope.items()
        if record.get("retained", 0) > 0
    }
    selection_scope = usable_diagnostic or effective_scope
    diagnostic_consumed = bool(usable_diagnostic)
    trials = sum(v["trials"] for v in effective_scope.values())
    learning_rate_priors = (_learning_rate_prior_scope(
        teacher, channel, capability, curriculum_scope, context_key)
        if rejection_pressure > 0 else {})
    # Priors stay owned by the inherited bandit. Context decides only when its
    # observed safety preference is demonstrably better than the current pick.
    def score_effective(key):
        record = selection_scope.get(key)
        if not record:
            return float("-inf")
        mean = record["reward_sum"] / record["trials"]
        if learning_rate_priors and not diagnostic_consumed:
            member_lrs = {
                float(teacher["strategies"][member]["lr"])
                for member in record["members"]
            }
            if len(member_lrs) != 1:
                raise ValueError(LearningExperimentError.EFFECTIVE_POLICY_LR_DRIFT.value)
            prior = learning_rate_priors.get(next(iter(member_lrs)))
            if prior and prior["trials"]:
                mean = (
                    record["reward_sum"] + prior["reward_sum"]
                ) / (
                    record["trials"] + prior["trials"]
                )
        exploration = (TEACHER_UCB_EXPLORATION_WEIGHT *
                       math.sqrt(math.log(trials+2)/(record["trials"]+1)))
        stagnation = record["no_target_gain_streak"]
        return mean + exploration/(1+stagnation+rejection_pressure) - _sibling_cooldown_penalty(channel, capability, curriculum_scope, key)
    retained_scope = {
        key: record for key, record in selection_scope.items()
        if record.get("retained", 0) > 0
    }
    best_effective = max(retained_scope or selection_scope, key=score_effective)
    best_record = selection_scope[best_effective]

    def member_rank(key):
        record = scope[key]
        mean = record["reward_sum"] / record["trials"]
        return (record.get("retained", 0), mean, record["trials"], key)

    best = max(best_record["members"], key=member_rank)
    proven_retained = best_record.get("retained", 0) > 0
    pressure_exploit = rejection_pressure >= REJECTION_PRESSURE_CONTEXTUAL_START
    if diagnostic_consumed:
        return result(
            best, teacher["strategies"][best],
            diagnostic_context_consumed=diagnostic_consumed,
            selection_reason="DIAGNOSTIC_OR_PRESSURE_CONTEXT")
    if proven_retained:
        return result(
            best, teacher["strategies"][best],
            selection_reason="PROVEN_RETAINED_CONTEXT")
    if pressure_exploit:
        return result(
            best, teacher["strategies"][best],
            selection_reason="DIAGNOSTIC_OR_PRESSURE_CONTEXT")

    # Healthy operation and a bounded pressure cadence still consult the
    # inherited bandit. Avoid calling it on pressure-exploitation visits:
    # pick() may mutate the strategy inventory, and discarded mutations would
    # otherwise consume the finite 512-strategy budget without being tried.
    original_key, original_policy = _pick_existing_active(
        engine, teacher, grade, rng, active_effective, inventory)
    original_effective = _effective_policy_key(original_policy)
    if original_effective == best_effective:
        return result(
            original_key, original_policy,
            diagnostic_context_consumed=diagnostic_consumed, selection_reason="INHERITED_MATCHES_CONTEXT")
    # Require evidence, but keep inherited exploration alive. The base pick
    # still gets a chance whenever it lacks direct context observations.
    if (proven_retained and rejection_pressure > 0 and
            (original_effective not in effective_scope or
             score_effective(best_effective) >
             score_effective(original_effective))):
        return result(best, teacher["strategies"][best], selection_reason="PROVEN_RETAINED_CONTEXT")
    if ((best_record["trials"] >= 2 or proven_retained) and
            original_effective in effective_scope and
            score_effective(best_effective) > score_effective(original_effective)):
        return result(best, teacher["strategies"][best], selection_reason="CONTEXT_UCB_PREFERENCE")
    return result(original_key, original_policy)


def _stagnation_feedback(teacher: dict, capability: str, policy_key: str,
                         decision: dict, reward: float, record: dict,
                         shared_stagnation: dict) -> tuple[float, float]:
    no_target_gain = decision.get("reason") == "NO_MEASURABLE_TARGET_GAIN"
    inherited_exploration = _inherited_exploration(
        teacher, capability.partition(".")[0], policy_key)
    selection_reward = reward
    repayment = 0.-inherited_exploration
    if no_target_gain and repayment < selection_reward:
        selection_reward = repayment
    if no_target_gain:
        record["no_target_gain_streak"] += 1
        shared_stagnation["no_target_gain_streak"] += 1
    else:
        record["no_target_gain_streak"] = 0
        shared_stagnation["no_target_gain_streak"] = 0
    return inherited_exploration, selection_reward


def observe_context(teacher: dict, *, capability: str, phase: str,
                    policy_key: str, decision: dict, local_gain: float,
                    curriculum_scope: str = "",
                    diagnostics: dict | None = None,
                    realized_action: dict | None = None,
                    student_checkpoint_sha256: str | None = None) -> dict:
    """Source-paired trial outcome; never rewrite historical UCB rewards."""
    if (policy_key not in teacher.get("strategies", {}) or
            not math.isfinite(local_gain) or
            decision.get("version") != VERSION or
            decision.get("active_capability") != capability or
            decision.get("phase") != phase):
        raise ValueError("LEARNING_EXPERIMENT_INVALID_CAUSAL_OUTCOME")
    no_target_gain = decision.get("reason") == "NO_MEASURABLE_TARGET_GAIN"
    channel = _channel(teacher)
    diagnostic_key, _diagnostic_payload = _diagnostic_context(
        channel, capability, curriculum_scope, diagnostics)
    context_key = capability+"|"+phase+"|"+curriculum_scope
    scope = channel["contexts"].setdefault(context_key, {})
    record = scope.setdefault(policy_key, {"trials": 0, "reward_sum": 0.,
                                            "unsafe": 0, "retained": 0,
                                            "latest": None,
                                            "no_target_gain_streak": 0})
    record.setdefault("no_target_gain_streak", 0)
    record.setdefault("retained", 0)
    action_key, action_record, stagnation_key = _bind_realized_action_record(record, realized_action, policy_key)
    shared_stagnation = _shared_stagnation_record(
        channel, capability, curriculum_scope, stagnation_key)
    capability_stagnation = _capability_stagnation_record(
        channel, capability, curriculum_scope)
    # Normalized worst-case retention cost stops many small wins concealing
    # a substantial single-capability loss. Provisional experimental metric.
    relative_loss = max((max(0., -v) for k, v in decision["deltas"].items()
                         if k in decision["protected_capabilities"]), default=0.)
    # Recovery is supposed to retain earlier foundations. Penalize measured
    # interference more heavily there, while introduction can still trade
    # controlled temporary forgetting for acquisition of something new.
    reward = local_gain - relative_loss * (1 if phase == "MAIN" else 2)
    if decision["decision"] == "REJECT":
        reward = min(reward, -relative_loss, -0.05)
    if decision["decision"] == "REJECT" or decision.get("worst_protected_loss", 0) >= 1:
        pattern = {"capability": capability, "phase": phase,
                   "curriculum_scope": curriculum_scope,
                   "policy": policy_key, "delta": decision["deltas"],
                   "paired_scores_sha256": decision["paired_scores_sha256"],
                   "source_cohort_sha256": decision["source_cohort_sha256"],
                   "outcome": ("REJECTED_UPDATE" if decision["decision"] == "REJECT"
                               else "ACCEPTED_WITH_MEASURED_PROTECTED_LOSS")}
        # A provisional regression is observed interference, not proof of
        # durable harm. Keep the distinction in each functional signature.
        entries = channel["negative_archetypes"]
        if not any(item["paired_scores_sha256"] == pattern["paired_scores_sha256"] and
                   item.get("source_cohort_sha256") == pattern["source_cohort_sha256"]
                   for item in entries):
            entries.append(pattern)
            del entries[:-MAX_FAILURE_ARCHETYPES]
    if decision["decision"] == "REJECT":
        record["unsafe"] += 1
        capability_stagnation["rejection_streak"] += 1
        capability_stagnation["attempts_since_retained"] += 1
        capability_stagnation["total_rejections"] += 1
        reason = decision.get("reason")
        if not isinstance(reason, str) or not reason:
            raise ValueError(LearningExperimentError.REJECTION_REASON_INVALID.value)
        reasons = capability_stagnation["current_rejection_reasons"]
        reasons[reason] = reasons.get(reason, 0) + 1
        if reason == "NO_MEASURABLE_TARGET_GAIN":
            capability_stagnation["consecutive_interference_rejections"] = 0
        else:
            capability_stagnation["consecutive_interference_rejections"] += 1
    else:
        record["retained"] += 1
        capability_stagnation["rejection_streak"] = 0
        capability_stagnation["consecutive_interference_rejections"] = 0
        capability_stagnation["attempts_since_retained"] = 0
        capability_stagnation["total_retained"] += 1
        capability_stagnation["current_rejection_reasons"] = {}
    effective_policy = _effective_policy_key(teacher["strategies"][policy_key])
    _record_checkpoint_policy_outcome(
        channel, context_key,
        effective_policy,
        student_checkpoint_sha256,
        no_target_gain=no_target_gain,
        retained=decision["decision"] != "REJECT")
    _teacher_breeding.record_policy_outcome_side_effects(
        channel, effective_policy, capability=capability,
        curriculum_scope=curriculum_scope, retained=decision["decision"] != "REJECT",
        realized_action_key=action_key)
    if no_target_gain:
        capability_stagnation["no_target_gain_streak"] += 1
    else:
        capability_stagnation["no_target_gain_streak"] = 0
    inherited_exploration, selection_reward = _stagnation_feedback(
        teacher, capability, policy_key, decision, reward, record,
        shared_stagnation)
    record["trials"] += 1
    record["reward_sum"] += reward
    record["latest"] = reward
    record["last_plasticity_active"] = bool(
        (decision.get("plasticity_escape") or {}).get("active"))
    diagnostic_stats = record.setdefault("diagnostic_stats", {})
    diagnostic = diagnostic_stats.setdefault(diagnostic_key, {
        "trials": 0, "reward_sum": 0., "unsafe": 0, "retained": 0,
    })
    diagnostic["trials"] += 1
    diagnostic["reward_sum"] += reward
    if decision["decision"] == "REJECT":
        diagnostic["unsafe"] += 1
    else:
        diagnostic["retained"] += 1
    _record_realized_action_outcome(
        action_record, rejected=decision["decision"] == "REJECT",
        no_target_gain=no_target_gain, reward=reward, diagnostic_key=diagnostic_key)
    strain = decision.get("matrix_strain") or {}
    if strain.get("status") == "MEASURED":
        # A bounded teacher-observable geometric feature; outcome rewards
        # still come only from actual source-scored capability probes.
        matrices = strain["matrices"]
        record["latest_matrix_strain"] = {
            "best_checkpoint_sha256": strain["best_checkpoint_sha256"],
            "tensor_count": len(matrices),
            "mean_delta_best": sum(item["delta_best_mean_sq"]
                                   for item in matrices.values()) / len(matrices),
            "mean_delta_start": sum(item["delta_start_mean_sq"]
                                    for item in matrices.values()) / len(matrices),
        }
    replay = decision.get("fragile_replay") or {}
    if replay.get("status") == "MEASURED":
        record["latest_fragile_replay"] = {
            "cohort_sha256": replay["cohort_sha256"],
            "rows": replay["rows"],
            "regressions": len(replay["regressions"]),
            "repaired": replay["repaired"],
        }
    channel["events"] += 1
    return {"version": VERSION, "teacher_context_reward": reward,
            "no_target_gain_streak": record["no_target_gain_streak"],
            "shared_no_target_gain_streak":
                shared_stagnation["no_target_gain_streak"],
            "capability_rejection_streak":
                capability_stagnation["rejection_streak"],
            "capability_no_target_gain_streak":
                capability_stagnation["no_target_gain_streak"],
            "consecutive_interference_rejections":
                capability_stagnation["consecutive_interference_rejections"],
            "attempts_since_retained":
                capability_stagnation["attempts_since_retained"],
            "diagnostic_context_key": diagnostic_key,
            **({"realized_action_key": action_key} if action_key is not None else {}),
            "inherited_exploration_credit": inherited_exploration,
            "teacher_selection_reward": selection_reward,
            "legacy_reward_reinterpreted": False,
            "negative_archetype_count": len(channel["negative_archetypes"])}


def selection_credit(lesson_reward: float, retention: dict | None,
                     contextual: dict | None) -> float:
    """Use source-paired admission feedback for forward-only bandit learning.

    The old lesson delta still describes retained student accuracy. Under
    retention it is zero on rejection, which must not mean a neutral teacher
    experiment. The context channel has already scored that same attempt.
    """
    if retention is None:
        return lesson_reward
    reward = contextual.get("teacher_selection_reward") if isinstance(contextual, dict) else None
    if reward is None and isinstance(contextual, dict):
        reward = contextual.get("teacher_context_reward")
    if (not isinstance(reward, (float, int)) or not math.isfinite(reward) or
            (retention.get("decision") == "REJECT" and reward >= 0)):
        raise ValueError("LEARNING_EXPERIMENT_INVALID_SELECTION_CREDIT")
    return float(reward)


def fork_student(mx, parameters: dict, optimizer):
    """Create an isolated MLX-native trial without a host NumPy round-trip."""
    import mlx.optimizers as optim
    mx.eval(parameters, optimizer.state)

    def copy_value(value):
        if isinstance(value, mx.array):
            # MLX-native construction gives the trial an independently mutable
            # leaf without forcing the accepted parent through host-visible
            # NumPy memory first.
            return mx.array(value)
        if isinstance(value, dict):
            return {key: copy_value(item) for key, item in value.items()}
        raise ValueError("LEARNING_EXPERIMENT_UNKNOWN_OPTIMIZER_STATE")

    trial_parameters = copy_value(parameters)
    trial_optimizer = optim.AdamW(
        learning_rate=float(optimizer.learning_rate),
        betas=list(optimizer.betas), eps=optimizer.eps,
        weight_decay=optimizer.weight_decay,
        bias_correction=optimizer.bias_correction)
    trial_optimizer.state = copy_value(optimizer.state)
    mx.eval(trial_parameters, trial_optimizer.state)
    return trial_parameters, trial_optimizer


def commit_trial(parameters: dict, optimizer, trial_parameters: dict, trial_optimizer) -> None:
    """A single caller-owned promotion; rejected trials leave parents intact."""
    if set(parameters) != set(trial_parameters):
        raise ValueError("LEARNING_EXPERIMENT_PARAMETER_IDENTITY_DRIFT")
    if (set(optimizer.state) != set(trial_optimizer.state) or
            int(trial_optimizer.state["step"].item()) <
            int(optimizer.state["step"].item())):
        raise ValueError("LEARNING_EXPERIMENT_ADAMW_DRIFT")
    parameters.update(trial_parameters)
    optimizer.state = trial_optimizer.state
    optimizer.learning_rate = trial_optimizer.learning_rate


def earlier_grade_capabilities(program, graduated_grades, target: str, *,
                               carried_mastery_debt=()) -> tuple[str, ...]:
    """Earlier graduated skills and explicitly carried debt supply old lessons.

    A champion for the active grade does not make its own rows earlier-grade
    rehearsal; future grades must not leak into the pool during recovery.
    """
    from bilqis_mlx.factory.schedule import ScheduleProgram
    if not isinstance(program, ScheduleProgram):
        raise TypeError("LEARNING_EXPERIMENT_SCHEDULE_PROGRAM_REQUIRED")
    target_index = next((
        index for index, grade in enumerate(program.grades)
        if target in {capability.id for capability in grade.capabilities}
    ), None)
    if target_index is None:
        raise ValueError("LEARNING_EXPERIMENT_UNKNOWN_TARGET_GRADE")
    graduated = set(graduated_grades)
    debt = set(carried_mastery_debt)
    return tuple(sorted(
        capability.id
        for grade in program.grades[:target_index]
        for capability in grade.capabilities
        if grade.id in graduated or capability.id in debt))






def reserve_weakness_targets(chosen: list[dict],
                             targets: list[dict], *,
                             protected_ids: set[str] | frozenset[str] = frozenset()
                             ) -> tuple[list[dict], tuple[dict, ...]]:
    """Replace generic current rows with weak semantics without changing batch size."""
    result = list(chosen)
    protected = set(protected_ids)
    remaining_protected = set(protected)
    consumed = set()
    for index, row in enumerate(result):
        identity = row.get("id")
        if identity in remaining_protected:
            consumed.add(index)
            remaining_protected.remove(identity)
    if remaining_protected:
        raise ValueError(
            WeaknessTargetError.LEARNING_EXPERIMENT_WEAKNESS_TARGET_CAPACITY_DRIFT.value)
    delivered = []
    for target in targets:
        existing = next((
            index for index, row in enumerate(result)
            if index not in consumed and row["id"] == target["id"]
        ), None)
        if existing is not None:
            consumed.add(existing)
            delivered.append(target)
            continue

        pattern = target.get("operand_truths")
        answer_kind = target.get("answer_kind", "binary")
        replacement = None
        if isinstance(pattern, list):
            replacement = next((
                index for index, row in enumerate(result)
                if index not in consumed and row.get("operand_truths") == pattern
            ), None)
        if replacement is None and answer_kind == "binary":
            replacement = next((
                index for index, row in enumerate(result)
                if index not in consumed and row.get("gold") == target.get("gold")
            ), None)
        if replacement is None:
            replacement = next((
                index for index, row in enumerate(result)
                if index not in consumed and
                row.get("answer_kind", "binary") == answer_kind
            ), None)
        if replacement is None:
            replacement = next((
                index for index in range(len(result)) if index not in consumed
            ), None)
        if replacement is None:
            raise ValueError(WeaknessTargetError.LEARNING_EXPERIMENT_WEAKNESS_TARGET_CAPACITY_DRIFT.value)
        result[replacement] = target
        consumed.add(replacement)
        delivered.append(target)
    return result, tuple(delivered)


def select_source_lesson(current: list[dict], prior: list[dict], policy: dict,
                         *, seed: int, batch_size: int,
                         targets: list[dict] | tuple[dict, ...] = (),
                         priority_target_ids: set[str] | frozenset[str] = frozenset(),
                         target_exposures: Mapping[str, int] | None = None,
                         reserved_support_slots: int = 0
                         ) -> tuple[list[dict], dict]:
    """Make inherited old/contrast/depth knobs effective for every answer type.

    'old' means actual examples originating in already-graduated grades, not
    embedded prerequisites or a source-unverified fixed teaching mix.
    'depth' uses token-count emphasis only when that proxy is named as such.
    Future-grade preview is intentionally inapplicable: never teach new roots.
    """
    if not current or type(batch_size) is not int or batch_size < 2:
        raise ValueError("LEARNING_EXPERIMENT_EMPTY_TYPED_LESSON")
    if (type(reserved_support_slots) is not int or
            not 0 <= reserved_support_slots <= batch_size):
        raise ValueError(WeaknessTargetError.LEARNING_EXPERIMENT_SUPPORT_CAPACITY_INVALID.value)
    rng = random.Random(seed)
    requested_old = int(policy.get("old", 0))
    if not 0 <= requested_old <= 32:
        raise ValueError("LEARNING_EXPERIMENT_INVALID_OLD_POLICY")
    target_ids = {row["id"] for row in targets}
    generic_current = [
        row for row in current if row.get("id") not in target_ids]
    if not generic_current:
        raise ErrorBus.legacy_error(SCHOOL.LEARNING.MISSING_FRESH_CURRENT_ROWS)
    semantic_patterns = sorted({
        tuple(row["operand_truths"]) for row in generic_current
        if isinstance(row.get("operand_truths"), list)
    })
    structured_binary = bool(semantic_patterns) and all(
        isinstance(row.get("operand_truths"), list) for row in generic_current)
    minimum_current = len(semantic_patterns) if structured_binary else 2
    old_count = min(batch_size-minimum_current,
                    round(requested_old*batch_size/32)) if prior else 0
    present_count = batch_size-old_count
    choose_current = _choose_binary_rows if structured_binary else _choose_typed_rows
    current_ids = {row["id"] for row in current}
    if any(row.get("id") not in current_ids for row in targets):
        raise ValueError(WeaknessTargetError.LEARNING_EXPERIMENT_WEAKNESS_TARGET_OUTSIDE_CURRENT.value)
    priority_target_ids = set(priority_target_ids)
    if (any(not isinstance(identity, str) or not identity
            for identity in priority_target_ids) or
            not priority_target_ids <= target_ids):
        raise ValueError(LearningExperimentError.PRIORITY_TARGET_INVALID.value)
    fresh_support = (
        _fresh_support_rows(
            generic_current, policy, rng,
            structured_binary=structured_binary,
            semantic_patterns=semantic_patterns,
            present_count=present_count,
            max_rows=max(0, batch_size-reserved_support_slots))
        if targets else ())
    # Weakness replay replaces current-capability rows, while preservation
    # support is injected later into the whole batch and may displace old-grade
    # rows.  Bound replay by both constraints instead of charging every future
    # support row against the current slice.
    free_current_slots = max(0, present_count - len(fresh_support))
    free_batch_slots_after_support = max(
        0, batch_size - len(fresh_support) - reserved_support_slots)
    target_capacity = min(
        free_current_slots, free_batch_slots_after_support)
    priority_targets = [
        row for row in targets if row["id"] in priority_target_ids]
    ordinary_targets = [
        row for row in targets if row["id"] not in priority_target_ids]
    selected_priority = select_weakness_targets(
        priority_targets,
        WeaknessTargetRequest(
            exposures=dict(target_exposures or {}),
            capacity=target_capacity,
        ))
    selected_ordinary = select_weakness_targets(
        ordinary_targets,
        WeaknessTargetRequest(
            exposures=dict(target_exposures or {}),
            capacity=max(0, target_capacity-len(selected_priority)),
        ))
    selected_targets = [*selected_priority, *selected_ordinary]
    current_rows = choose_current(generic_current, present_count, policy, rng)
    current_rows, delivered_support = reserve_weakness_targets(
        current_rows, list(fresh_support))
    support_ids = {row["id"] for row in delivered_support}
    current_rows, delivered_targets = reserve_weakness_targets(
        current_rows, selected_targets, protected_ids=support_ids)
    result = current_rows + _choose_typed_rows(prior, old_count, policy, rng)
    rng.shuffle(result)
    delivered_patterns = ({tuple(row["operand_truths"]) for row in result
                           if isinstance(row.get("operand_truths"), list)}
                          if structured_binary else set())
    return ([{**row, "answer_kind": row.get("answer_kind", "binary")}
             for row in result],
            {"effective_old_grade_examples": old_count,
             "requested_old_per_32": requested_old,
             "weakness_targets_available": len(targets),
             "weakness_targets_requested": len(selected_targets),
             "weakness_targets_delivered": len(delivered_targets),
             "weakness_target_ids": [row["id"] for row in delivered_targets],
             "fresh_support_ids": [row["id"] for row in delivered_support],
             "fresh_support_delivered": len(delivered_support),
             "priority_weakness_targets_available": len(priority_targets),
             "priority_weakness_targets_requested": len(selected_priority),
             "priority_weakness_targets_delivered": sum(
                 row["id"] in priority_target_ids for row in delivered_targets),
             "reserved_support_slots": reserved_support_slots,
             "current_semantic_patterns_required": len(semantic_patterns),
             "current_semantic_patterns_delivered": len(delivered_patterns),
             "depth_control": "SOURCE_TOKEN_LENGTH_PROXY" if policy.get("depth", 1) >= COMPOSITION_DEPTH_POLICY_THRESHOLD
                              else "UNBIASED_SOURCE_GROUPS",
             "contrast_control": "SOURCE_GROUP_DIVERSITY" if policy.get("contrast", 0.) >= .5
                                 else "SOURCE_GROUP_RANDOM",
             "preview_control": "NOT_AVAILABLE_UNADMITTED_FUTURE_GRADE"})
