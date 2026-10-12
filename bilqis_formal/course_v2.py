"""Chat-authored, versioned logical prerequisites and matched Kev candidate panels.

The human curriculum owns the target/required tier. Kev cannot trade a
compositional competency for a simpler one or reclassify exercise difficulty.
These tiers are structural hypotheses, not calibrated psychometric difficulty.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from .dialogue import gold_label
from .semantics import app, digest, evaluate, variables

VERSION = "bilqis.formal.course/v0.2.0"


@dataclass(frozen=True)
class Stage:
    id: str
    prerequisite: tuple[str, ...]
    semantic_id: str
    competency: str
    tier: str


STAGES = (
    Stage("D00.PROTOCOL", (), "PROC.DIALOGUE",
          "Separate Boolean truth values from correct/incorrect judgments and learn question/answer/feedback turns.", "foundation"),
    Stage("D01.NOT", ("D00.PROTOCOL",), "OP.NOT",
          "Evaluate and judge the atomic NOT truth function.", "atomic"),
    Stage("D02.AND", ("D00.PROTOCOL",), "OP.AND",
          "Evaluate and judge all four atomic AND truth cases.", "atomic"),
    Stage("D03.AND_NOT_RIGHT", ("D01.NOT", "D02.AND"), "COMP.AND.NOT_RIGHT",
          "Compose AND with NOT on the right operand, including the rare TRUE case.", "medium"),
    Stage("D04.AND_NOT_LEFT", ("D01.NOT", "D02.AND"), "COMP.AND.NOT_LEFT",
          "Compose AND with NOT on the left operand, including the rare TRUE case.", "medium"),
    Stage("D05.NOT_AND", ("D02.AND", "D01.NOT"), "COMP.NOT.AND",
          "Apply NOT to the whole conjunction, not merely one operand.", "hard"),
)
STAGE = {s.id: s for s in STAGES}
BY_SEMANTIC = {s.semantic_id: s.id for s in STAGES}


@dataclass(frozen=True)
class Panel:
    id: str
    stage: str
    role: str
    semantic_id: str
    tier: str
    structure: str
    axis: str
    description: str
    rows: tuple[dict, ...]


def _row(record, stage, role):
    return {"id": digest(record), "input": record, "gold": gold_label(record),
            "stage": stage, "tier": STAGE[stage].tier,
            "family": STAGE[stage].semantic_id, "role": role}


def _single(stage, expr, valuation, role, *, both_judgments=True):
    base = {"task": "evaluate", "expression": expr, "valuation": dict(valuation)}
    out = [_row(base, stage, role)]
    if both_judgments:
        for proposed in (False, True):
            out.append(_row({**base, "task": "judge_answer", "proposed_answer": proposed}, stage, role))
    return out


def truth_rows(stage, expr, role, *, judgments=True):
    names = sorted(variables(expr))
    return [r for values in product((False, True), repeat=len(names))
            for r in _single(stage, expr, dict(zip(names, values)), role, both_judgments=judgments)]


def _expr(stage, variant):
    if stage == "D02.AND":
        return app("AND", *variant)
    if stage == "D03.AND_NOT_RIGHT":
        return app("AND", variant[0], app("NOT", variant[1]))
    if stage == "D04.AND_NOT_LEFT":
        return app("AND", app("NOT", variant[0]), variant[1])
    if stage == "D05.NOT_AND":
        return app("NOT", app("AND", *variant))
    raise ValueError("NO_COMPOSITION_FOR_STAGE")


def mandatory_train(stage):
    if stage == "D00.PROTOCOL":
        return (truth_rows(stage, "TRUE", "train")
                + truth_rows(stage, "FALSE", "train")
                + truth_rows(stage, "P", "train"))
    if stage == "D01.NOT":
        return (truth_rows(stage, app("NOT", "P"), "train")
                + truth_rows(stage, app("NOT", "Q"), "train"))
    if stage == "D02.AND":
        return (truth_rows(stage, _expr(stage, ("P", "Q")), "train")
                + [_row({"task": "evaluate", "expression": app("AND", a, b), "valuation": {}},
                        stage, "train") for a, b in product(("TRUE", "FALSE"), repeat=2)])
    if stage == "D03.AND_NOT_RIGHT":
        pairs = [("TRUE", "FALSE"), ("FALSE", "FALSE"), ("TRUE", "TRUE")]
    elif stage == "D04.AND_NOT_LEFT":
        pairs = [("FALSE", "TRUE"), ("TRUE", "TRUE"), ("FALSE", "FALSE")]
    elif stage == "D05.NOT_AND":
        pairs = [("TRUE", "FALSE"), ("TRUE", "TRUE"), ("FALSE", "TRUE")]
    else:
        raise ValueError("UNKNOWN_STAGE")
    return [r for pair in pairs for r in _single(stage, _expr(stage, pair), {}, "train")]


def fixed_gate(stage):
    """Never exposed to Kev, teacher selection, gradient data, or remediation."""
    if stage == "D00.PROTOCOL":
        return truth_rows(stage, "R", "gate") + truth_rows(stage, "Q", "gate")
    if stage == "D01.NOT":
        return truth_rows(stage, app("NOT", "R"), "gate")
    if stage == "D02.AND":
        return truth_rows(stage, _expr(stage, ("R", "Q")), "gate")
    return truth_rows(stage, _expr(stage, ("R", "P")), "gate")


def _shape(expr):
    if isinstance(expr, str):
        return "v" if expr in ("P", "Q", "R") else expr
    return expr[0] + "(" + ",".join(_shape(e) for e in expr[1:]) + ")"


def _contrast(stage, expression, axis):
    """Two cases, one TRUE and one FALSE, differing at exactly one valuation bit."""
    names = sorted(variables(expression))
    if len(names) != 2 or axis not in names:
        raise ValueError("CONTRAST_AXIS")
    outcomes = []
    for values in product((False, True), repeat=2):
        env = dict(zip(names, values))
        outcomes.append((env, evaluate(expression, env)))
    opposites = [(a, b) for a, v in outcomes for b, w in outcomes
                 if v and not w and sum(a[n] != b[n] for n in names) == 1
                 and a[axis] != b[axis]]
    if not opposites:
        raise ValueError("NO_MATCHED_CONTRAST")
    # Stable, declared contrast; not chosen by an LLM or a hidden model score.
    return sorted(opposites, key=lambda pair: tuple(pair[0][n] for n in names))[0]


def panels(stage, role):
    if stage not in STAGE or role not in ("lesson", "exam"):
        raise ValueError("UNKNOWN_STAGE_OR_ROLE")
    if stage in ("D00.PROTOCOL", "D01.NOT", "D02.AND"):
        return ()  # No meaningful pretrained teacher comparison yet.
    operands = ("P", "Q") if role == "lesson" else ("Q", "R")
    expression = _expr(stage, operands)
    result = []
    for axis in sorted(variables(expression)):
        positive, negative = _contrast(stage, expression, axis)
        rows = tuple(r for env in (positive, negative)
                     for r in _single(stage, expression, env, role))
        panel = Panel(
            "C" + digest((VERSION, stage, role, _shape(expression), axis))[:12],
            stage, role, STAGE[stage].semantic_id, STAGE[stage].tier, _shape(expression),
            axis, f"Matched pair in {_shape(expression)}: change only variable {axis}; "
                  f"one TRUE and one FALSE; three task records per valuation.",
            rows,
        )
        result.append(panel)
    return tuple(result)


def validate_panels(stage, role, candidates):
    if not 2 <= len(candidates) <= 8:
        raise ValueError("UNCOMPARABLE_PANEL_COUNT")
    expected = STAGE[stage]
    reference = candidates[0]
    ids = set()
    for p in candidates:
        if p.id in ids or (p.stage, p.role, p.semantic_id, p.tier, p.structure) != (
                stage, role, expected.semantic_id, expected.tier, reference.structure):
            raise ValueError("UNCOMPARABLE_PANEL")
        ids.add(p.id)
        if len(p.rows) != len(reference.rows) or len(p.rows) != 6:
            raise ValueError("UNBALANCED_CONTRAST_SIZE")
        if any(r["stage"] != stage or r["role"] != role or r["family"] != expected.semantic_id
               or r["tier"] != expected.tier for r in p.rows):
            raise ValueError("PANEL_ROW_PROVENANCE")
        if {r["gold"] for r in p.rows if r["input"]["task"] == "evaluate"} != {
                "ATOM.TRUE", "ATOM.FALSE"}:
            raise ValueError("CONTRAST_LACKS_BOTH_TRUTHS")
        if {r["gold"] for r in p.rows if r["input"]["task"] == "judge_answer"} != {
                "FEEDBACK.CORRECT", "FEEDBACK.INCORRECT"}:
            raise ValueError("CONTRAST_LACKS_BOTH_VERDICTS")
    return True


def validate_course():
    seen = set()
    for stage in STAGES:
        if stage.id in seen or not set(stage.prerequisite) <= seen:
            raise ValueError("BAD_PREREQUISITE_GRAPH")
        mandatory, gate = mandatory_train(stage.id), fixed_gate(stage.id)
        lesson, exam = panels(stage.id, "lesson"), panels(stage.id, "exam")
        if lesson:
            validate_panels(stage.id, "lesson", lesson)
            validate_panels(stage.id, "exam", exam)
        grouped = [[r["id"] for r in mandatory],
                   [r["id"] for p in lesson for r in p.rows],
                   [r["id"] for p in exam for r in p.rows],
                   [r["id"] for r in gate]]
        if set(grouped[3]) & (set(grouped[0]) | set(grouped[1]) | set(grouped[2])):
            raise ValueError("SEALED_GATE_REUSED")
        if set(grouped[2]) & (set(grouped[0]) | set(grouped[1])):
            raise ValueError("FORMATIVE_REUSED_FOR_TRAINING")
        if set(grouped[0]) & set(grouped[1]):
            raise ValueError("SELECTED_LESSON_DUPLICATES_CORE")
        for r in mandatory + gate + [x for p in lesson + exam for x in p.rows]:
            if r["gold"] != gold_label(r["input"]):
                raise ValueError("NON_ORACLE_LABEL")
        seen.add(stage.id)
    return True
