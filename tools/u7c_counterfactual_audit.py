"""Read-only evaluation of U7C's PRE-FROZEN causal sibling cohort.

Posthoc analysis definition, using the original pre-gradient rows and sibling
worlds. Never changes the optimizer, teaching schedule, or frozen source.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path

from bilqis_development import run as student
from bilqis_development.continuation import load
from bilqis_spiral.run import read, sha, write, PARENT, CURRENT
from bilqis_spiral.sampler import check_row, existing_ids
from bilqis_u7c.run import RUN, verify

SOURCE = Path(__file__).resolve()
OUT = RUN / "paired-final-audit.json"


def audit():
    policy, pools, corpus = verify(RUN)
    source = RUN / "paired-causal-final.json.gz"
    if sha(source) != policy["files"]["paired-causal-final.json.gz"]:
        raise ValueError("paired final was altered after freeze")
    final = read(RUN/"final-evaluation.json.gz")
    original = {r["id"]: r for r in final["cross"]}
    witnesses = read(source)
    frozen_train = {r["id"] for group in ("fresh", "weak", "cross")
                    for rows in pools[group].values() for r in rows}
    frozen_dev = existing_ids(corpus)
    sibling_ids = []
    for w in witnesses:
        if w["base"] not in original:
            raise ValueError("paired witness base not in frozen final")
        anchor = original[w["base"]]
        for side in ("old", "new"):
            sibling = check_row(w[side])
            if sibling["id"] in frozen_train or sibling["id"] in frozen_dev or sibling["id"] in original:
                raise ValueError("sibling included in optimizer or old evaluation")
            sibling_ids.append(sibling["id"])
        if w["old"]["gold"] == anchor["gold"] or w["new"]["gold"] == anchor["gold"]:
            raise ValueError("causal contrast did not change gold")
    if len(set(sibling_ids)) != 2*len(witnesses):
        raise ValueError("frozen siblings repeated")
    before, _, _ = load(CURRENT)
    after, _, _ = load(RUN/"after.pt")
    comparisons = {}
    for tag, model in (("before",before),("after",after)):
        rows = [row for w in witnesses for row in
                (original[w["base"]], w["old"], w["new"])]
        scores = student.score(model, rows)
        pred = scores["predictions"]
        if len(pred) != 3*len(witnesses):
            raise ValueError("paired prediction size")
        all_three = 0
        tally = Counter()
        stage = Counter()
        gate = Counter()
        for i, w in enumerate(witnesses):
            group = pred[i*3:i*3+3]
            all_good = all(p["prediction"] == p["gold"] for p in group)
            all_three += all_good
            for x,p in zip(("original", "old_flip", "new_flip"),group):
                tally[(x,"correct")] += p["prediction"] == p["gold"]
                tally[(x,"n")] += 1
                stage[(str(w["stage"]),x,"correct")] += p["prediction"] == p["gold"]
                stage[(str(w["stage"]),x,"n")] += 1
                gate[(w["gate"],x,"correct")] += p["prediction"] == p["gold"]
                gate[(w["gate"],x,"n")] += 1
        comparisons[tag] = {"triples":len(witnesses), "all_three_correct":all_three,
            "single_arm_count":sum(tally[(x,"correct")] for x in ("old_flip","new_flip")),
            "single_arm_n":2*len(witnesses),
            "anchor_correct":tally[("original","correct")],
            "anchor_n":len(witnesses),
            "by_stage": {"|".join(k):v for k,v in sorted(stage.items())},
            "by_gate": {"|".join(k):v for k,v in sorted(gate.items())},
            "frozen_training_overlap":0,
            "source_rows_sha256":sha(source)}
    result = {"status":"POSTHOC_SCORING_OF_PREFROZEN_COHORT",
        "pregradient_frozen_sha256":sha(source), "script_sha256":sha(SOURCE),
        "actual_optimizer_updates":read(RUN/"training-result.json")["actual_updates"],
        "witnesses":len(witnesses), "unseen_siblings":len(sibling_ids),
        "before":comparisons["before"], "after":comparisons["after"]}
    write(OUT,result)
    return {k:result[k] for k in ("status","actual_optimizer_updates","witnesses","unseen_siblings")} | {
        "before": {x:comparisons["before"][x] for x in ("all_three_correct","single_arm_count","anchor_correct")},
        "after": {x:comparisons["after"][x] for x in ("all_three_correct","single_arm_count","anchor_correct")}}


if __name__=="__main__":
    print(json.dumps(audit(),sort_keys=True))
