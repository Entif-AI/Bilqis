import unittest
from collections import Counter
from bilqis_alpha.decision_episodes import build, pattern
from bilqis_alpha.semantics import digest


class EpisodesTest(unittest.TestCase):
    def test_frozen_pair_and_composition_firewall(self):
        data=build(); again=build()
        self.assertEqual(digest(data),digest(again))
        self.assertEqual(len(data['blocks']),16)
        self.assertTrue(all(len(b['batches'])==96 and all(len(x)==32 for x in b['batches']) for b in data['blocks']))
        train={e['pattern'] for e in data['episodes'] if e['split']=='TRAIN'}
        held={e['pattern'] for e in data['episodes'] if e['split']=='HELDOUT'}
        self.assertFalse(train & held)
        self.assertEqual(sum(len(x) for b in data['blocks'] for x in b['batches']),49152)
        forward=Counter(i for b in data['blocks'] for x in b['batches'] for i in x)
        reverse=Counter(i for b in reversed(data['blocks']) for x in b['batches'] for i in x)
        self.assertEqual(forward,reverse)
        for b in data['blocks']: self.assertTrue(all(p<int(b['block_id'][1:]) for p in b['prerequisites']))
        self.assertTrue(data['historically_exposed_domain'])
        with self.assertRaises(ValueError): build(seed=203)

    def test_no_answer_metadata_in_encodings(self):
        data=build()
        self.assertTrue(all(set(r)=={'row_id','episode_id','step','state_tokens','candidate_tokens','candidate_ids','gold_id','kind'} for r in data['rows']))
        self.assertEqual(len({e['episode_id'] for e in data['episodes']}),len(data['episodes']))
        self.assertGreater(len({len(r['candidate_tokens']) for r in data['rows']}),1)
