"""Small pure/read-only helpers for projecting accepted C11 command state."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from types import MappingProxyType

from bilqis_mlx.mission_control.operator import ActionParameter
from bilqis_mlx.runtime.bamf_bundle import inspect_accepted_generation

from .model import ResolvedCommandTarget
from ..transport import _invalid


VALUE_FLAGS = MappingProxyType({
    "model_topology": "--model-topology",
    "atlas_release_manifest": "--atlas-release-manifest",
    "run_id": "--run-id",
    "run_seed": "--run-seed",
    "learning_rate": "--learning-rate",
    "adam_beta1": "--adam-beta1",
    "adam_beta2": "--adam-beta2",
    "adam_eps": "--adam-eps",
    "weight_decay": "--weight-decay",
    "atlas_admission_scope": "--atlas-admission-scope",
    "admission_policy": "--admission-policy",
    "minutes": "--minutes",
    "steps_per_visit": "--steps-per-visit",
    "max_visits": "--max-visits",
    "source_prefetch_workers": "--source-prefetch-workers",
    "batch_size": "--batch-size",
    "reserve_gib": "--reserve-gib",
})

BOOL_FLAGS = MappingProxyType({
    "autonomous_curriculum": "--autonomous-curriculum",
    "verify_source": "--verify-source",
    "timing_trace": "--timing-trace",
    "flash_mode": "--flash-mode",
    "source_teaching_enrichment": "--source-teaching-enrichment",
    "admit_next_grade_with_debt": "--admit-next-grade-with-debt",
})


def parameter_map(parameters: tuple[ActionParameter, ...]) -> dict[str, object]:
    return {parameter.key: parameter.value for parameter in parameters}


def parameter_flags(
    parameters: tuple[ActionParameter, ...], *,
    omit: frozenset[str] = frozenset(),
) -> list[str]:
    result: list[str] = []
    for parameter in parameters:
        if parameter.key in omit:
            continue
        if parameter.key in VALUE_FLAGS:
            if type(parameter.value) not in (str, int, float):
                _invalid("CONTROL_PLANE_COMMAND_PARAMETER_INVALID")
            result.extend((VALUE_FLAGS[parameter.key], str(parameter.value)))
        elif parameter.key in BOOL_FLAGS:
            if type(parameter.value) is not bool:
                _invalid("CONTROL_PLANE_COMMAND_PARAMETER_INVALID")
            if parameter.value:
                result.append(BOOL_FLAGS[parameter.key])
        else:
            _invalid("CONTROL_PLANE_COMMAND_PARAMETER_UNSUPPORTED")
    return result


def run_cli_json(argv: tuple[str, ...]) -> dict:
    completed = subprocess.run(
        [sys.executable, "-m", "bilqis_mlx.cli", *argv],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        _invalid(
            f"CONTROL_PLANE_COMMAND_PREFLIGHT_REJECTED_{completed.returncode}")
    for line in reversed(completed.stdout.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    _invalid("CONTROL_PLANE_COMMAND_PREFLIGHT_OUTPUT_INVALID")


def report_target(
    run_dir: Path, report: dict, *, existing: bool,
) -> ResolvedCommandTarget:
    identity = report.get("run_identity")
    topology = report.get("model_topology")
    atlas = report.get("atlas_release_manifest")
    if not all(isinstance(item, dict) for item in (identity, topology, atlas)):
        _invalid("CONTROL_PLANE_COMMAND_PREFLIGHT_OUTPUT_INVALID")
    inspection = None
    if existing:
        inspection = inspect_accepted_generation(run_dir / "bamf-state.json")
        if inspection is None:
            _invalid("CONTROL_PLANE_COMMAND_TARGET_UNAVAILABLE")
    return ResolvedCommandTarget(
        run_dir=str(run_dir),
        run_id=identity.get("run_id"),
        run_seed=identity.get("run_seed"),
        run_identity_sha256=identity.get("run_identity_sha256"),
        generation=inspection.generation if inspection else 0,
        generation_manifest_sha256=(
            inspection.generation_manifest_sha256 if inspection else None),
        optimizer_step=inspection.optimizer_step if inspection else 0,
        candidate_identity_sha256=(
            inspection.candidate_identity_sha256
            if inspection else identity.get("initial_candidate_identity_sha256")),
        factory_release_sha256=(
            inspection.factory_release_sha256
            if inspection else identity.get("factory_release_sha256")),
        semantic_release_sha256=(
            inspection.semantic_release_sha256
            if inspection else atlas.get("release_sha256")),
        topology_sha256=(
            inspection.topology_sha256 if inspection else topology.get("digest")),
        acceptance_sha256=(
            inspection.acceptance_sha256 if inspection else None),
        source_identity=identity.get("initial_source_identity"),
    )


def same_lineage(
    expected: ResolvedCommandTarget, actual: ResolvedCommandTarget,
) -> bool:
    fields = (
        "run_dir", "run_id", "run_seed", "run_identity_sha256",
        "topology_sha256", "source_identity",
    )
    return all(
        getattr(expected, name) is None
        or getattr(actual, name) == getattr(expected, name)
        for name in fields
    )
