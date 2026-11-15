"""Publication and mutation helpers shared by BAMF custody tests."""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
from copy import deepcopy
from dataclasses import replace
import os
from pathlib import Path
from unittest.mock import patch

from bilqis_mlx.data_plane import data_plane
from bilqis_mlx.learning.atlas_acceptance import mint_acceptance_binding
from bilqis_mlx.learning.atlas_engram_transaction import MotifAllocationSnapshot
from bilqis_mlx.runtime.bamf_bundle import (
    load_bamf_generation, publish_bamf_generation, publish_initial_generation,
)
from bilqis_mlx.runtime.bamf_bundle.admission import derive_successor_bundle
from bilqis_mlx.runtime.bamf_bundle.motif.codec import snapshot_to_record
from bilqis_mlx.runtime.bamf_bundle.records import canonical, sha
from bilqis_mlx.runtime.model_topology_v2 import GenerationExtents, ParameterCensus
from bilqis_mlx.semantics.tests.core.test_atlas_export_clearance import REGISTRY


@contextmanager
def host_source_authority_patch(registry=REGISTRY):
    """Substitute the fixed host reader for one complete test scenario."""
    with patch(
            "bilqis_mlx.runtime.bamf_bundle.source_authority_custody."
            "read_host_system_source_authority_registry",
            return_value=registry):
        yield


def rewrite_motif_bundle_fixture(
        bundle_root: Path, manifest: dict,
        allocations: MotifAllocationSnapshot) -> dict:
    root = Path(bundle_root)
    record = deepcopy({key: value for key, value in manifest.items()
                       if key != "manifest_sha256"})
    raw_motif = canonical(snapshot_to_record(allocations))
    motif_sha = sha(raw_motif)
    motif_path = root / record["sidecars"]["motif_allocation"]["filename"]
    with motif_path.open("wb") as stream:
        stream.write(raw_motif)
        stream.flush()
        os.fsync(stream.fileno())
    data_plane().put_object(motif_sha, raw_motif)
    record["sidecars"]["motif_allocation"] = {
        "filename": motif_path.name,
        "sha256": motif_sha,
        "object_sha256": motif_sha,
    }
    prior_extents = record["extents"]
    record["extents"] = GenerationExtents(
        prior_extents["semantic_bank_count"], prior_extents["motif_page_count"],
        prior_extents["active_semantic_digest"], allocations.manifest.digest,
        prior_extents["factor_map_digest"],
    ).to_record()
    raw_manifest = canonical(record)
    manifest_sha = sha(raw_manifest)
    manifest_path = root / "manifest.json"
    with manifest_path.open("wb") as stream:
        stream.write(raw_manifest)
        stream.flush()
        os.fsync(stream.fileno())
    data_plane().put_node(
        manifest_sha, raw_manifest, record["generation"],
        record["parent_manifest_sha256"])
    directory = os.open(root, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return {**record, "manifest_sha256": manifest_sha}


def shape_patch(registry=REGISTRY):
    from ..helpers import DECLARED
    from ..genesis_authority_fixtures import genesis_feature_source_patch

    stack = ExitStack()
    stack.enter_context(host_source_authority_patch(registry))
    stack.enter_context(genesis_feature_source_patch())
    for target in ("bilqis_mlx.runtime.model_topology_v2.expected_bamf_shapes",
                   "bilqis_mlx.runtime.topology_v2.ledger.expected_bamf_shapes",
                   "bilqis_mlx.runtime.topology_v2.validation.expected_bamf_shapes",
                   "bilqis_mlx.runtime.backbone_identity.expected_bamf_shapes",
                   "bilqis_mlx.learning.atlas_participation_census."
                   "expected_bamf_shapes",
                   "bilqis_mlx.learning._retention.atlas_participation_census."
                   "expected_bamf_shapes"):
        stack.enter_context(patch(target, return_value=DECLARED))

    def census(spec, extents):
        return ParameterCensus(spec.digest, extents.digest, DECLARED)

    stack.enter_context(patch(
        "bilqis_mlx.runtime.topology_v2.construction.bamf_parameter_census",
        side_effect=census))
    return stack


def retention_decision(*, accepted=True, parent=None, retained=None) -> object:
    from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
        _screen_inputs,
    )
    from tests.bamf_disposable_retention import issue_disposable_screen
    from ..helpers import parent_state

    screen = _screen_inputs(protected_loss=2 if accepted else 3)
    return issue_disposable_screen(
        screen,
        parent if parent is not None else parent_state(),
        retained if retained is not None else parent_state(),
    )


def acceptance(bundle, *, parent=None) -> object:
    from bilqis_mlx.runtime.bamf_bundle.genesis.records import (
        successor_candidate_identity_digest,
    )
    from bilqis_mlx.runtime.bamf_bundle.records import canonical, sha
    return mint_acceptance_binding(
        retention_decision(parent=parent, retained=bundle.retained_state),
        bundle.retained_state, run_id=bundle.run_id,
        generation=bundle.generation,
        feature_sha256=bundle.extents.factor_map_digest,
        source_authority_registry_sha256=bundle.correction_frontier.get(
            "source_authority_registry_sha256"),
        teacher_state_sha256=sha(canonical(dict(bundle.teacher_state))),
        generation_authority_sha256=successor_candidate_identity_digest(bundle))


def _publish_initial_candidate(run_dir, bundle, foundation_features):
    from ..helpers import accepted_state, genesis_preparation

    prepared = genesis_preparation(
        run_id=bundle.run_id,
        foundation_features=foundation_features,
        delivery_events=({"event": "FIXTURE_GENESIS", "optimizer_step": 0},))
    pointer = publish_initial_generation(run_dir, prepared, reserve_gib=0.)
    source_authority = bundle.correction_frontier.get(
        "source_authority_registry_sha256")
    source_authority_record = bundle.correction_frontier.get(
        "source_authority_registry")
    if source_authority is None:
        return pointer
    parent = load_bamf_generation(Path(run_dir) / "bamf-state.json")
    retained = accepted_state(parent.retained_state, parent.extents)
    bundle = derive_successor_bundle(
        parent, retained, parent_manifest_sha256=pointer["manifest_sha256"],
        delivery_events=({"event": "FIXTURE_SOURCE_AUTHORITY"},))
    bundle = replace(bundle, correction_frontier={
        **bundle.correction_frontier,
        "source_authority_registry_sha256": source_authority,
        "source_authority_registry": source_authority_record,
    })
    return publish_bamf_generation(
        run_dir, bundle,
        acceptance=acceptance(bundle, parent=parent.retained_state),
        reserve_gib=0.)


def _normalize_candidate_for_parent(bundle, parent):
    if bundle.run_identity is None:
        bundle = replace(bundle, run_identity=parent.run_identity)
    kind = bundle.transition.get("kind")
    if kind == "RETAINED_CANDIDATE":
        retained = replace(
            bundle.retained_state,
            allocations=parent.retained_state.allocations,
            custody=parent.retained_state.custody)
        bundle = derive_successor_bundle(
            parent, retained,
            parent_manifest_sha256=bundle.parent_manifest_sha256,
            delivery_events=bundle.outbox)
    elif kind == "PACKAGE_IMPORT":
        retained = replace(
            bundle.retained_state,
            allocations=parent.retained_state.allocations,
            custody=parent.retained_state.custody)
        bundle = replace(
            bundle, implementation_sha256=parent.implementation_sha256,
            topology=parent.topology, extents=parent.extents,
            retained_state=retained, provenance=parent.provenance,
            semantic_abi=dict(parent.semantic_abi),
            compiler_features=dict(parent.compiler_features),
            correction_frontier=dict(parent.correction_frontier),
            teacher_state=dict(parent.teacher_state),
            evaluation_contract=dict(parent.evaluation_contract),
            run_identity=parent.run_identity)
    elif kind == "PARAMETER_EXTENSION":
        retained = replace(
            bundle.retained_state,
            allocations=parent.retained_state.allocations,
            custody=parent.retained_state.custody)
        extents = replace(
            parent.extents,
            active_semantic_digest=bundle.extents.active_semantic_digest,
            factor_map_digest=bundle.extents.factor_map_digest)
        semantic = {
            **parent.semantic_abi,
            "active_set_sha256": bundle.semantic_abi["active_set_sha256"],
        }
        provenance = replace(
            parent.provenance, release_digest=bundle.provenance.release_digest)
        correction = {
            **parent.correction_frontier,
            "source_identity": provenance.source_identity,
            "release_digest": provenance.release_digest,
        }
        compiler = {
            **parent.compiler_features,
            "factor_map_sha256": extents.factor_map_digest,
            "compiler_sha256": bundle.compiler_features["compiler_sha256"],
        }
        bundle = replace(
            bundle, implementation_sha256=parent.implementation_sha256,
            topology=parent.topology, extents=extents,
            retained_state=retained, provenance=provenance,
            semantic_abi=semantic,
            compiler_features=compiler,
            correction_frontier=correction,
            teacher_state=dict(parent.teacher_state),
            evaluation_contract=dict(parent.evaluation_contract),
            run_identity=parent.run_identity)
    elif (bundle.topology == parent.topology
            and bundle.extents.semantic_bank_count == parent.extents.semantic_bank_count
            and bundle.extents.motif_page_count == parent.extents.motif_page_count
            and bundle.extents.active_semantic_digest
            == parent.extents.active_semantic_digest
            and bundle.extents.factor_map_digest == parent.extents.factor_map_digest):
        retained = replace(
            bundle.retained_state,
            allocations=parent.retained_state.allocations,
            custody=parent.retained_state.custody)
        bundle = replace(
            bundle, implementation_sha256=parent.implementation_sha256,
            topology=parent.topology, extents=parent.extents,
            retained_state=retained, provenance=parent.provenance,
            semantic_abi=dict(parent.semantic_abi),
            compiler_features=dict(parent.compiler_features),
            correction_frontier=dict(parent.correction_frontier),
            teacher_state=dict(parent.teacher_state),
            evaluation_contract=dict(parent.evaluation_contract),
            run_identity=parent.run_identity)
    return bundle


def publish_candidate(run_dir, bundle, *, foundation_features=None):
    if bundle.generation == 0:
        return _publish_initial_candidate(run_dir, bundle, foundation_features)
    parent = load_bamf_generation(Path(run_dir) / "bamf-state.json")
    bundle = _normalize_candidate_for_parent(bundle, parent)
    return publish_bamf_generation(
        run_dir, bundle,
        acceptance=acceptance(bundle, parent=parent.retained_state),
        reserve_gib=0.)


__all__ = (
    "acceptance", "host_source_authority_patch", "publish_candidate", "retention_decision",
    "rewrite_motif_bundle_fixture", "shape_patch",
)
