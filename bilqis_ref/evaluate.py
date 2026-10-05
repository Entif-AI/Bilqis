"""Read a fixed checkpoint and evaluate immutable cases without training or feedback."""
from __future__ import annotations
import argparse,json,hashlib,time
from pathlib import Path
from collections import defaultdict
import torch
from .semantics import canonical,LABEL_NAMES,LABELS,digest,World,validate_query,apply_counterfactual,oracle,independent_oracle
from .codec import encode
from .model import initialize,ModelConfig,batch,state_hash
from .sealing import verify_opening

def evaluate(checkpoint:Path,seal:Path,out:Path)->dict:
    if out.exists():raise FileExistsError("evaluation output is append-only")
    verify_opening(seal);receipt=json.loads((checkpoint/"receipt.json").read_text());raw=(checkpoint/"state.pt").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=receipt["payload_sha256"]:raise ValueError("CHECKPOINT_CHANGED")
    payload=torch.load(checkpoint/"state.pt",map_location="cpu",weights_only=True);cfg=payload["config"];m=initialize(ModelConfig(**cfg["model"]),cfg["seed"]);m.load_state_dict(payload["model"]);m.eval()
    if state_hash(m)!=receipt["state_sha256"]:raise ValueError("MODEL_IDENTITY")
    cases=[json.loads(x) for x in (seal/"evaluator-input/cases.jsonl").read_text().splitlines()];gold={x["case_id"]:x["label"] for x in map(json.loads,(seal/"custodian-private/gold.jsonl").read_text().splitlines())}
    gold_records={x["case_id"]:x for x in map(json.loads,(seal/"custodian-private/gold.jsonl").read_text().splitlines())}
    pair_results=[];predictions=[];strata=defaultdict(list);before=state_hash(m);t0=time.perf_counter()
    with torch.no_grad():
        for c in cases:
            s=c["semantic"];World.from_obj(s["world"]);validate_query(s["query"],len(s["world"]["entities"]))
            if digest(s)!=c["semantic_sha256"]:raise ValueError("SEMANTIC_HASH")
            pred=LABEL_NAMES[int(m(*batch([encode(s,cfg["representation"])] )).argmax(-1)[0])];ok=pred==gold[c["case_id"]]
            strata[f"{c['family']}/s{c['stage']}"].append(int(ok));predictions.append({"case_id":c["case_id"],"prediction":pred,"gold":gold[c["case_id"]],"correct":ok})
            witness=gold_records[c["case_id"]].get("world_intervention_witness")
            if witness is not None:
                w2=apply_counterfactual(World.from_obj(s["world"]),witness);q=s["query"];a=oracle(w2,q)
                if a!=independent_oracle(w2,q):raise RuntimeError("COUNTERFACTUAL_ORACLE_DISAGREEMENT")
                target2=LABEL_NAMES[LABELS.index(a)]
                if target2==gold[c["case_id"]]:raise ValueError("COUNTERFACTUAL_DID_NOT_FLIP")
                s2={"abi":s["abi"],"world":w2.obj(),"query":q};pred2=LABEL_NAMES[int(m(*batch([encode(s2,cfg["representation"])] )).argmax(-1)[0])]
                pair_results.append({"case_id":c["case_id"],"original_correct":ok,"counterfactual_prediction":pred2,"counterfactual_gold":target2,"both_correct":bool(ok and pred2==target2)})
    if before!=state_hash(m):raise RuntimeError("EVALUATOR_MUTATED_MODEL")
    summary={"run_class":"ENGINEERING_EVALUATION","independent_custody_verified":False,"model_state_sha256":before,"cases":len(cases),"macro_stratum_accuracy":sum(sum(v)/len(v) for v in strata.values())/len(strata),"primary_world_sensitive_macro_accuracy":sum(sum(v)/len(v) for k,v in strata.items() if not k.endswith("/s0"))/sum(not k.endswith("/s0") for k in strata),"strata":{k:{"n":len(v),"correct":sum(v)} for k,v in strata.items()},"counterfactual_pairs":len(pair_results),"counterfactual_pair_consistency":sum(x["both_correct"] for x in pair_results)/len(pair_results) if pair_results else None,"evaluation_seconds":time.perf_counter()-t0,"scientific_efficacy_claim":False}
    out.mkdir(parents=True);(out/"predictions.jsonl").write_bytes(b"".join(canonical(x)+b"\n" for x in predictions));(out/"counterfactual-pairs.jsonl").write_bytes(b"".join(canonical(x)+b"\n" for x in pair_results));(out/"summary.json").write_bytes(canonical(summary)+b"\n");return summary

def main():
    p=argparse.ArgumentParser();p.add_argument("--checkpoint",type=Path,required=True);p.add_argument("--seal",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();print(json.dumps(evaluate(a.checkpoint,a.seal,a.out),indent=2))
if __name__=="__main__":main()
