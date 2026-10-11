"""Exhaustive finite micro-worlds and composition-level split identities."""
import itertools
import json
from collections import Counter

from . import ROOT
from .semantics import ABI, LABELS, atom, combine, constant, digest, evaluate, negate, normalize, quantify, sid, variable, world_from_states

VERSION = "alpha-worlds-0.1.0"


def composition(q):
    op = q["op"].rsplit(":", 1)[-1].upper()
    if op in ("RELATION", "EQUAL"):
        return op
    children = [q["body"]] if "body" in q else q["args"]
    return op + "(" + ",".join(composition(a) for a in children) + ")"


def templates():
    ab, ba = atom("a", "b"), atom("b", "a")
    xb = atom(variable(), constant("b"))
    xa, ax = atom(variable(), constant("a")), atom(constant("a"), variable())
    seen = [atom(a, b) for a, b in itertools.product(("a", "b"), repeat=2)]
    seen += [negate(q) for q in list(seen)]
    seen += [combine("and", ab, ba), combine("or", atom("a", "a"), atom("b", "b")),
             atom("a", "a", "equal"), atom("a", "b", "equal"),
             quantify("exists", xb), quantify("forall", xb),
             negate(quantify("exists", xb)), quantify("exists", negate(xb))]
    unseen = [negate(combine("and", ab, ba)), combine("and", ab, negate(ba)),
              quantify("exists", combine("and", xa, ax)), combine("or", ab, negate(ba))]
    return seen, unseen


def known_cases():
    return json.loads((ROOT / "fixtures/alpha/known-pass.json").read_text())["cases"]


def audit_cases(cases):
    seen = set()
    for row in cases:
        if row["id"] in seen:
            raise ValueError("duplicate case identity: " + row["id"])
        seen.add(row["id"])
        actual = evaluate(row["semantic"])
        if row["expected"] not in LABELS or actual != row["expected"]:
            raise ValueError(f"oracle/expected mismatch: {row['id']} expected={row['expected']} actual={actual}")


def build_corpus():
    seen, unseen = templates()
    rows = {}
    for states in itertools.product(range(4), repeat=4):
        w = world_from_states(states)
        ordinary = "DEV" if int(digest(w)[:8], 16) % 4 == 0 else "TRAIN"
        for split, queries in ((ordinary, seen), ("HELDOUT", unseen)):
            for q in queries:
                s = normalize({"abi": ABI, "world": w, "query": q})
                identity = digest(s)
                rows[identity] = {"id": "A-" + identity[:20], "split": split,
                                  "pattern": composition(s["query"]), "semantic": s,
                                  "expected": evaluate(s)}
    cases = [rows[k] for k in sorted(rows)]
    split_manifest = {"version": VERSION, "oracle_version": "belnap-finite-0.1.0",
                      "policy": "world-hash DEV for seen patterns; entire unseen AST patterns withheld",
                      "sealed": False, "corpus_sha256": digest(cases), "splits": {}}
    for split in ("TRAIN", "DEV", "HELDOUT"):
        subset = [r for r in cases if r["split"] == split]
        split_manifest["splits"][split] = {"ids": [r["id"] for r in subset],
            "patterns": sorted({r["pattern"] for r in subset}),
            "labels": dict(sorted(Counter(r["expected"] for r in subset).items())),
            "semantic_sha256": digest([r["semantic"] for r in subset])}
    return {"cases": cases, "split_manifest": split_manifest}


def frozen_corpus():
    corpus = build_corpus()
    expected = json.loads((ROOT / "fixtures/alpha/split-manifest.json").read_text())
    if corpus["split_manifest"] != expected:
        raise ValueError("frozen corpus drift; declare a new evidence epoch")
    audit_cases(known_cases())
    audit_cases(corpus["cases"])
    return corpus
