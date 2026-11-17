"""Join source-owned Factory delivery to C02 inputs and B11 row execution."""
from __future__ import annotations

from dataclasses import dataclass

from bilqis_mlx.factory.teaching import DeliveredTeaching
from bilqis_mlx.runtime.atlas_model_contracts import BamfCompiledBatch
from bilqis_mlx.runtime.bamf_bundle import (
    AuthenticatedCandidateFeatureContext, AuthenticatedGenerationFeatureContext,
    BamfBundleCandidate,
    authenticate_bamf_execution_feature_context,
)
from bilqis_mlx.runtime.source_execution import SourceExecutionContext

from .atlas_training_adapter import compile_training_batch
from .atlas_training_contracts import BamfTrainingBatch, BamfVisitProvenance, _invalid
from .factory_training_context import training_answer_plan
from .factory_training_source import (
    _FactoryMotifPlanningInput, _bind_b11_rows, _motif_planning_input,
    _prepare_b11_source_binding, _prepare_factory_source_rows,
)


@dataclass(frozen=True)
class PreparedFactoryTrainingBatch:
    """One source-owned C02 delivery plus exact row-scoped B11 inputs."""

    training_batch: BamfTrainingBatch
    compiled_rows: tuple[BamfCompiledBatch, ...]
    motif_inputs: tuple
    semantic_context: object

    def __post_init__(self) -> None:
        if (type(self.training_batch) is not BamfTrainingBatch
                or type(self.compiled_rows) is not tuple
                or len(self.compiled_rows) != len(self.training_batch.rows)
                or type(self.motif_inputs) is not tuple
                or len(self.motif_inputs) != len(self.training_batch.rows)
                or any(type(item) is not _FactoryMotifPlanningInput
                       for item in self.motif_inputs)
                or any(type(item) is not BamfCompiledBatch
                       for item in self.compiled_rows)
                or type(self.semantic_context) not in (
                    AuthenticatedCandidateFeatureContext,
                    AuthenticatedGenerationFeatureContext)):
            _invalid("FACTORY_TRAINING_BRIDGE_INVALID")
        self.semantic_context.__post_init__()




def _target_source_count(rows, rehearsal_by_id):
    return len(rows) - len(rehearsal_by_id)


def _validated_training_request(
        source_context, candidate, delivered_rows, generation_binding, *,
        capability, delivery, requested_count, source_seed, source_each,
        optimizer_step_seed, visit_provenance, teacher_strategy,
        rehearsal_by_id=None):
    rows = tuple(delivered_rows) if isinstance(delivered_rows, (tuple, list)) else ()
    rehearsal_by_id = {} if rehearsal_by_id is None else dict(rehearsal_by_id)
    target_source_count = _target_source_count(rows, rehearsal_by_id)
    if (type(source_context) is not SourceExecutionContext
            or not isinstance(candidate, BamfBundleCandidate)
            or not rows or any(type(row) is not dict for row in rows)
            or not isinstance(capability, str) or not capability
            or not isinstance(delivery, DeliveredTeaching)
            or type(requested_count) is not int or requested_count < len(rows)
            or type(source_seed) is not int or source_seed < 0
            or type(source_each) is not int or source_each != target_source_count
            or target_source_count < 1
            or type(optimizer_step_seed) is not int or optimizer_step_seed < 0
            or type(visit_provenance) is not BamfVisitProvenance
            or visit_provenance.capability_id != capability
            or not isinstance(teacher_strategy, dict)
            or not isinstance(generation_binding, str) or not generation_binding
            or source_context.source_root is None):
        _invalid("FACTORY_TRAINING_BRIDGE_INPUT_INVALID")
    return rows


def _prepared_source_inputs(
        prepared_source, source_context, authenticated, rows, *, capability,
        source_seed, source_each, delivery=None, rehearsal_by_id=None,
        rehearsal_bindings=None, rehearsal_authorities=None):
    if prepared_source is None:
        rehearsal_by_id = rehearsal_by_id or {}
        rehearsal_bindings = rehearsal_bindings or {}
        rehearsal_authorities = rehearsal_authorities or {}
        target_rows = tuple(row for row in rows if row.get("id") not in rehearsal_by_id)
        source_authority = (
            source_context.bind_rows(
                target_rows, seed=source_seed, capability=capability, each=source_each)
            if delivery is None or len(delivery.specimen_ids) == len(target_rows) else
            source_context.bind_delivery_rows(
                target_rows, seed=source_seed, capability=capability,
                direct_each=len(delivery.specimen_ids)))
        for identity, authority in rehearsal_authorities.items():
            row = next((item for item in rows if item.get("id") == identity), None)
            binding = rehearsal_bindings.get(identity)
            if (row is None or not isinstance(binding, dict)
                    or authority.capability_id != binding.get("capability")
                    or authority.seed != binding.get("seed")
                    or authority.each != binding.get("each")):
                _invalid("FACTORY_REHEARSAL_SOURCE_AUTHORITY_INVALID")
            source_context.require_bound_rows((row,), authority)
        adapter, manifest, profile, source_rows = _prepare_factory_source_rows(
            source_context, authenticated, rows, capability=capability,
            source_seed=source_seed, source_each=source_each,
            source_authority=source_authority,
            source_authorities_by_id=rehearsal_authorities,
            source_bindings_by_id=rehearsal_bindings)
        from bilqis_mlx.runtime.priority_source_materialization import (
            _prepare_model_sources,
        )
        prepared_model_sources, _configs = _prepare_model_sources(
            source_context, authenticated, manifest, source_rows)
        return (
            source_authority,
            adapter, manifest, profile, source_rows, prepared_model_sources,
            None, None,
        )
    from bilqis_mlx.runtime.priority_source_materialization import (
        PreparedPrioritySourceMaterialization,
    )
    if (type(prepared_source) is not PreparedPrioritySourceMaterialization
            or prepared_source.semantic_context is not authenticated
            or prepared_source.offer.capability_id != capability
            or prepared_source.offer.source_seed != source_seed
            or prepared_source.offer.source_each != source_each
            or prepared_source.rows != rows):
        _invalid("FACTORY_TRAINING_PREPARED_SOURCE_INVALID")
    prepared_source.require_current()
    source_context.require_bound_rows(
        rows, prepared_source.offer.source_authority)
    return (
        prepared_source.offer.source_authority,
        prepared_source.adapter,
        prepared_source.manifest,
        prepared_source.profile,
        prepared_source.source_rows,
        prepared_source.model_sources,
        prepared_source.motif_inputs,
        prepared_source.b11_sources,
    )


def _compile_factory_training(
        rows, source_context, candidate, delivery, capability, teacher_strategy,
        requested_count, optimizer_step_seed, visit_provenance, source_authority,
        rehearsal_by_id, rehearsal_authorities, source_rows,
        feature_artifact_path, generation_binding,
        authenticated, manifest, prepared_model_sources):
    by_tokens = {tuple(item.row["tokens"]): item.ast for item in source_rows}
    if len(by_tokens) != len(rows):
        _invalid("FACTORY_TRAINING_AMBIGUOUS_SOURCE_PREFIX")
    by_ast = {id(item.ast): item.projection for item in source_rows}
    return compile_training_batch(
        rows, source_context, candidate.topology, delivery=delivery,
        delivery_capability=capability,
        delivery_release_sha256=source_context.release.release_sha256,
        teacher_strategy=teacher_strategy,
        requested_count=requested_count, optimizer_step_seed=optimizer_step_seed,
        visit_provenance=visit_provenance,
        source_authority=source_authority,
        rehearsal_by_id=(rehearsal_by_id or {}),
        rehearsal_authorities=(rehearsal_authorities or {}),
        visible_ends={row["id"]: len(row["tokens"]) for row in rows},
        source_ast_for=lambda tokens: by_tokens[tuple(tokens)],
        compiler_config=tuple(item.config for item in source_rows),
        feature_artifact_path=feature_artifact_path,
        answer_plan_for=lambda prefix, release, cap, kind: training_answer_plan(
            prefix, release, kind, generation_binding),
        frames_for_ast=lambda ast: (() if by_ast[id(ast)] is None
                                    else by_ast[id(ast)].envelopes),
        task_scope=tuple(item.task for item in source_rows),
        source_frontier=tuple(item.frontier for item in source_rows),
        eligibility_policy=tuple(item.policy for item in source_rows),
        semantic_context=authenticated,
        released_manifest=tuple(getattr(item, "manifest", manifest) for item in source_rows),
        generation_binding=generation_binding,
        atlas_selection=authenticated.selection,
        prepared_model_sources=prepared_model_sources)


def prepare_factory_training_batch(
    source_context: SourceExecutionContext,
    candidate: BamfBundleCandidate,
    atlas_artifact_path: str,
    feature_artifact_path: str,
    delivered_rows,
    generation_binding: str,
    *,
    capability: str,
    delivery: DeliveredTeaching,
    requested_count: int,
    source_seed: int,
    source_each: int,
    optimizer_step_seed: int = 0,
    visit_provenance: BamfVisitProvenance,
    teacher_strategy: dict,
    rehearsal_by_id: dict | None = None,
    rehearsal_bindings: dict | None = None,
    rehearsal_authorities: dict | None = None,
    semantic_context=None,
    prepared_source=None,
) -> PreparedFactoryTrainingBatch:
    """Compile one real Factory draw once, then bind each C02 row into B11.

    The bridge owns composition only. A05/A06/A13 remain source authority, B11
    remains the neural owner, and C16 remains the durable-student launch owner.
    """
    rows = _validated_training_request(
        source_context, candidate, delivered_rows, generation_binding,
        capability=capability, delivery=delivery, requested_count=requested_count,
        source_seed=source_seed, source_each=source_each,
        optimizer_step_seed=optimizer_step_seed,
        visit_provenance=visit_provenance, teacher_strategy=teacher_strategy,
        rehearsal_by_id=rehearsal_by_id)
    authenticated = semantic_context
    if authenticated is None:
        authenticated = authenticate_bamf_execution_feature_context(
            candidate, atlas_artifact_path, source_context.run_dir)
    elif type(authenticated) is not AuthenticatedGenerationFeatureContext:
        _invalid("FACTORY_TRAINING_SEMANTIC_CONTEXT_INVALID")
    authenticated.__post_init__()
    (source_authority, _adapter, manifest, profile, source_rows,
     prepared_model_sources, prepared_motif_inputs,
     prepared_b11_sources) = _prepared_source_inputs(
        prepared_source, source_context, authenticated, rows,
        capability=capability, source_seed=source_seed, source_each=source_each,
        delivery=delivery, rehearsal_by_id=rehearsal_by_id,
        rehearsal_bindings=rehearsal_bindings,
        rehearsal_authorities=rehearsal_authorities)
    training = _compile_factory_training(
        rows, source_context, candidate, delivery, capability, teacher_strategy,
        requested_count, optimizer_step_seed, visit_provenance, source_authority,
        rehearsal_by_id, rehearsal_authorities, source_rows,
        feature_artifact_path, generation_binding,
        authenticated, manifest, prepared_model_sources)
    compiled_rows = _bind_b11_rows(
        source_context, candidate, authenticated, training, source_rows,
        profile, source_seed=source_seed, source_each=source_each,
        prepared_b11=prepared_b11_sources)
    motif_inputs = (
        prepared_motif_inputs if prepared_motif_inputs is not None else
        tuple(_motif_planning_input(
            source_context, authenticated, item.source_adapter, item.profile, item,
            source_seed=item.source_seed, source_each=item.source_each)
            for item in source_rows))
    prepared = PreparedFactoryTrainingBatch(
        training, compiled_rows, motif_inputs, authenticated)
    prepared.__post_init__()
    return prepared


__all__ = ("PreparedFactoryTrainingBatch", "prepare_factory_training_batch")
