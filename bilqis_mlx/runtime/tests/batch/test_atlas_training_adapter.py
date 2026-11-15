"""Provisional Factory-to-BAMF contract witnesses; no neural state is used."""
from dataclasses import replace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.adapters import SourceAdapterRegistry
from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.execution import CurriculumProfile
from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.factory.tests.test_teaching import closed_source_fixture
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.runtime.atlas_training_adapter import (
    BamfTarget, PreparedModelSourceInput, compile_training_batch,
    require_current_release,
)
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import visit_provenance
from bilqis_mlx.semantics.atlas_features import AtlasFeatures, ConceptFeature
from bilqis_mlx.semantics.core import Literal
from bilqis_mlx.semantics.context_eligibility import (
    PUBLIC_FORMAL, ContextEligibility, ContextMember, ContextPolicy,
    SourceFrontier, SourceGrant, TaskScope, frame_evidence_digest,
    member_evidence_digest,
)
from bilqis_mlx.semantics.cognitive_dependencies import (
    DependencyKind, DependencyRef,
)
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.semantics.frame_codec import SchemaTagMap
from bilqis_mlx.semantics.frame_compiler import (
    FrameCompilerConfig, SourceAtom, StreamingAST, atom_evidence_digest,
)
from bilqis_mlx.semantics.frame_schema import (
    ConceptRef, FrameSchema, FrameTree, RoleOccurrence, RoleSpec, SourceSpan,
    make_frame_instance,
)


def _source_context(rows, release, visible_ends, policy_mode, graph=None):
    """Issue real A13 synthetic source grants for the actual visible ASTs."""
    principal, tenant = "synthetic:person", "synthetic:tenant"
    region, scope = "synthetic:region", "synthetic:task"
    semantic_release = '0' * 64
    policy_epoch = 1
    envelopes = {}
    grants = {}
    for row in rows:
        tokens = row.get("tokens", ())
        end = visible_ends.get(
            row.get("id"), len(tokens) if isinstance(tokens, (tuple, list)) else 0)
        if not isinstance(tokens, (tuple, list)) or not 0 < end <= len(tokens):
            continue
        ast = source_ast_for(tuple(tokens[:end]), release, graph)
        if ast.source_instance_id in envelopes:
            continue
        identity = ast.source_instance_id
        frame = ast.frames[0].root
        member = ContextMember(
            "subject", 0, "source:member:" + ast.source_instance_id, end)
        frame_source = "source:frame:" + ast.source_instance_id
        evidence = (
            (frame_source, frame_evidence_digest(frame)),
            (member.source_handle, member_evidence_digest(frame, member)),
            *((atom.source_reference,
               atom_evidence_digest(ast.source_instance_id, atom, semantic_release))
              for atom in ast.atoms[:end]),
        )
        for handle, digest in evidence:
            grants[handle] = SourceGrant(
                handle, principal, tenant, PUBLIC_FORMAL, semantic_release, digest,
                ("TRAINING",), (region,), (scope,),
                rights_epoch=1, correction_generation=1,
                observed_at=2, effective_from=0)
        envelopes[identity] = ContextEligibility(
            frame_handle="frame:" + identity, frame=frame,
            source_handle=frame_source, members=(member,),
            principal_id=principal, tenant_id=tenant,
            purpose="TRAINING", source_regime=PUBLIC_FORMAL,
            semantic_release=semantic_release, jurisdiction=region,
            scope=scope, join_class=PUBLIC_FORMAL,
            policy_epoch=policy_epoch, rights_epoch=1,
            correction_generation=1, observed_at=2,
            effective_from=0, effective_until=None,
            causal_prefix_end=end)
    prefix = max((item.causal_prefix_end for item in envelopes.values()), default=1)
    task = TaskScope(
        principal, tenant, "TRAINING", semantic_release, region, scope,
        observed_frontier=3, effective_time=5, causal_prefix_end=prefix)
    allowed_purposes = ("TRAINING",) if policy_mode == "allow" else ("SERVING",)
    policy = ContextPolicy(
        "synthetic:policy", policy_epoch, 1,
        allowed_purposes, (PUBLIC_FORMAL,), (region,), (scope,),
        (PUBLIC_FORMAL,), ((PUBLIC_FORMAL, PUBLIC_FORMAL),),
        ((PUBLIC_FORMAL, PUBLIC_FORMAL, PUBLIC_FORMAL),))
    frontier = SourceFrontier(
        1, 1, tuple(sorted(grants.values(), key=lambda item: item.source_handle)))
    def frames_for_ast(ast):
        item = envelopes.get(ast.source_instance_id)
        return (item,) if item is not None else ()
    return frames_for_ast, task, frontier, policy


def _training_schema():
    return FrameSchema(
        'fixture:training-frame', 1, 'source:factory-fixture',
        (RoleSpec('subject', ('Entity',), 1, 1),),
        'ORDERED', 'synthetic')


def source_ast_for(tokens, release='fixture-release', graph=None):
    value = ','.join(str(token) for token in tokens)
    source_instance_id = 'synthetic:ast:' + value
    token_names = (
        graph.get('tokens') if isinstance(graph, dict)
        and isinstance(graph.get('tokens'), list) else
        ['fixture.padding', 'cogal.value.false', 'cogal.value.true'])
    atoms = tuple(
        SourceAtom(index, token_names[token], f'{source_instance_id}#atom:{index}')
        for index, token in enumerate(tokens))
    schema = _training_schema()
    frame = make_frame_instance(
        schema,
        source_instance_id=source_instance_id,
        structural_path=(),
        source_span=SourceSpan(0, len(tokens)),
        parent_occurrence_id=None,
        bindings=(RoleOccurrence(
            'subject', 0, concept=ConceptRef(
                'fixture:entity:' + value, '0' * 64, 0,
                ('Entity',), source_instance_id)),),
        causal_prefix_end=len(tokens))
    return StreamingAST(source_instance_id, atoms, (FrameTree(frame),))


def answer_plan_for(prefix, release, capability, kind):
    head = next(head for head in release.answer_heads if head.kind == kind)
    return {'modalityID': head.modality_id, 'input_prefix_end': prefix.visible_end,
            'decisions': [{'id': 'value', 'roleID': 'answer', 'occurrence': 0,
                           'kind': 'VALUE', 'legalValues': list(head.values), 'depends_on': []},
                          {'id': 'end', 'roleID': 'end', 'occurrence': 0,
                           'kind': 'CONTROL', 'legalValues': ['END_FRAME'], 'depends_on': ['value']}],
            'allowedOutputSchema': 'fixture', 'maximum_decisions': 2,
            'generation_binding': release.release_sha256}


def _atlas_features(asts: tuple[StreamingAST, ...], semantic_release: str) -> AtlasFeatures:
    concepts = {}
    for ast in asts:
        for tree in ast.frames:
            frame = tree.root
            if not hasattr(frame, 'bindings'):
                continue
            for binding in frame.bindings:
                candidates = ((binding.concept,) if binding.concept is not None
                              else binding.alternatives)
                for concept in candidates:
                    concepts[concept.semantic_id] = ConceptFeature(
                        concept.semantic_id, concept.abi_index, concept.type_ids,
                        (0.0,) * 64, 'ADMITTED_SOURCE')
    return AtlasFeatures(
        semantic_release, 'fixture:atlas', 'fixture:source', None,
        (('Entity', 2),), (('subject', 2),),
        (('fixture:training-frame', 2),),
        tuple(concepts[key] for key in sorted(concepts)), ())


class AtlasTrainingAdapterTest(unittest.TestCase):
    def setUp(self):
        course, graph, sources, answers, _ = closed_source_fixture()
        registered = sources.require('fixture.z-generator/v1', 'fixture.z-oracle/v1')
        def draw(**kwargs):
            return tuple({**row, 'source_id': 'source-1', 'source_family_id': 'family-1', 'episode_id': 'episode-1', 'tokens': [1, 2, 1]}
                         for row in registered.draw(**kwargs))
        def check(row, **kwargs):
            gold = row.get('gold')
            if isinstance(gold, dict):
                return gold == {'decisions': ['FALSE', 'END_FRAME']}
            return registered.check(row, **kwargs)
        sources = SourceAdapterRegistry((replace(registered, draw=draw, check=check),))
        curriculum, bindings = from_legacy_course(course)
        release = compile_executable_factory_release(curriculum, bindings, CurriculumProfile.full(),
            sources, answers, source_root=None, graph=graph, verification_seed=17)
        self.context = SourceExecutionContext(release, graph, None, sources, answers)
        self.model_generation = 'fixture-model-generation'
        self.rows = self.context.draw_rows(seed=17, capability='Z.C0', each=1)

    def source_owned_context(self, rows, *, seed=17):
        """Bind deliberate fixture variants as rows emitted by the source owner."""
        registered = self.context.source_registry.require(
            'fixture.z-generator/v1', 'fixture.z-oracle/v1')
        owned = tuple(dict(row) for row in rows)

        def draw(**kwargs):
            if (kwargs.get('capability') == 'Z.C0'
                    and kwargs.get('seed') == seed
                    and kwargs.get('each') == len(owned)):
                return owned
            return registered.draw(**kwargs)

        registry = SourceAdapterRegistry((replace(registered, draw=draw),))
        return replace(self.context, source_registry=registry)

    def compile(self, rows, *, release_sha=None, policy='allow',
                generation=None, sealed=(), context_mutator=None,
                frames_override=None, source_ast_override=None,
                delivery_override=None, extra_kwargs=None,
                source_context=None, source_seed=17, visit=None,
                optimizer_step_seed=42):
        context = source_context or self.context
        delivery = delivery_override or describe_delivered_teaching(
            context.release, 'Z.C0', 'source.direct/Z.C0', rows)
        visible_ends = {rows[0]['id']: 2}
        frames_for_ast, base_task, base_frontier, base_policy = _source_context(
            rows, context.release.release_sha256, visible_ends, policy,
            context.graph)
        task, frontier, context_policy = base_task, base_frontier, base_policy
        if context_mutator is not None:
            task, frontier, context_policy = context_mutator(
                task, frontier, context_policy)
        if frames_override is not None:
            frames_for_ast = frames_override
        legitimate_asts = tuple(source_ast_for(
            tuple(row['tokens'][:visible_ends.get(row['id'], len(row['tokens']))]),
            context.release.release_sha256, context.graph)
            for row in rows)
        inventories = {
            row['id']: (ast.source_instance_id, ast.frames)
            for row, ast in zip(rows, legitimate_asts)
        }
        schema = _training_schema()
        semantic_release = base_task.semantic_release
        compiler_config = FrameCompilerConfig(
            (schema,), SchemaTagMap.from_schemas(semantic_release, (schema,)),
            None,
            base_task, base_frontier, base_policy)
        # Synthetic factory fixtures have neither a source-pinned A01 artifact
        # nor a production source-frame inventory. Keep both substitutions
        # scoped to this compilation so one fixture can never leak authority
        # into a later repository test.
        with patch(
                'bilqis_mlx.runtime.atlas_training_adapter.rederive_training_authority',
                return_value=_atlas_features(legitimate_asts, semantic_release)), patch(
                    'bilqis_mlx.runtime.training_input_authority.source_frame_inventory',
                    side_effect=lambda _context, row, _selection:
                        inventories[row['id']]):
            return compile_training_batch(rows, context, ModelTopologySpecV2(),
                delivery=delivery, delivery_capability='Z.C0', delivery_release_sha256=release_sha or context.release.release_sha256,
                teacher_strategy={'policy': 'focused'}, requested_count=3,
                optimizer_step_seed=optimizer_step_seed,
                visit_provenance=(visit or visit_provenance('Z.C0')),
                source_authority=context.bind_rows(
                    rows, seed=source_seed, capability='Z.C0', each=len(rows)),
                rehearsal_by_id={rows[0]['id']: 'prior'}, visible_ends=visible_ends,
                source_ast_for=source_ast_override or (
                    lambda tokens: source_ast_for(
                        tokens, context.release.release_sha256,
                        context.graph)),
                compiler_config=compiler_config,
                feature_artifact_path='synthetic:feature-artifact',
                answer_plan_for=lambda *args: {**answer_plan_for(*args), 'generation_binding': self.model_generation},
                frames_for_ast=frames_for_ast, task_scope=task,
                source_frontier=frontier, eligibility_policy=context_policy,
                generation_binding=generation or self.model_generation,
                sealed_holdout_ids=sealed, **(extra_kwargs or {}))

    def test_prepared_source_prefix_is_reused_while_step_provenance_changes(self):
        first = self.compile(self.rows, optimizer_step_seed=42)
        model = first.rows[0].model_input
        prepared = PreparedModelSourceInput(
            self.rows[0]['id'], (1, 2), model.prefix,
            model.features, model.eligibility_digest)
        with patch(
                'bilqis_mlx.runtime.atlas_training_adapter.compile_prefix',
                side_effect=AssertionError('candidate step rebuilt source prefix')):
            identical = self.compile(
                self.rows, optimizer_step_seed=42,
                extra_kwargs={'prepared_model_sources': (prepared,)})
            second = self.compile(
                self.rows, optimizer_step_seed=43,
                extra_kwargs={'prepared_model_sources': (prepared,)})
        self.assertEqual(identical, first)
        self.assertIs(second.rows[0].model_input.prefix, model.prefix)
        self.assertEqual(first.rows[0].provenance.optimizer_step_seed, 42)
        self.assertEqual(second.rows[0].provenance.optimizer_step_seed, 43)
        self.assertEqual(
            first.rows[0].provenance.source_row_content_sha256,
            second.rows[0].provenance.source_row_content_sha256)

    def test_cross_source_ast_and_frame_substitution_is_rejected(self):
        def forged_ast(tokens):
            return replace(
                source_ast_for(
                    tokens, self.context.release.release_sha256,
                    self.context.graph),
                source_instance_id='synthetic:other-source')
        with self.assertRaises(BilqisError):
            self.compile(self.rows, source_ast_override=forged_ast)

    def test_same_source_id_with_forged_ast_semantics_is_rejected(self):
        legitimate = source_ast_for(
            (1, 2), self.context.release.release_sha256, self.context.graph)
        forged = replace(
            legitimate,
            atoms=(
                SourceAtom(0, 'fixture.token.FORGED', legitimate.atoms[0].source_reference),
                legitimate.atoms[1],
            ))
        with self.assertRaises(BilqisError):
            self.compile(
                self.rows,
                source_ast_override=lambda _tokens: forged,
                frames_override=lambda _ast: _source_context(
                    self.rows,
                    self.context.release.release_sha256,
                    {self.rows[0]['id']: 2},
                    'allow', self.context.graph)[0](legitimate))

    def test_same_source_ast_with_forged_source_reference_is_rejected(self):
        legitimate = source_ast_for(
            (1, 2), self.context.release.release_sha256, self.context.graph)
        forged = replace(
            legitimate,
            atoms=(
                replace(legitimate.atoms[0], source_reference='forged:atom:0'),
                legitimate.atoms[1],
            ))
        with self.assertRaises(BilqisError):
            self.compile(
                self.rows,
                source_ast_override=lambda _tokens: forged,
                frames_override=lambda _ast: _source_context(
                    self.rows,
                    self.context.release.release_sha256,
                    {self.rows[0]['id']: 2},
                    'allow', self.context.graph)[0](legitimate))

    def test_caller_cannot_supply_prefix_or_feature_authority(self):
        with self.assertRaises(TypeError):
            self.compile(
                self.rows,
                extra_kwargs={'compile_prefix': lambda *_args: object()})

    def test_training_provenance_preserves_immediate_c09_dependencies(self):
        rows = ({**self.rows[0], 'operation_id': 'fixture.operator'},)
        context = self.source_owned_context(rows)
        batch = self.compile(rows, source_context=context)
        row = batch.rows[0]
        prefix = row.model_input.prefix
        expected = {
            DependencyRef(DependencyKind.SOURCE, row.provenance.row_id),
            DependencyRef(DependencyKind.SOURCE, row.provenance.source_id),
            DependencyRef(
                DependencyKind.OPERATOR, 'operator:fixture.operator'),
            DependencyRef(
                DependencyKind.RELEASE,
                'release:' + prefix.semantic_release),
            DependencyRef(
                DependencyKind.POLICY,
                'policy:' + contract_digest((
                    prefix.scope,
                    prefix.policy_version[0],
                    prefix.policy_version[1],
                ))),
            DependencyRef(
                DependencyKind.RIGHTS,
                'rights:' + contract_digest((
                    prefix.policy_version[2],
                    prefix.policy_version[3],
                ))),
            DependencyRef(
                DependencyKind.TIME,
                'time:asof:context:' + prefix.context_digest),
        }
        self.assertEqual(set(row.provenance.immediate_dependencies), expected)
        with self.assertRaises(TypeError):
            self.compile(
                self.rows,
                extra_kwargs={'features_for': lambda *_args: ('forged',)})
