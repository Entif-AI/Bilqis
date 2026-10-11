import copy
import itertools
import tempfile
import unittest
from pathlib import Path

import torch

from bilqis_micro import kernel as prior
from bilqis_micro.graph import catalog
from bilqis_micro.model import initialize
from bilqis_micro.run import make_optimizer, default_config
from bilqis_ref.model import ModelConfig, batch
from bilqis_development.kernel import world, const, op, record, evaluate, independent_evaluate, encode, decode
from bilqis_development.registry import extended_catalog, candidates, admit
from bilqis_development.continuation import expand, save, load
from bilqis_development.data import FAMILIES,lesson
import random


class DevelopmentTests(unittest.TestCase):
    def check(self, w, q, gold):
        r = record(w, q)
        self.assertEqual(evaluate(r), gold)
        self.assertEqual(independent_evaluate(r), gold)
        self.assertEqual(decode(encode(r)), r)
        return r

    def test_sets_functions_graphs_and_composition(self):
        w = world('ABC', sets={'K0':['A','B'], 'K1':['B','C']},
                  functions={'F0':[['A','B']], 'F1':[['B','C']]}, edges=[['A','B'],['B','C']])
        a,b,c = [const('Entity', x) for x in 'ABC']
        k,l = [const('Set', x) for x in ('K0','K1')]
        f,g = [const('Function', x) for x in ('F0','F1')]
        self.check(w, op('MEMBER',b,op('INTERSECTION',k,l)), 'TRUE')
        self.check(w, op('MEMBER',b,op('DIFFERENCE',k,l)), 'FALSE')
        self.check(w, op('SUBSET',op('INTERSECTION',k,l),k), 'TRUE')
        self.check(w, op('MEMBER',a,op('DOMAIN',f)), 'TRUE')
        self.check(w, op('MEMBER',b,op('RANGE',f)), 'TRUE')
        self.check(w, op('MAPS',op('INVERSE',f),b,a), 'TRUE')
        self.check(w, op('MAPS',op('COMPOSITION',f,g),a,c), 'TRUE')
        self.check(w, op('MAPS',op('COMPOSITION',g,f),a,c), 'FALSE')
        self.check(w, op('PATH',a,c), 'TRUE')
        self.check(w, op('MEMBER',c,op('NEIGHBORS',a)), 'FALSE')
        self.check(w, op('AND',op('PATH',a,c),op('NOT',op('EDGE',a,c))), 'TRUE')

    def test_every_lesson_construction_is_typed_and_lossless(self):
        rng=random.Random(42)
        for stage in (5,6):
            for family in FAMILIES[str(stage)]:
                for category in ('focus','composition','helper','held_composite'):
                    for _ in range(3):
                        r=lesson(stage,family,rng,category)
                        self.assertEqual(evaluate(r['input']),independent_evaluate(r['input']))
                        self.assertEqual(decode(encode(r['input'])),r['input'])

    def test_exhaustive_graph_paths(self):
        nodes='ABC'; possible=list(itertools.product(nodes,repeat=2))
        for mask in range(1<<len(possible)):
            w=world(nodes,edges=[list(p) for i,p in enumerate(possible) if mask>>i&1])
            for a,b in possible:
                r=record(w,op('PATH',const('Entity',a),const('Entity',b)))
                self.assertEqual(evaluate(r), independent_evaluate(r))

    def test_provenance_dependency_revision_do_not_collapse(self):
        base=prior.world(list('ABC'), [('PARENT','A','B')],
                         propositions={'J0':prior.relation('PARENT',prior.entity('A'),prior.entity('B'))})
        events=[['E0','ASSERT','S0','J0','support'],['E1','OBSERVE','S1','J0','refute']]
        w=world('ABC',base=base,events=events,links=[['DERIVED_FROM','E1','E0']])
        a,b=[const('Event',e) for e in ('E1','E0')]; p=const('Proposition','J0')
        self.check(w,op('DERIVED_FROM',a,b),'TRUE')
        self.check(w,op('DEPENDENCY',a,b),'FALSE')
        self.check(w,op('SUPERSEDES',a,b),'FALSE')
        self.check(w,op('CURRENT_STATE',p),'CONFLICT')
        self.check(w,op('FORMAL_ENTAILS',p),'TRUE')
        self.check(w,op('OBSERVED_BY',const('Source','S0'),p),'FALSE')
        self.check(w,op('ASSERTED_BY',const('Source','S0'),p),'TRUE')
        revised=copy.deepcopy(w); revised['links']=[['SUPERSEDES','E1','E0']]
        self.check(revised,op('DERIVED_FROM',a,b),'FALSE')
        self.check(revised,op('SUPERSEDES',a,b),'TRUE')
        self.check(revised,op('REVISES',a,b),'TRUE')
        self.check(revised,op('CURRENT_STATE',p),'FALSE')
        self.check(revised,op('HISTORICAL_STATE',p),'CONFLICT')
        self.check(revised,op('FORMAL_ENTAILS',p),'TRUE')

    def test_rejects_ill_typed_and_noninvertible_queries(self):
        w=world('ABC',functions={'F0':[['A','C'],['B','C']]})
        with self.assertRaises(ValueError):
            record(w,op('MEMBER',const('Source','S0'),const('Set','K0')))
        with self.assertRaises(ValueError):
            record(w,op('MAPS',op('INVERSE',const('Function','F0')),const('Entity','C'),const('Entity','A')))
        bad=copy.deepcopy(w); bad['extra']=0
        with self.assertRaises(ValueError): record(bad,op('EDGE',const('Entity','A'),const('Entity','B')))

    def test_admission_requires_retrieval_source_and_formal_validation(self):
        c=candidates()[0]; state=[]
        good=admit(c, [c['candidate_id']], state)
        self.assertEqual(good['disposition'],'accepted')
        bad=copy.deepcopy(c); bad['source']='unknown'
        self.assertEqual(admit(bad,[bad['candidate_id']],state)['disposition'],'rejected')
        self.assertEqual(admit(c,[],state)['disposition'],'deferred')
        collapse=next(c for c in candidates() if c['candidate_id']=='collapse-provenance-supersession')
        self.assertEqual(admit(collapse,[collapse['candidate_id']],state)['disposition'],'rejected')

    def test_live_expansion_preserves_all_trained_weights_and_moments(self):
        model,initial=initialize(ModelConfig(vocab_size=68,width=16,layers=1,heads=2,context=96,precision='fp32'))
        optimizer=make_optimizer(model,default_config())
        x=batch([[7,6,7],[6,7]])
        for _ in range(3):
            optimizer.zero_grad(); model(*x).square().mean().backward(); optimizer.step()
        before={k:v.clone() for k,v in model.state_dict().items()}
        old=torch.clone(model(*x)); moments=copy.deepcopy(optimizer.state_dict())
        rng=torch.get_rng_state().clone(); object_id=id(model)
        receipt=expand(model,optimizer,catalog(),extended_catalog())
        self.assertEqual(id(model),object_id)
        self.assertTrue(torch.equal(rng,torch.get_rng_state()))
        for k,v in before.items():
            self.assertTrue(torch.equal(v,model.state_dict()[k][:68] if k=='embedding.weight' else model.state_dict()[k]))
        self.assertTrue(torch.equal(old,model(*x)))
        after=optimizer.state_dict()
        self.assertEqual(moments['param_groups'],after['param_groups'])
        for i,s in moments['state'].items():
            for k,v in s.items():
                actual=after['state'][i][k]
                if v.ndim==2 and v.shape[0]==68:
                    self.assertTrue(torch.equal(v,actual[:68])); self.assertEqual(int(torch.count_nonzero(actual[68:])),0)
                else: self.assertTrue(torch.equal(v,actual))
        self.assertEqual(receipt['optimizer_steps_before'],[3])
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'checkpoint.pt'; save(p,model,optimizer,extended_catalog(),{'step':3,'expansion':receipt})
            restored,opt,payload=load(p)
            self.assertTrue(torch.equal(model(*x),restored(*x)))
            optimizer.zero_grad();model(*x).square().mean().backward();optimizer.step()
            opt.zero_grad();restored(*x).square().mean().backward();opt.step()
            for a,b in zip(model.parameters(),restored.parameters()): self.assertTrue(torch.equal(a,b))
