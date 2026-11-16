from __future__ import annotations

from types import MappingProxyType
from bilqis_mlx.errors.authority import authority_label, authority_report


def _authority_candidate_reason(candidate: dict) -> str | None:
    reason = candidate.get("reason")
    if authority_report(reason, domain="retention") is None:
        return None
    return authority_label(reason, domain="retention",
                           blocking_capability=candidate.get("blocking_capability"),
                           blocking_scope=candidate.get("blocking_scope"))


def _signal_label(signal) -> str:
    return _SIGNAL_LABELS.get(str(signal), str(signal))

def _teacher_decision_text(decision: object) -> str:
    if not isinstance(decision, dict):
        return "LESSON COMMITTED; exam pending"
    warnings = [_signal_label(signal) for signal in decision.get("warning_signals", ())]
    selected = decision.get("selected") or {}
    selection = decision.get("policy_selection") or {}
    warning_prefix = ("warn " if selection.get("diagnostic_context_consumed") else
                      "warn-context ")
    parts = [warning_prefix + ",".join(warnings)] if warnings else []
    replayed = selected.get("exam_mistake_replay")
    champion = selected.get("champion_priority")
    if type(replayed) is int and replayed:
        parts.append(f"miss {replayed}")
    if type(champion) is int and champion:
        parts.append(f"champ {champion}")
    return " | ".join(parts) + "; exam pending" if parts else "LESSON COMMITTED; exam pending"


def _warning_text(event: dict) -> str:
    decision = event.get("teacher_decision")
    if not isinstance(decision, dict):
        return "-"
    warnings = [_signal_label(signal) for signal in decision.get("warning_signals", ())]
    return ",".join(warnings) if warnings else "-"

def _candidate_result_reason(event: dict) -> tuple[str, str]:
    candidate = event.get("candidate_retention")
    steps = event.get("retained_optimizer_updates")
    if candidate is None and steps is None:
        return "PEND", "EXAM PENDING"
    if not isinstance(candidate, dict):
        return "UNK", "ADMISSION UNKNOWN"
    reason = str(candidate.get("reason") or "UNKNOWN")
    reason = _authority_candidate_reason(candidate) or _REASON_LABELS.get(reason, reason)
    if candidate.get("decision") == "PROVISIONAL" and type(steps) is int and steps > 0:
        return "RETAIN", reason
    if candidate.get("decision") == "REJECT" and steps == 0:
        return "REJECT", reason
    return "CONFLT", "ADMISSION CONFLICT"



def _candidate_admission_text(event: dict) -> str:
    """Distinguish an attempted lesson from student/AdamW promotion."""
    candidate = event.get("candidate_retention")
    steps = event.get("retained_optimizer_updates")
    if candidate is None and steps is None:
        return _teacher_decision_text(event.get("teacher_decision"))
    if not isinstance(candidate, dict):
        label = "ADMISSION UNKNOWN"
    elif candidate.get("decision") == "PROVISIONAL" and type(steps) is int and steps > 0:
        label = f"RETAIN {steps}"
    elif candidate.get("decision") == "REJECT" and steps == 0:
        reason = candidate.get("reason")
        authority = _authority_candidate_reason(candidate)
        if authority is not None:
            label = "REJECT " + authority
        elif reason == "NO_MEASURABLE_TARGET_GAIN":
            label = "REJECT NO TARGET GAIN"
        elif reason == "FRAGILE_COMPOSITION_REPLAY_REGRESSION":
            label = "REJECT OR/XOR LOSS"
        elif reason == "PROTECTED_CAPABILITY_REGRESSION":
            label = "REJECT PROTECTED LOSS"
        else:
            label = "REJECT " + str(reason or "UNKNOWN")
    else:
        label = "ADMISSION CONFLICT"
    instructional = _teacher_decision_text(event.get("teacher_decision"))
    hint = instructional.removesuffix("; exam pending")
    if hint != "LESSON COMMITTED":
        label += " | " + hint
    association = _association_text(event)
    if association is not None:
        label += " | " + association
    return label



def _association_text(event: dict) -> str | None:
    bridge = event.get("boolean_association_bridge")
    if isinstance(bridge, dict) and bridge.get("active_for_visit") is True:
        grades = bridge.get("borrowed_source_grades")
        delivered = bridge.get("delivered_examples")
        active = event.get("active_grade") or event.get("grade")
        if (isinstance(grades, list) and grades and
                all(isinstance(grade, str) and grade for grade in grades) and
                type(delivered) is int and delivered > 0 and
                isinstance(active, str) and active):
            return "COMPOSE " + "+".join(grades) + "->" + active + f" x{delivered}"
    return None



def _instruction_method_text(event: dict) -> str:
    """Project the lesson mechanism actually evidenced by the visit receipt."""
    parts = []
    if _association_text(event) is not None:
        parts.append("COMPOSE")
    decision = event.get("teacher_decision") or {}
    selected = decision.get("selected") if isinstance(decision, dict) else {}
    selected = selected if isinstance(selected, dict) else {}
    if type(selected.get("exam_mistake_replay")) is int and selected["exam_mistake_replay"] > 0:
        parts.append("MISS")
    prerequisites = selected.get("prerequisite_connections")
    if isinstance(prerequisites, (list, tuple)) and prerequisites:
        parts.append("PREREQ")
    if type(selected.get("champion_priority")) is int and selected["champion_priority"] > 0:
        parts.append("CHAMP")
    if parts:
        return "+".join(parts)
    methodology = event.get("lesson_methodology") or {}
    if isinstance(methodology, dict) and type(methodology.get("delivered_examples")) is int:
        if methodology["delivered_examples"] > 0:
            return "SOURCE"
    if type(selected.get("delivered_examples")) is int and selected["delivered_examples"] > 0:
        return "DIRECT"
    return "-"



_SIGNAL_LABELS = MappingProxyType({
    "REPETITIVE_ANSWERS": "S1",
    "CHANCE_LEVEL_OR_LAGGING": "S2",
    "LACK_OF_DURABLE_GAIN": "S3",
    "DISCONNECTED_PREREQUISITES": "S4",
    "EXCESSIVE_INTRODUCTORY_COMPLEXITY": "S5",
})

_REASON_LABELS = MappingProxyType({
    "NO_MEASURABLE_TARGET_GAIN": "NO TARGET GAIN",
    "FRAGILE_COMPOSITION_REPLAY_REGRESSION": "OR/XOR LOSS",
    "PROTECTED_CAPABILITY_REGRESSION": "PROTECTED LOSS",
    "ACTIVE_SCHOOL_GRADE_REGRESSION": "FRONTIER LOSS",
    "PAIRED_SCREEN_WITHIN_BUDGET": "WITHIN BUDGET",
})
