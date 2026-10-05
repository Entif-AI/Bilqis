"""Explicit condition-fork adapter; never changes architecture or token allocation."""
from __future__ import annotations
import argparse,json,hashlib,copy
from pathlib import Path
import torch
from .run import write_json,config_identity

def fork(parent:Path,new_config:dict,out:Path)->dict:
    if out.exists():raise FileExistsError("child fork exists")
    receipt=json.loads((parent/"receipt.json").read_text());raw=(parent/"state.pt").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=receipt["payload_sha256"]:raise ValueError("PARENT_PAYLOAD_CHANGED")
    p=torch.load(parent/"state.pt",map_location="cpu",weights_only=True);old=p["config"]
    allowed={"representation","teacher_policy","steps","assistance"};changed=[k for k in set(old)|set(new_config) if old.get(k)!=new_config.get(k)]
    if not set(changed).issubset(allowed):raise ValueError("FORK_CHANGES_ARCHITECTURE_OR_OPTIMIZER")
    if new_config["run_class"]!="ENGINEERING" or new_config["steps"]<=p["state"]["step"]:raise ValueError("FORK_BUDGET_OR_CLASS")
    if "isomorphic" in (old["representation"],new_config["representation"]) and old["representation"]!=new_config["representation"]:raise ValueError("PERMUTATION_REQUIRES_SPECIALIZED_COORDINATE_TRANSFORM; use coupled unit control")
    out.mkdir(parents=True);p["config"]=new_config;p["parent"]=receipt["checkpoint_id"]
    torch.save(p,out/"state.pt");r=copy.deepcopy(receipt);r.update(checkpoint_id="FORK-"+config_identity(new_config)[:12],parent_id=receipt["checkpoint_id"],parent_receipt_sha256=hashlib.sha256((parent/"receipt.json").read_bytes()).hexdigest(),config_sha256=config_identity(new_config),payload_sha256=hashlib.sha256((out/"state.pt").read_bytes()).hexdigest(),fork_changes=changed)
    write_json(out/"receipt.json",r);write_json(out/"fork-lineage.json",{"parent_checkpoint":str(parent),"parent_payload_sha256":receipt["payload_sha256"],"child_config_sha256":config_identity(new_config),"changes":changed,"optimizer_policy":"preserve parent optimizer; any reset is a separate intervention","scientific_efficacy_claim":False});return r

def main():
    p=argparse.ArgumentParser();p.add_argument("--parent",type=Path,required=True);p.add_argument("--config",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();print(json.dumps(fork(a.parent,json.loads(a.config.read_text()),a.out),indent=2))
if __name__=="__main__":main()
