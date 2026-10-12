"""v0.3: the student learns truth functions before grading proposed answers.

Teacher feedback is present from the first lesson, but it is *not* an early
student answer target. All mathematical labels come from the Boolean oracle.
The human-authored dependency graph is explicit and versioned separately
from the older v0.1/v0.2 experimental curricula.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from .semantics import app, canonical, digest, evaluate, variables
from .dialogue_v3 import answer_domain, gold_label

VERSION = "bilqis.formal.course/v0.3.0"


@dataclass(frozen=True)
class Stage:
    id: str
    prerequisite: tuple[str, ...]
    semantic_id: str
    objective: str
    tier: str
    student_task: str = "evaluate"


STAGES = (
    Stage("V00.BOOLEAN", (), "ATOM.TRUE_FALSE",
          "Recognize Boolean TRUE/FALSE and atomic valuations; teacher supplies feedback.", "foundation"),
    Stage("V01.NOT", ("V00.BOOLEAN",), "OP.NOT",
          "Evaluate NOT for both truth values, independently of grading anybody else's answer.", "atomic"),
    Stage("V02.AND", ("V00.BOOLEAN",), "OP.AND",
          "Evaluate all four AND truth cases without judging proposed answers.", "atomic"),
    Stage("V03.AND_NOT_RIGHT", ("V01.NOT", "V02.AND"), "COMP.AND.NOT_RIGHT",
          "Evaluate a conjunction with a negated right operand.", "medium"),
    Stage("V04.AND_NOT_LEFT", ("V01.NOT", "V02.AND"), "COMP.AND.NOT_LEFT",
          "Evaluate a conjunction with a negated left operand.", "medium"),
    Stage("V05.NOT_AND", ("V01.NOT", "V02.AND"), "COMP.NOT.AND",
          "Evaluate negation of the whole conjunction.", "hard"),
    Stage("J00.PROPOSED_ANSWER",
          ("V00.BOOLEAN", "V01.NOT", "V02.AND", "V03.AND_NOT_RIGHT",
           "V04.AND_NOT_LEFT", "V05.NOT_AND"),
          "TASK.JUDGE_ANSWER",
          "New metacognitive task: independently judge another proposed Boolean answer.",
          "metacognitive", "judge_answer"),
)
STAGE = {s.id: s for s in STAGES}


def missing_prerequisites(stage, admitted):
    """The graph, not a loop position, decides which work is legally teachable."""
    return tuple(x for x in STAGE[stage].prerequisite if x not in admitted)


@dataclass(frozen=True)
class Panel:
    id: str
    stage: str
    role: str
    tier: str
    structure: str
    axis: str
    description: str
    rows: tuple[dict, ...]


def row(stage, expression, env, role, proposed=None):
    task = STAGE[stage].student_task
    record = {"task": task, "expression": expression, "valuation": dict(env)}
    if task == "judge_answer":
        if type(proposed) is not bool:
            raise ValueError("PROPOSED_ANSWER_REQUIRED")
        record["proposed_answer"] = proposed
    item = {"id": digest(record), "input": record, "gold": gold_label(record),
            "stage": stage, "family": STAGE[stage].semantic_id,
            "tier": STAGE[stage].tier, "role": role}
    return item


def truth_rows(stage, expression, role):
    names = sorted(variables(expression))
    records = []
    for vals in product((False, True), repeat=len(names)):
        env = dict(zip(names, vals))
        if STAGE[stage].student_task == "judge_answer":
            records.extend(row(stage, expression, env, role, claimed)
                           for claimed in (False, True))
        else:
            records.append(row(stage, expression, env, role))
    return records


def expression(stage, symbols):
    if stage == "V02.AND":
        return app("AND", *symbols)
    if stage == "V03.AND_NOT_RIGHT":
        return app("AND", symbols[0], app("NOT", symbols[1]))
    if stage == "V04.AND_NOT_LEFT":
        return app("AND", app("NOT", symbols[0]), symbols[1])
    if stage == "V05.NOT_AND":
        return app("NOT", app("AND", *symbols))
    raise ValueError("NOT_A_COMPOSITION")


def mandatory_train(stage):
    if stage == "V00.BOOLEAN":
        return (truth_rows(stage, "TRUE", "train") +
                truth_rows(stage, "FALSE", "train") +
                truth_rows(stage, "P", "train"))
    if stage == "V01.NOT":
        return (truth_rows(stage, app("NOT", "P"), "train") +
                truth_rows(stage, app("NOT", "Q"), "train"))
    if stage == "V02.AND":
        return (truth_rows(stage, expression(stage, ("P", "Q")), "train") +
                [row(stage, app("AND", a, b), {}, "train")
                 for a, b in product(("TRUE", "FALSE"), repeat=2)])
    if stage in ("V03.AND_NOT_RIGHT", "V04.AND_NOT_LEFT", "V05.NOT_AND"):
        return truth_rows(stage, expression(stage, ("P", "Q")), "train")
    if stage == "J00.PROPOSED_ANSWER":
        return (truth_rows(stage, "P", "train") +
                truth_rows(stage, app("NOT", "P"), "train") +
                truth_rows(stage, app("AND", "P", "Q"), "train") +
                [r for operator in ("V03.AND_NOT_RIGHT", "V04.AND_NOT_LEFT",
                                    "V05.NOT_AND")
                 for r in truth_rows(stage, expression(operator, ("P", "Q")), "train")])
    raise ValueError("UNKNOWN_STAGE")


def fixed_gate(stage):
    """Sealed, deterministic, oracle-checked, never selected by a teacher."""
    if stage == "V00.BOOLEAN":
        return truth_rows(stage, "R", "gate") + truth_rows(stage, "Q", "gate")
    if stage == "V01.NOT":
        return (truth_rows(stage, app("NOT", "R"), "gate") +
                truth_rows(stage, app("NOT", "TRUE"), "gate") +
                truth_rows(stage, app("NOT", "FALSE"), "gate"))
    if stage == "V02.AND":
        return truth_rows(stage, expression(stage, ("R", "Q")), "gate")
    if stage in ("V03.AND_NOT_RIGHT", "V04.AND_NOT_LEFT", "V05.NOT_AND"):
        return truth_rows(stage, expression(stage, ("R", "P")), "gate")
    if stage == "J00.PROPOSED_ANSWER":
        return (truth_rows(stage, "R", "gate") +
                truth_rows(stage, app("NOT", "R"), "gate") +
                truth_rows(stage, app("AND", "R", "Q"), "gate") +
                [r for operator in ("V03.AND_NOT_RIGHT", "V04.AND_NOT_LEFT",
                                    "V05.NOT_AND")
                 for r in truth_rows(stage, expression(operator, ("R", "Q")), "gate")])
    raise ValueError("UNKNOWN_STAGE")


def structural_transfer_probe(stage):
    """Frozen post-gate diagnostic only, not a progression or teacher input.

    Tests mixed constants/variables at new AST shapes. Failure does not
    silently add unlearned structure to a stage's admission criteria.
    """
    cases = {
        "V02.AND": (app("AND", "TRUE", "R"), app("AND", "FALSE", "R")),
        "V03.AND_NOT_RIGHT": (
            app("AND", "TRUE", app("NOT", "R")),
            app("AND", "R", app("NOT", "FALSE"))),
        "V04.AND_NOT_LEFT": (
            app("AND", app("NOT", "R"), "TRUE"),
            app("AND", app("NOT", "FALSE"), "R")),
        "V05.NOT_AND": (
            app("NOT", app("AND", "TRUE", "R")),
            app("NOT", app("AND", "R", "FALSE"))),
        "J00.PROPOSED_ANSWER": (
            app("AND", "TRUE", "R"),
            app("NOT", app("AND", "R", "FALSE"))),
    }
    return [row for expr in cases.get(stage, ()) for row in truth_rows(
        stage, expr, "structural_diagnostic")]


def shape(expr):
    if isinstance(expr, str):
        return "v" if expr in ("P", "Q", "R") else expr
    return expr[0] + "(" + ",".join(shape(v) for v in expr[1:]) + ")"


def contrast(expr, axis):
    names = sorted(variables(expr))
    if len(names) != 2 or axis not in names:
        raise ValueError("BAD_CONTRAST_AXIS")
    cases = [(dict(zip(names, vals)), evaluate(expr, dict(zip(names, vals))))
             for vals in product((False, True), repeat=2)]
    pairs = [(left, right) for left, a in cases for right, b in cases
             if a and not b and sum(left[n] != right[n] for n in names) == 1
             and left[axis] != right[axis]]
    if not pairs:
        raise ValueError("NO_DISCRIMINATING_PAIR")
    return sorted(pairs, key=lambda pair: tuple(pair[0][n] for n in names))[0]


def panels(stage, role):
    if stage not in STAGE or role not in ("lesson", "exam"):
        raise ValueError("UNKNOWN_PANEL")
    if stage not in ("V03.AND_NOT_RIGHT", "V04.AND_NOT_LEFT", "V05.NOT_AND"):
        return ()  # No nontrivial and comparable teacher decision yet.
    symbols = ("Q", "P") if role == "lesson" else ("Q", "R")
    expr = expression(stage, symbols)
    result = []
    for axis in sorted(variables(expr)):
        positive, negative = contrast(expr, axis)
        rows = tuple(row(stage, expr, vals, role) for vals in (positive, negative))
        result.append(Panel(
            "C" + digest((VERSION, stage, role, shape(expr), axis))[:12],
            stage, role, STAGE[stage].tier, shape(expr), axis,
            f"Same expression shape {shape(expr)}; vary only {axis}. "
            "Two cases: one TRUE, one FALSE. Both are oracle-checked.",
            rows))
    return tuple(result)


def validate_panels(stage, role, offered):
    if len(offered) != 2:
        raise ValueError("MISSING_COMPARABLE_ALTERNATIVES")
    reference = offered[0]
    ids = set()
    axes = set()
    expected_expr = expression(stage, ("Q", "P") if role == "lesson" else ("Q", "R"))
    for item in offered:
        if item.id in ids or (item.stage, item.role, item.tier, item.structure) != (
                stage, role, STAGE[stage].tier, reference.structure):
            raise ValueError("MIXED_PANEL")
        ids.add(item.id)
        if item.axis in axes or item.axis not in variables(expected_expr):
            raise ValueError("DUPLICATED_OR_UNKNOWN_AXIS")
        axes.add(item.axis)
        if item.id != "C" + digest((VERSION, stage, role, shape(expected_expr), item.axis))[:12]:
            raise ValueError("PANEL_IDENTITY_CHANGED")
        if len(item.rows) != 2 or {r["gold"] for r in item.rows} != {
                "ATOM.FALSE", "ATOM.TRUE"}:
            raise ValueError("UNBALANCED_TRUTH_CONTRAST")
        if any(r["input"]["task"] != "evaluate" or r["stage"] != stage or r["role"] != role
               or r["family"] != STAGE[stage].semantic_id or r["tier"] != STAGE[stage].tier
               or canonical(r["input"]["expression"]) != canonical(expected_expr)
               or r["gold"] != gold_label(r["input"])
               or r["id"] != digest(r["input"])
               for r in item.rows):
            raise ValueError("WRONG_PANEL_COMPETENCY")
        a, b = [r["input"]["valuation"] for r in item.rows]
        if sum(a[name] != b[name] for name in a) != 1 or a[item.axis] == b[item.axis]:
            raise ValueError("UNMATCHED_CONTRAST")
    return True


def validate_course():
    seen = set()
    for s in STAGES:
        if s.id in seen or not set(s.prerequisite) <= seen:
            raise ValueError("BAD_PREREQUISITE_DAG")
        train, gate = mandatory_train(s.id), fixed_gate(s.id)
        lesson, exam = panels(s.id, "lesson"), panels(s.id, "exam")
        diagnostic = structural_transfer_probe(s.id)
        if lesson:
            validate_panels(s.id, "lesson", lesson)
            validate_panels(s.id, "exam", exam)
        bundles = [
            {r["id"] for r in train},
            {r["id"] for p in lesson for r in p.rows},
            {r["id"] for p in exam for r in p.rows},
            {r["id"] for r in gate},
            {r["id"] for r in diagnostic},
        ]
        if any(bundles[i] & bundles[j] for i in range(len(bundles))
               for j in range(i + 1, len(bundles))):
            raise ValueError("TRAIN_EXAM_GATE_OVERLAP")
        for r in train + gate + diagnostic + [x for p in lesson + exam for x in p.rows]:
            if r["input"]["task"] != s.student_task or r["gold"] != gold_label(r["input"]):
                raise ValueError("WRONG_STUDENT_TASK_OR_ORACLE")
            if r["gold"] not in answer_domain(r["input"]):
                raise ValueError("WRONG_OUTPUT_DOMAIN")
        if s.id != "J00.PROPOSED_ANSWER" and any(
                r["input"]["task"] == "judge_answer" for r in train + gate):
            raise ValueError("PREMATURE_METACOGNITION")
        seen.add(s.id)
    return True
