"""Championship role receipts and fresh title-match adjudication."""
from __future__ import annotations

from copy import deepcopy

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.championship_witnesses import (
    battery_from_exam, championship_role_qualified, championship_threshold_met,
    earning_witness, maxed_role, refresh_battery, verified_battery,
)
from bilqis_mlx.learning.mentor_epoch import _pointer


def _role_receipt(challenger_exam: dict, capability: str,
                  mastered: tuple[str, ...], *, prior=None, scope=None,
                  surviving_battery=None, owner_maxed=None,
                  archive_exams=(), capability_group: str,
                  checkpoint_origin_group=None, qualification_score=None) -> dict:
    pointer = challenger_exam["checkpoint"]
    score = challenger_exam["scores"][capability]
    scope = tuple(scope or (capability,))
    witness = earning_witness(challenger_exam, scope)
    proofs = {item["sha256"]: item
              for item in (prior or {}).get("qualification_witnesses", ())}
    proofs[witness["sha256"]] = witness
    for archived in archive_exams:
        extra = earning_witness(archived, scope)
        proofs[extra["sha256"]] = extra
    prior_pointer = (prior or {}).get("checkpoint") or {}
    changed_owner = bool(prior and prior_pointer.get("sha256") != pointer["sha256"])
    ancestors = set((prior or {}).get("ancestor_checkpoint_sha256s", ()))
    if changed_owner:
        ancestors.add(prior_pointer["sha256"])
    parents = [prior_pointer["sha256"]] if changed_owner else list(
        (prior or {}).get("parent_champion_sha256s", ()))
    if surviving_battery is None:
        if prior is not None:
            surviving_battery = verified_battery(prior)
        else:
            surviving_battery = battery_from_exam(challenger_exam, scope)
    if owner_maxed is None:
        owner_maxed = score["correct"] == score["total"]
    if qualification_score is None:
        if prior is not None and championship_role_qualified(prior):
            qualification_score = {
                "correct": prior.get(
                    "championship_qualification_correct", prior["correct"]),
                "total": prior.get(
                    "championship_qualification_total", prior["total"]),
            }
        else:
            qualification_score = score
    if not championship_threshold_met(qualification_score):
        ErrorBus.Raise(
            SCHOOL.MODEL_TOPOLOGY.INVALID,
            reason="championship role qualification threshold not met")
    if not isinstance(capability_group, str) or not capability_group:
        ErrorBus.raise_(
            SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID,
            reason="CHAMPIONSHIP_CAPABILITY_GROUP_REQUIRED")
    checkpoint_origin_group = (
        challenger_exam.get("checkpoint_origin_group")
        if checkpoint_origin_group is None else checkpoint_origin_group)
    if (checkpoint_origin_group is not None
            and (not isinstance(checkpoint_origin_group, str)
                 or not checkpoint_origin_group)):
        ErrorBus.raise_(
            SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID,
            reason="CHAMPIONSHIP_CHECKPOINT_ORIGIN_GROUP_INVALID")
    return {
        **({"complete_solver_provenance": deepcopy(challenger_exam["complete_solver_provenance"])}
           if "complete_solver_provenance" in challenger_exam else {}),
        "rubric": challenger_exam["rubric_sha256"],
        "cohort_rubric_sha256": challenger_exam.get(
            "cohort_rubric_sha256", challenger_exam["rubric_sha256"]),
        "capability": capability,
        "cohort_sha256": challenger_exam["cohort_sha256"],
        "assessment_scope_sha256": challenger_exam["assessment_scope_sha256"],
        "source_graph_sha256": challenger_exam["source_graph_sha256"],
        "source_oracle_sha256": challenger_exam["source_oracle_sha256"],
        "correct": score["correct"], "total": score["total"],
        "championship_qualification_correct": qualification_score["correct"],
        "championship_qualification_total": qualification_score["total"],
        "breadth": len(mastered), "perfect_capabilities": list(mastered),
        "maxed": bool(owner_maxed),
        # Capability ID is the title jurisdiction.  The opaque group is only
        # an accepted-Factory grouping context for sibling/fan-out mechanics.
        "capability_group": capability_group,
        "checkpoint_origin_group": checkpoint_origin_group,
        "qualification_witnesses": list(proofs.values()),
        "surviving_battery": list(surviving_battery),
        "checkpoint": dict(pointer),
        "ancestor_checkpoint_sha256s": sorted(ancestors),
        "parent_champion_sha256s": sorted(set(parents)),
        "evaluation_id": ("championship-epoch/" + challenger_exam["cohort_sha256"] +
                          "/" + pointer["sha256"]),
    }


def _battery_score(role: dict, results: dict) -> tuple[int, int]:
    battery = verified_battery(role)
    expected = {segment["sha256"] for segment in battery}
    if set(results) != expected:
        raise ValueError("CHAMPIONSHIP_TITLE_MATCH_BATTERY_RESULT_MISSING")
    correct = total = 0
    for segment in battery:
        offered = {question["id"] for question in segment["questions"]}
        answered = set(results[segment["sha256"]])
        if not answered <= offered:
            raise ValueError("CHAMPIONSHIP_TITLE_MATCH_BATTERY_RESULT_DRIFT")
        correct += len(answered)
        total += len(offered)
    return correct, total


def _same_current_context(reference: dict, replay: dict, capability: str) -> None:
    common = ("cohort_sha256", "rubric_sha256", "assessment_scope_sha256",
              "source_graph_sha256", "source_oracle_sha256")
    if (not isinstance(replay, dict) or
            any(replay.get(key) != reference.get(key) for key in common) or
            replay.get("cohort_rubric_sha256", replay.get("rubric_sha256")) !=
            reference.get("cohort_rubric_sha256", reference.get("rubric_sha256")) or
            capability not in replay.get("scores", {}) or
            capability not in replay.get("questions", {}) or
            capability not in replay.get("correct_questions", {})):
        raise ValueError("CHAMPIONSHIP_TITLE_MATCH_CURRENT_REPLAY_DRIFT")


def _resolve_title_match(*, capability: str, prior: dict, challenger_exam: dict,
                         incumbent_exam: dict, match: dict, qualification_scope,
                         grade_caps: tuple[str, ...]) -> tuple[dict, bool, dict]:
    incumbent = _pointer(prior["checkpoint"])
    challenger = _pointer(challenger_exam["checkpoint"])
    if (match.get("incumbent_checkpoint_sha256") != incumbent["sha256"] or
            match.get("challenger_checkpoint_sha256") != challenger["sha256"]):
        raise ValueError("CHAMPIONSHIP_TITLE_MATCH_IDENTITY_DRIFT")
    fresh_incumbent = match.get("incumbent_current_exam")
    fresh_challenger = match.get("challenger_current_exam")
    _same_current_context(challenger_exam, fresh_incumbent, capability)
    _same_current_context(challenger_exam, fresh_challenger, capability)
    if (_pointer(fresh_incumbent["checkpoint"])["sha256"] != incumbent["sha256"] or
            _pointer(fresh_challenger["checkpoint"])["sha256"] != challenger["sha256"]):
        raise ValueError("CHAMPIONSHIP_TITLE_MATCH_CURRENT_OWNER_DRIFT")
    results = match.get("battery_results")
    if not isinstance(results, dict) or set(results) != {incumbent["sha256"], challenger["sha256"]}:
        raise ValueError("CHAMPIONSHIP_TITLE_MATCH_RESULTS_INVALID")
    incumbent_correct, total = _battery_score(prior, results[incumbent["sha256"]])
    challenger_correct, challenger_total = _battery_score(
        prior, results[challenger["sha256"]])
    if challenger_total != total:
        raise ValueError("CHAMPIONSHIP_TITLE_MATCH_TOTAL_DRIFT")
    # The incumbent must strictly outperform the challenger to defend.
    # A battery tie transfers the title to the qualified challenger.
    challenger_wins = total == 0 or challenger_correct >= incumbent_correct
    winner_exam = fresh_challenger if challenger_wins else fresh_incumbent
    gate_exam = challenger_exam if challenger_wins else incumbent_exam
    winner_results = results[challenger["sha256"] if challenger_wins else incumbent["sha256"]]
    battery = refresh_battery(
        prior, gate_exam=gate_exam, fresh_exam=winner_exam,
        qualification_scope=qualification_scope, battery_correct=winner_results)
    mastered = tuple(sorted(cap for cap in grade_caps
                            if cap in winner_exam["scores"] and
                            winner_exam["scores"][cap]["correct"] ==
                            winner_exam["scores"][cap]["total"]))
    if challenger_wins:
        owner_maxed = (
            challenger_exam["scores"][capability]["correct"] ==
            challenger_exam["scores"][capability]["total"] or
            fresh_challenger["scores"][capability]["correct"] ==
            fresh_challenger["scores"][capability]["total"])
    else:
        owner_maxed = bool(prior.get("maxed", maxed_role(prior))) or (
            incumbent_exam["scores"][capability]["correct"] ==
            incumbent_exam["scores"][capability]["total"] or
            fresh_incumbent["scores"][capability]["correct"] ==
            fresh_incumbent["scores"][capability]["total"])
    receipt = _role_receipt(
        winner_exam, capability, mastered, prior=prior,
        scope=qualification_scope, surviving_battery=battery,
        owner_maxed=owner_maxed, archive_exams=(gate_exam,),
        capability_group=(
            prior.get("capability_group") or prior.get("origin_grade")),
        checkpoint_origin_group=(
            challenger_exam.get("checkpoint_origin_group")
            if challenger_wins else
            prior.get("checkpoint_origin_group",
                      prior.get("checkpoint_origin_grade"))),
        qualification_score=(
            challenger_exam["scores"][capability] if challenger_wins else {
                "correct": prior.get(
                    "championship_qualification_correct", prior["correct"]),
                "total": prior.get(
                    "championship_qualification_total", prior["total"]),
            }))
    return receipt, challenger_wins, {
        "capability": capability,
        "decision": "TITLE_WON" if challenger_wins else "TITLE_DEFENDED",
        "incumbent_sha256": incumbent["sha256"],
        "challenger_sha256": challenger["sha256"],
        "incumbent_battery_correct": incumbent_correct,
        "challenger_battery_correct": challenger_correct,
        "battery_total": total,
        "winner_sha256": receipt["checkpoint"]["sha256"],
        "qualification_scope": list(qualification_scope),
    }
