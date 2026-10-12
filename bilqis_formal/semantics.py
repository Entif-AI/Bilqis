"""Tiny classical Boolean algebra with first-class rule identities and schema matching.

This is a new semantic space. It does not borrow numeric token IDs, weights, or
models from the earlier T0/T1 or U0-U7 experimental lineages. There are no worlds.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import hashlib
import json


VERSION = "bilqis.formal.f0/v0.1.0"
ATOMS = ("FALSE", "TRUE", "P", "Q", "R")
METAS = ("$A", "$B", "$C")
ARITY = {"NOT": 1, "AND": 2, "OR": 2, "IMPLIES": 2}


def app(op, *args):
    value = (op, *args)
    validate(value)
    return value


def validate(expr, *, meta=False, depth=0):
    if depth > 12:
        raise ValueError("FORMULA_DEPTH")
    if isinstance(expr, str):
        if expr in ATOMS or (meta and expr in METAS):
            return
        raise ValueError("FORMULA_ATOM")
    if (not isinstance(expr, (tuple, list)) or not expr or not isinstance(expr[0], str)
            or expr[0] not in ARITY or len(expr) != ARITY[expr[0]] + 1):
        raise ValueError("FORMULA_ARITY")
    for child in expr[1:]:
        validate(child, meta=meta, depth=depth + 1)


def variables(expr):
    validate(expr)
    if isinstance(expr, str):
        return {expr} if expr in ("P", "Q", "R") else set()
    return set().union(*(variables(v) for v in expr[1:]))


def evaluate(expr, env):
    validate(expr)
    if set(env) != variables(expr) or any(type(v) is not bool for v in env.values()):
        raise ValueError("EXACT_VALUATION_REQUIRED")

    def visit(e):
        if isinstance(e, str):
            return (e == "TRUE") if e in ("TRUE", "FALSE") else env[e]
        values = [visit(v) for v in e[1:]]
        if e[0] == "NOT":
            return not values[0]
        a, b = values
        return {"AND": a and b, "OR": a or b, "IMPLIES": (not a) or b}[e[0]]

    return visit(expr)


def equivalent(a, b):
    names = sorted(variables(a) | variables(b))
    for vals in product((False, True), repeat=len(names)):
        env = dict(zip(names, vals))
        if evaluate(a, {n: env[n] for n in variables(a)}) != evaluate(b, {n: env[n] for n in variables(b)}):
            return False
    return True


@dataclass(frozen=True)
class Law:
    semantic_id: str
    source: object
    target: object
    prerequisites: tuple[str, ...]
    origin: str = "classical-boolean-algebra"


LAWS = {
    x.semantic_id: x for x in (
        Law("LAW.NOT.INVOLUTION", ("NOT", ("NOT", "$A")), "$A", ("OP.NOT",)),
        Law("LAW.AND.IDENTITY.RIGHT", ("AND", "$A", "TRUE"), "$A", ("OP.AND",)),
        Law("LAW.AND.IDENTITY.LEFT", ("AND", "TRUE", "$A"), "$A", ("OP.AND",)),
        Law("LAW.AND.ANNIHILATOR.RIGHT", ("AND", "$A", "FALSE"), "FALSE", ("OP.AND",)),
        Law("LAW.AND.ANNIHILATOR.LEFT", ("AND", "FALSE", "$A"), "FALSE", ("OP.AND",)),
        Law("LAW.AND.ASSOCIATIVITY", ("AND", ("AND", "$A", "$B"), "$C"),
            ("AND", "$A", ("AND", "$B", "$C")), ("OP.AND",)),
        Law("LAW.OR.IDENTITY.RIGHT", ("OR", "$A", "FALSE"), "$A", ("OP.OR",)),
        Law("LAW.OR.ANNIHILATOR.RIGHT", ("OR", "$A", "TRUE"), "TRUE", ("OP.OR",)),
        Law("LAW.IMPLIES.DEFINITION", ("IMPLIES", "$A", "$B"), ("OR", ("NOT", "$A"), "$B"),
            ("OP.IMPLIES", "OP.NOT", "OP.OR")),
    )
}

# Stable semantic IDs, never derived from English labels or candidate position.
# The ABI reserves later operators and laws, but stage gates control exposure.
TOKENS = (
    "SYNTAX.PAD", "TASK.EVALUATE", "TASK.LAW_APPLIES", "SYNTAX.SEP", "SYNTAX.END",
    "SYNTAX.PATH_ROOT", "SYNTAX.PATH_0", "SYNTAX.PATH_1", "SYNTAX.BIND",
    *("ATOM." + x for x in ATOMS), *("OP." + x for x in ARITY), *LAWS,
    "META.SCHEMA_VARIABLE", "META.UNIFORM_SUBSTITUTION",
)
TOKEN_ID = {name: i for i, name in enumerate(TOKENS)}


def match(pattern, expr, bindings=None):
    """Uniformly match formula metavariables against entire well-formed ASTs."""
    validate(pattern, meta=True)
    validate(expr)
    bindings = {} if bindings is None else dict(bindings)

    def rec(p, e):
        if isinstance(p, str) and p in METAS:
            if p in bindings:
                return bindings[p] == e
            bindings[p] = e
            return True
        return (p == e if isinstance(p, str) else
                isinstance(e, (list, tuple)) and len(p) == len(e) and p[0] == e[0]
                and all(rec(a, b) for a, b in zip(p[1:], e[1:])))

    return bindings if rec(pattern, expr) else None


def instantiate(pattern, bindings):
    validate(pattern, meta=True)
    if isinstance(pattern, str):
        if pattern in METAS:
            if pattern not in bindings:
                raise ValueError("UNBOUND_METAVARIABLE")
            validate(bindings[pattern])
            return bindings[pattern]
        return pattern
    return (pattern[0], *(instantiate(v, bindings) for v in pattern[1:]))


def at_path(expr, path):
    validate(expr)
    for index in path:
        if not isinstance(index, int) or isinstance(expr, str) or index < 0 or index >= ARITY[expr[0]]:
            raise ValueError("INVALID_PATH")
        expr = expr[index + 1]
    return expr


def replace_at(expr, path, new):
    validate(expr)
    validate(new)
    if not path:
        return new
    index = path[0]
    if not isinstance(index, int) or isinstance(expr, str) or not 0 <= index < ARITY[expr[0]]:
        raise ValueError("INVALID_PATH")
    args = list(expr[1:])
    args[index] = replace_at(args[index], path[1:], new)
    return (expr[0], *args)


def rewrite(source, law_id, path=()):
    law = LAWS[law_id]
    bindings = match(law.source, at_path(source, path))
    return None if bindings is None else replace_at(source, path, instantiate(law.target, bindings))


def law_applies(source, target, law_id, path=()):
    validate(target)
    return rewrite(source, law_id, path) == target


def truth(record):
    if record["task"] == "evaluate":
        return evaluate(record["expression"], record["valuation"])
    if record["task"] == "law_applies":
        return law_applies(record["source"], record["target"], record["law"], tuple(record["path"]))
    raise ValueError("UNKNOWN_TASK")


def _prefix(expr):
    validate(expr)
    if isinstance(expr, str):
        return [TOKEN_ID["ATOM." + expr]]
    return [TOKEN_ID["OP." + expr[0]], *[t for item in expr[1:] for t in _prefix(item)]]


def encode(record):
    if record["task"] == "evaluate":
        exp = record["expression"]
        if set(record["valuation"]) != variables(exp):
            raise ValueError("VALUATION_BINDING")
        ids = [TOKEN_ID["TASK.EVALUATE"], *_prefix(exp), TOKEN_ID["SYNTAX.BIND"]]
        for name, value in sorted(record["valuation"].items()):
            if type(value) is not bool:
                raise ValueError("NON_BOOLEAN_VALUATION")
            ids.extend((TOKEN_ID["ATOM." + name], TOKEN_ID["ATOM.TRUE" if value else "ATOM.FALSE"]))
    elif record["task"] == "law_applies":
        ids = [TOKEN_ID["TASK.LAW_APPLIES"], TOKEN_ID[record["law"]],
               *_prefix(record["source"]), TOKEN_ID["SYNTAX.SEP"], *_prefix(record["target"]),
               TOKEN_ID["SYNTAX.PATH_ROOT"]]
        for index in record["path"]:
            if index not in (0, 1):
                raise ValueError("INVALID_PATH")
            ids.append(TOKEN_ID["SYNTAX.PATH_" + str(index)])
    else:
        raise ValueError("UNKNOWN_TASK")
    return ids + [TOKEN_ID["SYNTAX.END"]]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify_registry():
    assert len(TOKENS) == len(TOKEN_ID)
    for law in LAWS.values():
        validate(law.source, meta=True)
        validate(law.target, meta=True)
        bindings = dict(zip(METAS, ("P", "Q", "R")))
        a, b = instantiate(law.source, bindings), instantiate(law.target, bindings)
        if not equivalent(a, b):
            raise ValueError("UNSOUND_LAW: " + law.semantic_id)
        if not law_applies(a, b, law.semantic_id):
            raise ValueError("BROKEN_LAW_MATCHER: " + law.semantic_id)
    return True
