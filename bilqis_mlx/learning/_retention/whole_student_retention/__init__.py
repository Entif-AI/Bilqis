"""Keep recoverable whole-student peaks without rolling back active learning.

Only source-scored results on the identical qualification cohort are ranked.
Changing the numeric scope, rubric, or examination cohort starts a new
comparison. A peak holds its matching own-AdamW bundle, not just weights.
"""
from __future__ import annotations

import hashlib
import json


SCHEMA = "bilqis.mlx.whole-student-retention/v1"
MAX_SCOPE_PEAKS = 4


def advance_peaks(existing: list[dict], *, curriculum_mode: str,
                  numeric_maximum: int | None, rubric_sha256: str,
                  cohort_sha256: str, assessment_scope_sha256: str,
                  scores: dict, checkpoint: dict) -> tuple[list[dict], dict]:
    """Return bounded, comparable peak pointers and this evaluation's status.

    A higher combined correct count is necessary for replacement. A peak is
    advisory/custodial: it never replaces the actively learning student and
    never certifies grade graduation or overrides per-capability protection.
    """
    if (not isinstance(existing, list) or not curriculum_mode or not rubric_sha256
            or not cohort_sha256 or not assessment_scope_sha256 or not scores
            or not isinstance(checkpoint, dict)
            or not all(k in checkpoint for k in ("filename", "sha256", "optimizer_step"))):
        raise ValueError("WHOLE_STUDENT_PEAK_INCOMPLETE_SOURCE")
    total = correct = 0
    for value in scores.values():
        if (not isinstance(value, dict) or
                type(value.get("correct")) is not int or
                type(value.get("total")) is not int or
                not 0 <= value["correct"] <= value["total"]):
            raise ValueError("WHOLE_STUDENT_PEAK_INVALID_SCORE")
        correct += value["correct"]
        total += value["total"]
    if total == 0:
        raise ValueError("WHOLE_STUDENT_PEAK_EMPTY_EXAM")
    scope = {"curriculum_mode": curriculum_mode,
             "numeric_maximum": numeric_maximum,
             "rubric_sha256": rubric_sha256,
             "cohort_sha256": cohort_sha256,
             "assessment_scope_sha256": assessment_scope_sha256}
    identity = hashlib.sha256(json.dumps(scope, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    previous = next((item for item in existing if item["scope_sha256"] == identity), None)
    promoted = previous is None or correct > previous["correct"]
    record = {"schema": SCHEMA, "scope_sha256": identity, **scope,
              "correct": correct, "total": total,
              "scores": scores, "checkpoint": dict(checkpoint)}
    updated = ([item for item in existing if item["scope_sha256"] != identity]
               + [record if promoted else previous])
    updated = updated[-MAX_SCOPE_PEAKS:]
    peak = record if promoted else previous
    return updated, {"promoted": promoted, "scope_sha256": identity,
                     "exam_correct": correct, "exam_total": total,
                     "best_correct": peak["correct"], "best_total": peak["total"],
                     "best_checkpoint_sha256": peak["checkpoint"]["sha256"],
                     "best_optimizer_step": peak["checkpoint"]["optimizer_step"],
                     "live_student_unchanged": True}
