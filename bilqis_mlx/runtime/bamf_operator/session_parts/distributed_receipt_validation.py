"""Cold validation of C08 distributed attempt evidence bound into B13 events."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.atlas_resources import (
    load_persisted_distributed_manifest, validate_distributed_resume,
)


_FIELDS = (
    "c08_distributed_manifest_digest",
    "c08_distributed_logical_batch_digest",
    "c08_distributed_source_release",
    "c08_distributed_curriculum_release",
    "c08_distributed_world_size",
    "c08_distributed_backend",
    "c08_distributed_device_families",
    "c08_distributed_mlx_version",
    "c08_distributed_numeric_precision",
    "c08_distributed_reduction_policy",
)


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_FIRST_STUDENT.INVALID, reason=reason)


def validate_distributed_step_receipts(
        run_dir: Path, proposal: dict, steps: list[dict]) -> None:
    """Verify historical distributed topology evidence without making it model identity."""
    for step in steps:
        controls = step.get("controls") if isinstance(step, dict) else None
        cost = controls.get("realized_cost") if isinstance(controls, dict) else None
        if not isinstance(cost, dict):
            continue
        present = {name for name in _FIELDS if name in cost}
        if not present:
            continue
        if present != set(_FIELDS):
            _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_EVIDENCE_INCOMPLETE")
        logical_batch = cost["c08_distributed_logical_batch_digest"]
        manifest = load_persisted_distributed_manifest(Path(run_dir), logical_batch)
        devices = cost["c08_distributed_device_families"]
        if not isinstance(devices, (tuple, list)):
            _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_EVIDENCE_DRIFT")
        if (manifest.digest != cost["c08_distributed_manifest_digest"]
                or manifest.retained_generation != proposal.get("generation")
                or manifest.retained_manifest_sha256
                != proposal.get("accepted_manifest_sha256")
                or manifest.logical_batch_digest != logical_batch
                or manifest.source_release != cost["c08_distributed_source_release"]
                or manifest.curriculum_release
                != cost["c08_distributed_curriculum_release"]
                or manifest.curriculum_release
                != proposal.get("factory_release_sha256")
                or manifest.numeric_precision
                != cost["c08_distributed_numeric_precision"]
                or manifest.reduction_policy
                != cost["c08_distributed_reduction_policy"]):
            _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_EVIDENCE_DRIFT")
        validate_distributed_resume(
            manifest,
            world_size=cost["c08_distributed_world_size"],
            backend=cost["c08_distributed_backend"],
            device_families=tuple(devices),
            mlx_version=cost["c08_distributed_mlx_version"])


__all__ = ("validate_distributed_step_receipts",)
