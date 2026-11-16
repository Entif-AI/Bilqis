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
