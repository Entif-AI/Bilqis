"""Generation-independent C04 task lowering for reusable C05 evaluation cases."""
from __future__ import annotations

from dataclasses import dataclass

from bilqis_mlx.factory.generation import runtime_adapter_for_release
from bilqis_mlx.runtime.atlas_model_contracts import BamfCompiledBatch
from bilqis_mlx.runtime.source_execution import (
    SourceExecutionContext, source_content_digest,
)
from bilqis_mlx.semantics.cognitive_dag import TaskGoal
from bilqis_mlx.semantics.cognitive_operators import OperatorBinding
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.source_adapters.task_goal_registry import require_task_goal_lowerer

from .capability_evaluation import _invalid


_PRIVATE_SOURCE_KEYS = frozenset((
    "gold", "native_output", "auxiliary_labels", "answer", "label",
    "expected", "expected_answer", "score", "oracle_result",
))
_LOWERING_RESULT_WIDTH = 2


def _source_view(row: dict) -> dict:
    if not isinstance(row, dict):
        _invalid("BAMF_C04_SOURCE_TASK_ROW_INVALID")
    return {key: value for key, value in row.items()
            if key not in _PRIVATE_SOURCE_KEYS}


@dataclass(frozen=True)
class FactoryTaskTemplate:
    """Gold-blind source lowering with no generation execution authority."""

    goal: TaskGoal
    binding: OperatorBinding
    release_sha256: str
    capability_id: str
    source_row_id: str
    source_row_sha256: str
    source_binding_sha256: str
    source_family_id: str
    episode_id: str
    lowerer_sha256: str

    def __post_init__(self) -> None:
        if (type(self.goal) is not TaskGoal
                or type(self.binding) is not OperatorBinding
                or not all(isinstance(item, str) and item for item in (
                    self.release_sha256, self.capability_id, self.source_row_id,
                    self.source_row_sha256, self.source_binding_sha256,
                    self.source_family_id, self.episode_id, self.lowerer_sha256))
                or self.goal.goal_id != self.source_row_id
                or self.goal.semantic_release != self.binding.task.semantic_release
                or contract_digest(self.binding) != self.source_binding_sha256):
            _invalid("BAMF_C04_FACTORY_TASK_TEMPLATE_INVALID")


def _owner(source_context, compiled_batch):
    source = compiled_batch.sources[0]
    row = source.source_row
    row_id, capability_id = row.get("id"), row.get("capability")
    row_sha256 = source_content_digest((_source_view(row),))
    execution = source_context.release.execution_plan.capability_map.get(capability_id)
    if execution is None:
        _invalid("BAMF_C04_FACTORY_TASK_CAPABILITY_MISSING")
    adapter = runtime_adapter_for_release(
        source_context.source_root, source_context.graph,
        source_context.release, source_context.source_registry, execution,
        drift_code="BAMF_C04_FACTORY_TASK_ADAPTER_DRIFT",
    )
    try:
        lowerer = require_task_goal_lowerer(
            execution.provider_id, adapter.descriptor.implementation_sha256)
    except ValueError:
        _invalid("BAMF_C04_SOURCE_TASK_LOWERER_REQUIRED")
    training = compiled_batch.training_authority
    family = None if training is None else training.source_family_id
    episode = None if training is None else training.episode_id
    if not isinstance(family, str) or not family:
        family = row.get("source_family_id")
    if not isinstance(family, str) or not family:
        family = contract_digest({
            "schema": "bilqis.mlx.source-draw-family/v1",
            "provider": execution.provider_id,
            "implementation": execution.provider_implementation_sha256,
            "capability": execution.capability_id,
        })
    if not isinstance(episode, str) or not episode:
        episode = row.get("episode_id")
    if not isinstance(episode, str) or not episode:
        episode = row_id
    return row, row_id, capability_id, row_sha256, execution, lowerer, family, episode


def factory_task_template(
    source_context: SourceExecutionContext,
    compiled_batch: BamfCompiledBatch,
) -> FactoryTaskTemplate:
    """Lower one exact source row once, before any generation is selected."""
    if (type(source_context) is not SourceExecutionContext
            or type(compiled_batch) is not BamfCompiledBatch):
        _invalid("BAMF_C04_FACTORY_TASK_TEMPLATE_REQUIRED")
    source_context.__post_init__()
    compiled_batch.__post_init__()
    row, row_id, capability_id, row_sha256, execution, lowerer, family, episode = (
        _owner(source_context, compiled_batch))
    lowered = lowerer.lower(
        _source_view(row),
        semantic_release=compiled_batch.compiled.features.semantic_release,
        source_root=source_context.source_root,
        graph=source_context.graph,
        release=source_context.release,
        capability=execution,
    )
    if (not isinstance(lowered, tuple) or len(lowered) != _LOWERING_RESULT_WIDTH
            or type(lowered[0]) is not TaskGoal
            or type(lowered[1]) is not OperatorBinding):
        _invalid("BAMF_C04_SOURCE_TASK_LOWERING_INVALID")
    goal, binding = lowered
    return FactoryTaskTemplate(
        goal, binding, source_context.release.release_sha256, capability_id,
        row_id, row_sha256, contract_digest(binding), family, episode,
        lowerer.implementation_sha256)


def validate_factory_task_template(
    source_context: SourceExecutionContext,
    compiled_batch: BamfCompiledBatch,
    template: FactoryTaskTemplate,
) -> None:
    """Revalidate source/release/lowerer identity without lowering the task again."""
    if not factory_task_template_matches(source_context, compiled_batch, template):
        _invalid("BAMF_C04_FACTORY_TASK_TEMPLATE_DRIFT")


def factory_task_template_matches(
    source_context: SourceExecutionContext,
    compiled_batch: BamfCompiledBatch,
    template: FactoryTaskTemplate,
) -> bool:
    """Check the live source/lowerer contract without invoking the lowerer."""
    if (type(source_context) is not SourceExecutionContext
            or type(compiled_batch) is not BamfCompiledBatch
            or type(template) is not FactoryTaskTemplate):
        _invalid("BAMF_C04_FACTORY_TASK_TEMPLATE_REQUIRED")
    source_context.__post_init__()
    compiled_batch.__post_init__()
    template.__post_init__()
    _row, row_id, capability_id, row_sha256, _execution, lowerer, family, episode = (
        _owner(source_context, compiled_batch))
    return not (
        template.release_sha256 != source_context.release.release_sha256
        or template.capability_id != capability_id
        or template.source_row_id != row_id
        or template.source_row_sha256 != row_sha256
        or template.lowerer_sha256 != lowerer.implementation_sha256
        or template.goal.semantic_release
        != compiled_batch.compiled.features.semantic_release
        or template.source_binding_sha256 != contract_digest(template.binding)
        or template.source_family_id != family
        or template.episode_id != episode)


__all__ = (
    "FactoryTaskTemplate", "_source_view", "factory_task_template",
    "factory_task_template_matches", "validate_factory_task_template",
)
