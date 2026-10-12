"""Typed finite relations with explicitly local Belnap-Dunn truth semantics.

Support/refutation are independent evidence sets. Absence is UNKNOWN, never
closed-world FALSE. Quantifiers range over the declared nonempty domain.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from . import ROOT

ABI = "bilqis-alpha-cogal-0.1.0"
ORACLE_VERSION = "belnap-finite-0.1.0"
LABELS = ("TRUE", "FALSE", "UNKNOWN", "CONFLICT")
BITS = ((1, 0), (0, 1), (0, 0), (1, 1))


def sid(name: str) -> str:
    return "urn:bilqis:alpha:cogal:" + name


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode()


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def registry() -> dict:
    return json.loads((ROOT / "fixtures/alpha/semantic-registry.json").read_text())


class SemanticError(ValueError):
    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SemanticError("ILLEGAL_COMPOSITION", detail)


def constant(name: str) -> dict:
    return {"kind": "constant", "id": sid(name)}


def variable(name: str = "x") -> dict:
    return {"kind": "variable", "id": sid(name)}


def atom(source: str | dict, target: str | dict, op: str = "relation") -> dict:
    return {"op": sid(op), "args": [constant(source) if isinstance(source, str) else source,
                                    constant(target) if isinstance(target, str) else target]}


def negate(q: dict) -> dict:
    return {"op": sid("not"), "args": [q]}


def combine(op: str, left: dict, right: dict) -> dict:
    return {"op": sid(op), "args": [left, right]}


def quantify(op: str, body: dict) -> dict:
    return {"op": sid(op), "variable": sid("x"), "body": body}


def world_from_states(states: list | tuple) -> dict:
    require(len(states) == 4 and all(type(i) is int and 0 <= i < 4 for i in states), "four relation states")
    facts = []
    for (a, b), state in zip((("a", "a"), ("a", "b"), ("b", "a"), ("b", "b")), states):
        for bit, polarity in zip(BITS[state], ("support", "refute")):
            if bit:
                facts.append({"predicate": sid("relation"),
                              "roles": {"source": sid(a), "target": sid(b)},
                              "polarity": sid(polarity),
                              "source": sid("source-0" if polarity == "support" else "source-1")})
    return {"entities": [sid("a"), sid("b")],
            "sources": [sid("source-0"), sid("source-1")],
            "facts": sorted(facts, key=canonical)}


def normalize(semantic: dict) -> dict:
    require(isinstance(semantic, dict) and set(semantic) == {"abi", "world", "query"}, "semantic fields")
    require(semantic["abi"] == ABI, "semantic ABI")
    w = semantic["world"]
    operators = {r["id"]: r for r in registry()["entries"] if r["type"] in ("operator", "predicate")}
    require(isinstance(w, dict) and set(w) == {"entities", "sources", "facts"}, "world fields")
    require(w["entities"] == [sid("a"), sid("b")], "alpha domain is exactly {a,b}; empty domains unsupported")
    require(w["sources"] == [sid("source-0"), sid("source-1")], "declared evidence sources")
    require(isinstance(w["facts"], list), "facts list")
    seen = set()
    for f in w["facts"]:
        require(isinstance(f, dict) and set(f) == {"predicate", "roles", "polarity", "source"}, "fact fields")
        require(f["predicate"] == sid("relation"), "binary relation predicate")
        roles = f["roles"]
        require(isinstance(roles, dict) and set(roles) == {"source", "target"}, "directed argument roles")
        require(all(v in w["entities"] for v in roles.values()), "fact entity references")
        require(f["polarity"] in (sid("support"), sid("refute")), "evidence polarity")
        require(f["source"] in w["sources"], "evidence provenance")
        key = canonical(f)
        require(key not in seen, "duplicate evidence record")
        seen.add(key)

    def term(t, bound):
        require(isinstance(t, dict) and set(t) == {"kind", "id"}, "typed term")
        if t["kind"] == "constant":
            require(t["id"] in w["entities"], "constant domain")
        elif t["kind"] == "variable":
            require(t["id"] in bound, "free variable")
        else:
            raise SemanticError("ILLEGAL_COMPOSITION", "term kind")
        return dict(t)

    def query(q, bound=frozenset(), depth=0):
        require(isinstance(q, dict) and depth <= 4, "query type/depth")
        op = q.get("op")
        if op not in operators:
            raise SemanticError("UNSUPPORTED_CONSTRUCT", str(op))
        if op in (sid("exists"), sid("forall")):
            require(set(q) == {"op", "variable", "body"}, "binder fields")
            require(q["variable"] == sid("x") and sid("x") not in bound, "alpha binder/shadowing")
            return {"op": op, "variable": sid("x"),
                    "body": query(q["body"], bound | {sid("x")}, depth + 1)}
        require(set(q) == {"op", "args"} and isinstance(q["args"], list), "operator fields")
        require(len(q["args"]) == operators[op]["arity"], "operator arity")
        if op in (sid("relation"), sid("equal")):
            args = [term(t, bound) for t in q["args"]]
        else:
            args = [query(a, bound, depth + 1) for a in q["args"]]
        if op in (sid("and"), sid("or"), sid("equal")):
            args.sort(key=canonical)
        return {"op": op, "args": args}

    result = {"abi": ABI, "world": {"entities": list(w["entities"]),
              "sources": list(w["sources"]), "facts": sorted(w["facts"], key=canonical)},
              "query": query(semantic["query"])}
    # Return a detached canonical object: callers cannot mutate registry/world state.
    return json.loads(canonical(result))


def evaluate(semantic: dict) -> str:
    s = normalize(semantic)
    w = s["world"]

    def value(term, env):
        return term["id"] if term["kind"] == "constant" else env[term["id"]]

    def fold(op, a, b):
        return (a[0] & b[0], a[1] | b[1]) if op == sid("and") else (a[0] | b[0], a[1] & b[1])

    def visit(q, env):
        op = q["op"]
        if op == sid("relation"):
            a, b = [value(t, env) for t in q["args"]]
            evidence = {f["polarity"] for f in w["facts"]
                        if f["roles"] == {"source": a, "target": b}}
            return int(sid("support") in evidence), int(sid("refute") in evidence)
        if op == sid("equal"):
            a, b = [value(t, env) for t in q["args"]]
            return (1, 0) if a == b else (0, 1)
        if op == sid("not"):
            t, f = visit(q["args"][0], env)
            return f, t
        if op in (sid("and"), sid("or")):
            return fold(op, *[visit(a, env) for a in q["args"]])
        if op in (sid("exists"), sid("forall")):
            states = [visit(q["body"], dict(env, **{q["variable"]: a})) for a in w["entities"]]
            return fold(sid("or" if op == sid("exists") else "and"), *states)
        raise SemanticError("UNSUPPORTED_CONSTRUCT", op)

    return LABELS[BITS.index(visit(s["query"], {}))]
