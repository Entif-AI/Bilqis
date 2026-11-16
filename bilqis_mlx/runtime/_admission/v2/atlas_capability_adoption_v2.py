"""C07 v2 mutation helpers for neural-inert Factory release adoption."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.runtime.atlas_admission_policy_v2 import _require_exact_atlas_release
from bilqis_mlx.runtime.atlas_lease_contracts import _invalid, _sha
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.jit_adoption import (
    _PreparedSuccessorRuntime,
    verify_current_implementations,
)


def _historical_factory_release_sha256(
        run_dir: Path, manifest_sha256: str, acceptance_sha256: str, student) -> str:
    """Resolve Factory authority for an accepted historical manifest."""
    from bilqis_mlx.runtime.bamf_bundle.atlas_admission import ParsedAtlasAdmissionBinding
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
        ParsedFactoryReleaseAdmissionBinding,
    )
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest,
        parent_acceptance_anchor_from_manifest,
    )
    from bilqis_mlx.runtime.bamf_bundle.genesis import (
        BamfRunIdentity,
        ParsedInitialGenerationBinding,
    )

    visited = set()
    while True:
        if manifest_sha256 in visited:
            _invalid("BAMF_ATLAS_ACCEPTED_FACTORY_BINDING_REQUIRED")
        visited.add(manifest_sha256)
        binding = accepted_binding_for_manifest(
            run_dir, manifest_sha256, student,
            expected_acceptance_sha256=acceptance_sha256)
        if isinstance(binding, (
                ParsedAtlasAdmissionBinding,
                ParsedFactoryReleaseAdmissionBinding)):
            return binding.factory_release_sha256
        if student.generation == 0:
            if (type(binding) is not ParsedInitialGenerationBinding
                    or type(student.run_identity) is not BamfRunIdentity):
                _invalid("BAMF_ATLAS_ACCEPTED_FACTORY_BINDING_REQUIRED")
            return student.run_identity.factory_release_sha256
        parent_manifest = student.parent_manifest_sha256
        parent_acceptance = parent_acceptance_anchor_from_manifest(
            run_dir, manifest_sha256)
        if not _sha(parent_manifest) or not _sha(parent_acceptance):
            _invalid("BAMF_ATLAS_ACCEPTED_FACTORY_BINDING_REQUIRED")
        student = load_bamf_bundle(
            run_dir / "bamf-bundles" / parent_manifest,
            expected_manifest_sha256=parent_manifest)
        manifest_sha256 = parent_manifest
        acceptance_sha256 = parent_acceptance


def _generated_grade_digest(authority, handoff):
    if authority is None:
        return None
    from bilqis_mlx.runtime.generated_grade import (
        _require_generated_grade_authority,
    )
    authority = _require_generated_grade_authority(authority)
    if (
        authority.predecessor_factory_release_sha256
        != handoff.receipt.predecessor_release.release_sha256
        or authority.a09_proposal_sha256 != handoff.proposal.proposal_sha256
    ):
        _invalid("BAMF_GENERATED_GRADE_ACCEPTED_AUTHORITY_DRIFT")
    return authority.proposal_sha256


def _accepted_capability_only_retry_state_once_v2(
        current, handoff, lease, *, generated_grade_authority=None):
    """Return an exact retry or the exact accepted predecessor pointer."""
    from bilqis_mlx.runtime.atlas_flywheel_runtime_context import (
        atlas_admission_checkpoint,
    )
    from bilqis_mlx.runtime.atlas_admission import (
        _accepted_run_lease_identity,
        read_accepted_atlas_factory_release,
        read_accepted_atlas_lease_v2,
    )
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
        FACTORY_RELEASE_ADMISSION_SCHEMA_V2,
        FACTORY_RELEASE_ADMISSION_SCHEMA_V3,
        ParsedFactoryReleaseAdmissionBinding,
    )
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest,
        accepted_generation,
        parent_acceptance_anchor_from_manifest,
    )
    from bilqis_mlx.semantics.domains import contract_digest
    from bilqis_mlx.factory.atlas_frontier_progress_validation import requested_keys

    pointer, accepted = accepted_generation(current.run_dir / "bamf-state.json")
    accepted_release = read_accepted_atlas_factory_release(current.run_dir)
    predecessor = handoff.receipt.predecessor_release.release_sha256
    successor = handoff.staged_candidate.successor.release_sha256
    source_authority = current.source_authority
    if accepted_release.release_sha256 == successor:
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        source_authority = AcceptedRuntimeHost(Path(current.run_dir)).source_authority()
    persisted = read_accepted_atlas_lease_v2(
        current.run_dir, source_authority=source_authority)
    if persisted is None or persisted != lease:
        _invalid("BAMF_ATLAS_V2_LEASE_CURRENT_AUTHORITY_DRIFT")
    lease.source_approval.verify_signature(current.legacy.registry)
    _require_exact_atlas_release(current, handoff, lease)
    if accepted_release.release_sha256 == predecessor:
        accepted_identity = _accepted_run_lease_identity(current.run_dir)
        runtime_checkpoint = atlas_admission_checkpoint(
            current.runtime, accepted_release)
        if (accepted_identity != current.legacy.run_identity
                or current.legacy.current_release.release_sha256 != predecessor
                or handoff.proposal.current_release_sha256 != predecessor
                or accepted.retained_state.optimizer_step
                != current.legacy.checkpoint.optimizer_step
                or runtime_checkpoint != current.legacy.checkpoint):
            _invalid("BAMF_ATLAS_V2_CAPABILITY_RETRY_CONFLICT")
        return None, dict(pointer)
    if accepted_release.release_sha256 != successor:
        _invalid("BAMF_ATLAS_V2_CAPABILITY_RETRY_CONFLICT")
    expected_generated_grade = _generated_grade_digest(
        generated_grade_authority, handoff)
    binding = accepted_binding_for_manifest(
        current.run_dir, pointer["manifest_sha256"], accepted,
        expected_acceptance_sha256=pointer["acceptance_sha256"])
    transition = dict(accepted.transition)
    if (not isinstance(binding, ParsedFactoryReleaseAdmissionBinding)
            or binding.run_id != accepted.run_id
            or binding.handoff_sha256 != handoff.handoff_sha256
            or binding.proposal_sha256 != handoff.proposal.proposal_sha256
            or binding.selection_receipt_sha256 != handoff.receipt.receipt_sha256
            or binding.lease_sha256 != lease.digest()
            or binding.source_approval_sha256 != contract_digest(lease.source_approval)
            or binding.predecessor_factory_release_sha256 != predecessor
            or binding.factory_release_sha256 != successor
            or transition.get("staged_candidate_sha256")
               != handoff.staged_candidate.staged_sha256
            or accepted.retained_state.optimizer_step
               != current.legacy.checkpoint.optimizer_step):
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT")
    if (binding.schema_version in {
            FACTORY_RELEASE_ADMISSION_SCHEMA_V2,
            FACTORY_RELEASE_ADMISSION_SCHEMA_V3}
            and not set(requested_keys((handoff.receipt,))).issubset(
                binding.accepted_obligation_keys)):
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT")
    if expected_generated_grade is not None and (
            binding.schema_version != FACTORY_RELEASE_ADMISSION_SCHEMA_V3
            or binding.generated_grade_proposal_sha256
               != expected_generated_grade):
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT")
    parent_manifest = accepted.parent_manifest_sha256
    parent_acceptance = parent_acceptance_anchor_from_manifest(
        current.run_dir, pointer["manifest_sha256"])
    if not _sha(parent_manifest) or not _sha(parent_acceptance):
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT")
    parent = load_bamf_bundle(
        current.run_dir / "bamf-bundles" / parent_manifest,
        expected_manifest_sha256=parent_manifest)
    if _historical_factory_release_sha256(
            current.run_dir, parent_manifest, parent_acceptance, parent) != predecessor:
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT")
    return pointer, None


def _accepted_capability_only_retry_state_v2(
        current, handoff, lease, *, generated_grade_authority=None):
    """Classify against one stable accepted-generation snapshot, retrying once."""
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import accepted_generation

    def identity(pointer):
        return (
            pointer["generation"],
            pointer["manifest_sha256"],
            pointer["acceptance_sha256"],
        )

    for attempt in range(2):
        before, _student = accepted_generation(current.run_dir / "bamf-state.json")
        try:
            if generated_grade_authority is None:
                result = _accepted_capability_only_retry_state_once_v2(
                    current, handoff, lease)
            else:
                result = _accepted_capability_only_retry_state_once_v2(
                    current, handoff, lease,
                    generated_grade_authority=generated_grade_authority)
        except BilqisError:
            after, _student = accepted_generation(current.run_dir / "bamf-state.json")
            if identity(after) == identity(before):
                raise
            if attempt == 1:
                _invalid("BAMF_ATLAS_V2_CAPABILITY_RETRY_CONFLICT")
            continue
        after, _student = accepted_generation(current.run_dir / "bamf-state.json")
        if identity(after) == identity(before):
            return result
        if attempt == 1:
            _invalid("BAMF_ATLAS_V2_CAPABILITY_RETRY_CONFLICT")

    _invalid("BAMF_ATLAS_V2_CAPABILITY_RETRY_CONFLICT")


def accepted_capability_only_retry_v2(
        current, handoff, lease, *, generated_grade_authority=None):
    """Authenticate an exact accepted Factory-only child before live verification."""
    retry, _parent_pointer = _accepted_capability_only_retry_state_v2(
        current, handoff, lease,
        generated_grade_authority=generated_grade_authority)
    return retry


def _revalidate_capability_publication(
        current, handoff, lease, runtime, source_authority, expected_parent_pointer,
        *, generated_grade_authority=None):
    from bilqis_mlx.runtime.atlas_admission import (
        read_accepted_atlas_factory_release,
        read_accepted_atlas_lease_v2,
    )
    persisted = read_accepted_atlas_lease_v2(
        runtime.run_dir, source_authority=source_authority)
    if persisted is None or persisted != lease:
        _invalid("BAMF_ATLAS_V2_LEASE_CURRENT_AUTHORITY_DRIFT")
    try:
        from bilqis_mlx.runtime.atlas_flywheel_runtime_context import (
            atlas_admission_checkpoint,
        )
        from bilqis_mlx.runtime.atlas_capability_facts_v2 import (
            read_capability_only_admission_facts_v2,
        )
        from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
        from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import accepted_generation
        from bilqis_mlx.factory.live_answers import live_answer_registry
        from bilqis_mlx.source_adapters.school import live_source_registry

        pointer, _accepted = accepted_generation(runtime.run_dir / "bamf-state.json")
        if pointer != expected_parent_pointer:
            _invalid("BAMF_ATLAS_RUNTIME_CONTEXT_CHANGED")
        parent, parent_manifest = load_bamf_generation_authority(
            runtime.run_dir / "bamf-state.json")
        lease.source_approval.verify_signature(current.legacy.registry)
        _require_exact_atlas_release(current, handoff, lease)
        accepted_current = read_accepted_atlas_factory_release(runtime.run_dir)
        runtime_checkpoint = atlas_admission_checkpoint(runtime, accepted_current)
        if (accepted_current.release_sha256
                != handoff.receipt.predecessor_release.release_sha256
                or parent.retained_state.optimizer_step
                   != current.legacy.checkpoint.optimizer_step
                or runtime_checkpoint != current.legacy.checkpoint):
            raced = accepted_capability_only_retry_v2(
                current, handoff, lease,
                generated_grade_authority=generated_grade_authority)
            if isinstance(raced, dict):
                return raced, None, None
            _invalid("BAMF_ATLAS_RUNTIME_CONTEXT_CHANGED")
        read_capability_only_admission_facts_v2(runtime.run_dir, handoff)
        verify_current_implementations(
            handoff.staged_candidate.successor,
            live_source_registry(), live_answer_registry())
    except BilqisError:
        raced = accepted_capability_only_retry_v2(
            current, handoff, lease,
            generated_grade_authority=generated_grade_authority)
        if isinstance(raced, dict):
            return raced, None, None
        raise
    except (ValueError, TypeError, AttributeError) as error:
        reason = {
            "JIT_ADOPTION_SOURCE_IMPLEMENTATION_DRIFT":
                "BAMF_ATLAS_SOURCE_IMPLEMENTATION_DRIFT",
            "JIT_ADOPTION_ANSWER_IMPLEMENTATION_DRIFT":
                "BAMF_ATLAS_ANSWER_IMPLEMENTATION_DRIFT",
        }.get(str(error), "BAMF_ATLAS_IMPLEMENTATION_REVALIDATION_FAILED")
        _invalid(reason)
    return None, parent, parent_manifest


def publish_capability_only_factory_successor(
        current, handoff, lease, *, expected_parent_pointer,
        generated_grade_authority=None):
    """Publish one verified zero-ID Factory successor without any A02 owner call."""
    from bilqis_mlx.runtime.atlas_admission import (
        _hold_current_atlas_lease_v2_publication,
    )
    with _hold_current_atlas_lease_v2_publication(current.run_dir, lease):
        return _publish_capability_only_factory_successor_locked(
            current, handoff, lease,
            expected_parent_pointer=expected_parent_pointer,
            generated_grade_authority=generated_grade_authority)


def _publish_capability_only_factory_successor_locked(
        current, handoff, lease, *, expected_parent_pointer,
        generated_grade_authority=None):
    """Publish while human v2 lease renewal is structurally excluded."""
    from . import admission as runtime_admission
    from bilqis_mlx.runtime.atlas_admission import (
        read_accepted_atlas_factory_release,
        read_accepted_atlas_obligation_credit,
    )
    from bilqis_mlx.runtime.bamf_bundle.factory_release_adoption import (
        _issue_factory_release_adoption_transition,
        derive_factory_release_adoption_candidate,
    )
    from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
        _issue_factory_release_admission_binding,
    )
    from bilqis_mlx.runtime.bamf_bundle.publication import (
        publish_factory_release_adoption_generation,
    )
    from bilqis_mlx.semantics.domains import contract_digest
    from bilqis_mlx.factory.atlas_frontier_progress_validation import requested_keys

    runtime = current.runtime
    source_authority = current.source_authority
    from bilqis_mlx.runtime.atlas_flywheel_runtime_context import (
        is_atlas_admission_runtime,
    )
    if not is_atlas_admission_runtime(runtime):
        _invalid("BAMF_ATLAS_V2_CAPABILITY_OWNER_UNAVAILABLE")
    refreshed, current_parent_pointer = _accepted_capability_only_retry_state_v2(
        current, handoff, lease,
        generated_grade_authority=generated_grade_authority)
    if isinstance(refreshed, dict):
        return refreshed
    if current_parent_pointer != expected_parent_pointer:
        _invalid("BAMF_ATLAS_RUNTIME_CONTEXT_CHANGED")
    raced, parent, parent_manifest = _revalidate_capability_publication(
        current, handoff, lease, runtime, source_authority,
        expected_parent_pointer,
        generated_grade_authority=generated_grade_authority)
    if isinstance(raced, dict):
        return raced
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import accepted_generation
    last_pointer, _accepted = accepted_generation(runtime.run_dir / "bamf-state.json")
    if last_pointer != expected_parent_pointer:
        _invalid("BAMF_ATLAS_RUNTIME_CONTEXT_CHANGED")
    transition = _issue_factory_release_adoption_transition(
        predecessor_factory_release_sha256=
            handoff.receipt.predecessor_release.release_sha256,
        factory_release_sha256=handoff.staged_candidate.successor.release_sha256,
        handoff_sha256=handoff.handoff_sha256,
        proposal_sha256=handoff.proposal.proposal_sha256,
        staged_candidate_sha256=handoff.staged_candidate.staged_sha256,
        selection_receipt_sha256=handoff.receipt.receipt_sha256,
        lease_sha256=lease.digest(),
        source_approval_sha256=contract_digest(lease.source_approval),
    )
    handoff.receipt.verify()
    inherited = read_accepted_atlas_obligation_credit(runtime.run_dir)
    accepted_obligation_keys = tuple(sorted(set(
        (() if inherited is None else inherited.obligation_keys)
        + tuple(requested_keys((handoff.receipt,)))
    )))
    candidate = derive_factory_release_adoption_candidate(
        parent, parent_manifest_sha256=parent_manifest, transition=transition)
    binding = _issue_factory_release_admission_binding(
        candidate, parent, transition=transition,
        accepted_obligation_keys=accepted_obligation_keys,
        generated_grade_proposal_sha256=_generated_grade_digest(
            generated_grade_authority, handoff))
    release_file = runtime_admission._persist_executable_factory_release(
        runtime.run_dir, handoff.staged_candidate.successor)
    expected_release_file = (
        "factory-releases/" + handoff.staged_candidate.successor.release_sha256 + ".json")
    if release_file != expected_release_file:
        _invalid("BAMF_ATLAS_FACTORY_RELEASE_DURABLE_DRIFT")
    pointer = publish_factory_release_adoption_generation(
        runtime.run_dir, candidate, admission=binding,
        reserve_gib=float(runtime.reserve_gib))
    cold = read_accepted_atlas_factory_release(runtime.run_dir)
    if cold.release_sha256 != handoff.staged_candidate.successor.release_sha256:
        _invalid("BAMF_ATLAS_ACCEPTED_FACTORY_RELEASE_DRIFT")
    return pointer
