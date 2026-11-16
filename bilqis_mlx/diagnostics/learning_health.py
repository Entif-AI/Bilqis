"""Bounded, non-authoritative learning health over accepted paired assessments.

Numbers are comparable only within one source/rubric/policy/cohort epoch.
Unknown warning predicates stay NOT_MEASURED rather than borrowing a verdict
from a retention decision or a teaching heuristic.
"""
from __future__ import annotations

from .signals import DiagnosticStatus, LearningSignal
from .trajectories import CohortTrajectory, MIN_RETENTION_OBSERVATIONS
from bilqis_mlx.semantics.domains import contract_digest

SCHEMA = "bilqis.bamf.learning-health/v1"
STATE_SCHEMA = "bilqis.bamf.learning-health-state/v1"
_SIGNALS = tuple(LearningSignal)
_UNKNOWN = DiagnosticStatus.NOT_MEASURED.value


def validate_learning_health_state(record):
    """Validate the bounded aggregate that may enter accepted B13 custody."""
    if (not isinstance(record, dict) or record.get("schema") != STATE_SCHEMA
            or record.get("coverage_state") not in {"VALID", "PARTIAL"}
            or not isinstance(record.get("by_capability"), dict)
            or len(record["by_capability"]) > 48
            or not isinstance(record.get("certified_surfaces", []), list)
            or len(record.get("certified_surfaces", [])) > 128):
        raise ValueError("LEARNING_HEALTH_STATE_ENVELOPE_INVALID")
    for capability, health in record["by_capability"].items():
        if (not isinstance(capability, str) or not capability
                or not isinstance(health, dict)
                or health.get("schema") != SCHEMA
                or health.get("capability_id") != capability
                or health.get("history_state")
                not in {"VALID", "PARTIAL", "INVALID", "NOT_MEASURED"}):
            raise ValueError("LEARNING_HEALTH_STATE_CAPABILITY_INVALID")
    for surface in record.get("certified_surfaces", []):
        _validate_certified_surface(surface)
    return record


def _validate_certified_surface(surface):
    required = (
        "surface_id", "capability_id", "rubric_sha256", "source_sha256",
        "fixed_cohort_sha256", "retention_policy_sha256",
        "certified_checkpoint_sha256",
    )
    if (not isinstance(surface, dict)
            or any(not isinstance(surface.get(key), str) or not surface[key]
                   for key in required)
            or any(len(surface[key]) != 64
                   or any(char not in "0123456789abcdef" for char in surface[key])
                   for key in required[2:])
            or _score(surface) is None):
        raise ValueError("LEARNING_HEALTH_CERTIFIED_SURFACE_INVALID")


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
            and previous.get("history_state") != "INVALID"
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


def _recent_checkpoints(visit, accepted, score, previous, epoch_sha256):
    checkpoint = visit.get("accepted_checkpoint_sha256")
    optimizer_step = visit.get("accepted_optimizer_step")
    if (not accepted or score is None or not isinstance(checkpoint, str)
            or len(checkpoint) != 64 or any(c not in "0123456789abcdef" for c in checkpoint)
            or type(optimizer_step) is not int or optimizer_step < 0):
        return (), None
    prior = (tuple(previous.get("recent_checkpoints", ()))
             if isinstance(previous, dict)
             and previous.get("epoch_sha256") == epoch_sha256 else ())
    if isinstance(previous, dict) and previous.get("history_state") == "INVALID":
        return prior[-MIN_RETENTION_OBSERVATIONS:], (
            previous.get("history_error") or "PRIOR_HISTORY_INVALID")
    for item in prior:
        if item.get("checkpoint_sha256") == checkpoint:
            if (item.get("optimizer_step") == optimizer_step
                    and item.get("correct") == score[0] and item.get("total") == score[1]):
                return prior[-MIN_RETENTION_OBSERVATIONS:], None
            return prior[-MIN_RETENTION_OBSERVATIONS:], "CHECKPOINT_EVIDENCE_DIVERGENCE"
    if prior and optimizer_step <= prior[-1].get("optimizer_step", optimizer_step):
        return prior[-MIN_RETENTION_OBSERVATIONS:], "NON_MONOTONIC_OPTIMIZER_STEP"
    return (*prior, {
        "checkpoint_sha256": checkpoint, "optimizer_step": optimizer_step,
        "correct": score[0], "total": score[1],
    })[-MIN_RETENTION_OBSERVATIONS:], None


def _warnings(visit, recent, history_error=None):
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
    if history_error is not None:
        warnings[2] = {
            "signal": LearningSignal.LACK_OF_DURABLE_GAIN.value,
            "status": DiagnosticStatus.NOT_MEASURED.value,
            "note": f"Longitudinal history invalid: {history_error}",
            "evidence_count": len(recent),
        }
    elif (len(recent) == MIN_RETENTION_OBSERVATIONS
            and len({item["checkpoint_sha256"] for item in recent}) == len(recent)
            and len({item["total"] for item in recent}) == 1):
        trend = CohortTrajectory(
            visit.get("fixed_cohort_sha256") or "UNKNOWN",
            tuple((item["optimizer_step"], item["correct"], item["total"])
                  for item in recent))
        warned = trend.no_lasting_gain or trend.regressed_from_peak
        warnings[2] = {
            "signal": LearningSignal.LACK_OF_DURABLE_GAIN.value,
            "status": (DiagnosticStatus.OBSERVED_LONGITUDINALLY.value
                       if warned else DiagnosticStatus.NOT_OBSERVED.value),
            "note": ("No lasting gain or regression from an intervening peak"
                     if warned else "Latest accepted checkpoint retains best fixed-screen gain"),
            "evidence_count": len(recent),
        }
    return tuple(warnings)


def _certified_surface_regression(visit, score, surfaces):
    ids, compared, regressed = [], 0, False
    for surface in surfaces:
        if not isinstance(surface, dict):
            raise ValueError("LEARNING_HEALTH_CERTIFIED_SURFACE_RECORD_INVALID")
        _validate_certified_surface(surface)
        identity = surface.get("surface_id")
        surface_score = _score(surface)
        if not isinstance(identity, str) or not identity:
            raise ValueError("LEARNING_HEALTH_CERTIFIED_SURFACE_ID_INVALID")
        if (surface.get("capability_id") != visit.get("capability_id")
                or surface.get("rubric_sha256") != visit.get("rubric_sha256")
                or surface.get("source_sha256") != visit.get("source_sha256")
                or surface.get("fixed_cohort_sha256") != visit.get("fixed_cohort_sha256")
                or surface.get("retention_policy_sha256")
                != visit.get("retention_policy_sha256")
                or not isinstance(surface.get("certified_checkpoint_sha256"), str)
                or len(surface["certified_checkpoint_sha256"]) != 64
                or any(char not in "0123456789abcdef"
                       for char in surface["certified_checkpoint_sha256"])):
            ids.append(identity)
            continue
        ids.append(identity)
        if score is None or surface_score is None or surface_score[1] != score[1]:
            continue
        compared += 1
        regressed = regressed or score[0] < surface_score[0]
    return tuple(ids), (
        "OBSERVED_REGRESSION" if regressed else
        "NOT_OBSERVED" if compared else
        "NOT_MEASURED")


def _history_projection(visit, accepted, score, previous, capability, epoch, epoch_sha256):
    first, latest, best, points, comparable = _accepted_scores(
        accepted, score, previous, capability, epoch, epoch_sha256)
    recent, history_error = _recent_checkpoints(
        visit, accepted, score, previous, epoch_sha256)
    previous_state = (
        previous.get("history_state") if isinstance(previous, dict) else None)
    history_state = (
        "INVALID" if history_error is not None else
        "PARTIAL" if visit.get("history_seed_state", "VALID") == "PARTIAL"
        or previous_state == "PARTIAL" else
        "VALID" if accepted and score is not None else
        "NOT_MEASURED")
    if history_error is not None:
        latest = {"correct": score[0], "total": score[1]} if score is not None else None
        first = best = None
        points, comparable = (1 if latest else 0), False
    return (
        first, latest, best, points, comparable, recent,
        history_state, history_error,
    )


def _protected_regression(visit):
    protected = tuple(item for item in visit.get("protected", ())
                      if isinstance(item, dict))
    regression = tuple(item["capability_id"] for item in protected
                       if _score(item) is not None
                       and type(item.get("before")) is int
                       and item["after"] < item["before"])
    state = (
        "OBSERVED_REGRESSION" if regression else
        "NOT_OBSERVED" if visit.get("protected_scope_state") == "MEASURED" else
        "NOT_MEASURED")
    return regression, state


def project_learning_health(visit: dict, *, accepted: bool,
                            previous: dict | None = None,
                            certified_surfaces=()) -> dict:
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
    if not isinstance(certified_surfaces, (tuple, list)):
        raise ValueError("LEARNING_HEALTH_CERTIFIED_SURFACES_INVALID")
    epoch = _epoch(visit)
    epoch_sha256 = contract_digest(epoch)
    measured_target = visit.get("learning_target")
    if measured_target is None and visit.get("evidence_stage") != "STRICT_GENERALIZATION":
        measured_target = visit.get("target")
    score = _score(measured_target)
    (first, latest, best, points, comparable, recent,
     history_state, history_error) = _history_projection(
        visit, accepted, score, previous, capability, epoch, epoch_sha256)
    regression, protected_regression_state = _protected_regression(visit)
    prior_surface_ids, surface_regression = _certified_surface_regression(
        visit, score if accepted else None, certified_surfaces)
    return {
        "schema": SCHEMA, "capability_id": capability, "grade_id": grade,
        "grade_definition_id": visit.get("grade_definition_id"),
        "grade_definition_version": visit.get("grade_definition_version"),
        "epoch_sha256": epoch_sha256,
        "state": "MEASURED" if latest else "NOT_MEASURED",
        "history_state": history_state,
        "history_error": history_error,
        "first": first, "latest": latest, "best": best,
        "comparable_points": points,
        "recent_checkpoints": recent,
        "gain_from_first": (max(0, latest["correct"] - first["correct"])
                            if comparable else None),
        "regressed_from_first": (latest["correct"] < first["correct"]
                                  if comparable else False),
        "distance_to_mastery_state": "MEASURED" if latest else "NOT_MEASURED",
        "distance_to_mastery": (
            latest["total"] - latest["correct"] if latest else None),
        "fixed_screen_errors": (latest["total"] - latest["correct"]
                                if latest else None),
        "qualification_state": "NOT_MEASURED",
        "protected_regression_state": protected_regression_state,
        "regressed_protected_capabilities": regression,
        "prior_certified_surface_ids": prior_surface_ids,
        "certified_surface_regression_state": surface_regression,
        "warnings": _warnings(visit, recent, history_error),
    }
