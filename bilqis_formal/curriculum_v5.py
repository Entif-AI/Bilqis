"""Independent, versioned train/DEV/sealed splits for the atomic curriculum.

This deliberately does not amend v0.3/e6 or v0.4/e7 frozen question sets.
The finite literal NOT domain is fully taught; held-out transfer is instead
measured on an unseen variable. Literal retention is reported as taught-domain
coverage, never disguised as an unseen exam.
"""
from __future__ import annotations

from .course_v3 import row, truth_rows
from .dialogue_v3 import gold_label
from .semantics import app, variables

VERSION = "bilqis.formal.atomic-curriculum/v0.5.0"
STAGES = ("V00.BOOLEAN", "V01.NOT", "V02.AND")
DEPENDENCIES = {"V00.BOOLEAN": (), "V01.NOT": ("V00.BOOLEAN",),
                "V02.AND": ("V00.BOOLEAN",)}


def unique(rows):
    return list({r["id"]: r for r in rows}.values())


def split(stage):
    if stage == "V00.BOOLEAN":
        train = truth_rows(stage, "TRUE", "train") + truth_rows(stage, "FALSE", "train")
        train += truth_rows(stage, "P", "train")
        dev = truth_rows(stage, "Q", "dev")
        gate = truth_rows(stage, "R", "sealed")
    elif stage == "V01.NOT":
        train = truth_rows(stage, app("NOT", "P"), "train")
        train += truth_rows(stage, app("NOT", "TRUE"), "train")
        train += truth_rows(stage, app("NOT", "FALSE"), "train")
        dev = truth_rows(stage, app("NOT", "Q"), "dev")
        gate = truth_rows(stage, app("NOT", "R"), "sealed")
    elif stage == "V02.AND":
        train = truth_rows(stage, app("AND", "P", "Q"), "train")
        for left in ("TRUE", "FALSE"):
            for right in ("TRUE", "FALSE"):
                train.append(row(stage, app("AND", left, right), {}, "train"))
        train += truth_rows(stage, app("AND", "P", "TRUE"), "train")
        train += truth_rows(stage, app("AND", "FALSE", "P"), "train")
        dev = truth_rows(stage, app("AND", "Q", "R"), "dev")
        dev += truth_rows(stage, app("AND", "TRUE", "Q"), "dev")
        dev += truth_rows(stage, app("AND", "Q", "FALSE"), "dev")
        gate = truth_rows(stage, app("AND", "R", "P"), "sealed")
        gate += truth_rows(stage, app("AND", "TRUE", "R"), "sealed")
        gate += truth_rows(stage, app("AND", "R", "FALSE"), "sealed")
    else:
        raise ValueError("UNDECLARED_V05_STAGE")
    return {"train": unique(train), "dev": unique(dev), "gate": unique(gate)}


def family(record):
    """A coarse, inspectable teaching group, not a learned ontology."""
    expr = record["input"]["expression"]
    variables_seen = variables(expr)
    if not variables_seen:
        return "literal"
    if record["stage"] == "V02.AND" and len(variables_seen) == 1:
        return "mixed"
    return "variable"


def literal_coverage_rows(stage):
    return [r for r in split(stage)["train"] if family(r) == "literal"]


def validate():
    for stage in STAGES:
        pools = split(stage)
        ids = [{r["id"] for r in pools[key]} for key in ("train", "dev", "gate")]
        if any(not p for p in ids) or any(ids[i] & ids[j] for i in range(3)
                                           for j in range(i + 1, 3)):
            raise ValueError("EXAM_OR_FORMATIVE_LEAK")
        for part, rows in pools.items():
            for r in rows:
                if (r["input"]["task"] != "evaluate" or
                        r["role"] != ("sealed" if part == "gate" else part) or
                        r["gold"] != gold_label(r["input"])):
                    raise ValueError("WRONG_ORACLE_OR_ROLE")
        for part in ("train", "dev", "gate"):
            if {r["gold"] for r in pools[part]} != {"ATOM.FALSE", "ATOM.TRUE"}:
                raise ValueError("UNBALANCED_TRUTH_DOMAIN")
        if not set(DEPENDENCIES[stage]) <= set(STAGES[:STAGES.index(stage)]):
            raise ValueError("BAD_PREREQUISITE_ORDER")
    if set(DEPENDENCIES) != set(STAGES):
        raise ValueError("MISSING_CURRICULUM_DEPENDENCY")
    if len(literal_coverage_rows("V01.NOT")) != 2:
        raise ValueError("MISSING_NEGATION_LITERALS")
    return True
