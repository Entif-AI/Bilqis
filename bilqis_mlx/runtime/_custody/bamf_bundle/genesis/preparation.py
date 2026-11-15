"""Construct and validate owner-issued BAMF generation zero."""
from __future__ import annotations

from bilqis_mlx.factory.executable_release import (
    ExecutableAdmissionReceipt, ExecutableFactoryRelease,
)
from bilqis_mlx.learning.atlas_candidate import CandidateState
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    bind_candidate_identity,
)
from bilqis_mlx.learning.atlas_engram import INITIAL_MOTIF_CAPACITY, MotifManifest
from bilqis_mlx.learning.atlas_engram_transaction import MotifAllocationSnapshot
from bilqis_mlx.learning.atlas_plasticity import PlasticityPolicy
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.atlas_optimizer import (
    AdamWHyperparameters, _create_unbound_bamf_optimizer,
)
from bilqis_mlx.runtime.model_topology_v2 import (
    B01GenerationAuthority, GenerationProvenance, b01_generation_extents,
    validate_b01_generation_authority,
)

from ..records import BamfBundleCandidate, invalid, sidecar_records
from .foundation import (
    InitialFoundationFeatureAuthority, initial_foundation_row_ages,
    initial_foundation_sidecars,
)
from .origin import InitialFactoryFoundationAuthority
from .preparation_authority import (
    PreparedInitialGeneration, _PREPARED_INITIAL_GENERATION_ISSUER,
    _factory_generation_provenance, _host_bound_frontier, _issue_binding,
    _validate_candidate_b01_authority, _validate_candidate_source_authority,
    _validated_factory_origin,
)
from .records import (
    BamfRunIdentity, InitialGenerationBinding, ParsedInitialGenerationBinding,
    initial_generation_candidate_identity_digest, optimizer_hyperparameters_digest,
)

def _build_initial_candidate(
        *, run_id, run_seed, release, admission, origin_checkpoint, model_authority,
        optimizer_hyperparameters, provenance, foundation_features,
        correction_frontier, semantic_abi, compiler_features, teacher_state,
        evaluation_contract, delivery_events):
    allocations = MotifAllocationSnapshot(MotifManifest(provenance.release_digest))
    try:
        extents = b01_generation_extents(
            semantic_abi=semantic_abi, compiler_features=compiler_features,
            motif_page_count=allocations.manifest.capacity // INITIAL_MOTIF_CAPACITY,
            motif_key_map_digest=allocations.manifest.digest)
        topology, implementation_sha256 = validate_b01_generation_authority(
            model_authority, extents)
    except (TypeError, ValueError, KeyError):
        invalid("BAMF_INITIAL_GENERATION_MODEL_AUTHORITY_DRIFT")
    optimizer, _decay, _initialization = _create_unbound_bamf_optimizer(
        topology, extents, run_seed=run_seed)
    state = CandidateState(
        optimizer, PlasticityPolicy(
            "FOUNDATION", 0, initial_foundation_row_ages(foundation_features)),
        allocations, 0)
    state_binding = bind_candidate_identity(state, topology.digest, extents.digest)
    identity = BamfRunIdentity(
        run_id, run_seed, origin_checkpoint.sha256, origin_checkpoint.filename,
        origin_checkpoint.optimizer_step,
        release.release_sha256, admission.semantic_graph_sha256,
        state_binding.digest, topology.digest, extents.digest,
        implementation_sha256, provenance.source_identity, provenance.release_digest,
        provenance.teacher_identity, provenance.teacher_epoch)
    return BamfBundleCandidate(
        run_id, 0, None, implementation_sha256, topology, extents, state,
        optimizer_hyperparameters, provenance, semantic_abi, compiler_features,
        correction_frontier, teacher_state, evaluation_contract,
        {"schema": "bilqis.mlx.bamf-generation-transition/v1", "kind": "INITIAL",
         "invalidate_derived_caches": False},
        delivery_events, identity)


def prepare_initial_generation(
        *, run_id: str, run_seed: int, graph: dict,
        model_authority: B01GenerationAuthority,
        optimizer_hyperparameters: AdamWHyperparameters,
        provenance: GenerationProvenance,
        factory_authority: InitialFactoryFoundationAuthority | None = None,
        release: ExecutableFactoryRelease | None = None,
        admission: ExecutableAdmissionReceipt | None = None,
        origin_checkpoint: Checkpoint | None = None,
        foundation_features: InitialFoundationFeatureAuthority | None = None,
        delivery_events: tuple = ()) -> PreparedInitialGeneration:
    """Construct one source-bound generation-zero candidate and live B13 capability."""
    authority = _validated_factory_origin(
        factory_authority, graph, release=release, admission=admission,
        origin_checkpoint=origin_checkpoint)
    release, admission = authority.release, authority.admission
    origin_checkpoint = authority.origin_checkpoint
    if type(foundation_features) is not InitialFoundationFeatureAuthority:
        invalid("BAMF_INITIAL_GENERATION_SOURCE_AUTHORITY_INVALID")
    expected_provenance = _factory_generation_provenance(
        release, foundation_features)
    if (not isinstance(run_id, str) or not run_id
            or type(run_seed) is not int or run_seed < 0
            or type(model_authority) is not B01GenerationAuthority
            or type(optimizer_hyperparameters) is not AdamWHyperparameters
            or type(provenance) is not GenerationProvenance
            or provenance != expected_provenance
            or type(delivery_events) is not tuple):
        invalid("BAMF_INITIAL_GENERATION_SOURCE_AUTHORITY_DRIFT")
    sidecars = list(initial_foundation_sidecars(
        release, admission, graph, run_seed=run_seed,
        feature_authority=foundation_features))
    sidecars[2] = _host_bound_frontier(sidecars[2])
    candidate = _build_initial_candidate(
        run_id=run_id, run_seed=run_seed, release=release, admission=admission,
        origin_checkpoint=origin_checkpoint, model_authority=model_authority,
        optimizer_hyperparameters=optimizer_hyperparameters,
        provenance=provenance, foundation_features=foundation_features,
        correction_frontier=sidecars[2], semantic_abi=sidecars[0],
        compiler_features=sidecars[1], teacher_state=sidecars[3],
        evaluation_contract=sidecars[4], delivery_events=delivery_events)
    sidecar_records(candidate)
    binding = _issue_binding(
        candidate, release=release, admission=admission, graph=graph,
        origin_checkpoint=origin_checkpoint, factory_authority=authority,
        foundation_features=foundation_features)
    prepared = object.__new__(PreparedInitialGeneration)
    for name, value in (
            ("candidate", candidate), ("binding", binding),
            ("factory_authority", authority), ("graph", dict(graph)),
            ("foundation_features", foundation_features),
            ("_issuance", _PREPARED_INITIAL_GENERATION_ISSUER)):
        object.__setattr__(prepared, name, value)
    prepared.__post_init__()
    return prepared


def validate_initial_generation_binding(candidate, binding) -> None:
    """Require a live B13 bootstrap capability for the exact generation-zero state."""
    if type(binding) is InitialGenerationBinding:
        binding.__post_init__()
    if (type(candidate) is not BamfBundleCandidate
            or type(binding) is not InitialGenerationBinding
            or candidate.generation != 0 or candidate.parent_manifest_sha256 is not None
            or type(candidate.run_identity) is not BamfRunIdentity
            or binding.run_id != candidate.run_id
            or binding.run_identity_sha256 != candidate.run_identity.digest
            or binding.candidate_identity_sha256
            != initial_generation_candidate_identity_digest(candidate)
            or binding.optimizer_hyperparameters_sha256
            != optimizer_hyperparameters_digest(candidate.optimizer_hyperparameters)
            or binding.feature_sha256 != candidate.extents.factor_map_digest
            or binding.optimizer_step != candidate.retained_state.optimizer_step):
        invalid("BAMF_INITIAL_GENERATION_BINDING_DRIFT")


def validate_initial_generation_preparation(prepared: PreparedInitialGeneration) -> None:
    """Replay all Factory/source/B01 authority immediately before mutation."""
    if type(prepared) is not PreparedInitialGeneration:
        invalid("BAMF_INITIAL_GENERATION_PREPARATION_REQUIRED")
    prepared.__post_init__()
    _validate_candidate_source_authority(
        prepared.candidate, release=prepared.release,
        admission=prepared.admission, graph=prepared.graph,
        origin_checkpoint=prepared.origin_checkpoint,
        factory_authority=prepared.factory_authority,
        foundation_features=prepared.foundation_features)
    _validate_candidate_b01_authority(
        prepared.candidate, prepared.foundation_features)
    validate_initial_generation_binding(prepared.candidate, prepared.binding)


def validate_parsed_initial_generation_binding(student, binding, expected_digest: str) -> None:
    """Revalidate persisted bootstrap evidence without restoring live authority."""
    if (type(binding) is not ParsedInitialGenerationBinding
            or type(student.run_identity) is not BamfRunIdentity
            or student.generation != 0 or binding.digest != expected_digest
            or binding.run_id != student.run_id
            or binding.run_identity_sha256 != student.run_identity.digest
            or binding.candidate_identity_sha256
            != initial_generation_candidate_identity_digest(student)
            or binding.optimizer_hyperparameters_sha256
            != optimizer_hyperparameters_digest(student.optimizer_hyperparameters)
            or binding.feature_sha256 != student.extents.factor_map_digest
            or binding.optimizer_step != student.retained_state.optimizer_step):
        invalid("BAMF_INITIAL_GENERATION_BINDING_DRIFT")
