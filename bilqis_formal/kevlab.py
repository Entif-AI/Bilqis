"""Order-audited Kev choice over formally admitted lesson and exam panels.

No English-to-formula conversion. A Kev decision is returned as an existing ID.
An unstable choice or unavailable runtime yields ABSTAIN, never fake selection.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .curriculum import Panel, STAGE
from .kev_teacher import KevTeacher


def _rotations(panels):
    # Each candidate is shown in every position. This is not an independence
    # guarantee, so record all distributions and reject changed choices.
    n = len(panels)
    return [panels[i:] + panels[:i] for i in range(n)]


def choose(stage: str, role: str, panels: tuple[Panel, ...], *, teacher=None,
           recent_errors: tuple[str, ...] = ()):  # returns JSON-safe trace
    if role not in ("lesson", "exam") or not 2 <= len(panels) <= 8:
        raise ValueError("KEV_PANEL_ROLE_OR_SIZE")
    if any(p.stage != stage or p.role != role or not p.rows for p in panels):
        raise ValueError("KEV_PANEL_PROVENANCE")
    if teacher is None:
        teacher = KevTeacher()
    choices = []
    trace = []
    for order in _rotations(list(panels)):
        state = ("You are choosing which PREVALIDATED FORMAL SEMANTIC COMPOSITION is most useful to "
                 "teach or test one already-authored curriculum goal. All candidates have mechanically "
                 "verified Boolean labels. Do not change or invent mathematical laws, examples, "
                 "gold answers, learning stages or prerequisites. Student receives ONLY symbolic tokens. "
                 "Goal: " + STAGE[stage].teaching_goal +
                 " Known student errors: " + ("; ".join(recent_errors) or "none measured") +
                 ". All candidates use already admitted prerequisites.")
        instructions = ("Choose the most pedagogically informative next LESSON composition, "
                        "especially a discriminating near miss. Return exactly one offered candidate ID."
                        if role == "lesson" else
                        "Choose the most diagnostic fresh FORMATIVE EXAM composition, not the answer to any "
                        "question. Return exactly one offered candidate ID.")
        candidates = [{"candidate_id": p.id, "description": p.description} for p in order]
        result = teacher.score(state, instructions, candidates,
                               binding={"stage": stage, "role": role})
        trace.append(result)
        if result.get("status") == "ERROR":
            return {"status": "KEV_ERROR", "selected_id": None, "order_votes": choices,
                    "traces": trace, "reason": result.get("error")}
        choices.append(result["choice"])
    if len(set(choices)) > 1:
        status, winner = "ORDER_UNSTABLE", None
    elif min(t["margin"] for t in trace) < KevTeacher.MIN_MARGIN:
        status, winner = "LOW_MARGIN", None
    else:
        status, winner = "SELECTED", choices[0]
    return {"status": status, "selected_id": winner, "order_votes": choices,
            "position_coverage": {p.id: len(_rotations(list(panels))) for p in panels},
            "mean_probability": {p.id: sum(t["probabilities"][p.id] for t in trace) / len(trace)
                                 for p in panels}, "min_margin": min(t["margin"] for t in trace),
            "traces": trace}


def select_panel(panels: tuple[Panel, ...], trace: dict):
    if trace.get("status") != "SELECTED":
        return None
    return next((p for p in panels if p.id == trace.get("selected_id")), None)
