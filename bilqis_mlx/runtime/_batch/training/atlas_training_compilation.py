"""Candidate-bound compilation helpers for Atlas training rows."""
from __future__ import annotations

from dataclasses import dataclass
from graphlib import CycleError, TopologicalSorter

from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind, DependencyRef
from bilqis_mlx.semantics.domains import contract_digest

from .atlas_training_contracts import BamfModelInput, BamfTarget, _freeze, _invalid


@dataclass(frozen=True)
class PreparedModelSourceInput:
    """Candidate-independent C02 source/formal/prefix compilation."""

    row_id: str
    visible: tuple
    prefix: object
    features: tuple
    eligibility_digest: str

    def __post_init__(self):
        if (not isinstance(self.row_id, str) or not self.row_id
                or type(self.visible) is not tuple
                or type(self.features) is not tuple
                or not isinstance(self.eligibility_digest, str)
                or not self.eligibility_digest):
            _invalid("PREPARED_SOURCE_MODEL_INPUT_INVALID")
        self.prefix.__post_init__()


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


def _answer_contract(row, capability, capabilities, heads, source_context):
    kind, gold = row.get("answer_kind", "binary"), row.get("gold")
    families = {
        family.kind: family.values
        for family in capabilities[capability].answer_families
    }
    if not isinstance(kind, str) or kind not in families or kind not in heads:
        _invalid("ANSWER_NOT_RELEASED")
    source_context.answer_registry.require(kind)
    return kind, gold, families, heads[kind]


def _compile_model_input(
        row, capability: str, visible: tuple, *, source_context, capabilities, heads,
        source_ast_for, frames_for_ast, task_scope, source_frontier,
        eligibility_policy, compiler_config, atlas_selection, feature_artifact_path,
        answer_plan_for, generation_binding: str, atlas_features,
        prepare_source_input, semantic_context=None, released_manifest=None,
        prepared_source=None) -> tuple:
    kind, gold, families, head = _answer_contract(
        row, capability, capabilities, heads, source_context)
    if prepared_source is None:
        ast = source_ast_for(visible)
        frames = frames_for_ast(ast)
        prepared_source, atlas_features = prepare_source_input(
            row, capability, visible, source_context=source_context,
            source_ast=ast, frames=frames, task_scope=task_scope,
            source_frontier=source_frontier, eligibility_policy=eligibility_policy,
            compiler_config=compiler_config, atlas_selection=atlas_selection,
            feature_artifact_path=feature_artifact_path,
            semantic_context=semantic_context, released_manifest=released_manifest,
            atlas_features=atlas_features)
    elif (type(prepared_source) is not PreparedModelSourceInput
          or prepared_source.row_id != row.get("id")
          or prepared_source.visible != visible):
        _invalid("PREPARED_SOURCE_MODEL_INPUT_INVALID")
    else:
        prepared_source.__post_init__()
    prefix = prepared_source.prefix
    plan = _answer_plan(answer_plan_for(
        prefix, source_context.release, capabilities[capability], kind),
        head, len(visible), generation_binding)
    model_input = BamfModelInput(
        prefix, prepared_source.features, prepared_source.eligibility_digest, plan)
    return kind, gold, families, head, plan, model_input, atlas_features


def _compile_target(row, *, kind, gold, families, head, plan) -> BamfTarget:
    """Compile only released registry-owned scalar modalities."""
    if (not isinstance(gold, str) or gold not in families[kind]
            or gold not in head.values):
        _invalid('ANSWER_NOT_RELEASED')
    return BamfTarget(kind, gold, head.token_ids[head.values.index(gold)], True)


def _compile_native_target(row, *, kind: str, gold, head,
                           source_context: SourceExecutionContext):
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


def _prepared_sources(prepared_model_sources, row_count):
    if prepared_model_sources is None:
        return None
    if (type(prepared_model_sources) is not tuple
            or len(prepared_model_sources) != row_count
            or any(type(item) is not PreparedModelSourceInput
                   for item in prepared_model_sources)):
        _invalid("PREPARED_SOURCE_MODEL_INPUT_INVALID")
    return prepared_model_sources


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
