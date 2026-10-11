"""Checks the shipped cohort and real checkpoint lineage, without retraining."""
import unittest
from pathlib import Path

import torch

from bilqis_micro.model import load_checkpoint
from bilqis_micro.graph import compile_embeddings
from bilqis_micro.run import optimizer_receipt
from bilqis_development.continuation import load
from bilqis_development.run import read,verify

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/evidence/u5-u6/run-01'


class DevelopmentEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze,cls.config,cls.data=verify(RUN)

    def test_real_trained_row_and_moment_migration(self):
        parent,p=load_checkpoint(ROOT/'docs/evidence/micro-universes/run-01/after-U4.pt')
        continued,opt,c=load(RUN/'expanded-U4.pt')
        for name,weights in parent.state_dict().items():
            actual=continued.state_dict()[name]
            self.assertTrue(torch.equal(weights,actual[:68] if name=='embedding.weight' else actual))
        before=p['optimizer'];after=opt.state_dict()
        self.assertEqual(before['param_groups'],after['param_groups'])
        for parameter,state in before['state'].items():
            for key,value in state.items():
                actual=after['state'][parameter][key]
                if value.shape!=actual.shape:
                    self.assertTrue(torch.equal(value,actual[:68]));self.assertEqual(int(torch.count_nonzero(actual[68:])),0)
                else:self.assertTrue(torch.equal(value,actual))
        table,_=compile_embeddings(96,c['graph'])
        self.assertTrue(torch.equal(continued.embedding.weight[68:],table[68:]))
        self.assertEqual(optimizer_receipt(opt)['steps'],[8400])

    def test_new_balanced_probes_and_old_probes_are_preserved(self):
        previous=read(ROOT/'docs/evidence/micro-universes/run-01/data.json')
        for stage in map(str,range(5)):
            self.assertEqual(self.data['stages'][stage],previous['stages'][stage])
        from collections import defaultdict,Counter
        for stage in ('5','6'):
            for split in ('varied','composite'):
                labels=defaultdict(Counter)
                for r in self.data['stages'][stage]['eval'][split]:labels[r['family']][r['gold']]+=1
                for family,count in labels.items():
                    self.assertEqual(len(set(count.values())),1)
                    self.assertEqual(set(count),{'UNKNOWN','TRUE','FALSE','CONFLICT'} if family in ('current-evidence','historical-evidence') else {'TRUE','FALSE'})
        h=read(RUN/'helper-summary.json');manifest=read(RUN/'manifest.json')
        self.assertEqual(h['actual_kev_decisions'],20)
        self.assertEqual(sum(manifest['helper_lessons_by_decision'].values()),2560)

    def test_actual_continuation_and_fresh_numeric_replay(self):
        result=read(RUN/'result.json');replay=read(RUN/'replay.json')
        self.assertEqual(result['additional_updates'],5000)
        self.assertEqual(result['examples'],160000)
        self.assertTrue(all(n>0 for n in result['helper_exposures'].values()))
        self.assertEqual(set(result['helper_exposures']),set(read(RUN/'manifest.json')['helper_lessons_by_decision']))
        self.assertEqual(result['stages'][1]['start_state_sha256'],result['stages'][0]['end_state_sha256'])
        self.assertEqual(result['stages'][1]['optimizer_before'],result['stages'][0]['optimizer_after'])
        model,opt,payload=load(RUN/'after-U6.pt')
        self.assertEqual(optimizer_receipt(opt)['steps'],[13400])
        self.assertEqual(payload['state_sha256'],result['final_state_sha256'])
        self.assertNotEqual(replay['training_pid'],replay['replay_pid'])
        self.assertEqual(replay['status'],'REPRODUCED')
        self.assertLessEqual(replay['max_absolute_error'],1e-6)
