"""Capability-local defended championship ownership within one curriculum epoch.

Historical champion and soup receipts stay in the old state fields. The
epoch owns current title holders, surviving batteries and frozen vote entitlements.
This module never reads tensors, trains a student, or changes an optimizer.
"""
from __future__ import annotations

from copy import deepcopy

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.championship_witnesses import (
    battery_from_exam, championship_role_qualified, championship_threshold_met,
    earning_witness, maxed_role, refresh_battery,
    verified_battery)
from bilqis_mlx.learning.mentor_epoch import EARNED_ONLY_POLICY, _pointer


def _pair_key(capability: str, left_sha256: str, right_sha256: str) -> str:
    """Canonical lifetime identity for one capability title matchup."""
    first, second = sorted((left_sha256, right_sha256))
    return f"{capability}|{first}|{second}"


def _settled_match(epoch: dict, capability: str, left_sha256: str,
                   right_sha256: str) -> dict | None:
    ledger = epoch.get("settled_matchups", {})
    if not isinstance(ledger, dict):
        raise ValueError("CHAMPIONSHIP_SETTLED_MATCH_LEDGER_INVALID")
    return ledger.get(_pair_key(capability, left_sha256, right_sha256))


def _archive_invalid_role(updated: dict, capability: str, role: dict,
                          reason: str) -> None:
    archive = updated.setdefault("invalidated_active_roles", [])
    archive.append({
        "capability": capability,
        "origin_grade": role.get("origin_grade"),
        "reason": reason,
        "role": deepcopy(role),
    })


def _capability_grade(capability: str, grades: dict) -> str:
    matches = tuple(grade for grade, capabilities in grades.items()
                    if capability in capabilities)
    if len(matches) != 1:
        raise ValueError("CHAMPIONSHIP_CAPABILITY_GROUP_AMBIGUOUS_OR_ABSENT")
    return matches[0]


def _sanitize_role_origins(updated: dict, grades: dict) -> None:
    """Keep title jurisdiction distinct from checkpoint-training provenance."""
    roles = updated.setdefault("active_roles", {})
    invalid = []
    for capability, role in list(roles.items()):
        title_grade = _capability_grade(capability, grades)
        if title_grade not in grades or capability not in _grade_caps(grades, title_grade):
            raise ValueError("CHAMPIONSHIP_ACTIVE_ROLE_CAPABILITY_UNKNOWN")
        origin = role.get("origin_grade") if isinstance(role, dict) else None
        if not championship_role_qualified(role):
            _archive_invalid_role(
                updated, capability, role, "CHAMPIONSHIP_THRESHOLD_NOT_MET")
            del roles[capability]
            invalid.append(capability)
            continue
        if origin != title_grade:
            reason = ("TITLE_ORIGIN_PROVENANCE_MISSING" if origin is None else
                      "CROSS_GRADE_TITLE_OWNER")
            _archive_invalid_role(updated, capability, role, reason)
            del roles[capability]
            invalid.append(capability)
            continue
        # Historical receipts predate the explicit separation between the
        # capability's title grade and the grade whose retained optimizer update
        # produced the whole-student checkpoint.  At that time they were forced
        # to be identical, so the legacy field is sufficient migration proof.
        checkpoint_origin = role.get("checkpoint_origin_grade")
        if checkpoint_origin is None:
            role["checkpoint_origin_grade"] = origin
        elif checkpoint_origin not in grades:
            _archive_invalid_role(
                updated, capability, role,
                "CHECKPOINT_ORIGIN_PROVENANCE_INVALID")
            del roles[capability]
            invalid.append(capability)
    if invalid:
        soups = updated.get("active_grade_soups", {})
        if soups:
            updated.setdefault("invalidated_active_soups", []).append({
                "reason": "ACTIVE_ROLE_PROVENANCE_INVALIDATED",
                "capabilities": sorted(invalid),
                "active_grade_soups": deepcopy(soups),
            })
        updated["active_grade_soups"] = {}


def sanitize_role_origins(epoch: dict, *, grades: dict) -> tuple[dict, bool]:
    """Public neural-inert migration gate for active title provenance."""
    updated = deepcopy(epoch)
    before_roles = deepcopy(updated.get("active_roles", {}))
    before_soups = deepcopy(updated.get("active_grade_soups", {}))
    _sanitize_role_origins(updated, grades)
    return updated, (before_roles != updated.get("active_roles", {}) or
                     before_soups != updated.get("active_grade_soups", {}))


def reset_active_championships(epoch: dict, *, student: dict,
                               generation: int) -> tuple[dict, bool]:
    """Metadata-only reset with lossless historical role/soup evidence.

    The current causal student becomes a *non-teaching* reset reference.
    Its optimizer step must be surpassed before future exams can award roles.
    An already reset epoch is returned unchanged, for idempotent preparation.
    """
    candidate = _pointer(student)
    previous = _pointer(epoch["baseline"])
    if (type(generation) is not int or generation < 1 or
            candidate["optimizer_step"] < previous["optimizer_step"]):
        raise ValueError("CHAMPIONSHIP_RESET_INVALID_STUDENT_OR_GENERATION")
    if epoch.get("active_championship_reset") is not None:
        return deepcopy(epoch), False
    updated = deepcopy(epoch)
    archived = {
        "source_generation": generation,
        "starting_student": candidate,
        "active_roles": updated.get("active_roles", {}),
        "active_grade_soups": updated.get("active_grade_soups", {}),
        "qualified": updated.get("qualified", []),
        "baseline_roles": updated.get("baseline_roles", {}),
    }
    updated["superseded_active_championships"] = [
        *updated.get("superseded_active_championships", []), archived]
    updated["active_roles"] = {}
    updated["active_grade_soups"] = {}
    updated["baseline_roles"] = {}
    updated["qualified"] = []
    updated["earned_role_votes_at_reset"] = 0
    updated["guidance_policy"] = EARNED_ONLY_POLICY
    updated["championship_eligibility_after_step"] = candidate["optimizer_step"]
    updated["active_championship_reset"] = {
        "policy": EARNED_ONLY_POLICY,
        "source_generation": generation,
        "student_sha256": candidate["sha256"],
        "optimizer_step": candidate["optimizer_step"],
        "old_active_role_count": len(archived["active_roles"]),
        "old_active_soup_grades": sorted(archived["active_grade_soups"]),
        "preexisting_championships_archived": True,
        "training_or_optimizer_updates": 0,
    }
    return updated, True


def rebase_active_championships(epoch: dict, *, prior_student: dict,
                                baseline: dict, generation: int) -> dict:
    """Replace an experiment's non-teaching baseline and clear earned authority.

    This is intentionally different from a routine idempotent reset: it is an
    explicit experiment rebase. The former active epoch remains archived. The
    replacement baseline is a non-teaching custody/reference checkpoint, not a
    fictitious incumbent that globally blocks later best-score capability roles.
    """
    prior = _pointer(prior_student)
    replacement = _pointer(baseline)
    previous_baseline = _pointer(epoch["baseline"])
    previous_graduate = epoch.get("previous_graduate")
    if previous_graduate is not None:
        previous_graduate = _pointer(previous_graduate)
        if replacement["optimizer_step"] < previous_graduate["optimizer_step"]:
            raise ValueError("CHAMPIONSHIP_REBASE_PREDATES_PREVIOUS_GRADUATE")
    if type(generation) is not int or generation < 1:
        raise ValueError("CHAMPIONSHIP_REBASE_INVALID_GENERATION")
    updated = deepcopy(epoch)
    archive = {
        "source_generation": generation,
        "starting_student": prior,
        "prior_baseline": previous_baseline,
        "active_roles": updated.get("active_roles", {}),
        "active_grade_soups": updated.get("active_grade_soups", {}),
        "qualified": updated.get("qualified", []),
        "baseline_roles": updated.get("baseline_roles", {}),
        "active_championship_reset": updated.get("active_championship_reset"),
    }
    updated["superseded_active_championships"] = [
        *updated.get("superseded_active_championships", []), archive]
    updated["baseline"] = replacement
    updated["active_roles"] = {}
    updated["active_grade_soups"] = {}
    updated["baseline_roles"] = {}
    updated["qualified"] = []
    updated["earned_role_votes_at_reset"] = 0
    updated["guidance_policy"] = EARNED_ONLY_POLICY
    updated["championship_eligibility_after_step"] = replacement["optimizer_step"]
    updated["baseline_challenge_required"] = False
    updated["baseline_surpassed"] = None
    updated["active_championship_reset"] = {
        "policy": EARNED_ONLY_POLICY,
        "source_generation": generation,
        "student_sha256": replacement["sha256"],
        "optimizer_step": replacement["optimizer_step"],
        "old_active_role_count": len(archive["active_roles"]),
        "old_active_soup_grades": sorted(archive["active_grade_soups"]),
        "preexisting_championships_archived": True,
        "training_or_optimizer_updates": 0,
        "experiment_baseline_rebased": True,
        "baseline_challenge_required": False,
    }
    return updated


def active_frontier(epoch: dict) -> dict:
    """Adapt one-owner-per-capability receipts to existing soup machinery."""
    roles = epoch.get("active_roles", {})
    if not isinstance(roles, dict):
        raise ValueError("CHAMPIONSHIP_EPOCH_ACTIVE_ROLES_INVALID")
    if any(not isinstance(item, dict) or item.get("capability") != cap
           for cap, item in roles.items()):
        raise ValueError("CHAMPIONSHIP_EPOCH_ACTIVE_ROLE_DRIFT")
    return {item["rubric"] + ":" + cap: item for cap, item in roles.items()
            if championship_role_qualified(item)}


def _grade_caps(course_grades, grade):
    result = tuple(course_grades[grade])
    if not result or len(result) != len(set(result)):
        raise ValueError("CHAMPIONSHIP_EPOCH_INVALID_GRADE")
    return result
