import unittest
from bilqis_alpha.decision_episodes import build
from bilqis_alpha.decision_navigation import candidate_tokens, oracle_trace, state_tokens


class CueBaselineTest(unittest.TestCase):
    def test_explicit_binding_and_availability_are_copyable(self):
        from bilqis_alpha.decision_baseline import cue_choice
        examples=build()['episodes']
        binding=next(e for e in examples if e['family']=='binding' and e['split']=='TRAIN')
        rows,_=oracle_trace(binding)
        row=next(r for r in rows if r['panel']['focus_kind']=='bind')
        candidates=row['panel']['candidates']
        index=cue_choice(state_tokens(row['state']),[candidate_tokens(c) for c in candidates])
        self.assertEqual(candidates[index]['candidate_id'],row['gold_id'])
        for mode in ('ambiguous','missing','unsupported','outside'):
            row=oracle_trace(next(e for e in examples if e['mode']==mode))[0][0]
            candidates=row['panel']['candidates']
            index=cue_choice(state_tokens(row['state']),[candidate_tokens(c) for c in candidates])
            self.assertEqual(candidates[index]['candidate_id'],row['gold_id'])

    def test_evidence_reading_requires_more_than_copying_an_instruction(self):
        from bilqis_alpha.decision_baseline import cue_choice
        row=next(r for r in oracle_trace(build()['episodes'][0])[0] if r['panel']['focus_kind']=='read')
        candidates=row['panel']['candidates']
        self.assertIsNone(cue_choice(state_tokens(row['state']),[candidate_tokens(c) for c in candidates]))
