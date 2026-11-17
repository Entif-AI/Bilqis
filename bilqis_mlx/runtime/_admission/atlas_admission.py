"""C07 lease contracts plus fixture and accepted-run persistence boundaries.

The historical ``DISPOSABLE_CONTRACT`` shape remains non-authoritative. Production
lease persistence independently replays accepted B13 birth identity before that
shape may be attached to a saved run.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from ..semantics.domains import contract_digest
from .atlas_lease_contracts import (
    AtlasAdmissionLease, AtlasAdmissionLeaseV2, AtlasSourceApproval,
    DeltaBudgetPolicy, LeaseRunIdentity, ResourceCeiling, ResourceCeilingV2,
    _invalid, _sha, _name, _names,
)
from .atlas_lease_storage import (
    _atlas_authority_epoch_lock, _atlas_lease_lock, classify_accepted_atlas_epoch,
    _lease_from_json, _persist_atlas_lease_locked, _read_atlas_lease, _store,
)
from .state import _durable_json


from .atlas_adoption_v2 import (
    adopt_capability_only_atlas_successor_v2,
    adopt_parameter_extension_atlas_successor_v2,
)
from .atlas_admission_requests import (
    add_atlas_admission_arguments,
    advance_atlas_frontier,
    advance_atlas_frontier_v2,
    dispatch_atlas_frontier_proposal,
    issue_atlas_lease,
    persist_atlas_lease,
    read_atlas_lease,
    read_atlas_lease_request,
    stage_unleased_atlas_proposal,
    validate_atlas_command_request,
    validate_atlas_lease_request,
)


def _accepted_run_lease_identity(run_dir):
    """Re-derive the lease comparison identity from live accepted B13 custody."""
    from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
    from .jit_adoption import _accepted_lease_run_identity

    student, _manifest_sha256 = load_bamf_generation_authority(
        Path(run_dir) / 'bamf-state.json')
    if student.run_identity is None:
        _invalid('BAMF_ATLAS_ACCEPTED_RUN_IDENTITY_REQUIRED')
    return _accepted_lease_run_identity(student.run_identity)


def _accepted_source_registry(run_dir, source_authority):
    """Resolve source verification only through one accepted-run C09 capability."""
    from bilqis_mlx.runtime.atlas_source_authority import (
        SourceAuthorityRuntime, require_source_authority_runtime,
    )
    if type(source_authority) is not SourceAuthorityRuntime:
        _invalid('BAMF_C09_SOURCE_AUTHORITY_RUNTIME_INVALID')
    from bilqis_mlx.runtime.bamf_bundle.admission import (
        bind_accepted_execution_cache,
    )
    cache = bind_accepted_execution_cache(Path(run_dir))
    require_source_authority_runtime(source_authority, cache)
    return cache._correction_registry


def persist_accepted_atlas_lease(run_dir, lease, *, source_authority):
    """Persist a human lease only after independent accepted-run identity replay."""
    expected = _accepted_run_lease_identity(run_dir)
    if not isinstance(lease, AtlasAdmissionLease) or lease.run_identity != expected:
        _invalid('BAMF_ATLAS_LEASE_RUN_IDENTITY_DRIFT')
    registry = _accepted_source_registry(run_dir, source_authority)
    with _atlas_authority_epoch_lock(run_dir):
        epoch = classify_accepted_atlas_epoch(Path(run_dir))
        if epoch == 'v2':
            _invalid('BAMF_ATLAS_V1_SUCCESSOR_AUTHORITY_PRESENT')
        with _atlas_lease_lock(run_dir, fixture_authority=False):
            return _persist_atlas_lease_locked(
                run_dir, lease, independently_loaded_run=expected, registry=registry,
                fixture_authority=False)


def read_accepted_atlas_lease(run_dir, *, source_authority):
    """Read the current production lease only through accepted B13 run identity."""
    expected = _accepted_run_lease_identity(run_dir)
    registry = _accepted_source_registry(run_dir, source_authority)
    return _read_atlas_lease(
        run_dir, expected, registry=registry, fixture_authority=False)


def read_accepted_atlas_factory_release(run_dir):
    """Resolve current Factory authority only through accepted B13 lineage.

    Generation zero binds the founding Factory release in ``BamfRunIdentity``.
    A C07 generation binds its successor in its generation-specific admission
    family: ``AtlasAdmissionBinding`` for parameter extension or
    ``FactoryReleaseAdmissionBinding`` for neural-inert Factory adoption.
    Ordinary retained generations inherit the nearest accepted ancestor's Factory
    authority through the acceptance-bound parent chain; they never reintroduce
    the legacy operator receipt as a second current-Factory authority.
    """
    from bilqis_mlx.runtime.bamf_bundle.atlas_admission import (
        ParsedAtlasAdmissionBinding,
    )
    from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
        ParsedFactoryReleaseAdmissionBinding,
    )
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest, accepted_generation,
        parent_acceptance_anchor_from_manifest,
    )
    from bilqis_mlx.runtime.bamf_bundle.genesis import (
        BamfRunIdentity, ParsedInitialGenerationBinding,
    )
    from . import admission as factory_admission

    root = Path(run_dir)
    pointer, student = accepted_generation(root / "bamf-state.json")
    manifest_sha256 = pointer["manifest_sha256"]
    acceptance_sha256 = pointer["acceptance_sha256"]
    visited = set()
    while True:
        if manifest_sha256 in visited:
            _invalid("BAMF_ATLAS_ACCEPTED_FACTORY_BINDING_REQUIRED")
        visited.add(manifest_sha256)
        binding = accepted_binding_for_manifest(
            root, manifest_sha256, student,
            expected_acceptance_sha256=acceptance_sha256)
        if isinstance(binding, (
                ParsedAtlasAdmissionBinding,
                ParsedFactoryReleaseAdmissionBinding)):
            digest = binding.factory_release_sha256
            break
        if student.generation == 0:
            identity = student.run_identity
            if (type(binding) is not ParsedInitialGenerationBinding
                    or type(identity) is not BamfRunIdentity):
                _invalid("BAMF_ATLAS_ACCEPTED_FACTORY_BINDING_REQUIRED")
            digest = identity.factory_release_sha256
            break
        parent_manifest_sha256 = student.parent_manifest_sha256
        parent_acceptance_sha256 = parent_acceptance_anchor_from_manifest(
            root, manifest_sha256)
        if (not _sha(parent_manifest_sha256)
                or not _sha(parent_acceptance_sha256)):
            _invalid("BAMF_ATLAS_ACCEPTED_FACTORY_BINDING_REQUIRED")
        student = load_bamf_bundle(
            root / "bamf-bundles" / parent_manifest_sha256,
            expected_manifest_sha256=parent_manifest_sha256)
        manifest_sha256 = parent_manifest_sha256
        acceptance_sha256 = parent_acceptance_sha256
    return factory_admission._read_executable_factory_release_artifact(root, {
        "factory_release_sha256": digest,
        "factory_release_file": "factory-releases/" + digest + ".json",
    })


def _accepted_atlas_obligation_state(run_dir):
    """Recover cumulative accepted obligation identity through B13 ancestry."""
    from bilqis_mlx.runtime.bamf_bundle.atlas_admission import (
        ATLAS_ADMISSION_SCHEMA_V2, ATLAS_ADMISSION_SCHEMA_V3,
        ParsedAtlasAdmissionBinding,
    )
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
        FACTORY_RELEASE_ADMISSION_SCHEMA_V2,
        FACTORY_RELEASE_ADMISSION_SCHEMA_V3,
        FACTORY_RELEASE_ADMISSION_SCHEMA_V4,
        ParsedFactoryReleaseAdmissionBinding,
    )
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest, accepted_generation,
        parent_acceptance_anchor_from_manifest,
    )

    root = Path(run_dir)
    pointer, student = accepted_generation(root / "bamf-state.json")
    current_acceptance = pointer["acceptance_sha256"]
    current_release = read_accepted_atlas_factory_release(root)
    manifest_sha256 = pointer["manifest_sha256"]
    acceptance_sha256 = current_acceptance
    visited = set()
    while student.generation > 0:
        if manifest_sha256 in visited:
            _invalid("BAMF_ATLAS_ACCEPTED_OBLIGATION_BINDING_REQUIRED")
        visited.add(manifest_sha256)
        binding = accepted_binding_for_manifest(
            root, manifest_sha256, student,
            expected_acceptance_sha256=acceptance_sha256)
        if (isinstance(binding, ParsedAtlasAdmissionBinding)
                and binding.schema_version in {
                    ATLAS_ADMISSION_SCHEMA_V2, ATLAS_ADMISSION_SCHEMA_V3}):
            return (
                current_release.release_sha256,
                current_acceptance,
                binding.selected_obligation_keys,
            )
        if (isinstance(binding, ParsedFactoryReleaseAdmissionBinding)
                and binding.schema_version in {
                    FACTORY_RELEASE_ADMISSION_SCHEMA_V2,
                    FACTORY_RELEASE_ADMISSION_SCHEMA_V3,
                    FACTORY_RELEASE_ADMISSION_SCHEMA_V4}):
            return (
                current_release.release_sha256,
                current_acceptance,
                binding.accepted_obligation_keys,
            )
        parent_manifest = student.parent_manifest_sha256
        parent_acceptance = parent_acceptance_anchor_from_manifest(
            root, manifest_sha256)
        if not _sha(parent_manifest) or not _sha(parent_acceptance):
            _invalid("BAMF_ATLAS_ACCEPTED_OBLIGATION_BINDING_REQUIRED")
        student = load_bamf_bundle(
            root / "bamf-bundles" / parent_manifest,
            expected_manifest_sha256=parent_manifest)
        manifest_sha256 = parent_manifest
        acceptance_sha256 = parent_acceptance
    return current_release.release_sha256, current_acceptance, ()


def read_accepted_atlas_obligation_credit(run_dir):
    """Mint ephemeral planner credit only from authenticated accepted B13 custody."""
    from bilqis_mlx.factory.atlas_delta_adapter import (
        _issue_accepted_obligation_credit,
    )

    release_sha256, acceptance_sha256, obligation_keys = (
        _accepted_atlas_obligation_state(run_dir))
    if not obligation_keys:
        return None
    return _issue_accepted_obligation_credit(
        release_sha256, acceptance_sha256, obligation_keys)


def renew_atlas_lease(run_dir, lease, *, independently_loaded_run, registry,
                      expected_prior_lease_sha256, human_started):
    """Renew disposable scope explicitly; caller assertions do not prove human identity."""
    if (human_started is not True or not _sha(expected_prior_lease_sha256)
            or not isinstance(lease, AtlasAdmissionLease)
            or lease.run_identity != independently_loaded_run):
        _invalid('BAMF_ATLAS_LEASE_RENEWAL_ARGUMENT_INVALID')
    lease.source_approval.verify(registry)
    from bilqis_mlx.runtime._coordination import run_root_claim
    with run_root_claim(Path(run_dir), create_parent=False), _atlas_lease_lock(run_dir):
        directory = _store(run_dir)
        prior = _read_atlas_lease(run_dir, independently_loaded_run,
                                  registry=registry, current_authority=False)
        edge = {'schema': 'bilqis.c07.lease-renewal/v1',
                'prior_lease_sha256': expected_prior_lease_sha256,
                'replacement_lease_sha256': lease.digest(),
                'human_command_sha256': lease.human_command_sha256}
        edges = directory / 'renewals'
        if edges.is_symlink() or (edges.exists() and not edges.is_dir()):
            _invalid('BAMF_ATLAS_LEASE_UNSAFE_PATH')
        edge_path = edges / (lease.digest() + '.json')
        if edge_path.is_symlink():
            _invalid('BAMF_ATLAS_LEASE_UNSAFE_PATH')
        if prior == lease:
            if not edge_path.is_file() or json.loads(edge_path.read_text()) != edge:
                _invalid('BAMF_ATLAS_LEASE_RENEWAL_PREDECESSOR_DRIFT')
            return directory / 'current.json'
        if (prior is None or prior.digest() != expected_prior_lease_sha256
                or prior.lease_id == lease.lease_id
                or prior.human_command_sha256 == lease.human_command_sha256
                or lease.requested_at <= prior.requested_at):
            _invalid('BAMF_ATLAS_LEASE_RENEWAL_PREDECESSOR_DRIFT')
        relative = 'autonomy/atlas-admission/leases/' + lease.digest() + '.json'
        path = Path(run_dir) / relative
        for artifact, payload in ((path, asdict(lease)), (edge_path, edge)):
            if artifact.is_symlink():
                _invalid('BAMF_ATLAS_LEASE_UNSAFE_PATH')
            if artifact.exists():
                if json.loads(artifact.read_text()) != json.loads(json.dumps(payload)):
                    _invalid('BAMF_ATLAS_LEASE_IMMUTABLE_DRIFT')
            else:
                _durable_json(artifact, payload)
        reference = directory / 'current.json'
        _durable_json(reference, {'schema': 'bilqis.c07.atlas-lease-reference/v1',
            'run_identity_digest': contract_digest(independently_loaded_run),
            'lease_sha256': lease.digest(), 'lease_file': relative}, replace_existing=True)
        if read_atlas_lease(run_dir, independently_loaded_run, registry=registry) != lease:
            _invalid('BAMF_ATLAS_LEASE_READBACK_DRIFT')
        return reference


# V2 is deliberately a separate human-authority epoch.  Re-export its public
# entrypoints here without changing the v1 storage or policy contracts above.
from .atlas_lease_v2 import (
    _hold_current_atlas_lease_v2_publication,
    issue_atlas_lease_v2,
    persist_accepted_atlas_lease_v2,
    persist_atlas_lease_v2,
    read_accepted_atlas_lease_v2,
    read_atlas_lease_v2,
    renew_atlas_lease_v2,
)
from .atlas_enrollment_v2 import (
    AtlasAdmissionEnrollmentRequestV2,
    enroll_accepted_atlas_lease_v2,
    read_atlas_enrollment_request_v2,
)
