"""Durable, one-student, auto-mutating skill-tree training loop.

Thousands of lessons should not require thousands of assistant turns. A
single model+AdamW+semantic graph continues through grades. The teacher
chooses and mutates strategies based on *observed* learning outcomes; weak
or regressed lessons are practice signals, not automatic rollback triggers.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import signal
import shutil
import statistics
import time
import uuid

import torch
from torch.nn import functional as F

from bilqis_active import load_active
from bilqis_development.continuation import load as load_checkpoint
from bilqis_development.continuation import save as save_checkpoint
from bilqis_development.continuation import expand
from bilqis_micro.graph import STATES
from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import batch, state_hash
from bilqis_logic.kernel import digest

from .arithmetic import extend_graph
from .grades import skill_tree
from .lessons import TeacherLibrary, compose_batch, encode
from .grow import grow, compare_outputs

VERSION = "bilqis.school.auto-spiral/v1"
ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "school50-continuous-v1"
STATE = "state.json"
KNOBS = {
    "old": [4, 8, 12, 16, 20],
    "preview": [0, 2, 4],
    "depth": [1, 2, 3, 4],
    "contrast": [0.0, 0.5, 1.0],
    "lr": [0.00004, 0.00008, 0.00013, 0.0002, 0.0003],
    "distill": [0.0, 0.15, 0.35, 0.65],
}
INITIAL = (
    {"old":12,"preview":2,"depth":2,"contrast":.5,"lr":.00013,"distill":.15},
    {"old":20,"preview":0,"depth":2,"contrast":1.,"lr":.00008,"distill":.65},
    {"old":8,"preview":4,"depth":3,"contrast":1.,"lr":.00020,"distill":.15},
    {"old":16,"preview":2,"depth":1,"contrast":.0,"lr":.00008,"distill":.35},
)
MAX_STRATEGIES = 512
GRADES = skill_tree()
REPORT_GRADES = tuple(g.number for g in GRADES if g.ready)
REPORT_GRADE_IDS = tuple(f"G{grade:02d}" for grade in REPORT_GRADES)
BASELINE_PROBE_PROFILE = "school50-fixed-24-v1"
GRADE_CHAMPION_PROFILE = "school50-grade-champion-48-v1"
GRADE_CHAMPION_COUNT = 48
CANDIDATE_CLEAR_REWARD = 0.05
CANDIDATE_SENTINEL_PER_GRADE = 8
CANDIDATE_MAX_ATTEMPTS = 3
CONSOLIDATION_WEIGHT = 0.15


def _read(path):
    return json.loads(Path(path).read_text())


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _atomic_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_name(path.name+"."+uuid.uuid4().hex+".tmp")
    with temporary.open("x") as stream:
        json.dump(obj,stream,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary,path)


def _policy_key(policy):
    return hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest()[:12]


def _stats():
    return {"trials":0,"reward_sum":0.0,"reward_ema":0.0,"latest":None}


def _teacher():
    return {"strategies":{_policy_key(p):dict(p) for p in INITIAL},
            "global_stats":{_policy_key(p):_stats() for p in INITIAL},
            "grade_stats":{}, "events":0, "mutations":0}


def mutate(teacher, rng):
    """Change ONE permitted knob, record it once, reuse across later grades."""
    if len(teacher["strategies"])>=MAX_STRATEGIES:return None
    viable=[(key,info) for key,info in teacher["global_stats"].items()
            if info["trials"]]
    base=teacher["strategies"][max(viable,key=lambda v:v[1]["reward_ema"])[0]] if viable \
         else rng.choice(list(teacher["strategies"].values()))
    for _ in range(24):
        variant=dict(base)
        field=rng.choice(list(KNOBS))
        candidates=[v for v in KNOBS[field] if v!=variant[field]]
        variant[field]=rng.choice(candidates)
        if variant["old"]+variant["preview"]>24:continue
        identity=_policy_key(variant)
        if identity not in teacher["strategies"]:
            teacher["strategies"][identity]=variant
            teacher["global_stats"][identity]=_stats()
            teacher["mutations"]+=1
            return identity
    return None


def pick(teacher, grade, rng, exclude=None):
    if teacher["events"] and teacher["events"] % 3 == 0:
        mutate(teacher,rng)
    local=teacher["grade_stats"].get(str(grade),{})
    total=teacher["events"]+1
    excluded=set(exclude or ())
    def rank(item):
        key, policy=item
        info=local.get(key) or teacher["global_stats"][key]
        if info["trials"]==0:
            return 10 + rng.random()
        exploitation=info["reward_sum"]/info["trials"]
        exploration=0.6*math.sqrt(math.log(total+2)/(1+info["trials"]))
        return exploitation+exploration
    choices=[
        item for item in teacher["strategies"].items()
        if item[0] not in excluded
    ]
    if not choices:
        raise ValueError("NO_UNTRIED_TEACHER_STRATEGY_FOR_GRADE_ATTEMPT")
    return max(choices,key=rank)


def observe(teacher, grade, policy_key, reward):
    if not math.isfinite(reward):
        raise ValueError("NONFINITE_TEACHER_REWARD")
    for entry in (teacher["global_stats"][policy_key],
                  teacher["grade_stats"].setdefault(str(grade),{}).setdefault(policy_key,_stats())):
        entry["trials"]+=1
        entry["reward_sum"]+=reward
        entry["reward_ema"]=reward if entry["latest"] is None else (
            .8*entry["reward_ema"]+.2*reward)
        entry["latest"]=reward
    teacher["events"]+=1


def _checkpoint(run_dir, model, optimizer, graph, metadata):
    destination=run_dir/("student-"+str(metadata["step"])+"-"+uuid.uuid4().hex[:12]+".pt")
    save_checkpoint(destination,model,optimizer,graph,metadata)
    return destination.name, _sha(destination)


def _checkpoint_step(path):
    parts=Path(path).stem.split("-",2)
    if len(parts)!=3 or parts[0]!="student":
        raise ValueError("INVALID_STUDENT_CHECKPOINT_NAME")
    return int(parts[1])


def _checkpoint_retention_plan(out, state, *, keep_recent=8, keep_pass=4):
    """Return conservative keep/delete sets without mutating disk or state."""
    if keep_recent < 0 or keep_pass < 0:
        raise ValueError("INVALID_CHECKPOINT_RETENTION_REQUEST")
    out=Path(out)
    checkpoints=list(out.glob("student-*.pt"))
    protected=set()

    def protect(name):
        if name and (out/name).is_file():
            protected.add(name)

    # Runtime-critical anchors are never eligible for pruning.
    protect(state.get("checkpoint"))
    protect(state.get("school_start_checkpoint"))
    protect(state.get("accepted_pass",{}).get("checkpoint"))
    protect(state.get("champion_pass",{}).get("checkpoint"))
    for champion in state.get("grade_champions",{}).values():
        protect(champion.get("checkpoint"))
    for event in state.get("architecture_history",[]):
        protect(event.get("from"))
        protect(event.get("to"))

    # Keep several recent pass-end snapshots for manual recovery/comparison.
    pass_steps=[
        row["optimizer_step"] for row in state.get("grade_ledger",[])
        if row.get("grade")==REPORT_GRADE_IDS[-1]
    ]
    if keep_pass:
        for step in pass_steps[-keep_pass:]:
            for path in out.glob(f"student-{step}-*.pt"):
                protected.add(path.name)

    # Keep a short rolling tail of ordinary grade checkpoints as crash/recovery
    # insurance. mtime disambiguates same-step growth migrations.
    if keep_recent:
        recent=sorted(
            checkpoints,
            key=lambda path:(
                _checkpoint_step(path),path.stat().st_mtime_ns,path.name)
        )[-keep_recent:]
        protected.update(path.name for path in recent)

    keep=[path for path in checkpoints if path.name in protected]
    delete=[path for path in checkpoints if path.name not in protected]
    return {"keep":keep,"delete":delete,"protected_names":protected}


def _prune_checkpoints(out, state, *, keep_recent=8, keep_pass=4):
    """Delete only checkpoint binaries outside the durable retention set."""
    plan=_checkpoint_retention_plan(
        out,state,keep_recent=keep_recent,keep_pass=keep_pass)
    deleted_bytes=0
    for path in plan["delete"]:
        deleted_bytes+=path.stat().st_size
        path.unlink()
    remaining=list(Path(out).glob("student-*.pt"))
    remaining_bytes=sum(path.stat().st_size for path in remaining)
    retention=state.setdefault("checkpoint_retention",{})
    retention.update({
        "enabled":True,
        "keep_recent":keep_recent,
        "keep_pass":keep_pass,
        "last_pruned_count":len(plan["delete"]),
        "last_pruned_bytes":deleted_bytes,
        "retained_count":len(remaining),
        "retained_bytes":remaining_bytes,
        "last_pruned_optimizer_step":state["optimizer_step"],
        "total_pruned_count":(
            retention.get("total_pruned_count",0)+len(plan["delete"])),
        "total_pruned_bytes":(
            retention.get("total_pruned_bytes",0)+deleted_bytes),
    })
    return retention


def _validate(checkpoint, state):
    path=Path(checkpoint)
    if not path.is_file() or _sha(path)!=state["checkpoint_sha256"]:
        raise ValueError("RUNNER_CURRENT_CHECKPOINT_MISSING_OR_CHANGED")
    model,optimizer,payload=load_checkpoint(path)
    if (state_hash(model)!=state["model_sha256"] or
        optimizer_receipt(optimizer)["steps"]!=[state["optimizer_step"]] or
        len(payload["graph"]["tokens"])!=state["vocab"] or
        digest(payload["graph"])!=state["graph_sha256"]):
        raise ValueError("RUNNER_CANNOT_RECONSTRUCT_CONTINUOUS_STUDENT")
    return model,optimizer,payload


def initialize(out=RUN):
    out=Path(out)
    if out.exists():
        raise FileExistsError("CONTINUING_RUN_ALREADY_INITIALIZED")
    model,optimizer,prior,source=load_active()
    original_step=optimizer_receipt(optimizer)["steps"]
    if original_step != [13848]:
        raise ValueError("WRONG_ACTIVE_LEARNER_FOR_INITIAL_SCHOOL_MIGRATION")
    graph=extend_graph(prior["graph"])
    migration=expand(model,optimizer,prior["graph"],graph)
    if optimizer_receipt(optimizer)["steps"] != original_step:
        raise ValueError("VOCAB_EXPANSION_RESET_OPTIMIZER")
    out.mkdir(parents=True,exist_ok=False)
    name,checksum=_checkpoint(out,model,optimizer,graph,{
        "epoch":VERSION,"step":13848,"parent_checkpoint_sha256":source["checkpoint_sha256"],
        "vocabulary_expansion":migration,
        "no_model_reset":True,"no_optimizer_reset":True,
    })
    state={"version":VERSION,"checkpoint":name,"checkpoint_sha256":checksum,
           "model_sha256":state_hash(model),
           "optimizer_step":13848,"vocab":len(graph["tokens"]),
           "graph_sha256":digest(graph),
           "parent_checkpoint_sha256":source["checkpoint_sha256"],
           "school_start_checkpoint":name,
           "school_start_checkpoint_sha256":checksum,
           "next_grade":1,"spiral_pass":1,"completed_grades":0,
           "completed_updates":0,"attempted_updates":0,"teacher":_teacher(),
           "blocked_grade_ids":[g.id for g in GRADES if not g.ready],
           "grade_ledger":[],"candidate_ledger":[],"last_results":{},
           "no_retention_rollback":True,
           "last_run_wall_seconds":0.0}
    _atomic_json(out/STATE,state)
    return state


def grow_active_school(out=RUN, *, factor=4, layers=6):
    """Grow one stopped student at a durable grade boundary, never restart."""
    out=Path(out)
    state=_read(out/STATE)
    before,optimizer,payload=_validate(out/state["checkpoint"],state)
    if before.config.width*factor>768 or before.config.layers>=layers:
        raise ValueError("MODEL_GROWTH_REQUIRES_NEW_UNREPEATED_CAPACITY")
    larger,larger_optimizer,receipt=grow(before,optimizer,factor=factor,layers=layers)
    lib=TeacherLibrary()
    representative=[]
    for grade in (1,4,8,10,14,17,19,22):
        policy={"old":12,"preview":2,"depth":2,"contrast":1.,
                "lr":.00013,"distill":.35}
        rows,_=compose_batch(lib,grade,policy,payload["graph"],random.Random(grade))
        representative.append(batch([encode(r,payload["graph"]) for r in rows]))
    parity=compare_outputs(before,larger,representative)
    if optimizer_receipt(larger_optimizer)["steps"]!=[state["optimizer_step"]]:
        raise ValueError("MODEL_GROWTH_RESET_ADAMW")
    previous_name,previous_sha=state["checkpoint"],state["checkpoint_sha256"]
    next_name,next_sha=_checkpoint(out,larger,larger_optimizer,payload["graph"],{
        "epoch":VERSION,"step":state["optimizer_step"],
        "migrated_from":previous_name,"migrated_from_sha256":previous_sha,
        "function_preservation_proof":parity,"expansion":receipt})
    # Reopen the *actual* new binary and prove identity before updating the
    # active pointer. Interrupted growth leaves the old pointer authoritative.
    proof={"checkpoint_sha256":next_sha,"optimizer_step":state["optimizer_step"],
           "vocab":state["vocab"],"graph_sha256":state["graph_sha256"],
           "model_sha256":state_hash(larger)}
    reloaded,restored,_=_validate(out/next_name,proof)
    if state_hash(reloaded)!=state_hash(larger):
        raise ValueError("GROWN_CHECKPOINT_READBACK_CHANGED_WEIGHTS")
    state["checkpoint"],state["checkpoint_sha256"]=next_name,next_sha
    state["model_sha256"]=proof["model_sha256"]
    state.setdefault("architecture_history",[]).append({
        "from":previous_name,"from_sha256":previous_sha,
        "to":next_name,"to_sha256":next_sha,
        "step":state["optimizer_step"],"proof":parity,"parameters":receipt})
    _atomic_json(out/STATE,state)
    return {"status":"FUNCTION_PRESERVING_GROWTH_VERIFIED",
            "student_optimizer_step":state["optimizer_step"],
            "old_parameters":receipt["old_parameters"],
            "new_parameters":receipt["new_parameters"],
            "representation_parity":parity,
            "active_checkpoint":str(out/next_name),
            "active_checkpoint_sha256":next_sha}


def _device(model, optimizer, name):
    if name=="mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS_NOT_AVAILABLE")
    if name not in ("cpu","mps"):raise ValueError("UNSUPPORTED_LEARNER_DEVICE")
    model.to(name)
    for data in optimizer.state.values():
        for key,val in data.items():
            if isinstance(val,torch.Tensor):
                data[key]=val.to(name)
    return torch.device(name)


def _probe_metrics(model, lib, graph, grade, seed, *, count=24, device="cpu"):
    rng=random.Random(seed)
    rows=[]
    for i in range(count):
        packet=lib.one(grade,rng,depth=2 if i%3 else 3,
                       prefer_composition=i%2==0,
                       truth=bool(i%2) if grade>=19 else None)
        rows.append(packet[i%len(packet)] if isinstance(packet,list) else packet)
    old_training=model.training
    model.eval()
    with torch.no_grad():
        ids,lengths=batch([encode(row,graph) for row in rows],device=device)
        logits=model(ids,lengths)
        labels=torch.tensor(
            [STATES.index(row["gold"]) for row in rows],
            device=device,dtype=torch.long)
        predictions=logits.argmax(-1).cpu().tolist()
        correct=sum(STATES[i]==row["gold"] for i,row in zip(predictions,rows))
        probs=F.softmax(logits,dim=-1)
        correct_prob=probs.gather(1,labels[:,None]).squeeze(1)
        masked=logits.clone()
        masked.scatter_(1,labels[:,None],float("-inf"))
        margin=logits.gather(1,labels[:,None]).squeeze(1)-masked.max(-1).values
        cross=F.cross_entropy(logits,labels)
    if old_training:model.train()
    return {
        "accuracy":correct/count,
        "cross_entropy":float(cross.detach().cpu()),
        "correct_probability":float(correct_prob.mean().detach().cpu()),
        "margin":float(margin.mean().detach().cpu()),
    }


def _scores(model, lib, graph, grade, seed, *, count=24, device="cpu"):
    return _probe_metrics(
        model,lib,graph,grade,seed,count=count,device=device)["accuracy"]


def _sentinel_metrics(model, lib, graph, *, device,
                      count_per_grade=CANDIDATE_SENTINEL_PER_GRADE):
    metrics=[
        _probe_metrics(
            model,lib,graph,grade,971003+grade*811,
            count=count_per_grade,device=device)
        for grade in REPORT_GRADES
    ]
    return {
        name:sum(item[name] for item in metrics)/len(metrics)
        for name in ("accuracy","cross_entropy","correct_probability","margin")
    }


def _candidate_gate_decision(reward, before_sentinel=None, after_sentinel=None,
                             *, clear_reward=CANDIDATE_CLEAR_REWARD):
    if reward <= -clear_reward:
        return {"decision":"REJECT","reason":"CLEAR_REWARD_LOSS"}
    if before_sentinel is None or after_sentinel is None:
        return {
            "decision":"MEASURE",
            "reason":(
                "CLEAR_REWARD_WIN_NEEDS_SENTINEL"
                if reward >= clear_reward else "AMBIGUOUS_REWARD"),
        }
    deltas={
        "accuracy":after_sentinel["accuracy"]-before_sentinel["accuracy"],
        "cross_entropy":before_sentinel["cross_entropy"]-after_sentinel["cross_entropy"],
        "correct_probability":(
            after_sentinel["correct_probability"]-
            before_sentinel["correct_probability"]),
        "margin":after_sentinel["margin"]-before_sentinel["margin"],
    }
    score=0
    if deltas["accuracy"] > 0:score+=2
    elif deltas["accuracy"] < 0:score-=2
    for name,epsilon in (
        ("cross_entropy",0.002),
        ("correct_probability",0.001),
        ("margin",0.005),
    ):
        if deltas[name] > epsilon:score+=1
        elif deltas[name] < -epsilon:score-=1
    if reward >= clear_reward and score >= 0:
        decision,reason="PROMOTE","CLEAR_REWARD_WIN_SENTINEL_SAFE"
    elif reward >= clear_reward and score < 0:
        decision,reason="REJECT","SENTINEL_VETOED_LOCAL_WIN"
    elif score > 0:
        decision,reason="PROMOTE","SENTINEL_BETTER"
    elif score < 0:
        decision,reason="REJECT","SENTINEL_WORSE"
    else:
        decision,reason="REJECT","SENTINEL_NO_DEMONSTRATED_GAIN"
    return {"decision":decision,"reason":reason,
            "sentinel_deltas":deltas,"sentinel_vote_score":score}


def _candidate_teacher_credit(raw_reward, gate, *,
                              clear_reward=CANDIDATE_CLEAR_REWARD):
    if gate["decision"]=="PROMOTE":
        if gate["reason"]=="SENTINEL_BETTER":
            return max(raw_reward,clear_reward/2)
        if gate["reason"]=="CONSOLIDATION_FULL_PROBE_GAIN":
            return max(raw_reward,clear_reward/2)
        return raw_reward
    if gate["reason"]=="CLEAR_REWARD_LOSS":
        return raw_reward
    if gate["reason"] in ("SENTINEL_WORSE","SENTINEL_VETOED_LOCAL_WIN"):
        return min(raw_reward,-clear_reward)
    if gate["reason"]=="SENTINEL_NO_DEMONSTRATED_GAIN":
        return 0.0
    if gate["reason"]=="CONSOLIDATION_FULL_PROBE_NO_GAIN":
        return 0.0
    if gate["reason"]=="CONSOLIDATION_FULL_PROBE_RETENTION_LOSS":
        return min(raw_reward,-clear_reward)
    return raw_reward


def _consolidation_confirmation(before_model, after_model, graph, lib, *,
                                device):
    before=_probe_all_grades(before_model,graph,lib,device=device)
    after=_probe_all_grades(after_model,graph,lib,device=device)
    deltas={grade:after[grade]-before[grade] for grade in REPORT_GRADE_IDS}
    mean_delta=sum(deltas.values())/len(deltas)
    worst=min(deltas,key=deltas.get)
    worst_delta=deltas[worst]
    minimum_net_gain=1/(24*len(REPORT_GRADE_IDS))
    if mean_delta < minimum_net_gain-1e-12:
        decision,reason="REJECT","CONSOLIDATION_FULL_PROBE_NO_GAIN"
    elif worst_delta <= -(2/24):
        decision,reason="REJECT","CONSOLIDATION_FULL_PROBE_RETENTION_LOSS"
    else:
        decision,reason="PROMOTE","CONSOLIDATION_FULL_PROBE_GAIN"
    return {
        "decision":decision,
        "reason":reason,
        "mean_delta":mean_delta,
        "minimum_net_gain":minimum_net_gain,
        "median_delta":statistics.median(deltas.values()),
        "improved_grades":sum(delta>0 for delta in deltas.values()),
        "regressed_grades":sum(delta<0 for delta in deltas.values()),
        "unchanged_grades":sum(delta==0 for delta in deltas.values()),
        "worst_grade":worst,
        "worst_grade_delta":worst_delta,
        "deltas":deltas,
        "before_scores":before,
        "after_scores":after,
    }


def _candidate_line(info):
    sentinel=info.get("sentinel_deltas")
    sentinel_text=""
    if sentinel is not None:
        sentinel_text=(
            f" | sentinel acc {sentinel['accuracy']*100:+.1f}pp"
            f" CE {sentinel['cross_entropy']:+.4f}"
            f" p(correct) {sentinel['correct_probability']:+.4f}"
            f" margin {sentinel['margin']:+.4f}"
        )
    consolidation=""
    if info.get("consolidation_enabled"):
        consolidation=(
            f" | soup KL {info['consensus_distill_mean']:.4f}"
            f" cov {info['consensus_coverage_mean']*100:.1f}%"
        )
        confirm=info.get("consolidation_confirmation")
        if confirm is not None:
            consolidation+=(
                f" full22 {confirm['mean_delta']*100:+.1f}pp"
                f" worst {confirm['worst_grade']} "
                f"{confirm['worst_grade_delta']*100:+.1f}pp"
            )
    return (
        f"[candidate] pass {info['pass']} {info['grade']} "
        f"attempt {info['attempt']}/{info['max_attempts']} "
        f"strategy {info['strategy']} | probe "
        f"{info['before']*100:.1f}%->{info['after']*100:.1f}% "
        f"({info['immediate_delta']*100:+.1f}pp) | "
        f"old avg {info['old_mean_delta']*100:+.1f}pp | "
        f"reward {info['reward']:+.4f}"
        f" teacher-credit {info['teacher_credit']:+.4f}"
        f"{sentinel_text}{consolidation} | "
        f"{info['decision']} {info['reason']}"
    )


def _find_school_start_checkpoint(out, state):
    named=state.get("school_start_checkpoint")
    if named:
        path=Path(out)/named
        expected=state.get("school_start_checkpoint_sha256")
        if not path.is_file() or (expected and _sha(path)!=expected):
            raise ValueError("SCHOOL_START_CHECKPOINT_MISSING_OR_CHANGED")
        return path
    candidates=[]
    for path in sorted(Path(out).glob("student-13848-*.pt")):
        try:
            _,optimizer,payload=load_checkpoint(path)
        except Exception:
            continue
        if (optimizer_receipt(optimizer)["steps"]==[13848] and
            len(payload["graph"]["tokens"])==state["vocab"] and
            digest(payload["graph"])==state["graph_sha256"]):
            candidates.append(path)
    if len(candidates)!=1:
        raise ValueError("SCHOOL_START_CHECKPOINT_AMBIGUOUS_OR_MISSING")
    return candidates[0]


def _ensure_starting_probe_baseline(out, state, lib):
    if (state.get("school_start_probe_profile")==BASELINE_PROBE_PROFILE and
        set(state.get("school_start_probe_scores",{}))==set(REPORT_GRADE_IDS)):
        return False
    path=_find_school_start_checkpoint(out,state)
    model,optimizer,payload=load_checkpoint(path)
    if optimizer_receipt(optimizer)["steps"] != [13848]:
        raise ValueError("SCHOOL_START_CHECKPOINT_STEP_DRIFT")
    scores={
        f"G{grade:02d}":_scores(
            model,lib,payload["graph"],grade,170003+grade*617,
            count=24,device="cpu")
        for grade in REPORT_GRADES
    }
    state["school_start_checkpoint"]=path.name
    state["school_start_checkpoint_sha256"]=_sha(path)
    state["school_start_probe_profile"]=BASELINE_PROBE_PROFILE
    state["school_start_probe_scores"]=scores
    state["school_start_probe_mean"]=sum(scores.values())/len(scores)
    return True


def _pass_rows(state, pass_number):
    rows={}
    for record in state["grade_ledger"]:
        if (record["spiral_pass"]==pass_number and
            record["grade"] in REPORT_GRADE_IDS):
            if record["grade"] in rows:
                raise ValueError("DUPLICATE_GRADE_IN_SPIRAL_PASS")
            rows[record["grade"]]=record
    return rows


def _find_pass_checkpoint(out, state, pass_number):
    rows=_pass_rows(state,pass_number)
    if set(rows)!=set(REPORT_GRADE_IDS):
        raise ValueError("PASS_CHECKPOINT_REQUIRES_COMPLETE_EXECUTABLE_PASS")
    explicit=rows[REPORT_GRADE_IDS[-1]].get("checkpoint")
    if explicit:
        path=Path(out)/explicit
        if not path.is_file():
            raise ValueError("PASS_CHECKPOINT_MISSING")
        _,optimizer,payload=load_checkpoint(path)
        if (optimizer_receipt(optimizer)["steps"]==
            [rows[REPORT_GRADE_IDS[-1]]["optimizer_step"]] and
            len(payload["graph"]["tokens"])==state["vocab"] and
            digest(payload["graph"])==state["graph_sha256"]):
            return path
        raise ValueError("PASS_CHECKPOINT_CHANGED")
    step=rows[REPORT_GRADE_IDS[-1]]["optimizer_step"]
    candidates=[]
    for path in sorted(Path(out).glob(f"student-{step}-*.pt")):
        try:
            _,optimizer,payload=load_checkpoint(path)
        except Exception:
            continue
        metadata=payload.get("metadata",{})
        if (optimizer_receipt(optimizer)["steps"]==[step] and
            metadata.get("last_grade")==REPORT_GRADES[-1] and
            metadata.get("spiral_pass")==pass_number and
            len(payload["graph"]["tokens"])==state["vocab"] and
            digest(payload["graph"])==state["graph_sha256"]):
            candidates.append(path)
    if len(candidates)!=1:
        raise ValueError("PASS_CHECKPOINT_AMBIGUOUS_OR_MISSING")
    return candidates[0]


def _probe_all_grades(model, graph, lib, *, device):
    return {
        f"G{grade:02d}":_scores(
            model,lib,graph,grade,170003+grade*617,count=24,device=device)
        for grade in REPORT_GRADES
    }


def _grade_champion_score(model, graph, lib, grade, *, device):
    return _scores(
        model,lib,graph,grade,1931003+grade*1237,
        count=GRADE_CHAMPION_COUNT,device=device)


def _recoverable_champion_candidates(out, state):
    out=Path(out)
    candidates={}
    def add(name, source_pass=None):
        if name and (out/name).is_file():
            candidates.setdefault(name,source_pass)
    add(state.get("checkpoint"),state.get("spiral_pass"))
    add(state.get("accepted_pass",{}).get("checkpoint"),
        state.get("accepted_pass",{}).get("pass"))
    add(state.get("champion_pass",{}).get("checkpoint"),
        state.get("champion_pass",{}).get("pass"))
    for report in state.get("pass_reports",[]):
        add(report.get("checkpoint"),report.get("pass"))
    for row in state.get("grade_ledger",[]):
        add(row.get("checkpoint"),row.get("spiral_pass"))
    return candidates


def _ensure_grade_champions(out, state, lib):
    champions=state.get("grade_champions",{})
    if (state.get("grade_champion_profile")==GRADE_CHAMPION_PROFILE and
        set(champions)==set(REPORT_GRADE_IDS) and
        all((Path(out)/item["checkpoint"]).is_file()
            for item in champions.values())):
        return False
    candidates=_recoverable_champion_candidates(out,state)
    if not candidates:
        raise ValueError("NO_RECOVERABLE_CHECKPOINTS_FOR_GRADE_CHAMPIONS")
    best={}
    for name,source_pass in candidates.items():
        path=Path(out)/name
        model,optimizer,payload=load_checkpoint(path)
        if (len(payload["graph"]["tokens"])!=state["vocab"] or
            digest(payload["graph"])!=state["graph_sha256"]):
            continue
        scores={
            f"G{grade:02d}":_grade_champion_score(
                model,payload["graph"],lib,grade,device="cpu")
            for grade in REPORT_GRADES
        }
        holistic=sum(scores.values())/len(scores)
        step=optimizer_receipt(optimizer)["steps"][0]
        checksum=_sha(path)
        for grade_id,score in scores.items():
            incumbent=best.get(grade_id)
            if (incumbent is None or score>incumbent["score"] or
                (score==incumbent["score"] and
                 holistic>incumbent["holistic_mean"])):
                best[grade_id]={
                    "score":score,
                    "checkpoint":name,
                    "checkpoint_sha256":checksum,
                    "optimizer_step":step,
                    "source_pass":source_pass,
                    "holistic_mean":holistic,
                }
    if set(best)!=set(REPORT_GRADE_IDS):
        raise ValueError("GRADE_CHAMPION_MIGRATION_INCOMPLETE")
    state["grade_champion_profile"]=GRADE_CHAMPION_PROFILE
    state["grade_champions"]=best
    return True


def _maybe_promote_grade_champion(state, grade_id, score, *,
                                  checkpoint, checkpoint_sha256,
                                  optimizer_step, source_pass,
                                  holistic_mean=None):
    incumbent=state["grade_champions"].get(grade_id)
    delta=None if incumbent is None else score-incumbent["score"]
    promoted=(incumbent is None or score>incumbent["score"])
    if promoted:
        state["grade_champions"][grade_id]={
            "score":score,
            "checkpoint":checkpoint,
            "checkpoint_sha256":checkpoint_sha256,
            "optimizer_step":optimizer_step,
            "source_pass":source_pass,
            "holistic_mean":holistic_mean,
        }
    return {
        "score":score,
        "prior_best":None if incumbent is None else incumbent["score"],
        "vs_prior_best":delta,
        "new_champion":promoted,
        "prior_checkpoint":None if incumbent is None else incumbent["checkpoint"],
    }


def _average_model_state_dicts(models, weights):
    if not models or len(models)!=len(weights) or sum(weights)<=0:
        raise ValueError("INVALID_MODEL_SOUP_INGREDIENTS")
    total=float(sum(weights))
    states=[model.state_dict() for model in models]
    keys=list(states[0])
    if any(list(state)!=keys for state in states[1:]):
        raise ValueError("MODEL_SOUP_STATE_KEYS_DIFFER")
    averaged={}
    for key in keys:
        tensors=[state[key].detach().cpu() for state in states]
        first=tensors[0]
        if any(t.shape!=first.shape or t.dtype!=first.dtype for t in tensors[1:]):
            raise ValueError("MODEL_SOUP_TENSOR_ABI_DIFFERS")
        if torch.is_floating_point(first):
            value=sum(t.float()*float(w) for t,w in zip(tensors,weights))/total
            averaged[key]=value.to(first.dtype)
        else:
            if any(not torch.equal(first,t) for t in tensors[1:]):
                raise ValueError("MODEL_SOUP_NONFLOAT_BUFFER_DIFFERS")
            averaged[key]=first.clone()
    return averaged


def _load_checkpoint_preserving_rng(path):
    rng=torch.get_rng_state()
    try:
        return load_checkpoint(path)
    finally:
        torch.set_rng_state(rng)


def _build_grade_champion_soup(out, state, lib, *, device):
    out=Path(out)
    shadow=copy.deepcopy(state)
    _ensure_reporting_state(out,shadow,lib)
    _ensure_grade_champions(out,shadow,lib)
    pass_champion=shadow["champion_pass"]
    pass_path=out/pass_champion["checkpoint"]
    if (_sha(pass_path)!=pass_champion["checkpoint_sha256"]):
        raise ValueError("PASS_CHAMPION_CHECKPOINT_CHANGED")
    pass_model,_,payload=_load_checkpoint_preserving_rng(pass_path)
    ingredient_models={}
    grade_weights={}
    for grade_id in REPORT_GRADE_IDS:
        name=shadow["grade_champions"][grade_id]["checkpoint"]
        expected_sha=shadow["grade_champions"][grade_id]["checkpoint_sha256"]
        if _sha(out/name)!=expected_sha:
            raise ValueError("GRADE_CHAMPION_CHECKPOINT_CHANGED")
        grade_weights[name]=grade_weights.get(name,0)+1
        if name not in ingredient_models:
            model,_,candidate_payload=_load_checkpoint_preserving_rng(out/name)
            if (model.config!=pass_model.config or
                digest(candidate_payload["graph"])!=digest(payload["graph"])):
                raise ValueError("GRADE_CHAMPION_SOUP_REQUIRES_IDENTICAL_MODEL_ABI")
            ingredient_models[name]=model
    names=list(ingredient_models)
    weights=[grade_weights[name] for name in names]
    ingredient_sha256={name:_sha(out/name) for name in names}
    grade_assignments={
        grade_id:{
            "checkpoint":shadow["grade_champions"][grade_id]["checkpoint"],
            "checkpoint_sha256":shadow["grade_champions"][grade_id]["checkpoint_sha256"],
            "grade_champion_score":shadow["grade_champions"][grade_id]["score"],
            "source_pass":shadow["grade_champions"][grade_id]["source_pass"],
        }
        for grade_id in REPORT_GRADE_IDS
    }
    soup=copy.deepcopy(pass_model)
    soup.load_state_dict(_average_model_state_dicts(
        [ingredient_models[name] for name in names],weights))
    if device=="mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS_NOT_AVAILABLE")
    if device not in ("cpu","mps"):
        raise ValueError("UNSUPPORTED_LEARNER_DEVICE")
    soup.to(device)
    soup.eval()
    for parameter in soup.parameters():
        parameter.requires_grad_(False)
    manifest={
        "pass_champion_pass":pass_champion["pass"],
        "pass_champion_checkpoint":pass_champion["checkpoint"],
        "pass_champion_checkpoint_sha256":pass_champion["checkpoint_sha256"],
        "ingredient_checkpoint_weights":grade_weights,
        "ingredient_checkpoint_sha256":ingredient_sha256,
        "grade_champion_assignments":grade_assignments,
        "unique_ingredient_checkpoints":len(names),
        "grade_count":len(REPORT_GRADE_IDS),
    }
    manifest["teacher_digest"]=hashlib.sha256(
        json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    return soup,payload,manifest,pass_model


def evaluate_grade_champion_soup(out=RUN, *, device="cpu"):
    """Inference-only grade-champion weight soup versus the pass champion."""
    out=Path(out)
    state=_read(out/STATE)
    lib=TeacherLibrary()
    soup,payload,manifest,pass_model=_build_grade_champion_soup(
        out,state,lib,device=device)
    pass_model.to(device)
    soup_scores=_probe_all_grades(
        soup,payload["graph"],lib,device=device)
    pass_scores=_probe_all_grades(
        pass_model,payload["graph"],lib,device=device)
    deltas={grade:soup_scores[grade]-pass_scores[grade]
            for grade in REPORT_GRADE_IDS}
    soup_mean=sum(soup_scores.values())/len(soup_scores)
    pass_mean=sum(pass_scores.values())/len(pass_scores)
    return {
        "status":"INFERENCE_ONLY_GRADE_CHAMPION_SOUP",
        "live_state_mutated":False,
        "optimizer_averaged":False,
        **manifest,
        "pass_champion_mean":pass_mean,
        "soup_mean":soup_mean,
        "mean_delta":soup_mean-pass_mean,
        "pass_champion_median":statistics.median(pass_scores.values()),
        "soup_median":statistics.median(soup_scores.values()),
        "improved_grades":sum(delta>0 for delta in deltas.values()),
        "regressed_grades":sum(delta<0 for delta in deltas.values()),
        "unchanged_grades":sum(delta==0 for delta in deltas.values()),
        "grade_deltas":deltas,
        "soup_scores":soup_scores,
        "pass_champion_scores":pass_scores,
    }


def _pass_report(pass_number, scores, baseline, previous=None, *,
                 checkpoint=None, checkpoint_sha256=None, optimizer_step=None):
    if set(scores)!=set(REPORT_GRADE_IDS) or set(baseline)!=set(REPORT_GRADE_IDS):
        raise ValueError("PASS_REPORT_REQUIRES_COMPLETE_SCORE_SET")
    if previous is not None and set(previous)!=set(REPORT_GRADE_IDS):
        raise ValueError("PASS_REPORT_PREVIOUS_SCORE_SET_INCOMPLETE")
    values=[scores[grade] for grade in REPORT_GRADE_IDS]
    start_deltas=[scores[g]-baseline[g] for g in REPORT_GRADE_IDS]
    prior_deltas=(
        [scores[g]-previous[g] for g in REPORT_GRADE_IDS]
        if previous is not None else None)
    low=min(REPORT_GRADE_IDS,key=lambda grade:scores[grade])
    high=max(REPORT_GRADE_IDS,key=lambda grade:scores[grade])
    return {
        "pass":pass_number,
        "checkpoint":checkpoint,
        "checkpoint_sha256":checkpoint_sha256,
        "optimizer_step":optimizer_step,
        "scores":dict(scores),
        "mean_probe_score":sum(values)/len(values),
        "median_probe_score":statistics.median(values),
        "mean_vs_previous":(
            sum(prior_deltas)/len(prior_deltas)
            if prior_deltas is not None else None),
        "median_vs_previous":(
            statistics.median(prior_deltas)
            if prior_deltas is not None else None),
        "mean_vs_school_start":sum(start_deltas)/len(start_deltas),
        "median_vs_school_start":statistics.median(start_deltas),
        "school_start_mean_probe_score":sum(baseline.values())/len(baseline),
        "mean_gap_to_100":1.0-sum(values)/len(values),
        "grades_at_or_above_90":sum(value>=.9 for value in values),
        "perfect_grades":sum(value==1.0 for value in values),
        "lowest_grade":low,
        "lowest_probe_score":scores[low],
        "highest_grade":high,
        "highest_probe_score":scores[high],
    }


def _pass_summary_line(report):
    prior=(
        "n/a" if report["mean_vs_previous"] is None else
        f"mean {report['mean_vs_previous']*100:+.1f}pp, "
        f"median {report['median_vs_previous']*100:+.1f}pp"
    )
    disposition=report.get("disposition","OBSERVED")
    champion=report.get("vs_champion_pass")
    champion_text=""
    if champion is not None:
        champion_text=(
            f" | vs champion P{champion['pass']} "
            f"mean {champion['mean_delta']*100:+.1f}pp, "
            f"median {champion['median_delta']*100:+.1f}pp"
        )
    return (
        f"=== PASS {report['pass']} REPORT | "
        f"mean probe {report['mean_probe_score']*100:.1f}% | "
        f"median probe {report['median_probe_score']*100:.1f}% | "
        f"vs prior pass {prior} | "
        f"vs school start mean {report['mean_vs_school_start']*100:+.1f}pp, "
        f"median {report['median_vs_school_start']*100:+.1f}pp | "
        f">=90% {report['grades_at_or_above_90']}/{len(REPORT_GRADES)} | "
        f"100% {report['perfect_grades']}/{len(REPORT_GRADES)} | "
        f"gap to 100 {report['mean_gap_to_100']*100:.1f}pp | "
        f"low {report['lowest_grade']} {report['lowest_probe_score']*100:.1f}% | "
        f"high {report['highest_grade']} {report['highest_probe_score']*100:.1f}% | "
        f"{disposition}{champion_text} ==="
    )


def _material_pass_regression(current_scores, champion_scores, threshold):
    deltas=[current_scores[g]-champion_scores[g] for g in REPORT_GRADE_IDS]
    mean_delta=sum(deltas)/len(deltas)
    median_delta=statistics.median(deltas)
    regressions=sum(delta<0 for delta in deltas)
    return {
        # Aggregate simultaneous performance is the primary safety signal.
        # Median/grade counts remain diagnostic, but do not mask asymmetric
        # losses where fewer grades fall by more than the gains elsewhere.
        "regressed":mean_delta <= -threshold,
        "mean_delta":mean_delta,
        "median_delta":median_delta,
        "regressed_grades":regressions,
        "improved_grades":sum(delta>0 for delta in deltas),
        "unchanged_grades":sum(delta==0 for delta in deltas),
    }


def _restore_last_results_to_pass(state, pass_number):
    rows=_pass_rows(state,pass_number)
    if set(rows)!=set(REPORT_GRADE_IDS):
        raise ValueError("ACCEPTED_PASS_ROWS_MISSING")
    for grade in REPORT_GRADE_IDS:
        state["last_results"][grade]=rows[grade]


def _load_accepted_student(out, state, accepted, device):
    path=Path(out)/accepted["checkpoint"]
    if not path.is_file() or _sha(path)!=accepted["checkpoint_sha256"]:
        raise ValueError("ACCEPTED_PASS_CHECKPOINT_MISSING_OR_CHANGED")
    model,optimizer,payload=load_checkpoint(path)
    if optimizer_receipt(optimizer)["steps"] != [accepted["optimizer_step"]]:
        raise ValueError("ACCEPTED_PASS_OPTIMIZER_STEP_CHANGED")
    _device(model,optimizer,device)
    state["checkpoint"]=path.name
    state["checkpoint_sha256"]=accepted["checkpoint_sha256"]
    state["model_sha256"]=state_hash(model)
    state["optimizer_step"]=accepted["optimizer_step"]
    state["completed_updates"]=max(0,accepted["optimizer_step"]-13848)
    state["vocab"]=len(payload["graph"]["tokens"])
    state["graph_sha256"]=digest(payload["graph"])
    if accepted["pass"]==0:
        state["last_results"]={
            grade:{
                "grade":grade,
                "after":accepted["scores"][grade],
                "baseline_reference":True,
            }
            for grade in REPORT_GRADE_IDS
        }
    else:
        _restore_last_results_to_pass(state,accepted["pass"])
    return model,optimizer,payload


def _reload_live_student(out, state, device):
    model,optimizer,payload=_validate(Path(out)/state["checkpoint"],state)
    _device(model,optimizer,device)
    return model,optimizer,payload


def _ensure_reporting_state(out, state, lib):
    changed=_ensure_starting_probe_baseline(out,state,lib)
    reports=state.setdefault("pass_reports",[])
    if not reports:
        complete=[]
        for pass_number in sorted({r["spiral_pass"] for r in state["grade_ledger"]}):
            if set(_pass_rows(state,pass_number))==set(REPORT_GRADE_IDS):
                complete.append(pass_number)
        if complete:
            pass_number=complete[-1]
            path=_find_pass_checkpoint(out,state,pass_number)
            model,optimizer,payload=load_checkpoint(path)
            scores=_probe_all_grades(model,payload["graph"],lib,device="cpu")
            report=_pass_report(
                pass_number,scores,state["school_start_probe_scores"],
                checkpoint=path.name,checkpoint_sha256=_sha(path),
                optimizer_step=optimizer_receipt(optimizer)["steps"][0])
            report["disposition"]="ACCEPTED_BASELINE_FOR_REPORTING"
            reports.append(report)
            state["accepted_pass"]={
                "pass":pass_number,
                "checkpoint":path.name,
                "checkpoint_sha256":_sha(path),
                "optimizer_step":report["optimizer_step"],
                "scores":dict(scores),
            }
            state["champion_pass"]=dict(state["accepted_pass"])
            changed=True
        elif "accepted_pass" not in state:
            state["accepted_pass"]={
                "pass":0,
                "checkpoint":state["school_start_checkpoint"],
                "checkpoint_sha256":state["school_start_checkpoint_sha256"],
                "optimizer_step":13848,
                "scores":dict(state["school_start_probe_scores"]),
            }
            state["champion_pass"]=dict(state["accepted_pass"])
            changed=True
    elif "accepted_pass" not in state:
        latest=reports[-1]
        state["accepted_pass"]={
            "pass":latest["pass"],
            "checkpoint":latest["checkpoint"],
            "checkpoint_sha256":latest["checkpoint_sha256"],
            "optimizer_step":latest["optimizer_step"],
            "scores":dict(latest["scores"]),
        }
        state["champion_pass"]=dict(state["accepted_pass"])
        changed=True
    elif "champion_pass" not in state:
        # Existing runs historically replaced accepted_pass even after small
        # declines. Seed the champion from the best stored pass report that
        # still has a checkpoint available, preferring higher mean score.
        candidates=[
            report for report in reports
            if report.get("checkpoint") and
            (Path(out)/report["checkpoint"]).is_file()
        ]
        best=max(candidates,key=lambda report:report["mean_probe_score"]) if candidates else None
        if best is not None:
            state["champion_pass"]={
                "pass":best["pass"],
                "checkpoint":best["checkpoint"],
                "checkpoint_sha256":best["checkpoint_sha256"],
                "optimizer_step":best["optimizer_step"],
                "scores":dict(best["scores"]),
            }
        else:
            state["champion_pass"]=dict(state["accepted_pass"])
        changed=True
    return changed


def _train(model, optimizer, reference, graph, rows, counts, policy, device,
           *, consensus_teacher=None, consensus_weight=0.0):
    lengths=[encode(row,graph) for row in rows]
    labels=torch.tensor([STATES.index(r["gold"]) for r in rows],
                        device=device,dtype=torch.long)
    inp,n=batch(lengths,device=device)
    model.train()
    optimizer.zero_grad(set_to_none=True)
    logits=model(inp,n)
    cross=F.cross_entropy(logits,labels)
    retained=counts["old"]
    first_old=counts["current"]
    old_slice=slice(first_old,first_old+retained)
    memory=torch.zeros((),device=device)
    if retained and policy["distill"]>0:
        with torch.no_grad():
            reference.eval()
            old_logits=reference(inp[old_slice],n[old_slice])
        memory=F.kl_div(
            F.log_softmax(logits[old_slice]/1.5,dim=-1),
            F.softmax(old_logits/1.5,dim=-1),
            reduction="batchmean")*(1.5**2)
    consensus=torch.zeros((),device=device)
    consensus_coverage=torch.zeros((),device=device)
    if consensus_teacher is not None and consensus_weight>0:
        with torch.no_grad():
            consensus_teacher.eval()
            teacher_logits=consensus_teacher(inp,n)
            trusted=teacher_logits.argmax(-1)==labels
        if bool(trusted.any()):
            consensus=F.kl_div(
                F.log_softmax(logits[trusted]/1.5,dim=-1),
                F.softmax(teacher_logits[trusted]/1.5,dim=-1),
                reduction="batchmean")*(1.5**2)
            consensus_coverage=trusted.float().mean()
    loss=(cross + policy["distill"]*memory +
          consensus_weight*consensus)
    if not bool(torch.isfinite(loss)):
        raise ValueError("NONFINITE_CONTINUOUS_LEARNER_LOSS")
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
    optimizer.step()
    return {
        "total":float(loss.detach().cpu()),
        "cross_entropy":float(cross.detach().cpu()),
        "parent_distill":float(memory.detach().cpu()),
        "consensus_distill":float(consensus.detach().cpu()),
        "consensus_coverage":float(consensus_coverage.detach().cpu()),
    }


def _progress_line(progress):
    repeat = progress["repeat_delta"]
    rolling = progress["rolling_repeat_delta"]
    repeat_text = "n/a" if repeat is None else f"{repeat*100:+.1f}pp"
    rolling_text = "n/a" if rolling is None else f"{rolling*100:+.1f}pp"
    patience = ""
    if progress["patience_minutes"] is not None:
        patience = (
            f" | no-gain {progress['minutes_since_measurable_progress']:.1f}"
            f"/{progress['patience_minutes']:.1f}m"
        )
    gate=""
    if progress.get("candidate_gate_enabled"):
        gate=(
            f" | gate {progress['candidate_gate_disposition']} "
            f"{progress['candidate_attempts']}/{progress['candidate_max_attempts']}"
        )
    personal=""
    if progress.get("grade_champion_score") is not None:
        delta=progress.get("vs_grade_champion")
        delta_text="baseline" if delta is None else f"{delta*100:+.1f}pp"
        marker=" NEW" if progress.get("new_grade_champion") else ""
        personal=(
            f" | best48 {progress['grade_champion_score']*100:.1f}% "
            f"vs personal-best {delta_text}{marker}"
        )
    consolidation=""
    if progress.get("consolidation_enabled"):
        consolidation=(
            f" | soup KL {progress['consensus_distill_mean']:.4f}"
            f" cov {progress['consensus_coverage_mean']*100:.1f}%"
        )
    return (
        f"[{progress['elapsed_minutes']:6.1f}m] pass {progress['pass']} "
        f"{progress['grade']} step {progress['step']} | probe "
        f"{progress['accuracy_before']*100:.1f}%->{progress['accuracy_after']*100:.1f}% "
        f"({progress['immediate_delta']*100:+.1f}pp) | vs prior {repeat_text} "
        f"| rolling{progress['progress_window']} {rolling_text} "
        f"| old avg {progress['old_mean_delta']*100:+.1f}pp "
        f"| reward {progress['reward']:+.4f} "
        f"| teacher {progress['teacher_strategies']}/{MAX_STRATEGIES} strategies/"
        f"{progress['teacher_mutations']} mutations{gate}{personal}"
        f"{consolidation}{patience}"
    )


def _stagnation_stop(*, elapsed_seconds, seconds_since_progress,
                     repeat_comparisons, progress_window, patience_minutes):
    if patience_minutes is None or repeat_comparisons < progress_window:
        return False
    patience_seconds=patience_minutes*60
    return (elapsed_seconds >= patience_seconds and
            seconds_since_progress >= patience_seconds)


def _lineage_metric_events(events, rejected_passes):
    return [event for event in events if event["pass"] not in rejected_passes]


def _metric_summary(events):
    repeats=[
        event["repeat_delta"] for event in events
        if event["repeat_delta"] is not None
    ]
    immediate=[event["immediate_delta"] for event in events]
    old=[event["old_mean_delta"] for event in events]
    return {
        "grade_visits":len(events),
        "updates":sum(event["updates"] for event in events),
        "repeat_comparisons":len(repeats),
        "repeat_improved":sum(value>0 for value in repeats),
        "repeat_unchanged":sum(value==0 for value in repeats),
        "repeat_regressed":sum(value<0 for value in repeats),
        "mean_repeat_delta":(
            sum(repeats)/len(repeats) if repeats else None),
        "mean_immediate_delta":(
            sum(immediate)/len(immediate) if immediate else None),
        "mean_old_delta":sum(old)/len(old) if old else None,
    }


def _graceful_interrupt_handler(stop_state):
    """First SIGINT requests a durable stop; second preserves emergency abort."""
    def handle(signum, frame):
        if stop_state["requested"]:
            signal.default_int_handler(signum, frame)
        stop_state["requested"]=True
        os.write(
            2,
            b"\nInterrupt requested: finishing the current grade, "
              b"checkpointing, then stopping. Press Ctrl+C again to abort immediately.\n",
        )
    return handle


def run(out=RUN, *, max_updates=1024, max_minutes=4,
        block=32, device="cpu", strict_full50=False,
        max_run_gib=32, max_grade_visits=None,
        patience_minutes=None, progress_window=8,
        min_repeat_improvement=0.01, progress_format="json",
        stop_requested=None, rollback_regressed_pass=False,
        pass_regression_threshold=0.01, prune_checkpoints=False,
        keep_recent_checkpoints=8, keep_pass_checkpoints=4,
        candidate_grade_gate=False,
        candidate_max_attempts=CANDIDATE_MAX_ATTEMPTS,
        candidate_clear_reward=CANDIDATE_CLEAR_REWARD,
        candidate_sentinel_per_grade=CANDIDATE_SENTINEL_PER_GRADE,
        consolidate_grade_champions=False,
        consolidation_weight=CONSOLIDATION_WEIGHT):
    if (max_updates < 1 or max_minutes <= 0 or block < 1 or block > 256
        or not 1<=max_run_gib<=500
        or (max_grade_visits is not None and max_grade_visits < 1)
        or (patience_minutes is not None and patience_minutes <= 0)
        or progress_window < 1 or min_repeat_improvement < 0
        or not 0<=pass_regression_threshold<=1
        or keep_recent_checkpoints < 0 or keep_pass_checkpoints < 0
        or candidate_max_attempts < 1
        or candidate_clear_reward < 0
        or candidate_sentinel_per_grade < 1
        or consolidation_weight < 0
        or (consolidate_grade_champions and not candidate_grade_gate)
        or progress_format not in ("json","human")):
        raise ValueError("INVALID_BOUNDED_TRAINING_REQUEST")
    out=Path(out)
    if strict_full50 and any(not g.ready for g in GRADES):
        raise ValueError("FULL_50_NOT_COMPILED: GRAMMAR_AND_LEXICON_NEED_VALIDATED_GENERATORS")
    if not (out/STATE).exists():
        initialize(out)
    state=_read(out/STATE)
    if state["version"] != VERSION:
        raise ValueError("CANNOT_SILENTLY_RESUME_DIFFERENT_SCHOOL_ENGINE")
    migrated_accounting=False
    legacy_completed=state["completed_updates"]
    if "attempted_updates" not in state:
        state["attempted_updates"]=legacy_completed
        migrated_accounting=True
    live_updates=max(0,state["optimizer_step"]-13848)
    if state["completed_updates"] != live_updates:
        state["completed_updates"]=live_updates
        migrated_accounting=True
    if "candidate_ledger" not in state:
        state["candidate_ledger"]=[]
        migrated_accounting=True
    model,optimizer,payload=_validate(out/state["checkpoint"],state)
    gpu=_device(model,optimizer,device)
    lib=TeacherLibrary()
    reporting_changed=_ensure_reporting_state(out,state,lib)
    grade_champions_changed=_ensure_grade_champions(out,state,lib)
    if reporting_changed or grade_champions_changed or migrated_accounting:
        _atomic_json(out/STATE,state)
    consensus_teacher=None
    consensus_manifest=None
    if consolidate_grade_champions:
        consensus_teacher,consensus_payload,consensus_manifest,_ = (
            _build_grade_champion_soup(out,state,lib,device=device))
        if digest(consensus_payload["graph"])!=state["graph_sha256"]:
            raise ValueError("CONSOLIDATION_TEACHER_GRAPH_CHANGED")
        state.setdefault("consolidation_sessions",[]).append({
            "teacher_digest":consensus_manifest["teacher_digest"],
            "weight":consolidation_weight,
            "parent_checkpoint":state["checkpoint"],
            "parent_checkpoint_sha256":state["checkpoint_sha256"],
            "parent_optimizer_step":state["optimizer_step"],
            "pass_champion_pass":consensus_manifest["pass_champion_pass"],
            "ingredient_checkpoint_weights":
                consensus_manifest["ingredient_checkpoint_weights"],
        })
        _atomic_json(out/STATE,state)
    if prune_checkpoints:
        _prune_checkpoints(
            out,state,keep_recent=keep_recent_checkpoints,
            keep_pass=keep_pass_checkpoints)
        _atomic_json(out/STATE,state)
    start=time.monotonic()
    consumed=0
    visits_this_call=0
    candidate_rejections_this_call=0
    candidate_promotions_this_call=0
    candidate_no_updates_this_call=0
    metric_events=[]
    rejected_passes=set()
    measurable_progress_events=[]
    last_measurable_progress=start
    paused_for_storage=False
    stopped_for_stagnation=False
    paused_for_visit_limit=False
    stopped_for_interrupt=False
    while (consumed < max_updates and time.monotonic()-start < max_minutes*60
           and (max_grade_visits is None or visits_this_call < max_grade_visits)):
        if stop_requested is not None and stop_requested():
            stopped_for_interrupt=True
            break
        checkpoints = list(out.glob("student-*.pt"))
        storage_bytes = sum(p.stat().st_size for p in checkpoints)
        # Compute bound before beginning the next grade: a new checkpoint
        # may require roughly current-model payload bytes, and a little
        # headroom for atomic writes, file indexes and the run journal.
        recent_bytes=(out/state["checkpoint"]).stat().st_size
        if storage_bytes+recent_bytes*2 >= max_run_gib*1024**3:
            paused_for_storage=True
            break
        grade=state["next_grade"]
        if grade > 50:
            grade=1
            state["next_grade"]=1
            state["spiral_pass"]+=1
        if not lib.ready(grade):
            # An unimplemented skill is NEVER taught using synthetic/fake
            # oracle labels, and it never forces a learner reset or rollback.
            state["next_grade"]+=1
            if state["next_grade"]>50:
                state["next_grade"]=1
                state["spiral_pass"]+=1
            continue
        if shutil.disk_usage(out).free < 512*1024*1024:
            raise OSError("SCHOOL_STORAGE_RESERVE_512MiB_REACHED")
        grade_id=f"G{grade:02d}"
        prior_visit=state["last_results"].get(grade_id)
        probe_seed=170003+grade*617
        before=_scores(model,lib,payload["graph"],grade,probe_seed,device=device)
        guards=[g for g in (1,10,13,16,17,19) if g<grade and lib.ready(g)]
        before_old={str(g):_scores(model,lib,payload["graph"],g,170003+g*617,
                                  count=12,device=device) for g in guards}
        base_seed=(state["spiral_pass"]*1000003 + grade*9973 +
                   state["completed_grades"]*3)
        max_attempts=(candidate_max_attempts if candidate_grade_gate else 1)
        promoted=False
        last_attempt=None
        accepted_steps=0
        budget_exhausted=False
        attempted_strategy_keys=set()
        for attempt in range(1,max_attempts+1):
            steps=min(block,max_updates-consumed)
            if steps < 1:
                budget_exhausted=True
                break
            rng=random.Random(
                base_seed + attempt*104729 + state["teacher"]["events"]*17)
            key,policy=pick(
                state["teacher"],grade,rng,exclude=attempted_strategy_keys)
            attempted_strategy_keys.add(key)
            anchor=copy.deepcopy(model).eval()
            for p in anchor.parameters():p.requires_grad_(False)
            for group in optimizer.param_groups:group["lr"]=policy["lr"]
            tallies={"current":0,"old":0,"preview":0}
            train_metrics=[]
            for local_step in range(steps):
                rows,counts=compose_batch(lib,grade,policy,payload["graph"],rng)
                if counts["current"] <= 0 or len(rows)!=32:
                    raise ValueError("NO_COGNITIVE_GROWTH_SAMPLES")
                metrics=_train(
                    model,optimizer,anchor,payload["graph"],rows,counts,policy,gpu,
                    consensus_teacher=consensus_teacher,
                    consensus_weight=(
                        consolidation_weight if consolidate_grade_champions else 0.0))
                train_metrics.append(metrics)
                for name,value in counts.items():tallies[name]+=value
            candidate_step=optimizer_receipt(optimizer)["steps"][0]
            if candidate_step != state["optimizer_step"]+steps:
                raise ValueError("CANDIDATE_ADAMW_CONTINUITY_BROKEN")
            after=_scores(
                model,lib,payload["graph"],grade,probe_seed,device=device)
            after_old={
                str(g):_scores(
                    model,lib,payload["graph"],g,170003+g*617,
                    count=12,device=device)
                for g in guards
            }
            old_delta=sum(after_old[k]-before_old[k] for k in before_old)
            old_mean_delta=old_delta/max(1,len(before_old))
            immediate_delta=after-before
            reward=2*immediate_delta+.6*old_mean_delta
            gate=(
                _candidate_gate_decision(
                    reward,clear_reward=candidate_clear_reward)
                if candidate_grade_gate
                else {"decision":"PROMOTE","reason":"GRADE_GATE_DISABLED"}
            )
            before_sentinel=after_sentinel=None
            if gate["decision"]=="MEASURE":
                before_sentinel=_sentinel_metrics(
                    anchor,lib,payload["graph"],device=device,
                    count_per_grade=candidate_sentinel_per_grade)
                after_sentinel=_sentinel_metrics(
                    model,lib,payload["graph"],device=device,
                    count_per_grade=candidate_sentinel_per_grade)
                gate=_candidate_gate_decision(
                    reward,before_sentinel,after_sentinel,
                    clear_reward=candidate_clear_reward)
            consolidation_confirmation=None
            if consolidate_grade_champions and gate["decision"]=="PROMOTE":
                consolidation_confirmation=_consolidation_confirmation(
                    anchor,model,payload["graph"],lib,device=device)
                gate={
                    **gate,
                    "decision":consolidation_confirmation["decision"],
                    "reason":consolidation_confirmation["reason"],
                    "consolidation_confirmation":consolidation_confirmation,
                }
            teacher_credit=_candidate_teacher_credit(
                reward,gate,clear_reward=candidate_clear_reward)
            observe(state["teacher"],grade,key,teacher_credit)
            consumed+=steps
            state["attempted_updates"]+=steps
            attempt_record={
                "spiral_pass":state["spiral_pass"],
                "grade":grade_id,
                "attempt":attempt,
                "max_attempts":max_attempts,
                "parent_checkpoint":state["checkpoint"],
                "parent_optimizer_step":state["optimizer_step"],
                "candidate_optimizer_step":candidate_step,
                "strategy_id":key,
                "strategy":policy,
                "before":before,
                "after":after,
                "old_before":before_old,
                "old_after":after_old,
                "old_mean_delta":round(old_mean_delta,6),
                "reward":round(reward,6),
                "teacher_credit":round(teacher_credit,6),
                "updates":steps,
                "loss_first":train_metrics[0]["total"],
                "loss_last":train_metrics[-1]["total"],
                "cross_entropy_first":train_metrics[0]["cross_entropy"],
                "cross_entropy_last":train_metrics[-1]["cross_entropy"],
                "parent_distill_mean":(
                    sum(item["parent_distill"] for item in train_metrics)/
                    len(train_metrics)),
                "consensus_distill_mean":(
                    sum(item["consensus_distill"] for item in train_metrics)/
                    len(train_metrics)),
                "consensus_coverage_mean":(
                    sum(item["consensus_coverage"] for item in train_metrics)/
                    len(train_metrics)),
                "consolidation_teacher_digest":(
                    None if consensus_manifest is None
                    else consensus_manifest["teacher_digest"]),
                "consolidation_weight":(
                    consolidation_weight if consolidate_grade_champions else 0.0),
                "consolidation_confirmation":consolidation_confirmation,
                "row_exposures":tallies,
                "decision":gate["decision"],
                "reason":gate["reason"],
                "sentinel_before":before_sentinel,
                "sentinel_after":after_sentinel,
                "sentinel_deltas":gate.get("sentinel_deltas"),
                "sentinel_vote_score":gate.get("sentinel_vote_score"),
                "teacher_mutations":state["teacher"]["mutations"],
            }
            state["candidate_ledger"].append(attempt_record)
            last_attempt=attempt_record
            if candidate_grade_gate:
                line_info={
                    "pass":state["spiral_pass"],"grade":grade_id,
                    "attempt":attempt,"max_attempts":max_attempts,
                    "strategy":key,"before":before,"after":after,
                    "immediate_delta":immediate_delta,
                    "old_mean_delta":old_mean_delta,"reward":reward,
                    "teacher_credit":teacher_credit,
                    "decision":gate["decision"],"reason":gate["reason"],
                    "sentinel_deltas":gate.get("sentinel_deltas"),
                    "consolidation_enabled":consolidate_grade_champions,
                    "consensus_distill_mean":
                        attempt_record["consensus_distill_mean"],
                    "consensus_coverage_mean":
                        attempt_record["consensus_coverage_mean"],
                    "consolidation_confirmation":
                        attempt_record["consolidation_confirmation"],
                }
                if progress_format=="human":
                    print(_candidate_line(line_info),flush=True)
                else:
                    print(json.dumps({"candidate_attempt":line_info},
                                     sort_keys=True),flush=True)
            if gate["decision"]=="PROMOTE":
                promoted=True
                accepted_steps=steps
                candidate_promotions_this_call+=1
                break
            candidate_rejections_this_call+=1
            _atomic_json(out/STATE,state)
            model,optimizer,payload=_reload_live_student(out,state,device)
            gpu=torch.device(device)
            if stop_requested is not None and stop_requested():
                break

        if budget_exhausted and last_attempt is None:
            break
        if promoted:
            key=last_attempt["strategy_id"]
            policy=last_attempt["strategy"]
            after=last_attempt["after"]
            after_old=last_attempt["old_after"]
            old_mean_delta=last_attempt["old_mean_delta"]
            old_delta=sum(after_old[k]-before_old[k] for k in before_old)
            immediate_delta=after-before
            reward=last_attempt["reward"]
            losses=[last_attempt["loss_first"],last_attempt["loss_last"]]
            tallies=last_attempt["row_exposures"]
            state["completed_updates"]+=accepted_steps
            state["optimizer_step"]+=accepted_steps
            if optimizer_receipt(optimizer)["steps"]!=[state["optimizer_step"]]:
                raise ValueError("ADAMW_CONTINUITY_BROKEN")
            student_update_applied=True
            gate_disposition=last_attempt["reason"]
        else:
            # All candidate lessons failed to demonstrate enough value.
            # Preserve teacher evidence, but advance the curriculum with the
            # production student and AdamW state unchanged.
            model,optimizer,payload=_reload_live_student(out,state,device)
            gpu=torch.device(device)
            key=None
            policy=None
            after=before
            after_old=dict(before_old)
            old_delta=0.0
            old_mean_delta=0.0
            immediate_delta=0.0
            reward=0.0
            accepted_steps=0
            tallies={"current":0,"old":0,"preview":0}
            losses=[None,None]
            student_update_applied=False
            gate_disposition="NO_CANDIDATE_PROMOTED"
            candidate_no_updates_this_call+=1
        repeat_delta=(None if prior_visit is None
                      else after-prior_visit["after"])
        metric_events.append({
            "pass":state["spiral_pass"],
            "grade":grade_id,
            "updates":accepted_steps,
            "repeat_delta":repeat_delta,
            "immediate_delta":immediate_delta,
            "old_mean_delta":old_mean_delta,
        })
        lineage_events=_lineage_metric_events(metric_events,rejected_passes)
        repeat_deltas=[
            event["repeat_delta"] for event in lineage_events
            if event["repeat_delta"] is not None
        ]
        recent_repeat=repeat_deltas[-progress_window:]
        rolling_repeat_delta=(sum(recent_repeat)/len(recent_repeat)
                              if recent_repeat else None)
        now=time.monotonic()
        if (len(recent_repeat) >= progress_window and
            rolling_repeat_delta >= min_repeat_improvement):
            last_measurable_progress=now
            measurable_progress_events.append({
                "pass":state["spiral_pass"],
                "at":now,
            })
        visits_this_call+=1
        state["completed_grades"]+=1
        record={"spiral_pass":state["spiral_pass"],"grade":grade_id,
                "strategy_id":key,"strategy":policy,
                "before":before,"after":after,"old_before":before_old,
                "old_after":after_old,"reward":round(reward,6),
                "repeat_delta":None if repeat_delta is None else round(repeat_delta,6),
                "old_mean_delta":round(old_mean_delta,6),
                "updates":accepted_steps,
                "loss_first":losses[0],"loss_last":losses[-1],
                "consensus_distill_mean":(
                    None if last_attempt is None
                    else last_attempt.get("consensus_distill_mean")),
                "consensus_coverage_mean":(
                    None if last_attempt is None
                    else last_attempt.get("consensus_coverage_mean")),
                "consolidation_teacher_digest":(
                    None if last_attempt is None
                    else last_attempt.get("consolidation_teacher_digest")),
                "consolidation_confirmation":(
                    None if last_attempt is None
                    else last_attempt.get("consolidation_confirmation")),
                "teacher_mutations":state["teacher"]["mutations"],
                "row_exposures":tallies,
                "optimizer_step":state["optimizer_step"],
                "student_update_applied":student_update_applied,
                "candidate_attempts":(
                    last_attempt["attempt"] if last_attempt is not None else 0),
                "candidate_gate_disposition":gate_disposition}
        state["grade_ledger"].append(record)
        state["last_results"][f"G{grade:02d}"]=record
        state["next_grade"]=grade+1
        state["model_sha256"]=state_hash(model)
        grade_champion_result=None
        if student_update_applied:
            name,checksum=_checkpoint(out,model,optimizer,payload["graph"],{
                "epoch":VERSION,"step":state["optimizer_step"],
                "last_grade":grade,"spiral_pass":state["spiral_pass"],
                "learning_strategy":policy,
                "candidate_attempts":record["candidate_attempts"],
                "candidate_gate_disposition":gate_disposition,
                "parent_checkpoint_sha256":state["checkpoint_sha256"],
                "one_continuing_student":True})
            state["checkpoint"],state["checkpoint_sha256"]=name,checksum
            champion_score=_grade_champion_score(
                model,payload["graph"],lib,grade,device=device)
            grade_champion_result=_maybe_promote_grade_champion(
                state,grade_id,champion_score,
                checkpoint=name,checkpoint_sha256=checksum,
                optimizer_step=state["optimizer_step"],
                source_pass=state["spiral_pass"],
                holistic_mean=(
                    last_attempt.get("sentinel_after",{}).get("accuracy")
                    if last_attempt is not None and
                    last_attempt.get("sentinel_after") is not None
                    else None))
        state["last_run_wall_seconds"]=round(time.monotonic()-start,3)
        record["checkpoint"]=state["checkpoint"]
        record["checkpoint_sha256"]=state["checkpoint_sha256"]
        record["grade_champion_score"]=(
            None if grade_champion_result is None
            else grade_champion_result["score"])
        record["vs_grade_champion"]=(
            None if grade_champion_result is None
            else grade_champion_result["vs_prior_best"])
        record["new_grade_champion"]=(
            False if grade_champion_result is None
            else grade_champion_result["new_champion"])
        _atomic_json(out/STATE,state)
        pass_report=None
        if grade==REPORT_GRADES[-1]:
            previous=state["accepted_pass"]["scores"]
            scores=_probe_all_grades(
                model,payload["graph"],lib,device=device)
            pass_report=_pass_report(
                state["spiral_pass"],scores,state["school_start_probe_scores"],
                previous,
                checkpoint=state["checkpoint"],
                checkpoint_sha256=state["checkpoint_sha256"],
                optimizer_step=state["optimizer_step"])
            champion=state["champion_pass"]
            regression=_material_pass_regression(
                scores,champion["scores"],pass_regression_threshold)
            pass_report["vs_champion_pass"]={
                "pass":champion["pass"],
                **regression,
            }
            rejected=rollback_regressed_pass and regression["regressed"]
            if rejected:
                rejected_passes.add(state["spiral_pass"])
                rejected_checkpoint=state["checkpoint"]
                rejected_sha=state["checkpoint_sha256"]
                rejected_step=state["optimizer_step"]
                pass_report["disposition"]=(
                    f"ROLLED_BACK_TO_CHAMPION_PASS_{champion['pass']}")
                state["pass_reports"].append(pass_report)
                state.setdefault("pass_rollbacks",[]).append({
                    "rejected_pass":state["spiral_pass"],
                    "rejected_checkpoint":rejected_checkpoint,
                    "rejected_checkpoint_sha256":rejected_sha,
                    "rejected_optimizer_step":rejected_step,
                    "champion_pass":champion["pass"],
                    "restored_checkpoint":champion["checkpoint"],
                    "restored_checkpoint_sha256":champion["checkpoint_sha256"],
                    "restored_optimizer_step":champion["optimizer_step"],
                    "threshold":pass_regression_threshold,
                    "mean_delta":regression["mean_delta"],
                    "median_delta":regression["median_delta"],
                    "regressed_grades":regression["regressed_grades"],
                    "teacher_events_preserved":state["teacher"]["events"],
                    "teacher_mutations_preserved":state["teacher"]["mutations"],
                })
                model,optimizer,payload=_load_accepted_student(
                    out,state,champion,device)
                state["accepted_pass"]=dict(champion)
                gpu=torch.device(device)
                measurable_progress_events=[
                    event for event in measurable_progress_events
                    if event["pass"] not in rejected_passes
                ]
                last_measurable_progress=(
                    measurable_progress_events[-1]["at"]
                    if measurable_progress_events else start)
            else:
                current={
                    "pass":state["spiral_pass"],
                    "checkpoint":state["checkpoint"],
                    "checkpoint_sha256":state["checkpoint_sha256"],
                    "optimizer_step":state["optimizer_step"],
                    "scores":dict(scores),
                }
                state["accepted_pass"]=current
                current_mean=sum(scores.values())/len(scores)
                champion_mean=(
                    sum(champion["scores"].values())/len(champion["scores"]))
                if current_mean > champion_mean:
                    state["champion_pass"]=dict(current)
                    pass_report["disposition"]="ACCEPTED_NEW_CHAMPION"
                else:
                    pass_report["disposition"]="ACCEPTED_CHAMPION_UNCHANGED"
                state["pass_reports"].append(pass_report)
            _atomic_json(out/STATE,state)
        if prune_checkpoints:
            _prune_checkpoints(
                out,state,keep_recent=keep_recent_checkpoints,
                keep_pass=keep_pass_checkpoints)
            _atomic_json(out/STATE,state)
        lineage_events=_lineage_metric_events(metric_events,rejected_passes)
        repeat_deltas=[
            event["repeat_delta"] for event in lineage_events
            if event["repeat_delta"] is not None
        ]
        recent_repeat=repeat_deltas[-progress_window:]
        rolling_repeat_delta=(sum(recent_repeat)/len(recent_repeat)
                              if recent_repeat else None)
        elapsed=time.monotonic()-start
        since_progress=elapsed-(last_measurable_progress-start)
        progress={"pass":state["spiral_pass"],"grade":grade_id,
                  "step":record["optimizer_step"],"updates":accepted_steps,
                  "strategy":key,
                  "teacher_strategies":len(state["teacher"]["strategies"]),
                  "teacher_mutations":state["teacher"]["mutations"],
                  "accuracy_before":before,"accuracy_after":after,
                  "immediate_delta":immediate_delta,
                  "repeat_delta":repeat_delta,
                  "rolling_repeat_delta":rolling_repeat_delta,
                  "progress_window":progress_window,
                  "reward":round(reward,4),
                  "old_mean_delta":old_mean_delta,
                  "old_delta_sum":old_delta,
                  "elapsed_minutes":elapsed/60,
                  "minutes_since_measurable_progress":since_progress/60,
                  "patience_minutes":patience_minutes,
                  "min_repeat_improvement":min_repeat_improvement,
                  "candidate_gate_enabled":candidate_grade_gate,
                  "candidate_gate_disposition":gate_disposition,
                  "candidate_attempts":record["candidate_attempts"],
                  "candidate_max_attempts":max_attempts,
                  "grade_champion_score":record["grade_champion_score"],
                  "vs_grade_champion":record["vs_grade_champion"],
                  "new_grade_champion":record["new_grade_champion"],
                  "consolidation_enabled":consolidate_grade_champions,
                  "consensus_distill_mean":(
                      record["consensus_distill_mean"] or 0.0),
                  "consensus_coverage_mean":(
                      record["consensus_coverage_mean"] or 0.0)}
        if progress_format=="human":
            print(_progress_line(progress),flush=True)
        else:
            print(json.dumps(progress,sort_keys=True),flush=True)
        if pass_report is not None:
            if progress_format=="human":
                print(_pass_summary_line(pass_report),flush=True)
            else:
                print(json.dumps({"pass_report":pass_report},sort_keys=True),
                      flush=True)
        if stop_requested is not None and stop_requested():
            stopped_for_interrupt=True
            break
        if _stagnation_stop(
                elapsed_seconds=elapsed,
                seconds_since_progress=since_progress,
                repeat_comparisons=len(repeat_deltas),
                progress_window=progress_window,
                patience_minutes=patience_minutes):
            stopped_for_stagnation=True
            break
    if (max_grade_visits is not None and
        visits_this_call >= max_grade_visits and
        not stopped_for_stagnation and not paused_for_storage):
        paused_for_visit_limit=True
    status=("PAUSED_FOR_STORAGE_QUOTA" if paused_for_storage else
            "STOPPED_BY_GRACEFUL_INTERRUPT" if stopped_for_interrupt else
            "STOPPED_NO_MEASURABLE_REPEAT_IMPROVEMENT" if stopped_for_stagnation else
            "PAUSED_AT_REQUESTED_GRADE_VISIT_LIMIT" if paused_for_visit_limit else
            "PAUSED_AT_DURABLE_GRADE_BOUNDARY")
    lineage_events=_lineage_metric_events(metric_events,rejected_passes)
    rejected_events=[
        event for event in metric_events if event["pass"] in rejected_passes
    ]
    lineage_summary=_metric_summary(lineage_events)
    attempted_summary=_metric_summary(metric_events)
    rejected_summary=_metric_summary(rejected_events)
    repeat_deltas=[
        event["repeat_delta"] for event in lineage_events
        if event["repeat_delta"] is not None
    ]
    recent_repeat=repeat_deltas[-progress_window:]
    retention=state.get("checkpoint_retention",{})
    return {"status":status,
            "checkpoint_quota_gib":max_run_gib,
            "completed_this_call":lineage_summary["updates"],
            "training_updates_attempted_this_call":consumed,
            "grade_visits_this_call":visits_this_call,
            "accepted_grade_visits_this_call":lineage_summary["grade_visits"],
            "accepted_updates_this_call":lineage_summary["updates"],
            "repeat_comparisons_this_call":lineage_summary["repeat_comparisons"],
            "mean_repeat_delta_this_call":lineage_summary["mean_repeat_delta"],
            "repeat_improved_this_call":lineage_summary["repeat_improved"],
            "repeat_unchanged_this_call":lineage_summary["repeat_unchanged"],
            "repeat_regressed_this_call":lineage_summary["repeat_regressed"],
            "mean_immediate_delta_this_call":lineage_summary["mean_immediate_delta"],
            "mean_old_delta_this_call":lineage_summary["mean_old_delta"],
            "attempted_run_metrics":attempted_summary,
            "rejected_run_metrics":rejected_summary,
            "rejected_passes_this_call":sorted(rejected_passes),
            "candidate_grade_gate":candidate_grade_gate,
            "candidate_promotions_this_call":candidate_promotions_this_call,
            "candidate_rejections_this_call":candidate_rejections_this_call,
            "candidate_no_update_grades_this_call":candidate_no_updates_this_call,
            "consolidation_enabled":consolidate_grade_champions,
            "consolidation_weight":(
                consolidation_weight if consolidate_grade_champions else 0.0),
            "consolidation_teacher_digest":(
                None if consensus_manifest is None
                else consensus_manifest["teacher_digest"]),
            "rolling_repeat_delta":(sum(recent_repeat)/len(recent_repeat)
                                    if recent_repeat else None),
            "progress_window":progress_window,
            "min_repeat_improvement":min_repeat_improvement,
            "patience_minutes":patience_minutes,
            "total_school_updates":state["completed_updates"],
            "total_training_updates_attempted":state["attempted_updates"],
            "live_optimizer_step":state["optimizer_step"],
            "completed_grades":state["completed_grades"],
            "spiral_pass":state["spiral_pass"],
            "next_grade":state["next_grade"],
            "teacher_strategies":len(state["teacher"]["strategies"]),
            "teacher_strategy_capacity":MAX_STRATEGIES,
            "observed_teacher_mutations":state["teacher"]["mutations"],
            "compiled_grades":sum(g.ready for g in GRADES),
            "blocked_grades":state["blocked_grade_ids"],
            "accepted_pass":state.get("accepted_pass",{}).get("pass"),
            "champion_pass":state.get("champion_pass",{}).get("pass"),
            "pass_rollbacks":len(state.get("pass_rollbacks",[])),
            "checkpoint_files_retained":retention.get("retained_count"),
            "checkpoint_storage_gib":(
                retention.get("retained_bytes")/1024**3
                if retention.get("retained_bytes") is not None else None),
            "checkpoints_pruned_total":retention.get("total_pruned_count",0),
            "checkpoint_gib_pruned_total":(
                retention.get("total_pruned_bytes",0)/1024**3),
            "latest_checkpoint":str(out/state["checkpoint"])}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-dir",type=Path,default=RUN)
    parser.add_argument("--max-updates",type=int,default=1024)
    parser.add_argument("--minutes",type=float,default=4)
    parser.add_argument("--block",type=int,default=32)
    parser.add_argument("--max-run-gib",type=float,default=32,
                        help="Pause safely before generated checkpoint history exceeds this many GiB.")
    parser.add_argument("--grade-visits",type=int,default=None,
                        help="Pause at a durable boundary after this many completed grade visits.")
    parser.add_argument("--patience-minutes",type=float,default=None,
                        help="Stop if repeated-grade trend shows no measurable improvement for this long.")
    parser.add_argument("--progress-window",type=int,default=8,
                        help="Repeated-grade comparisons used for the rolling improvement trend.")
    parser.add_argument("--min-repeat-improvement",type=float,default=0.01,
                        help="Rolling repeated-grade accuracy gain that resets the patience clock (0.01 = 1 pp).")
    parser.add_argument("--progress-format",choices=("human","json"),default="json",
                        help="Per-grade live progress output.")
    parser.add_argument("--graceful-interrupt",action="store_true",
                        help="First Ctrl+C finishes the current grade and checkpoints before stopping; second Ctrl+C aborts immediately.")
    parser.add_argument("--rollback-regressed-pass",action="store_true",
                        help="At a completed executable pass, restore the last accepted pass if broad probe performance regresses materially.")
    parser.add_argument("--pass-regression-threshold",type=float,default=0.01,
                        help="Mean 22-grade probe regression versus the retained champion required before rollback can trigger (0.01 = 1 pp).")
    parser.add_argument("--prune-checkpoints",action="store_true",
                        help="Prune redundant historical checkpoint binaries while preserving durable recovery anchors.")
    parser.add_argument("--keep-recent-checkpoints",type=int,default=8,
                        help="With pruning enabled, retain this many most recent grade checkpoints.")
    parser.add_argument("--keep-pass-checkpoints",type=int,default=4,
                        help="With pruning enabled, retain this many recent G22 pass-end checkpoints.")
    parser.add_argument("--candidate-grade-gate",action="store_true",
                        help="Train grade lessons as candidates and promote only evidence-backed student updates.")
    parser.add_argument("--candidate-max-attempts",type=int,
                        default=CANDIDATE_MAX_ATTEMPTS,
                        help="Maximum teaching strategies tried from the same live student for one grade.")
    parser.add_argument("--candidate-clear-reward",type=float,
                        default=CANDIDATE_CLEAR_REWARD,
                        help="Teacher reward magnitude treated as clear local evidence; wins still face the cross-grade sentinel.")
    parser.add_argument("--candidate-sentinel-per-grade",type=int,
                        default=CANDIDATE_SENTINEL_PER_GRADE,
                        help="Examples per compiled grade in the continuous promotion sentinel.")
    parser.add_argument("--consolidate-grade-champions",action="store_true",
                        help="Use the frozen grade-champion soup as an additional trusted-row distillation teacher; requires candidate gating.")
    parser.add_argument("--consolidation-weight",type=float,
                        default=CONSOLIDATION_WEIGHT,
                        help="KL weight for trusted grade-champion soup guidance during candidate training.")
    parser.add_argument("--device",choices=("cpu","mps"),default="cpu")
    parser.add_argument("--grow",action="store_true",
                        help="Function-preserving capacity migration, keeping trained state.")
    parser.add_argument("--require-full50",action="store_true")
    parser.add_argument("--status",action="store_true")
    parser.add_argument("--evaluate-grade-champion-soup",action="store_true",
                        help="Read-only inference evaluation of a grade-champion weight soup versus the holistic pass champion.")
    arguments=parser.parse_args()
    if arguments.evaluate_grade_champion_soup:
        print(json.dumps(
            evaluate_grade_champion_soup(arguments.run_dir,device=arguments.device),
            indent=2,sort_keys=True))
    elif arguments.grow:
        print(json.dumps(grow_active_school(arguments.run_dir),indent=2,sort_keys=True))
    elif arguments.status:
        result=_read(arguments.run_dir/STATE)
        print(json.dumps({k:v for k,v in result.items()
                          if k not in ("teacher","grade_ledger",
                                       "candidate_ledger","last_results")},
                         indent=2,sort_keys=True))
    else:
        stop_state={"requested":False}
        previous_handler=None
        if arguments.graceful_interrupt:
            previous_handler=signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT,_graceful_interrupt_handler(stop_state))
        try:
            result=run(arguments.run_dir,max_updates=arguments.max_updates,
                       max_minutes=arguments.minutes,block=arguments.block,
                       device=arguments.device,strict_full50=arguments.require_full50,
                       max_run_gib=arguments.max_run_gib,
                       max_grade_visits=arguments.grade_visits,
                       patience_minutes=arguments.patience_minutes,
                       progress_window=arguments.progress_window,
                       min_repeat_improvement=arguments.min_repeat_improvement,
                       progress_format=arguments.progress_format,
                       rollback_regressed_pass=arguments.rollback_regressed_pass,
                       pass_regression_threshold=arguments.pass_regression_threshold,
                       prune_checkpoints=arguments.prune_checkpoints,
                       keep_recent_checkpoints=arguments.keep_recent_checkpoints,
                       keep_pass_checkpoints=arguments.keep_pass_checkpoints,
                       candidate_grade_gate=arguments.candidate_grade_gate,
                       candidate_max_attempts=arguments.candidate_max_attempts,
                       candidate_clear_reward=arguments.candidate_clear_reward,
                       candidate_sentinel_per_grade=arguments.candidate_sentinel_per_grade,
                       consolidate_grade_champions=arguments.consolidate_grade_champions,
                       consolidation_weight=arguments.consolidation_weight,
                       stop_requested=(lambda: stop_state["requested"])
                                      if arguments.graceful_interrupt else None)
        finally:
            if previous_handler is not None:
                signal.signal(signal.SIGINT,previous_handler)
        print(json.dumps(result,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
