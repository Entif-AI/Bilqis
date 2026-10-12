import copy
import unittest
from bilqis_alpha.semantics import ABI, atom, combine, negate, quantify, variable, world_from_states
from bilqis_alpha.decision_navigation import initial, panel, apply, target, oracle_trace, state_tokens, candidate_tokens


def episode(query=None, mode='active'):
    return {'version':'decision-episodes-0.1.0', 'split':'TRAIN', 'family':'orientation', 'mode':mode,
            'semantic':{'abi':ABI,'world':world_from_states([2,0,1,2]),'query':query or atom('a','b')}, 'update':None}


class NavigationTest(unittest.TestCase):
    def test_order_stale_and_tampered_panel(self):
        s = initial(episode()); p = panel(s); perm = panel(s, 9)
        self.assertEqual(p['panel_id'], perm['panel_id'])
        n = apply(s, perm, target(s))
        with self.assertRaises(ValueError): apply(n, p, target(s))
        bad = copy.deepcopy(p); bad['candidates'][0]['semantic_delta'] = {}
        with self.assertRaises(ValueError): apply(s, bad, target(s))
        with self.assertRaises(ValueError): target(s, bad)
        with self.assertRaises(ValueError): target(n, p)
        with self.assertRaises(ValueError): apply(s, p, 'not-offered')
        changed = copy.deepcopy(s); changed['world']['facts'] = []
        with self.assertRaises(ValueError): panel(changed)

    def test_scope_binding_and_four_states(self):
        for query in (negate(quantify('exists', atom('a',variable()))),
                      quantify('exists', negate(atom('a',variable())))):
            rows, final = oracle_trace(episode(query))
            self.assertEqual(final['status'], 'resolved')
            self.assertTrue(any(r['state']['tasks'][r['state']['cursor']]['kind']=='bind' for r in rows))
            for row in rows:
                self.assertTrue(state_tokens(row['state']))
                for c in row['panel']['candidates']: self.assertTrue(candidate_tokens(c))
        values = set()
        for label in range(4):
            e = episode(); e['semantic']['world'] = world_from_states([2,label,2,2])
            _, final = oracle_trace(e); values.add(final['outcome'])
        self.assertEqual(values, {'TRUE','FALSE','UNKNOWN','CONFLICT'})

    def test_wrong_relation_can_leave_terminal_label_right(self):
        e = episode(combine('or',atom('a','b'),negate(atom('b','a'))))
        s = initial(e); ideal, good = oracle_trace(e)
        p = panel(s)
        wrong = next(c for c in p['candidates'] if c['effect_class']=='orient' and c['candidate_id']!=target(s))
        s = apply(s,p,wrong['candidate_id'])
        while s['status']=='active': s = apply(s,panel(s),target(s))
        self.assertEqual(s['outcome'],good['outcome'])
        self.assertNotEqual(s['history'][0]['candidate_id'],ideal[0]['gold_id'])

    def test_reserved_outcomes_and_missing_unsupported_are_explicit(self):
        for mode, reserved in [('ambiguous','clarify'),('missing','insufficient'),('unsupported','abstain'),('outside','other')]:
            e=episode(mode=mode)
            if mode=='unsupported': e['semantic']['query']={'op':'unsupported','args':[]}
            s = initial(e); p = panel(s)
            c = next(c for c in p['candidates'] if c['candidate_id']==target(s))
            self.assertEqual(c['effect_class'],reserved)
            n = apply(s,p,c['candidate_id']); self.assertNotEqual(n['status'],'resolved')
            self.assertIsNone(n['outcome'])

    def test_unsupported_never_bypasses_world_or_abi_validation(self):
        e=episode(mode='unsupported'); e['semantic']['abi']='invented'
        with self.assertRaises(ValueError): initial(e)
        e=episode(mode='unsupported'); e['semantic']['world']={'anything':'goes'}
        with self.assertRaises(ValueError): initial(e)
        with self.assertRaises(ValueError): initial(episode(mode='unsupported'))
