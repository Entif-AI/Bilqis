"""Explicit, neural-inert profile adoption through accepted native B13 custody."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from bilqis_mlx.factory.executable_release import ExecutableFactoryRelease
from bilqis_mlx.factory.profile_expansion import verify_profile_expansion
from bilqis_mlx.runtime.atlas_lease_contracts import _invalid
from bilqis_mlx.semantics.domains import contract_digest


def read_profile_release(value):
    """Read a compiled artifact; file location never supplies admission authority."""
    if isinstance(value, ExecutableFactoryRelease):
        value.verify()
        return value
    path = Path(value)
    if path.is_symlink() or not path.is_file():
        _invalid('BAMF_PROFILE_RELEASE_ARTIFACT_INVALID')
    payload = json.loads(path.read_text(encoding='utf-8'))
    # Factory manifests are the same content-addressed payload used by admission.
    if 'factory_release_sha256' in payload:
        digest = payload.pop('factory_release_sha256')
        return ExecutableFactoryRelease.from_manifest(payload, digest)
    if 'release_sha256' in payload and 'manifest' in payload:
        return ExecutableFactoryRelease.from_manifest(payload['manifest'], payload['release_sha256'])
    return ExecutableFactoryRelease.from_manifest(payload, contract_digest(payload))


@dataclass(frozen=True)
class _ProfileContext:
    pointer: dict
    parent: object
    predecessor: object
    successor: object
    lease: object
    proof: object | None
    active_grade_sha256: str | None


def _context(run_dir, successor):
    from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
    from bilqis_mlx.runtime.atlas_admission import (
        read_accepted_atlas_factory_release, read_accepted_atlas_lease_v2,
    )
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import accepted_generation
    from bilqis_mlx.runtime.bamf_bundle import (
        load_bamf_generation_authority, read_accepted_generation_feature_context,
    )
    from bilqis_mlx.runtime.jit_adoption import verify_current_implementations
    from bilqis_mlx.factory.live_answers import live_answer_registry
    from bilqis_mlx.source_adapters.school import live_source_registry

    parent, manifest = load_bamf_generation_authority(run_dir / 'bamf-state.json')
    pointer, _ = accepted_generation(run_dir / 'bamf-state.json')
    if pointer['manifest_sha256'] != manifest:
        _invalid('BAMF_PROFILE_ACCEPTED_PARENT_CHANGED')
    host = AcceptedRuntimeHost(run_dir)
    lease = read_accepted_atlas_lease_v2(run_dir, source_authority=host.source_authority())
    if lease is None:
        _invalid('BAMF_PROFILE_CURRENT_LEASE_REQUIRED')
    approval = lease.source_approval
    feature = read_accepted_generation_feature_context(run_dir / 'bamf-state.json')
    if (not approval.audit_passed or not approval.rights_compatible
            or approval.atlas_release_sha256 != feature.receipt.source_release_sha256
            or approval.atlas_release_sha256 != feature.features.semantic_release):
        _invalid('BAMF_PROFILE_SOURCE_AUTHORITY_DRIFT')
    predecessor = read_accepted_atlas_factory_release(run_dir)
    graph = parent.compiler_features.get('factory_semantic_catalog', {})
    successor.verify_semantic_catalog(graph)
    answers = live_answer_registry()
    verify_current_implementations(successor, live_source_registry(), answers)
    from bilqis_mlx.factory._executable_release.evidence import _answer_head_bindings
    if successor.answer_heads != _answer_head_bindings(successor.execution_plan, graph, answers):
        _invalid('BAMF_PROFILE_ANSWER_HEAD_DRIFT')
    if successor.release_sha256 == predecessor.release_sha256:
        _verify_exact_retry(run_dir, pointer, parent, successor, lease)
        return _ProfileContext(pointer, parent, predecessor, successor, lease, None, None)
    proof = verify_profile_expansion(predecessor, successor)
    if len(proof.added_capabilities) > approval.delta_budget_policy.max_capabilities:
        _invalid('BAMF_PROFILE_DELTA_BUDGET_EXCEEDED')
    active_digest = None
    if proof.added_capabilities:
        from bilqis_mlx.runtime.active_generated_grade import read_active_generated_grade
        active = read_active_generated_grade(run_dir, repair=False)
        if active is None:
            _invalid('BAMF_PROFILE_ACTIVE_GRADE_REQUIRED')
        enabled = successor.execution_plan.capability_map
        if any(member.capability_id not in enabled for member in active.definition.members):
            _invalid('BAMF_PROFILE_ACTIVE_GRADE_MEMBERSHIP_DRIFT')
        active_digest = active.activation_sha256
    return _ProfileContext(pointer, parent, predecessor, successor, lease, proof, active_digest)


def _verify_exact_retry(run_dir, pointer, parent, successor, lease):
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import accepted_binding_for_manifest
    from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
        FACTORY_RELEASE_ADMISSION_SCHEMA_V4, ParsedFactoryReleaseAdmissionBinding,
    )
    from bilqis_mlx.runtime.admission import _read_executable_factory_release_artifact
    binding = accepted_binding_for_manifest(
        run_dir, pointer['manifest_sha256'], parent,
        expected_acceptance_sha256=pointer['acceptance_sha256'])
    if (not isinstance(binding, ParsedFactoryReleaseAdmissionBinding)
            or binding.schema_version != FACTORY_RELEASE_ADMISSION_SCHEMA_V4
            or binding.factory_release_sha256 != successor.release_sha256
            or binding.lease_sha256 != lease.digest()
            or binding.source_approval_sha256 != contract_digest(lease.source_approval)
            or binding.parent_manifest_sha256 != parent.parent_manifest_sha256):
        _invalid('BAMF_PROFILE_RETRY_AUTHORITY_DRIFT')
    digest = binding.predecessor_factory_release_sha256
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import parent_acceptance_anchor_from_manifest
    from bilqis_mlx.runtime.atlas_capability_adoption_v2 import _historical_factory_release_sha256
    prior_manifest = binding.parent_manifest_sha256
    prior_acceptance = parent_acceptance_anchor_from_manifest(run_dir, pointer['manifest_sha256'])
    prior_student = load_bamf_bundle(
        run_dir / 'bamf-bundles' / prior_manifest, expected_manifest_sha256=prior_manifest)
    if _historical_factory_release_sha256(
            run_dir, prior_manifest, prior_acceptance, prior_student) != digest:
        _invalid('BAMF_PROFILE_RETRY_AUTHORITY_DRIFT')
    previous = _read_executable_factory_release_artifact(run_dir, {
        'factory_release_sha256': digest,
        'factory_release_file': f'factory-releases/{digest}.json',
    })
    proof = verify_profile_expansion(previous, successor)
    if (proof.profile_sha256 != binding.profile_sha256
            or proof.transition_sha256 != binding.profile_transition_sha256):
        _invalid('BAMF_PROFILE_RETRY_AUTHORITY_DRIFT')


def preview_profile_release(run_dir, successor):
    """Validate an explicit successor without publishing a generation."""
    context = _context(Path(run_dir), read_profile_release(successor))
    return {
        'factory_profile_release_sha256': context.successor.release_sha256,
        'previous_factory_release_sha256': context.predecessor.release_sha256,
        'profile_id': context.successor.profile.profile_id,
        'added_capabilities': (() if context.proof is None else context.proof.added_capabilities),
        'actual_neural_updates': 0,
    }


def adopt_profile_release(run_dir, successor, *, reserve_gib=100.0):
    """Adopt the exact requested artifact; caller owns the sovereign operator lock."""
    from bilqis_mlx.runtime.atlas_admission import (
        _hold_current_atlas_lease_v2_publication,
        read_accepted_atlas_factory_release, read_accepted_atlas_obligation_credit,
    )
    from bilqis_mlx.runtime.bamf_bundle.factory_release_adoption import (
        _issue_profile_expansion_transition, derive_factory_release_adoption_candidate,
    )
    from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
        _issue_factory_release_admission_binding,
    )
    from bilqis_mlx.runtime.bamf_bundle.publication import publish_factory_release_adoption_generation
    from bilqis_mlx.runtime.admission import _persist_executable_factory_release

    root = Path(run_dir)
    release = read_profile_release(successor)
    initial = _context(root, release)
    with _hold_current_atlas_lease_v2_publication(root, initial.lease):
        context = _context(root, release)
        if context.lease != initial.lease or context.pointer != initial.pointer:
            _invalid('BAMF_PROFILE_ACCEPTED_PARENT_CHANGED')
        if context.proof is None:
            return context.pointer
        transition = _issue_profile_expansion_transition(
            predecessor_factory_release_sha256=context.predecessor.release_sha256,
            factory_release_sha256=release.release_sha256,
            profile_sha256=context.proof.profile_sha256,
            parent_manifest_sha256=context.pointer['manifest_sha256'],
            lease_sha256=context.lease.digest(),
            source_approval_sha256=contract_digest(context.lease.source_approval),
            profile_transition_sha256=context.proof.transition_sha256)
        candidate = derive_factory_release_adoption_candidate(
            context.parent, parent_manifest_sha256=context.pointer['manifest_sha256'],
            transition=transition)
        inherited = read_accepted_atlas_obligation_credit(root)
        binding = _issue_factory_release_admission_binding(
            candidate, context.parent, transition=transition,
            accepted_obligation_keys=(() if inherited is None else inherited.obligation_keys))
        _persist_executable_factory_release(root, release)
        pointer = publish_factory_release_adoption_generation(
            root, candidate, admission=binding, reserve_gib=reserve_gib,
            expected_active_grade_activation_sha256=context.active_grade_sha256)
        if read_accepted_atlas_factory_release(root).release_sha256 != release.release_sha256:
            _invalid('BAMF_PROFILE_ACCEPTED_RELEASE_DRIFT')
        return pointer
