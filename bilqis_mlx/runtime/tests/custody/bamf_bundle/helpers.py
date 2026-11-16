"""Small real-B12 fixtures for B13.1 custody tests."""
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import replace
import os
from pathlib import Path
import tempfile

import mlx.core as mx

from bilqis_mlx.learning.atlas_candidate import (
    CandidateCustodyIdentity, CandidateState, begin_candidate, candidate_step,
    resolve_candidate,
)
from bilqis_mlx.learning._retention.tests.execution_fixtures import execution_provenance
from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.learning.atlas_engram_transaction import MotifAllocationSnapshot
from bilqis_mlx.learning.atlas_plasticity import IdentityRowAge, PlasticityPolicy
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters, AdamWStateTree
from bilqis_mlx.runtime.bamf_bundle import (
    BamfBundleCandidate, prepare_initial_generation, publish_initial_generation,
)
from bilqis_mlx.runtime.bamf_bundle.genesis.foundation import (
    initial_foundation_sidecars,
)
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, GenerationProvenance, Initializer, ModelTopologySpecV2,
    ParameterGroup, ParameterSpec, b01_generation_authority,
    b01_generation_extents, b01_model_implementation_sha256,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    genesis_feature_source_patch, issue_factory_authority, issue_feature_authority,
)

NAME = "identity.bank.0"
RELEASE = "b" * 64
IMPLEMENTATION = b01_model_implementation_sha256()
DECLARED = (ParameterSpec(NAME, (2, 2), Initializer.EMBEDDING,
                          ParameterGroup.IDENTITY_ROW_AGE, True),)
HP = AdamWHyperparameters(.001, (.9, .95), 1e-8, .01)
FIXTURE_PARENT_MANIFEST = "6" * 64


def _genesis_defaults(release, semantic_release):
    source_identity = (release.source_bindings.source_attestation_sha256
                       or release.source_bindings.digest())
    teacher_identity = release.execution_plan.projection_digests.teaching
    provenance = GenerationProvenance(
        source_identity, semantic_release, teacher_identity, 0)
    motif = MotifManifest(provenance.release_digest)
    extents = GenerationExtents(
        1, 1, "a" * 64, motif.digest, "c" * 64)
    return {
        "provenance": provenance,
        "extents": extents,
        "semantic_abi": {
            "schema": "bilqis.mlx.bamf-semantic-abi/v1",
            "active_set_sha256": "a" * 64,
            "semantic_bank_count": 1,
            "bank_identities": ["bank:0"],
        },
        "compiler_features": {
            "schema": "bilqis.mlx.bamf-compiler-features/v1",
            "factor_map_sha256": "c" * 64,
            "compiler_sha256": "f" * 64,
            "rights_epoch": 2,
            "correction_generation": 4,
        },
        "correction_frontier": {
            "schema": "bilqis.mlx.bamf-correction-frontier/v1",
            "source_identity": source_identity,
            "release_digest": release.release_sha256,
            "rights_epoch": 2,
            "correction_generation": 4,
            "frontier": [],
        },
        "teacher_state": {
            "schema": "bilqis.mlx.bamf-teacher-state/v1",
            "teacher_identity": teacher_identity,
            "teacher_epoch": 0,
            "next_seed": 42,
            "cursor": "lesson:7",
        },
        "evaluation_contract": {
            "schema": "bilqis.mlx.bamf-evaluation-contract/v1",
            "contract_sha256": "9" * 64,
        },
    }
def genesis_preparation(*, run_id="fixture-run", run_seed=17,
                        delivery_events=None, **overrides):
    """Enter B13 generation zero through the production constructor and issuer."""
    foundation_features = overrides.pop("foundation_features", None)
    from bilqis_mlx.runtime.tests.operator.test_admission import _executable_fixture
    release, graph = _executable_fixture()
    origin = Checkpoint("7" * 64, "bundles/foundation-origin", 0, True)
    factory_authority = issue_factory_authority(release, graph, origin)
    generic_features = foundation_features is None
    if generic_features:
        foundation_features = issue_feature_authority()
    forbidden = {
        "semantic_abi", "compiler_features", "correction_frontier",
        "teacher_state", "evaluation_contract",
    } & set(overrides)
    if forbidden:
        raise AssertionError(
            "generation-zero sidecars are owner-derived: " + ",".join(sorted(forbidden)))
    values = _genesis_defaults(
        release, foundation_features.features.semantic_release) | overrides
    replay = genesis_feature_source_patch() if generic_features else nullcontext()
    with replay:
        (semantic_abi, compiler_features, _correction_frontier,
         _teacher_state, _evaluation_contract) = initial_foundation_sidecars(
            release, factory_authority.admission, graph, run_seed=run_seed,
            feature_authority=foundation_features)
        motif = MotifManifest(values["provenance"].release_digest)
        extents = b01_generation_extents(
            semantic_abi=semantic_abi,
            compiler_features=compiler_features, motif_page_count=1,
            motif_key_map_digest=motif.digest)
        return prepare_initial_generation(
            run_id=run_id, run_seed=run_seed, graph=graph,
            factory_authority=factory_authority,
            model_authority=b01_generation_authority(extents),
            optimizer_hyperparameters=HP,
            provenance=values["provenance"],
            foundation_features=foundation_features,
            delivery_events=(
                ({"event": "FIXTURE_GENESIS", "optimizer_step": 0},)
                if delivery_events is None else delivery_events),
        )
def publish_genesis(run_dir, *, run_seed=17, source_authority_registry=None, **overrides):
    """Publish a real production generation zero, never a test-minted C05 token."""
    from .publication.publication_helpers import host_source_authority_patch
    patch_registry = (
        host_source_authority_patch()
        if source_authority_registry is None
        else host_source_authority_patch(source_authority_registry)
    )
    with patch_registry:
        return publish_initial_generation(
            run_dir, genesis_preparation(run_seed=run_seed, **overrides),
            reserve_gib=0.)
def parent_state() -> CandidateState:
    values = mx.array([[.5, -.25], [1., 2.]], dtype=mx.float32)
    optimizer = AdamWStateTree(
        {NAME: values}, {NAME: mx.ones_like(values) * .1},
        {NAME: mx.ones_like(values) * .01},
        {NAME: mx.array([2, 3], dtype=mx.uint64)})
    policy = PlasticityPolicy(
        "ADAPTIVE", 7, (IdentityRowAge(0, 0, 7), IdentityRowAge(0, 1, 2)))
    allocations = MotifAllocationSnapshot(MotifManifest(RELEASE))
    extents = GenerationExtents(1, 1, "a" * 64, allocations.manifest.digest, "c" * 64)
    return CandidateState(
        optimizer, policy, allocations, 11,
        CandidateCustodyIdentity(
            "fixture-run", 0, FIXTURE_PARENT_MANIFEST,
            ModelTopologySpecV2().digest, extents.digest))


def accepted_state(
        parent: CandidateState,
        extents: GenerationExtents | None = None,
        spec: ModelTopologySpecV2 | None = None) -> CandidateState:
    transaction = begin_candidate(parent)
    spec = ModelTopologySpecV2() if spec is None else spec
    extents = extents or GenerationExtents(
        1, 1, "a" * 64, parent.allocations.manifest.digest, "c" * 64)
    with shape_patch():
        transaction = candidate_step(
            transaction, {NAME: mx.array([[3., 4.], [0., 0.]], dtype=mx.float32)},
            execution_provenance(transaction.parent, rows=(0,),
                                       candidate_step=transaction.update_steps + 1,
                                       extents=extents), HP,
            spec=spec, extents=extents,
            loss_bearing=True, max_norm=1.)
    return resolve_candidate(transaction, accepted=True)


def rejected_state(
        parent: CandidateState,
        extents: GenerationExtents | None = None) -> CandidateState:
    transaction = begin_candidate(parent)
    spec = ModelTopologySpecV2()
    extents = extents or GenerationExtents(
        1, 1, "a" * 64, parent.allocations.manifest.digest, "c" * 64)
    with shape_patch():
        transaction = candidate_step(
            transaction, {NAME: mx.ones((2, 2), dtype=mx.float32)},
            execution_provenance(transaction.parent, rows=(0,),
                                       candidate_step=transaction.update_steps + 1,
                                       extents=extents), HP,
            spec=spec, extents=extents,
            loss_bearing=True, max_norm=1.)
    return resolve_candidate(transaction, accepted=False)


def next_accepted_step(
        parent: CandidateState,
        extents: GenerationExtents | None = None) -> CandidateState:
    transaction = begin_candidate(parent)
    spec = ModelTopologySpecV2()
    extents = extents or GenerationExtents(
        1, 1, "a" * 64, parent.allocations.manifest.digest, "c" * 64)
    with shape_patch():
        transaction = candidate_step(
            transaction, {NAME: mx.array([[.25, -.5], [0., 0.]], dtype=mx.float32)},
            execution_provenance(transaction.parent, rows=(0,),
                                       candidate_step=transaction.update_steps + 1,
                                       extents=extents), HP,
            spec=spec, extents=extents,
            loss_bearing=True, max_norm=1.)
    return resolve_candidate(transaction, accepted=True)


def candidate(state: CandidateState, generation=0, parent=None) -> BamfBundleCandidate:
    motif_digest = state.allocations.manifest.digest
    extents = GenerationExtents(1, 1, "a" * 64, motif_digest, "c" * 64)
    provenance = GenerationProvenance("fixture-source", "d" * 64, "fixture-teacher", 3)
    transition = {
        "schema": "bilqis.mlx.bamf-generation-transition/v1",
        "kind": "INITIAL" if generation == 0 else "RETAINED_CANDIDATE",
        "invalidate_derived_caches": generation > 0,
    }
    return BamfBundleCandidate(
        "fixture-run", generation, parent, IMPLEMENTATION, ModelTopologySpecV2(),
        extents, state, HP, provenance,
        {"schema": "bilqis.mlx.bamf-semantic-abi/v1", "active_set_sha256": "a" * 64,
         "semantic_bank_count": 1, "bank_identities": ["bank:0"]},
        {"schema": "bilqis.mlx.bamf-compiler-features/v1", "factor_map_sha256": "c" * 64,
         "compiler_sha256": "f" * 64, "rights_epoch": 2,
         "correction_generation": 4},
        {"schema": "bilqis.mlx.bamf-correction-frontier/v1", "source_identity": "fixture-source",
         "release_digest": "d" * 64, "rights_epoch": 2,
         "correction_generation": 4, "frontier": []},
        {"schema": "bilqis.mlx.bamf-teacher-state/v1", "teacher_identity": "fixture-teacher",
         "teacher_epoch": 3, "next_seed": 42, "cursor": "lesson:7"},
        {"schema": "bilqis.mlx.bamf-evaluation-contract/v1", "contract_sha256": "9" * 64},
        transition, ({"event": "FIXTURE_ACCEPTED", "optimizer_step": state.optimizer_step},))


def provision_source_authority_registry(run_dir: Path, registry) -> Path:
    """Install test-only C09 host-root material outside generation custody."""
    from bilqis_mlx.runtime.bamf_bundle.records import canonical, invalid
    from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import (
        SOURCE_AUTHORITY_REGISTRY_FILE, source_authority_registry_lock,
    )

    root = Path(run_dir)
    root.mkdir(parents=True, exist_ok=True)
    raw = canonical(registry.to_record())
    with source_authority_registry_lock(root):
        target = root / SOURCE_AUTHORITY_REGISTRY_FILE
        if target.exists():
            if target.read_bytes() != raw:
                invalid("BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_IMMUTABLE")
            return target
        fd, temporary = tempfile.mkstemp(
            prefix=".source-authority-registry.", suffix=".tmp", dir=root)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, target)
            return target
        finally:
            if temporary_path.exists():
                temporary_path.unlink()


def with_source_authority_registry(bundle, registry):
    """Bind accepted candidate material to the separately provisioned host root."""
    return replace(bundle, correction_frontier={
        **bundle.correction_frontier,
        "source_authority_registry_sha256": registry.digest,
        "source_authority_registry": registry.to_record(),
    })


from .publication.publication_helpers import (
    acceptance, publish_candidate, retention_decision,
    rewrite_motif_bundle_fixture, shape_patch,
)
