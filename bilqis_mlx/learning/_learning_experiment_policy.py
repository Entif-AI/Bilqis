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


from ._learning_experiment_decision import (
    _capability_stagnation, _channel, _diagnostic_context,
    _effective_context_scope, _effective_policy_key,
)

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
