"""v0.3 typed teaching dialogue.

Teacher FEEDBACK.CORRECT/INCORRECT always denotes the oracle's assessment of
the student's previous prediction. JUDGMENT.CORRECT/INCORRECT is a *different*
student-answer domain, first introduced in downstream metacognitive training.
No teacher feedback for the current question is placed in its input.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .dialogue import TOKENS_V2, question_prompt
from .semantics import evaluate, truth

VERSION = "bilqis.formal.dialogue/v0.3.0"
TOKENS_V3 = TOKENS_V2 + ("JUDGMENT.INCORRECT", "JUDGMENT.CORRECT")
IDS = {token: i for i, token in enumerate(TOKENS_V3)}
TRUTH_LABELS = ("ATOM.FALSE", "ATOM.TRUE")
JUDGMENT_LABELS = ("JUDGMENT.INCORRECT", "JUDGMENT.CORRECT")
STUDENT_LABELS = TRUTH_LABELS + JUDGMENT_LABELS


@dataclass(frozen=True)
class CompletedTurn:
    record: dict
    student_answer: str


def answer_domain(record):
    if record["task"] in ("evaluate", "law_applies"):
        return TRUTH_LABELS
    if record["task"] == "judge_answer":
        return JUDGMENT_LABELS
    raise ValueError("UNKNOWN_STUDENT_TASK")


def gold_label(record):
    task = record["task"]
    if task == "judge_answer":
        if type(record.get("proposed_answer")) is not bool:
            raise ValueError("PROPOSED_ANSWER_MUST_BE_BOOLEAN")
        expected = evaluate(record["expression"], record["valuation"])
        return JUDGMENT_LABELS[int(expected == record["proposed_answer"])]
    return TRUTH_LABELS[int(truth(record))]


def encode_completed(turn, *, include_feedback=True, pad_absent=False):
    if turn.student_answer not in answer_domain(turn.record):
        raise ValueError("BAD_STUDENT_ANSWER_DOMAIN")
    correct = gold_label(turn.record)
    is_correct = turn.student_answer == correct
    prefix = [*question_prompt(turn.record), IDS[turn.student_answer], IDS["ACT.TURN_END"]]
    teacher = [IDS["ROLE.TEACHER"], IDS["ACT.FEEDBACK"],
               IDS["FEEDBACK.CORRECT" if is_correct else "FEEDBACK.INCORRECT"]]
    if not is_correct:
        teacher += [IDS["ACT.CORRECT_ANSWER"], IDS[correct]]
    else:
        # Fix each turn's length independently of the oracle verdict.
        # A PAD-only control must not reveal correctness through pad count.
        teacher += [IDS["SYNTAX.PAD"], IDS["SYNTAX.PAD"]]
    teacher.append(IDS["ACT.TURN_END"])
    if include_feedback:
        return prefix + teacher
    if pad_absent:
        return prefix + [IDS["SYNTAX.PAD"]] * len(teacher)
    return prefix


def encode_prompt(record, history=(), *, context=96, max_turns=3, mode="full"):
    if mode not in ("full", "answer_only", "answer_only_padded", "none"):
        raise ValueError("BAD_CONTEXT_MODE")
    current = question_prompt(record)
    if len(current) > context:
        raise ValueError("CURRENT_QUESTION_EXCEEDS_CONTEXT")
    selected = []
    remaining = context - len(current)
    for turn in reversed(tuple(history) if mode != "none" else ()):
        if len(selected) == max_turns:
            break
        if turn.record == record:
            continue  # Previously answered copy of the *current* question is excluded.
        fragment = encode_completed(
            turn, include_feedback=mode == "full",
            pad_absent=mode == "answer_only_padded")
        if len(fragment) <= remaining:
            selected.insert(0, fragment)
            remaining -= len(fragment)
    return [token for item in selected for token in item] + current


def paired_valid_primers(rows):
    """Fixed valid opposite-answer corrections, selected from training rows only.

    Selection is made without reference to the held-out question or its gold.
    Consequently each primer is used for *every* held-out item, rather than
    selecting the 'helpful' primer by peeking at that item's true answer.
    """
    grouped = {}
    for item in rows:
        record = item["input"]
        key = json.dumps((record["task"], record.get("expression")),
                         sort_keys=True, separators=(",", ":"))
        grouped.setdefault(key, []).append(item)
    for group in grouped.values():
        for a in group:
            for b in group:
                if a["gold"] == b["gold"]:
                    continue
                ta = CompletedTurn(a["input"],
                                   next(x for x in answer_domain(a["input"]) if x != a["gold"]))
                tb = CompletedTurn(b["input"],
                                   next(x for x in answer_domain(b["input"]) if x != b["gold"]))
                if len(encode_completed(ta)) == len(encode_completed(tb)):
                    assert a["input"] != b["input"]
                    return ta, tb
    raise ValueError("NO_EQUAL_LENGTH_OPPOSITE_LABEL_PRIMERS")


def counterfactual_feedback_prompt(record, historical_turn, *, context=96):
    """Read-only adversarial probe: contradict a past CORRECT_ANSWER token.

    This constructs one knowingly invalid teacher correction only to measure
    model sensitivity. It must NEVER be a teaching input, gold label,
    promotion condition, or Kev candidate. The current question is unchanged.
    """
    seq = encode_prompt(record, [historical_turn], context=context, mode="full")
    marker = IDS["ACT.CORRECT_ANSWER"]
    if marker not in seq:
        raise ValueError("COUNTERFACTUAL_REQUIRES_WRONG_PRIOR_ANSWER")
    index = seq.index(marker) + 1
    proper = gold_label(historical_turn.record)
    if seq[index] != IDS[proper]:
        raise ValueError("SOURCE_TEACHER_CORRECTION_WAS_NOT_ORACLE_VALID")
    opposite = next(x for x in answer_domain(historical_turn.record) if x != proper)
    altered = list(seq)
    altered[index] = IDS[opposite]
    assert len(seq) == len(altered)
    assert seq[-len(question_prompt(record)):] == altered[-len(question_prompt(record)):]
    return seq, altered


def verify_protocol():
    if len(TOKENS_V3) != len(set(TOKENS_V3)):
        raise ValueError("DUPLICATED_SEMANTIC_TOKEN")
    if IDS["FEEDBACK.CORRECT"] == IDS["JUDGMENT.CORRECT"]:
        raise ValueError("TEACHER_STUDENT_ROLE_COLLISION")
    for expected in (False, True):
        for proposed in (False, True):
            case = {"task": "judge_answer", "expression": "TRUE" if expected else "FALSE",
                    "valuation": {}, "proposed_answer": proposed}
            if gold_label(case) != ("JUDGMENT.CORRECT" if expected == proposed
                                    else "JUDGMENT.INCORRECT"):
                raise ValueError("BAD_JUDGMENT_ORACLE")
            if gold_label({**case, "task": "evaluate"}) not in TRUTH_LABELS:
                raise ValueError("BAD_TRUTH_ORACLE")
    return True
