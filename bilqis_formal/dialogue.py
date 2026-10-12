"""Versioned teacher/student protocol. Truth, answers, and feedback are not aliases.

The student's input ends *before* its current answer. Completed prior turns may
contain actual student answers and oracle-checked teacher feedback. This makes
the attention-window treatment distinguishable from ordinary gradient rehearsal.
"""
from __future__ import annotations

from dataclasses import dataclass

from .semantics import TOKENS, TOKEN_ID, encode as encode_v1, evaluate, truth, validate

VERSION = "bilqis.formal.dialogue/v0.2.0"
NEW_TOKENS = (
    "ROLE.TEACHER", "ROLE.STUDENT", "ACT.QUESTION", "ACT.ANSWER",
    "ACT.FEEDBACK", "ACT.CORRECT_ANSWER", "ACT.PROPOSED_ANSWER",
    "ACT.TURN_END", "TASK.JUDGE_ANSWER",
    "FEEDBACK.CORRECT", "FEEDBACK.INCORRECT",
    "PROC.DIALOGUE", "COMP.AND.NOT_RIGHT", "COMP.AND.NOT_LEFT",
    "COMP.NOT.AND",
)
TOKENS_V2 = TOKENS + NEW_TOKENS
IDS = {name: i for i, name in enumerate(TOKENS_V2)}
VALUE_LABELS = ("ATOM.FALSE", "ATOM.TRUE")
JUDGMENT_LABELS = ("FEEDBACK.INCORRECT", "FEEDBACK.CORRECT")
ALL_LABELS = VALUE_LABELS + JUDGMENT_LABELS


def answer_domain(record):
    if record["task"] in ("evaluate", "law_applies"):
        return VALUE_LABELS
    if record["task"] == "judge_answer":
        return JUDGMENT_LABELS
    raise ValueError("UNKNOWN_DIALOGUE_TASK")


def gold_label(record):
    domain = answer_domain(record)
    if record["task"] == "judge_answer":
        if type(record.get("proposed_answer")) is not bool:
            raise ValueError("PROPOSED_ANSWER_NOT_BOOLEAN")
        gold_truth = evaluate(record["expression"], record["valuation"])
        return domain[int(record["proposed_answer"] == gold_truth)]
    return domain[int(truth(record))]


def _question(record):
    kind = record["task"]
    if kind == "judge_answer":
        claimed = record["proposed_answer"]
        if type(claimed) is not bool:
            raise ValueError("PROPOSED_ANSWER_NOT_BOOLEAN")
        base = {"task": "evaluate", "expression": record["expression"],
                "valuation": record["valuation"]}
        return [IDS["TASK.JUDGE_ANSWER"], *encode_v1(base),
                IDS["ACT.PROPOSED_ANSWER"], IDS["ATOM.TRUE" if claimed else "ATOM.FALSE"]]
    return encode_v1(record)


def question_prompt(record):
    return [IDS["ROLE.TEACHER"], IDS["ACT.QUESTION"], *_question(record),
            IDS["ACT.TURN_END"], IDS["ROLE.STUDENT"], IDS["ACT.ANSWER"]]


@dataclass(frozen=True)
class CompletedTurn:
    record: dict
    student_answer: str


def encode_completed(turn: CompletedTurn, *, include_feedback=True):
    domain = answer_domain(turn.record)
    if turn.student_answer not in domain:
        raise ValueError("WRONG_ANSWER_DOMAIN")
    correct = gold_label(turn.record)
    verdict = "FEEDBACK.CORRECT" if turn.student_answer == correct else "FEEDBACK.INCORRECT"
    finished = [*question_prompt(turn.record), IDS[turn.student_answer], IDS["ACT.TURN_END"]]
    if not include_feedback:
        return finished
    finished += [IDS["ROLE.TEACHER"], IDS["ACT.FEEDBACK"], IDS[verdict]]
    if verdict == "FEEDBACK.INCORRECT":
        finished += [IDS["ACT.CORRECT_ANSWER"], IDS[correct]]
    return finished + [IDS["ACT.TURN_END"]]


def encode_prompt(record, history=(), *, context=96, max_turns=3,
                  history_mode="full"):
    """Keep complete most-recent turns, excluding any identical current question.

    No target answer, teacher feedback or current gold appears in the input;
    only *already completed* turns can contain correction information.
    """
    current = question_prompt(record)
    if history_mode not in ("full", "answer_only", "none"):
        raise ValueError("UNKNOWN_HISTORY_MODE")
    if len(current) > context:
        raise ValueError("CURRENT_QUESTION_TOO_LONG")
    chosen = []
    remaining = context - len(current)
    for turn in reversed(tuple(history) if history_mode != "none" else ()):
        if len(chosen) >= max_turns:
            break
        if turn.record == record:
            continue
        segment = encode_completed(turn, include_feedback=history_mode == "full")
        if len(segment) <= remaining:
            chosen.insert(0, segment)
            remaining -= len(segment)
    return [item for segment in chosen for item in segment] + current


def verify_protocol():
    if len(TOKENS_V2) != len(set(TOKENS_V2)):
        raise ValueError("TOKEN_COLLISION")
    for t in ({"task": "evaluate", "expression": "FALSE", "valuation": {}},
              {"task": "evaluate", "expression": "TRUE", "valuation": {}}):
        if gold_label(t) not in VALUE_LABELS:
            raise ValueError("BAD_TRUTH_DOMAIN")
        for a in (False, True):
            judge = {**t, "task": "judge_answer", "proposed_answer": a}
            if gold_label(judge) not in JUDGMENT_LABELS:
                raise ValueError("BAD_VERDICT_DOMAIN")
    return True
