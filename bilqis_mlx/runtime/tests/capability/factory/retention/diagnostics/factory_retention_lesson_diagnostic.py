"""Non-authorizing same-grade diagnostic for the second Factory C05 gate."""
from __future__ import annotations

from pathlib import Path
from time import perf_counter

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.retention_policy import retention_reason, scaled_loss_allowance
from bilqis_mlx.runtime.capability_evaluation import _answer_identity
from bilqis_mlx.runtime.factory_complete_solver import factory_complete_solver
from bilqis_mlx.runtime.factory_retention_owner import (
    C05_FRESH_LESSON_SEED_OFFSET,
    C05_FRESH_TARGET_SEED_OFFSET,
    C05_PROBE_EACH,
    C05_PROTECTED_REFERENCE_LOSS,
    _candidate_from_live_parent,
    _fresh_rows,
    _instruments,
    _owner_seed,
    _training_exclusions,
)
from bilqis_mlx.runtime.tests.capability.factory.retention.diagnostics.factory_retention_target_diagnostic import (
    _value_receipt,
)


def _lesson_setup(source_context, candidate, target_capability):
    source_context.__post_init__()
    release = source_context.release
    capability_map = release.execution_plan.capability_map
    if target_capability not in capability_map:
        raise AssertionError("C05 lesson diagnostic capability is not admitted")
    target_group = capability_map[target_capability].grade_id
    lesson_capabilities = tuple(
        item.capability_id for item in release.execution_plan.capabilities
        if item.grade_id == target_group)
    training = _training_exclusions(candidate)
    if any(
        authority.delivery_capability != target_capability
        or authority.release_sha256 != release.release_sha256
        for authority in candidate.training_authorities
    ):
        raise AssertionError("C05 lesson diagnostic training authority drift")
    return release, target_group, lesson_capabilities, training


def _lesson_scores(
    lesson_capabilities, target_capability, instruments,
    parent_solver, parent_generation, candidate_solver, candidate_generation,
):
    scores = {
        capability: {"parent_correct": 0, "candidate_correct": 0, "total": 0}
        for capability in lesson_capabilities
    }
    changed_cases = []
    for instrument in instruments:
        case = instrument.case
        capability = case.capability_id
        parent_result, parent_contract = parent_solver.evaluate(
            case.goal, parent_generation)
        candidate_result, candidate_contract = candidate_solver.evaluate(
            case.goal, candidate_generation)
        parent_answer = _answer_identity(parent_result.answer)
        candidate_answer = _answer_identity(candidate_result.answer)
        gold = _answer_identity(case.gold)
        parent_match = parent_answer == gold
        candidate_match = candidate_answer == gold
        score = scores[capability]
        score["parent_correct"] += int(parent_match)
        score["candidate_correct"] += int(candidate_match)
        score["total"] += 1
        if parent_match != candidate_match or parent_answer != candidate_answer:
            changed_cases.append({
                "case_id": case.case_id,
                "capability": capability,
                "gold": _value_receipt(case.gold),
                "parent": {
                    "correct": parent_match,
                    "answer": _value_receipt(parent_result.answer),
                    "route": parent_result.route.value,
                },
                "candidate": {
                    "correct": candidate_match,
                    "answer": _value_receipt(candidate_result.answer),
                    "route": candidate_result.route.value,
                },
                "solver_contract_match": parent_contract == candidate_contract,
            })
    capability_scores = []
    protected_exceeded = []
    same_grade_net_gain = 0
    for capability in lesson_capabilities:
        score = scores[capability]
        delta = score["candidate_correct"] - score["parent_correct"]
        same_grade_net_gain += delta
        allowance = None
        if capability != target_capability:
            allowance = scaled_loss_allowance(
                score["total"], C05_PROTECTED_REFERENCE_LOSS, C05_PROBE_EACH)
            if -delta > allowance:
                protected_exceeded.append(capability)
        capability_scores.append({
            "capability": capability,
            **score,
            "delta": delta,
            "protected_loss_allowance": allowance,
        })
    return capability_scores, protected_exceeded, same_grade_net_gain, changed_cases


def diagnose_factory_retention_lesson(
    source_context,
    candidate,
    artifact_path: str,
    target_capability: str,
    *,
    run_dir: Path,
):
    """Measure C05's same-grade gate without issuing acceptance authority."""
    started = perf_counter()
    release, target_group, lesson_capabilities, training = _lesson_setup(
        source_context, candidate, target_capability)

    bound_at = perf_counter()
    parent, candidate_bundle, candidate_state, cache = _candidate_from_live_parent(
        run_dir, candidate)
    candidate_sha256 = candidate_identity_digest(candidate_state)
    fresh_seed = _owner_seed(
        release.release_sha256, cache, target_capability, candidate_sha256)
    initial_seed = fresh_seed + C05_FRESH_LESSON_SEED_OFFSET
    lesson_draw = _fresh_rows(
        source_context, lesson_capabilities, seed=initial_seed, training=training)
    bound_done = perf_counter()

    instruments = _instruments(
        source_context, candidate_bundle, artifact_path, lesson_draw.rows,
        seed=lesson_draw.seed, each=C05_PROBE_EACH)
    instruments_done = perf_counter()
    parent_solver, parent_generation = factory_complete_solver(
        source_context, parent, artifact_path, instruments)
    parent_solver_done = perf_counter()
    candidate_solver, candidate_generation = factory_complete_solver(
        source_context, candidate_bundle, artifact_path, instruments)
    candidate_solver_done = perf_counter()

    capability_scores, protected_exceeded, same_grade_net_gain, changed_cases = (
        _lesson_scores(
            lesson_capabilities, target_capability, instruments,
            parent_solver, parent_generation, candidate_solver, candidate_generation)
    )

    reason = retention_reason(
        no_target_gain=False,
        same_grade_net_gain=same_grade_net_gain,
        fixed_grade_regression=False,
        active_grade_regression=False,
        whole_school_regression=False,
        frontier_measured=True,
        fragile_losses=False,
        exceeded=bool(protected_exceeded),
    )
    decisive = None if reason == "PAIRED_SCREEN_WITHIN_BUDGET" else reason

    finished = perf_counter()
    return {
        "schema": "bilqis.mlx.c05-lesson-diagnostic/v1",
        "authorizing": False,
        "target_capability": target_capability,
        "target_group": target_group,
        "lesson_capabilities": list(lesson_capabilities),
        "target_initial_seed": fresh_seed + C05_FRESH_TARGET_SEED_OFFSET,
        "lesson_seed": lesson_draw.seed,
        "initial_seed": initial_seed,
        "source_draw_attempts": lesson_draw.seed - initial_seed + 1,
        "training_family_ids": training[0],
        "training_episode_ids": training[1],
        "parent_generation": parent_generation,
        "candidate_generation": candidate_generation,
        "capability_scores": capability_scores,
        "same_grade_net_gain": same_grade_net_gain,
        "protected_exceeded": protected_exceeded,
        "decisive_rejection_reason": decisive,
        "changed_cases": changed_cases,
        "total": len(instruments),
        "timing_seconds": {
            "bind_and_draw": bound_done - bound_at,
            "instrument_compile": instruments_done - bound_done,
            "parent_solver_build": parent_solver_done - instruments_done,
            "candidate_solver_build": candidate_solver_done - parent_solver_done,
            "solve": finished - candidate_solver_done,
            "total": finished - started,
        },
    }


__all__ = ("diagnose_factory_retention_lesson",)
