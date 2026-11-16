"""Neural-inert trial of active-mentor reset at a new curriculum grade.

Historical champions and soups remain archived elsewhere unchanged. These
functions only *plan* an active adviser roster; they never clone weights,
update AdamW, declare graduation or install a new human training policy.
The caller must independently verify checkpoint bundles and graph binding.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json


SCHEMA = "bilqis.mlx.mentor-epoch-trial/v1"
EARNED_ONLY_POLICY = "bilqis.mlx.earned-champions-only/v1"


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                             separators=(",", ":")).encode()).hexdigest()


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and all(
        symbol in "0123456789abcdef" for symbol in value)


def _pointer(pointer):
    if (not isinstance(pointer, dict) or not _sha(pointer.get("sha256")) or
            not isinstance(pointer.get("filename"), str) or
            len(pointer["filename"].split("/")) != 2 or
            pointer["filename"].split("/")[0] != "bundles" or
            pointer["filename"].split("/")[1] in (".", "..", "") or
            type(pointer.get("optimizer_step")) is not int or
            pointer["optimizer_step"] < 0 or
            pointer.get("model_and_native_adamw") is not True):
        raise ValueError("MENTOR_EPOCH_WHOLE_STUDENT_OWN_ADAMW_REQUIRED")
    return dict(pointer)


def _scores(scores):
    if not isinstance(scores, dict) or not scores:
        raise ValueError("MENTOR_EPOCH_INCOMPLETE_SCORES")
    for cap, value in scores.items():
        if (not isinstance(cap, str) or not cap or
                not isinstance(value, dict) or
                type(value.get("correct")) is not int or
                type(value.get("total")) is not int or
                not 0 <= value["correct"] <= value["total"] or
                value["total"] < 1):
            raise ValueError("MENTOR_EPOCH_INVALID_SOURCE_SCORE")
    return scores


def begin_epoch(*, previous_graduate: dict, admitted_baseline: dict,
                introduced_grade: str, source_graph_sha256: str,
                previous_capabilities: tuple[str, ...],
                previous_graduation_exam: dict) -> dict:
    """Describe a frozen post-admission baseline, not fabricate a new soup.

    The previous graduation exam must belong to one complete source-scored
    student; the post-admission reference may differ after append-only
    vocabulary extension, but remains an intact, separately bound checkpoint.
    """
    graduate = _pointer(previous_graduate)
    baseline = _pointer(admitted_baseline)
    caps = tuple(previous_capabilities)
    if (not introduced_grade or not _sha(source_graph_sha256) or
            not caps or len(set(caps)) != len(caps) or
            any(not isinstance(cap, str) or
                cap.partition(".")[0] == introduced_grade for cap in caps) or
            baseline["optimizer_step"] < graduate["optimizer_step"]):
        raise ValueError("MENTOR_EPOCH_INVALID_GRADE_BOUNDARY")
    exam = previous_graduation_exam
    if (not isinstance(exam, dict) or
            exam.get("checkpoint_sha256") != graduate["sha256"] or
            not _sha(exam.get("cohort_sha256")) or
            not _sha(exam.get("rubric_sha256")) or
            set(_scores(exam.get("scores"))) != set(caps) or
            any(exam["scores"][cap]["correct"] != exam["scores"][cap]["total"]
                for cap in caps)):
        raise ValueError("MENTOR_EPOCH_COMPLETE_PREVIOUS_GRADUATION_REQUIRED")
    return {"schema": SCHEMA, "introduced_grade": introduced_grade,
            "source_graph_sha256": source_graph_sha256,
            "previous_capabilities": list(caps),
            "previous_graduate": graduate, "baseline": baseline,
            "baseline_roles": {},
            "active_roles": {}, "active_grade_soups": {},
            "guidance_policy": EARNED_ONLY_POLICY,
            "championship_eligibility_after_step": baseline["optimizer_step"],
            "earned_role_votes_at_reset": 0,
            "previous_graduation_exam_sha256": _digest(exam),
            "qualified": [], "historical_advisers_remain_archived": True}


def begin_debt_epoch(*, previous_checkpoint: dict, admitted_baseline: dict,
                     introduced_grade: str, source_graph_sha256: str,
                     previous_capabilities: tuple[str, ...],
                     previous_boundary_exam: dict,
                     previous_mastery_debt: tuple[str, ...]) -> dict:
    """Start a new-grade epoch without mislabeling unresolved prior work mastered.

    The previous checkpoint is preserved for custody, but is explicitly not a
    graduate.  The complete prior-course exam must name exactly the carried
    non-perfect capabilities; no missing or synthetic score may become debt.
    """
    checkpoint = _pointer(previous_checkpoint)
    baseline = _pointer(admitted_baseline)
    caps = tuple(previous_capabilities)
    debt = tuple(previous_mastery_debt)
    if (not introduced_grade or not _sha(source_graph_sha256) or
            not caps or len(set(caps)) != len(caps) or
            any(not isinstance(cap, str) or
                cap.partition(".")[0] == introduced_grade for cap in caps) or
            baseline["optimizer_step"] < checkpoint["optimizer_step"] or
            not debt or len(set(debt)) != len(debt) or
            not set(debt) <= set(caps)):
        raise ValueError("MENTOR_EPOCH_INVALID_DEBT_BOUNDARY")
    exam = previous_boundary_exam
    if (not isinstance(exam, dict) or
            exam.get("checkpoint_sha256") != checkpoint["sha256"] or
            not _sha(exam.get("cohort_sha256")) or
            not _sha(exam.get("rubric_sha256")) or
            set(_scores(exam.get("scores"))) != set(caps)):
        raise ValueError("MENTOR_EPOCH_COMPLETE_PREVIOUS_BOUNDARY_REQUIRED")
    observed_debt = tuple(cap for cap in caps
                          if exam["scores"][cap]["correct"] !=
                          exam["scores"][cap]["total"])
    if set(observed_debt) != set(debt):
        raise ValueError("MENTOR_EPOCH_MASTERY_DEBT_MISMATCH")
    return {
        "schema": SCHEMA,
        "introduced_grade": introduced_grade,
        "source_graph_sha256": source_graph_sha256,
        "previous_capabilities": list(caps),
        "previous_graduate": None,
        "previous_boundary_checkpoint": checkpoint,
        "previous_mastery_debt": list(debt),
        "baseline": baseline,
        "baseline_roles": {},
        "active_roles": {},
        "active_grade_soups": {},
        "guidance_policy": EARNED_ONLY_POLICY,
        "championship_eligibility_after_step": baseline["optimizer_step"],
        "earned_role_votes_at_reset": 0,
        "previous_boundary_exam_sha256": _digest(exam),
        "qualified": [],
        "historical_advisers_remain_archived": True,
        "admission_mode": "CARRIED_MASTERY_DEBT",
    }


def begin_initial_epoch(*, student: dict, introduced_grade: str,
                        source_graph_sha256: str, frontier: dict, soups: dict) -> dict:
    """Start earned roles before graduation; preserve existing active titles."""
    baseline = _pointer(student)
    if not introduced_grade or not _sha(source_graph_sha256):
        raise ValueError("CHAMPIONSHIP_INITIAL_EPOCH_IDENTITY_REQUIRED")
    roles = {}
    if frontier and not soups:
        raise ValueError("CHAMPIONSHIP_INITIAL_EPOCH_SOUPS_REQUIRED")
    for soup in soups.values():
        for role in soup["roles"]:
            item = frontier[role["rubric"] + ":" + role["capability"]]
            if item["checkpoint"]["sha256"] != role["checkpoint_sha256"]:
                raise ValueError("CHAMPIONSHIP_INITIAL_EPOCH_ROLE_DRIFT")
            roles[role["capability"]] = deepcopy(item)
    return {"schema": SCHEMA, "introduced_grade": introduced_grade,
            "source_graph_sha256": source_graph_sha256,
            "previous_capabilities": [], "previous_graduate": None,
            "baseline": baseline, "baseline_roles": {},
            "active_roles": roles, "active_grade_soups": deepcopy(soups),
            "guidance_policy": EARNED_ONLY_POLICY,
            "championship_eligibility_after_step": -1,
            "qualified": [], "historical_advisers_remain_archived": True}


def active_adviser_checkpoints(epoch: dict, *, cohort_sha256: str | None = None,
                               scope_sha256: str | None = None,
                               rubric_sha256: str | None = None) -> tuple[dict, ...]:
    """Only newly earned best-score role owners may advise, never the baseline.

    Qualified candidates from the early experiment are historical receipts,
    not championship title holders or sources of teacher gradients.
    """
    if epoch.get("schema") != SCHEMA:
        raise ValueError("MENTOR_EPOCH_UNKNOWN_SCHEMA")
    _pointer(epoch["baseline"])
    if any(value is not None and not _sha(value)
           for value in (cohort_sha256, scope_sha256, rubric_sha256)):
        raise ValueError("MENTOR_EPOCH_INVALID_ADVISER_SCOPE")
    if epoch.get("guidance_policy") != EARNED_ONLY_POLICY:
        raise ValueError("MENTOR_EPOCH_FRESH_CHAMPIONS_RESET_REQUIRED")
    unique = {}
    for entry in epoch.get("active_roles", {}).values():
        if (cohort_sha256 is not None and entry.get("cohort_sha256") != cohort_sha256
                or rubric_sha256 is not None and entry.get("rubric") != rubric_sha256
                or scope_sha256 is not None and
                epoch.get("active_role_scope_sha256") != scope_sha256):
            continue
        pointer = _pointer(entry["checkpoint"])
        unique[pointer["sha256"]] = pointer
    return tuple(unique[sha] for sha in sorted(unique))


def reference_checkpoints(epoch: dict) -> tuple[dict, ...]:
    """Preserve *all* referenced whole models, not only the latest adviser.

    A mentor can cease to qualify on a new cohort without becoming unowned
    checkpoint data. Archive custody and active teaching eligibility differ.
    """
    active_adviser_checkpoints(epoch)
    pointers = [_pointer(epoch["baseline"])]
    if epoch.get("previous_graduate") is not None:
        pointers.append(_pointer(epoch["previous_graduate"]))
    if epoch.get("previous_boundary_checkpoint") is not None:
        pointers.append(_pointer(epoch["previous_boundary_checkpoint"]))
    pointers.extend(_pointer(item["checkpoint"]) for item in epoch["qualified"])
    for historic in epoch.get("superseded_active_championships", ()):
        pointers.extend(_pointer(item["checkpoint"])
                        for item in historic["active_roles"].values())
        pointers.append(_pointer(historic["starting_student"]))
        if historic.get("prior_baseline") is not None:
            pointers.append(_pointer(historic["prior_baseline"]))
    unique = {}
    identity_by_sha = {}
    for pointer in pointers:
        # Distinct bundle paths can legitimately custody the same model SHA at
        # the same optimizer step. Preserve every referenced full-bundle alias,
        # but still fail closed if one model SHA is attributed to contradictory
        # optimizer/native-AdamW identity.
        identity = (pointer["optimizer_step"], pointer["model_and_native_adamw"])
        prior_identity = identity_by_sha.setdefault(pointer["sha256"], identity)
        if prior_identity != identity:
            raise ValueError("MENTOR_EPOCH_CHECKPOINT_POINTER_CONFLICT")
        key = (pointer["sha256"], pointer["filename"])
        unique.setdefault(key, pointer)
    return tuple(unique.values())


def qualify_candidate(epoch: dict, candidate: dict, baseline_exam: dict,
                      candidate_exam: dict, *, mature_loss_budget: int) -> dict:
    """Trial-only mentor eligibility, not student admission or graduation.

    Both complete examinations must use *identical* source questions, graph,
    rubric and assessment scope. The explicit tolerance is a policy input,
    not a hidden zero-forgetting mandate or an optimizer-level candidate gate.
    """
    active_adviser_checkpoints(epoch)
    pointer = _pointer(candidate)
    if type(mature_loss_budget) is not int or mature_loss_budget < 0:
        raise ValueError("MENTOR_EPOCH_INVALID_MATURE_LOSS_POLICY")
    common = ("cohort_sha256", "rubric_sha256", "assessment_scope_sha256",
              "source_graph_sha256")
    if (not isinstance(baseline_exam, dict) or
            not isinstance(candidate_exam, dict) or
            any(not _sha(baseline_exam.get(k)) or
                baseline_exam[k] != candidate_exam.get(k) for k in common) or
            baseline_exam["source_graph_sha256"] != epoch["source_graph_sha256"] or
            baseline_exam.get("checkpoint_sha256") != epoch["baseline"]["sha256"] or
            candidate_exam.get("checkpoint_sha256") != pointer["sha256"] or
            pointer["sha256"] == epoch["baseline"]["sha256"]):
        raise ValueError("MENTOR_EPOCH_MISMATCHED_EXAMINATION")
    before, after = _scores(baseline_exam.get("scores")), _scores(candidate_exam.get("scores"))
    prior = set(epoch["previous_capabilities"])
    current = {name for name in before if name.partition(".")[0] ==
               epoch["introduced_grade"]}
    if (not current or set(before) != set(after) or
            not prior <= set(before) or
            any(before[name]["total"] != after[name]["total"] for name in before) or
            any(name not in prior | current for name in before)):
        raise ValueError("MENTOR_EPOCH_INCOMPLETE_PAIRED_SCOPE")
    old_losses = {name: before[name]["correct"] - after[name]["correct"]
                  for name in prior if before[name]["correct"] > after[name]["correct"]}
    new_gain = sum(after[name]["correct"] - before[name]["correct"] for name in current)
    total_gain = sum(after[name]["correct"] - before[name]["correct"] for name in before)
    if new_gain <= 0:
        decision = "HOLD_NO_NEW_GRADE_GAIN"
    elif max(old_losses.values(), default=0) > mature_loss_budget:
        decision = "HOLD_MATURE_LOSS"
    elif total_gain <= 0:
        decision = "HOLD_NO_CUMULATIVE_GAIN"
    elif any(item["cohort_sha256"] == baseline_exam["cohort_sha256"] and
             item["scope_sha256"] == baseline_exam["assessment_scope_sha256"] and
             item["rubric_sha256"] == baseline_exam["rubric_sha256"] and
             item["cumulative_correct_gain"] >= total_gain
             for item in epoch["qualified"]):
        decision = "HOLD_NO_BETTER_SAME_SCOPE_REFERENCE"
    else:
        decision = "QUALIFIED"
    updated = deepcopy(epoch)
    if decision == "QUALIFIED" and not any(
            item["checkpoint"]["sha256"] == pointer["sha256"]
            for item in updated["qualified"]):
        updated["qualified"].append({
            "checkpoint": pointer, "scope_sha256": baseline_exam["assessment_scope_sha256"],
            "cohort_sha256": baseline_exam["cohort_sha256"],
            "rubric_sha256": baseline_exam["rubric_sha256"],
            "cumulative_correct_gain": total_gain,
            "new_grade_correct_gain": new_gain,
            "paired_evidence_sha256": _digest([baseline_exam, candidate_exam])})
    return {"decision": decision, "new_grade_correct_gain": new_gain,
            "cumulative_correct_gain": total_gain, "mature_losses": old_losses,
            "epoch": updated, "student_or_optimizer_mutated": False}
