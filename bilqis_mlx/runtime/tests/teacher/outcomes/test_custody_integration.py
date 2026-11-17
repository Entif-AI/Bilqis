"""Disposable native custody checks for accepted HOW evidence."""
from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.control_plane.tests.cp07.native_source_support import NativeSourceFixture
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import record_bamf_rejection
from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
from bilqis_mlx.learning.teacher_strategy_population import effective_policy_key
from bilqis_mlx.runtime import state
from bilqis_mlx.runtime.accepted_teacher_custody import derive_c03_successor_bundle
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation
from bilqis_mlx.runtime.outcomes.issuance import credited_visit, carry_credit_to_successor
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch


def retained_observation(visit):
    teacher = restore_teacher_lineage(visit.projection.teacher_state).teacher()
    identity = visit.identity.to_record()
    policy = teacher['strategies'][identity['policy_key']]
    value = {
        'schema': 'bilqis.bamf.teacher-outcome/v1', 'attempt_id': 'native:1',
        'proposal_id': 'a' * 64, 'candidate_evidence': {'sha256': 'b' * 64},
        'teacher_visit': identity,
        'context': {'grade': 'A', 'phase': 'RECOVERY_1',
                    'curriculum_scope': 'factory/7', 'rubric_sha256': 'd' * 64,
                    'diagnostics': {}},
        'selected_teacher': deepcopy(teacher), 'selected_policy': deepcopy(policy),
        'effective_policy_key': effective_policy_key(policy), 'realized_action': None,
        'attempted_steps': 1, 'retained_steps': 1,
        'decision': {'decision': 'PROVISIONAL', 'reason': 'PAIRED_SCREEN_WITHIN_BUDGET',
                     'evidence_sha256': 'e' * 64},
        'scores': [[identity['capability_id'], 1, 2, 4]],
        'protected_capabilities': [],
    }
    value['outcome_sha256'] = state._fingerprint(value)
    return value


class NativeOutcomeCustodyTests(NativeSourceFixture, unittest.TestCase):
    def prepared(self):
        parent = self.parent()
        from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import selection_teacher
        teacher = selection_teacher()
        for stats in teacher['global_stats'].values():
            stats.setdefault('latest', None)
        with patch('bilqis_mlx.control_plane.tests.cp07.native_source_support.selection_teacher',
                   return_value=teacher):
            visit = self.bound_native_visit(parent, capability='A.NATIVE')
        credited = credited_visit(visit, retained_observation(visit))
        source = self.source()
        retained = replace(source.retained_state, policy=parent.retained_state.policy)
        with shape_patch():
            successor = derive_c03_successor_bundle(
                self.run, retained, credited,
                next_seed=visit.identity.selection_seed + 1,
                cursor=visit.identity.visit_id,
                delivery_events=({'event': 'BAMF_C16_3_ACCEPTED',
                                  'optimizer_step': source.retained_state.optimizer_step,
                                  'capability': 'A.NATIVE'},))
        return parent, credited, successor

    def test_compatible_accepted_credit_survives_cold_bundle_read(self):
        parent, visit, successor = self.prepared()
        with shape_patch():
            carried = carry_credit_to_successor(visit, successor, parent)
        teacher = restore_teacher_lineage(carried.teacher_state).teacher()
        from bilqis_mlx.runtime.accepted_teacher_custody import _bank_identity, _plasticity_identity
        self.assertEqual((_bank_identity(parent), _plasticity_identity(parent.retained_state), parent.provenance.source_identity, parent.provenance.release_digest), (_bank_identity(successor), _plasticity_identity(successor.retained_state), successor.provenance.source_identity, successor.provenance.release_digest))
        record = teacher['causal_experiment']['contexts']['A.NATIVE|RECOVERY_1|factory/7']
        self.assertEqual(record[visit.identity.policy_key]['retained'], 1)
        checkpoint = teacher['causal_experiment']['student_policy_epoch']
        self.assertEqual(checkpoint['contexts'], {})
        self.assertEqual(checkpoint['unretained_contexts'], {})
        with shape_patch(), patch.object(mlx_checkpoint, 'assert_headroom'):
            self.publish(carried, acceptance=self.binding(carried))
            loaded = load_bamf_generation(self.run / 'bamf-state.json')
        self.assertEqual(restore_teacher_lineage(loaded.teacher_state).teacher(), teacher)

    def test_changed_bank_does_not_carry_incompatible_evidence(self):
        parent, visit, successor = self.prepared()
        altered = replace(successor, semantic_abi={**successor.semantic_abi,
                          'bank_identities': ['different-bank']})
        with shape_patch():
            actual = carry_credit_to_successor(visit, altered, parent)
        self.assertIs(actual, altered)
        self.assertNotIn('A.NATIVE|RECOVERY_1|factory/7',
                         restore_teacher_lineage(actual.teacher_state).teacher()['causal_experiment']['contexts'])

    def test_changed_plasticity_does_not_carry_incompatible_evidence(self):
        parent, visit, successor = self.prepared()
        changed = self.source().retained_state.policy
        self.assertNotEqual(changed.to_record(), parent.retained_state.policy.to_record())
        altered = replace(successor, retained_state=replace(successor.retained_state, policy=changed))
        with shape_patch():
            actual = carry_credit_to_successor(visit, altered, parent)
        self.assertIs(actual, altered)
        self.assertNotIn('A.NATIVE|RECOVERY_1|factory/7',
                         restore_teacher_lineage(actual.teacher_state).teacher()['causal_experiment']['contexts'])

    def test_unissued_outcome_cannot_commit_rejection(self):
        parent = self.parent()
        visit = self.bound_native_visit(parent)
        pointer = (self.run / 'bamf-state.json').read_bytes()
        evidence = {'schema': 'bilqis.bamf.c16.3-rejection/v2',
                    'teacher_visit': visit.identity.to_record(),
                    'visit_id': visit.identity.visit_id,
                    'capability': visit.identity.capability_id,
                    'selected_policy_key': visit.identity.policy_key,
                    'how_outcome': retained_observation(visit)}
        with self.assertRaises(BilqisError):
            record_bamf_rejection(self.run, parent, evidence)
        self.assertEqual((self.run / 'bamf-state.json').read_bytes(), pointer)
