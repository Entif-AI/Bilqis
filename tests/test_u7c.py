"""Admission gates of the new immutable U7C successor."""
import copy
from collections import Counter
import unittest

from bilqis_u7c.grammar import audit_cohort, accepted_specs
from bilqis_u7c.run import RUN, CURRENT, MIX, read, verify, teacher_panel, teacher_text, RETENTION
from bilqis_development.continuation import load
from bilqis_micro.run import optimizer_receipt
from bilqis_spiral.sampler import Sampler
from bilqis_teacher.policy import feedback
from bilqis_spiral.run import PARENT


class U7CTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy, cls.pools, cls.corpus = verify(RUN)
        cls.final = read(RUN/'final-evaluation.json.gz')
        cls.audit = read(RUN/'preflight.json')
        cls.signals = feedback(read(RUN/'dev-before.json.gz'), cls.corpus)

    def test_parent_optimizer_and_untrained_evidence_preserved(self):
        model,opt,payload=load(CURRENT)
        self.assertEqual(optimizer_receipt(opt)['steps'], [13400])
        self.assertEqual(payload['state_sha256'],self.policy['start']['state_sha256'])
        if (RUN/'training-result.json').exists():
            trained = read(RUN/'training-result.json')
            self.assertLessEqual(trained['actual_updates'], self.policy['updates_cap'])
            self.assertEqual(trained['optimizer_step'], 13400 + trained['actual_updates'])
        self.assertEqual(self.audit['retention_start']['primitives'],26)
        self.assertEqual(self.audit['retention_start']['u4_composite'],50)

    def test_semantic_truth_table_balanced_and_arms_needed_on_train_and_final(self):
        prior=self.audit['train']['baselines']
        separate=self.audit['final']['baselines']
        for baselines in (prior, separate):
            self.assertEqual(baselines['gate']['correct']*2,baselines['gate']['n'])
            for arm in ('old','new'):
                self.assertLess(baselines[arm]['correct']*5,baselines[arm]['n']*4)
        self.assertEqual(self.audit['split']['intersection'],0)
        self.assertEqual(self.audit['train']['rows'],432)
        self.assertEqual(self.audit['final']['rows'],288)
        self.assertEqual(len(read(RUN/'paired-causal-train.json.gz')), 216)
        self.assertEqual(len(read(RUN/'paired-causal-final.json.gz')), 144)

    def test_english_only_real_example_options_and_review(self):
        for period in range(4):
            for stage in (5,6):
                panel=teacher_panel(stage,self.signals,period)
                state,question,options=teacher_text(panel,self.pools['cross'][str(stage)])
                self.assertEqual(len(options),4)
                self.assertEqual(sum('Review:' in x['description'] for x in options),1)
                self.assertEqual(sum('Example one:' in x['description'] for x in options),3)
                for value in (state,question,*(o['description'] for o in options)):
                    for leak in ('{','}','[',']','"op"','"kind"','"gold"','"TRUE"','"FALSE"','K0','J0','PARENT','DERIVED_FROM'):
                        self.assertNotIn(leak,value)
                self.assertIn('mistakes out of',state)
                self.assertIn('Which single lesson family',question)

    def test_all_steps_obey_exact_sampler_allocation_and_weak_floors(self):
        sampler=Sampler(self.corpus,self.pools,self.policy['seed']+1,self.signals)
        for _ in range(48):
            rows,labels,keys=sampler.batch()
            self.assertEqual(Counter(labels),Counter(MIX))
            self.assertEqual(Counter(r['stage'] for r,l in zip(rows,labels) if l=='cross_stage'),
                             {5:4,6:4})
            weak=[(r,k) for r,l,k in zip(rows,labels,keys) if l=='weak_reinforcement']
            self.assertGreaterEqual(sum(r['stage']<5 for r,k in weak),2)
            self.assertGreaterEqual(sum(r['stage']>=5 for r,k in weak),2)

    def test_no_new_shortcut_grammar_causal_witness_and_split(self):
        witnesses=read(RUN/'paired-causal-train.json.gz')
        audit=audit_cohort(self.pools['cross'], witnesses)
        self.assertEqual(audit['baselines'],self.audit['train']['baselines'])
        final=read(RUN/'paired-causal-final.json.gz')
        rows={'5':[], '6':[]}
        for r in self.final['cross']: rows[str(r['stage'])].append(r)
        audit_final=audit_cohort(rows,final)
        self.assertEqual(audit_final['baselines'],self.audit['final']['baselines'])

if __name__=='__main__': unittest.main()
