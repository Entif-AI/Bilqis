"""Qualification and comparable-score helpers for championship epochs."""
from __future__ import annotations

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.championship_witnesses import championship_threshold_met
from bilqis_mlx.learning.mentor_epoch import _pointer

from .receipts import _same_current_context
from .state import _group_caps, _role_group, _settled_match


def _invalid(reason):
    ErrorBus.raise_(SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID, reason=reason)


def _challenge_group(capability_groups: dict, challenger_exam: dict) -> str:
    group = challenger_exam.get("challenge_group")
    if group not in capability_groups:
        _invalid("CHAMPIONSHIP_EPOCH_CHALLENGE_GROUP_INVALID")
    return group


def _exam_matches_capability(challenger: dict, incumbent: dict,
                             capability: str) -> None:
    common = ("cohort_sha256", "rubric_sha256", "assessment_scope_sha256",
              "source_graph_sha256", "source_oracle_sha256")
    if (not isinstance(incumbent, dict) or
            any(incumbent.get(field) != challenger.get(field) for field in common) or
            incumbent.get("cohort_rubric_sha256", incumbent.get("rubric_sha256")) !=
            challenger.get("cohort_rubric_sha256", challenger.get("rubric_sha256")) or
            capability not in incumbent.get("scores", {}) or
            capability not in challenger.get("scores", {}) or
            incumbent["scores"][capability].get("total") !=
            challenger["scores"][capability].get("total")):
        raise ValueError("CHAMPIONSHIP_EPOCH_SAME_COHORT_REQUIRED")


def needed_incumbents(epoch: dict, *, capability_groups: dict,
                      challenger_exam: dict) -> dict:
    """Load only current-group owners needed for primary and one-hop fan-out screens."""
    roles = epoch.get("active_roles", {})
    scores = challenger_exam["scores"]
    challenger = _pointer(challenger_exam["checkpoint"])
    group = _challenge_group(capability_groups, challenger_exam)
    needed = {}
    for cap in _group_caps(capability_groups, group):
        if cap not in scores:
            continue
        prior = roles.get(cap)
        if prior is None:
            continue
        if _role_group(prior) != group:
            continue
        pointer = _pointer(prior["checkpoint"])
        if pointer["sha256"] == challenger["sha256"]:
            continue
        if _settled_match(epoch, cap, pointer["sha256"], challenger["sha256"]):
            continue
        needed[pointer["sha256"]] = pointer
    return needed


def _incumbent_score(capability: str, prior: dict, challenger_exam: dict,
                     incumbent_exams: dict) -> dict:
    prior_pointer = _pointer(prior["checkpoint"])
    incumbent = incumbent_exams.get(prior_pointer["sha256"])
    if incumbent is None:
        raise ValueError("CHAMPIONSHIP_EPOCH_INCUMBENT_EXAM_REQUIRED")
    _exam_matches_capability(challenger_exam, incumbent, capability)
    return incumbent["scores"][capability]


def _primary_qualification(candidate: dict, incumbent: dict) -> str | None:
    if candidate["total"] != incumbent["total"]:
        raise ValueError("CHAMPIONSHIP_EPOCH_SCORE_TOTAL_DRIFT")
    if candidate["correct"] > incumbent["correct"]:
        return "STRICT_GAIN"
    if candidate["correct"] == candidate["total"]:
        return "CAPABILITY_MAX"
    return None


def _initial_title_threshold_met(score: dict) -> bool:
    """Require capability-local proficiency strictly above 90%."""
    return championship_threshold_met(score)


def _fanout_scores(capability: str, prior: dict, challenger: dict,
                   screen: dict) -> tuple[dict, dict]:
    incumbent = _pointer(prior["checkpoint"])
    contender = _pointer(challenger["checkpoint"])
    if (not isinstance(screen, dict) or
            screen.get("incumbent_checkpoint_sha256") != incumbent["sha256"] or
            screen.get("challenger_checkpoint_sha256") != contender["sha256"]):
        raise ValueError("CHAMPIONSHIP_FANOUT_SCREEN_IDENTITY_DRIFT")
    incumbent_exam = screen.get("incumbent_exam")
    challenger_exam = screen.get("challenger_exam")
    # The primary takeover may have been proved on a different capability-
    # local panel.  Fan-out compares the sibling owner and challenger on the
    # sibling's own fresh current panel; only checkpoint identity is inherited
    # from the primary challenger.
    _same_current_context(challenger_exam, incumbent_exam, capability)
    _same_current_context(challenger_exam, challenger_exam, capability)
    if (_pointer(incumbent_exam["checkpoint"])["sha256"] != incumbent["sha256"] or
            _pointer(challenger_exam["checkpoint"])["sha256"] != contender["sha256"]):
        raise ValueError("CHAMPIONSHIP_FANOUT_SCREEN_OWNER_DRIFT")
    before = incumbent_exam["scores"][capability]
    after = challenger_exam["scores"][capability]
    if (not isinstance(before, dict) or not isinstance(after, dict) or
            type(before.get("correct")) is not int or
            type(before.get("total")) is not int or
            type(after.get("correct")) is not int or
            type(after.get("total")) is not int or
            before["total"] != after["total"] or before["total"] < 1 or
            not 0 <= before["correct"] <= before["total"] or
            not 0 <= after["correct"] <= after["total"]):
        raise ValueError("CHAMPIONSHIP_FANOUT_SCREEN_SCORE_DRIFT")
    return before, after
