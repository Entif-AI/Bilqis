"""Same auditable Kev choice for lessons and formative exams, within one tier.

The exact human-authored target, eligible structure, and comparable controls
are resolved before Kev is called. Its decision cannot widen the curriculum.
"""
from __future__ import annotations

from .course_v2 import STAGE, validate_panels
from .kev_teacher import KevTeacher


def error_witnesses(predictions, limit=4):
    """Give Kev the discriminating *observations*, never a generic 'evaluation' tag."""
    failures = [p for p in predictions if p["prediction"] != p["gold"]]
    return [{"task": e["task"], "expression": e["input"].get("expression"),
             "valuation": e["input"].get("valuation"),
             "proposed_answer": e["input"].get("proposed_answer"),
             "expected": e["gold"], "observed": e["prediction"],
             "prob_gold": round(e["prob_gold"], 6)} for e in failures[:limit]]


def choose(stage, role, candidates, *, teacher=None, recent_predictions=(), anchors=None):
    validate_panels(stage, role, candidates)
    if teacher is None:
        teacher = KevTeacher()
    required = STAGE[stage]
    traces, votes = [], []
    for i in range(len(candidates)):
        offered = candidates[i:] + candidates[:i]
        state = (
            "You are selecting a formally validated, learner-specific controlled contrast. "
            "The HUMANS already fixed the competence, difficulty stratum, prerequisites, "
            "task types, question count and oracle. You cannot change any of those. "
            f"Required semantic target: {required.semantic_id}. "
            f"Required tier (structural hypothesis, not empirically calibrated): {required.tier}. "
            f"Teaching objective: {required.competency}. "
            f"Role: {role}. All alternatives have the identical AST shape and one TRUE/one FALSE "
            "evaluation and matched CORRECT/INCORRECT judgments. "
            f"Empirical reference anchors from currently observed student: {anchors or 'not measured'}. "
            f"Actual error witnesses: {error_witnesses(recent_predictions) or 'none observed'}. "
            "The only differing feature of each eligible candidate is WHICH single valuation "
            "variable changes across an otherwise matched positive/negative pair."
        )
        question = (
            "Which offered candidate_id is the more discriminating near-neighbor contrast "
            "for the stated competency and observed error mechanism? Choose one ID only. "
            "Do not rank unrelated tiers, predict mathematical gold, invent an alternative, "
            "or prefer an option simply because it is earlier in the list."
        )
        result = teacher.score(state, question, [
            {"candidate_id": p.id, "description": p.description} for p in offered],
            binding={"stage": stage, "role": role, "tier": required.tier})
        traces.append(result)
        if result.get("status") == "ERROR":
            return {"status": "KEV_ERROR", "selected_id": None,
                    "order_votes": votes, "traces": traces, "error": result.get("error")}
        votes.append(result["choice"])
    if len(set(votes)) != 1:
        status, winner = "ORDER_UNSTABLE", None
    elif min(t["margin"] for t in traces) < KevTeacher.MIN_MARGIN:
        status, winner = "LOW_MARGIN", None
    else:
        status, winner = "SELECTED", votes[0]
    return {"status": status, "selected_id": winner, "order_votes": votes,
            "position_coverage": {p.id: len(candidates) for p in candidates},
            "mean_probability": {p.id: sum(t["probabilities"][p.id] for t in traces) / len(traces)
                                 for p in candidates},
            "min_margin": min(t["margin"] for t in traces),
            "traces": traces, "tier": required.tier, "target": required.semantic_id}


def selected_panel(candidates, result):
    if result.get("status") != "SELECTED":
        return None
    return next((p for p in candidates if p.id == result["selected_id"]), None)
