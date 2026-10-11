"""Typed, closed finite worlds; independent set/table and matrix/operation oracles.

Proof entailment is satisfaction in the least closure of the declared Horn rule,
not unrestricted first-order theorem proving. Evidence reports are separate from
closed-world relational facts. Live interpretations are evaluated separately.
The lossless codec contains asserted facts and syntax, never inferred closure.
"""
from __future__ import annotations

import copy

from bilqis_logic import kernel as boolean
from .graph import ENTITIES, ID, RELATIONS, RULE, STATES, TOKENS

VERSION = "micro-finite-world-0.1.0"
SOURCES = ("S0", "S1", "S2")
PROPOSITIONS = ("J0", "J1", "J2")


def entity(name):
    return {"kind": "entity", "name": name}


def bound(index):
    return {"kind": "bound", "index": index}


def relation(name, left, right):
    return {"kind": "relation", "name": name, "args": [left, right]}


def logic(operator, *args):
    return {"kind": "apply", "operator": operator, "args": list(args)}


def compare(operator, left, right):
    return {"kind": "compare", "operator": operator, "args": [left, right]}


def quantify(operator, body):
    return {"kind": "quantify", "operator": operator, "body": body}


def compose(first, second, left, right):
    return {"kind": "compose", "relations": [first, second], "args": [left, right]}


def entails(conclusion):
    return {"kind": "entails", "conclusion": conclusion}


def rule_step(premises, conclusion):
    return {"kind": "rule_step", "premises": list(premises), "conclusion": conclusion}


def countermodel(premises, conclusion):
    return {"kind": "countermodel", "premises": list(premises), "conclusion": conclusion}


def observe(proposition):
    return {"kind": "observe", "proposition": proposition}


def evidence_logic(operator, *args):
    return {"kind": "evidence", "operator": operator, "args": list(args)}


def world(entities, facts=(), *, rules=(), propositions=None, reports=(), live=(0,)):
    w = {"entities": sorted(entities), "facts": sorted([list(f) for f in facts]), "rules": sorted(rules),
         "propositions": copy.deepcopy(propositions or {}), "reports": sorted([list(r) for r in reports]), "live": sorted(live)}
    validate_world(w)
    return w


def _keys(obj, *keys):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        raise ValueError("exact typed fields required")


def _member(value, choices):
    if type(value) is not str or value not in choices:
        raise ValueError("identity outside admitted type/domain")


def _unique_list(items):
    if not isinstance(items, list) or len({boolean.digest(x) for x in items}) != len(items):
        raise ValueError("unique list required")


def validate_world(w):
    _keys(w, "entities", "facts", "rules", "propositions", "reports", "live")
    for key in ("entities", "facts", "rules", "reports", "live"):
        _unique_list(w[key])
    if not 2 <= len(w["entities"]) <= 5:
        raise ValueError("finite domain must have 2-5 entities")
    for e in w["entities"]:
        _member(e, ENTITIES)
    for f in w["facts"]:
        if not isinstance(f, list) or len(f) != 3:
            raise ValueError("binary asserted fact required")
        _member(f[0], RELATIONS)
        for e in f[1:]:
            _member(e, w["entities"])
    for r in w["rules"]:
        _member(r, (RULE,))
    if not isinstance(w["propositions"], dict) or any(p not in PROPOSITIONS for p in w["propositions"]):
        raise ValueError("proposition map")
    for expr in w["propositions"].values():
        if _type(expr, w) != "Boolean":
            raise ValueError("propositions name closed Boolean statements")
    if not w["live"] or any(type(i) is not int or i not in (0, 1) for i in w["live"]):
        raise ValueError("live interpretation domain")
    for r in w["reports"]:
        if not isinstance(r, list) or len(r) != 4:
            raise ValueError("source/proposition/polarity/interpretation required")
        _member(r[0], SOURCES)
        _member(r[1], w["propositions"])
        _member(r[2], ("support", "refute"))
        if type(r[3]) is not int or r[3] not in w["live"]:
            raise ValueError("report outside live interpretations")


def _type(e, w, scope=0, depth=0):
    if not isinstance(e, dict) or depth > 10:
        raise ValueError("typed expression/depth")
    kind = e.get("kind")
    child = lambda x, s=scope: _type(x, w, s, depth + 1)
    if kind == "entity":
        _keys(e, "kind", "name")
        _member(e["name"], w["entities"])
        return "Entity"
    if kind == "bound":
        _keys(e, "kind", "index")
        if type(e["index"]) is not int or e["index"] not in (0, 1) or e["index"] >= scope:
            raise ValueError("unbound de Bruijn variable")
        return "Entity"
    if kind == "literal":
        _keys(e, "kind", "value")
        if type(e["value"]) is not bool:
            raise ValueError("Boolean literal")
        return "Boolean"
    if kind in ("relation", "compare", "compose"):
        _keys(e, "kind", "relations" if kind == "compose" else "name" if kind == "relation" else "operator", "args")
        if kind == "compose":
            if not isinstance(e["relations"], list) or len(e["relations"]) != 2:
                raise ValueError("two relation composition")
            for name in e["relations"]:
                _member(name, RELATIONS)
        else:
            _member(e["name"] if kind == "relation" else e["operator"], RELATIONS if kind == "relation" else ("EQ", "NEQ"))
        if not isinstance(e["args"], list) or len(e["args"]) != 2 or any(child(a) != "Entity" for a in e["args"]):
            raise ValueError("Entity*Entity arguments")
        return "Boolean"
    if kind in ("apply", "evidence"):
        _keys(e, "kind", "operator", "args")
        operators = boolean.OPERATORS if kind == "apply" else {"NOT": 1, "AND": 2, "OR": 2}
        _member(e["operator"], operators)
        if not isinstance(e["args"], list) or len(e["args"]) != operators[e["operator"]]:
            raise ValueError("operator arity")
        allowed = ("Boolean",) if kind == "apply" else ("Boolean", "Evidence")
        if any(child(a) not in allowed for a in e["args"]):
            raise ValueError("operator argument type")
        return "Boolean" if kind == "apply" else "Evidence"
    if kind == "quantify":
        _keys(e, "kind", "operator", "body")
        _member(e["operator"], ("EXISTS", "FORALL"))
        if scope >= 2 or child(e["body"], scope + 1) != "Boolean":
            raise ValueError("finite Boolean quantifier, at most two binders")
        return "Boolean"
    if kind in ("entails", "rule_step", "countermodel"):
        _keys(e, "kind", "conclusion", *([] if kind == "entails" else ["premises"]))
        if child(e["conclusion"]) != "Boolean":
            raise ValueError("Boolean conclusion")
        if kind != "entails":
            if not isinstance(e["premises"], list) or len(e["premises"]) != 2 or any(child(p) != "Boolean" for p in e["premises"]):
                raise ValueError("two Boolean premises")
        return "Boolean"
    if kind == "observe":
        _keys(e, "kind", "proposition")
        _member(e["proposition"], w["propositions"])
        return "Evidence"
    raise ValueError("unknown expression kind")


def record(w, expression):
    row = {"task": "micro", "world": copy.deepcopy(w), "query": copy.deepcopy(expression)}
    validate_record(row)
    return row


def validate_record(r):
    if not isinstance(r, dict):
        raise ValueError("record required")
    if r.get("task") in ("evaluate", "equivalent"):
        _keys(r, "task", *(["expression", "assignments"] if r["task"] == "evaluate" else ["left", "right"]))
        boolean.decode(boolean.encode(r))
        return
    _keys(r, "task", "world", "query")
    if r["task"] != "micro":
        raise ValueError("unknown task")
    validate_world(r["world"])
    if _type(r["query"], r["world"]) not in ("Boolean", "Evidence"):
        raise ValueError("query must return Boolean or Evidence")


def _set_relations(w):
    rels = {r: set() for r in RELATIONS}
    for name, a, b in w["facts"]:
        rels[name].add((a, b))
        if name == "PARENT":
            rels["CHILD"].add((b, a))
        elif name == "CHILD":
            rels["PARENT"].add((b, a))
        elif name == "LINK":
            rels["LINK"].add((b, a))
    if RULE in w["rules"]:
        rels["GRANDPARENT"] |= {(a, c) for a, b in rels["PARENT"] for x, c in rels["PARENT"] if b == x}
    return rels


def _matrices(w):
    # Separate implementation: adjacency tables, transpose and Boolean matrix product.
    n = len(w["entities"])
    indices = {e: i for i, e in enumerate(w["entities"])}
    m = {r: [[False] * n for _ in range(n)] for r in RELATIONS}
    for name, a, b in w["facts"]:
        m[name][indices[a]][indices[b]] = True
    p, c = m["PARENT"], m["CHILD"]
    parent = [[p[i][j] or c[j][i] for j in range(n)] for i in range(n)]
    m["PARENT"] = parent
    m["CHILD"] = [[parent[j][i] for j in range(n)] for i in range(n)]
    m["LINK"] = [[m["LINK"][i][j] or m["LINK"][j][i] for j in range(n)] for i in range(n)]
    if RULE in w["rules"]:
        m["GRANDPARENT"] = [[m["GRANDPARENT"][i][j] or any(parent[i][k] and parent[k][j] for k in range(n))
                             for j in range(n)] for i in range(n)]
    return indices, m


def _operation(op, values):
    a = values[0]
    if op == "NOT":
        return not a
    b = values[1]
    return {"AND": lambda: a and b, "OR": lambda: a or b, "XOR": lambda: a != b,
            "XNOR": lambda: a == b, "IMPLIES": lambda: not a or b, "IFF": lambda: a == b}[op]()


def _table(op, values):
    index = int(not values[0]) if len(values) == 1 else 2 * int(not values[0]) + int(not values[1])
    return boolean.TABLES[op][index]


def _bits(v):
    return (v, not v) if type(v) is bool else v


def _evidence_table(op, values):
    # Four-state tables indexed UNKNOWN, TRUE, FALSE, CONFLICT.
    states = [(False, False), (True, False), (False, True), (True, True)]
    i = states.index(_bits(values[0]))
    if op == "NOT":
        return states[[0, 2, 1, 3][i]]
    j = states.index(_bits(values[1]))
    table = ([[0, 0, 2, 2], [0, 1, 2, 3], [2, 2, 2, 2], [2, 3, 2, 3]] if op == "AND" else
             [[0, 1, 0, 1], [1, 1, 1, 1], [0, 1, 2, 3], [1, 1, 3, 3]])
    return states[table[i][j]]


def _evidence_operation(op, values):
    s, r = _bits(values[0])
    if op == "NOT":
        return r, s
    t, u = _bits(values[1])
    return (s and t, r or u) if op == "AND" else (s or t, r and u)


def _rule_match(e, resolve):
    p, q = e["premises"]
    c = e["conclusion"]
    if (any(x["kind"] != "relation" for x in (p, q, c)) or
            p["name"] != "PARENT" or q["name"] != "PARENT" or c["name"] != "GRANDPARENT"):
        return False
    a, b = map(resolve, p["args"])
    x, z = map(resolve, q["args"])
    return b == x and list(map(resolve, c["args"])) == [a, z]


def _eval(e, w, lookup, op, evidence_op, interpretation, bindings=()):
    # Syntax traversal is shared; relational closure and both algebras are independent.
    ev = lambda x, bs=bindings: _eval(x, w, lookup, op, evidence_op, interpretation, bs)
    k = e["kind"]
    if k == "entity":
        return e["name"]
    if k == "bound":
        return bindings[e["index"]]
    if k == "literal":
        return e["value"]
    if k == "relation":
        return lookup(e["name"], *(ev(a) for a in e["args"]))
    if k == "compare":
        equal = ev(e["args"][0]) == ev(e["args"][1])
        return equal if e["operator"] == "EQ" else not equal
    if k in ("apply", "evidence"):
        return (op if k == "apply" else evidence_op)(e["operator"], [ev(a) for a in e["args"]])
    if k == "quantify":
        values = [ev(e["body"], (name,) + bindings) for name in w["entities"]]
        return any(values) if e["operator"] == "EXISTS" else all(values)
    if k == "compose":
        a, b = map(ev, e["args"])
        return any(lookup(e["relations"][0], a, x) and lookup(e["relations"][1], x, b) for x in w["entities"])
    if k == "entails":
        return ev(e["conclusion"])
    if k == "rule_step":
        return RULE in w["rules"] and _rule_match(e, ev) and all(ev(p) for p in e["premises"])
    if k == "countermodel":
        return all(ev(p) for p in e["premises"]) and not ev(e["conclusion"])
    if k == "observe":
        polarities = {r[2] for r in w["reports"] if r[1] == e["proposition"] and r[3] == interpretation}
        return "support" in polarities, "refute" in polarities
    raise ValueError("unknown expression")


def _evaluate(r, independent):
    validate_record(r)
    if r["task"] != "micro":
        return "TRUE" if boolean.gold(r, independent=independent) else "FALSE"
    w = r["world"]
    if independent:
        indices, matrices = _matrices(w)
        lookup = lambda name, a, b: matrices[name][indices[a]][indices[b]]
    else:
        rels = _set_relations(w)
        lookup = lambda name, a, b: (a, b) in rels[name]
    outcomes = {_bits(_eval(r["query"], w, lookup, _operation if independent else _table,
                           _evidence_operation if independent else _evidence_table, i)) for i in w["live"]}
    if len(outcomes) != 1:
        return "AMBIGUOUS"
    return {(False, False): "UNKNOWN", (True, False): "TRUE", (False, True): "FALSE", (True, True): "CONFLICT"}[outcomes.pop()]


def evaluate(r):
    return _evaluate(r, False)


def independent_evaluate(r):
    return _evaluate(r, True)


def _prefix(e):
    k = e["kind"]
    if k == "entity":
        return [ID["micro.entity." + e["name"]]]
    if k == "bound":
        return [ID["micro.bound." + str(e["index"])]]
    if k == "literal":
        return [7 if e["value"] else 6]
    if k in ("apply", "evidence", "relation", "compare"):
        identity = {"apply": "cogal.operator.", "evidence": "micro.evidence.", "relation": "micro.relation.", "compare": "micro.compare."}[k]
        return [ID[identity + e["name" if k == "relation" else "operator"]]] + [t for a in e["args"] for t in _prefix(a)]
    if k == "quantify":
        return [ID["micro.quantifier." + e["operator"]]] + _prefix(e["body"])
    if k == "compose":
        return [ID["micro.compose"]] + [ID["micro.relation." + name] for name in e["relations"]] + [t for a in e["args"] for t in _prefix(a)]
    if k == "observe":
        return [ID["micro.evidence.observe"], ID["micro.proposition." + e["proposition"]]]
    out = [ID["micro.proof." + k]]
    if k != "entails":
        for p in e["premises"]:
            out += [ID["micro.proof.premise"]] + _prefix(p)
    return out + [ID["micro.proof.conclusion"]] + _prefix(e["conclusion"])


def encode(r):
    validate_record(r)
    if r["task"] != "micro":
        return boolean.encode(r)
    w = r["world"]
    ids = [ID["micro.syntax.world"], ID["micro.syntax.entities"]]
    ids += [ID["micro.entity." + e] for e in w["entities"]]
    ids += [ID["micro.syntax.facts"]]
    ids += [t for f in w["facts"] for t in [ID["micro.relation." + f[0]], ID["micro.entity." + f[1]], ID["micro.entity." + f[2]]]]
    ids += [ID["micro.syntax.rules"]] + [ID[name] for name in w["rules"]]
    ids += [ID["micro.syntax.propositions"]]
    for name, expr in sorted(w["propositions"].items()):
        ids += [ID["micro.proposition." + name]] + _prefix(expr)
    ids += [ID["micro.syntax.reports"]]
    ids += [t for s, p, polarity, i in w["reports"] for t in [ID["micro.source." + s], ID["micro.proposition." + p], ID["micro.report." + polarity], ID["micro.interpretation." + str(i)]]]
    ids += [ID["micro.syntax.interpretations"]] + [ID["micro.interpretation." + str(i)] for i in w["live"]]
    return ids + [ID["micro.syntax.query"]] + _prefix(r["query"]) + [ID["syntax.end"]]


def decode(ids):
    if not isinstance(ids, list) or not ids or any(type(t) is not int or t < 1 or t >= len(TOKENS) for t in ids):
        raise ValueError("token ABI")
    if ids[0] != ID["micro.syntax.world"]:
        return boolean.decode(ids)
    cursor = 1

    def peek():
        if cursor >= len(ids):
            raise ValueError("truncated stream")
        return TOKENS[ids[cursor]]

    def take(expected=None, prefix=None):
        nonlocal cursor
        s = peek()
        cursor += 1
        if expected is not None and s != expected or prefix is not None and not s.startswith(prefix):
            raise ValueError("typed token/delimiter")
        return s.removeprefix(prefix) if prefix else s

    def expr(depth=0):
        if depth > 10:
            raise ValueError("expression depth")
        s = take()
        sub = lambda: expr(depth + 1)
        if s.startswith("micro.entity."):
            return entity(s.split(".")[-1])
        if s.startswith("micro.bound."):
            return bound(int(s.split(".")[-1]))
        if s in ("cogal.value.true", "cogal.value.false"):
            return boolean.literal(s.endswith("true"))
        if s.startswith("cogal.operator."):
            op = s.split(".")[-1]
            return logic(op, *(sub() for _ in range(boolean.OPERATORS[op])))
        if s.startswith("micro.relation."):
            return relation(s.split(".")[-1], sub(), sub())
        if s.startswith("micro.compare."):
            return compare(s.split(".")[-1], sub(), sub())
        if s.startswith("micro.quantifier."):
            return quantify(s.split(".")[-1], sub())
        if s == "micro.compose":
            names = [take(prefix="micro.relation.") for _ in range(2)]
            return compose(*names, sub(), sub())
        if s == "micro.evidence.observe":
            return observe(take(prefix="micro.proposition."))
        if s.startswith("micro.evidence."):
            op = s.split(".")[-1]
            return evidence_logic(op, *(sub() for _ in range(1 if op == "NOT" else 2)))
        if s.startswith("micro.proof."):
            k = s.split(".")[-1]
            if k not in ("entails", "rule_step", "countermodel"):
                raise ValueError("proof query token")
            premises = []
            if k != "entails":
                for _ in range(2):
                    take("micro.proof.premise")
                    premises.append(sub())
            take("micro.proof.conclusion")
            conclusion = sub()
            return entails(conclusion) if k == "entails" else {"rule_step": rule_step, "countermodel": countermodel}[k](premises, conclusion)
        raise ValueError("expression token")

    take("micro.syntax.entities")
    entities = []
    while peek() != "micro.syntax.facts":
        entities.append(take(prefix="micro.entity."))
    take("micro.syntax.facts")
    facts = []
    while peek() != "micro.syntax.rules":
        facts.append([take(prefix="micro.relation.")] + [take(prefix="micro.entity.") for _ in range(2)])
    take("micro.syntax.rules")
    rules = []
    while peek() != "micro.syntax.propositions":
        rules.append(take(RULE))
    take("micro.syntax.propositions")
    props = {}
    while peek() != "micro.syntax.reports":
        name = take(prefix="micro.proposition.")
        if name in props:
            raise ValueError("duplicate proposition")
        props[name] = expr()
    take("micro.syntax.reports")
    reports = []
    while peek() != "micro.syntax.interpretations":
        reports.append([take(prefix="micro.source."), take(prefix="micro.proposition."), take(prefix="micro.report."), int(take(prefix="micro.interpretation."))])
    take("micro.syntax.interpretations")
    live = []
    while peek() != "micro.syntax.query":
        live.append(int(take(prefix="micro.interpretation.")))
    take("micro.syntax.query")
    query = expr()
    take("syntax.end")
    if cursor != len(ids):
        raise ValueError("trailing tokens")
    # Do not canonicalize malformed or duplicate input away during decoding.
    return record({"entities": entities, "facts": facts, "rules": rules, "propositions": props, "reports": reports, "live": live}, query)
