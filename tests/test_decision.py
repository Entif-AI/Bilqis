"""Owned diagnostic decisions; scorers cannot change truth or curriculum gates."""
import copy
import json
import math
import unittest
from pathlib import Path

from bilqis_ref.decision import (native_item, normalize, route, curriculum_proposal,
                                metrics, permute)
from bilqis_ref.decision_fixture import build_fixture
from bilqis_ref.teacher import TeacherState
from bilqis_ref.local_http import local_json
from bilqis_ref.decision_qualification import classify


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = build_fixture()
        self.item = self.fixture['items'][0]
        self.identity = {'engine_revision': 'a' * 40, 'model': 'owned-test',
                         'model_revision': 'b' * 40, 'backend': 'mlx'}

    def scored(self, probabilities=None):
        ids = [o['id'] for o in self.item['options']]
        probabilities = probabilities or [0.9] + [0.1 / (len(ids)-1)] * (len(ids)-1)
        return normalize(self.item, 'semif', {'option_ids': ids, 'probabilities': probabilities,
                         'prompt_sha256': 'c' * 64}, self.identity, 10, False)

    def test_frozen_fixture_reproduces_and_labels_have_origin(self):
        stored = json.loads((Path(__file__).parents[1]/'fixtures/decision-v1.json').read_text())
        self.assertEqual(stored, self.fixture)
        self.assertGreaterEqual(len(stored['items']), 20)
        self.assertEqual(len({x['id'] for x in stored['items']}), len(stored['items']))
        for item in stored['items']:
            self.assertTrue(item['provenance']['source'])
            if item['label'] is not None:
                self.assertTrue(item['provenance']['label_origin'])
                self.assertIn(item['label'], [o['id'] for o in item['options']])

    def test_gold_and_provenance_are_never_sent_to_engine(self):
        row = native_item(self.item)
        self.assertEqual(set(row), {'id', 'state', 'question', 'options'})
        item = copy.deepcopy(self.item); item['split'] = 'SEALED'
        with self.assertRaises(ValueError): native_item(item)

    def test_local_client_rejects_external_or_credentialed_endpoints_before_calling(self):
        for url in ['http://192.168.0.92:8008/v1/models','https://127.0.0.1/v1/models',
                    'http://user:secret@127.0.0.1/v1/models','http://127.0.0.1/v1/models?redirect=1']:
            with self.assertRaises(ValueError):local_json(url,'/v1/models')

    def test_permutation_preserves_identity_and_does_not_mutate_fixture(self):
        original = copy.deepcopy(self.item)
        shuffled = permute(self.item, 19)
        self.assertEqual(self.item, original)
        self.assertCountEqual(shuffled['options'], original['options'])
        self.assertEqual(shuffled['id'], original['id'])

    def test_score_boundary_rejects_nonfinite_unmatched_or_unscaled_probabilities(self):
        for probabilities in ([math.nan]*len(self.item['options']), [0.2],
                              [0.8]*len(self.item['options'])):
            with self.assertRaises(ValueError): self.scored(probabilities)
        native = {'option_ids': ['invented'], 'probabilities': [1.]}
        with self.assertRaises(ValueError): normalize(self.item,'semif',native,self.identity,1,False)

    def test_native_metadata_survives_and_low_margin_routes_to_review(self):
        result = self.scored()
        self.assertEqual(result['runtime_metadata']['native']['prompt_sha256'], 'c'*64)
        uniform = self.scored([1/len(self.item['options'])]*len(self.item['options']))
        self.assertEqual(route(uniform,self.fixture['policy']), 'review')
        self.assertEqual(result['candidate_ids'], [o['id'] for o in self.item['options']])

    def test_kev_api_rounding_is_retained_without_renormalizing(self):
        probabilities = dict(zip([x['id'] for x in self.item['options']], [0.9,0.0333,0.0333,0.0333]))
        native = {'answers':{'decision':{'probabilities':probabilities,'choice':'TRUE'}}}
        result = normalize(self.item,'kev',native,self.identity,10,False)
        self.assertEqual(result['probabilities'], probabilities)
        self.assertEqual(result['runtime_metadata']['native'], native)

    def test_invalid_generated_choice_is_a_measured_failure_not_repaired(self):
        native = {'choices':[{'message':{'content':'Probably TRUE, trust me.'}}]}
        result = normalize(self.item,'generative',native,self.identity,10,False)
        self.assertIsNone(result['selected_id'])
        self.assertEqual(result['validation_error'],'GENERATION_INVALID_CHOICE')
        self.assertEqual(route(result,self.fixture['policy']),'review')

    def test_curriculum_consumer_checks_eligibility_and_never_promotes(self):
        teacher = TeacherState(promoted=[0])
        before = copy.deepcopy(teacher)
        proposal = curriculum_proposal(teacher, {'selected_id':'composition','route':'local'})
        self.assertEqual(proposal['stage'], teacher.choose())
        self.assertEqual(proposal['disposition'], 'deterministic_fallback')
        proposal = curriculum_proposal(teacher, {'selected_id':'purpose-use','route':'local'})
        self.assertEqual(proposal['stage'], 2)
        self.assertEqual(teacher, before)
        teacher.held = True
        with self.assertRaises(RuntimeError): curriculum_proposal(teacher, proposal)

    def test_metrics_exclude_unlabeled_rows_and_do_not_invent_calibration(self):
        result = self.scored(); result['selected_id'] = self.item['label']
        report = metrics([self.item], [result], self.fixture['policy'])
        self.assertEqual(report['labeled'], 1)
        self.assertEqual(report['accuracy'], 1.)
        self.assertIsNone(report['ece'])
        self.assertEqual(report['ece_status'], 'insufficient_labeled_sample')
        unlabeled = copy.deepcopy(self.item); unlabeled['label'] = None
        self.assertIsNone(metrics([unlabeled], [result], self.fixture['policy'])['accuracy'])

    def test_raw_temperature_and_small_samples_cannot_qualify_primary_engine(self):
        bad={'labeled':23,'accuracy':0.5,'confident_wrong':0,'false_confident_local_completions':0}
        good={**bad,'accuracy':1.}
        self.assertEqual(classify({'K1':bad,'S1':bad,'K3':good},self.fixture['policy']),'QUALITY_INADEQUATE')
        self.assertEqual(classify({'K1':bad,'S1':good},self.fixture['policy']),'QUALIFIED_SEMIF')
        self.assertEqual(classify({'K1':good,'S1':{**good,'labeled':1}},self.fixture['policy']),
                         'ENGINEERING_READY_QUALITY_UNCLEAR')


if __name__ == '__main__': unittest.main()
