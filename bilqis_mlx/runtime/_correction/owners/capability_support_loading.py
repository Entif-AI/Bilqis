"""Authenticated accepted-generation loading for C09 capability support."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.learning.atlas_acceptance import (
    ACCEPTANCE_SCHEMA, CLOSURE_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
    EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
    EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
)

from .atlas_requalification_contracts import RequalificationLedger
from .atlas_revalidation_common import _invalid
from .capability_support_materialization import materialized_support, retained_closure_nodes


_SOURCE_QUALIFIED_ACCEPTANCE_SCHEMAS = (
    ACCEPTANCE_SCHEMA,
    CLOSURE_ACCEPTANCE_SCHEMA,
    MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
    EXACT_ACCEPTANCE_SCHEMA,
    EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
    EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
)


def _accepted_materialization(
    run_dir: Path, manifest_sha256: str, expected_acceptance_sha256: str | None = None,
):
    """Authenticate every ancestor against the current pointer's acceptance chain."""
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest, parent_acceptance_anchor_from_manifest,
    )
    from bilqis_mlx.runtime.bamf_bundle.publication import (
        _live_bundle_manifest, _pointer_lock, _read_pointer,
    )
    from bilqis_mlx.runtime.accepted_correction_ledger import _manifest_lineage

    run_dir = Path(run_dir)
    with _pointer_lock(run_dir):
        pointer = _read_pointer(run_dir / "bamf-state.json")
        if pointer is None:
            _invalid("BAMF_C09_CAPABILITY_SUPPORT_GENERATION_MISSING")
        _live_bundle_manifest(run_dir, pointer)
        current = pointer["manifest_sha256"]
        expected = pointer.get("acceptance_sha256")
        if not isinstance(expected, str):
            _invalid("BAMF_C09_CAPABILITY_SUPPORT_ACCEPTANCE_MISSING")
        if current != manifest_sha256:
            lineage = _manifest_lineage(run_dir, current)
            if manifest_sha256 not in lineage:
                _invalid("BAMF_C09_CAPABILITY_SUPPORT_ACCEPTANCE_DRIFT")
            for child in reversed(lineage[lineage.index(manifest_sha256) + 1:]):
                expected = parent_acceptance_anchor_from_manifest(run_dir, child)
                if expected is None:
                    _invalid("BAMF_C09_CAPABILITY_SUPPORT_ACCEPTANCE_MISSING")
        if expected_acceptance_sha256 is not None and expected != expected_acceptance_sha256:
            _invalid("BAMF_C09_CAPABILITY_SUPPORT_ACCEPTANCE_DRIFT")
        student = load_bamf_bundle(
            run_dir / "bamf-bundles" / manifest_sha256,
            expected_manifest_sha256=manifest_sha256,
        )
        binding = accepted_binding_for_manifest(
            run_dir, manifest_sha256, student, expected_acceptance_sha256=expected)
    return binding, student


def _latest_source_qualified_materialization(
    run_dir: Path, current_manifest_sha256: str, capability_id: str,
):
    """Resolve the newest accepted ancestor that actually qualified this capability."""
    from bilqis_mlx.runtime.accepted_correction_ledger import _manifest_lineage

    for manifest_sha256 in reversed(_manifest_lineage(
            Path(run_dir), current_manifest_sha256)):
        binding, student = _accepted_materialization(run_dir, manifest_sha256)
        if (binding.schema_version not in _SOURCE_QUALIFIED_ACCEPTANCE_SCHEMAS
                or not any(anchor[0] == capability_id
                           for anchor in getattr(binding, "source_anchors", ()))):
            continue
        return manifest_sha256, binding, student
    _invalid("BAMF_C09_CAPABILITY_SUPPORT_SOURCE_MISSING")


def load_current_support(run_dir: Path, capability_id: str):
    from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
    from bilqis_mlx.runtime.bamf_bundle.publication import (
        _live_bundle_manifest, _pointer_lock, _read_pointer,
    )

    run_dir = Path(run_dir)
    with _pointer_lock(run_dir):
        pointer = _read_pointer(run_dir / "bamf-state.json")
        if pointer is None:
            _invalid("BAMF_C09_CAPABILITY_SUPPORT_GENERATION_MISSING")
        manifest_sha256 = pointer["manifest_sha256"]
        _live_bundle_manifest(run_dir, pointer)
    _current_binding, current_student = _accepted_materialization(
        run_dir, manifest_sha256)
    source_manifest_sha256, binding, student = (
        _latest_source_qualified_materialization(
            run_dir, manifest_sha256, capability_id))
    support, node, _source_generation_bindings = materialized_support(
        binding, student, source_manifest_sha256, capability_id)
    current_generation_binding = execution_generation_digest(
        current_student.retained_state.optimizer.parameters,
        spec=current_student.topology,
        extents=current_student.extents,
    )
    closure = retained_closure_nodes(binding, student, capability_id)
    return manifest_sha256, support, node, (current_generation_binding,), closure


def accepted_support_census(
    run_dir: Path, manifest_sha256: str,
) -> tuple[RequalificationLedger, tuple[object, ...]]:
    """Materialize current lossless learned support without physical owners."""
    from bilqis_mlx.runtime.accepted_correction_ledger import _manifest_lineage

    materializations = {}
    for lineage_manifest in reversed(_manifest_lineage(run_dir, manifest_sha256)):
        binding, student = _accepted_materialization(run_dir, lineage_manifest)
        if (binding.schema_version not in _SOURCE_QUALIFIED_ACCEPTANCE_SCHEMAS
                or not getattr(binding, "source_anchors", ())):
            continue
        for capability_id in sorted({anchor[0] for anchor in binding.source_anchors}):
            materializations.setdefault(
                capability_id, (lineage_manifest, binding, student))
    supports = []
    nodes = {}
    for capability_id, (source_manifest, binding, student) in sorted(
            materializations.items()):
        support, node, _bindings = materialized_support(
            binding, student, source_manifest, capability_id)
        supports.append(support)
        for item in (node, *retained_closure_nodes(binding, student, capability_id)):
            if item.artifact_id in nodes and nodes[item.artifact_id] != item:
                _invalid("BAMF_C09_CAPABILITY_SUPPORT_CLOSURE_CONFLICT")
            nodes[item.artifact_id] = item
    return RequalificationLedger(tuple(supports)), tuple(nodes.values())


__all__ = ("accepted_support_census", "load_current_support")
