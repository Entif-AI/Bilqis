"""Runtime adapter for contextual teacher selection and bounded vNext canaries."""
from __future__ import annotations

import bilqis_mlx.learning.learning_experiment as _learning_experiment
import bilqis_mlx.learning.teacher_breeding as _teacher_breeding
import bilqis_mlx.learning.teacher_strategy_population as _strategy_population
import bilqis_mlx.learning.teacher_vnext_replay as _teacher_vnext
import bilqis_mlx.runtime.timing_trace as _timing_trace


def select_visit_policy(engine, teacher, cap, school, rng, learning_settings,
                        teacher_curriculum_scope, previsit_diagnostics,
                        lesson_grade, total_capabilities=None,
                        plasticity_escape=None):
    """Select one policy while preserving contextual and vNext authority rules."""
    with _timing_trace.trace_span("POLICY_SELECT", capability=cap):
        if learning_settings is None:
            if teacher.get("selection_contract") == _strategy_population.BAMF_SUCCESSOR_SELECTION:
                active, inventory = _strategy_population.active_effective_strategy_keys(teacher, lesson_grade, {})
                key, policy = _strategy_population.pick_existing_active(engine, teacher, lesson_grade, rng, active, inventory)
            else:
                key, policy = engine.pick(teacher, lesson_grade, rng)
            return key, policy, {
                "diagnostic_context_consumed": False,
                "diagnostic_context_key": None,
                "selection_reason": "INHERITED_BANDIT",
                "selection_policy": "bilqis.mlx.teacher-selection/inherited-v1",
            }
        key, policy, metadata = _learning_experiment.contextual_pick(
            engine, teacher, cap, school.stage, rng,
            curriculum_scope=teacher_curriculum_scope,
            diagnostics=previsit_diagnostics, return_metadata=True,
            student_checkpoint_sha256=school.current_student.sha256,
            total_capabilities=total_capabilities, lesson_grade=lesson_grade,
            plasticity_active=bool((plasticity_escape or {}).get("active")))
        legacy_key, legacy_reason = key, metadata.get("selection_reason")
        context_key = cap + "|" + school.stage + "|" + teacher_curriculum_scope
        channel = teacher.get("causal_experiment", {})
        scope = channel.get("contexts", {}).get(context_key, {})
        active, inventory = _strategy_population.active_effective_strategy_keys(
            teacher, lesson_grade, scope, total_capabilities=total_capabilities)
        active = _teacher_breeding.filter_active_effective(
            teacher, grade=lesson_grade, capability=cap,
            curriculum_scope=teacher_curriculum_scope,
            active_effective=active, inventory=inventory)
        active, _retired = _strategy_population.checkpoint_active_effective_strategy_keys(
            teacher, lesson_grade, scope, channel, context_key, active, inventory,
            school.current_student.sha256)
        sibling_penalties = {
            effective: penalty for effective in active
            if (penalty := _strategy_population.sibling_cooldown_penalty(
                channel, cap, teacher_curriculum_scope, effective)) > 0
        }
        ordinal = int(channel.get("events", 0)) + 1
        if legacy_reason in {
                "FRESH_MUTATED_CHALLENGER", "PORTABLE_RETAINED_CHALLENGER",
                "PLASTICITY_RETRY"}:
            canary = {
                "schema": _teacher_vnext.SCHEMA,
                "policy_version": "teacher-vnext-canary/v1",
                "candidate_ordinal": ordinal, "scheduled": False,
                "actual_authority_changed": False,
                "status": (
                    "BYPASSED_BESPOKE_EXPLORATION"
                    if legacy_reason == "FRESH_MUTATED_CHALLENGER"
                    else ("BYPASSED_PORTABLE_RETAINED_CHALLENGER"
                          if legacy_reason == "PORTABLE_RETAINED_CHALLENGER"
                          else "BYPASSED_PLASTICITY_RETRY")),
                "policy_key": None,
            }
        else:
            canary = _teacher_vnext.select_canary(
                teacher, capability=cap, phase=school.stage,
                curriculum_scope=teacher_curriculum_scope,
                candidate_ordinal=ordinal, rng=rng,
                active_effective_policy_keys=active, inventory=inventory,
                effective_policy_penalties=sibling_penalties)
        metadata = dict(metadata)
        metadata["vnext_canary"] = canary
        metadata["actual_authority_changed"] = bool(
            canary.get("actual_authority_changed"))
        if canary.get("status") == "SELECTED":
            key = canary["policy_key"]
            policy = teacher["strategies"][key]
            metadata.update({
                "legacy_policy_key": legacy_key,
                "legacy_selection_reason": legacy_reason,
                "selection_reason": "VNEXT_CANARY",
                "selection_policy": _teacher_vnext.SELECTION_POLICY,
            })
        return key, policy, metadata
