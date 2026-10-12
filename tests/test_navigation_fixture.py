"""Fixture-local #69 corpus; information parity does not prove a learning effect."""
import copy
import json
import unittest
from pathlib import Path
from bilqis_ref.navigation_fixture import build_corpus, resolve_object, render, decode, context
from bilqis_ref.semantics import digest


class NavigationFixtureTests(unittest.TestCase):
    def setUp(self): self.corpus=build_corpus()

    def test_frozen_corpus_and_all_ten_required_classes(self):
        stored=json.loads((Path(__file__).parents[1]/'fixtures/navigation-v1.json').read_text())
        self.assertEqual(stored,self.corpus)
        self.assertEqual(len({x['family'] for x in stored['cases']}),10)
        self.assertEqual(len({x['id'] for x in stored['cases']}),10)
        self.assertEqual(stored['authority']['official_rosetta_authority'],False)
        for case in stored['cases']:
            self.assertTrue(case['provenance'])
            self.assertIn(case['expected_terminal']['status'],['resolved','ambiguous','absent','unsupported'])

    def test_matched_surfaces_round_trip_and_do_not_reveal_expected_answer(self):
        for case in self.corpus['cases']:
            b=render(self.corpus,case,'bilqis');t=render(self.corpus,case,'typed')
            self.assertEqual(decode(b,'bilqis'),decode(t,'typed'))
            self.assertEqual(decode(b,'bilqis'),context(self.corpus,case))
            self.assertNotIn('expected_terminal',b);self.assertNotIn('expected_terminal',t)
            self.assertNotIn('evidence_schedule',b)

    def test_semantic_identities_are_content_bound_including_composition(self):
        for identity in self.corpus['objects']:
            self.assertEqual(digest(resolve_object(self.corpus,identity)),identity)
        reused=next(x for x in self.corpus['cases'] if x['family']=='compositional_reuse')
        self.assertTrue(reused['resolved_refs'])
        target=reused['expected_terminal']['object_id']
        self.assertTrue(resolve_object(self.corpus,target)['members'])
        view=context(self.corpus,reused)
        for reference in reused['resolved_refs']:self.assertIn(reference,view['objects'])

    def test_cycle_missing_reference_and_corrupt_identity_are_rejected(self):
        identity=next(iter(self.corpus['objects']))
        for replacement in ({'ref':identity},{'ref':'missing'},{'kind':'corrupt'}):
            corpus=copy.deepcopy(self.corpus);corpus['objects'][identity]=replacement
            with self.assertRaises(ValueError):resolve_object(corpus,identity)

    def test_alternate_order_has_the_same_target_and_unknown_is_not_ambiguity(self):
        exact=self.corpus['cases'][0];alternate=self.corpus['cases'][8]
        self.assertEqual(exact['expected_terminal'],alternate['expected_terminal'])
        ambiguous=self.corpus['cases'][3];absent=self.corpus['cases'][5]
        self.assertGreater(len(ambiguous['initial_live']),1)
        self.assertNotEqual(ambiguous['expected_terminal']['status'],absent['expected_terminal']['status'])


if __name__=='__main__':unittest.main()
