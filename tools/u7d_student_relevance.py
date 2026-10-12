"""Read-only posthoc overlap of frozen U7D worlds with accepted U6 neural errors.

No native Kev inference, no final opening, no gradients, no edits to frozen
candidate worlds. This is exploratory DEV relevance, not prospective selection.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import json
from pathlib import Path

from bilqis_u7d import run_v2 as exp
from bilqis_u7d import laboratory_v2 as lab
from bilqis_development import run as model_run
from bilqis_development.continuation import load
from bilqis_spiral.run import CURRENT

OUT=exp.RUN/"student-relevance-posthoc.json"


def audit():
    _,episodes=exp.verify()
    model,optimizer,payload=load(CURRENT)
    from bilqis_micro.run import optimizer_receipt
    if optimizer_receipt(optimizer)["steps"]!=[13400]:
        raise ValueError("student analysis drifted off accepted U6")
    records=[]
    labels=[]
    for e in episodes:
        for name,spec in e["dossiers"].items():
            for after in (False,True):
                kind,record=lab._query(spec,after)
                gold,_=lab.oracle(spec,after)
                for part,r in enumerate(record if kind=="pair" else [record]):
                    answer=gold[part] if kind=="pair" else gold
                    records.append(r)
                    labels.append({"episode":e["id"],"kind":e["kind"],"name":name,
                                   "intervened":after,"part":part,"gold":answer,
                                   "causal":name==e["target"]})
    preds=model_run.predict(model,records)
    if len(preds)!=len(records):raise ValueError("incomplete U6 prediction audit")
    totals=Counter()
    by_family=defaultdict(Counter)
    causal=defaultdict(Counter)
    for item,pred in zip(labels,preds):
        good=(pred["prediction"]==item["gold"])
        totals["correct"]+=good
        totals["n"]+=1
        cat=by_family[item["kind"]]
        cat["correct"]+=good;cat["n"]+=1
        target=causal[item["kind"]]
        if item["causal"]:
            target["correct"]+=good;target["n"]+=1
    per_pair=defaultdict(dict)
    for item,pred in zip(labels,preds):
        key=(item["episode"],item["name"],item["part"])
        per_pair[key][item["intervened"]]=pred["prediction"]
    consistency=Counter()
    for key,vals in per_pair.items():
        if set(vals)!={False,True}:raise ValueError("counterfactual pair missing")
        spec=next(e["dossiers"][key[1]] for e in episodes if e["id"]==key[0])
        original,_=lab.oracle(spec,False)
        changed,_=lab.oracle(spec,True)
        gold_before=original[key[2]] if isinstance(original,list) else original
        gold_after=changed[key[2]] if isinstance(changed,list) else changed
        consistency["n"]+=1
        consistency["gold_changed"]+=(gold_before!=gold_after)
        consistency["student_changed"]+=(vals[False]!=vals[True])
        consistency["joint_correct"]+=(vals[False]==gold_before and vals[True]==gold_after)
        if gold_before!=gold_after:
            consistency["gold_changed_joint_correct"]+=(vals[False]==gold_before and vals[True]==gold_after)
    answer={"status":"POSTHOC_U6_STUDENT_DEV_RELEVANCE_ONLY",
            "student_start":payload["state_sha256"],"optimizer_step":13400,
            "run_freeze_sha256":exp.sha(exp.RUN/"freeze.json"),
            "source_code_sha256":exp.sha(Path(__file__)),
            "dev_episodes":len(episodes),"records":len(records),
            "correct":totals["correct"],"n":totals["n"],
            "by_family":{k:dict(v) for k,v in by_family.items()},
            "causal_dossiers":{k:dict(v) for k,v in causal.items()},
            "paired_semantic_behavior":dict(consistency),
            "sealed_final_unopened":True,"gradients":0}
    exp.write(OUT,answer)
    return answer


if __name__=="__main__":
    print(json.dumps(audit(),sort_keys=True))
