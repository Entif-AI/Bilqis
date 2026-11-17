"""C08 execution of source-bound Factory rows as scalar or true MLX microbatches."""
from __future__ import annotations

from bilqis_mlx.runtime.atlas_model import (
    bamf_microbatch_value_and_grad, bamf_value_and_grad, microbatch_compatible,
)
from bilqis_mlx.runtime.factory_task_authority import (
    bind_factory_task_compiled_batch, factory_task_authority,
    factory_task_training_goal,
)
from bilqis_mlx.runtime.task_goal_readout import (
    task_goal_route_plan, task_goal_training_targets,
)

from .c08_gradient_accumulation import accumulate_logical_batch_gradients


def _row_execution_inputs(
        source_context, compiled, feature_snapshot, generation):
    authority = factory_task_authority(source_context, compiled)
    bound = bind_factory_task_compiled_batch(compiled, authority)
    resolved = factory_task_training_goal(source_context, bound, authority)
    targets, mask = task_goal_training_targets(authority.goal, resolved)
    plan = task_goal_route_plan(
        authority.goal, bound, feature_snapshot, generation)
    return bound, authority, targets, mask, plan


def _mentor_multiplier(mentor_supervision, compiled):
    if mentor_supervision is None:
        return 1.0
    from bilqis_mlx.learning._championship.adviser_supervision import MentorSupervision
    if type(mentor_supervision) is not MentorSupervision:
        raise ValueError("FACTORY_MENTOR_SUPERVISION_TYPE_INVALID")
    return 1.0 + mentor_supervision.influence_for(compiled)


def execute_factory_training_row(
        parameters, compiled, source_context, feature_snapshot, generation, cache, *,
        salience_supervision=None, mentor_supervision=None):
    """Preserve the scalar B11 path as correctness oracle and fallback."""
    bound, authority, targets, mask, plan = _row_execution_inputs(
        source_context, compiled, feature_snapshot, generation)
    multiplier = _mentor_multiplier(mentor_supervision, compiled)
    gradient = bamf_value_and_grad(
        parameters, bound, plan, targets, mask, cache,
        salience_supervision=salience_supervision,
        source_loss_multiplier=multiplier)
    return gradient, authority, targets


def execute_factory_logical_batch(
        parameters, prepared, source_context, feature_snapshot, generation, cache,
        resource_plan, *, salience_supervision=None, mentor_supervision=None):
    """Execute each compatible C08 group with one MLX gradient launch."""
    rows = tuple(_row_execution_inputs(
        source_context, compiled, feature_snapshot, generation)
        for compiled in prepared.compiled_rows)
    bound = tuple(item[0] for item in rows)
    authorities = tuple(item[1] for item in rows)
    targets = tuple(item[2] for item in rows)
    masks = tuple(item[3] for item in rows)
    plans = tuple(item[4] for item in rows)

    def execute_row(index):
        multiplier = _mentor_multiplier(
            mentor_supervision, prepared.compiled_rows[index])
        return bamf_value_and_grad(
            parameters, bound[index], plans[index], targets[index], masks[index], cache,
            salience_supervision=salience_supervision,
            source_loss_multiplier=multiplier)

    def execute_group(group):
        if mentor_supervision is not None:
            # R05 row influence is source-row specific. Preserve the scalar B11
            # oracle until the microbatch kernel grows explicit per-row weights.
            return None
        group_rows = tuple(bound[index] for index in group)
        group_plans = tuple(plans[index] for index in group)
        group_targets = tuple(targets[index] for index in group)
        group_masks = tuple(masks[index] for index in group)
        if not microbatch_compatible(
                group_rows, group_plans, group_targets, group_masks):
            return None
        return bamf_microbatch_value_and_grad(
            parameters,
            group_rows,
            group_plans,
            group_targets,
            group_masks,
            cache,
            salience_supervision=salience_supervision)

    gradient = accumulate_logical_batch_gradients(
        resource_plan, execute_row, execute_group=execute_group)
    return gradient, authorities, targets


__all__ = ("execute_factory_logical_batch", "execute_factory_training_row")
