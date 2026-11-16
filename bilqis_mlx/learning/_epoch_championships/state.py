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
        "capability_group": _role_group(role),
        "reason": reason,
        "role": deepcopy(role),
    })


def _capability_group(capability: str, capability_groups: dict) -> str:
    matches = tuple(group for group, capabilities in capability_groups.items()
                    if capability in capabilities)
    if len(matches) != 1:
        raise ValueError("CHAMPIONSHIP_CAPABILITY_GROUP_AMBIGUOUS_OR_ABSENT")
    return matches[0]


def _role_group(role: dict) -> str | None:
    if not isinstance(role, dict):
        return None
    return role.get("capability_group", role.get("origin_grade"))


def _checkpoint_origin_group(role: dict) -> str | None:
    if not isinstance(role, dict):
        return None
    return role.get(
        "checkpoint_origin_group",
        role.get("checkpoint_origin_grade"),
    )


def _sanitize_role_groups(updated: dict, capability_groups: dict) -> None:
    """Validate grouping without turning a developmental group into title authority."""
    roles = updated.setdefault("active_roles", {})
    invalid = []
    for capability, role in list(roles.items()):
        if not any(capability in capabilities
                   for capabilities in capability_groups.values()):
            continue
        group = _capability_group(capability, capability_groups)
        if capability not in _group_caps(capability_groups, group):
            raise ValueError("CHAMPIONSHIP_ACTIVE_ROLE_CAPABILITY_UNKNOWN")
        recorded_group = _role_group(role)
        if not championship_role_qualified(role):
            _archive_invalid_role(
                updated, capability, role, "CHAMPIONSHIP_THRESHOLD_NOT_MET")
            del roles[capability]
            invalid.append(capability)
            continue
        if recorded_group != group:
            reason = ("CAPABILITY_GROUP_MISSING" if recorded_group is None else
                      "CAPABILITY_GROUP_DRIFT")
            _archive_invalid_role(updated, capability, role, reason)
            del roles[capability]
            invalid.append(capability)
            continue
        checkpoint_origin = _checkpoint_origin_group(role)
        if (checkpoint_origin is not None
                and (not isinstance(checkpoint_origin, str)
                     or not checkpoint_origin)):
            _archive_invalid_role(
                updated, capability, role, "CHECKPOINT_ORIGIN_PROVENANCE_INVALID")
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


def sanitize_role_groups(epoch: dict, *, capability_groups: dict) -> tuple[dict, bool]:
    """Public neural-inert validation gate for active capability grouping."""
    updated = deepcopy(epoch)
    before_roles = deepcopy(updated.get("active_roles", {}))
    before_soups = deepcopy(updated.get("active_grade_soups", {}))
    _sanitize_role_groups(updated, capability_groups)
    return updated, (before_roles != updated.get("active_roles", {}) or
                     before_soups != updated.get("active_grade_soups", {}))


def sanitize_role_origins(epoch: dict, *, grades: dict) -> tuple[dict, bool]:
    """Legacy receipt reader retained until the mentor-epoch migration owns deletion."""
    return sanitize_role_groups(epoch, capability_groups=grades)


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


def _group_caps(capability_groups, group):
    result = tuple(capability_groups[group])
    if not result or len(result) != len(set(result)):
        ErrorBus.raise_(
            SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID,
            reason="CHAMPIONSHIP_EPOCH_INVALID_GROUP")
    return result


# Read-only compatibility names for pre-v1.2 mentor-epoch callers. New title
# code must use the capability-group names above.
_capability_grade = _capability_group
_grade_caps = _group_caps
_sanitize_role_origins = _sanitize_role_groups
