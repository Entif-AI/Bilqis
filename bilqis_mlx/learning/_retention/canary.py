"""Calibrated reject-only retention canaries for bounded candidate visits."""
from __future__ import annotations

from dataclasses import dataclass

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.teacher_multifidelity import (
    DEFAULT_ACTIVATION_POLICY,
    qualify_activation,
)


SCHEMA = "bilqis.retention-target-canary/v1"
HISTORY_SCHEMA = "bilqis.retention-target-canary-history/v1"
HISTORY_LIMIT = 128


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


@dataclass(frozen=True)
class CanaryPolicy:
    version: str
    decision_rung: int
    minimum_target_delta_to_continue: int

    def __post_init__(self) -> None:
        if (not isinstance(self.version, str) or not self.version
                or type(self.decision_rung) is not int or self.decision_rung < 1
                or type(self.minimum_target_delta_to_continue) is not int
                or self.minimum_target_delta_to_continue < 1):
            _invalid("retention canary policy invalid")


DEFAULT_POLICY = CanaryPolicy(
    version="retention-target-canary/v1",
    decision_rung=8,
    minimum_target_delta_to_continue=1,
)


def decision_rung(policy: CanaryPolicy, full_budget_steps: int) -> int | None:
    if (type(policy) is not CanaryPolicy or type(full_budget_steps) is not int
            or full_budget_steps < 1):
        _invalid("retention canary budget invalid")
    return policy.decision_rung if policy.decision_rung < full_budget_steps else None


def activation(teacher: dict) -> dict:
    if not isinstance(teacher, dict):
        _invalid("retention canary teacher invalid")
    history = teacher.get("retention_canary_projection")
    if history is None:
        return qualify_activation((), policy=DEFAULT_ACTIVATION_POLICY)
    if (not isinstance(history, dict)
            or history.get("schema") != HISTORY_SCHEMA
            or not isinstance(history.get("reviews"), list)
            or any(not isinstance(review, dict)
                   or review.get("channel") != "RETENTION_TARGET_CANARY"
                   for review in history["reviews"])):
        _invalid("retention canary history invalid")
    return qualify_activation(tuple(history["reviews"]), policy=DEFAULT_ACTIVATION_POLICY)


def _target_delta(rows, parent_predictions, candidate_predictions) -> int:
    if (not isinstance(rows, (list, tuple)) or not rows
            or not isinstance(parent_predictions, dict)
            or not isinstance(candidate_predictions, dict)):
        _invalid("retention canary evidence invalid")
    before = after = 0
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get("id"), str)
                or not isinstance(row.get("gold"), str) or row["id"] in seen
                or row["id"] not in parent_predictions
                or row["id"] not in candidate_predictions):
            _invalid("retention canary evidence invalid")
        seen.add(row["id"])
        before += int(parent_predictions[row["id"]] == row["gold"])
        after += int(candidate_predictions[row["id"]] == row["gold"])
    return after - before


def probe(policy: CanaryPolicy, *, rung: int, full_budget_steps: int, rows,
          parent_predictions: dict, candidate_predictions: dict,
          activation_state: dict) -> dict:
    expected = decision_rung(policy, full_budget_steps)
    if (expected is None or rung != expected or
            not isinstance(activation_state, dict)
            or activation_state.get("status") not in {"QUALIFIED", "NOT_QUALIFIED"}):
        _invalid("retention canary probe invalid")
    delta = _target_delta(rows, parent_predictions, candidate_predictions)
    would_stop = delta < policy.minimum_target_delta_to_continue
    active = activation_state["status"] == "QUALIFIED"
    return {
        "schema": SCHEMA,
        "policy_version": policy.version,
        "channel": "RETENTION_TARGET_CANARY",
        "mode": "ACTIVE" if active else "SHADOW",
        "rung": rung,
        "full_budget_steps": full_budget_steps,
        "target_correct_delta": delta,
        "minimum_target_delta_to_continue": policy.minimum_target_delta_to_continue,
        "would_stop": would_stop,
        "stop": bool(active and would_stop),
        "authority": "REJECT_ONLY",
        "activation_status": activation_state["status"],
    }


def complete(teacher: dict, probe_receipt: dict, *, final_retained: bool,
             spent_steps: int, full_budget_steps: int) -> dict:
    if (not isinstance(teacher, dict) or not isinstance(probe_receipt, dict)
            or probe_receipt.get("schema") != SCHEMA
            or type(final_retained) is not bool
            or type(spent_steps) is not int or type(full_budget_steps) is not int
            or not 1 <= spent_steps <= full_budget_steps):
        _invalid("retention canary completion invalid")
    review = None
    if probe_receipt["mode"] == "SHADOW" and spent_steps == full_budget_steps:
        would_stop = bool(probe_receipt["would_stop"])
        rung = int(probe_receipt["rung"])
        review = {
            "schema": SCHEMA,
            "channel": "RETENTION_TARGET_CANARY",
            "mode": "SHADOW",
            "policy_version": probe_receipt["policy_version"],
            "first_would_stop_step": rung if would_stop else None,
            "final_retained": final_retained,
            "false_kill": bool(would_stop and final_retained),
            "false_continue": bool(not would_stop and not final_retained),
            "actual_steps_spent": full_budget_steps,
            "shadow_steps_if_active": rung if would_stop else full_budget_steps,
            "shadow_steps_saved": full_budget_steps - rung if would_stop else 0,
        }
        history = teacher.setdefault(
            "retention_canary_projection",
            {"schema": HISTORY_SCHEMA, "reviews": []},
        )
        if (history.get("schema") != HISTORY_SCHEMA
                or not isinstance(history.get("reviews"), list)):
            _invalid("retention canary history invalid")
        history["reviews"].append(review)
        del history["reviews"][:-HISTORY_LIMIT]
    activation_state = activation(teacher)
    return {
        **probe_receipt,
        "spent_steps": spent_steps,
        "steps_saved": full_budget_steps - spent_steps,
        "final_retained": final_retained,
        "calibration_review": review,
        "post_visit_activation": activation_state,
    }


def require_confirmed_reject(probe_receipt: dict | None, *, stage: str,
                             outcome: dict) -> None:
    if not probe_receipt or not probe_receipt.get("stop"):
        return
    if (stage != "TARGET_ONLY_REJECTED" or not isinstance(outcome, dict)
            or outcome.get("decision") != "REJECT"
            or outcome.get("reason") != "NO_MEASURABLE_TARGET_GAIN"):
        _invalid("retention canary early stop was not confirmed by final retention")


__all__ = (
    "CanaryPolicy", "DEFAULT_POLICY", "SCHEMA", "activation", "complete",
    "decision_rung", "probe", "require_confirmed_reject",
)
