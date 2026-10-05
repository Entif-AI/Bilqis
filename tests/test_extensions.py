import unittest,tempfile,json,hashlib,copy
from pathlib import Path
import jsonschema
from bilqis_ref.semantics import *
from bilqis_ref.run import train
from bilqis_ref.fork import fork
from bilqis_ref.assistance import read_event,fill
from bilqis_ref.sealing import prepare
from bilqis_ref.evaluate import evaluate

class ExtensionTests(unittest.TestCase):
    @staticmethod
    def cfg():return json.loads((Path(__file__).parents[1]/"configs/smoke-bilqis-ternary.json").read_text())
    def test_preprobe_resume(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cfg=self.cfg();a=train(cfg,root/"a");cp=root/"a/checkpoints/CP-0000002-preprobe";b=train(cfg,root/"b",resume=cp)
            self.assertEqual(a["state_sha256"],b["state_sha256"]);self.assertEqual(a["teacher"],b["teacher"])
    def test_fork_changes_only_allowed_fields(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cfg=self.cfg();train(cfg,root/"a",stop_after=2);cp=root/"a/checkpoints/CP-0000002";child=copy.deepcopy(cfg);child["representation"]="cnl"
            r=fork(cp,child,root/"fork");b=train(child,root/"b",resume=root/"fork");self.assertEqual(b["steps"],4);self.assertEqual(r["fork_changes"],["representation"])
            child["model"]["width"]=64
            with self.assertRaises(ValueError):fork(cp,child,root/"bad")
    def test_paired_counterfactual_evaluator(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);train(self.cfg(),root/"a");prepare(root/"seal",920,4,"SEALED",["cycle"])
            result=evaluate(root/"a/checkpoints/CP-0000004",root/"seal",root/"eval");self.assertEqual(result["counterfactual_pairs"],16);self.assertTrue(0<=result["counterfactual_pair_consistency"]<=1)
    def test_counterfactual_query_unchanged(self):
        found=0
        for i in range(20):
            e=example(300,"iid",2,i);s=e["semantic"];w=World.from_obj(s["world"]);witness=counterfactual_witness(w,s["query"])
            if witness:
                found+=1;w2=apply_counterfactual(w,witness);self.assertNotEqual(oracle(w,s["query"]),oracle(w2,s["query"]))
        self.assertEqual(found,20)
    def test_loopback_only(self):
        with self.assertRaises(ValueError):fill(Path("absent"),Path("absent"),Path("absent"),"https://example.com/v1/chat/completions",Path("absent"))
    def test_event_replay_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p={"request_sha256":"r","stage":0,"seed_offset":1,"focus":"contrast","rationale":"fixture, not model-generated"};r={"request_sha256":"r","model_identity_sha256":"model","proposal":p,"proposal_sha256":digest(p)};(root/"r.json").write_bytes(canonical(r))
            read_event(root,"r","model",[0]);r["proposal"]["seed_offset"]=2;(root/"r.json").write_bytes(canonical(r))
            with self.assertRaises(ValueError):read_event(root,"r","model",[0])
    def test_json_schema_parity(self):
        schema=json.loads((Path(__file__).parents[1]/"schemas/semantic.schema.json").read_text());s=example(1,"iid",3,0)["semantic"];jsonschema.validate(s,schema);s["gold"]="TRUE"
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(s,schema)
    def test_bool_ids_rejected(self):
        w=example(3,"iid",0,0)["semantic"]["world"];w["entities"][0]["id"]=False
        with self.assertRaises(ValueError):World.from_obj(w)
