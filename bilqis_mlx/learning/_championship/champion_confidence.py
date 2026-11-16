"""Small, source-gated confidence advice from frozen whole-student champions.

Votes affect the causal student's supervised gradient, not independent exams,
oracle golds, optimizer lineage, or student checkpoint selection. Live adviser
inference is deduplicated by checkpoint, but each active maxed capability role
contributes one direct vote; a shared checkpoint is counted once per role.
"""
from __future__ import annotations

from enum import Enum
import numpy as np
from .championship_witnesses import maxed_role


POLICY = "bilqis.mlx.champion-confidence/v1"
MAX_INFLUENCE = 0.08
TEMPERATURE = 1.5
MIN_TYPED_CLASSES = 2
UNMASKED_VOTE_FIELDS = 2
MASKED_VOTE_FIELDS = 3


class ChampionConfidenceError(str, Enum):
    INVALID_VOTE = "CHAMPION_CONFIDENCE_INVALID_VOTE"
    INVALID_VOTE_MASK = "CHAMPION_CONFIDENCE_INVALID_VOTE_MASK"


def _active_roles(snapshot, grade):
    roles = snapshot.get("roles") if isinstance(snapshot, dict) else None
    if (not isinstance(roles, list) or snapshot.get("grade") != grade or
            len(roles) != snapshot.get("vote_count") or
            len({role.get("capability") for role in roles}) != len(roles) or
            any(not role.get("capability", "").startswith(grade + ".") for role in roles)):
        raise ValueError("CHAMPION_CONFIDENCE_ACTIVE_GRADE_ROLE_DRIFT")
    return roles


def _active_role_item(frontier, role):
    item = frontier.get(role["rubric"] + ":" + role["capability"])
    if (item is None or item.get("capability") != role["capability"] or
            item.get("checkpoint", {}).get("sha256") != role.get("checkpoint_sha256")):
        raise ValueError("CHAMPION_CONFIDENCE_ACTIVE_ROLE_PROVENANCE_DRIFT")
    return item


def champion_roster(frontier: dict, grade: str, *, snapshot=None) -> tuple[dict, ...]:
    """One direct mentor per checkpoint with positive proven perfect breadth.

    A frozen grade soup snapshot identifies the *current* champion roles.
    Historical examinations remain in the frontier for provenance, but an
    earlier-rubric role is not another independently entitled mentor vote.
    Best-score roles below perfection remain valid championship/soup evidence,
    but contribute zero direct perfect-breadth mentor influence.
    The optional unscoped form is retained for source-only legacy fixtures.
    """
    if snapshot is not None:
        roles = _active_roles(snapshot, grade)
        selected = []
        for role in roles:
            item = _active_role_item(frontier, role)
            selected.append(item)
    else:
        selected = frontier.values()
    unique = {}
    for item in selected:
        if not item["capability"].startswith(grade + "."):
            continue
        breadth = item.get("breadth")
        mastered = item.get("perfect_capabilities")
        if (type(breadth) is not int or breadth < 0 or
                not isinstance(mastered, list) or len(mastered) != breadth or
                not item["checkpoint"].get("model_and_native_adamw")):
            raise ValueError("CHAMPION_CONFIDENCE_RANK_NOT_VERIFIED")
        # Best-score championship is broader than perfect-witness status.
        # A subperfect role stays valid for title/soup accounting but must not
        # itself recruit direct perfect-breadth advice. If this same checkpoint
        # owns another perfect role in the grade, that role will recruit it once.
        if breadth == 0 or item["capability"] not in mastered:
            continue
        sha = item["checkpoint"]["sha256"]
        if sha not in unique or breadth > unique[sha]["breadth"]:
            unique[sha] = {"checkpoint": item["checkpoint"], "breadth": breadth}
    return tuple(unique[sha] for sha in sorted(unique))


def perfect_role_roster(frontier: dict, grade_soups: dict) -> tuple[dict, ...]:
    """Inventory active maxed roles; the trainer scopes direct votes to the lesson grade.

    Several capability roles may share one intact checkpoint. Inference may be
    deduplicated by checkpoint, but voting weight remains the number of active
    perfect roles that checkpoint owns, not its historical/global breadth.
    """
    if not isinstance(frontier, dict) or not isinstance(grade_soups, dict):
        raise ValueError("CHAMPION_CONFIDENCE_ROLE_ROSTER_INVALID")
    unique = {}
    for grade, snapshot in sorted(grade_soups.items()):
        roles = _active_roles(snapshot, grade)
        for role in roles:
            capability = role["capability"]
            item = _active_role_item(frontier, role)
            correct, total = role.get("correct"), role.get("total")
            if (type(correct) is not int or type(total) is not int or total < 1 or
                    not 0 <= correct <= total):
                raise ValueError("CHAMPION_CONFIDENCE_ACTIVE_ROLE_SCORE_DRIFT")
            entitled = maxed_role(item)
            if role.get("maxed", correct == total) != entitled:
                raise ValueError("CHAMPION_CONFIDENCE_ACTIVE_ROLE_ENTITLEMENT_DRIFT")
            if not entitled:
                continue
            if not item.get("checkpoint", {}).get("model_and_native_adamw"):
                raise ValueError("CHAMPION_CONFIDENCE_PERFECT_ROLE_DRIFT")
            pointer = item["checkpoint"]
            sha = pointer["sha256"]
            mentor = unique.setdefault(sha, {
                "checkpoint": pointer,
                "breadth": 0,
                "source_grade_votes": {},
                "capabilities": [],
            })
            mentor["breadth"] += 1
            mentor["source_grade_votes"][grade] = (
                mentor["source_grade_votes"].get(grade, 0) + 1)
            mentor["capabilities"].append(capability)
    return tuple({**unique[sha],
                  "source_grade_votes": dict(sorted(
                      unique[sha]["source_grade_votes"].items())),
                  "capabilities": tuple(sorted(unique[sha]["capabilities"]))}
                 for sha in sorted(unique))


def vote_targets(votes, labels, *, eligible_capabilities: int,
                 teacher_distill: float):
    """Return soft targets and bounded per-row weights for gold-agreeing votes.

    Each champion contributes MAX_INFLUENCE * teacher_distill * breadth/N,
    at most MAX_INFLUENCE in total for any row. Wrong votes are ignored.
    Teacher-selected distillation strength remains authoritative.
    """
    return vote_targets_typed(votes, labels, classes=2,
                              eligible_capabilities=eligible_capabilities,
                              teacher_distill=teacher_distill)


def vote_targets_typed(votes, labels, *, classes: int,
                       eligible_capabilities: int, teacher_distill: float):
    """The same source-gold-agreeing bounded confidence for any admitted head.

    Dense one-hot class targets are never allocated. A wrong mentor simply
    contributes no advice; independent scorer logits remain untouched.
    """
    labels = np.asarray(labels, dtype=np.int64)
    if (type(classes) is not int or classes < MIN_TYPED_CLASSES or
            labels.ndim != 1 or (labels < 0).any() or
            (labels >= classes).any() or
            type(eligible_capabilities) is not int or eligible_capabilities < 1 or
            not np.isfinite(teacher_distill) or not 0 <= teacher_distill <= 1):
        raise ValueError("CHAMPION_CONFIDENCE_INVALID_INPUT")
    target = np.zeros((len(labels), classes), dtype=np.float64)
    weight = np.zeros(len(labels), dtype=np.float64)
    for vote in votes:
        if len(vote) == UNMASKED_VOTE_FIELDS:
            breadth, raw = vote
            eligible_mask = None
        elif len(vote) == MASKED_VOTE_FIELDS:
            breadth, raw, eligible_mask = vote
        else:
            raise ValueError(ChampionConfidenceError.INVALID_VOTE.value)
        raw = np.asarray(raw, dtype=np.float64)
        if (type(breadth) not in (int, float) or
                not np.isfinite(breadth) or not 0 < breadth <= eligible_capabilities or
                raw.shape != (len(labels), classes) or not np.isfinite(raw).all()):
            raise ValueError(ChampionConfidenceError.INVALID_VOTE.value)
        accepted = np.argmax(raw, axis=-1) == labels
        if eligible_mask is not None:
            eligible_mask = np.asarray(eligible_mask)
            if (eligible_mask.shape != (len(labels),) or
                    eligible_mask.dtype.kind != "b"):
                raise ValueError(ChampionConfidenceError.INVALID_VOTE_MASK.value)
            accepted &= eligible_mask
        if not accepted.any():
            continue
        scaled = raw / TEMPERATURE
        scaled -= scaled.max(axis=-1, keepdims=True)
        probabilities = np.exp(scaled)
        probabilities /= probabilities.sum(axis=-1, keepdims=True)
        contribution = MAX_INFLUENCE * teacher_distill * breadth / eligible_capabilities
        target[accepted] += contribution * probabilities[accepted]
        weight[accepted] += contribution
    active = weight > 0
    target[active] /= weight[active, None]
    target[~active] = 1.0 / classes
    weight = np.minimum(weight, MAX_INFLUENCE)
    return target.astype(np.float32), weight.astype(np.float32)
