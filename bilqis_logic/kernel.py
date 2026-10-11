"""Typed Boolean AST, two independent evaluators, and a lossless numeric codec.

The codec traverses syntax only. Neither answers nor reduced truth functions are
input features. Stable semantic identities are separate from numeric token IDs.
"""
from __future__ import annotations

import hashlib
import itertools
import json

VERSION = "cogal-t0-t1-0.1.0"
OPERATORS = {"NOT": 1, "AND": 2, "OR": 2, "XOR": 2, "XNOR": 2,
             "IMPLIES": 2, "IFF": 2}
# Frozen user-authored order: TT, TF, FT, FF; NOT: T, F.
TABLES = {"NOT": [False, True], "AND": [True, False, False, False],
          "OR": [True, True, True, False], "XOR": [False, True, True, False],
          "XNOR": [True, False, False, True], "IMPLIES": [True, False, True, True],
          "IFF": [True, False, False, True]}
TOKENS = ["syntax.pad", "task.evaluate", "task.equivalent", "syntax.bind",
          "syntax.separator", "syntax.end", "cogal.value.false", "cogal.value.true",
          "cogal.variable.P", "cogal.variable.Q"] + ["cogal.operator." + s for s in OPERATORS]
TOKEN_ID = {s: i for i, s in enumerate(TOKENS)}


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def literal(value):
    if type(value) is not bool:
        raise ValueError("Boolean literal required")
    return {"kind": "literal", "value": value}


def variable(name):
    if name not in ("P", "Q"):
        raise ValueError("only P/Q variables admitted")
    return {"kind": "variable", "name": name}


def apply(operator, *args):
    expr = {"kind": "apply", "operator": operator, "args": list(args)}
    validate(expr)
    return expr


def validate(expr, depth=0):
    if not isinstance(expr, dict) or depth > 8:
        raise ValueError("typed expression/depth")
    kind = expr.get("kind")
    if kind == "literal" and set(expr) == {"kind", "value"} and type(expr["value"]) is bool:
        return
    if kind == "variable" and set(expr) == {"kind", "name"} and type(expr["name"]) is str and expr["name"] in ("P", "Q"):
        return
    if (kind != "apply" or set(expr) != {"kind", "operator", "args"}
            or type(expr["operator"]) is not str or expr["operator"] not in OPERATORS or not isinstance(expr["args"], list)
            or len(expr["args"]) != OPERATORS[expr["operator"]]):
        raise ValueError("operator signature/Boolean type")
    for arg in expr["args"]:
        validate(arg, depth + 1)


def free_variables(expr):
    validate(expr)
    if expr["kind"] == "variable":
        return {expr["name"]}
    if expr["kind"] == "literal":
        return set()
    return set().union(*(free_variables(a) for a in expr["args"]))


def assignments(exprs):
    names = sorted(set().union(*(free_variables(e) for e in exprs)))
    return [dict(zip(names, values)) for values in itertools.product((False, True), repeat=len(names))]


def check_environment(expr, env):
    if (not isinstance(env, dict) or set(env) != free_variables(expr)
            or any(type(v) is not bool for v in env.values())):
        raise ValueError("exact Boolean variable assignments required")


def _table_eval(expr, env):
    if expr["kind"] == "literal":
        return expr["value"]
    if expr["kind"] == "variable":
        return env[expr["name"]]
    values = [_table_eval(a, env) for a in expr["args"]]
    index = (0 if values[0] else 1) if len(values) == 1 else (
        (0 if values[0] else 2) + (0 if values[1] else 1))
    return TABLES[expr["operator"]][index]


def evaluate(expr, env):
    check_environment(expr, env)
    return _table_eval(expr, env)


def _independent_eval(expr, env):
    if expr["kind"] == "literal":
        return expr["value"]
    if expr["kind"] == "variable":
        return env[expr["name"]]
    values = [_independent_eval(a, env) for a in expr["args"]]
    a = values[0]
    if expr["operator"] == "NOT":
        return not a
    b = values[1]
    # Operational Boolean algebra, independent of the frozen lookup tables.
    return {"AND": lambda: a and b, "OR": lambda: a or b,
            "XOR": lambda: a != b, "XNOR": lambda: a == b,
            "IMPLIES": lambda: (not a) or b, "IFF": lambda: a == b}[expr["operator"]]()


def independent_evaluate(expr, env):
    check_environment(expr, env)
    return _independent_eval(expr, env)


def equivalent(left, right, *, independent=False):
    evaluator = _independent_eval if independent else _table_eval
    return all(evaluator(left, env) == evaluator(right, env) for env in assignments((left, right)))


def evaluation_record(expr, env):
    check_environment(expr, env)
    return {"task": "evaluate", "expression": expr, "assignments": dict(env)}


def equivalence_record(left, right):
    validate(left)
    validate(right)
    return {"task": "equivalent", "left": left, "right": right}


def gold(record, *, independent=False):
    if record["task"] == "evaluate":
        evaluator = independent_evaluate if independent else evaluate
        return evaluator(record["expression"], record["assignments"])
    if record["task"] == "equivalent":
        return equivalent(record["left"], record["right"], independent=independent)
    raise ValueError("unknown task")


def _prefix(expr):
    validate(expr)
    if expr["kind"] == "literal":
        return [7 if expr["value"] else 6]
    if expr["kind"] == "variable":
        return [TOKEN_ID["cogal.variable." + expr["name"]]]
    return [TOKEN_ID["cogal.operator." + expr["operator"]]] + [t for a in expr["args"] for t in _prefix(a)]


def encode(record):
    if record["task"] == "evaluate":
        check_environment(record["expression"], record["assignments"])
        ids = [1] + _prefix(record["expression"]) + [3]
        for name, value in sorted(record["assignments"].items()):
            ids += [TOKEN_ID["cogal.variable." + name], 7 if value else 6]
    elif record["task"] == "equivalent":
        ids = [2] + _prefix(record["left"]) + [4] + _prefix(record["right"])
    else:
        raise ValueError("unknown task")
    return ids + [5]


def decode(ids):
    if (not isinstance(ids, list) or any(type(t) is not int or t < 1 or t >= len(TOKENS) for t in ids)):
        raise ValueError("token ABI")
    cursor = 1

    def take():
        nonlocal cursor
        if cursor >= len(ids):
            raise ValueError("truncated stream")
        token = ids[cursor]
        cursor += 1
        return token

    def expr(depth=0):
        if depth > 8:
            raise ValueError("expression depth")
        token = take()
        if token in (6, 7):
            return literal(token == 7)
        if token in (8, 9):
            return variable("P" if token == 8 else "Q")
        if token >= 10:
            op = TOKENS[token].removeprefix("cogal.operator.")
            return apply(op, *(expr(depth + 1) for _ in range(OPERATORS[op])))
        raise ValueError("expression token")

    if not ids:
        raise ValueError("empty stream")
    if ids[0] == 1:
        tree = expr()
        if take() != 3:
            raise ValueError("binding delimiter")
        env = {}
        token = take()
        while token != 5:
            if token not in (8, 9):
                raise ValueError("binding variable")
            name = "P" if token == 8 else "Q"
            value = take()
            if name in env or value not in (6, 7):
                raise ValueError("binding value/duplicate")
            env[name] = value == 7
            token = take()
        row = evaluation_record(tree, env)
    elif ids[0] == 2:
        left = expr()
        if take() != 4:
            raise ValueError("pair delimiter")
        row = equivalence_record(left, expr())
        if take() != 5:
            raise ValueError("end delimiter")
    else:
        raise ValueError("task token")
    if cursor != len(ids):
        raise ValueError("trailing tokens")
    return row


def token_manifest():
    return {"version": VERSION, "tokens": TOKENS, "answer_order": [False, True],
            "syntax": "typed prefix; explicit variable bindings; unreduced expression pair",
            "labels_in_input": False, "natural_language_in_input": False}
