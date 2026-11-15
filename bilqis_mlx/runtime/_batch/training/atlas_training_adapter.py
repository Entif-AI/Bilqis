"""Release-bound, source-visible BAMF input preparation."""
from __future__ import annotations

from dataclasses import asdict, replace
from graphlib import CycleError, TopologicalSorter
from typing import Callable

from bilqis_mlx.runtime.source_execution import (
    SourceBatchAuthority, SourceExecutionContext, source_content_digest,
)
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.factory.teaching import DeliveredTeaching, content_digest
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.cognitive_dependencies import (
    DependencyKind, DependencyRef,
)
from bilqis_mlx.semantics.frame_compiler import (
    FrameCompilerConfig, compile_prefix,
)
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, ContextEligibility, ContextPolicy,
    SourceFrontier, TaskScope, project_context,
)
from bilqis_mlx.semantics.domains import contract_digest
from .atlas_training_contracts import (
    BamfModelInput, BamfTarget, BamfDeliveryProvenance,
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


def _answer_plan(plan, head, visible_end, generation_binding):
    fields = {'modalityID', 'input_prefix_end', 'decisions', 'allowedOutputSchema',
              'maximum_decisions', 'generation_binding'}
    decision_fields = {'id', 'roleID', 'occurrence', 'kind', 'legalValues', 'depends_on'}
    if (not isinstance(plan, dict) or set(plan) != fields or plan['modalityID'] != head.modality_id
            or type(plan['input_prefix_end']) is not int or not 0 <= plan['input_prefix_end'] <= visible_end
            or type(plan['maximum_decisions']) is not int or not 1 <= plan['maximum_decisions'] <= 64
            or not isinstance(plan['decisions'], (list, tuple)) or not plan['decisions']
            or len(plan['decisions']) > plan['maximum_decisions']
            or not plan['allowedOutputSchema'] or plan['generation_binding'] != generation_binding):
        _invalid('ANSWER_PLAN_INVALID')
    graph = {}
    for decision in plan['decisions']:
        if (not isinstance(decision, dict) or set(decision) != decision_fields
                or not isinstance(decision['id'], str) or not decision['id']
                or not isinstance(decision['roleID'], str) or not decision['roleID']
                or type(decision['occurrence']) is not int or decision['occurrence'] < 0
                or decision['kind'] not in (
                    'VALUE', 'ROLE', 'CONTROL', 'EPISTEMIC', 'OPERATOR', 'OPERAND')
                or not isinstance(decision['legalValues'], (list, tuple)) or not decision['legalValues']
                or not isinstance(decision['depends_on'], (list, tuple))
                or any(not isinstance(dep, str) or not dep for dep in decision['depends_on'])
                or decision['id'] in graph):
            _invalid('ANSWER_PLAN_INVALID')
        graph[decision['id']] = tuple(decision['depends_on'])
    if any(dep not in graph for deps in graph.values() for dep in deps):
        _invalid('ANSWER_PLAN_INVALID')
    try:
        tuple(TopologicalSorter(graph).static_order())
    except CycleError:
        _invalid('ANSWER_PLAN_INVALID')
    return _freeze(plan)


def _require_semantic_authority(
        compiler_config, task_scope, source_frontier, eligibility_policy,
        atlas_selection, feature_artifact_path, semantic_context=None,
        released_manifest=None):
    return _require_semantic_authority_impl(
        compiler_config, task_scope, source_frontier, eligibility_policy,
        atlas_selection, feature_artifact_path, rederive_training_authority,
        semantic_context, released_manifest)


def _compile_model_input(
        row, capability: str, visible: tuple, *, source_context, capabilities, heads,
        source_ast_for: Callable, frames_for_ast: Callable, task_scope: TaskScope, source_frontier: SourceFrontier,
        eligibility_policy: ContextPolicy, compiler_config: FrameCompilerConfig,
        atlas_selection, feature_artifact_path,
        answer_plan_for: Callable, generation_binding: str,
        atlas_features: AtlasFeatures | None, semantic_context=None,
        released_manifest=None) -> tuple:
    kind, gold = row.get('answer_kind', 'binary'), row.get('gold')
    families = {family.kind: family.values for family in capabilities[capability].answer_families}
    if not isinstance(kind, str) or kind not in families or kind not in heads:
        _invalid('ANSWER_NOT_RELEASED')
    source_context.answer_registry.require(kind)
    head = heads[kind]
    ast = source_ast_for(visible)
    frames = frames_for_ast(ast)
    if (type(frames) is not tuple or
            any(type(frame) is not ContextEligibility for frame in frames)):
        _invalid('CONTEXT_SOURCE_FRAMES_REQUIRED')
    if not frames and getattr(ast, 'frames', ()):
        _invalid('CONTEXT_SOURCE_FRAMES_REQUIRED')
    _require_source_inventory(
        ast, source_context, row, atlas_selection, semantic_context,
        released_manifest)
    _require_source_lineage(ast, frames, visible, source_context.graph)
    projection = None
    if frames:
        projection = project_context(frames, task_scope, source_frontier, eligibility_policy)
        if type(projection) is not ApprovedContextProjection:
            _invalid('CONTEXT_NOT_ELIGIBLE')
    current_features = _require_semantic_authority(
        compiler_config, task_scope, source_frontier, eligibility_policy,
        atlas_selection, feature_artifact_path, semantic_context,
        released_manifest)
    if atlas_features is None:
        atlas_features = current_features
    elif current_features != atlas_features:
        _invalid('UPSTREAM_SEMANTIC_AUTHORITY_MISMATCH')
    prefix = compile_prefix(
        ast, len(visible), task_scope.semantic_release,
        compiler_config if projection is None
        else replace(compiler_config, approved=projection))
    features = (() if projection is None
                else _source_features(projection, atlas_features, atlas_selection))
    eligibility_digest = (projection.digest if projection is not None else contract_digest({
        'schema': 'bilqis.mlx.c02-atomic-eligibility/v1',
        'task': asdict(task_scope), 'frontier': asdict(source_frontier),
        'policy': asdict(eligibility_policy),
        'source_instance_id': ast.source_instance_id,
        'visible_end': len(visible),
    }))
    plan = _answer_plan(answer_plan_for(
        prefix, source_context.release, capabilities[capability], kind),
        head, len(visible), generation_binding)
    model_input = BamfModelInput(prefix, features, eligibility_digest, plan)
    return kind, gold, families, head, plan, model_input, atlas_features

def _compile_target(row, *, kind, gold, families, head, plan) -> BamfTarget:
    """Compile only released registry-owned scalar modalities.

    B10 structured route supervision is derived later from FactoryTaskAuthority;
    callers cannot inject target encoders at this boundary.
    """
    if (not isinstance(gold, str) or gold not in families[kind]
            or gold not in head.values):
        _invalid('ANSWER_NOT_RELEASED')
    return BamfTarget(kind, gold, head.token_ids[head.values.index(gold)], True)

def _compile_native_target(row, *, kind: str, gold, head, source_context: SourceExecutionContext):
    native = row.get('native_output')
    if kind.startswith('numeric_') and native is None:
        _invalid('NATIVE_TARGET_REQUIRED')
    if native is None:
        return None
    if not isinstance(gold, str) or gold not in head.values:
        _invalid('NATIVE_TARGET_MISMATCH')
    native_token_id = head.token_ids[head.values.index(gold)]
    if (not isinstance(native, dict) or native.get('token_id') != native_token_id or
            native.get('identity') != source_context.graph['tokens'][native_token_id]):
        _invalid('NATIVE_TARGET_MISMATCH')
    return BamfTarget('semantic_token', native['identity'], native['token_id'], True)


def source_prefix_dependencies(
    row_id: str,
    source_id: str | None,
    operation_id: str | None,
    prefix,
) -> tuple[DependencyRef, ...]:
    """Derive C09 inputs from the source-owned row and exact A05 prefix."""
    dependencies = {
        DependencyRef(DependencyKind.SOURCE, row_id),
        DependencyRef(
            DependencyKind.RELEASE,
            "release:" + prefix.semantic_release),
        DependencyRef(
            DependencyKind.POLICY,
            "policy:" + contract_digest((
                prefix.scope, prefix.policy_version[0], prefix.policy_version[1]))),
        DependencyRef(
            DependencyKind.RIGHTS,
            "rights:" + contract_digest((
                prefix.policy_version[2], prefix.policy_version[3]))),
    }
    if source_id is not None:
        dependencies.add(DependencyRef(DependencyKind.SOURCE, source_id))
    if operation_id is not None:
        dependencies.add(DependencyRef(
            DependencyKind.OPERATOR, "operator:" + operation_id))
    if prefix.context_digest is not None:
        dependencies.add(DependencyRef(
            DependencyKind.TIME,
            "time:asof:context:" + prefix.context_digest))
    return tuple(sorted(dependencies))


def _row_immediate_dependencies(row_id, source_id, operation_id, model_input):
    """Freeze the exact C09 inputs while C02 still owns their authority."""
    return source_prefix_dependencies(row_id, source_id, operation_id, model_input.prefix)


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
                           semantic_context=None, released_manifest=None) -> BamfTrainingBatch:
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
            released_manifest=released_manifest)
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
        provenance = replace(
            provenance,
            immediate_dependencies=_row_immediate_dependencies(
                identity, source_id, operation_id, model_input))
        result.append(BamfTrainingRow(model_input, target, native_target, provenance))
    return _issue_training_batch(
        release.release_sha256, generation_binding, content_digest(delivered_rows),
        delivery_capability, tuple(result))
