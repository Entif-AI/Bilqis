"""Operator-owned C12 receive, screen and accepted-publication composition."""
from __future__ import annotations

from pathlib import Path

from .adoption import _verify_export_clearance, publish_screened_delta_import
from .contracts import require
from .delta import apply_plastic_delta, screen_delta_candidate
from .exchange import inspect_package, stage_received_package
from .receiver import _load_current_generation, current_receiver_binding


def _stage_received_package_if_current(
        inspected, staging_dir, run_dir, accepted_manifest_sha256,
        source_authority_registry_sha256):
    """Stage only while full accepted B13/source custody remains authenticated."""
    from bilqis_mlx.runtime.bamf_bundle import publication
    from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import (
        resolve_source_authority_registry,
    )

    run_dir = Path(run_dir)
    with publication._pointer_lock(run_dir):
        student, pointer = publication._load_generation_locked(
            run_dir / "bamf-state.json")
        require(
            pointer.get("manifest_sha256") == accepted_manifest_sha256,
            "receiver accepted generation advanced after source clearance",
        )
        publication._require_published_acceptance(run_dir, pointer, student)
        require(
            student.correction_frontier.get("source_authority_registry_sha256")
            == source_authority_registry_sha256,
            "receiver acceptance authority changed after source clearance",
        )
        registry = resolve_source_authority_registry(
            run_dir, student.correction_frontier)
        require(
            registry is not None
            and registry.digest == source_authority_registry_sha256,
            "receiver source authority root changed after source clearance",
        )
        return stage_received_package(inspected, staging_dir)


def screen_received_package(
        sender_dir, staging_dir, package_sha256, run_dir, *,
        max_wire_bytes: int, source_context, artifact_path,
        target_capability: str, export_clearance, atlas_selection,
        source_frontier):
    """Run an exact remote package through C12 binding and C05 screening only."""
    run_dir = Path(run_dir)
    binding = current_receiver_binding(run_dir)
    inspected = inspect_package(
        sender_dir, package_sha256, binding, max_wire_bytes=max_wire_bytes)
    require(inspected.plan.disposition == "EXACT_BINDING",
            "package is not eligible for receiver-state adoption")

    _, parent = _load_current_generation(run_dir)
    _, accepted_manifest_sha256, source_authority_registry_sha256 = (
        _verify_export_clearance(
            inspected.package, parent, export_clearance, atlas_selection,
            source_frontier, source_context, run_dir))
    exchange = _stage_received_package_if_current(
        inspected, staging_dir, run_dir, accepted_manifest_sha256,
        source_authority_registry_sha256)

    candidate = apply_plastic_delta(exchange.package, run_dir)
    return screen_delta_candidate(
        candidate, source_context, artifact_path, target_capability,
        run_dir=run_dir)


def receive_screen_and_publish_package(
        sender_dir, staging_dir, package_sha256, run_dir, *,
        max_wire_bytes: int, source_context, artifact_path, target_capability: str,
        export_clearance, atlas_selection, source_frontier,
        reserve_gib: float = 100.0):
    """Apply one exact-binding package only through A12, C05, B12 and B13 owners."""
    screened = screen_received_package(
        sender_dir, staging_dir, package_sha256, run_dir,
        max_wire_bytes=max_wire_bytes, source_context=source_context,
        artifact_path=artifact_path, target_capability=target_capability,
        export_clearance=export_clearance, atlas_selection=atlas_selection,
        source_frontier=source_frontier)
    return publish_screened_delta_import(
        screened, Path(run_dir), export_clearance=export_clearance,
        atlas_selection=atlas_selection, source_frontier=source_frontier,
        source_context=source_context, reserve_gib=reserve_gib)
