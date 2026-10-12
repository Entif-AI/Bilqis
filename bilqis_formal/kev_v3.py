"""Within-competency near-neighbor choice for v0.3 Boolean evaluations only."""
from __future__ import annotations

from .course_v3 import STAGE, validate_panels
from .kev_teacher import KevTeacher
from .kev_v2 import error_witnesses, selected_panel


def choose(stage, role, candidates, *, teacher, recent_predictions=(), anchors=None):
    validate_panels(stage, role, candidates)
    competency = STAGE[stage]
    traces, votes = [], []
    for offset in range(len(candidates)):
        order = candidates[offset:] + candidates[:offset]
        state = (
            "Decide between two prevalidated TRUE/FALSE teaching contrasts. "
            "Human-authored curriculum locks the student's skill and difficulty. "
            f"Required identity: {competency.semantic_id}. "
            f"Target: {competency.objective}. Tier: {competency.tier}. "
            f"Prerequisites: {competency.prerequisite}. Role: {role}. "
            "Both candidates have exactly one TRUE and one FALSE case, identical "
            "formula shape, task type, and example count. They differ ONLY by "
            "which single valuation bit changes. The student does NOT grade "
            "proposed answers in this stage. Never invent laws or gold labels. "
            f"Already observed gate anchors: {anchors or 'none'}. "
            f"Concrete error witnesses: {error_witnesses(recent_predictions) or 'none'}."
        )
        instruction = (
            "Select only the candidate_id of the more diagnostic near-neighbor "
            "for the declared competency and observed errors. Never select "
            "another difficulty or task, and do not prefer an option by position."
        )
        decision = teacher.score(
            state, instruction,
            [{"candidate_id": p.id, "description": p.description} for p in order],
            binding={"stage": stage, "role": role, "tier": competency.tier})
        traces.append(decision)
        if decision.get("status") == "ERROR":
            return {"status": "KEV_ERROR", "selected_id": None,
                    "order_votes": votes, "traces": traces, "error": decision.get("error")}
        votes.append(decision["choice"])
    if len(set(votes)) > 1:
        status, winner = "ORDER_UNSTABLE", None
    elif min(t["margin"] for t in traces) < KevTeacher.MIN_MARGIN:
        status, winner = "LOW_MARGIN", None
    else:
        status, winner = "SELECTED", votes[0]
    return {"status": status, "selected_id": winner,
            "order_votes": votes, "traces": traces,
            "min_margin": min(t["margin"] for t in traces),
            "target": competency.semantic_id, "tier": competency.tier}
