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


from ._learning_experiment_retention import (
    Settings, _fixed_frontier_retention_evidence, _paired_screen,
    _prototype_similarity, _same_grade_retention_evidence,
)

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


def _frontier_retention_state(fixed_frontier_replay, protected_frontier_grade,
                              fixed, fragile_replay):
    frontier, whole_school_regression, active_grade_regression, frontier_net = (
        _fixed_frontier_retention_evidence(
            fixed_frontier_replay, protected_frontier_grade))
    frontier_measured = frontier.get("status") == "MEASURED"
    protected_frontier_delta = None
    if frontier_measured and protected_frontier_grade is not None:
        grades = frontier.get("grades")
        grade = (grades.get(protected_frontier_grade)
                 if isinstance(grades, dict) else None)
        if isinstance(grade, dict):
            protected_frontier_delta = grade["after"] - grade["before"]
    fixed_grade_regression = (
        fixed.get("status") == "MEASURED" and
        fixed["net_correct_delta"] < 0)
    fragile_losses = bool(
        fragile_replay and fragile_replay.get("regressions"))
    if (fragile_replay is not None and
            fragile_replay.get("status") not in ("MEASURED", "NOT_MEASURED")):
        raise ValueError("LEARNING_EXPERIMENT_INVALID_FRAGILE_REPLAY")
    return (frontier, whole_school_regression, active_grade_regression,
            frontier_net, frontier_measured, protected_frontier_delta,
            fixed_grade_regression, fragile_losses)


def _decision_record(*, reason, fragile_replay, fixed, frontier, frontier_net,
                     protected_frontier_grade, protected_frontier_delta, phase,
                     active_capability, active, protected, allowed, tolerances,
                     regressions, mature_grades, projected_mature_debt,
                     plasticity, exceeded, active_gain, same_grade_net_gain,
                     required, protected_net_gain, fingerprint,
                     source_cohort_sha256, deltas, negative_prototypes):
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
        "mature_protected_capabilities": sorted(
            cap for cap in regressions if cap.partition(".")[0] in mature_grades),
        "projected_mature_grade_debt": projected_mature_debt,
        "mature_grade_debt_hard_limit": _mature_debt.HARD_LIMIT,
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
        "discordance_similarity": _prototype_similarity(
            deltas, negative_prototypes or []),
        "exact_complete_exam_qualification": False,
    }


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
    (frontier, whole_school_regression, active_grade_regression, frontier_net,
     frontier_measured, protected_frontier_delta, fixed_grade_regression,
     fragile_losses) = _frontier_retention_state(
         fixed_frontier_replay, protected_frontier_grade, fixed, fragile_replay)
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
    return _decision_record(
        reason=reason, fragile_replay=fragile_replay, fixed=fixed,
        frontier=frontier, frontier_net=frontier_net,
        protected_frontier_grade=protected_frontier_grade,
        protected_frontier_delta=protected_frontier_delta, phase=phase,
        active_capability=active_capability, active=active, protected=protected,
        allowed=allowed, tolerances=tolerances, regressions=regressions,
        mature_grades=mature_grades, projected_mature_debt=projected_mature_debt,
        plasticity=plasticity, exceeded=exceeded, active_gain=active_gain,
        same_grade_net_gain=same_grade_net_gain, required=required,
        protected_net_gain=protected_net_gain, fingerprint=fingerprint,
        source_cohort_sha256=source_cohort_sha256, deltas=deltas,
        negative_prototypes=negative_prototypes)


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
