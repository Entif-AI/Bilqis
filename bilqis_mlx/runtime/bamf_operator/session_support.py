"""Visit context, evidence and resource helpers for the BAMF operator."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import math
import shutil

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.paths import LEGACY_SOURCE
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.bamf_bundle import (
    authenticate_bamf_execution_feature_context,
)
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.semantics.atlas.feature_io import persist_feature_manifest


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_FIRST_STUDENT.INVALID, reason=reason)


@dataclass(frozen=True)
class BamfPreparedVisit:
    """One owner-composed candidate with no rejection/publication side effect."""

    status: str
    parent: object
    selection: object | None = None
    step: object | None = None
    steps: tuple = ()
    decision: object | None = None
    retained: object | None = None
    capability: str | None = None
    successor: object | None = None
    candidate_evidence: dict | None = None
    rejection_journal_ordinal: int | None = None
    rejection_attempt_ordinal: int | None = None


def _execution_context(run_dir: Path, *, currentness_metrics=None):
    host = AcceptedRuntimeHost(run_dir, currentness_metrics=currentness_metrics)
    parent = load_accepted_generation(run_dir)
    context = host.source_context(source_root=LEGACY_SOURCE.resolve())
    authenticated = authenticate_bamf_execution_feature_context(
        parent, None, run_dir)
    object.__setattr__(context, "_accepted_feature_context", authenticated)
    feature = persist_feature_manifest(
        authenticated.features, run_dir / "operator-artifacts" / "features",
        predecessor=authenticated.construction_predecessor)
    return parent, context, authenticated.selection.path, feature.path


def _step_seed(visit_id: str, ordinal: int = 1) -> int:
    if type(ordinal) is not int or ordinal < 1:
        _invalid("BAMF_C16_3_STEP_ORDINAL_INVALID")
    suffix = "" if ordinal == 1 else f"|step={ordinal}"
    return int.from_bytes(sha256(
        f"bilqis.bamf.c16.3-step-seed/v1|{visit_id}{suffix}".encode()).digest()[:8], "big")


def _resource_observation(run_dir: Path, step) -> dict:
    """Capture only resource facts the accepted visit can truthfully support."""
    steps = step if type(step) is tuple else (step,)
    if not steps:
        _invalid("BAMF_C16_3_RESOURCE_OBSERVATION_INVALID")
    budget, wall_seconds = None, 0.0
    atlas_reloads = feature_rebuilds = 0
    visit_atlas_reloads = visit_feature_rebuilds = None
    for ordinal, item in enumerate(steps, 1):
        cost = getattr(item, "realized_cost", None)
        if not isinstance(cost, dict):
            _invalid("BAMF_C16_3_RESOURCE_OBSERVATION_INVALID")
        current_budget = cost.get("c08_memory_budget_bytes")
        current_wall = cost.get("wall_seconds")
        current_atlas = cost.get("atlas_reload_count", 0)
        current_features = cost.get("feature_manifest_rebuild_count", 0)
        current_visit_atlas = cost.get("visit_atlas_reload_count", current_atlas)
        current_visit_features = cost.get(
            "visit_feature_manifest_rebuild_count", current_features)
        if (type(current_budget) is not int or current_budget <= 0
                or (budget is not None and current_budget != budget)
                or type(current_wall) not in (int, float) or type(current_wall) is bool
                or not math.isfinite(current_wall) or current_wall <= 0
                or cost.get("optimizer_steps") != 1
                or cost.get("candidate_optimizer_steps", ordinal) != ordinal
                or type(current_atlas) is not int or current_atlas < 0
                or type(current_features) is not int or current_features < 0
                or type(current_visit_atlas) is not int or current_visit_atlas < 0
                or type(current_visit_features) is not int or current_visit_features < 0
                or (visit_atlas_reloads is not None
                    and current_visit_atlas != visit_atlas_reloads)
                or (visit_feature_rebuilds is not None
                    and current_visit_features != visit_feature_rebuilds)):
            _invalid("BAMF_C16_3_RESOURCE_OBSERVATION_INVALID")
        budget = current_budget
        wall_seconds += float(current_wall)
        atlas_reloads += current_atlas
        feature_rebuilds += current_features
        visit_atlas_reloads = current_visit_atlas
        visit_feature_rebuilds = current_visit_features
    final_transaction = getattr(steps[-1], "transaction", None)
    optimizer_steps = getattr(final_transaction, "update_steps", len(steps))
    if optimizer_steps != len(steps):
        _invalid("BAMF_C16_3_RESOURCE_OBSERVATION_INVALID")
    disk_used = shutil.disk_usage(Path(run_dir)).used
    return {
        "schema": "bilqis.bamf.c16.3-resource-observation/v1",
        "memory_budget_bytes": budget,
        "disk_used_bytes": disk_used,
        "optimizer_steps": optimizer_steps,
        "wall_seconds": float(wall_seconds),
        "atlas_reload_count": atlas_reloads,
        "feature_manifest_rebuild_count": feature_rebuilds,
        "visit_atlas_reload_count": visit_atlas_reloads,
        "visit_feature_manifest_rebuild_count": visit_feature_rebuilds,
    }
