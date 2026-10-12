"""Behavioral admission, split and compilation boundaries for developmental teachers."""
import copy
import random
import unittest

from bilqis_development import data
from bilqis_development.registry import extended_catalog as catalog
from bilqis_teacher.policy import load_policy, novelty, validate_lesson, feedback, source_text
from bilqis_teacher.grammar import exercises, compile_exercise, validate_witness


class TeacherPolicyTests(unittest.TestCase):
    def test_policy_loads_the_exact_spiral_and_closeout_contract(self):
        p = load_policy()
        self.assertEqual(p['version'], '1.0.0')
        self.assertEqual(p['batch'], {'current': 12, 'fresh_prior': 4, 'cross_stage': 8, 'weak_reinforcement': 8})
        self.assertEqual(set(p['closeout']), {'A', 'B', 'C'})

    def test_known_alias_and_typed_composition_bypass_retrieval(self):
        g = catalog()
        identity = g['tokens'][-1]
        self.assertEqual(novelty({'identity': identity}, g)['category'], 'KNOWN_ID')
        self.assertEqual(novelty({'referent': identity, 'surface': identity.rsplit('.', 1)[-1]}, g)['category'], 'SURFACE_ALIAS')
        r = data.lesson(6, 'provenance-ancestry', random.Random(44))
        found = novelty({'source': '84', 'record': r['input']}, g)
        self.assertEqual(found['category'], 'COMPOSITION_ONLY')
        self.assertFalse(found['eg2_permitted'])

    def test_unqualified_and_previously_deferred_gaps_cannot_retrieve(self):
        g = catalog()
        for c in ({'gap': 'new'}, {'source': 'invented', 'gap': 'new'}, {'source': '84', 'gap': 'new', 'history': 'rejected'}):
            found = novelty(c, g)
            self.assertEqual(found['category'], 'DEFERRED')
            self.assertFalse(found['eg2_permitted'])
        self.assertTrue(novelty({'source': '84', 'gap': 'unrepresented operator', 'source_excerpt': source_text('84')[:120]}, g)['eg2_permitted'])

    def test_gold_source_type_and_language_cannot_bypass_admission(self):
        r = data.lesson(6, 'provenance-ancestry', random.Random(44))
        validate_lesson(r)
        bad = copy.deepcopy(r); bad['gold'] = 'CONFLICT'
        with self.assertRaises(ValueError): validate_lesson(bad)
        bad = copy.deepcopy(r); bad['input']['English'] = 'answer is true'
        with self.assertRaises(ValueError): validate_lesson(bad)
        bad = copy.deepcopy(r); bad['source_locator'] = 'https://example.invalid/gold'
        with self.assertRaises(ValueError): validate_lesson(bad)
        bad = copy.deepcopy(r); bad['input']['query']['op'] = 'UNVALIDATED_ID'
        with self.assertRaises(ValueError): validate_lesson(bad)

    def test_feedback_requires_exact_dev_identity_and_rejects_final(self):
        r = data.lesson(6, 'provenance-ancestry', random.Random(44))
        corpus = {'stages': {'6': {'eval': {'varied': [r], 'composite': [r]}}}}
        p = {'id': r['id'], 'family': r['family'], 'gold': r['gold'], 'prediction': 'FALSE'}
        scores = {'6': {s: {'predictions': [p]} for s in ('varied', 'composite')}}
        self.assertIn('6:provenance-ancestry', feedback(scores, corpus))
        bad = copy.deepcopy(scores); bad['6']['varied']['predictions'][0]['id'] = 'final-case'
        with self.assertRaisesRegex(ValueError, 'DEV'): feedback(bad, corpus)

    def test_grammar_compiles_distinct_candidates_and_both_causal_arms(self):
        specs = exercises(6)
        self.assertGreater(len(specs), 10)
        self.assertEqual(len(specs), len({s['id'] for s in specs}))
        for spec in specs[:6]:
            r, witness = compile_exercise(spec, random.Random(707), set())
            validate_lesson(r); validate_witness(r, witness)
            self.assertNotEqual(r['gold'], witness['old_contrast']['gold'])
            self.assertNotEqual(r['gold'], witness['new_contrast']['gold'])
            bad = copy.deepcopy(witness); bad['old_contrast'] = r
            with self.assertRaises(ValueError): validate_witness(r, bad)

    def test_new_identity_or_wrong_source_spec_is_rejected(self):
        spec = exercises(6)[0]
        for key, value in (('family', 'invented-concept'), ('source', '85')):
            bad = dict(spec, **{key: value})
            with self.assertRaises(ValueError): compile_exercise(bad, random.Random(7), set())


if __name__ == '__main__': unittest.main()
