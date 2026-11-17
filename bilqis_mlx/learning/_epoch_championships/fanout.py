"""One-hop same-group fan-out after a primary championship takeover."""
from __future__ import annotations

from bilqis_mlx.learning.mentor_epoch import _pointer

from .qualification import _fanout_scores
from .receipts import _resolve_title_match
from .state import _pair_key, _settled_match, _settlement_receipt_context


def _advance_fanout(
        updated, original_roles, roles, primary, group, caps, scores, pointer,
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
    # Primary title evidence is intentionally capability-local.  A real
    # takeover therefore has no obligation to have pre-measured its siblings.
    # The takeover itself opens exactly one bounded same-group screen, which
    # the runtime satisfies with each sibling's own capability-local panel.
    siblings = eligible
    if siblings and fanout_screen is None:
        decisions.append({
            "group": group,
            "decision": "FANOUT_SCREEN_REQUIRED",
            "capabilities": siblings,
            "challenger_sha256": pointer["sha256"],
        })
        return
    for cap in siblings:
        prior = original_roles[cap]
        prior_pointer = _pointer(prior["checkpoint"])
        if fanout_screen is None or cap not in fanout_screen:
            raise ValueError("CHAMPIONSHIP_FANOUT_SCREEN_CAPABILITY_MISSING")
        incumbent_score, candidate = _fanout_scores(
            cap, prior, challenger_exam, fanout_screen[cap])
        if candidate["correct"] < incumbent_score["correct"]:
            continue
        match = title_matches.get(cap)
        if match is None:
            decisions.append({
                "group": group, "capability": cap,
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
            cap, verdict["incumbent_sha256"], verdict["challenger_sha256"],
            updated.get("comparison_context_sha256"))] = {
                **verdict,
                "group": group,
                "qualification": "FANOUT_MATCH_OR_BEAT",
                **_settlement_receipt_context(updated),
            }
        decisions.append({
            "group": group, **verdict,
            "qualification": "FANOUT_MATCH_OR_BEAT",
        })
        if won and cap not in changes:
            changes.append(cap)
