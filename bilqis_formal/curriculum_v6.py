"""Versioned semantic-neighborhood curriculum for the standalone Boolean student.

All semantic grouping lives with the teacher. The student sees only the exact
typed question ABI already used by v0.5; neither semantic classes nor answers
are inserted into its prompt. This module never reads a sealed evaluation
result while choosing a training example.
"""
from __future__ import annotations

from itertools import product
from functools import lru_cache
import json

from .course_v3 import truth_rows
from .dialogue_v3 import gold_label, encode_prompt
from .semantics import app, evaluate, equivalent, variables

VERSION = "bilqis.formal.semantic-curriculum/v0.6.0"
STAGES = ("V00.BOOLEAN", "V01.NOT", "V02.AND")
DEPENDENCIES = {"V00.BOOLEAN": (), "V01.NOT": ("V00.BOOLEAN",),
                "V02.AND": ("V00.BOOLEAN",)}


def NOT(x):
    return app("NOT", x)


def AND(x, y):
    return app("AND", x, y)


# Expressions are explicit rather than generated from held-out performance.
# Train/dev/sealed identities have no overlap within this new e9 epoch.
EXPRESSIONS = {
    "V00.BOOLEAN": {
        "train": ("TRUE", "FALSE", "P"),
        "dev": ("Q",),
        "gate": ("R",),
    },
    "V01.NOT": {
        "train": (NOT("P"), NOT("TRUE"), NOT("FALSE"), NOT(NOT("P")),
                  NOT(NOT("TRUE")), NOT(NOT("FALSE"))),
        "dev": (NOT("Q"), NOT(NOT("Q")), NOT(NOT(NOT("Q")))),
        "gate": (NOT("R"), NOT(NOT("R")), NOT(NOT(NOT("R")))),
    },
    "V02.AND": {
        "train": (AND("P", "Q"), AND("Q", "P"),
                  AND("P", "TRUE"), AND("TRUE", "P"),
                  AND("P", "FALSE"), AND("FALSE", "P"),
                  AND("P", "P"),
                  AND("P", AND("Q", "TRUE")),
                  AND(AND("P", "TRUE"), "Q"),
                  AND("P", AND("Q", "FALSE")),
                  AND(AND("P", "P"), "Q")),
        "dev": (AND("Q", "R"), AND("R", "Q"),
                AND("Q", "TRUE"), AND("FALSE", "Q"),
                AND("Q", "Q"), AND("Q", AND("R", "TRUE")),
                AND(AND("Q", "TRUE"), "R"),
                AND("Q", AND("R", "FALSE"))),
        "gate": (AND("R", "P"), AND("P", "R"),
                 AND("TRUE", "R"), AND("R", "FALSE"),
                 AND("R", "R"), AND("R", AND("P", "TRUE")),
                 AND(AND("R", "TRUE"), "P"),
                 AND("R", AND("P", "FALSE")),
                 AND(AND("R", "P"), "R")),
    },
}

# Exact, independently checkable algebraic relationships. Each is taught only
# through ordinary truth-label prediction; no explicit law label enters input.
RELATIONS = (
    ("P", AND("P", "TRUE")),
    ("P", AND("TRUE", "P")),
    ("P", AND("P", "P")),
    (AND("P", "Q"), AND("Q", "P")),
    (AND("P", "Q"), AND("P", AND("Q", "TRUE"))),
    (AND("P", "FALSE"), "FALSE"),
    (NOT(NOT("P")), "P"),
)


@lru_cache(maxsize=512)
def signature(expr):
    """Full eight-row truth signature on the stable P/Q/R valuation universe."""
    names = variables(expr)
    return "".join("1" if evaluate(expr, {name: env[name] for name in names})
                   else "0" for values in product((False, True), repeat=3)
                   for env in [dict(zip(("P", "Q", "R"), values))])


@lru_cache(maxsize=512)
def concept_key(expr):
    """Teacher-only equivalence/complement neighborhood (not a gold label)."""
    bits = signature(expr)
    opposite = "".join("0" if bit == "1" else "1" for bit in bits)
    return min(bits, opposite)


def depth(expr):
    return 0 if isinstance(expr, str) else 1 + max(depth(child) for child in expr[1:])


@lru_cache(maxsize=512)
def expression_id(expr):
    return json.dumps(expr, separators=(",", ":"), sort_keys=True)


def rows(stage, role):
    if stage not in STAGES:
        raise ValueError("UNDECLARED_V06_STAGE")
    if role not in ("train", "dev", "gate"):
        raise ValueError("UNDECLARED_V06_SPLIT")
    return [r for expr in EXPRESSIONS[stage][role]
            for r in truth_rows(stage, expr, "sealed" if role == "gate" else role)]


def split(stage):
    """Administrative full split. Training and DEV must use role-specific rows."""
    return {role: rows(stage, role) for role in ("train", "dev", "gate")}


def validate():
    if set(DEPENDENCIES) != set(STAGES) or set(EXPRESSIONS) != set(STAGES):
        raise ValueError("V06_INCOMPLETE_STAGE_GRAPH")
    for stage in STAGES:
        if any(dep not in STAGES[:STAGES.index(stage)] for dep in DEPENDENCIES[stage]):
            raise ValueError("V06_INVALID_DEPENDENCY")
        sets = split(stage)
        identities = [{r["id"] for r in sets[role]}
                      for role in ("train", "dev", "gate")]
        if any(not v for v in identities) or any(
                identities[i] & identities[j] for i in range(3) for j in range(i + 1, 3)):
            raise ValueError("V06_LEAKED_QUESTION_IDENTITY")
        for role, rows in sets.items():
            if {r["gold"] for r in rows} != {"ATOM.TRUE", "ATOM.FALSE"}:
                raise ValueError("V06_MISSING_TRUTH_CLASS")
            for row in rows:
                if row["gold"] != gold_label(row["input"]):
                    raise ValueError("V06_WRONG_ORACLE")
                if len(encode_prompt(row["input"], mode="none")) > 96:
                    raise ValueError("V06_CONTEXT_OVERFLOW")
                if row["role"] != ("sealed" if role == "gate" else role):
                    raise ValueError("V06_WRONG_SPLIT_ROLE")
    for left, right in RELATIONS:
        if not equivalent(left, right) or signature(left) != signature(right):
            raise ValueError("V06_UNSOUND_SEMANTIC_RELATION")
        if concept_key(left) != concept_key(right):
            raise ValueError("V06_BROKEN_EQUIVALENCE_CLASS")
    # The source's finite grammar limits novelty claims. Prove distinct
    # expression identities, not historical unobservability of formulas.
    return True
