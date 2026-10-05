"""Custodian-side file separation and commitments. Not a sandbox or independent custody by itself."""
from __future__ import annotations
import argparse,hashlib,json,secrets,os
from pathlib import Path
from .semantics import example,canonical,digest,World,counterfactual_witness

def prepare(out:Path,seed:int,n:int,pool:str,families:list[str],forbidden_hashes:set[str]|None=None)->dict:
    if out.exists():raise FileExistsError("Never overwrite a sealed epoch")
    if pool not in ("DEV","SEALED") or n<4 or n%4:raise ValueError("pool/count")
    out.mkdir(parents=True);private=out/"custodian-private";public=out/"evaluator-input";private.mkdir(mode=0o700);public.mkdir()
    seen=set(forbidden_hashes or ());rows=[];gold=[]
    for family in families:
        for stage in range(5):
            accepted=0;index=0;attempts=0
            while accepted<n:
                e=example(seed,family,stage,index,pool,depth=3 if stage in (3,4) else 2)
                witness=counterfactual_witness(World.from_obj(e["semantic"]["world"]),e["semantic"]["query"])
                if e["semantic_sha256"] in seen or (stage>0 and witness is None):
                    index+=4 if stage==4 else 2;attempts+=1
                    if attempts>100000:raise RuntimeError("SENSITIVE_SEAL_GENERATION_LIMIT")
                    continue
                seen.add(e["semantic_sha256"]);case_id=f"{family}-s{stage}-{accepted:06d}"
                rows.append({"case_id":case_id,"stage":stage,"family":family,"semantic":e["semantic"],"semantic_sha256":e["semantic_sha256"],"world_sensitive":witness is not None})
                gold.append({"case_id":case_id,"label":e["label"],"provenance":e["provenance"],"world_intervention_witness":witness});accepted+=1;index=accepted
    inputs=b"".join(canonical(x)+b"\n" for x in rows);targets=b"".join(canonical(x)+b"\n" for x in gold)
    (public/"cases.jsonl").write_bytes(inputs);(private/"gold.jsonl").write_bytes(targets)
    salt=secrets.token_hex(32);commitment=hashlib.sha256(salt.encode()+targets).hexdigest()
    (private/"opening.json").write_bytes(canonical({"salt":salt,"seed":seed,"gold_sha256":hashlib.sha256(targets).hexdigest()})+b"\n")
    manifest={"schema":"bilqis.seal/0.1","pool":pool,"case_count":len(rows),"families":families,"per_family_stage":n,"primary_stages":[1,2,3,4],"primary_inclusion":"one legal world-only intervention changes the answer; stage 0 is diagnostic only",
              "inputs_sha256":hashlib.sha256(inputs).hexdigest(),"gold_commitment_sha256":commitment,
              "custody":"LOCAL_ENGINEERING_ONLY; move private directory and seed to independent custodian for confirmatory use",
              "leakage_boundary":"evaluator-input is not learner TRAIN or DEV; do not expose before locked milestone"}
    (out/"manifest.json").write_bytes(canonical(manifest)+b"\n");return manifest

def verify_opening(root:Path)->bool:
    manifest=json.loads((root/"manifest.json").read_text());opening=json.loads((root/"custodian-private/opening.json").read_text());gold=(root/"custodian-private/gold.jsonl").read_bytes()
    if hashlib.sha256((root/"evaluator-input/cases.jsonl").read_bytes()).hexdigest()!=manifest["inputs_sha256"]:raise ValueError("INPUTS_CHANGED")
    if hashlib.sha256(opening["salt"].encode()+gold).hexdigest()!=manifest["gold_commitment_sha256"]:raise ValueError("GOLD_OPENING_CHANGED")
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True,type=Path);p.add_argument("--seed",required=True,type=int);p.add_argument("--n",type=int,default=512);p.add_argument("--pool",choices=["DEV","SEALED"],default="SEALED");p.add_argument("--families",nargs="+",default=["cycle","blocks"]);p.add_argument("--exclude",type=Path)
    a=p.parse_args();excluded=set(json.loads(a.exclude.read_text())) if a.exclude else set();print(json.dumps(prepare(a.out,a.seed,a.n,a.pool,a.families,excluded),indent=2))
if __name__=="__main__":main()
