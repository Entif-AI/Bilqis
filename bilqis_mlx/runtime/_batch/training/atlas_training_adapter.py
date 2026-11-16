"""Release-bound, source-visible BAMF input preparation."""
from __future__ import annotations

from dataclasses import asdict, replace
from typing import Callable

from bilqis_mlx.runtime.source_execution import (
    SourceBatchAuthority, SourceExecutionContext, source_content_digest,
)
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.factory.teaching import DeliveredTeaching, content_digest
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.frame_compiler import (
    FrameCompilerConfig, compile_prefix,
)
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, ContextEligibility, ContextPolicy,
    SourceFrontier, TaskScope, project_context,
)
from bilqis_mlx.semantics.domains import contract_digest
from .atlas_training_contracts import (
    BamfTarget, BamfDeliveryProvenance,
    BamfTrainingRow, BamfTrainingBatch, BamfVisitProvenance, PaddedMicrobatch,
    _invalid, _freeze, _issue_training_batch, require_current_release,
)
from .batch_training_authority import rederive_training_authority
from .training_input_authority import (
    require_semantic_authority as _require_semantic_authority_impl,
    require_source_lineage as _require_source_lineage,
    require_source_inventory as _require_source_inventory,
    row_contexts as _row_contexts,
    source_features as _source_features,
)
from .training_request import (
    require_compile_request as _require_compile_request,
    row_source_inputs as _row_source_inputs,
)
from .atlas_training_delivery import (
    pad_microbatches, attach_auxiliaries, execute_with_backend,
    capture_realized_delivery, require_independent_cohorts, resolve_batch_rules,
)
from .atlas_training_compilation import (
    PreparedModelSourceInput, _compile_model_input, _compile_native_target,
    _compile_target, _prepared_sources, _row_immediate_dependencies,
    source_prefix_dependencies,
)


def prepare_model_source_input(
        row, capability: str, visible: tuple, *, source_context,
        source_ast, frames: tuple, task_scope: TaskScope,
        source_frontier: SourceFrontier, eligibility_policy: ContextPolicy,
        compiler_config: FrameCompilerConfig, atlas_selection,
        feature_artifact_path, semantic_context=None, released_manifest=None,
        atlas_features: AtlasFeatures | None = None):
    """Compile source-owned model context once, excluding candidate generation."""
    if (not isinstance(row, dict) or row.get("capability") != capability
            or type(visible) is not tuple):
        _invalid("PREPARED_SOURCE_MODEL_INPUT_INVALID")
    if (type(frames) is not tuple
            or any(type(frame) is not ContextEligibility for frame in frames)):
        _invalid("CONTEXT_SOURCE_FRAMES_REQUIRED")
    if not frames and getattr(source_ast, "frames", ()):
        _invalid("CONTEXT_SOURCE_FRAMES_REQUIRED")
    _require_source_inventory(
        source_ast, source_context, row, atlas_selection, semantic_context,
        released_manifest)
    _require_source_lineage(source_ast, frames, visible, source_context.graph)
    projection = None
    if frames:
        projection = project_context(
            frames, task_scope, source_frontier, eligibility_policy)
        if type(projection) is not ApprovedContextProjection:
            _invalid("CONTEXT_NOT_ELIGIBLE")
    current_features = _require_semantic_authority(
        compiler_config, task_scope, source_frontier, eligibility_policy,
        atlas_selection, feature_artifact_path, semantic_context,
        released_manifest)
    if atlas_features is None:
        atlas_features = current_features
    elif current_features != atlas_features:
        _invalid("UPSTREAM_SEMANTIC_AUTHORITY_MISMATCH")
    prefix = compile_prefix(
        source_ast, len(visible), task_scope.semantic_release,
        compiler_config if projection is None
        else replace(compiler_config, approved=projection))
    features = (() if projection is None
                else _source_features(projection, atlas_features, atlas_selection))
    eligibility_digest = (
        projection.digest if projection is not None else contract_digest({
            "schema": "bilqis.mlx.c02-atomic-eligibility/v1",
            "task": asdict(task_scope), "frontier": asdict(source_frontier),
            "policy": asdict(eligibility_policy),
            "source_instance_id": source_ast.source_instance_id,
            "visible_end": len(visible),
        }))
    prepared = PreparedModelSourceInput(
        row["id"], visible, prefix, features, eligibility_digest)
    prepared.__post_init__()
    return prepared, atlas_features


def _require_semantic_authority(
        compiler_config, task_scope, source_frontier, eligibility_policy,
        atlas_selection, feature_artifact_path, semantic_context=None,
        released_manifest=None):
    return _require_semantic_authority_impl(
        compiler_config, task_scope, source_frontier, eligibility_policy,
        atlas_selection, feature_artifact_path, rederive_training_authority,
        semantic_context, released_manifest)


def compile_training_batch(delivered_rows, source_context: SourceExecutionContext,
                           topology, *, delivery: DeliveredTeaching, delivery_capability: str,
                           delivery_release_sha256: str, teacher_strategy: dict, requested_count: int,
                           optimizer_step_seed: int, visit_provenance: BamfVisitProvenance,
                           source_authority: SourceBatchAuthority,
                           rehearsal_by_id: dict, visible_ends: dict, source_ast_for: Callable,
                           compiler_config, feature_artifact_path, answer_plan_for: Callable,
                           frames_for_ast: Callable, task_scope: TaskScope,
                           source_frontier: SourceFrontier, eligibility_policy: ContextPolicy, generation_binding: str,
                           sealed_holdout_ids=(), atlas_selection=None,
                           semantic_context=None, released_manifest=None,
                           prepared_model_sources=None) -> BamfTrainingBatch:
    """Compile source-oracled delivery through accepted A05/A06 owners."""
    if type(topology) is not ModelTopologySpecV2:
        _invalid('TOPOLOGY_AUTHORITY_REQUIRED')
    if (type(visit_provenance) is not BamfVisitProvenance
            or visit_provenance.capability_id != delivery_capability):
        _invalid('VISIT_PROVENANCE_CAPABILITY_MISMATCH')
    release, capabilities, owner = _require_compile_request(delivered_rows, source_context,
        delivery=delivery, delivery_capability=delivery_capability,
        delivery_release_sha256=delivery_release_sha256,
        teacher_strategy=teacher_strategy, requested_count=requested_count,
        optimizer_step_seed=optimizer_step_seed, source_authority=source_authority,
        rehearsal_by_id=rehearsal_by_id,
        visible_ends=visible_ends, source_ast_for=source_ast_for, answer_plan_for=answer_plan_for,
        frames_for_ast=frames_for_ast, task_scope=task_scope, source_frontier=source_frontier,
        eligibility_policy=eligibility_policy, generation_binding=generation_binding,
        sealed_holdout_ids=sealed_holdout_ids)
    row_count = len(delivered_rows)
    prepared_model_sources = _prepared_sources(prepared_model_sources, row_count)
    compiler_configs = _row_contexts(
        compiler_config, FrameCompilerConfig, row_count,
        'UPSTREAM_SEMANTIC_AUTHORITY_MISMATCH')
    task_scopes = _row_contexts(
        task_scope, TaskScope, row_count, 'CONTEXT_AUTHORITY_REQUIRED')
    source_frontiers = _row_contexts(
        source_frontier, SourceFrontier, row_count, 'CONTEXT_AUTHORITY_REQUIRED')
    eligibility_policies = _row_contexts(
        eligibility_policy, ContextPolicy, row_count, 'CONTEXT_AUTHORITY_REQUIRED')
    atlas_features = None
    heads = {head.kind: head for head in release.answer_heads}
    result = []
    for row_index, row in enumerate(delivered_rows):
        (identity, capability, source_id, operation_id, family, episode,
         rehearsal, visible) = _row_source_inputs(
            row, row_index, capabilities=capabilities, owner=owner, delivery=delivery,
            delivery_capability=delivery_capability,
            source_context=source_context, source_authority=source_authority, rehearsal_by_id=rehearsal_by_id,
            visible_ends=visible_ends,
            sealed_holdout_ids=sealed_holdout_ids)
        (kind, gold, families, head, plan, model_input,
         atlas_features) = _compile_model_input(
            row, capability, visible, source_context=source_context,
            capabilities=capabilities, heads=heads, source_ast_for=source_ast_for, frames_for_ast=frames_for_ast,
            task_scope=task_scopes[row_index],
            source_frontier=source_frontiers[row_index],
            eligibility_policy=eligibility_policies[row_index],
            compiler_config=compiler_configs[row_index],
            atlas_selection=atlas_selection, feature_artifact_path=feature_artifact_path,
            answer_plan_for=answer_plan_for, generation_binding=generation_binding,
            atlas_features=atlas_features, semantic_context=semantic_context,
            released_manifest=released_manifest,
            prepare_source_input=prepare_model_source_input,
            prepared_source=(None if prepared_model_sources is None
                             else prepared_model_sources[row_index]))
        maximum_decisions = dict(model_input.answer_plan).get('maximum_decisions')
        if (type(maximum_decisions) is not int
                or len(model_input.prefix.positions) + maximum_decisions
                > topology.context):
            _invalid('TRAINING_CONTEXT_BUDGET_EXCEEDED')
        target = _compile_target(
            row, kind=kind, gold=gold, families=families, head=head, plan=plan)
        native_target = _compile_native_target(row, kind=kind, gold=gold, head=head,
                                               source_context=source_context)
        provenance = BamfDeliveryProvenance(identity, source_content_digest((row,)), source_id,
            capability, operation_id,
            _freeze(teacher_strategy), requested_count, len(delivered_rows), rehearsal,
            optimizer_step_seed, visit_provenance, family, episode)
        provenance = replace(provenance, immediate_dependencies=_row_immediate_dependencies(
            identity, source_id, operation_id, model_input))
        result.append(BamfTrainingRow(model_input, target, native_target, provenance))
    return _issue_training_batch(
        release.release_sha256, generation_binding, content_digest(delivered_rows),
        delivery_capability, tuple(result))
