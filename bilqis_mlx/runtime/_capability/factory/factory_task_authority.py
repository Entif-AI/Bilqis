"""Factory/source ownership of one gold-blind C04 TaskGoal and binding."""
from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import replace
import hashlib
import json

from bilqis_mlx.factory.generation import runtime_adapter_for_release
from bilqis_mlx.runtime.atlas_model_contracts import BamfCompiledBatch
from bilqis_mlx.runtime.source_execution import (
    SourceExecutionContext, source_content_digest,
)
from bilqis_mlx.semantics.cognitive_dag import TaskGoal
from bilqis_mlx.semantics.cognitive_operators import OperatorBinding
from bilqis_mlx.semantics.domains import contract_digest

from .capability_evaluation import _invalid
from .factory_task_template import (
    FactoryTaskTemplate, _source_view, factory_task_template,
    validate_factory_task_template,
)
from bilqis_mlx.source_adapters.task_goal_registry import require_task_goal_lowerer


_ISSUER = object()


def _generation_authority(
    source_context, compiled_batch, row_id, capability_id, row_sha256,
    generation_binding,
):
    training = compiled_batch.training_authority
    if training is None:
        if not isinstance(generation_binding, str) or not generation_binding:
            _invalid("BAMF_C04_EVALUATION_GENERATION_REQUIRED")
        return generation_binding, source_context.release.release_sha256, None
    if (training.release_sha256 != source_context.release.release_sha256
            or training.source_row_id != row_id
            or training.source_row_sha256 != row_sha256
            or training.delivery_capability != capability_id
            or (generation_binding is not None
                and generation_binding != training.generation_binding)):
        _invalid("BAMF_C04_FACTORY_TASK_SOURCE_MISMATCH")
    return training.generation_binding, training.release_sha256, training.digest


@dataclass(frozen=True, init=False)
class FactoryTaskAuthority:
    goal: TaskGoal
    binding: OperatorBinding
    release_sha256: str
    generation_binding: str
    capability_id: str
    source_row_id: str
    source_row_sha256: str
    source_binding_sha256: str
    training_authority_sha256: str | None
    source_family_id: str
    episode_id: str
    lowerer_sha256: str
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("BAMF_C04_FACTORY_TASK_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self):
        if (getattr(self, "_issuance", None) is not _ISSUER
                or type(self.goal) is not TaskGoal
                or type(self.binding) is not OperatorBinding
                or not all(isinstance(item, str) and item for item in (
                    self.release_sha256, self.generation_binding,
                    self.capability_id, self.source_row_id,
                    self.source_row_sha256, self.source_binding_sha256,
                    self.source_family_id, self.episode_id, self.lowerer_sha256))
                or (self.training_authority_sha256 is not None
                    and (not isinstance(self.training_authority_sha256, str)
                         or not self.training_authority_sha256))
                or self.goal.goal_id != self.source_row_id
                or self.goal.semantic_release != self.binding.task.semantic_release
                or self.goal.scope != self.binding.task.scope
                or contract_digest(self.binding) != self.source_binding_sha256):
            _invalid("BAMF_C04_FACTORY_TASK_AUTHORITY_INVALID")

    @property
    def digest(self) -> str:
        wire = json.dumps({
            "goal": contract_digest(self.goal),
            "binding": self.source_binding_sha256,
            "release": self.release_sha256,
            "generation": self.generation_binding,
            "capability": self.capability_id,
            "row": self.source_row_id,
            "row_sha256": self.source_row_sha256,
            "training_authority": self.training_authority_sha256,
            "source_family": self.source_family_id,
            "episode": self.episode_id,
            "lowerer": self.lowerer_sha256,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(wire.encode()).hexdigest()


def _issue_authority(
        template: FactoryTaskTemplate, generation: str,
        training_sha256: str | None, source_row_sha256: str) -> FactoryTaskAuthority:
    item = object.__new__(FactoryTaskAuthority)
    for name, value in (
        ("goal", template.goal), ("binding", template.binding),
        ("release_sha256", template.release_sha256),
        ("generation_binding", generation),
        ("capability_id", template.capability_id),
        ("source_row_id", template.source_row_id),
        ("source_row_sha256", source_row_sha256),
        ("source_binding_sha256", template.source_binding_sha256),
        ("training_authority_sha256", training_sha256),
        ("source_family_id", template.source_family_id),
        ("episode_id", template.episode_id),
        ("lowerer_sha256", template.lowerer_sha256), ("_issuance", _ISSUER),
    ):
        object.__setattr__(item, name, value)
    item.__post_init__()
    return item


def factory_task_authority(
    source_context: SourceExecutionContext,
    compiled_batch: BamfCompiledBatch,
    *,
    generation_binding: str | None = None,
) -> FactoryTaskAuthority:
    """Ask only the admitted source owner to lower one exact gold-blind task."""
    if (type(source_context) is not SourceExecutionContext
            or type(compiled_batch) is not BamfCompiledBatch):
        _invalid("BAMF_C04_FACTORY_TASK_AUTHORITY_REQUIRED")
    source_context.__post_init__()
    compiled_batch.__post_init__()
    template = factory_task_template(source_context, compiled_batch)
    source_row_sha256 = source_content_digest((compiled_batch.sources[0].source_row,))
    generation_binding, release_sha256, training_sha256 = _generation_authority(
        source_context, compiled_batch, template.source_row_id,
        template.capability_id, source_row_sha256,
        generation_binding)
    if release_sha256 != template.release_sha256:
        _invalid("BAMF_C04_FACTORY_TASK_SOURCE_MISMATCH")
    return _issue_authority(
        template, generation_binding, training_sha256, source_row_sha256)


def rebind_factory_task_authority(
    source_context: SourceExecutionContext,
    compiled_batch: BamfCompiledBatch,
    template: FactoryTaskTemplate,
    *,
    generation_binding: str,
) -> FactoryTaskAuthority:
    """Bind one already-lowered gold-blind task to a new execution generation."""
    if (type(source_context) is not SourceExecutionContext
            or type(compiled_batch) is not BamfCompiledBatch
            or type(template) is not FactoryTaskTemplate
            or not isinstance(generation_binding, str) or not generation_binding):
        _invalid("BAMF_C04_FACTORY_TASK_REBIND_INVALID")
    source_context.__post_init__()
    compiled_batch.__post_init__()
    validate_factory_task_template(source_context, compiled_batch, template)
    source = compiled_batch.sources[0]
    row = source.source_row
    row_id = row.get("id")
    capability_id = row.get("capability")
    row_sha256 = source_content_digest((row,))
    generation, release_sha256, training_sha256 = _generation_authority(
        source_context, compiled_batch, row_id, capability_id, row_sha256,
        generation_binding)
    if (template.release_sha256 != release_sha256
            or template.capability_id != capability_id
            or template.source_row_id != row_id
            or template.goal.semantic_release
            != compiled_batch.compiled.features.semantic_release
            or template.source_binding_sha256 != contract_digest(template.binding)):
        _invalid("BAMF_C04_FACTORY_TASK_REBIND_DRIFT")
    return _issue_authority(template, generation, training_sha256, row_sha256)


def factory_task_training_goal(
    source_context: SourceExecutionContext,
    compiled_batch: BamfCompiledBatch,
    authority: FactoryTaskAuthority,
):
    """Resolve training-only route truth through the same source lowerer owner."""
    if (type(source_context) is not SourceExecutionContext
            or type(compiled_batch) is not BamfCompiledBatch
            or type(authority) is not FactoryTaskAuthority):
        _invalid("BAMF_C04_FACTORY_TASK_TRAINING_TARGET_INVALID")
    source = compiled_batch.sources[0]
    row = source.source_row
    execution = source_context.release.execution_plan.capability_map.get(
        authority.capability_id)
    if (execution is None or row.get("id") != authority.source_row_id
            or source_content_digest((row,)) != authority.source_row_sha256):
        _invalid("BAMF_C04_FACTORY_TASK_TRAINING_TARGET_INVALID")
    adapter = runtime_adapter_for_release(
        source_context.source_root, source_context.graph,
        source_context.release, source_context.source_registry, execution,
        drift_code="BAMF_C04_FACTORY_TASK_ADAPTER_DRIFT",
    )
    lowerer = require_task_goal_lowerer(
        execution.provider_id, adapter.descriptor.implementation_sha256)
    if lowerer.implementation_sha256 != authority.lowerer_sha256:
        _invalid("BAMF_C04_FACTORY_TASK_TRAINING_TARGET_INVALID")
    resolved = lowerer.resolve(
        dict(row), semantic_release=compiled_batch.compiled.features.semantic_release,
        source_root=source_context.source_root, graph=source_context.graph,
        release=source_context.release, capability=execution)
    if type(resolved) is not TaskGoal:
        _invalid("BAMF_C04_FACTORY_TASK_TRAINING_TARGET_INVALID")
    return resolved


def bind_factory_task_compiled_batch(
    compiled_batch: BamfCompiledBatch,
    authority: FactoryTaskAuthority,
) -> BamfCompiledBatch:
    """Bind existing C04 source authority to the B11 batch it already owns."""
    if (type(compiled_batch) is not BamfCompiledBatch
            or type(authority) is not FactoryTaskAuthority):
        _invalid("BAMF_C04_B11_TASK_AUTHORITY_BINDING_INVALID")
    authority.__post_init__()
    compiled_batch.__post_init__()
    return replace(compiled_batch, task_authority=authority)


__all__ = (
    "FactoryTaskAuthority", "_source_view", "factory_task_authority",
    "factory_task_training_goal",
    "bind_factory_task_compiled_batch", "rebind_factory_task_authority",
)
