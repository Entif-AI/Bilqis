"""Bounded, non-authoritative learning health over accepted paired assessments.

Numbers are comparable only within one source/rubric/policy/cohort epoch.
Unknown warning predicates stay NOT_MEASURED rather than borrowing a verdict
from a retention decision or a teaching heuristic.
"""
from __future__ import annotations

from .signals import DiagnosticStatus, LearningSignal
from bilqis_mlx.semantics.domains import contract_digest

SCHEMA = "bilqis.bamf.learning-health/v1"
_SIGNALS = tuple(LearningSignal)
_UNKNOWN = DiagnosticStatus.NOT_MEASURED.value


def _warning(signal, status=_UNKNOWN, note="Required source evidence unavailable"):
    return {"signal": signal.value, "status": status, "note": note, "evidence_count": 0}


def _score(value):
    if not isinstance(value, dict) or value.get("state") != "MEASURED":
        return None
    after, total = value.get("after"), value.get("total")
    if (type(after) is not int or type(total) is not int or total < 1
            or not 0 <= after <= total):
        return None
    return after, total


def _epoch(visit):
    return (
        visit.get("grade_id"), visit.get("grade_definition_id"),
        visit.get("grade_definition_version"),
        visit.get("retention_policy_sha256"),
        visit.get("fixed_cohort_sha256"), visit.get("rubric_sha256"),
        visit.get("source_sha256"),
    )


def _accepted_scores(accepted, score, previous, capability, epoch, epoch_sha256):
    first = latest = best = None
    points, comparable = 0, False
    if not accepted or score is None:
        return first, latest, best, points, comparable
    first = latest = best = {"correct": score[0], "total": score[1]}
    points = 1
    if (all(isinstance(item, str) and item for item in epoch[3:])
            and isinstance(previous, dict)
            and previous.get("schema") == SCHEMA
            and previous.get("capability_id") == capability
            and previous.get("epoch_sha256") == epoch_sha256
            and previous.get("latest") is not None
            and previous["latest"].get("total") == score[1]):
        first = previous["first"]
        best = (previous["best"] if previous["best"]["correct"] >= score[0]
                else latest)
        points = min(64, int(previous.get("comparable_points", 1)) + 1)
        comparable = True
    return first, latest, best, points, comparable


def _warnings(visit):
    warnings = [_warning(signal) for signal in _SIGNALS]
    for key, positions in (("learning_signals", (0, 1)),
                           ("learning_methodology", (3, 4))):
        for finding in visit.get(key, ()):
            if not isinstance(finding, dict):
                continue
            for index in positions:
                if finding.get("signal") == warnings[index]["signal"]:
                    warnings[index] = {
                        "signal": finding["signal"],
                        "status": finding.get("status", _UNKNOWN),
                        "note": finding.get("note", ""),
                        "evidence_count": finding.get("evidence_count", 0),
                    }
    # A parent/candidate pair is not a three-checkpoint S3 trajectory.
    return tuple(warnings)


def project_learning_health(visit: dict, *, accepted: bool,
                            previous: dict | None = None,
                            certified_surface_ids=()) -> dict:
    """Read a completed visit and optionally extend its accepted trajectory.

    The caller must establish actual publication before passing accepted=True.
    Prior certified surfaces are explicit identities, never grade-letter order.
    """
    if not isinstance(visit, dict) or type(accepted) is not bool:
        raise ValueError("LEARNING_HEALTH_VISIT_INVALID")
    capability = visit.get("capability_id")
    grade = visit.get("grade_id")
    if not isinstance(capability, str) or not capability:
        raise ValueError("LEARNING_HEALTH_CAPABILITY_REQUIRED")
    if not isinstance(grade, str) or not grade:
        raise ValueError("LEARNING_HEALTH_GRADE_REQUIRED")
    if (not isinstance(certified_surface_ids, (tuple, list))
            or any(not isinstance(item, str) or not item
                   for item in certified_surface_ids)):
        raise ValueError("LEARNING_HEALTH_CERTIFIED_SURFACES_INVALID")
    epoch = _epoch(visit)
    epoch_sha256 = contract_digest(epoch)
    measured_target = visit.get("learning_target")
    if measured_target is None and visit.get("evidence_stage") != "STRICT_GENERALIZATION":
        measured_target = visit.get("target")
    score = _score(measured_target)
    first, latest, best, points, comparable = _accepted_scores(
        accepted, score, previous, capability, epoch, epoch_sha256)
    protected = tuple(item for item in visit.get("protected", ())
                      if isinstance(item, dict))
    regression = tuple(item["capability_id"] for item in protected
                       if _score(item) is not None
                       and type(item.get("before")) is int
                       and item["after"] < item["before"])
    return {
        "schema": SCHEMA, "capability_id": capability, "grade_id": grade,
        "grade_definition_id": visit.get("grade_definition_id"),
        "grade_definition_version": visit.get("grade_definition_version"),
        "epoch_sha256": epoch_sha256,
        "state": "MEASURED" if latest else "NOT_MEASURED",
        "first": first, "latest": latest, "best": best,
        "comparable_points": points,
        "gain_from_first": (max(0, latest["correct"] - first["correct"])
                            if comparable else None),
        "regressed_from_first": (latest["correct"] < first["correct"]
                                  if comparable else False),
        "distance_to_mastery": None,
        "fixed_screen_errors": (latest["total"] - latest["correct"]
                                if latest else None),
        "qualification_state": "NOT_MEASURED",
        "regressed_protected_capabilities": regression,
        "prior_certified_surface_ids": tuple(certified_surface_ids),
        "certified_surface_regression_state": "NOT_MEASURED",
        "warnings": _warnings(visit),
    }
