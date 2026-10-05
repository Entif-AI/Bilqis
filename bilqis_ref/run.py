"""Exact, offline engineering runner. Confirmatory SYS additionally requires an external seal custodian and a locked local-model assistance replay."""
from __future__ import annotations
import argparse,json,hashlib,os,time,platform,resource
from dataclasses import asdict
from pathlib import Path
import torch
from .semantics import example,canonical,digest,LABEL_NAMES
from .codec import encode,TOKENS
from .model import ModelConfig,initialize,batch,state_hash
from .teacher import TeacherState,PREREQUISITES
from .pedagogue import request as teacher_request, accept as accept_proposal
from .assistance import read_event


def write_json(path:Path,obj:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+".tmp");tmp.write_bytes(canonical(obj)+b"\n");os.replace(tmp,path)

def config_identity(cfg:dict)->str:
    # Interruption stop and output paths are execution controls, not experimental config.
    return digest(cfg)

def evaluate(model,seed:int,representation:str,stage:int,n:int,transfer:bool=False)->dict:
    model.eval();correct=0;tokens=0;t0=time.perf_counter();out=[]
    with torch.no_grad():
        for i in range(0,n,8):
            records=[example(seed,"iid",stage,j,"DEV",depth=3 if transfer and stage in (3,4) else 2) for j in range(i,min(i+8,n))]
            seq=[encode(e["semantic"],representation,reverse_entities=transfer) for e in records]
            pred=model(*batch(seq)).argmax(-1).tolist();gold=[LABEL_NAMES.index(e["label"]) for e in records]
            correct+=sum(a==b for a,b in zip(pred,gold));tokens+=sum(map(len,seq))
            out.extend({"semantic_sha256":e["semantic_sha256"],"gold":b,"prediction":a} for e,a,b in zip(records,pred,gold))
    return {"correct":correct,"n":n,"tokens":tokens,"seconds":time.perf_counter()-t0,"predictions":out}

def save_checkpoint(out:Path,model,opt,cfg:dict,state:dict,teacher:TeacherState,parent:str|None)->str:
    step=state["step"];name=f"CP-{step:07d}"+("-preprobe" if state.get("pending_probe") is not None else "");dest=out/"checkpoints"/name
    if dest.exists():raise FileExistsError(f"immutable checkpoint exists: {dest}")
    dest.mkdir(parents=True)
    payload={"model":model.state_dict(),"optimizer":opt.state_dict(),"torch_rng":torch.get_rng_state(),"state":state,"teacher":asdict(teacher),"config":cfg,"parent":parent}
    torch.save(payload,dest/"state.pt")
    receipt={"checkpoint_id":name,"parent_id":parent,"step":step,"state_sha256":state_hash(model),
             "payload_sha256":hashlib.sha256((dest/"state.pt").read_bytes()).hexdigest(),"config_sha256":config_identity(cfg),
             "token_abi_sha256":digest(TOKENS),"architecture":asdict(model.config),"parameter_count":sum(p.numel() for p in model.parameters()),
             "precision_recipe":{"linear_forward":"W1.58A8 float emulation" if model.config.precision=="ternary" else "FP32","master":"FP32","gradients":"FP32","optimizer":"FP32","embedding":"FP32","optimized_low_bit_kernel":False},
             "teacher":asdict(teacher),"exposures":state["examples"],"tokens":state["tokens"],"cost":state["cost"],"status":"ENGINEERING_WITNESS"}
    write_json(dest/"receipt.json",receipt);write_json(out/"latest.json",{"checkpoint":str(dest),"checkpoint_id":name})
    return name

def train(cfg:dict,out:Path,resume:Path|None=None,stop_after:int|None=None)->dict:
    if cfg.get("run_class")!="ENGINEERING":raise ValueError("CONFIRMATORY_GATE")
    import jsonschema
    jsonschema.validate(cfg,json.loads((Path(__file__).parents[1]/"schemas/config.schema.json").read_text()))
    if cfg["run_class"]!="ENGINEERING":raise ValueError("CONFIRMATORY_GATE: use the sealed operator procedure; reference command cannot certify a confirmatory run")
    model=initialize(ModelConfig(**cfg["model"]),cfg["seed"])
    opt=torch.optim.AdamW(model.parameters(),lr=cfg["optimizer"]["lr"],betas=tuple(cfg["optimizer"]["betas"]),eps=cfg["optimizer"]["eps"],weight_decay=cfg["optimizer"]["weight_decay"],foreach=False)
    state={"step":0,"examples":0,"tokens":0,"cost":{"generator_seconds":0.,"learner_seconds":0.,"evaluation_seconds":0.},"tranche_stage":0,"stage_example_counters":{str(i):0 for i in range(5)},"teacher_seed_offset":0,"assistance_events":{},"pending_probe":None};teacher=TeacherState();parent=None
    if resume:
        payload=torch.load(resume/"state.pt",map_location="cpu",weights_only=True)
        receipt=json.loads((resume/"receipt.json").read_text())
        if hashlib.sha256((resume/"state.pt").read_bytes()).hexdigest()!=receipt["payload_sha256"]:raise ValueError("CHECKPOINT_CORRUPT")
        if config_identity(payload["config"])!=config_identity(cfg):raise ValueError("CONFIG_MISMATCH")
        model.load_state_dict(payload["model"]);opt.load_state_dict(payload["optimizer"]);torch.set_rng_state(payload["torch_rng"])
        state=payload["state"];teacher=TeacherState(**payload["teacher"]);parent=receipt["checkpoint_id"]
        if state_hash(model)!=receipt["state_sha256"]:raise ValueError("STATE_HASH")
    if cfg.get("assistance",{}).get("event_store"):
        for rid,expected in state["assistance_events"].items():
            if hashlib.sha256((Path(cfg["assistance"]["event_store"])/(rid+".json")).read_bytes()).hexdigest()!=expected:raise ValueError("USED_ASSISTANCE_EVENT_CHANGED")
    out.mkdir(parents=True,exist_ok=True);write_json(out/"config.json",cfg)
    write_json(out/"environment.json",{"python":platform.python_version(),"torch":torch.__version__,"platform":platform.platform(),"threads":torch.get_num_threads(),"deterministic":True,"external_spend":0,"network_used":False,"independent_operator":False})
    limit=min(cfg["steps"],stop_after) if stop_after is not None else cfg["steps"]
    if limit<state["step"]:raise ValueError("stop before resume")
    if not resume:parent=save_checkpoint(out,model,opt,cfg,state,teacher,None)
    while state["step"]<limit or state["pending_probe"] is not None:
        if state["pending_probe"] is not None:
            stage=state["pending_probe"];scores={};t0=time.perf_counter()
            for skill in sorted(set(teacher.promoted+[stage])):
                normal=evaluate(model,cfg["seed"]+700001,cfg["representation"],skill,cfg["probe_n"])
                transfer=evaluate(model,cfg["seed"]+700003,cfg["representation"],skill,cfg["probe_n"],True)
                scores[str(skill)]={"correct":normal["correct"],"n":normal["n"],"transfer_correct":transfer["correct"],"transfer_n":transfer["n"]}
                write_json(out/"probes"/f"{state['step']:07d}-{skill}.json",{"normal":normal,"transfer":transfer,"pool":"DEV; reusable for remediation, not sealed evidence"})
            teacher.decide(stage,scores,cfg["thresholds"],True);state["cost"]["evaluation_seconds"]+=time.perf_counter()-t0
            state["pending_probe"]=None;parent=save_checkpoint(out,model,opt,cfg,state,teacher,parent)
            continue
        step=state["step"]
        if step%cfg["tranche_steps"]==0:
            state["tranche_stage"]=teacher.choose(cfg["teacher_policy"])
            if cfg.get("assistance"):
                assist=cfg["assistance"];eligible=[i for i in range(5) if i not in teacher.promoted and (cfg["teacher_policy"]!="topology" or all(p in teacher.promoted for p in PREREQUISITES[i]))] or [3]
                errors={str(i):round((1-score)*cfg["probe_n"]) for i,score in teacher.last_scores.items()}
                req=teacher_request(state["tranche_stage"],errors,config_identity({k:v for k,v in cfg.items() if k!="assistance"}));reqid=digest(req)
                write_json(out/"pending_teacher_request.json",dict(req,request_sha256=reqid,eligible_stages=eligible))
                if "event_store" in assist:
                    try:record,event_hash=read_event(Path(assist["event_store"]),reqid,assist["model_identity_sha256"],eligible)
                    except FileNotFoundError as exc:raise RuntimeError("TEACHER_REPLAY_MISSING; fill pending request with approved local adapter") from exc
                    state["assistance_events"][reqid]=event_hash
                else:
                    replay_bytes=Path(assist["replay_path"]).read_bytes()
                    if hashlib.sha256(replay_bytes).hexdigest()!=assist["replay_sha256"]:raise ValueError("ASSISTANCE_REPLAY_CHANGED")
                    record=json.loads(replay_bytes).get(reqid)
                    if record is None:raise RuntimeError("TEACHER_REPLAY_MISSING; student checkpoint remains authoritative")
                if not record.get("model_identity_sha256") or not record.get("route_ledger_id"):raise ValueError("ASSISTANCE_IDENTITY_MISSING")
                proposal=accept_proposal(record["proposal"],reqid,eligible);state["tranche_stage"]=proposal["stage"];state["teacher_seed_offset"]=proposal["seed_offset"]
                with (out/"assistance.jsonl").open("a") as f:f.write(json.dumps({"request_sha256":reqid,"step":step,"accepted":True,"record":record,"focus_effect":"audit-only; only stage and seed offset affect this ABI"})+"\n")
        stage=state["tranche_stage"];t0=time.perf_counter();records=[]
        for b in range(cfg["batch_size"]):
            # One deterministic rehearsal item in each four, when prior skills exist.
            s=teacher.promoted[(step+b)%len(teacher.promoted)] if teacher.promoted and b%4==0 else stage
            idx=state["stage_example_counters"][str(s)];records.append(example(cfg["seed"]+state["teacher_seed_offset"],"iid",s,idx,"TRAIN"));state["stage_example_counters"][str(s)]+=1
        seq=[encode(e["semantic"],cfg["representation"]) for e in records];x,l=batch(seq);y=torch.tensor([LABEL_NAMES.index(e["label"]) for e in records])
        state["cost"]["generator_seconds"]+=time.perf_counter()-t0;t0=time.perf_counter();model.train();opt.zero_grad(set_to_none=True)
        loss=torch.nn.functional.cross_entropy(model(x,l),y)
        if not bool(torch.isfinite(loss)):raise RuntimeError("NONFINITE_LOSS")
        loss.backward();grad=float(torch.nn.utils.clip_grad_norm_(model.parameters(),cfg["optimizer"]["clip_norm"]))
        if not (grad>=0 and grad<float('inf')):raise RuntimeError("NONFINITE_GRADIENT")
        opt.step();state["cost"]["learner_seconds"]+=time.perf_counter()-t0;state["step"]+=1;state["examples"]+=len(seq);state["tokens"]+=int(l.sum())
        with (out/"training.jsonl").open("a") as f:
            f.write(json.dumps({"step":state["step"],"stage":stage,"loss":float(loss.detach()),"gradient_norm":grad,"examples":state["examples"],"tokens":state["tokens"],"semantic_hashes":[e["semantic_sha256"] for e in records]})+"\n")
        at_boundary=state["step"]%cfg["tranche_steps"]==0
        if at_boundary:
            state["pending_probe"]=stage
            parent=save_checkpoint(out,model,opt,cfg,state,teacher,parent)
        elif state["step"]==limit:parent=save_checkpoint(out,model,opt,cfg,state,teacher,parent)
    report={"run_class":"ENGINEERING","replication_state":"SMOKE_TESTED" if cfg["profile"]=="smoke" else "COMPLETED_RUN","scientific_efficacy_claim":False,
            "state_sha256":state_hash(model),"last_checkpoint":parent,"examples":state["examples"],"tokens":state["tokens"],"steps":state["step"],"cost":state["cost"],
            "peak_rss_platform_units":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"energy_joules":None,"cash_new_external_spend":0,"teacher":asdict(teacher),"parameter_count":sum(p.numel() for p in model.parameters())}
    write_json(out/"result.json",report);return report

def main():
    p=argparse.ArgumentParser();p.add_argument("--config",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--resume",type=Path);p.add_argument("--stop-after",type=int)
    a=p.parse_args();print(json.dumps(train(json.loads(a.config.read_text()),a.out,a.resume,a.stop_after),indent=2))
if __name__=="__main__":main()
