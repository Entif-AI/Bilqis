"""Leakage-resistant paired composition cells from existing admitted primitives."""
from __future__ import annotations
from collections import Counter, defaultdict
import random

from bilqis_development import data, kernel as k
from bilqis_teacher.grammar import exercises, old_expression, validate_spec
from bilqis_teacher.policy import validate_lesson
from bilqis_spiral.sampler import check_row
from bilqis_development.registry import SOURCES

# Every gate receives equally many true and false golds. Both arms matter
# across matched cells, and independent same-world NOT siblings prove influence.
QUOTAS = {
    "AND": {("TRUE", "TRUE"): 2, ("TRUE", "FALSE"): 1,
            ("FALSE", "TRUE"): 1, ("FALSE", "FALSE"): 0},
    "OR": {("TRUE", "TRUE"): 0, ("TRUE", "FALSE"): 1,
           ("FALSE", "TRUE"): 1, ("FALSE", "FALSE"): 2},
}
FAMILIES = {
    5: ("set-membership", "set-subset", "function-domain"),
    6: ("epistemic-proposition", "epistemic-observation", "provenance-ancestry"),
}
ARMS = ("direction", "quantifier", "entailment")


def accepted_specs():
    return [s for stage in (5, 6) for s in exercises(stage)
            if s["family"] in FAMILIES[stage]]


def _record(spec, gate, w, old_arm, new_arm, suffix=""):
    family = f'cross:U{1 + ARMS.index(spec["old_arm"])}+U{spec["stage"]}:{spec["family"]}' + suffix
    row = data.row(k.record(w, k.op(gate, old_arm, new_arm)), spec["stage"], family)
    row["source_locator"] = SOURCES[spec["source"]]
    row["teacher_spec_id"] = spec["id"]
    return validate_lesson(row)


def generate_split(specs, rng, excluded, *, multiplier=1, varied=False):
    buckets, witnesses = {str(s): [] for s in (5, 6)}, []
    for spec in specs:
        validate_spec(spec)
        cells = defaultdict(list)
        quotas = { (gate, truth): multiplier * count for gate, qs in QUOTAS.items()
                   for truth, count in qs.items() }
        attempts = 0
        while any(len(cells[key]) < need for key, need in quotas.items()):
            attempts += 1
            if attempts > 30000:
                missing = {str(k): q - len(cells[k]) for k, q in quotas.items()
                           if len(cells[k]) < q}
                raise ValueError(f'balanced family unrealizable {spec["id"]}: {missing}')
            try:
                w = data.make_world(spec["stage"], rng, varied)
                a, b = old_expression(w, spec["old_arm"], rng), data.query(spec["family"], w, rng)
                truth = (k.independent_evaluate(k.record(w, a)),
                         k.independent_evaluate(k.record(w, b)))
                if truth not in QUOTAS["AND"]: continue
                for gate in ("AND", "OR"):
                    key = (gate, truth)
                    if len(cells[key]) >= quotas[key]: continue
                    row = _record(spec, gate, w, a, b)
                    if row["id"] in excluded: continue
                    # Counterfactual witness for each operand, retained out of optimizer input.
                    siblings = [
                        _record(spec, gate, w, k.op("NOT", a), b, ":old-contrast"),
                        _record(spec, gate, w, a, k.op("NOT", b), ":new-contrast")]
                    siblings = [dict(r) for r in siblings]
                    if (len({row["id"], *(r["id"] for r in siblings)}) != 3 or
                            any(r["id"] in excluded for r in siblings)):
                        continue
                    # The AND TT and OR FF anchors must have both causal arms.
                    if (gate, truth) in (("AND", ("TRUE", "TRUE")),
                                         ("OR", ("FALSE", "FALSE"))):
                        if any(s["gold"] == row["gold"] for s in siblings): continue
                        witnesses.append({"base": row["id"], "stage": spec["stage"],
                                          "gate": gate, "truth": list(truth),
                                          "old": siblings[0], "new": siblings[1]})
                    cells[key].append(row)
                    excluded.update([row["id"], *(r["id"] for r in siblings)])
            except ValueError:
                continue
        buckets[str(spec["stage"])].extend(row for group in cells.values() for row in group)
    return buckets, witnesses


def _majority_baseline(rows, key):
    by_group = defaultdict(Counter)
    for row in rows:
        x = row["input"]["query"]
        gate = x["op"]
        w = row["input"]["world"]
        old, new = x["args"]
        old_val = k.independent_evaluate(k.record(w, old))
        new_val = k.independent_evaluate(k.record(w, new))
        if old_val not in ("TRUE", "FALSE") or new_val not in ("TRUE", "FALSE"):
            raise ValueError("cross arm unexpectedly nonBoolean")
        group = {"gate": (gate,), "old": (gate, old_val),
                 "new": (gate, new_val)}[key]
        by_group[group][row["gold"]] += 1
    return {"correct": sum(max(x.values()) for x in by_group.values()),
            "n": len(rows), "groups": len(by_group)}


def audit_cohort(buckets, witnesses, *, forbidden=()):
    rows = [r for group in buckets.values() for r in group]
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)) or set(ids) & set(forbidden):
        raise ValueError("cross cohort duplicates forbidden/frozen row")
    counts = Counter()
    for row in rows:
        check_row(row)
        query = row["input"]["query"]
        if query["op"] not in ("AND", "OR") or query["args"][0]["kind"] != "prior":
            raise ValueError("unsupported cross grammar shape")
        w = row["input"]["world"]
        old = k.independent_evaluate(k.record(w, query["args"][0]))
        new = k.independent_evaluate(k.record(w, query["args"][1]))
        counts[(row["stage"], row["teacher_spec_id"], query["op"], old, new, row["gold"])] += 1
    for spec in accepted_specs():
        for gate, quota in QUOTAS.items():
            by_spec = [r for r in rows if r["teacher_spec_id"] == spec["id"]
                       and r["input"]["query"]["op"] == gate]
            if not by_spec: raise ValueError("missing eligible grammar family")
            if len(set(r["gold"] for r in by_spec)) != 2:
                raise ValueError("operator-specific answer hint")
            table = Counter((k.independent_evaluate(k.record(r["input"]["world"],r["input"]["query"]["args"][0])),
                             k.independent_evaluate(k.record(r["input"]["world"],r["input"]["query"]["args"][1])))
                            for r in by_spec)
            multiplier = len(by_spec)//sum(quota.values())
            if len(by_spec) != multiplier * sum(quota.values()) or any(
                table[truth] != n * multiplier for truth, n in quota.items()):
                raise ValueError("gate x operand-truth balance violation")
    baselines = {name: _majority_baseline(rows, name) for name in ("gate", "old", "new")}
    if baselines["gate"]["correct"] * 2 != len(rows):
        raise ValueError("operator baseline not exactly chance")
    if any(baselines[x]["correct"] * 5 >= len(rows) * 4 for x in ("old", "new")):
        raise ValueError("one-arm shortcut exceeds 80 percent admission ceiling")
    anchor_ids = {r["id"] for r in rows}
    for witness in witnesses:
        if witness["base"] not in anchor_ids: raise ValueError("orphan witness")
        anchor = next(r for r in rows if r["id"] == witness["base"])
        gate, a, b = anchor["input"]["query"]["op"], *anchor["input"]["query"]["args"]
        for index, side in enumerate(("old", "new")):
            altered = witness[side]
            validate_lesson(altered)
            expected = k.op(gate, *[k.op("NOT", arg) if index == j else arg
                                     for j, arg in enumerate((a, b))])
            if altered["input"] != k.record(anchor["input"]["world"], expected) or altered["gold"] == anchor["gold"]:
                raise ValueError("inactive / unbound same-world contrast")
    return {"rows": len(rows), "witnesses": len(witnesses),
            "gate_arms_answer": {"|".join(map(str,k)): v for k,v in sorted(counts.items())},
            "baselines": baselines, "operator_only_accuracy": baselines["gate"]["correct"]/len(rows),
            "old_arm_only_accuracy": baselines["old"]["correct"]/len(rows),
            "new_arm_only_accuracy": baselines["new"]["correct"]/len(rows)}
