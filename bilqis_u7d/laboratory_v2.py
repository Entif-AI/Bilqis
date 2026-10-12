"""U7D semantic laboratory v2: nested U4 evidence and U6 multi-hop lineage.

Immutable typed source/oracle worlds are *never* sent to Kev. Every legal
intervention changes one report assignment or edge type, preserving cardinality.
"""
from __future__ import annotations
from collections import Counter
import copy
import random

from bilqis_logic.kernel import digest
from bilqis_micro import kernel as old
from bilqis_development import kernel as new

VERSION="u7d-laboratory-3"
N_EPISODES=24
MAX_STEPS=10
DOSSIERS=("Ash","Birch","Cedar","Elm","Hazel","Juniper","Maple","Willow")
KIND=("nested-evidence","lineage","current-vs-history")
SOURCES={"nested-evidence":"https://github.com/Entif-AI/Bilqis/issues/80",
         "lineage":"https://github.com/Entif-AI/Bilqis/issues/84",
         "current-vs-history":"https://github.com/Entif-AI/Bilqis/issues/84"}

def _base(s):
    persons=("ABC","ABCD","ABCDE")[s%3]
    return old.world(persons,facts=[("PARENT",persons[0],persons[1])],
        propositions={"J0":old.relation("PARENT",old.entity(persons[0]),old.entity(persons[1])),
                      "J1":old.relation("PARENT",old.entity(persons[1]),old.entity(persons[0]))})

def _query(spec,intervened):
    kind=spec["kind"]
    base=_base(spec["world_variant"])
    if kind=="nested-evidence":
        reports=copy.deepcopy(spec["reports"])
        if intervened:
            # Reassign one report, same source/position/polarity/count.
            reports[0][1]="J1" if reports[0][1]=="J0" else "J0"
        w=old.world(base["entities"],facts=base["facts"],propositions=base["propositions"],
                    reports=reports,live=spec["live"])
        query=old.observe("J0")
        q=old.evidence_logic(spec["operation"],query,old.observe("J1")) if spec["operation"]!="NOT" else old.evidence_logic("NOT",old.evidence_logic("AND",query,old.observe("J1")))
        return "old",old.record(w,q)
    events=[["E0","ASSERT","S0","J0",spec["first"]],
            ["E1","INFER","S1","J0",spec["second"]],
            ["E2","INFER","S2","J0",spec["third"]]]
    links=[[spec["link1"],"E2","E1"],
           [spec["link2"],"E1","E0"]]
    if intervened:
        if kind=="lineage":
            links[0][0]="DEPENDS_ON" if links[0][0]=="DERIVED_FROM" else "DERIVED_FROM"
        else:
            links[0][0]="DERIVED_FROM" if links[0][0]=="SUPERSEDES" else "SUPERSEDES"
    w=new.world(base["entities"],base=base,events=events,links=links)
    if kind=="lineage":
        a=new.op("DERIVED_FROM",new.const("Event","E2"),new.const("Event","E0"))
        b=new.op("DEPENDENCY",new.const("Event","E2"),new.const("Event","E0"))
        q=new.op("AND",a,new.op("NOT",b)) if spec["operation"]=="AND" else new.op("OR",a,b)
        return "new",new.record(w,q)
    # Current and historical provenance distinction jointly evaluated.
    current=new.op("CURRENT_STATE",new.const("Proposition","J0"))
    historical=new.op("HISTORICAL_STATE",new.const("Proposition","J0"))
    return "pair",(new.record(w,current),new.record(w,historical))

def oracle(spec,intervened=False):
    source,rec=_query(spec,intervened)
    if source=="pair":
        a=tuple(new.evaluate(x) for x in rec)
        b=tuple(new.independent_evaluate(x) for x in rec)
    else:
        run=old if source=="old" else new
        a,b=run.evaluate(rec),run.independent_evaluate(rec)
    if a!=b:raise ValueError("independent semantic oracles disagree")
    if source=="pair":a=list(a)
    return a,digest(rec)

def _candidate(kind,operation,variant,rng):
    if kind=="nested-evidence":
        live=[0,1]
        # Fixed report and interpretation counts. Dossier identity never reveals
        # whether changing one proposition assignment changes nested evidence.
        reports=[[rng.choice(("S0","S1","S2")),rng.choice(("J0","J1")),
                  rng.choice(("support","refute")),rng.choice(live)] for _ in range(4)]
        reports[0][1]="J0"
        return {"kind":kind,"operation":operation,"world_variant":variant,
                "live":live,"reports":reports}
    return {"kind":kind,"operation":operation,"world_variant":variant,
            "first":rng.choice(("support","refute")),
            "second":rng.choice(("support","refute")),
            "third":rng.choice(("support","refute")),
            "link1":rng.choice(("SUPERSEDES","DERIVED_FROM")) if kind=="current-vs-history" else rng.choice(("DERIVED_FROM","DEPENDS_ON")),
            "link2":rng.choice(("DERIVED_FROM","DEPENDS_ON","SUPERSEDES"))}

def _kind(i):
    return ("nested-evidence","lineage","current-vs-history")[i%3]
def _operation(kind,i):
    if kind=="nested-evidence":return ("AND","OR","NOT")[(i//3)%3]
    if kind=="lineage":return ("AND","OR")[(i//3)%2]
    return "CURRENT_HISTORICAL"

def build(seed=88711):
    rng=random.Random(seed)
    episodes=[]
    for i in range(N_EPISODES):
        kind,operation=_kind(i),_operation(_kind(i),i)
        # Balanced index permutation by family, no deterministic A-first cue.
        target=DOSSIERS[(i*5+seed)%len(DOSSIERS)]
        rows={}
        for name in DOSSIERS:
            wanted=(name==target)
            for attempts in range(5000):
                spec=_candidate(kind,operation,(i+attempts)%3,rng)
                try:
                    before,qa=oracle(spec)
                    after,qb=oracle(spec,True)
                except ValueError:
                    continue
                if (before!=after)==wanted:
                    rows[name]=dict(spec,initial=before,intervened=after,
                                    before_sha256=qa,after_sha256=qb)
                    break
            else:raise ValueError(f"cannot build {kind} {operation} wanted={wanted}")
        episode={"id":f"U7D-{i:02d}","kind":kind,"operation":operation,"dossiers":rows,
                 "source":SOURCES[kind],"target":target,"max_steps":MAX_STEPS,
                 "semantic_fingerprint":digest([kind,operation,rows])}
        episodes.append(episode)
    validate_episodes(episodes)
    return episodes

def validate_episodes(episodes):
    if len(episodes)!=N_EPISODES or Counter(e["kind"] for e in episodes)!={"nested-evidence":8,"lineage":8,"current-vs-history":8}:
        raise ValueError("stage/family episode schedule")
    for e in episodes:
        if set(e["dossiers"])!=set(DOSSIERS) or e["max_steps"]!=MAX_STEPS:raise ValueError("legal episode shape")
        active=[]
        for name,spec in e["dossiers"].items():
            a,qa=oracle(spec);b,qb=oracle(spec,True)
            if (a,b,qa,qb)!=(spec["initial"],spec["intervened"],spec["before_sha256"],spec["after_sha256"]):
                raise ValueError("frozen oracle or world drift")
            if a!=b:active.append(name)
        if active!=[e["target"]]:raise ValueError("no single independently checked contrast")
        if digest([e["kind"],e["operation"],e["dossiers"]])!=e["semantic_fingerprint"]:
            raise ValueError("semantic fingerprint drift")
        # Observation shape must not directly reveal response from world-size.
        if e["kind"]=="nested-evidence":
            assert all(len(s["reports"])==4 and s["live"]==[0,1] for s in e["dossiers"].values())
        else:
            assert all(len((_query(s,False)[1][0] if e["kind"]=="current-vs-history" else _query(s,False)[1])["world"]["links"])==2 for s in e["dossiers"].values())
    return True

def initial(e):
    if e["kind"]=="nested-evidence":
        task=("Study evidence for two propositions across two live interpretations. "
              f"The question combines their evidence by {e['operation'].lower()} reasoning, "
              "including unknown, conflict and ambiguity where applicable. "
              "Each test reassigns one report to the other proposition without changing report count.")
    elif e["kind"]=="lineage":
        task=("Study a three-event history where content-origin, inferential-premise and "
              f"two-hop ancestry can differ. The question combines them with {e['operation'].lower()} logic. "
              "Each test rewires one edge's meaning, retaining two edges and all reports.")
    else:
        task=("Study which events remain current after replacement, contrasted with all "
              "historical evidence. A test rewires one edge without changing the number "
              "of reports or links.")
    return ("You control a finite semantic investigation. There are eight independent dossiers, "
            "each a different possible world. You can inspect, compare a controlled intervention, "
            "and submit a finding. Only a completed, independently checked one-factor contrast "
            "counts as a discovery. Names do not indicate answer quality. Ten actions maximum. "
            +task+" Dossiers: "+", ".join(DOSSIERS)+".")

def inspection(e,name):
    spec=e["dossiers"][name]
    if e["kind"]=="nested-evidence":
        parts=[]
        for r in spec["reports"]:
            pol="supports" if r[2]=="support" else "disputes"
            parts.append(f"{r[0].replace('S','source ')} {pol} the {'first' if r[1]=='J0' else 'second'} proposition in interpretation {r[3]+1}")
        return f"Dossier {name}. Both interpretations are live. "+"; ".join(parts)+". The first report can be reassigned to the other proposition."
    relation={"DERIVED_FROM":"content was copied from",
              "DEPENDS_ON":"uses as a reasoning premise",
              "SUPERSEDES":"explicitly replaces"}
    return (f"Dossier {name}. First report {spec['first']}s the claim; second {spec['second']}s it; "
            f"third {spec['third']}s it. The third event {relation[spec['link1']]} the second; "
            f"the second event {relation[spec['link2']]} the first. "
            "The test rewires the third-to-second relation into the alternative origin/premise meaning.")

def start(e):
    return {"inspected":[],"tested":[],"reported":None,"success":False,"done":False,
            "world_versions":{name:"original" for name in DOSSIERS},
            "observations":[],"actions":[]}

def legal(e,s):
    if s["done"]:return []
    out=[]
    for name in DOSSIERS:
        if name not in s["inspected"]:
            out.append({"candidate_id":f"Inspect {name}","description":f"Inspect dossier {name}; observe its evidence, events and relation facts."})
    for name in s["inspected"]:
        if name not in s["tested"]:
            out.append({"candidate_id":f"Test {name}","description":f"Intervene on dossier {name}; compare before and after from independent semantic oracles."})
    # Report always possible once inspected, even if wrong; the menu never leaks gold.
    for name in s["inspected"]:
        out.append({"candidate_id":f"Report {name}","description":f"Submit dossier {name} as a causal discovery. An unproven claim will be rejected."})
    out.append({"candidate_id":"End unresolved","description":"Abstain when no independently verified causal discovery is available."})
    if len(out)>25:raise ValueError("legal menu overflow")
    # Native Kev supports 16 options. At 8 inspected, 8 reports+8 tests+stop =17.
    # Cap report proposals to four most recently inspected, independent of oracle gold.
    reports=[x for x in out if x["candidate_id"].startswith("Report ")]
    if len(out)>16:
        last=set(s["inspected"][-max(0,16-len(out)+len(reports)):])
        out=[x for x in out if not x["candidate_id"].startswith("Report ") or x["candidate_id"][7:] in last]
    if len(out)>16:raise ValueError("Kev maximum option count exceeded")
    return out

def apply(e,state,action):
    if action not in {x["candidate_id"] for x in legal(e,state)}:raise ValueError("illegal action")
    s=copy.deepcopy(state)
    if action.startswith("Inspect "):
        name=action[8:];s["inspected"].append(name)
        feedback=inspection(e,name)
        s["observations"].append({"name":name,"kind":"inspect","feedback":feedback})
    elif action.startswith("Test "):
        name=action[5:];spec=e["dossiers"][name]
        initial,current=oracle(spec,s["world_versions"][name]=="intervened")
        # Actual mutation of the typed-world state; oracle reads the new world.
        s["world_versions"][name]="intervened"
        changed,changed_hash=oracle(spec,True)
        if (initial,current)!=(spec["initial"],spec["before_sha256"]):
            raise ValueError("world state mismatch before intervention")
        s["tested"].append(name)
        feedback=(f"Dossier {name} intervention completed. Before: {str(initial).lower()}. "
                  f"After: {str(changed).lower()}. The outcome "
                  +("changed." if initial!=changed else "remained the same.")+
                  " One report assignment or relation meaning was changed; "
                  "the report and edge counts were preserved. Independent oracles agree.")
        s["observations"].append({"name":name,"kind":"test","different":initial!=changed,
                                  "feedback":feedback,"after_query_sha256":changed_hash})
    elif action.startswith("Report "):
        name=action[7:]
        s["reported"]=name;s["done"]=True
        s["success"]=(name==e["target"] and name in s["tested"] and
             any(o.get("different") and o["name"]==name for o in s["observations"]))
        feedback="Submitted finding "+("passed" if s["success"] else "failed")+" independent causal validation."
    else:
        s["done"]=True;feedback="Investigation closed unresolved."
    s["actions"].append(action)
    return s,feedback

def prose(e,s):
    obs="\n".join(f"{i+1}. {o['feedback']}" for i,o in enumerate(s["observations"]))
    return initial(e)+"\nObservations: "+(obs or "none") + f"\nUsed {len(s['actions'])} of {MAX_STEPS} actions."

def transition_digest(e,old_state,choice,new_state,feedback):
    return digest([e["id"],old_state,choice,new_state,feedback])

def run_control(e,mode,seed):
    rng=random.Random(seed)
    state=start(e)
    committed=mode.split(":",1)[1] if mode.startswith("one-shot:") else rng.choice(DOSSIERS)
    for step in range(MAX_STEPS):
        if state["done"]:break
        actions={o["candidate_id"] for o in legal(e,state)}
        tested_positive=[o["name"] for o in state["observations"]
                         if o["kind"]=="test" and o.get("different")]
        if mode=="random":
            choices=[x for x in actions if x!="End unresolved"]
            choice=rng.choice(sorted(choices)) if choices else "End unresolved"
        elif mode=="heuristic":
            # Fixed transparent lexical heuristic, receives same inspections but
            # cannot read hidden truth tables or independently evaluated labels.
            if tested_positive and f"Report {tested_positive[0]}" in actions:
                choice=f"Report {tested_positive[0]}"
            else:
                candidates=[name for name in state["inspected"] if name not in state["tested"]]
                priority=[]
                for name in candidates:
                    x=next(o["feedback"] for o in state["observations"] if o["name"]==name and o["kind"]=="inspect")
                    if e["kind"]=="nested-evidence":
                        marked="supports" in x and "disputes" in x
                    else:
                        marked=("content was copied" in x and "reasoning premise" not in x)
                    if marked:priority.append(name)
                if priority:choice=f"Test {priority[0]}"
                else:
                    unopened=[name for name in DOSSIERS if name not in state["inspected"]]
                    choice=f"Inspect {unopened[0]}" if unopened else (
                        f"Test {candidates[0]}" if candidates else "End unresolved")
        elif mode in ("open-loop",) or mode.startswith("one-shot:"):
            # Commit a dossier name before seeing any evidence. Follow fixed plan,
            # no observation-conditioned revision.
            if step==0:choice=f"Inspect {committed}"
            elif step==1:choice=f"Test {committed}"
            elif step==2:choice=f"Report {committed}"
            else:choice="End unresolved"
        else:raise ValueError("unknown control")
        if choice not in actions:choice="End unresolved"
        state,_=apply(e,state,choice)
    return {"success":state["success"],"actions":state["actions"],
            "actions_used":len(state["actions"]),"tested":len(state["tested"]),
            "inspected":len(state["inspected"])}
