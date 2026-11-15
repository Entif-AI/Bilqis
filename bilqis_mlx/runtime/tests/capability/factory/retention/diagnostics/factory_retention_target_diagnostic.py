"""Non-authorizing target-first diagnostic for expensive Factory C05 screens."""
from __future__ import annotations

from pathlib import Path
from time import perf_counter

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.runtime.factory_complete_solver import factory_complete_solver
from bilqis_mlx.runtime.capability_evaluation import _answer_identity
from bilqis_mlx.runtime.factory_retention_owner import (
    C05_FRESH_TARGET_SEED_OFFSET,
    C05_PROBE_EACH,
    _candidate_from_live_parent,
    _fresh_rows,
    _instruments,
    _owner_seed,
    _training_exclusions,
)


def _value_receipt(value):
    raw = value.value
    if type(raw) not in (str, int, bool, float, type(None)):
        raw = repr(raw)
    return {
        "type": value.type_name,
        "state": value.state.value,
        "semantic_release": value.semantic_release,
        "value": raw,
    }


def _evaluate_solver_cases(
    parent_solver, parent_generation, candidate_solver, candidate_generation,
    instruments,
):
    parent_correct = candidate_correct = 0
    cases = []
    for instrument in instruments:
        case = instrument.case
        parent_at = perf_counter()
        parent_result, parent_contract = parent_solver.evaluate(
            case.goal, parent_generation)
        parent_done = perf_counter()
        candidate_result, candidate_contract = candidate_solver.evaluate(
            case.goal, candidate_generation)
        candidate_done = perf_counter()
        parent_match = _answer_identity(parent_result.answer) == _answer_identity(case.gold)
        candidate_match = (
            _answer_identity(candidate_result.answer) == _answer_identity(case.gold))
        parent_correct += int(parent_match)
        candidate_correct += int(candidate_match)
        cases.append({
            "case_id": case.case_id,
            "gold": _value_receipt(case.gold),
            "parent": {
                "correct": parent_match,
                "answer": _value_receipt(parent_result.answer),
                "route": parent_result.route.value,
                "neural_calls": parent_result.neural_calls,
                "fallback_reason": parent_result.fallback_reason,
                "solve_seconds": parent_done - parent_at,
            },
            "candidate": {
                "correct": candidate_match,
                "answer": _value_receipt(candidate_result.answer),
                "route": candidate_result.route.value,
                "neural_calls": candidate_result.neural_calls,
                "fallback_reason": candidate_result.fallback_reason,
                "solve_seconds": candidate_done - parent_done,
            },
            "solver_contract_match": parent_contract == candidate_contract,
        })
    return parent_correct, candidate_correct, cases


def diagnose_factory_retention_target(
    source_context,
    candidate,
    artifact_path: str,
    target_capability: str,
    *,
    run_dir: Path,
):
    """Measure only C05's first decisive gate without issuing acceptance authority."""
    started = perf_counter()
    source_context.__post_init__()
    release = source_context.release
    if target_capability not in release.execution_plan.capability_map:
        raise AssertionError("C05 target diagnostic capability is not admitted")
    training = _training_exclusions(candidate)
    if any(
        authority.delivery_capability != target_capability
        or authority.release_sha256 != release.release_sha256
        for authority in candidate.training_authorities
    ):
        raise AssertionError("C05 target diagnostic training authority drift")

    bound_at = perf_counter()
    parent, candidate_bundle, candidate_state, cache = _candidate_from_live_parent(
        run_dir, candidate)
    candidate_sha256 = candidate_identity_digest(candidate_state)
    fresh_seed = _owner_seed(
        release.release_sha256, cache, target_capability, candidate_sha256)
    initial_seed = fresh_seed + C05_FRESH_TARGET_SEED_OFFSET
    target_draw = _fresh_rows(
        source_context, (target_capability,), seed=initial_seed, training=training)
    bound_done = perf_counter()

    target_instruments = _instruments(
        source_context, candidate_bundle, artifact_path, target_draw.rows,
        seed=target_draw.seed, each=C05_PROBE_EACH)
    instruments_done = perf_counter()
    parent_solver, parent_generation = factory_complete_solver(
        source_context, parent, artifact_path, target_instruments)
    parent_solver_done = perf_counter()
    candidate_solver, candidate_generation = factory_complete_solver(
        source_context, candidate_bundle, artifact_path, target_instruments)
    candidate_solver_done = perf_counter()

    parent_correct, candidate_correct, cases = _evaluate_solver_cases(
        parent_solver, parent_generation, candidate_solver, candidate_generation,
        target_instruments)

    finished = perf_counter()
    delta = candidate_correct - parent_correct
    return {
        "schema": "bilqis.mlx.c05-target-diagnostic/v1",
        "authorizing": False,
        "target_capability": target_capability,
        "target_seed": target_draw.seed,
        "initial_seed": initial_seed,
        "source_draw_attempts": target_draw.seed - initial_seed + 1,
        "training_family_ids": training[0],
        "training_episode_ids": training[1],
        "parent_generation": parent_generation,
        "candidate_generation": candidate_generation,
        "parent_correct": parent_correct,
        "candidate_correct": candidate_correct,
        "total": len(target_instruments),
        "delta": delta,
        "decisive_rejection_reason": (
            "NO_MEASURABLE_TARGET_GAIN" if delta <= 0 else None),
        "cases": cases,
        "timing_seconds": {
            "bind_and_draw": bound_done - bound_at,
            "instrument_compile": instruments_done - bound_done,
            "parent_solver_build": parent_solver_done - instruments_done,
            "candidate_solver_build": candidate_solver_done - parent_solver_done,
            "solve": finished - candidate_solver_done,
            "total": finished - started,
        },
    }


__all__ = ("diagnose_factory_retention_target",)
