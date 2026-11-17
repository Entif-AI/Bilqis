"""Provisional Factory-to-BAMF contract witnesses; no neural state is used."""
from dataclasses import replace
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.adapters import SourceAdapterRegistry
from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.execution import CurriculumProfile
from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.factory.tests.test_teaching import closed_source_fixture
from bilqis_mlx.runtime.atlas_training_adapter import (
    BamfTarget, PreparedModelSourceInput, compile_training_batch,
    require_current_release,
)
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import visit_provenance
from bilqis_mlx.semantics.atlas_features import AtlasFeatures, ConceptFeature
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind, DependencyRef
from bilqis_mlx.semantics.context_eligibility import (
    PUBLIC_FORMAL, ContextEligibility, ContextMember, ContextPolicy,
    SourceFrontier, SourceGrant, TaskScope, frame_evidence_digest,
    member_evidence_digest,
)
from bilqis_mlx.semantics.core import Literal
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.semantics.frame_codec import SchemaTagMap
from bilqis_mlx.semantics.frame_compiler import (
    FrameCompilerConfig, SourceAtom, StreamingAST, atom_evidence_digest,
)
from bilqis_mlx.semantics.frame_schema import (
    ConceptRef, FrameSchema, FrameTree, RoleOccurrence, RoleSpec, SourceSpan,
    make_frame_instance,
)

from .atlas_training_adapter_case import AtlasTrainingAdapterCase
from .atlas_training_fixture_support import (
    _atlas_features, _source_context, _training_schema, answer_plan_for,
    source_ast_for,
)


class AtlasTrainingAdapterTest(AtlasTrainingAdapterCase):
    def test_cross_capability_rehearsal_keeps_target_visit_and_row_authorities_distinct(self):
        target = self.context.draw_rows(seed=17, capability='Z.C2', each=1)
        support, support_authority = self.context.draw_bound_rows(
            seed=23, capability='Z.C0', each=1)
        target_authority = self.context.bind_rows(
            target, seed=17, capability='Z.C2', each=1)
        rows = (*target, *support)
        batch = self.compile(
            rows, delivery_capability='Z.C2', source_authority=target_authority,
            rehearsal_by_id={support[0]['id']: 'prior'},
            rehearsal_authorities={support[0]['id']: support_authority})

        self.assertEqual(batch.delivery_capability, 'Z.C2')
        self.assertEqual(batch.rows[0].provenance.capability_id, 'Z.C2')
        self.assertEqual(batch.rows[1].provenance.capability_id, 'Z.C0')
        self.assertEqual(batch.rows[1].provenance.visit.capability_id, 'Z.C2')
        self.assertEqual(batch.rows[1].provenance.rehearsal, 'prior')
        self.assertEqual(
            batch.rows[1].provenance.source_family_id,
            support_authority.source_family_id)

    def test_same_capability_preservation_keeps_its_own_source_authority(self):
        target = self.context.draw_rows(seed=17, capability='Z.C0', each=1)
        preservation, preservation_authority = self.context.draw_bound_rows(
            seed=23, capability='Z.C0', each=1)
        target_authority = self.context.bind_rows(
            target, seed=17, capability='Z.C0', each=1)
        rows = (*target, *preservation)
        batch = self.compile(
            rows, delivery_capability='Z.C0', source_authority=target_authority,
            rehearsal_by_id={preservation[0]['id']: 'preservation'},
            rehearsal_authorities={preservation[0]['id']: preservation_authority})

        self.assertEqual(batch.rows[1].provenance.capability_id, 'Z.C0')
        self.assertEqual(batch.rows[1].provenance.visit.capability_id, 'Z.C0')
        self.assertEqual(batch.rows[1].provenance.rehearsal, 'preservation')
        self.assertEqual(
            batch.rows[1].provenance.source_family_id,
            preservation_authority.source_family_id)

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
                SourceAtom(0, 'fixture.token.FORGED',
                           legitimate.atoms[0].source_reference),
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
                replace(legitimate.atoms[0],
                        source_reference='forged:atom:0'),
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
