"""Generation-zero preparation authority and replay validation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from bilqis_mlx.factory.executable_release import (
    ExecutableAdmissionReceipt, ExecutableFactoryRelease,
)
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_candidate import CandidateState
from bilqis_mlx.learning.atlas_engram import INITIAL_MOTIF_CAPACITY, MotifManifest
from bilqis_mlx.learning.atlas_engram_transaction import MotifAllocationSnapshot
from bilqis_mlx.learning.atlas_plasticity import PlasticityPolicy
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.atlas_optimizer import _create_unbound_bamf_optimizer
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationProvenance, ModelTopologySpecV2, b01_generation_authority,
    b01_generation_extents, validate_b01_generation_authority,
)

from ..records import BamfBundleCandidate, invalid
from .foundation import (
    InitialFoundationFeatureAuthority, initial_foundation_row_ages,
    initial_foundation_sidecars,
)
from .origin import (
    InitialFactoryFoundationAuthority, replay_initial_factory_foundation_authority,
)
from .records import (
    BamfRunIdentity, InitialGenerationBinding, _mint_initial_generation_binding,
)

_PREPARED_INITIAL_GENERATION_ISSUER = object()


@dataclass(frozen=True, init=False)
class PreparedInitialGeneration:
    candidate: BamfBundleCandidate
    binding: InitialGenerationBinding
    factory_authority: InitialFactoryFoundationAuthority
    graph: dict
    foundation_features: InitialFoundationFeatureAuthority
    _issuance: object = field(init=False, default=None, repr=False, compare=False)

    def __init__(self, *args, **kwargs) -> None:
        invalid("BAMF_INITIAL_GENERATION_PREPARATION_REQUIRED")

    def __post_init__(self) -> None:
        if getattr(self, "_issuance", None) is not _PREPARED_INITIAL_GENERATION_ISSUER:
            invalid("BAMF_INITIAL_GENERATION_PREPARATION_REQUIRED")

    @property
    def release(self) -> ExecutableFactoryRelease:
        return self.factory_authority.release

    @property
    def admission(self) -> ExecutableAdmissionReceipt:
        return self.factory_authority.admission

    @property
    def origin_checkpoint(self) -> Checkpoint:
        return self.factory_authority.origin_checkpoint


def _validated_factory_origin(
        factory_authority, graph, *, release=None, admission=None,
        origin_checkpoint=None) -> InitialFactoryFoundationAuthority:
    if (type(factory_authority) is not InitialFactoryFoundationAuthority
            or not isinstance(graph, dict)):
        invalid("BAMF_INITIAL_GENERATION_SOURCE_AUTHORITY_INVALID")
    authority = replay_initial_factory_foundation_authority(factory_authority, graph)
    if ((release is not None and release != authority.release)
            or (admission is not None and admission != authority.admission)
            or (origin_checkpoint is not None
                and origin_checkpoint != authority.origin_checkpoint)):
        invalid("BAMF_INITIAL_GENERATION_SOURCE_AUTHORITY_DRIFT")
    return authority


def _factory_generation_provenance(
        release: ExecutableFactoryRelease,
        features: InitialFoundationFeatureAuthority) -> GenerationProvenance:
    """Bind Factory source/teacher identity to the admitted Atlas semantic release."""
    source = (release.source_bindings.source_attestation_sha256
              or release.source_bindings.digest())
    return GenerationProvenance(
        source, features.features.semantic_release,
        release.execution_plan.projection_digests.teaching, 0)


def _host_bound_frontier(correction_frontier: Mapping[str, object]) -> dict:
    from ..source_authority_custody import (
        HOST_SYSTEM_SOURCE_AUTHORITY_ORIGIN,
        read_host_system_source_authority_registry,
    )

    trusted = read_host_system_source_authority_registry()
    return {
        **dict(correction_frontier),
        "source_authority_registry": trusted.to_record(),
        "source_authority_registry_sha256": trusted.digest,
        "source_authority_registry_origin": HOST_SYSTEM_SOURCE_AUTHORITY_ORIGIN,
    }


def validate_initial_generation_source_authority(candidate: BamfBundleCandidate):
    """Narrow C09 replay for generation-zero publication and retry custody."""
    from ..source_authority_custody import (
        HOST_SYSTEM_SOURCE_AUTHORITY_ORIGIN,
        read_host_system_source_authority_registry,
    )

    correction = candidate.correction_frontier
    if (not isinstance(correction, Mapping)
            or correction.get("source_authority_registry_origin")
            != HOST_SYSTEM_SOURCE_AUTHORITY_ORIGIN):
        invalid("BAMF_C09_SOURCE_AUTHORITY_BINDING_REQUIRED")
    trusted = read_host_system_source_authority_registry()
    if (correction.get("source_authority_registry") != trusted.to_record()
            or correction.get("source_authority_registry_sha256") != trusted.digest):
        invalid("BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_MISMATCH")
    return trusted


def _validate_candidate_source_authority(
        candidate: BamfBundleCandidate, *, release: ExecutableFactoryRelease,
        admission: ExecutableAdmissionReceipt, graph: dict,
        origin_checkpoint: Checkpoint,
        factory_authority: InitialFactoryFoundationAuthority | None = None,
        foundation_features: InitialFoundationFeatureAuthority | None = None) -> None:
    """Re-prove Factory/source/teacher authority for a generation-zero candidate."""
    authority = _validated_factory_origin(
        factory_authority, graph, release=release, admission=admission,
        origin_checkpoint=origin_checkpoint)
    release = authority.release
    admission = authority.admission
    origin_checkpoint = authority.origin_checkpoint
    if type(foundation_features) is not InitialFoundationFeatureAuthority:
        invalid("BAMF_INITIAL_GENERATION_SOURCE_AUTHORITY_INVALID")
    identity = candidate.run_identity
    if type(identity) is not BamfRunIdentity:
        invalid("BAMF_INITIAL_GENERATION_SOURCE_AUTHORITY_DRIFT")
    expected = _factory_generation_provenance(release, foundation_features)
    expected_sidecars = list(initial_foundation_sidecars(
        release, admission, graph, run_seed=identity.run_seed,
        feature_authority=foundation_features))
    expected_sidecars[2] = _host_bound_frontier(expected_sidecars[2])
    expected_sidecars = tuple(expected_sidecars)
    teacher = candidate.teacher_state
    correction = candidate.correction_frontier
    if (candidate.generation != 0 or candidate.parent_manifest_sha256 is not None
            or candidate.provenance != expected
            or tuple(dict(value) for value in (
                candidate.semantic_abi, candidate.compiler_features,
                candidate.correction_frontier, candidate.teacher_state,
                candidate.evaluation_contract)) != expected_sidecars
            or not isinstance(teacher, Mapping)
            or teacher.get("teacher_identity") != expected.teacher_identity
            or teacher.get("teacher_epoch") != expected.teacher_epoch
            or not isinstance(correction, Mapping)
            or correction.get("source_identity") != expected.source_identity
            or correction.get("release_digest") != expected.release_digest
            or identity.run_id != candidate.run_id
            or identity.origin_checkpoint_sha256 != origin_checkpoint.sha256
            or identity.origin_checkpoint_filename != origin_checkpoint.filename
            or identity.origin_optimizer_step != origin_checkpoint.optimizer_step
            or identity.factory_release_sha256 != release.release_sha256
            or identity.semantic_graph_sha256 != admission.semantic_graph_sha256
            or identity.initial_candidate_identity_sha256
            != candidate_identity_digest(candidate.retained_state)
            or identity.initial_topology_digest != candidate.topology.digest
            or identity.initial_extents_digest != candidate.extents.digest
            or identity.initial_implementation_sha256 != candidate.implementation_sha256
            or identity.initial_source_identity != expected.source_identity
            or identity.initial_release_digest != expected.release_digest
            or identity.initial_teacher_identity != expected.teacher_identity
            or identity.initial_teacher_epoch != expected.teacher_epoch):
        invalid("BAMF_INITIAL_GENERATION_SOURCE_AUTHORITY_DRIFT")


def _issue_binding(
        candidate: BamfBundleCandidate, *, release: ExecutableFactoryRelease,
        admission: ExecutableAdmissionReceipt, graph: dict,
        origin_checkpoint: Checkpoint,
        factory_authority: InitialFactoryFoundationAuthority | None = None,
        foundation_features: InitialFoundationFeatureAuthority | None = None,
        ) -> InitialGenerationBinding:
    _validate_candidate_source_authority(
        candidate, release=release, admission=admission, graph=graph,
        origin_checkpoint=origin_checkpoint,
        factory_authority=factory_authority,
        foundation_features=foundation_features)
    _validate_candidate_b01_authority(candidate, foundation_features)
    return _mint_initial_generation_binding(candidate)


def _validate_candidate_b01_authority(
        candidate: BamfBundleCandidate,
        foundation_features: InitialFoundationFeatureAuthority) -> None:
    """Rebuild generation-zero B01 geometry and seeded numerical state."""
    if (type(candidate) is not BamfBundleCandidate
            or type(candidate.run_identity) is not BamfRunIdentity
            or type(candidate.topology) is not ModelTopologySpecV2
            or candidate.generation != 0):
        invalid("BAMF_INITIAL_GENERATION_MODEL_AUTHORITY_DRIFT")
    try:
        allocations = MotifAllocationSnapshot(
            MotifManifest(candidate.provenance.release_digest))
        extents = b01_generation_extents(
            semantic_abi=candidate.semantic_abi,
            compiler_features=candidate.compiler_features,
            motif_page_count=allocations.manifest.capacity // INITIAL_MOTIF_CAPACITY,
            motif_key_map_digest=allocations.manifest.digest)
        authority = b01_generation_authority(extents)
        topology, implementation_sha256 = validate_b01_generation_authority(
            authority, extents)
        optimizer, _decay, _initialization = _create_unbound_bamf_optimizer(
            topology, extents, run_seed=candidate.run_identity.run_seed)
        expected_policy = PlasticityPolicy(
            "FOUNDATION", 0, initial_foundation_row_ages(
                foundation_features))
        expected_state = CandidateState(
            optimizer, expected_policy, allocations, 0,
            identity_scheme=candidate.retained_state.identity_scheme)
    except (TypeError, ValueError, KeyError, AttributeError):
        invalid("BAMF_INITIAL_GENERATION_MODEL_AUTHORITY_DRIFT")
    if (candidate.topology.digest != authority.parameter_census.topology_digest
            or candidate.extents != extents
            or candidate.extents.digest != authority.parameter_census.extents_digest
            or candidate.implementation_sha256 != implementation_sha256
            or candidate.retained_state.policy != expected_policy
            or candidate.retained_state.allocations != allocations
            or candidate.retained_state.optimizer_step != 0
            or candidate.retained_state.custody is not None
            or candidate.retained_state.step_proofs != ()
            or candidate_identity_digest(candidate.retained_state)
            != candidate_identity_digest(expected_state)):
        invalid("BAMF_INITIAL_GENERATION_MODEL_AUTHORITY_DRIFT")
