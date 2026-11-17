"""Read-only integer-root scope presentation helpers."""
from __future__ import annotations
from enum import Enum


PROFILE_ADOPTION_EVENTS = frozenset({
    "SCHOOL_EXECUTION_PROFILE_ADOPTED",
    "SCHOOL_SEMANTIC_CATALOG_PROFILE_ADOPTED",
})

class _NumericScopeError(str, Enum):
    CURRICULUM_REPLACEMENT_INVALID = "SCHOOL_TELEMETRY_CURRICULUM_REPLACEMENT_INVALID"


CURRICULUM_REPLACEMENT_INVALID = "SCHOOL_TELEMETRY_CURRICULUM_REPLACEMENT_INVALID"


def integer_root_scope(maximum) -> str:
    if type(maximum) is not int or maximum < 0:
        return "-"
    return f"0...{maximum}" if maximum else "0"


def apply_profile_adoption(telemetry, grade, event) -> None:
    telemetry._reset_score_era(reason=event["event"], grade=grade)
    dimensions = event.get("provider_dimensions")
    if dimensions is not None:
        if (not isinstance(dimensions, list) or any(
                not isinstance(item, dict) or
                not isinstance(item.get("provider_dimension_id"), str) or
                not isinstance(item.get("provider_dimension_value"), str) or
                type(item.get("provider_dimension_terminal")) is not bool or
                not isinstance(item.get("telemetry_projection"), str)
                for item in dimensions)):
            raise ValueError(_NumericScopeError.CURRICULUM_REPLACEMENT_INVALID.value)
        telemetry.board.state["provider_dimensions"] = dimensions
    introot = next((
        item for item in dimensions or ()
        if item.get("telemetry_projection") == "INTROOT"), None)
    maximum = event.get("numeric_maximum")
    if introot is not None:
        value = introot["provider_dimension_value"]
        if not value.isdecimal():
            raise ValueError(_NumericScopeError.CURRICULUM_REPLACEMENT_INVALID.value)
        maximum = int(value)
    if maximum is not None and (type(maximum) is not int or maximum < 0):
        raise ValueError(CURRICULUM_REPLACEMENT_INVALID)
    if maximum is not None:
        telemetry.board.state["numeric_maximum"] = maximum
    telemetry.board.state["step"] = event.get(
        "optimizer_step", telemetry.board.state.get("step"))
    telemetry.board.push("system", {
        "kind": "CURRICULUM", "grade": grade,
        "detail": "Active profile " + str(event.get("profile_id") or "-") +
                  (" | integer roots " + integer_root_scope(maximum)
                   if maximum is not None else ""),
    }, redraw=False)
