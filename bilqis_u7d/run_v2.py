"""Immutable U7D freeze/qualify/replay; gradients permitted only after explicit DEV win."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import math
import random
import sys
import time

from bilqis_logic.kernel import canonical,digest
from bilqis_development.vendor.kev_teacher import KevTeacher
from .laboratory_v2 import (VERSION,build,validate_episodes,MAX_STEPS,DOSSIERS,
                         initial,start,legal,apply,prose,run_control,transition_digest as step_hash)

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/"docs/evidence/u7d/run-03"
CHILD=ROOT/"bilqis_u7d"
DEVELOPMENT_SEED=88711
SEALED_SEED=21749
# Predeclared before model calls. At most 240 model choices, and no student updates
# unless these conditions ALL pass with matched action visibility and budgets.
POLICY={"version":VERSION,"episodes":24,"families":{"nested-evidence":8,"lineage":8,"current-vs-history":8},
        "max_actions":MAX_STEPS,"max_native_calls":264,
        "teacher_visible":"English state/instructions/natural-English action names/descriptions only",
        "controls":["random","heuristic","native-one-shot"],
        "qualify":{"kev_min_total":14,"kev_min_each_family":4,
                   "kev_over_random":8,"kev_over_one_shot":8,
                   "kev_over_heuristic":4,"max_native_errors":2,
                   "invalid_actions_allowed":0,"oracle_disagreement_allowed":0},
        "student_if_qualified":{"source":"accepted-U6-step-13400","maximum_updates":64,
                                "dev_gate_cadence":8,
                                "batch":{"current":12,"fresh_prior":4,"cross_stage":8,"weak_reinforcement":8},
                                "weak_priorities":{"U4":3,"U6_lineage":2,"U0":1,"other":2},
                                "final_no_access_before_training":True},
        "no_student_training_if_failed":True,"fixed_control_seed":48025,
        "sealed_final_policy":"8 held-out seeded worlds; file existence verified, not read during qualification",
        "status":"exploratory_DEV_qualification_not_confirmatory"}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):
    blob=path.read_bytes()
    return json.loads(gzip.decompress(blob) if path.suffix==".gz" else blob)
def write(path,obj):
    with path.open("xb") as f:f.write(canonical(obj)+b"\n")
def compressed(path,obj):
    with path.open("xb") as f:f.write(gzip.compress(canonical(obj)+b"\n",mtime=0))
def source_sha():
    paths=["bilqis_u7d/laboratory_v2.py","bilqis_u7d/run_v2.py",
           "bilqis_development/vendor/kev_teacher.py",
           "bilqis_micro/kernel.py","bilqis_development/kernel.py"]
    return {p:sha(ROOT/p) for p in paths}
def _control_rows(eps):
    out={}
    for actor in ("random","heuristic"):
        rows=[]
        for i,e in enumerate(eps):
            seed=POLICY["fixed_control_seed"]+i*113
            res=run_control(e,actor,seed)
            rows.append({"episode":e["id"],"family":e["kind"],**res})
        out[actor]={"episodes":rows,"successes":sum(r["success"] for r in rows),
                    "by_family":{k:sum(r["success"] for r in rows if r["family"]==k)
                                 for k in ("nested-evidence","lineage","current-vs-history")},
                    "actions":sum(r["actions_used"] for r in rows)}
    return out

def freeze(run=RUN):
    if run.exists():raise FileExistsError("immutable U7D run directory already exists")
    dev=build(DEVELOPMENT_SEED)
    sealed=build(SEALED_SEED)[:8]
    validate_episodes(dev)
    hashes={e["semantic_fingerprint"] for e in dev}
    if len(hashes)!=len(dev) or len({e["semantic_fingerprint"] for e in sealed})!=len(sealed) or hashes&{e["semantic_fingerprint"] for e in sealed}:
        raise ValueError("TRAIN/DEV versus final world collision")
    controls=_control_rows(dev)
    if any(sum(e["dossiers"][n]["initial"]!=e["dossiers"][n]["intervened"] for n in DOSSIERS)!=1 for e in dev):
        raise ValueError("more than one independent causal contrast")
    run.mkdir(parents=True,exist_ok=False)
    compressed(run/"dev-episodes.json.gz",dev)
    compressed(run/"sealed-final.json.gz",sealed)
    write(run/"matched-controls.json",controls)
    manifest={"policy":POLICY,"source_hashes":source_sha(),
              "dev_episode_sha256":sha(run/"dev-episodes.json.gz"),
              "sealed_final_sha256":sha(run/"sealed-final.json.gz"),
              "matched_controls_sha256":sha(run/"matched-controls.json"),
              "world_oracles_independently_agree":True,
              "one_factor_count_preserving_mutations":True,
              "public_sources":{k:dev[next(i for i,x in enumerate(dev) if x["kind"]==k)]["source"] for k in ("nested-evidence","lineage","current-vs-history")},
              "actions_frozen_before_native_requests":True,
              "parent_pr_113":"d2850f9eecb6138b7442e8927286894ff7b5d2da",
              "student_optimizer_updates":0}
    write(run/"freeze.json",manifest)
    return {"status":"FROZEN","dev":len(dev),"sealed_not_opened":len(sealed),
            "random":controls["random"]["successes"],"heuristic":controls["heuristic"]["successes"],
            "one_shot":"native-control-pending","student_updates":0}

def verify(run=RUN):
    manifest=read(run/"freeze.json")
    if manifest["source_hashes"]!=source_sha() or manifest["policy"]!=POLICY:
        raise ValueError("U7D source or frozen policy drift")
    for name,key in (("dev-episodes.json.gz","dev_episode_sha256"),
                     ("sealed-final.json.gz","sealed_final_sha256"),
                     ("matched-controls.json","matched_controls_sha256")):
        if sha(run/name)!=manifest[key]:raise ValueError("U7D preserved evidence altered: "+name)
    dev=read(run/"dev-episodes.json.gz")
    validate_episodes(dev)
    return manifest,dev

def _episode(e,teacher,record):
    s=start(e)
    log=[]
    native_errors=0
    for step in range(MAX_STEPS):
        if s["done"]:break
        options=legal(e,s)
        if not options:break
        # English-only. Stable Latin-square permutation changes option ordering
        # independently of the answer-bearing world and current queried value.
        offset=(int(e["id"][-2:])+step)%len(options)
        options=options[offset:]+options[:offset]
        state_text=prose(e,s)
        question=("Choose the most informative legal next action to discover a one-factor "
                  "cause of changed current evidence. Inspect concrete world facts, "
                  "test a candidate intervention, then report only a verified contrast. "
                  "Do not claim success from inspection alone. End without a finding if "
                  "you cannot prove one within the remaining action budget.")
        if any(x in state_text+question+" ".join(o["candidate_id"]+o["description"] for o in options)
               for x in ('"kind"', '"op"', '"gold"', 'J0', 'S0', 'E0', '{', '}')):
            raise ValueError("semantic typed ABI leaked into native English context")
        trace=teacher.score(state_text,question,options,
            {"epoch":"U7D","episode":e["id"],"step":step,"choice_role":"investigation"})
        choice=trace.get("choice")
        if trace["status"]=="ERROR":
            native_errors+=1
            choice="End unresolved"
        if choice not in {o["candidate_id"] for o in options}:
            native_errors+=1
            choice="End unresolved"
        old=s
        s,feedback=apply(e,s,choice)
        receipt={"episode":e["id"],"step":step,
                 "selected_action":choice,"available": [o["candidate_id"] for o in options],
                 "previous_state_hash":digest(old),
                 "next_state_hash":digest(s),
                 "transition_sha256":step_hash(e,old,choice,s,feedback),
                 "feedback":feedback,"native":trace}
        record(receipt)
        log.append({"choice":choice,"feedback":feedback,"hash":receipt["transition_sha256"]})
    return {"episode":e["id"],"family":e["kind"],"success":s["success"],
            "reported":s["reported"],"actions":s["actions"],
            "actions_used":len(s["actions"]),"tested":len(s["tested"]),
            "inspected":len(s["inspected"]),"native_errors":native_errors,
            "discoveries":int(s["success"]),"final_state_sha256":digest(s),
            "transition_digest":digest(log)}

def _score(rows,controls):
    correct=sum(r["success"] for r in rows)
    by_family={k:sum(r["success"] for r in rows if r["family"]==k)
               for k in ("nested-evidence","lineage","current-vs-history")}
    native_errors=sum(r["native_errors"] for r in rows)
    gate=POLICY["qualify"]
    failed=[]
    if correct<gate["kev_min_total"]:failed.append("TOTAL_UNDER_MINIMUM")
    if any(v<gate["kev_min_each_family"] for v in by_family.values()):
        failed.append("FAMILY_UNDER_MINIMUM")
    if correct<controls["random"]["successes"]+gate["kev_over_random"]:
        failed.append("NOT_BETTER_THAN_RANDOM")
    if correct<controls["native-one-shot"]["successes"]+gate["kev_over_one_shot"]:
        failed.append("NOT_BETTER_THAN_ONE_SHOT")
    if correct<controls["heuristic"]["successes"]+gate["kev_over_heuristic"]:
        failed.append("WORSE_THAN_HEURISTIC_TOLERANCE")
    if native_errors>gate["max_native_errors"]:failed.append("TOO_MANY_NATIVE_ERRORS")
    return {"qualified":not failed,"rejected_reasons":failed,
            "teacher":{"correct":correct,"n":len(rows),"by_family":by_family,
                       "actions":sum(r["actions_used"] for r in rows),
                       "native_errors":native_errors,"validated_discoveries":correct},
            "controls":{k:{"correct":v["successes"],"by_family":v["by_family"],
                            "actions":v["actions"]} for k,v in controls.items()},
            "required":gate,
            "student_optimizer_permitted":not failed}

def qualify(run=RUN):
    _,dev=verify(run)
    if (run/"qualification.json").exists() or (run/"native-traces.jsonl.gz").exists():
        raise FileExistsError("native qualification may never be reissued for same frozen cohort")
    teacher=KevTeacher()
    calls=0
    api_seconds=0.
    usage=Counter()
    controls=read(run/"matched-controls.json")
    one_shot=[]
    with (run/"native-one-shot.jsonl.gz").open("xb") as raw:
        with gzip.GzipFile(fileobj=raw,mode="wb",mtime=0) as stream:
            for index,e in enumerate(dev):
                choices=[{"candidate_id":"Inspect "+name,
                          "description":"Commit to dossier "+name+" before learning its evidence. No further observations can change this choice."}
                         for name in DOSSIERS]
                state=initial(e)
                question=("Choose one dossier to investigate without inspecting any facts first. "
                          "This is a one-decision baseline; your choice cannot change after evidence is revealed.")
                trace=teacher.score(state,question,choices,{"epoch":"U7D","episode":e["id"],"mode":"one-shot"})
                picked=trace.get("choice","")
                if picked not in {x["candidate_id"] for x in choices}:
                    picked="Inspect "+DOSSIERS[0]
                name=picked[len("Inspect "):]
                result=run_control(e,"one-shot:"+name,POLICY["fixed_control_seed"]+index*113)
                one_shot.append({"episode":e["id"],"family":e["kind"],**result})
                stream.write(canonical({"episode":e["id"],"selection":name,"trace":trace,"outcome":result})+b"\n")
                calls+=int(trace["choice_calls"])
                api_seconds+=trace["wall_seconds"]
                if isinstance(trace.get("usage"),dict):
                    for k,v in trace["usage"].items():
                        if isinstance(v,(int,float)):usage[k]+=v
    controls["native-one-shot"]={"episodes":one_shot,
        "successes":sum(x["success"] for x in one_shot),
        "by_family":{k:sum(x["success"] for x in one_shot if x["family"]==k)
                     for k in ("nested-evidence","lineage","current-vs-history")},
        "actions":sum(x["actions_used"] for x in one_shot)}
    with (run/"native-traces.jsonl.gz").open("xb") as raw:
        with gzip.GzipFile(fileobj=raw,mode="wb",mtime=0) as stream:
            def emit(rec):
                nonlocal calls,api_seconds
                trace=rec["native"]
                calls+=int(trace["choice_calls"])
                api_seconds+=trace["wall_seconds"]
                if isinstance(trace.get("usage"),dict):
                    for k,v in trace["usage"].items():
                        if isinstance(v,(int,float)):usage[k]+=v
                stream.write(canonical(rec)+b"\n")
            outcome=[_episode(e,teacher,emit) for e in dev]
    gate=_score(outcome,controls)
    report={"epoch":"U7D","status":"QUALIFIED" if gate["qualified"] else "NOT_QUALIFIED",
            "teacher_runtime":teacher.identity,"per_episode":outcome,
            "qualification":gate,"native_calls":calls,"native_wall_seconds":api_seconds,
            "native_usage":dict(usage),
            "native_traces_sha256":sha(run/"native-traces.jsonl.gz"),
            "native_one_shot_sha256":sha(run/"native-one-shot.jsonl.gz"),
            "native_one_shot_control":controls["native-one-shot"],
            "frozen_source_sha256":sha(run/"freeze.json"),
            "student_optimizer_updates":0,
            "sealed_final_opened":False}
    write(run/"qualification.json",report)
    return {"status":report["status"],"qualified":gate["qualified"],
            "teacher":gate["teacher"],"controls":gate["controls"],
            "reasons":gate["rejected_reasons"],"native_calls":calls,
            "native_wall_seconds":api_seconds,"student_optimizer_updates":0}

def replay(run=RUN):
    _,dev=verify(run)
    original=read(run/"qualification.json")
    with gzip.open(run/"native-traces.jsonl.gz","rt") as f:
        traces=[json.loads(x) for x in f]
    if sha(run/"native-traces.jsonl.gz")!=original["native_traces_sha256"]:
        raise ValueError("native trace digest changed")
    if sha(run/"native-one-shot.jsonl.gz")!=original["native_one_shot_sha256"]:
        raise ValueError("native one-shot bytes altered")
    with gzip.open(run/"native-one-shot.jsonl.gz","rt") as f:
        one_shot=[json.loads(x) for x in f]
    if len(one_shot)!=len(dev):raise ValueError("missing one-shot decisions")
    for i,(r,e) in enumerate(zip(one_shot,dev)):
        wire=r["trace"]["serialized_request"]
        if hashlib.sha256(wire.encode()).hexdigest()!=r["trace"]["request_sha256"]:
            raise ValueError("one-shot native byte identity")
        parsed=json.loads(wire)
        if parsed!=r["trace"]["payload"] or parsed["state"]!=initial(e):
            raise ValueError("one-shot prompt/episode mismatch")
        sampled=run_control(e,"one-shot:"+r["selection"],POLICY["fixed_control_seed"]+i*113)
        if sampled!=r["outcome"]:raise ValueError("one-shot contrast mismatch")
    groups={}
    for row in traces:groups.setdefault(row["episode"],[]).append(row)
    recovered=[]
    for e in dev:
        s=start(e);chain=[]
        rows=groups[e["id"]]
        for step,r in enumerate(rows):
            if r["step"]!=step or digest(s)!=r["previous_state_hash"]:
                raise ValueError("missing step / bad prior state")
            opts=legal(e,s)
            shift=(int(e["id"][-2:])+step)%len(opts)
            opts=opts[shift:]+opts[:shift]
            native=r["native"]
            raw=native["serialized_request"]
            if hashlib.sha256(raw.encode()).hexdigest()!=native["request_sha256"]:
                raise ValueError("native request byte integrity")
            wire=json.loads(raw)
            if (wire!=native["payload"] or
                list(wire["questions"]["decision"]["criteria"])!=[x["candidate_id"] for x in opts]):
                raise ValueError("native request and offered order mismatch")
            if wire["state"]!=prose(e,s):raise ValueError("inference saw wrong state")
            if r["available"]!=[x["candidate_id"] for x in opts]:raise ValueError("available action drift")
            if r["selected_action"] not in r["available"]:raise ValueError("unoffered executed action")
            nxt,feedback=apply(e,s,r["selected_action"])
            if (feedback!=r["feedback"] or digest(nxt)!=r["next_state_hash"] or
                step_hash(e,s,r["selected_action"],nxt,feedback)!=r["transition_sha256"]):
                raise ValueError("deterministic world transition mismatch")
            chain.append({"choice":r["selected_action"],"feedback":feedback,"hash":r["transition_sha256"]})
            s=nxt
        recovered.append({"episode":e["id"],"family":e["kind"],"success":s["success"],
                          "reported":s["reported"],"actions":s["actions"],
                          "actions_used":len(s["actions"]),"tested":len(s["tested"]),
                          "inspected":len(s["inspected"]),
                          "native_errors":original["per_episode"][len(recovered)]["native_errors"],
                          "discoveries":int(s["success"]),"final_state_sha256":digest(s),
                          "transition_digest":digest(chain)})
    if recovered!=original["per_episode"]:raise ValueError("episode replay mismatch")
    controls=read(run/"matched-controls.json")
    controls["native-one-shot"]=original["native_one_shot_control"]
    scored=_score(recovered,controls)
    if scored!=original["qualification"]:raise ValueError("qualification replay mismatch")
    receipt={"status":"EXACT_ENVIRONMENT_AND_NATIVE_BYTE_REPLAY",
             "worlds":len(dev),"choice_calls":original["native_calls"],
             "all_transitions_verified":True,"all_candidate_orders_verified":True,
             "all_oracles_verified":True,"additional_native_calls":0,
             "student_updates":original["student_optimizer_updates"]}
    write(run/"replay.json",receipt)
    return receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("freeze","qualify","replay"))
    p.add_argument("--run",type=Path,default=RUN)
    a=p.parse_args()
    value={"freeze":freeze,"qualify":qualify,"replay":replay}[a.action](a.run)
    print(json.dumps(value,sort_keys=True))
if __name__=="__main__":main()
