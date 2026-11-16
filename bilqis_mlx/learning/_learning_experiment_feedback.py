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
    DIAGNOSTIC_CONTEXT_KEY_LENGTH, _capability_stagnation_record, _channel, _diagnostic_context,
    _effective_policy_key, _inherited_exploration,
    _shared_stagnation_record,
)

def _stagnation_feedback(teacher: dict, capability: str, policy_key: str,
                         decision: dict, reward: float, record: dict,
                         shared_stagnation: dict, lesson_grade=None) -> tuple[float, float]:
    no_target_gain = decision.get("reason") == "NO_MEASURABLE_TARGET_GAIN"
    inherited_exploration = _inherited_exploration(
        teacher, lesson_grade if lesson_grade is not None else capability.partition(".")[0], policy_key)
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


def _retention_reward(channel, *, capability, phase, curriculum_scope,
                      policy_key, decision, local_gain):
    relative_loss = max(
        (max(0., -value)
         for key, value in decision["deltas"].items()
         if key in decision["protected_capabilities"]),
        default=0.,
    )
    reward = local_gain - relative_loss * (1 if phase == "MAIN" else 2)
    if decision["decision"] == "REJECT":
        reward = min(reward, -relative_loss, -0.05)
    if (decision["decision"] == "REJECT" or
            decision.get("worst_protected_loss", 0) >= 1):
        pattern = {
            "capability": capability, "phase": phase,
            "curriculum_scope": curriculum_scope, "policy": policy_key,
            "delta": decision["deltas"],
            "paired_scores_sha256": decision["paired_scores_sha256"],
            "source_cohort_sha256": decision["source_cohort_sha256"],
            "outcome": ("REJECTED_UPDATE"
                        if decision["decision"] == "REJECT"
                        else "ACCEPTED_WITH_MEASURED_PROTECTED_LOSS"),
        }
        entries = channel["negative_archetypes"]
        if not any(
                item["paired_scores_sha256"] == pattern["paired_scores_sha256"] and
                item.get("source_cohort_sha256") == pattern["source_cohort_sha256"]
                for item in entries):
            entries.append(pattern)
            del entries[:-MAX_FAILURE_ARCHETYPES]
    return reward


def _update_capability_stagnation(capability_stagnation, decision):
    if decision["decision"] == "REJECT":
        capability_stagnation["rejection_streak"] += 1
        capability_stagnation["attempts_since_retained"] += 1
        capability_stagnation["total_rejections"] += 1
        reason = decision.get("reason")
        if not isinstance(reason, str) or not reason:
            raise ValueError(
                LearningExperimentError.REJECTION_REASON_INVALID.value)
        reasons = capability_stagnation["current_rejection_reasons"]
        reasons[reason] = reasons.get(reason, 0) + 1
        capability_stagnation["consecutive_interference_rejections"] = (
            0 if reason == "NO_MEASURABLE_TARGET_GAIN"
            else capability_stagnation["consecutive_interference_rejections"] + 1)
    else:
        capability_stagnation["rejection_streak"] = 0
        capability_stagnation["consecutive_interference_rejections"] = 0
        capability_stagnation["attempts_since_retained"] = 0
        capability_stagnation["total_retained"] += 1
        capability_stagnation["current_rejection_reasons"] = {}


def _record_context_metrics(record, diagnostic_key, decision, reward,
                            action_record, no_target_gain):
    record["trials"] += 1
    record["reward_sum"] += reward
    record["latest"] = reward
    record["last_plasticity_active"] = bool(
        (decision.get("plasticity_escape") or {}).get("active"))
    diagnostic = record.setdefault("diagnostic_stats", {}).setdefault(
        diagnostic_key,
        {"trials": 0, "reward_sum": 0., "unsafe": 0, "retained": 0},
    )
    diagnostic["trials"] += 1
    diagnostic["reward_sum"] += reward
    diagnostic["unsafe" if decision["decision"] == "REJECT" else "retained"] += 1
    _record_realized_action_outcome(
        action_record, rejected=decision["decision"] == "REJECT",
        no_target_gain=no_target_gain, reward=reward,
        diagnostic_key=diagnostic_key)
    strain = decision.get("matrix_strain") or {}
    if strain.get("status") == "MEASURED":
        matrices = strain["matrices"]
        record["latest_matrix_strain"] = {
            "best_checkpoint_sha256": strain["best_checkpoint_sha256"],
            "tensor_count": len(matrices),
            "mean_delta_best": sum(
                item["delta_best_mean_sq"] for item in matrices.values()) /
                len(matrices),
            "mean_delta_start": sum(
                item["delta_start_mean_sq"] for item in matrices.values()) /
                len(matrices),
        }
    replay = decision.get("fragile_replay") or {}
    if replay.get("status") == "MEASURED":
        record["latest_fragile_replay"] = {
            "cohort_sha256": replay["cohort_sha256"],
            "rows": replay["rows"],
            "regressions": len(replay["regressions"]),
            "repaired": replay["repaired"],
        }


def _feedback_diagnostic_key(channel, capability, curriculum_scope, diagnostics, key):
    if key is None:
        return _diagnostic_context(channel, capability, curriculum_scope, diagnostics)[0]
    payload = channel.get('diagnostic_contexts', {}).get(key)
    if (not isinstance(payload, dict) or payload != diagnostics
            or hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:DIAGNOSTIC_CONTEXT_KEY_LENGTH] != key):
        raise ValueError(LearningExperimentError.DIAGNOSTIC_CONTEXT_COLLISION.value)
    return key


def observe_context(teacher: dict, *, capability: str, phase: str,
                    policy_key: str, decision: dict, local_gain: float,
                    curriculum_scope: str = "",
                    diagnostics: dict | None = None,
                    realized_action: dict | None = None,
                    student_checkpoint_sha256: str | None = None,
                    lesson_grade: str | None = None,
                    diagnostic_context_key: str | None = None) -> dict:
    """Source-paired trial outcome; never rewrite historical UCB rewards."""
    if (policy_key not in teacher.get("strategies", {}) or
            not math.isfinite(local_gain) or
            decision.get("version") != VERSION or
            decision.get("active_capability") != capability or
            decision.get("phase") != phase):
        raise ValueError("LEARNING_EXPERIMENT_INVALID_CAUSAL_OUTCOME")
    no_target_gain = decision.get("reason") == "NO_MEASURABLE_TARGET_GAIN"
    channel = _channel(teacher)
    diagnostic_key = _feedback_diagnostic_key(
        channel, capability, curriculum_scope, diagnostics, diagnostic_context_key)
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
    reward = _retention_reward(
        channel, capability=capability, phase=phase,
        curriculum_scope=curriculum_scope, policy_key=policy_key,
        decision=decision, local_gain=local_gain)
    if decision["decision"] == "REJECT":
        record["unsafe"] += 1
    else:
        record["retained"] += 1
    _update_capability_stagnation(capability_stagnation, decision)
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
        shared_stagnation, lesson_grade)
    _record_context_metrics(
        record, diagnostic_key, decision, reward, action_record, no_target_gain)
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
