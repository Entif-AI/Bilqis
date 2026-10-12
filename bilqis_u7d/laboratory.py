"""Typed, deterministic finite worlds. Kev sees only English views and legal actions."""
from __future__ import annotations
from collections import Counter
import copy
import hashlib
import random

from bilqis_logic.kernel import canonical, digest
from bilqis_micro import kernel as prior
from bilqis_development import kernel as recent

VERSION = "u7d-laboratory-1"
N_EPISODES = 24
MAX_STEPS = 10
DOSSIERS = ("Ash", "Birch", "Cedar", "Elm", "Hazel", "Juniper", "Maple", "Willow")
KIND = ("evidence", "supersession")
SOURCE = {"evidence": "https://github.com/Entif-AI/Bilqis/issues/80",
          "supersession": "https://github.com/Entif-AI/Bilqis/issues/84"}


def _base():
    return prior.world("ABC", propositions={
        "J0": prior.relation("PARENT", prior.entity("A"), prior.entity("B")),
        "J1": prior.relation("PARENT", prior.entity("B"), prior.entity("C"))})


def _outcome(kind, dossier, intervened):
    base = _base()
    if kind == "evidence":
        reports = [["S0", "J0", dossier["first"], 0],
                   ["S1", "J1" if intervened else "J0", dossier["second"], 0]]
        query = prior.record(prior.world("ABC", propositions=base["propositions"], reports=reports),
                             prior.observe("J0"))
        a, b = prior.evaluate(query), prior.independent_evaluate(query)
    else:
        link = dossier["link"]
        if intervened:
            link = {"SUPERSEDES": "DERIVED_FROM", "DERIVED_FROM": "DEPENDS_ON",
                    "DEPENDS_ON": "DERIVED_FROM"}[link]
        world = recent.world("ABC", base=base,
                             events=[["E0", "ASSERT", "S0", "J0", dossier["first"]],
                                     ["E1", "INFER" if dossier["link"] in ("DERIVED_FROM", "DEPENDS_ON") else "OBSERVE", "S1", "J0", dossier["second"]]],
                             links=[[link, "E1", "E0"]])
        query = recent.record(world, recent.op("CURRENT_STATE", recent.const("Proposition", "J0")))
        a, b = recent.evaluate(query), recent.independent_evaluate(query)
    if a != b: raise ValueError("formal interpreter/oracle mismatch")
    return a, digest(query)


def _make_dossier(kind, positive, rng):
    first = rng.choice(("support", "refute"))
    second = ("refute" if first == "support" else "support") if positive else first
    if kind == "supersession":
        link = "SUPERSEDES" if positive else rng.choice(("SUPERSEDES", "DERIVED_FROM", "DEPENDS_ON"))
    else:
        link = "report-assignment"
    return {"first":first, "second":second, "link":link}


def build(seed=91457):
    rng = random.Random(seed)
    result = []
    for i in range(N_EPISODES):
        kind = KIND[i%2]
        target = (i//2)%len(DOSSIERS)
        rows={}
        for j,name in enumerate(DOSSIERS):
            spec = _make_dossier(kind, j==target, rng)
            a, source_digest = _outcome(kind,spec,False)
            b, changed_digest = _outcome(kind,spec,True)
            if (a!=b)!=(j==target):
                raise ValueError("exactly one actual causal contrast per episode")
            rows[name] = dict(spec, before=a, after=b,
                              before_query_sha256=source_digest, after_query_sha256=changed_digest)
        episode={"id":f"U7D-{i:02d}", "stage":"U4" if kind=="evidence" else "U6",
                 "kind":kind, "source":SOURCE[kind], "dossiers":rows,
                 "target":DOSSIERS[target], "maximum_actions":MAX_STEPS,
                 "seed":seed, "id_sha256":digest([kind,rows])}
        result.append(episode)
    validate_episodes(result)
    return result


def validate_episodes(episodes):
    if len(episodes)!=N_EPISODES or Counter(e["kind"] for e in episodes)!={"evidence":12,"supersession":12}:
        raise ValueError("invalid episode family/schedule")
    for e in episodes:
        if e["maximum_actions"]!=MAX_STEPS or set(e["dossiers"])!=set(DOSSIERS):
            raise ValueError("incorrect episode legal actions")
        ids=[]
        for name,spec in e["dossiers"].items():
            before, qb=_outcome(e["kind"],spec,False)
            after, qa=_outcome(e["kind"],spec,True)
            if (before,after,qb,qa)!=(spec["before"],spec["after"],spec["before_query_sha256"],spec["after_query_sha256"]):
                raise ValueError("frozen world or independent oracle has drifted")
            ids.append(name if before!=after else "")
            if e["kind"]=="evidence" and spec["link"]!="report-assignment":raise ValueError("wrong U4 action")
        if [n for n in ids if n]!=[e["target"]]:
            raise ValueError("wrong frozen intervention gold or multiple causes")
        if e["source"]!=SOURCE[e["kind"]] or e["id_sha256"]!=digest([e["kind"],e["dossiers"]]):
            raise ValueError("invalid source and world provenance")
    if any(Counter(e["target"] for e in episodes if e["kind"]==k)!=dict.fromkeys(DOSSIERS,1)
           for k in KIND):
        # 12 episodes per family; targets repeat some positions, but no position more than twice.
        for k in KIND:
            v=Counter(e["target"] for e in episodes if e["kind"]==k)
            if min(v.values()) < 1 or max(v.values())>2: raise ValueError("target position skew")
    return True


def initial(episode):
    if episode["kind"]=="evidence":
        topic = ("For each named dossier, two source reports concern the same proposition. "
                 "The result may depend on evidence conflicts. You may inspect dossiers and "
                 "run one-factor report-reassignment contrasts.")
    else:
        topic = ("For each named dossier, two reports have a relationship in their event history. "
                 "Replacement, content origin and premise-use links have different effects "
                 "on the current evidence. You may inspect dossiers and rewire one link per test.")
    return ("You are an investigator in a small finite semantic world. Discover and verify "
            "which single named dossier has an intervention that changes the current evidence "
            "for the questioned claim. An inspection reveals facts but is not discovery. "
            "Only a checked contrast followed by a finding counts. "
            "All eight dossiers are equally likely by name; names are identifiers only. "
            "You have ten actions, including a finding. No guessing from the name. "+topic+
            " Available dossiers: "+", ".join(DOSSIERS)+". ")


def inspection(episode,name):
    x=episode["dossiers"][name]
    a="supports" if x["first"]=="support" else "disputes"
    b="supports" if x["second"]=="support" else "disputes"
    if episode["kind"]=="evidence":
        return (f"Dossier {name}: source One {a} the questioned claim; source Two {b} "
                "the same claim. Both reports are presently counted. "
                "The available test reassigns the second report to a different claim "
                "while keeping the number of reports constant.")
    relation={"SUPERSEDES":"explicitly replaces the earlier report",
              "DERIVED_FROM":"copied content from the earlier report",
              "DEPENDS_ON":"uses the earlier report as a premise"}[x["link"]]
    return (f"Dossier {name}: the earlier source {a} the claim; the later source {b} it. "
            f"The later report {relation}. The available test rewires exactly that "
            "one relation without changing the report count or contents.")


def start(episode):
    return {"inspected":[], "tested":[], "observations":[], "reported":None,
            "success":False, "done":False, "actions":[]}


def legal(episode,state):
    if state["done"]:return []
    options=[]
    if state["reported"] is None:
        for name in DOSSIERS:
            if name not in state["inspected"]:
                options.append({"candidate_id":"Inspect "+name,"description":f"Inspect dossier {name} and learn its underlying evidence and relation facts."})
        for name in state["inspected"]:
            if name not in state["tested"]:
                options.append({"candidate_id":"Test "+name,"description":f"Run a one-factor causal contrast for dossier {name}; compare current evidence before and after the intervention."})
        for name in state["tested"]:
            if any(o["name"]==name and o.get("different") for o in state["observations"]):
                options.append({"candidate_id":"Report "+name,"description":f"Submit the verified causal discovery for dossier {name}, using the observed intervention contrast."})
        options.append({"candidate_id":"End without finding","description":"Stop and report that the evidence is insufficient; do not claim a discovery."})
    # At most 8 inspect + at most 8 test + 1 report; a native choice API handles up to 16.
    if len(options)>16:raise ValueError("native candidate bound exceeded")
    return options


def apply(episode,state,action):
    choices={o["candidate_id"] for o in legal(episode,state)}
    if action not in choices:raise ValueError("illegal action")
    s=copy.deepcopy(state)
    if action.startswith("Inspect "):
        name=action[len("Inspect "):]
        s["inspected"].append(name)
        message=inspection(episode,name)
        s["observations"].append({"action":"inspect","name":name,"feedback":message})
    elif action.startswith("Test "):
        name=action[len("Test "):]
        x=episode["dossiers"][name]
        different=x["before"]!=x["after"]
        s["tested"].append(name)
        message=(f"Controlled contrast on {name}: initial evidence was {x['before'].lower()}; "
                 f"after changing exactly one {'report assignment' if episode['kind']=='evidence' else 'report relationship'}, "
                 f"evidence was {x['after'].lower()}. The two outcomes "
                 +("differ." if different else "are unchanged.")+
                 " Independent source and finite-world oracles agreed.")
        s["observations"].append({"action":"test","name":name,"different":different,"feedback":message})
    elif action.startswith("Report "):
        name=action[len("Report "):]
        s["reported"]=name
        s["success"]=(name==episode["target"] and name in s["tested"] and
                      any(o.get("different") and o["name"]==name for o in s["observations"]))
        s["done"]=True
        message="Finding submitted and bound to an independently verified intervention." if s["success"] else "Unverified finding rejected."
    else:
        s["done"]=True
        message="Investigation ended without a verified discovery."
    s["actions"].append(action)
    return s,message


def prose(episode,state):
    observations="\n".join(str(i+1)+". "+o["feedback"] for i,o in enumerate(state["observations"]))
    return initial(episode)+("\nObservations so far:\n"+observations if observations else "\nNo dossier inspected yet.")+f"\nActions used: {len(state['actions'])} of {MAX_STEPS}."


def step_hash(episode,old,action,new,feedback):
    return digest({"episode":episode["id"],"previous":old,"action":action,"next":new,"feedback":feedback})


def run_control(episode,actor,seed):
    rng=random.Random(seed)
    s=start(episode)
    target=actor.split(":",1)[-1] if actor.startswith("one-shot:") else rng.choice(DOSSIERS)
    selected=None
    for step in range(MAX_STEPS):
        opts=legal(episode,s)
        if not opts or s["done"]:break
        if actor=="random": action=rng.choice([o["candidate_id"] for o in opts])
        elif actor=="heuristic":
            # All deductions depend exclusively on inspected textual facts,
            # never episode target or oracle truth.
            inspected=[x for x in DOSSIERS if x in s["inspected"] and x not in s["tested"]]
            preferred=[]
            for x in inspected:
                msg=next(o["feedback"] for o in s["observations"] if o["name"]==x and o["action"]=="inspect")
                if episode["kind"]=="evidence":
                    marked= ("source One supports" in msg and "source Two disputes" in msg) or (
                        "source One disputes" in msg and "source Two supports" in msg)
                else:
                    marked=("explicitly replaces" in msg and (
                        ("earlier source supports" in msg and "later source disputes" in msg) or
                        ("earlier source disputes" in msg and "later source supports" in msg)))
                if marked:preferred.append(x)
            viable=[f"Report {x}" for x in DOSSIERS if f"Report {x}" in {o["candidate_id"] for o in opts}]
            if viable:action=viable[0]
            elif preferred:action="Test "+preferred[0]
            else:
                unopened=[x for x in DOSSIERS if x not in s["inspected"]]
                action="Inspect "+unopened[0] if unopened else (
                    f"Test {inspected[0]}" if inspected else "End without finding")
        elif actor.startswith("one-shot"):
            # A one-shot prediction is fixed before any dossier evidence.
            if step==0:action="Inspect "+target
            elif step==1:action="Test "+target
            elif f"Report {target}" in {o["candidate_id"] for o in opts}:action=f"Report {target}"
            else:action="End without finding"
        else:raise ValueError("unknown control")
        if action not in {o["candidate_id"] for o in opts}:action="End without finding"
        s,_=apply(episode,s,action)
    return {"success":s["success"],"actions":s["actions"],"action_count":len(s["actions"]),
            "observed":len(s["inspected"]),"contrasts":len(s["tested"])}
