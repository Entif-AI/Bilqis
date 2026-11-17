"""Fault boundaries for disposable B13 HOW credit custody."""

from dataclasses import replace
import json
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.bamf_bundle.publication as publication
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
from bilqis_mlx.data_plane import data_plane
import bilqis_mlx.runtime.bamf_bundle.publication.events as rejection_events
from bilqis_mlx.runtime import checkpoints
from bilqis_mlx.runtime.accepted_teacher_custody import (
    _issue_bound_visit, _selection_projection, derive_c03_successor_bundle,
)
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation, record_bamf_rejection
from bilqis_mlx.runtime.outcomes.issuance import credited_visit, carry_credit_to_successor
from bilqis_mlx.runtime.outcomes.replay import replay_rejected_outcomes
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import selection_teacher
from bilqis_mlx.runtime.tests.teacher.outcomes.test_custody_integration import retained_observation
from bilqis_mlx.runtime.tests.teacher.outcomes import test_rejection_custody as rejection_fixture
from bilqis_mlx.control_plane.tests.cp07.native_source_support import NativeSourceFixture


class OutcomeRecoveryTests(NativeSourceFixture, unittest.TestCase):
    fixture = rejection_fixture.NativeRejectionOutcomeTests.fixture

    def test_rejection_receipt_without_journal_never_credits_and_retry_commits_once(self):
        parent, teacher, cache, evidence = self.fixture()
        pointer = (self.run / 'bamf-state.json').read_bytes()
        plane = data_plane()
        with patch.object(rejection_events, 'data_plane', return_value=plane), \
                patch.object(plane, 'put_object', wraps=plane.put_object) as stored, \
                patch.object(checkpoints, '_reconcile_delivery_outbox', side_effect=RuntimeError('pre-append')):
            with self.assertRaisesRegex(RuntimeError, 'pre-append'):
                record_bamf_rejection(self.run, parent, evidence)
        self.assertEqual(stored.call_count, 2)
        self.assertEqual(json.loads(plane.get_object(stored.call_args_list[-1].args[0]))['schema'],
                         'bilqis.mlx.bamf-rejection-receipt/v1')
        self.assertEqual(replay_rejected_outcomes(self.run, parent, cache, teacher), teacher)
        self.assertEqual((self.run / 'bamf-state.json').read_bytes(), pointer)
        record_bamf_rejection(self.run, parent, evidence)
        folded = replay_rejected_outcomes(self.run, parent, cache, teacher)
        self.assertEqual(folded['causal_experiment']['events'], 1)
        self.assertEqual(replay_rejected_outcomes(self.run, parent, cache, folded), folded)

    def test_rejection_crash_after_append_replays_once(self):
        parent, teacher, cache, evidence = self.fixture()
        original = checkpoints._reconcile_delivery_outbox
        def append_then_crash(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError('post-append')
        with patch.object(checkpoints, '_reconcile_delivery_outbox', side_effect=append_then_crash):
            with self.assertRaisesRegex(RuntimeError, 'post-append'):
                record_bamf_rejection(self.run, parent, evidence)
        import bilqis_mlx.runtime.priority_rejection_replay as projection
        projection._projection.cache_clear()
        cold = replay_rejected_outcomes(self.run, parent, cache, teacher)
        self.assertEqual(cold['causal_experiment']['events'], 1)
        self.assertEqual(replay_rejected_outcomes(self.run, parent, cache, cold), cold)

    def candidate_after_rejection(self):
        parent, teacher, cache, evidence = self.fixture()
        evidence['structural_weaknesses'] = [
            rejection_fixture._structural_weakness_evidence(evidence)]
        record_bamf_rejection(self.run, parent, evidence)
        folded = replay_rejected_outcomes(self.run, parent, cache, teacher)
        initial = selection_teacher()
        for stat in initial['global_stats'].values():
            stat.setdefault('latest', None)
        with patch('bilqis_mlx.control_plane.tests.cp07.native_source_support.selection_teacher', return_value=initial):
            visit = self.bound_native_visit(parent)
        epoch = restore_teacher_lineage(visit.projection.teacher_state)
        projected = _selection_projection(visit.projection, replace(
            epoch, current_json=json.dumps(folded, sort_keys=True, allow_nan=False)))
        visit = _issue_bound_visit(projected, visit.identity)
        accepted = retained_observation(visit)
        visit = credited_visit(visit, accepted)
        source = self.source()
        retained = replace(source.retained_state, policy=parent.retained_state.policy)
        event = {'event': 'BAMF_C16_3_ACCEPTED', 'optimizer_step': retained.optimizer_step,
                 'capability': visit.identity.capability_id, 'how_outcome': accepted}
        with shape_patch():
            successor = derive_c03_successor_bundle(
                self.run, retained, visit, next_seed=visit.identity.selection_seed + 1,
                cursor=visit.identity.visit_id, delivery_events=(event,))
            successor = carry_credit_to_successor(visit, successor, parent)
        return parent, successor

    def assert_credited(self, loaded):
        teacher = restore_teacher_lineage(loaded.teacher_state).teacher()
        self.assertEqual(teacher['causal_experiment']['events'], 2)
        self.assertEqual(len(teacher['structural_weaknesses']['classes']), 1)
        record = teacher['causal_experiment']['contexts']['A.REJECT|RECOVERY_1|factory/7']
        self.assertEqual(sum(row['retained'] for row in record.values()), 1)
        self.assertEqual(sum(row['unsafe'] for row in record.values()), 1)

    def test_rejected_then_accepted_pre_pointer_failure_recovers_once(self):
        parent, successor = self.candidate_after_rejection()
        pointer = (self.run / 'bamf-state.json').read_bytes()
        with shape_patch(), patch.object(mlx_checkpoint, 'assert_headroom'), \
                patch.object(publication, '_atomic_pointer', side_effect=RuntimeError('pre-pointer')):
            with self.assertRaisesRegex(RuntimeError, 'pre-pointer'):
                self.publish(successor, acceptance=self.binding(successor))
        self.assertEqual((self.run / 'bamf-state.json').read_bytes(), pointer)
        with shape_patch(), patch.object(mlx_checkpoint, 'assert_headroom'):
            self.publish(successor, acceptance=self.binding(successor))
            loaded = load_bamf_generation(self.run / 'bamf-state.json')
        self.assert_credited(loaded)

    def test_rejected_then_accepted_post_pointer_outbox_recovery_once(self):
        parent, successor = self.candidate_after_rejection()
        original = publication.reconcile_bamf_outbox
        def crash_after_pointer(*args, **kwargs):
            if args[1].generation == successor.generation:
                raise RuntimeError('post-pointer')
            return original(*args, **kwargs)
        with shape_patch(), patch.object(mlx_checkpoint, 'assert_headroom'), \
                patch.object(publication, 'reconcile_bamf_outbox', side_effect=crash_after_pointer):
            with self.assertRaisesRegex(RuntimeError, 'post-pointer'):
                self.publish(successor, acceptance=self.binding(successor))
        with shape_patch():
            first = load_bamf_generation(self.run / 'bamf-state.json')
            second = load_bamf_generation(self.run / 'bamf-state.json')
        self.assert_credited(first)
        self.assert_credited(second)
        events = [json.loads(line) for line in (self.run / 'events.jsonl').read_text().splitlines()]
        self.assertEqual(sum(row['event'] == 'BAMF_C16_3_ACCEPTED' for row in events), 1)
