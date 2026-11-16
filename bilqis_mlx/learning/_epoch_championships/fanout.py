"""One-hop same-grade fan-out after a primary championship takeover."""
from __future__ import annotations

from bilqis_mlx.learning.mentor_epoch import _pointer

from .qualification import _fanout_scores
from .receipts import _resolve_title_match
from .state import _pair_key, _settled_match


def _advance_fanout(
        updated, original_roles, roles, primary, grade, caps, scores, pointer,
        challenger_exam, title_matches, fanout_screen, decisions, changes):
    """Apply exactly one sibling scan; secondary wins never recurse."""
    eligible = [
        cap for cap in caps if cap not in primary and
        (prior := original_roles.get(cap)) is not None and
        _pointer(prior["checkpoint"])["sha256"] != pointer["sha256"] and
        _settled_match(
            updated, cap, _pointer(prior["checkpoint"])["sha256"],
            pointer["sha256"]) is None
    ]
    for cap in (item for item in eligible if item not in scores):
        decisions.append({
            "grade": grade,
            "capability": cap,
            "decision": "FANOUT_DEFERRED_UNMEASURED",
            "challenger_sha256": pointer["sha256"],
            "reason": "CAPABILITY_ABSENT_FROM_CURRENT_COHORT",
        })
    siblings = [cap for cap in eligible if cap in scores]
    if siblings and fanout_screen is None:
        decisions.append({
            "grade": grade,
            "decision": "FANOUT_SCREEN_REQUIRED",
            "capabilities": siblings,
            "challenger_sha256": pointer["sha256"],
        })
        return
    for cap in siblings:
        prior = original_roles[cap]
        prior_pointer = _pointer(prior["checkpoint"])
        if cap not in fanout_screen:
            raise ValueError("CHAMPIONSHIP_FANOUT_SCREEN_CAPABILITY_MISSING")
        incumbent_score, candidate = _fanout_scores(
            cap, prior, challenger_exam, fanout_screen[cap])
        if candidate["correct"] < incumbent_score["correct"]:
            continue
        match = title_matches.get(cap)
        if match is None:
            decisions.append({
                "grade": grade, "capability": cap,
                "decision": "FANOUT_TITLE_MATCH_REQUIRED",
                "qualification": "FANOUT_MATCH_OR_BEAT",
                "qualification_scope": [cap],
                "incumbent_sha256": prior_pointer["sha256"],
                "challenger_sha256": pointer["sha256"],
            })
            continue
        receipt, won, verdict = _resolve_title_match(
            capability=cap, prior=prior,
            challenger_exam=fanout_screen[cap]["challenger_exam"],
            incumbent_exam=fanout_screen[cap]["incumbent_exam"], match=match,
            qualification_scope=(cap,), grade_caps=caps)
        roles[cap] = receipt
        updated["settled_matchups"][_pair_key(
            cap, verdict["incumbent_sha256"], verdict["challenger_sha256"])] = {
                **verdict,
                "grade": grade,
                "qualification": "FANOUT_MATCH_OR_BEAT",
            }
        decisions.append({
            "grade": grade, **verdict,
            "qualification": "FANOUT_MATCH_OR_BEAT",
        })
        if won and cap not in changes:
            changes.append(cap)
