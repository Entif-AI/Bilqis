"""Human-authored foundational course. Kev chooses examples, never the rules or gold.

The world is a Boolean valuation. New lesson families enter only after their
declared predecessors meet observable promotion criteria. Formative examinations
have disjoint source examples and frozen deterministic promotion probes.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from .semantics import LAWS, app, digest, equivalent, rewrite, truth, validate


@dataclass(frozen=True)
class Stage:
    id: str
    prerequisite: tuple[str, ...]
    new_id: str
    teaching_goal: str


STAGES = (
    Stage("F01.NOT", (), "OP.NOT", "Learn NOT's complete two-row truth function."),
    Stage("F02.AND", ("F01.NOT",), "OP.AND", "Learn AND's four-row truth function, including both false cases."),
    Stage("F03.NOT_INVOLUTION", ("F01.NOT", "F02.AND"), "LAW.NOT.INVOLUTION",
          "Learn double negation as a named uniform substitution law."),
    Stage("F04.AND_IDENTITY", ("F02.AND", "F03.NOT_INVOLUTION"), "LAW.AND.IDENTITY.RIGHT",
          "Recognize the AND-right-TRUE identity by name, not just output equality."),
    Stage("F05.AND_ANNIHILATOR", ("F02.AND", "F04.AND_IDENTITY"), "LAW.AND.ANNIHILATOR.RIGHT",
          "Distinguish AND-right-FALSE annihilator from right-TRUE identity."),
    Stage("F06.AND_ASSOCIATIVITY", ("F05.AND_ANNIHILATOR",), "LAW.AND.ASSOCIATIVITY",
          "Distinguish regrouping three operands from exchanging or deleting operands."),
)
STAGE = {s.id: s for s in STAGES}


@dataclass(frozen=True)
class Panel:
    id: str
    stage: str
    role: str
    description: str
    rows: tuple[dict, ...]


def expr_pretty(expr):
    if isinstance(expr, str):
        return expr
    if expr[0] == "NOT":
        return "NOT(" + expr_pretty(expr[1]) + ")"
    return "(" + expr_pretty(expr[1]) + " " + expr[0] + " " + expr_pretty(expr[2]) + ")"


def _row(record, stage, tier, family):
    gold = truth(record)
    if record["task"] == "law_applies" and gold and not equivalent(record["source"], record["target"]):
        raise ValueError("UNSOUND_LAW_EXAMPLE")
    return {"id": digest(record), "input": record, "gold": gold,
            "stage": stage, "tier": tier, "family": family}


def _eval(stage, expr, tier="easy", family="evaluation"):
    from .semantics import variables
    names = sorted(variables(expr))
    return [_row({"task": "evaluate", "expression": expr, "valuation": dict(zip(names, vals))},
                 stage, tier, family) for vals in product((False, True), repeat=len(names))]


def _law(stage, law_id, arg, tier="easy", family="rewrite"):
    pattern = LAWS[law_id].source
    from .semantics import instantiate
    if law_id == "LAW.AND.ASSOCIATIVITY":
        if not isinstance(arg, (list, tuple)) or len(arg) != 3:
            raise ValueError("ASSOCIATIVITY_NEEDS_THREE_FORMULAS")
        bindings = dict(zip(("$A", "$B", "$C"), arg))
    else:
        bindings = {"$A": arg}
    source = instantiate(pattern, bindings)
    target = rewrite(source, law_id)
    if target is None:
        raise ValueError("INVALID_AUTHORED_LAW")
    wrong = ("NOT", target) if law_id == "LAW.NOT.INVOLUTION" else (
        ("AND", arg[0], ("AND", arg[2], arg[1])) if law_id == "LAW.AND.ASSOCIATIVITY"
        else ("NOT", target))
    validate(wrong)
    def record(t, l=law_id):
        return {"task": "law_applies", "law": l, "path": [], "source": source, "target": t}
    rows = [_row(record(target), stage, tier, family + ":positive"),
            _row(record(wrong), stage, tier, family + ":wrong_target")]
    if law_id == "LAW.AND.IDENTITY.RIGHT":
        rows += [_row(record(target, "LAW.NOT.INVOLUTION"), stage, tier, family + ":wrong_law")]
    if law_id == "LAW.AND.ANNIHILATOR.RIGHT":
        rows += [_row(record(target, "LAW.AND.IDENTITY.RIGHT"), stage, tier, family + ":wrong_law")]
    if law_id == "LAW.AND.ASSOCIATIVITY":
        rows += [_row(record(target, "LAW.AND.IDENTITY.RIGHT"), stage, tier, family + ":wrong_law")]
    return rows


def mandatory_train(stage):
    if stage == "F01.NOT":
        return (_eval(stage, app("NOT", "TRUE")) + _eval(stage, app("NOT", "FALSE"))
                + _eval(stage, app("NOT", "P")) + _eval(stage, app("NOT", "Q")))
    if stage == "F02.AND":
        return ([x for a in ("TRUE", "FALSE") for b in ("TRUE", "FALSE")
                 for x in _eval(stage, app("AND", a, b))]
                + _eval(stage, app("AND", "P", "Q")))
    if stage == "F03.NOT_INVOLUTION":
        return _law(stage, "LAW.NOT.INVOLUTION", "P")
    if stage == "F04.AND_IDENTITY":
        return _law(stage, "LAW.AND.IDENTITY.RIGHT", "P")
    if stage == "F05.AND_ANNIHILATOR":
        return _law(stage, "LAW.AND.ANNIHILATOR.RIGHT", "P")
    if stage == "F06.AND_ASSOCIATIVITY":
        return _law(stage, "LAW.AND.ASSOCIATIVITY", ("P", "Q", "R"))
    raise ValueError("UNKNOWN_STAGE")


def _examples(stage, role):
    """Three bounded candidate compositions per stage; only prior primitives used.

    Lesson and exam structures are deliberately different. Their exact records
    must be disjoint. The chosen panel is only additive to mandatory training.
    """
    is_exam = role == "exam"
    if stage == "F01.NOT":
        # One operator has no previously learned connective with which to
        # compose. An invented three-way teacher/exam selection here would be
        # decorative and could test involution before its own law lesson.
        return []
    if stage == "F02.AND":
        if is_exam:
            return [("new P/R operands", _eval(stage, app("AND", "P", "R"), "easy")),
                    ("NOT of R as an AND operand", _eval(stage, app("AND", "P", app("NOT", "R")), "medium")),
                    ("NOT of a composite AND", _eval(stage, app("NOT", app("AND", "Q", "R")), "hard"))]
        return [("Q and P reversed", _eval(stage, app("AND", "Q", "P"), "medium")),
                ("NOT of P in AND", _eval(stage, app("AND", app("NOT", "P"), "Q"), "medium")),
                ("NOT of an AND expression", _eval(stage, app("NOT", app("AND", "P", "Q")), "hard"))]
    law_id = STAGE[stage].new_id
    if stage == "F03.NOT_INVOLUTION":
        subs = [("fresh R", "R"), ("negated R", app("NOT", "R")),
                ("AND containing R", app("AND", "P", "R"))] if is_exam else [
                ("fresh Q", "Q"), ("negated P", app("NOT", "P")),
                ("AND of P and Q", app("AND", "P", "Q"))]
    elif stage in ("F04.AND_IDENTITY", "F05.AND_ANNIHILATOR"):
        subs = [("fresh R", "R"), ("negated R", app("NOT", "R")),
                ("AND of P and R", app("AND", "P", "R"))] if is_exam else [
                ("fresh Q", "Q"), ("negated P", app("NOT", "P")),
                ("AND of P and Q", app("AND", "P", "Q"))]
    else:
        subs = [("negated R", ("P", "Q", app("NOT", "R"))),
                ("negated Q", ("P", app("NOT", "Q"), "R")),
                ("AND compound as third operand", ("P", "Q", app("AND", "R", "P")))] if is_exam else [
                ("negated P", (app("NOT", "P"), "Q", "R")),
                ("AND compound as first operand", (app("AND", "P", "Q"), "Q", "R")),
                ("compound second operand", ("P", app("AND", "Q", "R"), "R"))]
    tiers = ("easy", "medium", "hard")
    return [(label, _law(stage, law_id, s, tier, "law-schema"))
            for tier, (label, s) in zip(tiers, subs)]


def panels(stage, role):
    if stage not in STAGE or role not in ("lesson", "exam"):
        raise ValueError("UNKNOWN_PANEL")
    return tuple(Panel("C" + digest((stage, role, label))[:10], stage, role,
                       "".join((STAGE[stage].teaching_goal, " Candidate: ", label,
                                ". Sample structure: ",
                                expr_pretty(rows[0]["input"].get("source", rows[0]["input"].get("expression"))), ".")),
                       tuple(rows)) for label, rows in _examples(stage, role))


def fixed_gate(stage):
    """Required evidence is independent of which exam composition Kev picks."""
    if stage == "F01.NOT":
        return _eval(stage, app("NOT", "R"), "easy")
    if stage == "F02.AND":
        return (_eval(stage, app("AND", "P", "R"), "easy")
                + _eval(stage, app("AND", "P", app("NOT", "R")), "medium")
                + _eval(stage, app("NOT", app("AND", "Q", "R")), "hard"))
    result = []
    for p in panels(stage, "exam"):
        result.extend(p.rows)
    if stage == "F03.NOT_INVOLUTION":
        # A named law must ALSO transfer into actual evaluation. Do not demand
        # double-negation knowledge during the basic NOT stage.
        result += _eval(stage, app("NOT", app("NOT", "R")), "medium")
        result += _eval(stage, app("NOT", app("NOT", app("NOT", "R"))), "hard")
    return result


def validate_course():
    if tuple(STAGE) != tuple(s.id for s in STAGES):
        raise ValueError("DUPLICATE_STAGE")
    seen = set()
    for stage in STAGES:
        if not set(stage.prerequisite) <= seen:
            raise ValueError("FORWARD_DEPENDENCY")
        train = mandatory_train(stage.id) + [r for p in panels(stage.id, "lesson") for r in p.rows]
        exam = fixed_gate(stage.id)
        if len({r["id"] for r in train}) < len(mandatory_train(stage.id)):
            raise ValueError("DUPLICATE_CORE")
        if {r["id"] for r in train} & {r["id"] for r in exam}:
            raise ValueError("EXAM_LEAKAGE")
        if not any(r["gold"] for r in exam) or not any(not r["gold"] for r in exam):
            raise ValueError("IMBALANCED_GATE")
        seen.add(stage.id)
    return True
