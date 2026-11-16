"""Immutable championship history plus evolving per-capability defense batteries."""
from __future__ import annotations

import json

from bilqis_mlx.generated_assessment import digest
from .championship_policy import CONTEXT_KEYS


SCHEMA = "bilqis.mlx.championship-questions/v1"
BATTERY_SCHEMA = "bilqis.mlx.championship-defense-battery/v1"
COHORT_RUBRIC_KEY = "cohort_rubric_sha256"


def _context_payload(context: dict) -> dict:
    payload = {key: context[key] for key in CONTEXT_KEYS}
    cohort_rubric = context.get(COHORT_RUBRIC_KEY)
    if cohort_rubric is not None:
        if not isinstance(cohort_rubric, str) or len(cohort_rubric) != 64:
            raise ValueError("CHAMPIONSHIP_COHORT_RUBRIC_IDENTITY_DRIFT")
        payload[COHORT_RUBRIC_KEY] = cohort_rubric
    if "complete_solver_provenance" in context:
        provenance = context["complete_solver_provenance"]
        if (not isinstance(provenance, dict)
                or provenance.get("schema_version") != "bilqis.c05.complete-solver-provenance/v1"
                or any(not isinstance(provenance.get(key), str)
                       or len(provenance[key]) != 64
                       for key in ("generation_digest", "weight_sha256"))
                or not isinstance(provenance.get("solver_contracts"), (tuple, list))
                or not provenance["solver_contracts"]
                or any(not isinstance(value, str) or len(value) != 64
                       for value in provenance["solver_contracts"])):
            raise ValueError("CHAMPIONSHIP_COMPLETE_SOLVER_PROVENANCE_INVALID")
        payload["complete_solver_provenance"] = provenance
    return payload


def _context_identity(context: dict) -> tuple:
    payload = _context_payload(context)
    return (
        *(payload[key] for key in CONTEXT_KEYS),
        COHORT_RUBRIC_KEY in payload,
        payload.get(COHORT_RUBRIC_KEY),
        "complete_solver_provenance" in payload,
        json.dumps(payload.get("complete_solver_provenance"), sort_keys=True, separators=(",", ":")),
    )


def _context_from_identity(identity: tuple) -> dict:
    core = dict(zip(CONTEXT_KEYS, identity[:len(CONTEXT_KEYS)]))
    present, value, solver_present, solver_json = identity[len(CONTEXT_KEYS):]
    if present:
        core[COHORT_RUBRIC_KEY] = value
    if solver_present:
        core["complete_solver_provenance"] = json.loads(solver_json)
    return core


def earning_witness(exam: dict, capabilities) -> dict:
    """Preserve the complete question sets used to earn this title."""
    questions, perfect = [], []
    for capability in sorted(set(capabilities)):
        score = exam["scores"][capability]
        correct = exam["correct_questions"][capability]
        offered = exam["questions"][capability]
        if (len(offered) != score["total"] or len(correct) != score["correct"] or
                not {q["id"] for q in correct} <= {q["id"] for q in offered} or
                not 0 <= len(correct) <= score["total"] or score["total"] < 1):
            raise ValueError("CHAMPIONSHIP_QUESTION_SCORE_DRIFT")
        questions.extend({**question, "capability": capability} for question in offered)
        if len(correct) == score["total"]:
            perfect.append(capability)
    if (len({q["id"] for q in questions}) != len(questions) or
            any(not q.get("id") or not isinstance(q.get("gold"), str) for q in questions)):
        raise ValueError("CHAMPIONSHIP_QUESTION_IDENTITY_DRIFT")
    payload = {"schema": SCHEMA,
               **_context_payload(exam),
               "questions": sorted(questions, key=lambda q: q["id"]),
               "capabilities": sorted(set(capabilities)),
               "perfect_capabilities": perfect}
    return {**payload, "sha256": digest(payload)}


def verified_witnesses(role: dict) -> tuple[dict, ...]:
    witnesses = tuple(role.get("qualification_witnesses", ()))
    for witness in witnesses:
        payload = {k: v for k, v in witness.items() if k != "sha256"}
        if (payload.get("schema") != SCHEMA or digest(payload) != witness.get("sha256") or
                any(not isinstance(payload.get(key), str) or len(payload[key]) != 64
                    for key in CONTEXT_KEYS)):
            raise ValueError("CHAMPIONSHIP_QUESTION_WITNESS_DRIFT")
        if (COHORT_RUBRIC_KEY in payload and
                (not isinstance(payload[COHORT_RUBRIC_KEY], str) or
                 len(payload[COHORT_RUBRIC_KEY]) != 64)):
            raise ValueError("CHAMPIONSHIP_QUESTION_WITNESS_DRIFT")
    return witnesses


def _battery_segment(context: dict, questions) -> dict:
    unique = {}
    for question in questions:
        if (not isinstance(question, dict) or not isinstance(question.get("id"), str) or
                not question["id"] or not isinstance(question.get("gold"), str) or
                not isinstance(question.get("capability"), str)):
            raise ValueError("CHAMPIONSHIP_BATTERY_QUESTION_INVALID")
        key = question["id"]
        former = unique.setdefault(key, dict(question))
        if former != question:
            raise ValueError("CHAMPIONSHIP_BATTERY_QUESTION_DRIFT")
    payload = {
        "schema": BATTERY_SCHEMA,
        **_context_payload(context),
        "questions": sorted(unique.values(), key=lambda q: q["id"]),
    }
    return {**payload, "sha256": digest(payload)}


def _dedup_battery_segments(segments) -> tuple[dict, ...]:
    """Canonicalize the active battery as one global question-identity set."""
    chosen = {}
    by_context = {}
    context_order = []
    for segment in segments:
        context = _context_identity(segment)
        if context not in by_context:
            by_context[context] = []
            context_order.append(context)
        for question in segment["questions"]:
            identity = question["id"]
            prior = chosen.get(identity)
            if prior is not None:
                if prior != question:
                    raise ValueError("CHAMPIONSHIP_BATTERY_QUESTION_DRIFT")
                continue
            chosen[identity] = question
            by_context[context].append(question)
    return tuple(
        _battery_segment(_context_from_identity(context), questions)
        for context in context_order if (questions := by_context[context]))


def verified_battery(role: dict) -> tuple[dict, ...]:
    """Return the active per-capability title battery, migrating old witnesses lazily."""
    stored = role.get("surviving_battery")
    if stored is None:
        migrated = []
        capability = role.get("capability")
        for witness in verified_witnesses(role):
            if capability not in witness.get("capabilities", ()):
                continue
            migrated.append(_battery_segment(
                witness, (question for question in witness["questions"]
                          if question.get("capability") == capability)))
        stored = migrated
    if not isinstance(stored, (list, tuple)):
        raise ValueError("CHAMPIONSHIP_BATTERY_INVALID")
    result = []
    seen = set()
    for segment in stored:
        if not isinstance(segment, dict):
            raise ValueError("CHAMPIONSHIP_BATTERY_INVALID")
        payload = {key: value for key, value in segment.items() if key != "sha256"}
        if (payload.get("schema") != BATTERY_SCHEMA or
                digest(payload) != segment.get("sha256") or
                any(not isinstance(payload.get(key), str) or len(payload[key]) != 64
                    for key in CONTEXT_KEYS)):
            raise ValueError("CHAMPIONSHIP_BATTERY_DRIFT")
        if (COHORT_RUBRIC_KEY in payload and
                (not isinstance(payload[COHORT_RUBRIC_KEY], str) or
                 len(payload[COHORT_RUBRIC_KEY]) != 64)):
            raise ValueError("CHAMPIONSHIP_BATTERY_DRIFT")
        for question in payload.get("questions", ()):
            if (not isinstance(question, dict) or not question.get("id") or
                    not isinstance(question.get("gold"), str) or
                    not isinstance(question.get("capability"), str)):
                raise ValueError("CHAMPIONSHIP_BATTERY_QUESTION_INVALID")
        if segment["sha256"] not in seen:
            seen.add(segment["sha256"])
            result.append(segment)
    return _dedup_battery_segments(result)


def battery_from_exam(exam: dict, capabilities) -> tuple[dict, ...]:
    """Make one active battery segment from questions this checkpoint got right."""
    questions = []
    for capability in tuple(dict.fromkeys(capabilities)):
        if capability not in exam.get("correct_questions", {}):
            raise ValueError("CHAMPIONSHIP_BATTERY_CURRENT_EVIDENCE_MISSING")
        questions.extend({**question, "capability": capability}
                         for question in exam["correct_questions"][capability])
    return (() if not questions else (_battery_segment(exam, questions),))


def refresh_battery(role: dict, *, gate_exam: dict, fresh_exam: dict,
                    qualification_scope, battery_correct: dict) -> tuple[dict, ...]:
    """Keep only questions the winner answered correctly in the latest title match."""
    segments = list(battery_from_exam(gate_exam, qualification_scope))
    segments.extend(battery_from_exam(fresh_exam, qualification_scope))
    current_segment_count = len(segments)
    for segment in verified_battery(role):
        correct = set(battery_correct.get(segment["sha256"], ()))
        offered = {question["id"]: question for question in segment["questions"]}
        if not correct <= set(offered):
            raise ValueError("CHAMPIONSHIP_BATTERY_RESULT_DRIFT")
        questions = [offered[identity] for identity in correct]
        if questions:
            segments.append(_battery_segment(segment, questions))

    if "complete_solver_provenance" in role:
        # Preserve original replay provenance when a question survives deduplication.
        segments = segments[current_segment_count:] + segments[:current_segment_count]
    return _dedup_battery_segments(segments)


def preserves_witnesses(role: dict, correct_by_witness: dict) -> bool:
    """Every inherited question must be correct, including foreign grades."""
    witnesses = verified_witnesses(role)
    if not witnesses:
        return False
    return all(witness["sha256"] in correct_by_witness and
               {q["id"] for q in witness["questions"]} <=
               set(correct_by_witness[witness["sha256"]]) for witness in witnesses)


def maxed_role(role: dict) -> bool:
    """Saved perfect-question proof entitles a role to its direct advisory vote."""
    if "maxed" in role:
        if type(role["maxed"]) is not bool:
            raise ValueError("CHAMPIONSHIP_ROLE_MAXED_INVALID")
        return role["maxed"]
    witnesses = verified_witnesses(role)
    if witnesses:
        return any(role["capability"] in witness["perfect_capabilities"] or
                   (witness["sha256"] in role.get("cleared_witnesses", ()) and
                    role["capability"] in witness["capabilities"])
                   for witness in witnesses)
    return role.get("correct") == role.get("total") and role.get("total", 0) > 0
