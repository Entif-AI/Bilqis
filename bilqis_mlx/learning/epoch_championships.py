"""Capability-local defended championship ownership within one curriculum epoch.

Historical champion and soup receipts stay in the old state fields. The
epoch owns current title holders, surviving batteries and frozen vote entitlements.
This module never reads tensors, trains a student, or changes an optimizer.
"""
from __future__ import annotations

from copy import deepcopy

from bilqis_mlx.learning.championship_witnesses import (
    battery_from_exam, earning_witness, maxed_role, refresh_battery,
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
        "origin_grade": role.get("origin_grade"),
        "reason": reason,
        "role": deepcopy(role),
    })


def _capability_grade(capability: str, grades: dict) -> str:
    matches = tuple(grade for grade, capabilities in grades.items()
                    if capability in capabilities)
    if len(matches) != 1:
        raise ValueError("CHAMPIONSHIP_CAPABILITY_GROUP_AMBIGUOUS_OR_ABSENT")
    return matches[0]


def _sanitize_role_origins(updated: dict, grades: dict) -> None:
    """Keep title jurisdiction distinct from checkpoint-training provenance."""
    roles = updated.setdefault("active_roles", {})
    invalid = []
    for capability, role in list(roles.items()):
        title_grade = _capability_grade(capability, grades)
        if title_grade not in grades or capability not in _grade_caps(grades, title_grade):
            raise ValueError("CHAMPIONSHIP_ACTIVE_ROLE_CAPABILITY_UNKNOWN")
        origin = role.get("origin_grade") if isinstance(role, dict) else None
        if origin != title_grade:
            reason = ("TITLE_ORIGIN_PROVENANCE_MISSING" if origin is None else
                      "CROSS_GRADE_TITLE_OWNER")
            _archive_invalid_role(updated, capability, role, reason)
            del roles[capability]
            invalid.append(capability)
            continue
        # Historical receipts predate the explicit separation between the
        # capability's title grade and the grade whose retained optimizer update
        # produced the whole-student checkpoint.  At that time they were forced
        # to be identical, so the legacy field is sufficient migration proof.
        checkpoint_origin = role.get("checkpoint_origin_grade")
        if checkpoint_origin is None:
            role["checkpoint_origin_grade"] = origin
        elif checkpoint_origin not in grades:
            _archive_invalid_role(
                updated, capability, role,
                "CHECKPOINT_ORIGIN_PROVENANCE_INVALID")
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


def sanitize_role_origins(epoch: dict, *, grades: dict) -> tuple[dict, bool]:
    """Public neural-inert migration gate for active title provenance."""
    updated = deepcopy(epoch)
    before_roles = deepcopy(updated.get("active_roles", {}))
    before_soups = deepcopy(updated.get("active_grade_soups", {}))
    _sanitize_role_origins(updated, grades)
    return updated, (before_roles != updated.get("active_roles", {}) or
                     before_soups != updated.get("active_grade_soups", {}))


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
    return {item["rubric"] + ":" + cap: item for cap, item in roles.items()}


def _grade_caps(course_grades, grade):
    result = tuple(course_grades[grade])
    if not result or len(result) != len(set(result)):
        raise ValueError("CHAMPIONSHIP_EPOCH_INVALID_GRADE")
    return result


def _challenge_grade(epoch: dict, grades: dict, challenger_exam: dict) -> str:
    grade = challenger_exam.get("challenge_grade", epoch.get("introduced_grade"))
    if grade not in grades:
        raise ValueError("CHAMPIONSHIP_EPOCH_CHALLENGE_GRADE_INVALID")
    return grade


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


def needed_incumbents(epoch: dict, *, grades: dict,
                      challenger_exam: dict) -> dict:
    """Load only title-grade owners needed for primary and one-hop fan-out screens."""
    roles = epoch.get("active_roles", {})
    scores = challenger_exam["scores"]
    challenger = _pointer(challenger_exam["checkpoint"])
    grade = _challenge_grade(epoch, grades, challenger_exam)
    needed = {}
    for cap in _grade_caps(grades, grade):
        if cap not in scores:
            continue
        prior = roles.get(cap)
        if prior is None:
            continue
        if prior.get("origin_grade") != grade:
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
    """Require at least 66% proficiency before an empty title can be claimed."""
    if (not isinstance(score, dict) or type(score.get("correct")) is not int or
            type(score.get("total")) is not int or score["total"] < 1 or
            not 0 <= score["correct"] <= score["total"]):
        raise ValueError("CHAMPIONSHIP_INITIAL_TITLE_SCORE_INVALID")
    return score["correct"] * 100 >= score["total"] * 66


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
    _same_current_context(challenger, incumbent_exam, capability)
    _same_current_context(challenger, challenger_exam, capability)
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


def _role_receipt(challenger_exam: dict, capability: str,
                  mastered: tuple[str, ...], *, prior=None, scope=None,
                  surviving_battery=None, owner_maxed=None,
                  archive_exams=(), origin_grade=None,
                  checkpoint_origin_grade=None) -> dict:
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
        "breadth": len(mastered), "perfect_capabilities": list(mastered),
        "maxed": bool(owner_maxed),
        # `origin_grade` remains the stable title-jurisdiction field used by
        # soups/mentor routing.  The optimizer visit that created the intact
        # whole-student checkpoint is separate provenance and may differ.
        "origin_grade": (capability.partition(".")[0]
                         if origin_grade is None else origin_grade),
        "checkpoint_origin_grade": (
            challenger_exam.get("checkpoint_origin_grade")
            if checkpoint_origin_grade is None else checkpoint_origin_grade),
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
        origin_grade=prior["origin_grade"],
        checkpoint_origin_grade=(
            challenger_exam.get("checkpoint_origin_grade")
            if challenger_wins else
            prior.get("checkpoint_origin_grade", prior.get("origin_grade"))))
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


def advance_epoch(epoch: dict, *, grades: dict, challenger_exam: dict,
                  incumbent_exams: dict, title_matches=None,
                  fanout_screen=None) -> tuple[dict, tuple[str, ...], tuple[dict, ...]]:
    """Capability-local title fights with one non-recursive same-grade fan-out."""
    census = tuple(capability for capabilities in grades.values() for capability in capabilities)
    if len(census) != len(set(census)):
        raise ValueError("CHAMPIONSHIP_CAPABILITY_GROUP_AMBIGUOUS_OR_ABSENT")
    scores = challenger_exam["scores"]
    pointer = _pointer(challenger_exam["checkpoint"])
    updated = deepcopy(epoch)
    updated.setdefault("settled_matchups", {})
    _sanitize_role_origins(updated, grades)
    roles = updated.setdefault("active_roles", {})
    original_roles = deepcopy(roles)
    updated.setdefault("active_grade_soups", {})
    changes, decisions = [], []
    title_matches = title_matches or {}
    if pointer["optimizer_step"] <= epoch.get("championship_eligibility_after_step", -1):
        return updated, (), ()

    grade = _challenge_grade(epoch, grades, challenger_exam)
    checkpoint_origin_grade = challenger_exam.get("checkpoint_origin_grade")
    if checkpoint_origin_grade not in grades:
        raise ValueError("CHAMPIONSHIP_CHECKPOINT_ORIGIN_PROVENANCE_INVALID")
    caps = _grade_caps(grades, grade)
    mastered = tuple(sorted(
        cap for cap in caps if cap in scores and
        scores[cap]["correct"] == scores[cap]["total"]))

    primary = {}
    for cap in caps:
        if cap not in scores:
            continue
        prior = original_roles.get(cap)
        if prior is None:
            if not _initial_title_threshold_met(scores[cap]):
                decisions.append({
                    "grade": grade, "capability": cap,
                    "decision": "INITIAL_TITLE_THRESHOLD_NOT_MET",
                    "correct": scores[cap]["correct"],
                    "total": scores[cap]["total"],
                    "minimum_percent": 66,
                    "challenger_sha256": pointer["sha256"],
                })
                continue
            roles[cap] = _role_receipt(
                challenger_exam, cap, mastered, scope=(cap,),
                owner_maxed=(scores[cap]["correct"] == scores[cap]["total"]),
                origin_grade=grade)
            changes.append(cap)
            continue
        prior_pointer = _pointer(prior["checkpoint"])
        if prior_pointer["sha256"] == pointer["sha256"]:
            if scores[cap]["correct"] > prior.get("correct", -1):
                roles[cap] = _role_receipt(
                    challenger_exam, cap, mastered, prior=prior, scope=(cap,),
                    surviving_battery=verified_battery(prior),
                    owner_maxed=bool(prior.get("maxed", maxed_role(prior))) or
                    scores[cap]["correct"] == scores[cap]["total"],
                    origin_grade=grade)
            continue
        settled = _settled_match(
            updated, cap, prior_pointer["sha256"], pointer["sha256"])
        if settled is not None:
            decisions.append({
                "grade": grade, "capability": cap,
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

    primary_won = False
    for cap, (prior, qualification) in primary.items():
        match = title_matches.get(cap)
        if match is None:
            decisions.append({
                "grade": grade, "capability": cap,
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
                "grade": grade,
                "qualification": qualification,
            }
        decisions.append({"grade": grade, **verdict, "qualification": qualification})
        if won:
            primary_won = True
            if cap not in changes:
                changes.append(cap)

    # A real primary takeover opens one and only one same-grade sibling scan.
    # Secondary wins never participate in deciding whether another scan occurs.
    if primary_won:
        eligible_siblings = [
            cap for cap in caps if cap not in primary and
            (prior := original_roles.get(cap)) is not None and
            _pointer(prior["checkpoint"])["sha256"] != pointer["sha256"] and
            _settled_match(updated, cap, _pointer(prior["checkpoint"])["sha256"],
                           pointer["sha256"]) is None]
        unmeasured = [cap for cap in eligible_siblings if cap not in scores]
        for cap in unmeasured:
            decisions.append({
                "grade": grade,
                "capability": cap,
                "decision": "FANOUT_DEFERRED_UNMEASURED",
                "challenger_sha256": pointer["sha256"],
                "reason": "CAPABILITY_ABSENT_FROM_CURRENT_COHORT",
            })
        siblings = [cap for cap in eligible_siblings if cap in scores]
        if siblings and fanout_screen is None:
            decisions.append({
                "grade": grade,
                "decision": "FANOUT_SCREEN_REQUIRED",
                "capabilities": siblings,
                "challenger_sha256": pointer["sha256"],
            })
            return updated, tuple(changes), tuple(decisions)
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
            decisions.append({"grade": grade, **verdict,
                              "qualification": "FANOUT_MATCH_OR_BEAT"})
            if won and cap not in changes:
                changes.append(cap)

    return updated, tuple(changes), tuple(decisions)
