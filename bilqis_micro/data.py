"""Deterministic tiny worlds, compositions, perturbations and cumulative rehearsal.

Evaluation is an exploratory development readout, not a sealed benchmark. Varied
worlds use 4-5 entities; training uses 2-4. Composite readouts add a query nesting
absent from the new family's training. Exact evaluation inputs never enter train.
"""
from __future__ import annotations

from collections import Counter
import copy
import random

from bilqis_logic import kernel as boolean
from bilqis_logic.data import build_data as boolean_data
from .graph import RULE, STATES, TOKENS
from .kernel import (world, entity, bound, relation, logic, compare, quantify, compose, entails,
                     rule_step, countermodel, observe, evidence_logic, record, evaluate, independent_evaluate, encode, decode)

VERSION = "micro-lessons-0.1.0"
NAMES = ["Boolean refresh", "entities and roles", "quantification and composition", "inference and proof", "evidence and interpretations"]


def row(r, stage, family):
    answer = evaluate(r)
    if answer != independent_evaluate(r):
        raise ValueError("independent finite-world oracles disagree")
    return {"id": boolean.digest(r), "input": r, "gold": answer, "stage": stage, "family": family}


def unique(rows):
    return list({r["id"]: r for r in rows}.values())


def _boolean(rng, depth):
    if depth == 0:
        return boolean.literal(bool(rng.randrange(2)))
    op = rng.choice(list(boolean.OPERATORS))
    return boolean.apply(op, *(_boolean(rng, depth - 1 if rng.random() < .75 else 0) for _ in range(boolean.OPERATORS[op])))


def lesson(stage, rng, category="focus", varied=False):
    if stage == 0:
        depth = (3 if varied else 4) if category == "held_composite" else 2 if category == "composition" or varied else 1
        r = boolean.evaluation_record(_boolean(rng, depth), {})
        return row(r, 0, "Boolean:" + category)
    n = rng.choice((4, 5) if varied else (2, 3, 4) if stage == 1 else (3, 4))
    names = rng.sample(list("ABCDE"), n)
    a, b, c = names[0], names[1], names[2] if n > 2 else names[0]
    A, B, C = map(entity, (a, b, c))
    positive = bool(rng.randrange(2))
    facts = [("PARENT", a, b), ("PARENT", b, c) if positive else ("PARENT", c, b)]
    if rng.random() < .5:
        facts.append(("LINK", a, b))
    if n > 3 and rng.random() < .6:
        facts.append(("PARENT", names[3], rng.choice(names)))
    facts = sorted(set(facts))
    w = world(names, facts)
    two_hop = quantify("EXISTS", logic("AND", relation("PARENT", A, bound(0)), relation("PARENT", bound(0), C)))
    if stage == 1:
        k = rng.randrange(6)
        if k == 0:
            q, family = relation("PARENT", A if positive else B, B if positive else A), "direction"
        elif k == 1:
            q, family = relation("CHILD", B if positive else A, A if positive else B), "inverse"
        elif k == 2:
            q, family = relation("PARENT", A, C), "no_parent_transitivity"
        elif k == 3:
            q, family = relation("LINK", B, A), "symmetric_link"
        elif k == 4:
            q, family = compare("EQ", A, A if positive else B), "identity"
        else:
            q, family = relation("PARENT", B, C), "edge_presence"
    elif stage == 2:
        k = rng.randrange(7)
        if k == 0:
            q, family = two_hop, "bound_two_hop"
        elif k == 1:
            q, family = compose("PARENT", "PARENT", A, C), "relational_composition"
        elif k == 2:
            q, family = quantify("EXISTS", logic("AND", compare("NEQ", bound(0), A), relation("PARENT", bound(0), C))), "exists_distinct_parent"
        elif k == 3:
            star = [("PARENT", a, x) for x in names if x != a]
            w = world(names, star if positive else star[:-1])
            q = quantify("FORALL", logic("IMPLIES", compare("NEQ", bound(0), A), relation("PARENT", A, bound(0))))
            family = "forall_counterexample"
        elif k == 4:
            q, family = quantify("FORALL", quantify("EXISTS", compare("EQ", bound(1), bound(0)))), "nested_binding_witness"
        elif k == 5:
            q, family = quantify("EXISTS", quantify("FORALL", compare("EQ", bound(1), bound(0)))), "nested_binding_counterexample"
        else:
            q, family = quantify(rng.choice(("EXISTS", "FORALL")), relation("CHILD", bound(0), A if positive else C)), "inverse_quantification"
    elif stage == 3:
        w = world(names, facts, rules=[RULE] if rng.random() < .8 else [])
        conclusion = relation("GRANDPARENT", A, C)
        p, q2 = relation("PARENT", A, B), relation("PARENT", B, C)
        k = rng.randrange(6)
        if k == 0:
            q, family = entails(conclusion if positive else relation("GRANDPARENT", C, A)), "derived_entailment"
        elif k == 1:
            q, family = rule_step([p, q2] if positive else [q2, p], conclusion), "rule_application"
        elif k == 2:
            q, family = countermodel([p, q2], relation("PARENT", A, C) if positive else conclusion), "candidate_countermodel"
        elif k == 3:
            q, family = entails(quantify("EXISTS", relation("GRANDPARENT", A if positive else C, bound(0)))), "quantified_derivation"
        elif k == 4:
            q, family = logic("IMPLIES", two_hop, entails(conclusion)), "rule_implication"
        else:
            w = world(names, facts, rules=[RULE] if positive else [])
            q, family = entails(conclusion), "declared_rule_presence"
    else:
        w = world(names, facts, rules=[RULE])
        props = {"J0": entails(relation("GRANDPARENT", A, C)), "J1": relation("CHILD", B, A)}
        state = rng.randrange(5)
        live = [0, 1] if state == 4 else [0]
        reports = []
        source = rng.choice(("S0", "S1", "S2"))
        if state in (1, 3, 4):
            reports.append((source, "J0", "support", 0))
        if state in (2, 3):
            reports.append((rng.choice(("S0", "S1", "S2")), "J0", "refute", 0))
        if state == 4 and rng.random() < .5:
            reports.append((source, "J0", "refute", 1))
        if rng.random() < .5:
            reports.append((source, "J1", rng.choice(("support", "refute")), 0))
        w = world(names, facts, rules=[RULE], propositions=props, reports=sorted(set(reports)), live=live)
        q, family = observe("J0"), "evidence_state"
    if category in ("composition", "held_composite"):
        if stage == 4:
            q = evidence_logic(rng.choice(("AND", "OR")), q, rng.choice([observe("J1"), relation("CHILD", B, A), entails(relation("GRANDPARENT", A, C))]))
            if rng.random() < .5:
                q = evidence_logic("NOT", q)
            if category == "held_composite":
                q = evidence_logic("OR", evidence_logic("NOT", q), observe("J0"))
        else:
            earlier = rng.choice([relation("CHILD", B, A), compare("EQ", A, B), boolean.literal(positive)])
            q = logic(rng.choice(("AND", "XOR", "IMPLIES", "OR")), q, earlier)
            if rng.random() < .3:
                q = logic("NOT", q)
            if category == "held_composite":
                q = logic("XOR", logic("NOT", q), logic("IMPLIES", relation("PARENT", A, B), compare("EQ", A, C)))
        family += ":" + category
    return row(record(w, q), stage, family)


def perturb(original):
    """Try one edge/rule/report change; keep only a demonstrated gold-changing pair."""
    r = copy.deepcopy(original["input"])
    stage = original["stage"]
    candidates = []
    if stage == 0:
        def flips(e, path=()):
            if e["kind"] == "literal":
                return [path]
            return [p for i, a in enumerate(e["args"]) for p in flips(a, path + (i,))]
        for path in flips(r["expression"]):
            candidate = copy.deepcopy(r)
            leaf = candidate["expression"]
            for i in path:
                leaf = leaf["args"][i]
            leaf["value"] = not leaf["value"]
            candidates.append((candidate, "one Boolean literal"))
    else:
        for i in range(len(r["world"]["facts"])):
            candidate = copy.deepcopy(r)
            candidate["world"]["facts"].pop(i)
            candidates.append((candidate, "one asserted edge removed"))
        if r["world"]["rules"]:
            candidate = copy.deepcopy(r)
            candidate["world"]["rules"] = []
            candidates.append((candidate, "one declared rule removed"))
        if stage == 4:
            for report in [("S2", "J0", polarity, 0) for polarity in ("support", "refute")]:
                if list(report) not in r["world"]["reports"]:
                    candidate = copy.deepcopy(r)
                    candidate["world"]["reports"].append(list(report))
                    candidate["world"]["reports"].sort()
                    candidates.append((candidate, "one explicit report added"))
    for candidate, factor in candidates:
        changed = row(candidate, stage, original["family"] + ":contrast")
        if changed["gold"] != original["gold"]:
            return changed, factor
    return None


def build_data():
    stages, pairs = {}, {}
    legacy = boolean_data()
    for stage in range(5):
        rng = random.Random(10800 + stage)
        focus = unique([lesson(stage, rng) for _ in range(640)])
        compositions = unique([lesson(stage, rng, "composition") for _ in range(640)])
        if stage == 0:
            focus = unique(focus + [row(r["input"], 0, r["family"]) for r in legacy["TRAIN_A"]])
            compositions = unique(compositions + [row(r["input"], 0, r["family"]) for split in ("TRAIN_B_COMPOSITION", "TRAIN_B_EQUIVALENCE") for r in legacy[split]])
        contrasts, stage_pairs = [], []
        for original in focus + compositions:
            result = perturb(original)
            if result is not None:
                changed, factor = result
                contrasts += [original, changed]
                stage_pairs.append({"before": original["id"], "after": changed["id"], "factor": factor})
            if len(stage_pairs) >= 128:
                break
        stages[str(stage)] = {"name": NAMES[stage], "train": {"focus": focus, "composition": compositions, "contrast": unique(contrasts)}, "eval": {}}
        pairs[str(stage)] = stage_pairs
    all_train = {r["id"] for s in stages.values() for pool in s["train"].values() for r in pool}
    prior_eval = set()
    for stage in range(5):
        s = stages[str(stage)]
        s["eval"]["familiar"] = unique(s["train"]["focus"] + s["train"]["composition"])[:128]
        for split, category in (("varied", "focus"), ("composite", "held_composite")):
            rng = random.Random(20800 + 100 * stage + (split == "composite"))
            rows = unique([lesson(stage, rng, category, varied=True) for _ in range(400)])
            rows = [r for r in rows if r["id"] not in all_train | prior_eval][:128]
            s["eval"][split] = rows
            prior_eval.update(r["id"] for r in rows)
    return {"version": VERSION, "stages": stages, "contrast_pairs": pairs,
            "policy": "exploratory; familiar overlaps train; varied/composite exact inputs excluded from all training; no seal or attribution controls"}


def audit_data(data):
    if data["version"] != VERSION or set(data["stages"]) != {str(i) for i in range(5)}:
        raise ValueError("developmental stage contract")
    all_train = {r["id"] for s in data["stages"].values() for pool in s["train"].values() for r in pool}
    manifest, max_tokens = {}, 0
    for index, s in data["stages"].items():
        stage = int(index)
        manifest[index] = {"name": s["name"], "pools": {}, "tokens_exposed": []}
        tokens = set()
        for category in ("train", "eval"):
            for split, rows in s[category].items():
                if not rows or len({r["id"] for r in rows}) != len(rows):
                    raise ValueError("empty/duplicate lesson pool")
                for r in rows:
                    ids = encode(r["input"])
                    if (r["id"] != boolean.digest(r["input"]) or r["stage"] != stage or r["gold"] != evaluate(r["input"])
                            or r["gold"] != independent_evaluate(r["input"]) or decode(ids) != r["input"]):
                        raise ValueError("lesson identity, type, gold or codec binding")
                    if category == "eval" and split != "familiar" and r["id"] in all_train:
                        raise ValueError("evaluation input in training")
                    max_tokens = max(max_tokens, len(ids))
                    if category == "train":
                        tokens.update(ids)
                manifest[index]["pools"][category + ":" + split] = {"rows": len(rows), "labels": dict(Counter(r["gold"] for r in rows)), "sha256": boolean.digest(rows)}
        manifest[index]["tokens_exposed"] = [TOKENS[i] for i in sorted(tokens)]
        by_id = {r["id"]: r for pool in s["train"].values() for r in pool}
        for pair in data["contrast_pairs"][index]:
            if by_id[pair["before"]]["gold"] == by_id[pair["after"]]["gold"]:
                raise ValueError("contrast must change the formal answer")
    return {"version": VERSION, "stages": manifest, "max_input_tokens": max_tokens, "data_sha256": boolean.digest(data)}
