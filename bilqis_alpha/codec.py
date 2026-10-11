"""Lossless prefix codec; integer allocation never defines semantic geometry."""
from .semantics import ABI, SemanticError, digest, normalize, registry, sid

VERSION = "alpha-prefix-0.1.0"


def token_manifest() -> dict:
    entries = registry()["entries"]
    tokens = [sid("pad")] + sorted(r["id"] for r in entries if r["id"] != sid("pad"))
    return {"version": VERSION, "semantic_registry_sha256": digest(registry()),
            "tokens": tokens, "padding_id": 0, "reserved_policy": "none; new identities require ABI version",
            "oov_policy": "reject", "retention": "lossless within alpha domain; evidence order canonicalized"}


def encode(semantic: dict) -> list[int]:
    s = normalize(semantic)
    m = token_manifest()
    ids = {t: i for i, t in enumerate(m["tokens"])}
    out = [sid("world"), sid("a"), sid("b"), sid("source-0"), sid("source-1")]
    for f in s["world"]["facts"]:
        out.extend([sid("fact"), f["predicate"], sid("role-source"), f["roles"]["source"],
                    sid("role-target"), f["roles"]["target"], f["polarity"], f["source"]])
    out.append(sid("query"))

    def visit(q):
        op = q["op"]
        out.append(op)
        if op in (sid("relation"), sid("equal")):
            for role, t in zip(("role-source", "role-target") if op == sid("relation") else ("role-left", "role-right"), q["args"]):
                out.extend([sid(role), sid(t["kind"]), t["id"]])
        elif op in (sid("exists"), sid("forall")):
            out.extend([sid("role-binder"), q["variable"]])
            visit(q["body"])
        else:
            for a in q["args"]:
                visit(a)
        out.append(sid("end-node"))

    visit(s["query"])
    out.append(sid("answer"))  # query terminator, never a gold answer token
    return [ids[t] for t in out]


def decode(ids: list[int]) -> dict:
    tokens = token_manifest()["tokens"]
    if not isinstance(ids, list) or any(type(i) is not int or not 0 < i < len(tokens) for i in ids):
        raise ValueError("token domain/padding")
    text = [tokens[i] for i in ids]
    pos = 0

    def take(expected=None):
        nonlocal pos
        if pos >= len(text):
            raise ValueError("truncated codec")
        t = text[pos]
        pos += 1
        if expected is not None and t != expected:
            raise ValueError("codec signature")
        return t

    take(sid("world"))
    entities = [take(sid("a")), take(sid("b"))]
    sources = [take(sid("source-0")), take(sid("source-1"))]
    facts = []
    while pos < len(text) and text[pos] == sid("fact"):
        take(sid("fact"))
        predicate = take(sid("relation"))
        take(sid("role-source")); a = take()
        take(sid("role-target")); b = take()
        facts.append({"predicate": predicate, "roles": {"source": a, "target": b},
                      "polarity": take(), "source": take()})
    take(sid("query"))

    def visit(depth=0):
        if depth > 4:
            raise ValueError("codec depth")
        op = take()
        if op in (sid("relation"), sid("equal")):
            args = []
            roles = ("role-source", "role-target") if op == sid("relation") else ("role-left", "role-right")
            for role in roles:
                take(sid(role)); kind = take()
                if kind not in (sid("constant"), sid("variable")):
                    raise ValueError("codec term kind")
                args.append({"kind": kind.rsplit(":", 1)[-1], "id": take()})
            q = {"op": op, "args": args}
        elif op in (sid("exists"), sid("forall")):
            take(sid("role-binder"))
            q = {"op": op, "variable": take(), "body": visit(depth + 1)}
        elif op in (sid("not"), sid("and"), sid("or")):
            q = {"op": op, "args": [visit(depth + 1) for _ in range(1 if op == sid("not") else 2)]}
        else:
            raise ValueError("unsupported codec operator")
        take(sid("end-node"))
        return q

    q = visit()
    take(sid("answer"))
    if pos != len(text):
        raise ValueError("trailing codec tokens")
    return normalize({"abi": ABI, "world": {"entities": entities, "sources": sources, "facts": facts}, "query": q})
