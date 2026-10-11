"""Small authored algebra lessons and structurally isolated evaluation families."""
from __future__ import annotations

import itertools

from .kernel import (OPERATORS, assignments, apply, canonical, digest, encode,
                     equivalence_record, evaluation_record, gold, literal, variable)

VERSION = "cogal-pilot-data-0.1.0"
SYMMETRIC = {"AND", "OR", "XOR", "XNOR", "IFF"}


def structure(expr):
    """Operator tree ignoring values/names; commutative children are unordered."""
    if expr["kind"] != "apply":
        return "Boolean"
    children = [structure(a) for a in expr["args"]]
    if expr["operator"] in SYMMETRIC:
        children.sort(key=canonical)
    return [expr["operator"], children]


def expressions(record):
    return [record["expression"]] if record["task"] == "evaluate" else [record["left"], record["right"]]


def row(record, family):
    answer = gold(record)
    if answer != gold(record, independent=True):
        raise ValueError("independent oracle disagreement")
    return {"id": digest(record), "input": record, "gold": answer, "family": family}


def unique(rows):
    by_id = {}
    for r in rows:
        if r["id"] in by_id and by_id[r["id"]]["gold"] != r["gold"]:
            raise ValueError("conflicting labels")
        by_id.setdefault(r["id"], r)
    return [by_id[k] for k in sorted(by_id)]


def eval_rows(exprs, family):
    return unique([row(evaluation_record(e, env), family) for e in exprs for env in assignments((e,))])


def build_data():
    p, q, t, f = variable("P"), variable("Q"), literal(True), literal(False)
    n = lambda e: apply("NOT", e)
    b = lambda op, a, c: apply(op, a, c)
    data = {"TRAIN_A": unique([
        row(evaluation_record(apply(op, *map(literal, values)), {}), "primitive:" + op)
        for op, arity in OPERATORS.items() for values in itertools.product((True, False), repeat=arity)])}

    positives = [
        ("double_negation", n(n(p)), p),
        ("and_identity", b("AND", p, t), p),
        ("and_annihilator", b("AND", p, f), f),
        ("or_identity", b("OR", p, f), p),
        ("or_annihilator", b("OR", p, t), t),
        ("xor_identity", b("XOR", p, f), p),
        ("xor_complement", b("XOR", p, t), n(p)),
        ("iff_identity", b("IFF", p, t), p),
        ("iff_complement", b("IFF", p, f), n(p)),
        ("xnor_iff", b("XNOR", p, q), b("IFF", p, q)),
        *[("commutativity:" + op, b(op, p, q), b(op, q, p)) for op in sorted(SYMMETRIC)],
        ("de_morgan_and", n(b("AND", p, q)), b("OR", n(p), n(q))),
        ("de_morgan_or", n(b("OR", p, q)), b("AND", n(p), n(q))),
        ("implication_rewrite", b("IMPLIES", p, q), b("OR", n(p), q)),
        ("xor_iff_complement", b("XOR", p, q), n(b("IFF", p, q))),
        ("iff_xor_complement", b("IFF", p, q), n(b("XOR", p, q))),
    ]
    negatives = [
        ("double_negation_negative", n(n(p)), n(p)),
        ("and_identity_negative", b("AND", p, t), n(p)),
        ("and_annihilator_negative", b("AND", p, f), p),
        ("or_identity_negative", b("OR", p, f), f),
        ("or_annihilator_negative", b("OR", p, t), p),
        ("xor_identity_negative", b("XOR", p, f), n(p)),
        ("xor_complement_negative", b("XOR", p, t), p),
        ("iff_identity_negative", b("IFF", p, t), n(p)),
        ("iff_complement_negative", b("IFF", p, f), p),
        ("xnor_xor_negative", b("XNOR", p, q), b("XOR", p, q)),
        ("and_or_negative", b("AND", p, q), b("OR", q, p)),
        ("or_xor_negative", b("OR", p, q), b("XOR", q, p)),
        ("xor_and_negative", b("XOR", p, q), b("AND", q, p)),
        ("xnor_implies_negative", b("XNOR", p, q), b("IMPLIES", q, p)),
        ("iff_or_negative", b("IFF", p, q), b("OR", q, p)),
        ("de_morgan_and_negative", n(b("AND", p, q)), b("AND", n(p), n(q))),
        ("de_morgan_or_negative", n(b("OR", p, q)), b("OR", n(p), n(q))),
        ("implication_rewrite_negative", b("IMPLIES", p, q), b("AND", n(p), q)),
        ("xor_iff_negative", b("XOR", p, q), b("IFF", p, q)),
        ("iff_xor_negative", b("IFF", p, q), b("XOR", p, q)),
    ]
    for expected, lessons in ((True, positives), (False, negatives)):
        if any(gold(equivalence_record(left, right)) != expected for _, left, right in lessons):
            raise ValueError("authored algebra lesson disagrees with formal oracle")
    data["TRAIN_B_EQUIVALENCE"] = unique([
        row(equivalence_record(left, right), name) for name, left, right in positives + negatives])
    train_exprs = [e for _, left, right in positives + negatives for e in (left, right)]
    train_exprs += [p, q, n(p), n(q)] + [b(op, p, q) for op, arity in OPERATORS.items() if arity == 2]
    data["TRAIN_B_COMPOSITION"] = eval_rows(train_exprs, "short_algebra")

    binary = [op for op, arity in OPERATORS.items() if arity == 2]
    # Unfamiliar structural families are fixed before any model exists. No scores select them.
    dev = [n(b(op, n(p), q)) for op in binary]
    data["DEV"] = eval_rows(dev, "dev_nested_negation")
    heldout = [b(root, b(child, p, q), n(p)) for root in binary for child in binary]
    heldout += [b(root, b(child, p, q), n(b("IMPLIES", q, p)))
                for root in binary for child in ("XOR", "AND")]
    data["HELDOUT_COMPOSITION"] = eval_rows(heldout, "unseen_operator_nesting")

    held_pos, held_neg = [], []
    for a_op, c_op in itertools.product(binary, repeat=2):
        a, c = b(a_op, p, q), b(c_op, q, p)
        candidates = [
            ("compound_de_morgan", n(b("AND", a, c)), b("OR", n(a), n(c)), b("AND", n(a), n(c))),
            ("compound_implication", b("IMPLIES", a, c), b("OR", n(a), c), b("AND", n(a), c)),
            ("compound_xor_iff", b("XOR", a, c), n(b("IFF", a, c)), b("IFF", a, c)),
        ]
        for name, left, right, wrong in candidates:
            good = row(equivalence_record(left, right), name)
            bad = row(equivalence_record(left, wrong), name + "_negative")
            # Remove formally equivalent purported negatives before freeze, never using neural scores.
            if good["gold"] and not bad["gold"]:
                held_pos.append(good)
                held_neg.append(bad)
    # Fixed bounded count and deterministic ordering; balanced by independently graded gold.
    data["HELDOUT_EQUIVALENCE"] = unique(unique(held_pos)[:32] + unique(held_neg)[:32])
    data["HARD_NEGATIVES"] = [row(equivalence_record(b("IMPLIES", p, q), b("IMPLIES", q, p)),
                                   "implication_direction_counterexample")]
    audit_splits(data)
    return data


def audit_splits(data):
    train = [r for split in ("TRAIN_A", "TRAIN_B_COMPOSITION", "TRAIN_B_EQUIVALENCE") for r in data[split]]
    train_ids = {r["id"] for r in train}
    train_structures = {digest(structure(e)) for r in train for e in expressions(r["input"])}
    evaluation_structures = {}
    manifest = {}
    all_eval_ids = set()
    for split, rows in data.items():
        if len({r["id"] for r in rows}) != len(rows):
            raise ValueError("duplicate split rows")
        signatures = {digest(structure(e)) for r in rows for e in expressions(r["input"])}
        for r in rows:
            if (r["id"] != digest(r["input"]) or r["gold"] != gold(r["input"])
                    or r["gold"] != gold(r["input"], independent=True)):
                raise ValueError("dataset input/gold integrity")
        if not split.startswith("TRAIN"):
            ids = {r["id"] for r in rows}
            if ids & (train_ids | all_eval_ids):
                raise ValueError("exact evaluation input leaked")
            all_eval_ids |= ids
            if split != "HARD_NEGATIVES":
                if signatures & train_structures:
                    raise ValueError("evaluation tree structure leaked into training")
                evaluation_structures[split] = signatures
        manifest[split] = {"rows": len(rows), "true": sum(r["gold"] for r in rows),
                           "false": sum(not r["gold"] for r in rows), "structures": len(signatures),
                           "sha256": digest(rows), "max_input_tokens": max(map(lambda r: len(encode(r["input"])), rows))}
    if evaluation_structures["DEV"] & (evaluation_structures["HELDOUT_COMPOSITION"] | evaluation_structures["HELDOUT_EQUIVALENCE"]):
        raise ValueError("DEV/HELDOUT structure overlap")
    for split in ("TRAIN_B_EQUIVALENCE", "HELDOUT_EQUIVALENCE"):
        if manifest[split]["true"] != manifest[split]["false"]:
            raise ValueError("equivalence balance")
    return manifest
