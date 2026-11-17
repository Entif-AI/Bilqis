"""Disposable B13 publication with synthetic Factory and mocked lease authority.

C07 lease/source signatures and the generated-grade reader are replaced at their
boundaries; Factory compilation, current descriptor comparison, B13 issuance,
publication and cold reads use their production implementations.
"""
from contextlib import ExitStack, nullcontext
from dataclasses import asdict, dataclass, replace
from types import SimpleNamespace
import unittest
from unittest.mock import patch


from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.curriculum import BOOLEAN_OPERATORS
from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.executable_release import (
    compile_executable_factory_release, compile_successor_profile_release,
)
from bilqis_mlx.factory.execution import CapabilityProfile, CurriculumProfile, GradeProfile, _digest
from bilqis_mlx.factory.tests.executable_release.support import _answers, _boolean_answers
from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_boolean_course, _synthetic_course, _synthetic_registry
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import frozen_snapshot, source_features
from bilqis_mlx.runtime import mlx_checkpoint
from bilqis_mlx.runtime._release_adoption.native_profile import (
    adopt_profile_release, preview_profile_release,
)
from bilqis_mlx.runtime.admission import _persist_executable_factory_release
from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_factory_release
from bilqis_mlx.runtime.bamf_bundle import (
    load_bamf_generation_authority, read_accepted_generation_feature_context,
    verify_accepted_generation_feature_receipt,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.acceptance._generation_acceptance_support import GenerationAcceptanceFixture
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import publish_genesis, shape_patch


@dataclass(frozen=True)
class Approval:
    atlas_release_sha256: str
    audit_passed: bool = True
    rights_compatible: bool = True
    delta_budget_policy: object = None


@dataclass(frozen=True)
class Lease:
    source_approval: Approval

    def digest(self):
        return 'a' * 64


class NativeAdoptionTests(GenerationAcceptanceFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.graph = {'tokens': ['fixture.padding', 'cogal.value.false', 'cogal.value.true']}
        self.registry, self.answers = _synthetic_registry(), _answers()
        curriculum, bindings = from_legacy_course(_synthetic_course(6))
        profile = CurriculumProfile('reduced-z', (GradeProfile('Z', ('Z.C0', 'Z.C1')),))
        self.predecessor = compile_executable_factory_release(
            curriculum, bindings, profile, self.registry, self.answers,
            source_root=None, graph=self.graph, verification_seed=17)
        self.successor = compile_successor_profile_release(
            self.predecessor, CurriculumProfile.full(), self.registry, self.answers,
            source_root=None, graph=self.graph, verification_seed=17)

    def publish_parent(self):
        with shape_patch(), patch.object(mlx_checkpoint, 'assert_headroom'), \
             patch('bilqis_mlx.runtime.tests.operator.test_admission._executable_fixture',
                   return_value=(self.predecessor, self.graph)):
            pointer = publish_genesis(self.run)
            _persist_executable_factory_release(self.run, self.predecessor)
        return pointer

    def context_patches(self, *, real_grade=False):
        stack = ExitStack()
        stack.enter_context(shape_patch())
        stack.enter_context(patch.object(mlx_checkpoint, 'assert_headroom'))
        stack.enter_context(patch('bilqis_mlx.runtime.bamf_bundle.feature_authority.build_feature_manifest', return_value=source_features()))
        stack.enter_context(patch('bilqis_mlx.runtime.bamf_bundle.feature_authority.resolve_atlas_artifact_selection',
            side_effect=lambda identity: AtlasArtifactSelection('/fixture/atlas', identity.bundle_id,
                                                               identity.release_sha256, identity.source_bundle_id)))
        stack.enter_context(patch('bilqis_mlx.runtime.bamf_bundle.feature_authority.load_pinned_atlas_snapshot', side_effect=frozen_snapshot))
        feature = read_accepted_generation_feature_context(self.run / 'bamf-state.json')
        approval = Approval(feature.receipt.source_release_sha256, delta_budget_policy=Budget())
        lease = Lease(approval)
        cap = self.predecessor.curriculum.capability_map['Z.C0'] if 'Z.C0' in self.predecessor.execution_plan.capability_map else next(iter(self.predecessor.curriculum.capability_map.values()))
        member = SimpleNamespace(capability_id=cap.capability_id,
            semantic_id=cap.taught_roots[0],
            source_anchor=self.predecessor.source_bindings.by_capability[cap.capability_id].source_anchor)
        active = SimpleNamespace(activation_sha256='c' * 64, definition=SimpleNamespace(
            definition_sha256='b' * 64, members=(member,)))
        stack.enter_context(patch('bilqis_mlx.runtime.accepted_corrections.AcceptedRuntimeHost'))
        stack.enter_context(patch('bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_lease_v2', return_value=lease))
        stack.enter_context(patch('bilqis_mlx.runtime.atlas_admission._hold_current_atlas_lease_v2_publication', return_value=nullcontext()))
        stack.enter_context(patch('bilqis_mlx.source_adapters.school.live_source_registry', return_value=self.registry))
        stack.enter_context(patch('bilqis_mlx.factory.live_answers.live_answer_registry', return_value=self.answers))
        if not real_grade:
            stack.enter_context(patch('bilqis_mlx.runtime.active_generated_grade.read_active_generated_grade', return_value=active))
            stack.enter_context(patch('bilqis_mlx.runtime.active_generated_grade_custody._read_stored_active', return_value=active))
        return stack

    def test_publish_cold_retry_and_orphan(self):
        before = self.publish_parent()
        release_path = _persist_executable_factory_release(self.run, self.successor)
        before_bytes = (self.run / 'bamf-state.json').read_bytes()
        with self.context_patches():
            self.assertEqual(read_accepted_atlas_factory_release(self.run).release_sha256,
                             self.predecessor.release_sha256)
            parent, _ = load_bamf_generation_authority(self.run / 'bamf-state.json')
            old_receipt = read_accepted_generation_feature_context(self.run / 'bamf-state.json').receipt
            preview = preview_profile_release(self.run, self.run / release_path)
            self.assertEqual(len(preview['added_capabilities']), 4)
            self.assertEqual((self.run / 'bamf-state.json').read_bytes(), before_bytes)
            pointer = adopt_profile_release(self.run, self.successor, reserve_gib=0.)
            cold, digest = load_bamf_generation_authority(self.run / 'bamf-state.json')
            with self.assertRaises(BilqisError) as stale:
                verify_accepted_generation_feature_receipt(self.run / 'bamf-state.json', old_receipt)
            self.assertEqual(stale.exception.context['reason'], 'BAMF_FEATURE_RECEIPT_MISMATCH')
            fresh = read_accepted_generation_feature_context(self.run / 'bamf-state.json').receipt
            self.assertEqual(fresh.generation, pointer['generation'])
            self.assertEqual(adopt_profile_release(self.run, self.successor, reserve_gib=0.), pointer)
            pointer_bytes = (self.run / 'bamf-state.json').read_bytes()
            altered_lease = Lease(Approval(old_receipt.source_release_sha256, delta_budget_policy=Budget()))
            with patch.object(Lease, 'digest', return_value='f' * 64), patch(
                    'bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_lease_v2',
                    return_value=altered_lease):
                with self.assertRaises(BilqisError) as mismatch:
                    adopt_profile_release(self.run, self.successor, reserve_gib=0.)
                self.assertEqual(mismatch.exception.context['reason'], 'BAMF_PROFILE_RETRY_AUTHORITY_DRIFT')
            self.assertEqual((self.run / 'bamf-state.json').read_bytes(), pointer_bytes)
            self.assertEqual(read_accepted_atlas_factory_release(self.run).release_sha256,
                             self.successor.release_sha256)
        self.assertEqual(pointer['generation'], before['generation'] + 1)
        self.assertEqual(digest, pointer['manifest_sha256'])
        self.assertEqual(cold.transition['kind'], 'PROFILE_EXPANSION')
        self.assertEqual(candidate_identity_digest(cold.retained_state),
                         candidate_identity_digest(parent.retained_state))
        self.assertEqual(cold.retained_state.optimizer_step, parent.retained_state.optimizer_step)
        self.assertEqual(cold.topology.digest, parent.topology.digest)
        self.assertEqual(cold.extents.digest, parent.extents.digest)

    def test_actual_active_grade_remains_frozen_and_excludes_new_capabilities(self):
        from bilqis_mlx.factory.generated_grade.definition import _seal_generated_grade
        from bilqis_mlx.factory.tests.curriculum.generated_grade.test_definition import _single_member_fixture
        from bilqis_mlx.runtime.active_generated_grade import _active_from_proposal, read_active_generated_grade
        from bilqis_mlx.runtime.active_generated_grade_custody import _persist_activation
        from bilqis_mlx.runtime.lawful_teaching_frontier_contracts import LawfulTeachingExclusionCode
        from bilqis_mlx.runtime.lawful_teaching_frontier_projection import (
            _active_member_projection, _capabilities, _exclusions,
        )

        pointer = self.publish_parent()
        capability = self.predecessor.curriculum.capability_map['Z.C0']
        with patch('bilqis_mlx.factory.tests.curriculum.generated_grade.test_definition._release',
                   return_value=self.predecessor):
            release, proposal = _single_member_fixture(capability.taught_roots[0], 'Z.C0')
        definition = _seal_generated_grade(proposal, release, release_lineage=(release,))
        identity = (pointer['run_id'], pointer['generation'], pointer['manifest_sha256'],
                    pointer['acceptance_sha256'])
        active = _active_from_proposal(identity, proposal, definition)
        _persist_activation(self.run, active)
        with self.context_patches(real_grade=True), patch(
                'bilqis_mlx.runtime.active_generated_grade_custody._read_issued_proposal',
                return_value=proposal), patch(
                'bilqis_mlx.runtime.active_generated_grade._read_issued_proposal',
                return_value=proposal), patch(
                'bilqis_mlx.runtime.active_generated_grade._reconcile_accepted_generated_grade',
                return_value=None):
            before = read_active_generated_grade(self.run, repair=False)
            files_before = {p.relative_to(self.run): p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
            preview_profile_release(self.run, self.successor)
            files_after = {p.relative_to(self.run): p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
            self.assertEqual(files_after, files_before)
            adopt_profile_release(self.run, self.successor, reserve_gib=0.)
            after = read_active_generated_grade(self.run, repair=False)
            self.assertEqual(after, before)
            release = read_accepted_atlas_factory_release(self.run)
            projection = _active_member_projection(release, after)
            capabilities = _capabilities(release, SimpleNamespace(source_held_rows=()),
                SimpleNamespace(candidates=()), SimpleNamespace(blocked_capabilities=()), (),
                active_members=projection)
            self.assertEqual(tuple(item.capability_id for item in capabilities), ('Z.C0',))
            excluded = {item.capability_id: item.code for item in _exclusions(release, capabilities)}
            for capability_id in ('Z.C2', 'Z.C3', 'Z.C4', 'Z.C5'):
                self.assertEqual(excluded[capability_id], LawfulTeachingExclusionCode.FUTURE_GENERATED_GRADE)

    def test_missing_lease_and_changed_answer_head_preview_do_not_write(self):
        self.publish_parent()
        before = {p.relative_to(self.run): p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
        with self.context_patches():
            with patch('bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_lease_v2', return_value=None):
                with self.assertRaises(BilqisError) as missing:
                    preview_profile_release(self.run, self.successor)
                self.assertEqual(missing.exception.context['reason'], 'BAMF_PROFILE_CURRENT_LEASE_REQUIRED')
            head = self.successor.answer_heads[0]
            changed = replace(head, values=head.values[::-1],
                              semantic_identities=head.semantic_identities[::-1],
                              token_ids=head.token_ids[::-1])
            heads = (changed, *self.successor.answer_heads[1:])
            receipt = replace(self.successor.verification,
                              answer_heads_sha256=_digest([asdict(item) for item in heads]))
            forged = replace(self.successor, answer_heads=heads, verification=receipt)
            forged = replace(forged, release_sha256=forged.expected_digest())
            forged.verify()
            with self.assertRaises(BilqisError) as drift:
                preview_profile_release(self.run, forged)
            self.assertEqual(drift.exception.context['reason'], 'BAMF_PROFILE_ANSWER_HEAD_DRIFT')
        after = {p.relative_to(self.run): p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
        self.assertEqual(after, before)

    def test_changed_activation_rejects_publication(self):
        self.publish_parent()
        before = (self.run / 'bamf-state.json').read_bytes()
        with self.context_patches(), patch(
                'bilqis_mlx.runtime.active_generated_grade_custody._read_stored_active',
                return_value=SimpleNamespace(activation_sha256='d' * 64)):
            with self.assertRaises(BilqisError) as failure:
                adopt_profile_release(self.run, self.successor, reserve_gib=0.)
            self.assertEqual(failure.exception.context['reason'],
                             'BAMF_PROFILE_ACTIVE_GRADE_MEMBERSHIP_DRIFT')
        self.assertEqual((self.run / 'bamf-state.json').read_bytes(), before)

    def test_b_scope_expansion_publishes(self):
        course, self.registry = _synthetic_boolean_course()
        self.answers = _boolean_answers()
        curriculum, bindings = from_legacy_course(course)
        self.graph = {'tokens': ['fixture.padding', 'cogal.value.false', 'cogal.value.true',
                                 *(f'cogal.operator.{v}' for v in BOOLEAN_OPERATORS)]}
        profile = CurriculumProfile('reduced-b', (GradeProfile('B',
            enabled_capabilities=('B.AND', 'B.IFF', 'B.COMPOSITE', 'B.IDBOOLOPS'),
            capabilities=(CapabilityProfile('B.COMPOSITE', (('operators', ('AND', 'IFF')),)),
                          CapabilityProfile('B.IDBOOLOPS', (('operators', ('AND', 'IFF')),),
                                            (('boolean_operator', ('AND', 'IFF')),))),),))
        self.predecessor = compile_executable_factory_release(
            curriculum, bindings, profile, self.registry, self.answers,
            source_root=None, graph=self.graph, verification_seed=17)
        self.successor = compile_successor_profile_release(
            self.predecessor, CurriculumProfile.full(), self.registry, self.answers,
            source_root=None, graph=self.graph, verification_seed=17)
        before = self.publish_parent()
        with self.context_patches():
            pointer = adopt_profile_release(self.run, self.successor, reserve_gib=0.)
            self.assertEqual(read_accepted_atlas_factory_release(self.run).release_sha256,
                             self.successor.release_sha256)
        self.assertEqual(pointer['generation'], before['generation'] + 1)

    def test_narrowing_rejected_without_pointer_write(self):
        self.publish_parent()
        profile = CurriculumProfile('narrower-z', (GradeProfile('Z', ('Z.C0',)),))
        narrowed = compile_successor_profile_release(
            self.predecessor, profile, self.registry, self.answers,
            source_root=None, graph=self.graph, verification_seed=17)
        before = (self.run / 'bamf-state.json').read_bytes()
        with self.context_patches():
            with self.assertRaises(BilqisError) as failure:
                adopt_profile_release(self.run, narrowed, reserve_gib=0.)
            self.assertEqual(failure.exception.context['reason'],
                             'FACTORY_PROFILE_EXPANSION_NARROW_CAPABILITIES')
        self.assertEqual((self.run / 'bamf-state.json').read_bytes(), before)


@dataclass(frozen=True)
class Budget:
    max_capabilities: int = 99
