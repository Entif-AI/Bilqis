"""Operator-facing recovery policy for failures that survive domain self-healing.

The domain owner should repair, defer, retry, or regenerate a safe condition
before it reaches the CLI.  This module is the final translation layer for the
conditions that still require source repair or human action.  It never weakens
custody, source, semantic, or optimizer authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from ..errors import ErrorBus


@dataclass(frozen=True)
class RecoveryAdvice:
    code: str
    disposition: str
    next_action: str
    explanation: str = ""
    safe_check: str = ""
    manual_ref: str = "docs/operations/OPERATOR_FIELD_MANUAL.md"


_EXACT = MappingProxyType({
    "HUMAN_TRAINER_NEW_RUN_HAS_EXISTING_CONTENT": RecoveryAdvice(
        "HUMAN_TRAINER_NEW_RUN_HAS_EXISTING_CONTENT",
        "OPERATOR_ACTION",
        "A saved school already exists. Resume it with --resume rather than starting a new run.",
    ),
    "VERIFY_SOURCE_REQUIRES_DRY_RUN": RecoveryAdvice(
        "VERIFY_SOURCE_REQUIRES_DRY_RUN",
        "OPERATOR_ACTION",
        "Source verification is neural-inert. Re-run the command with --dry-run --verify-source.",
    ),
    "FLASH_MODE_REQUIRES_RESUME": RecoveryAdvice(
        "FLASH_MODE_REQUIRES_RESUME",
        "OPERATOR_ACTION",
        "Flash mode only applies to an existing school. Add --resume or omit --flash-mode.",
    ),
    "NUMERIC_STAIRCASE_REQUIRES_RESUME": RecoveryAdvice(
        "NUMERIC_STAIRCASE_REQUIRES_RESUME",
        "OPERATOR_ACTION",
        "Numeric staircase is a continuation of an existing student. Add --resume.",
    ),
    "COHORT_EMPTY": RecoveryAdvice(
        "COHORT_EMPTY",
        "INTERNAL_RECOVERY_REQUIRED",
        "An internal path attempted to materialize an empty assessment cohort. "
        "The durable checkpoint remains the resume authority; do not invent questions or bypass the cohort guard.",
    ),
    "LEARNING_EXPERIMENT_WEAKNESS_TARGET_CAPACITY_DRIFT": RecoveryAdvice(
        "LEARNING_EXPERIMENT_WEAKNESS_TARGET_CAPACITY_DRIFT",
        "INTERNAL_RECOVERY_REQUIRED",
        "The lesson builder overcommitted its finite batch capacity between fresh support, "
        "weakness replay, and preservation support. Preserve the durable checkpoint and "
        "repair the lesson capacity allocator before retrying; this error does not by itself "
        "indicate source identity, student, or AdamW custody drift.",
    ),
    "INVALID_OR_DRIFTED_SCHOOL_STATE": RecoveryAdvice(
        "INVALID_OR_DRIFTED_SCHOOL_STATE",
        "PRESERVE_AND_DIAGNOSE",
        "Run the neural-inert preflight against the same run directory: "
        "npm run train -- --dry-run --resume --verify-source [--run-dir <same-run-dir>]. "
        "Read the mismatch printed after the error code. Do not hand-edit state.json. "
        "If the course digest differs, resume through the release/compatibility path that owns "
        "that saved state or repair the producing code so it reconstructs the saved program identity. "
        "See docs/operations/OPERATOR_FIELD_MANUAL.md#invalid_or_drifted_school_state.",
        "The saved school identity failed one of its structural predicates. This does not by itself "
        "mean the student checkpoint or AdamW state is corrupt.",
        "npm run train -- --dry-run --resume --verify-source",
    ),
    "CHAMPIONSHIP_TITLE_MATCH_CURRENT_PANEL_UNMEASURED": RecoveryAdvice(
        "CHAMPIONSHIP_TITLE_MATCH_CURRENT_PANEL_UNMEASURED",
        "INTERNAL_RECOVERY_REQUIRED",
        "A title match was requested without a current comparable capability panel. "
        "That match must be deferred until the capability is measured, not forced or synthesized.",
    ),
})


_REASON_EXACT = MappingProxyType({
    "BAMF_PRIORITY_REJECTION_ORDER_INVALID": RecoveryAdvice(
        "BAMF_PRIORITY_REJECTION_ORDER_INVALID",
        "PRESERVE_AND_DIAGNOSE",
        "Preserve the accepted checkpoint and rejection journal. Do not delete, reorder, "
        "or hand-edit events.jsonl; repair the rejection-replay compatibility or ordering "
        "evidence before retrying the trainer.",
        "The trainer could not establish a safe rejection ordering for C03 priority replay.",
    ),
})


def _exact_advice(report, code):
    reason = report.context.get("reason")
    if isinstance(reason, str) and reason in _REASON_EXACT:
        return _REASON_EXACT[reason]
    return _EXACT.get(code)


def error_code(error: BaseException | str) -> str:
    """Extract the stable leading code without depending on exception prose."""
    text = str(error).strip()
    return text.split(":", 1)[0].strip() or error.__class__.__name__


def recovery_advice(error: BaseException | str) -> RecoveryAdvice:
    """Classify every surfaced operator failure into one safe recovery posture."""
    report = ErrorBus.report(error)
    code = report.code
    exact = _exact_advice(report, code)
    if exact is not None:
        return exact
    if not report.legacy_untyped:
        return RecoveryAdvice(code, report.disposition, report.next_action,
                              explanation=report.summary)
    if code.endswith("_EXHAUSTED") or "_EXHAUSTED_" in code:
        return RecoveryAdvice(
            code,
            "RETRY_OR_REGENERATE",
            "The owning source/generator exhausted its bounded search. Retry or expand that "
            "source-valid search; do not weaken gold, scope, or custody requirements.",
        )
    if "REQUIRES" in code or code.endswith("_REQUIRED"):
        return RecoveryAdvice(
            code,
            "OPERATOR_OR_SOURCE_PREREQUISITE",
            "A declared prerequisite is absent. Satisfy or safely produce the named prerequisite "
            "before retrying; do not fabricate its receipt.",
        )
    if any(marker in code for marker in (
            "DRIFT", "TAMPER", "UNSAFE", "MISMATCH", "CONFLICT", "CORRUPT")):
        return RecoveryAdvice(
            code,
            "PRESERVE_AND_REPAIR",
            "Identity or custody evidence disagrees. Preserve the durable checkpoint and repair "
            "the mismatched source/state boundary before retrying; bypass is not safe.",
        )
    if code.endswith("_MISSING") or "_MISSING_" in code:
        return RecoveryAdvice(
            code,
            "RECONSTRUCT_OR_RESTORE",
            "Required durable evidence is missing. Reconstruct it only from authoritative "
            "receipts or restore the original artifact; do not synthesize replacement evidence.",
        )
    if code.endswith("_INVALID") or "_INVALID_" in code:
        return RecoveryAdvice(
            code,
            "CORRECT_INPUT_OR_STATE",
            "The supplied configuration or saved structure is invalid. Correct the owning input "
            "or state producer, then retry from the last durable checkpoint.",
        )
    if any(marker in code for marker in (
            "FORBIDDEN", "PROHIBITED", "NOT_AUTHORIZED", "AUTHORITY_DENIED")):
        return RecoveryAdvice(
            code,
            "AUTHORITY_OR_POLICY_BLOCK",
            "The requested action crosses an explicit authority or safety boundary. Keep the "
            "durable state unchanged and obtain the required authority or choose the permitted path.",
        )
    if any(marker in code for marker in (
            "UNKNOWN", "UNSUPPORTED", "OUTSIDE", "INCOMPLETE", "WRONG_",
            "NOT_ADMITTED", "NOT_SCHEDULED", "NOT_COMPLETE", "OUT_OF_")):
        return RecoveryAdvice(
            code,
            "CORRECT_INPUT_OR_STATE",
            "The current request or generated state is outside the admitted contract. Correct the "
            "owning input/scope producer and retry; do not coerce the invalid value through the gate.",
        )
    if any(marker in code for marker in (
            "UNQUALIFIED", "NOT_QUALIFIED", "NOT_READY", "NOT_MASTERED", "UNAVAILABLE")):
        return RecoveryAdvice(
            code,
            "OPERATOR_OR_SOURCE_PREREQUISITE",
            "The operation is not yet qualified on current evidence. Produce the missing source or "
            "student evidence through its normal owner, then retry from the durable checkpoint.",
        )
    if "EMPTY" in code:
        return RecoveryAdvice(
            code,
            "RETRY_OR_REGENERATE",
            "A generated or selected work set is empty. The owning domain should regenerate, defer, "
            "or choose another admitted work item; it must not fabricate evidence.",
        )
    return RecoveryAdvice(
        code,
        "PRESERVE_AND_REPORT",
        "No automatic repair is proven safe for this condition. Preserve the last durable "
        "checkpoint and diagnose the owning boundary before retrying.",
    )
