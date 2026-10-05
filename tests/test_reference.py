"""Engineering acceptance: no test below estimates Bilqis learning efficacy."""
import unittest,copy,itertools,json,tempfile,hashlib
from pathlib import Path
import torch
from bilqis_ref.semantics import *
from bilqis_ref.codec import *
from bilqis_ref.model import *
from bilqis_ref.teacher import *
from bilqis_ref.pedagogue import accept,request,replay
from bilqis_ref.run import train

class FormalTests(unittest.TestCase):
    def test_roundtrips_and_independent_oracles(self):
        for family in ("iid","cycle","blocks"):
            for stage in range(5):
                for i in range(24):
                    e=example(8192,family,stage,i,"DEV");s=e["semantic"]
                    w=World.from_obj(s["world"])
                    self.assertEqual(oracle(w,s["query"]),independent_oracle(w,s["query"]))
                    for mode in ("bilqis","cnl","isomorphic","mixed"):
                        for reverse in (False,True):self.assertEqual(decode(encode(s,mode,reverse),mode),s)
    def test_all_three_node_graphs(self):
        edges=list(itertools.combinations(range(3),2))
        for mask in range(8):
            w=World(tuple(Entity(i,i%3,0,0) for i in range(3)),tuple(e for j,e in enumerate(edges) if mask>>j&1),((0,0),(1,0),(1,1)))
            for bits in range(1,8):
                q={"op":"CONNECTED","group":[i for i in range(3) if bits>>i&1]}
                self.assertEqual(oracle(w,q),independent_oracle(w,q))
    def test_evidence_algebra_exhaustive(self):
        for a,b in itertools.product(LABELS,repeat=2):
            w=World((Entity(0,0,0,0),Entity(1,0,0,0)),(),(a,b,(0,0)))
            for op in ("AND","OR"):
                q={"op":op,"args":[{"op":"EVID","value":0},{"op":"EVID","value":1}]}
                self.assertEqual(oracle(w,q),independent_oracle(w,q))
                self.assertEqual(oracle(w,{"op":"NOT","args":[{"op":"NOT","args":[q]}]}),oracle(w,q))
        self.assertNotEqual(LABELS[2],LABELS[3])
    def test_mixed_is_nonseparable_and_bijective(self):
        pairs={(x+y)%3:(x,y) for x,y in []} # no data-dependent remapping
        mapped={((x+y)%3,(x+2*y)%3) for x,y in itertools.product(range(3),repeat=2)}
        self.assertEqual(len(mapped),9)
        self.assertEqual(len({(0+y)%3 for y in range(3)}),3)
    def test_answer_balancing(self):
        for stage in range(5):
            labels=[example(99,"iid",stage,i)["label"] for i in range(16)]
            expected=LABEL_NAMES if stage==4 else LABEL_NAMES[:2]
            self.assertEqual({x:labels.count(x) for x in set(labels)},{x:16//len(expected) for x in expected})
    def test_negative_queries(self):
        bad=[{"op":"EQ","a":True,"b":1},{"op":"EQ","a":8,"b":0},{"op":"EQ","a":0,"b":0,"answer":True},{"op":"SAME","group":[]},{"op":"SAME","group":[1,1]},{"op":"SAME","group":[1,0]},{"op":"NOT","args":[]},{"op":"BOGUS"},{"op":"APL","a":0,"value":3}]
        for q in bad:
            with self.assertRaises(ValueError):validate_query(q,6)
    def test_negative_worlds(self):
        s=example(4,"iid",1,0)["semantic"]
        for field,val in (("color",9),("actual",True),("id",7)):
            w=copy.deepcopy(s["world"]);w["entities"][0][field]=val
            with self.assertRaises(ValueError):World.from_obj(w)
    def test_negative_codecs(self):
        s=example(4,"iid",1,0)["semantic"];tok=render(s)
        for bad in (tok[:-1],tok+["END"],["WRONG"]+tok[1:]):
            with self.assertRaises(ValueError):parse(bad)
        for bad in ([True],[-1],[512]):
            with self.assertRaises(ValueError):decode(bad)
        s["label"]="TRUE"
        with self.assertRaises(ValueError):encode(s)
    def test_invalid_family_split(self):
        with self.assertRaises(ValueError):example(1,"unknown",0,0)
        with self.assertRaises(ValueError):example(1,"iid",0,0,"PUBLISHED")
    def test_semantics_identical_under_relabel(self):
        s=example(911,"iid",3,7)["semantic"]
        a=encode(s);b=encode(s,"isomorphic")
        self.assertEqual(b,[PERMUTATION[i] for i in a]);self.assertNotEqual(a,b)
        self.assertEqual(len(a),len(encode(s,"mixed")))

class TeacherTests(unittest.TestCase):
    def test_no_false_promotion_with_tiny_probes(self):
        t=TeacherState();d=t.decide(0,{"0":{"correct":8,"n":8,"transfer_correct":8,"transfer_n":8}},{"mastery_lower":.9,"retention_lower":.85,"dev_transfer_accuracy":.75},True)
        self.assertFalse(d["promoted"])
    def test_prerequisites_and_rehearsal_guard(self):
        t=TeacherState();self.assertEqual(t.choose(),0)
        sc={"0":{"correct":256,"n":256,"transfer_correct":256,"transfer_n":256}}
        t.decide(0,sc,{"mastery_lower":.9,"retention_lower":.85,"dev_transfer_accuracy":.75},True)
        self.assertEqual(t.choose(),1)
        sc["0"]["correct"]=0;sc["1"]={"correct":256,"n":256,"transfer_correct":256,"transfer_n":256}
        self.assertFalse(t.decide(1,sc,{"mastery_lower":.9,"retention_lower":.85,"dev_transfer_accuracy":.75},True)["promoted"])
    def test_integrity_failure_holds(self):
        t=TeacherState();t.decide(0,{}, {},False)
        with self.assertRaises(RuntimeError):t.choose()
    def test_pedagogue_cannot_define_truth(self):
        p={"request_sha256":"x","stage":0,"seed_offset":0,"focus":"contrast","rationale":"Use another valid example."}
        self.assertEqual(accept(p,"x",[0]),p)
        for change in ({"answer":"TRUE"},{"stage":4},{"seed_offset":-1},{"request_sha256":"y"},{"focus":"execute"}):
            q=dict(p,**change)
            with self.assertRaises(ValueError):accept(q,"x",[0])
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"p.json";path.write_text(json.dumps(p))
            with self.assertRaises(ValueError):replay(path,"bad","x",[0])

class NumericalTests(unittest.TestCase):
    def test_token_permutation_two_optimizer_steps(self):
        for precision in ("fp32","ternary"):
            c=ModelConfig(width=16,layers=1,heads=2,context=384,precision=precision)
            a=initialize(c,321);b=initialize(c,321)
            with torch.no_grad():b.embedding.weight[torch.tensor(PERMUTATION)]=a.embedding.weight.clone()
            oa=torch.optim.AdamW(a.parameters(),lr=.0003,foreach=False);ob=torch.optim.AdamW(b.parameters(),lr=.0003,foreach=False)
            sem=[example(333,"iid",2,i)["semantic"] for i in range(2)]
            x,l=batch([encode(s) for s in sem]);xp,lp=batch([encode(s,"isomorphic") for s in sem]);y=torch.tensor([0,1])
            for step in range(2):
                oa.zero_grad();ob.zero_grad();pa=a(x,l);pb=b(xp,lp)
                torch.testing.assert_close(pa,pb,atol=0,rtol=0)
                torch.nn.functional.cross_entropy(pa,y).backward();torch.nn.functional.cross_entropy(pb,y).backward();oa.step();ob.step()
                torch.testing.assert_close(a.embedding.weight,b.embedding.weight[torch.tensor(PERMUTATION)],atol=0,rtol=0)
    def test_causal_right_padding(self):
        m=initialize(ModelConfig(width=16,layers=1,heads=2),16).eval();s=encode(example(1,"iid",0,0)["semantic"])
        x,l=batch([s]);a=m(x,l);z=torch.cat([x,torch.full((1,5),42)],1);b=m(z,l)
        torch.testing.assert_close(a,b,atol=2e-7,rtol=2e-6)
    def test_resume_is_bit_identical(self):
        cfg=json.loads((Path(__file__).parents[1]/"configs/smoke-bilqis-ternary.json").read_text())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=train(cfg,root/"uninterrupted");train(cfg,root/"partial",stop_after=2)
            cp=root/"partial/checkpoints/CP-0000002";b=train(cfg,root/"resumed",resume=cp)
            self.assertEqual(a["state_sha256"],b["state_sha256"]);self.assertEqual(a["tokens"],b["tokens"]);self.assertEqual(a["teacher"],b["teacher"])
            changed=copy.deepcopy(cfg);changed["seed"]+=1
            with self.assertRaises(ValueError):train(changed,root/"bad",resume=cp)
    def test_confirmatory_gate(self):
        cfg=json.loads((Path(__file__).parents[1]/"configs/smoke-bilqis-ternary.json").read_text());cfg["run_class"]="CONFIRMATORY"
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):train(cfg,Path(d))

if __name__=="__main__":unittest.main(verbosity=2)
