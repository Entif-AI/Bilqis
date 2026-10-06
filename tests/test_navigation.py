"""Deterministic admissibility and consequence tests; no learned scorer required."""
import copy
import unittest
from bilqis_ref.navigation_fixture import build_corpus, context
from bilqis_ref.navigation import initial, panel, apply, live, reference_view, expand_view


class NavigationTests(unittest.TestCase):
    def setUp(self):self.corpus=build_corpus()

    def case(self,family):return next(x for x in self.corpus['cases'] if x['family']==family)

    def walk(self,case,seed):
        state=initial(self.corpus,case)
        for _ in range(12):
            if state['status']!='active':return state
            p=panel(self.corpus,case,state,seed)
            choices=p['candidates'];factor=p['factor'];hint=state['hints'].get(factor)
            if any(x['semantic_delta'].get('value')==hint and x['effect_class']=='constrain' for x in choices):
                candidate=next(x for x in choices if x['semantic_delta'].get('value')==hint and x['effect_class']=='constrain')
            elif any(x['effect_class']=='resolve' for x in choices):candidate=next(x for x in choices if x['effect_class']=='resolve')
            elif factor is not None and factor not in case['capabilities']:candidate=next(x for x in choices if x['effect_class']=='insufficient')
            elif hint is None:candidate=next(x for x in choices if x['effect_class']=='clarify')
            else:candidate=next(x for x in choices if x['effect_class']=='other')
            state=apply(self.corpus,case,state,p,candidate['candidate_id'])
        self.fail('unbounded deterministic walk')

    def test_every_fixture_reaches_expected_terminal_under_deterministic_selection(self):
        for case in self.corpus['cases']:
            for seed in range(8):
                result=self.walk(case,seed)
                self.assertEqual(result['status'],case['expected_terminal']['status'],case['id'])
                self.assertEqual(result['object_id'],case['expected_terminal']['object_id'])

    def test_panel_and_candidate_identities_ignore_display_order(self):
        case=self.corpus['cases'][0];state=initial(self.corpus,case)
        a=panel(self.corpus,case,state,1);b=panel(self.corpus,case,state,9)
        self.assertEqual(a['panel_id'],b['panel_id'])
        self.assertEqual({x['candidate_id'] for x in a['candidates']},{x['candidate_id'] for x in b['candidates']})
        self.assertNotEqual(a['candidates'],b['candidates'])

    def test_stale_tampered_unknown_and_cross_fixture_panels_are_rejected(self):
        case=self.corpus['cases'][0];state=initial(self.corpus,case);p=panel(self.corpus,case,state)
        candidate=p['candidates'][0]['candidate_id'];next_state=apply(self.corpus,case,state,p,candidate)
        for changed,panel_value,selection in [(next_state,p,candidate),(state,p,'invented')]:
            with self.assertRaises(ValueError):apply(self.corpus,case,changed,panel_value,selection)
        changed=copy.deepcopy(p);changed['candidates'][0]['semantic_delta']['value']='invented'
        with self.assertRaises(ValueError):apply(self.corpus,case,state,changed,candidate)
        other=self.corpus['cases'][1]
        with self.assertRaises(ValueError):apply(self.corpus,other,state,p,candidate)

    def test_capability_projection_preserves_unsupported_distinction(self):
        case=self.case('capability_mismatch');state=self.walk(case,0)
        self.assertEqual(state['unsupported_distinctions'],['purpose'])
        self.assertEqual(len(live(self.corpus,case,state)),2)
        self.assertIsNone(state['object_id'])

    def test_ambiguity_and_absence_never_offer_forced_resolution(self):
        for family in ['persistent_ambiguity','absent_object']:
            case=self.case(family);state=self.walk(case,1)
            self.assertIsNone(state['object_id'])
        ambiguous=self.case('persistent_ambiguity')
        state=initial(self.corpus,ambiguous)
        self.assertFalse(any(x['effect_class']=='resolve' for x in panel(self.corpus,ambiguous,state)['candidates']))

    def test_references_reduce_repeated_payload_and_restore_identical_information(self):
        case=self.case('compositional_reuse');state=initial(self.corpus,case)
        full=context(self.corpus,case);compact=reference_view(self.corpus,case,state)
        self.assertLess(len(str(compact)),len(str(full)))
        self.assertEqual(expand_view(self.corpus,compact),full)

    def test_structurally_legal_wrong_choice_retains_its_consequence(self):
        case=self.corpus['cases'][0];state=initial(self.corpus,case);p=panel(self.corpus,case,state)
        wrong=next(x for x in p['candidates'] if x['semantic_delta'].get('value')=='container')
        after=apply(self.corpus,case,state,p,wrong['candidate_id'])
        self.assertEqual(after['constraints']['kind'],'container')
        self.assertEqual(len(after['history']),1)
        self.assertEqual(after['history'][0]['candidate_id'],wrong['candidate_id'])
        self.assertEqual(state['constraints'],{})


if __name__=='__main__':unittest.main()
