from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from bilqis_mlx.curriculum.promotion import (
    PROMOTION_SWEEP_ENTRY_FLOOR,
    PROMOTION_SWEEP_FAILURE_FLOOR,
)

from .common import digest, invalid, is_digest

SCORE_RECORD_FIELDS = 3
SCORE_CORRECT_INDEX = 1
SCORE_TOTAL_INDEX = 2


def _mean_score(records) -> Fraction:
    if not records:
        invalid()
    values = []
    for item in records:
        if (not isinstance(item, (tuple, list)) or len(item) != SCORE_RECORD_FIELDS
                or not isinstance(item[0], str) or not item[0]
                or type(item[SCORE_CORRECT_INDEX]) is not int
                or type(item[SCORE_TOTAL_INDEX]) is not int
                or item[SCORE_TOTAL_INDEX] <= 0
                or not 0 <= item[SCORE_CORRECT_INDEX] <= item[SCORE_TOTAL_INDEX]):
            invalid()
        values.append(Fraction(item[SCORE_CORRECT_INDEX], item[SCORE_TOTAL_INDEX]))
    return sum(values, Fraction()) / len(values)


def _score_record(value, capability: str):
    if not isinstance(value, dict):
        invalid()
    score = value.get(capability)
    if (not isinstance(score, dict)
            or type(score.get("correct")) is not int
            or type(score.get("total")) is not int
            or score["total"] <= 0
            or not 0 <= score["correct"] <= score["total"]):
        invalid()
    return capability, score["correct"], score["total"]


def _release_for_sha(run_dir: Path, release_sha256: str):
    from bilqis_mlx.runtime.admission import _read_executable_factory_release_artifact
    return _read_executable_factory_release_artifact(run_dir, {
        "factory_release_sha256": release_sha256,
        "factory_release_file": f"factory-releases/{release_sha256}.json",
    })


def _school_for_receipt(run_dir: Path, receipt: dict):
    from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
    from bilqis_mlx.runtime.state import _state_from_json

    release_sha256 = receipt.get("factory_release_sha256")
    if not is_digest(release_sha256) or not isinstance(receipt.get("school"), dict):
        invalid()
    release = _release_for_sha(run_dir, release_sha256)
    program = schedule_program_from_executable_release(release)
    try:
        return _state_from_json(receipt["school"], program)
    except (TypeError, ValueError, KeyError):
        invalid()


def _foundation_capabilities(run_dir: Path, release_sha256: str) -> tuple[str, ...]:
    release = _release_for_sha(run_dir, release_sha256)
    try:
        return release.require_foundation_capability_ids()
    except (AttributeError, TypeError, ValueError):
        invalid()


def _promotion_projection(school) -> tuple:
    return (
        school.stage,
        tuple(school.queue),
        tuple(school.promotion_sweep_scope),
        tuple(school.promotion_sweep_scores),
        school.grade_index,
        school.grade_exam_epoch,
        tuple(school.carried_mastery_debt),
    )


def evidence_interval(
        run_dir: Path, *, current_generation: int, candidate_sha256: str,
        optimizer_step: int, foundation: tuple[str, ...]):
    from bilqis_mlx.state_dag import read_generation

    matched_reverse = []
    release_sha256 = None
    for generation in range(current_generation, -1, -1):
        receipt = read_generation(run_dir, generation)
        school = _school_for_receipt(run_dir, receipt)
        same_attempt = (
            school.promotion_sweep_attempt_student_sha256 == candidate_sha256
            and tuple(school.promotion_sweep_attempt_scope) == foundation)
        if not same_attempt:
            invalid()
        if release_sha256 is None:
            release_sha256 = receipt.get("factory_release_sha256")
        if (school.current_student.sha256 != candidate_sha256
                or school.current_student.optimizer_step != optimizer_step
                or receipt.get("factory_release_sha256") != release_sha256):
            invalid()
        matched_reverse.append((generation, receipt, school))
        if (school.stage == "PROMOTION_SWEEP"
                and tuple(school.promotion_sweep_scope) == foundation
                and tuple(school.queue) == foundation):
            return list(reversed(matched_reverse))
    invalid()


def validate_sweep_evidence(
        evidence, foundation: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
    entry_school = evidence[0][2]
    final_receipt = evidence[-1][1]
    final_school = evidence[-1][2]
    if _mean_score(entry_school.promotion_sweep_scores) < PROMOTION_SWEEP_ENTRY_FLOOR:
        invalid()

    compressed = []
    last_projection = None
    for _generation, _receipt, school in evidence[:-1]:
        projection = _promotion_projection(school)
        if projection == last_projection:
            continue
        last_projection = projection
        compressed.append((school.stage, tuple(school.queue)))
        if school.promotion_sweep_scores and (
                _mean_score(school.promotion_sweep_scores)
                < PROMOTION_SWEEP_FAILURE_FLOOR):
            invalid()
    expected = [("PROMOTION_SWEEP", foundation)]
    for index in range(len(foundation)):
        remaining = foundation[index + 1:]
        expected.append(("ASSESS_PROMOTION_SWEEP", remaining))
        if remaining:
            expected.append(("PROMOTION_SWEEP", remaining))
    if compressed != expected:
        invalid()

    sweep_cleared = (
        not final_school.promotion_sweep_scope
        and final_school.stage not in {"PROMOTION_SWEEP", "ASSESS_PROMOTION_SWEEP"})
    ordinary = final_school.grade_exam_epoch == entry_school.grade_exam_epoch + 1
    debt_boundary = (
        final_school.grade_exam_epoch == entry_school.grade_exam_epoch
        and bool(final_school.carried_mastery_debt)
        and ((final_school.grade_index == entry_school.grade_index + 1
              and final_school.stage == "MAIN")
             or (final_school.grade_index == entry_school.grade_index
                 and final_school.stage == "AWAITING_NEXT_GRADE_WITH_DEBT")))
    if not sweep_cleared or not (ordinary or debt_boundary):
        invalid()

    prior = {capability: (correct, total)
             for capability, correct, total
             in evidence[-2][2].promotion_sweep_scores}
    last_exam = final_receipt.get("last_exam")
    if not isinstance(last_exam, dict):
        invalid()
    from bilqis_mlx.generated_assessment import PROMOTION_ATTEMPT_LIFECYCLE
    from bilqis_mlx.runtime.state import _fingerprint
    if (last_exam.get("student_sha256") != final_school.current_student.sha256
            or last_exam.get("optimizer_step") != final_school.current_student.optimizer_step):
        invalid()
    if (last_exam.get("grade_test_lifecycle") != PROMOTION_ATTEMPT_LIFECYCLE
            or last_exam.get("assessment_scope_sha256") != _fingerprint(foundation)):
        invalid()
    prior[foundation[-1]] = _score_record(last_exam.get("scores"), foundation[-1])[1:]
    final_scores = tuple((capability, *prior[capability]) for capability in foundation
                         if capability in prior)
    if (len(final_scores) != len(foundation)
            or _mean_score(final_scores) < PROMOTION_SWEEP_FAILURE_FLOOR):
        invalid()

    outcome = "PROMOTED_WITH_DEBT" if final_school.carried_mastery_debt else "PROMOTED"
    if not ordinary:
        outcome = "PROMOTED_WITH_DEBT"
    return outcome, tuple(final_school.carried_mastery_debt)


def evidence_digest(evidence) -> str:
    """Digest only promotion-authoritative state from verified State-DAG nodes.

    The State DAG already authenticates each raw receipt.  Re-hashing the full
    serialized SchoolState here would incorrectly make grade labels, grade index,
    course digest, and other scheduler-local metadata part of B09 transition
    authority.  The receipt instead commits to the exact fields that C05 validates
    for this promotion attempt.  Runtime release identity is still checked for
    immutability across the interval by ``evidence_interval``; the immutable birth
    release and foundation capability scope are bound separately in the issued
    promotion receipt.
    """
    records = []
    for generation, receipt, school in evidence:
        last_exam = receipt.get("last_exam")
        exam_projection = None
        if isinstance(last_exam, dict):
            exam_projection = {
                "student_sha256": last_exam.get("student_sha256"),
                "optimizer_step": last_exam.get("optimizer_step"),
                "grade_test_lifecycle": last_exam.get("grade_test_lifecycle"),
                "assessment_scope_sha256": last_exam.get("assessment_scope_sha256"),
                "scores": last_exam.get("scores"),
            }
        records.append({
            "generation": generation,
            "factory_release_sha256": receipt.get("factory_release_sha256"),
            "school": {
                "stage": school.stage,
                "queue": tuple(school.queue),
                "promotion_sweep_scope": tuple(school.promotion_sweep_scope),
                "promotion_sweep_scores": tuple(school.promotion_sweep_scores),
                "promotion_sweep_attempt_student_sha256":
                    school.promotion_sweep_attempt_student_sha256,
                "promotion_sweep_attempt_scope":
                    tuple(school.promotion_sweep_attempt_scope),
                "promotion_sweep_return_stage":
                    getattr(school, "promotion_sweep_return_stage", None),
                "grade_exam_epoch": school.grade_exam_epoch,
                "carried_mastery_debt": tuple(school.carried_mastery_debt),
                "current_student_sha256": school.current_student.sha256,
                "current_student_optimizer_step":
                    school.current_student.optimizer_step,
            },
            "last_exam": exam_projection,
        })
    return digest(records)
