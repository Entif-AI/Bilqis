"""Capability-local championship advancement and one-hop fan-out."""
from __future__ import annotations

from copy import deepcopy

from bilqis_mlx.learning.championship_witnesses import (
    championship_threshold_met, maxed_role, verified_battery,
)
from bilqis_mlx.learning.mentor_epoch import _pointer

from .qualification import (
    _challenge_group, _fanout_scores, _incumbent_score,
    _initial_title_threshold_met, _primary_qualification,
)
from .receipts import _resolve_title_match, _role_receipt
from .state import _group_caps, _pair_key, _sanitize_role_groups, _settled_match
from .fanout import _advance_fanout


def _scan_primary_candidates(
        updated, original_roles, roles, group, caps, scores, pointer,
        challenger_exam, incumbent_exams, mastered, decisions, changes):
    primary = {}
    for cap in caps:
        if cap not in scores:
            continue
        prior = original_roles.get(cap)
        if prior is None:
            if not _initial_title_threshold_met(scores[cap]):
                decisions.append({
                    "group": group, "capability": cap,
                    "decision": "INITIAL_TITLE_THRESHOLD_NOT_MET",
                    "correct": scores[cap]["correct"],
                    "total": scores[cap]["total"],
                    "minimum_percent_exclusive": 90,
                    "challenger_sha256": pointer["sha256"],
                })
                continue
            roles[cap] = _role_receipt(
                challenger_exam, cap, mastered, scope=(cap,),
                owner_maxed=(scores[cap]["correct"] == scores[cap]["total"]),
                capability_group=group)
            changes.append(cap)
            continue
        prior_pointer = _pointer(prior["checkpoint"])
        if not championship_threshold_met(scores[cap]):
            decisions.append({
                "group": group, "capability": cap,
                "decision": "TITLE_THRESHOLD_NOT_MET",
                "correct": scores[cap]["correct"],
                "total": scores[cap]["total"],
                "minimum_percent_exclusive": 90,
                "challenger_sha256": pointer["sha256"],
            })
            continue
        if prior_pointer["sha256"] == pointer["sha256"]:
            if scores[cap]["correct"] > prior.get("correct", -1):
                roles[cap] = _role_receipt(
                    challenger_exam, cap, mastered, prior=prior, scope=(cap,),
                    surviving_battery=verified_battery(prior),
                    owner_maxed=bool(prior.get("maxed", maxed_role(prior))) or
                    scores[cap]["correct"] == scores[cap]["total"],
                    capability_group=group)
            continue
        settled = _settled_match(
            updated, cap, prior_pointer["sha256"], pointer["sha256"])
        if settled is not None:
            decisions.append({
                "group": group, "capability": cap,
                "decision": "TITLE_MATCH_ALREADY_SETTLED",
                "incumbent_sha256": prior_pointer["sha256"],
                "challenger_sha256": pointer["sha256"],
                "settled_winner_sha256": settled.get("winner_sha256"),
            })
            continue
        incumbent_score = _incumbent_score(
            cap, prior, challenger_exam, incumbent_exams)
        qualification = _primary_qualification(scores[cap], incumbent_score)
        if qualification is not None:
            primary[cap] = (prior, qualification)
    return primary


def _resolve_primary_matches(
        updated, roles, group, caps, pointer, challenger_exam, incumbent_exams,
        primary, title_matches, decisions, changes):
    primary_won = False
    for cap, (prior, qualification) in primary.items():
        match = title_matches.get(cap)
        if match is None:
            decisions.append({
                "group": group, "capability": cap,
                "decision": "TITLE_MATCH_REQUIRED",
                "qualification": qualification,
                "qualification_scope": [cap],
                "incumbent_sha256": prior["checkpoint"]["sha256"],
                "challenger_sha256": pointer["sha256"],
            })
            continue
        gate_incumbent = incumbent_exams.get(prior["checkpoint"]["sha256"])
        if gate_incumbent is None:
            raise ValueError("CHAMPIONSHIP_TITLE_MATCH_INCUMBENT_GATE_MISSING")
        receipt, won, verdict = _resolve_title_match(
            capability=cap, prior=prior, challenger_exam=challenger_exam,
            incumbent_exam=gate_incumbent, match=match,
            qualification_scope=(cap,), grade_caps=caps)
        roles[cap] = receipt
        updated["settled_matchups"][_pair_key(
            cap, verdict["incumbent_sha256"], verdict["challenger_sha256"])] = {
                **verdict,
                "group": group,
                "qualification": qualification,
            }
        decisions.append({
            "group": group, **verdict, "qualification": qualification})
        if won:
            primary_won = True
            if cap not in changes:
                changes.append(cap)
    return primary_won


def advance_epoch(epoch: dict, *, capability_groups: dict, challenger_exam: dict,
                  incumbent_exams: dict, title_matches=None,
                  fanout_screen=None) -> tuple[dict, tuple[str, ...], tuple[dict, ...]]:
    """Capability-local title fights with one non-recursive same-group fan-out."""
    census = tuple(
        capability
        for capabilities in capability_groups.values()
        for capability in capabilities)
    if len(census) != len(set(census)):
        raise ValueError("CHAMPIONSHIP_CAPABILITY_GROUP_AMBIGUOUS_OR_ABSENT")
    scores = challenger_exam["scores"]
    pointer = _pointer(challenger_exam["checkpoint"])
    updated = deepcopy(epoch)
    updated.setdefault("settled_matchups", {})
    _sanitize_role_groups(updated, capability_groups)
    roles = updated.setdefault("active_roles", {})
    original_roles = deepcopy(roles)
    updated.setdefault("active_grade_soups", {})
    changes, decisions = [], []
    title_matches = title_matches or {}
    if pointer["optimizer_step"] <= epoch.get("championship_eligibility_after_step", -1):
        return updated, (), ()

    group = _challenge_group(capability_groups, challenger_exam)
    caps = _group_caps(capability_groups, group)
    mastered = tuple(sorted(
        cap for cap in caps if cap in scores and
        scores[cap]["correct"] == scores[cap]["total"]))

    primary = _scan_primary_candidates(
        updated, original_roles, roles, group, caps, scores, pointer,
        challenger_exam, incumbent_exams, mastered, decisions, changes)
    primary_won = _resolve_primary_matches(
        updated, roles, group, caps, pointer, challenger_exam, incumbent_exams,
        primary, title_matches, decisions, changes)

    # A real primary takeover opens one and only one same-grade sibling scan.
    # Secondary wins never participate in deciding whether another scan occurs.
    if primary_won:
        _advance_fanout(
            updated, original_roles, roles, primary, group, caps, scores, pointer,
            challenger_exam, title_matches, fanout_screen, decisions, changes)

    return updated, tuple(changes), tuple(decisions)
