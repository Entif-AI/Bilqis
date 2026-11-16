"""Non-authorizing fixed-school capability diagnostic for C05 protected losses."""
from __future__ import annotations

from pathlib import Path
from time import perf_counter

import mlx.core as mx

from bilqis_mlx.fixed_frontier import frontier_exam, load_frontier_cohort
from bilqis_mlx.learning.retention_policy import scaled_loss_allowance
from bilqis_mlx.runtime.capability_evaluation import _answer_identity
from bilqis_mlx.runtime.factory_complete_solver import factory_complete_solver
from bilqis_mlx.runtime.factory_retention_owner import (
    C05_PROBE_EACH, C05_PROTECTED_REFERENCE_LOSS,
    _candidate_from_live_parent, _instruments, _training_exclusions,
)
from bilqis_mlx.state_dag import read_current

from .factory_retention_target_diagnostic import _evaluate_solver_cases


def _parameter_group(name: str) -> str:
    for prefix in ("blocks.", "depth.", "plastic.", "features.", "readout.",
                   "identity.", "motif."):
        if name.startswith(prefix):
            return prefix[:-1]
    return "other"


def _optimizer_delta_summary(parent, candidate, gradient) -> dict:
    before = parent.retained_state.optimizer.parameters
    after = candidate.optimizer.parameters
    if set(before) != set(after) or set(gradient.gradients) != set(before):
        raise AssertionError("C05 fixed diagnostic optimizer census drift")
    scalars = []
    records = []
    for name in sorted(before):
        grad_max = mx.max(mx.abs(gradient.gradients[name]))
        delta_max = mx.max(mx.abs(after[name] - before[name]))
        scalars.extend((grad_max, delta_max))
        records.append((name, grad_max, delta_max))
    mx.eval(*scalars)
    groups = {}
    for name, grad_max, delta_max in records:
        group = groups.setdefault(_parameter_group(name), {
            "parameters": 0,
            "nonzero_gradient_parameters": 0,
            "changed_parameters": 0,
            "zero_gradient_changed_parameters": 0,
            "max_gradient_abs": 0.0,
            "max_delta_abs": 0.0,
        })
        grad_value = float(grad_max)
        delta_value = float(delta_max)
        group["parameters"] += 1
        group["nonzero_gradient_parameters"] += int(grad_value != 0.0)
        group["changed_parameters"] += int(delta_value != 0.0)
        group["zero_gradient_changed_parameters"] += int(
            grad_value == 0.0 and delta_value != 0.0)
        group["max_gradient_abs"] = max(group["max_gradient_abs"], grad_value)
        group["max_delta_abs"] = max(group["max_delta_abs"], delta_value)
    return groups


def _fixed_selection(source_context, candidate, target_capability, protected_capability, run_dir):
    release = source_context.release
    capability_map = release.execution_plan.capability_map
    if target_capability not in capability_map or protected_capability not in capability_map:
        raise AssertionError("C05 fixed diagnostic capability is not admitted")
    training = _training_exclusions(candidate)
    if any(
        authority.delivery_capability != target_capability
        or authority.release_sha256 != release.release_sha256
        for authority in candidate.training_authorities
    ):
        raise AssertionError("C05 fixed diagnostic training authority drift")
    parent, candidate_bundle, _candidate_state, _cache = _candidate_from_live_parent(
        run_dir, candidate)
    receipt = read_current(run_dir)
    if receipt.get("factory_release_sha256") != release.release_sha256:
        raise AssertionError("C05 fixed diagnostic Factory release drift")
    exam = frontier_exam(receipt)
    fixed = load_frontier_cohort(run_dir, exam)
    if fixed is None or exam.get("factory_release_sha256") != release.release_sha256:
        raise AssertionError("C05 fixed diagnostic cohort unavailable")
    rows = tuple(
        row for row in fixed.rows if row.get("capability") == protected_capability)
    if not rows:
        raise AssertionError("C05 fixed diagnostic protected capability absent")
    return release, training, parent, candidate_bundle, fixed, rows


def diagnose_fixed_capability(
    source_context,
    candidate,
    artifact_path: str,
    target_capability: str,
    protected_capability: str,
    *,
    run_dir: Path,
    gradient=None,
):
    """Measure one fixed protected capability without issuing retention authority."""
    started = perf_counter()
    source_context.__post_init__()
    _release, training, parent, candidate_bundle, fixed, rows = _fixed_selection(
        source_context, candidate, target_capability, protected_capability, run_dir)
    bound = perf_counter()

    instruments = _instruments(
        source_context, candidate_bundle, artifact_path, rows, seed=fixed.seed)
    instruments_done = perf_counter()
    parent_solver, parent_generation = factory_complete_solver(
        source_context, parent, artifact_path, instruments)
    candidate_solver, candidate_generation = factory_complete_solver(
        source_context, candidate_bundle, artifact_path, instruments)
    solvers_done = perf_counter()

    parent_correct, candidate_correct, cases = _evaluate_solver_cases(
        parent_solver, parent_generation, candidate_solver, candidate_generation,
        instruments)

    total = len(instruments)
    delta = candidate_correct - parent_correct
    allowance = scaled_loss_allowance(
        total, C05_PROTECTED_REFERENCE_LOSS, C05_PROBE_EACH)
    finished = perf_counter()
    return {
        "schema": "bilqis.mlx.c05-fixed-capability-diagnostic/v1",
        "authorizing": False,
        "target_capability": target_capability,
        "protected_capability": protected_capability,
        "fixed_seed": fixed.seed,
        "training_family_ids": training[0],
        "training_episode_ids": training[1],
        "parent_generation": parent_generation,
        "candidate_generation": candidate_generation,
        "parent_correct": parent_correct,
        "candidate_correct": candidate_correct,
        "total": total,
        "delta": delta,
        "protected_loss_allowance": allowance,
        "blocked": -delta > allowance,
        "optimizer_delta_groups": (
            None if gradient is None
            else _optimizer_delta_summary(parent, candidate, gradient)),
        "cases": cases,
        "timing_seconds": {
            "bind_and_select": bound - started,
            "instrument_compile": instruments_done - bound,
            "solver_build": solvers_done - instruments_done,
            "solve": finished - solvers_done,
            "total": finished - started,
        },
    }


__all__ = ("diagnose_fixed_capability",)
