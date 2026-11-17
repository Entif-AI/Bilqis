"""C07 v2 mutation helpers for genuine A02 parameter-extension successors."""
from __future__ import annotations

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.atlas_admission_policy_v2 import _require_exact_atlas_release
from bilqis_mlx.runtime.jit_adoption import (
    _accepted_native_retry,
    _authenticate_native_staged_candidate,
    verify_current_implementations,
)
from bilqis_mlx.runtime.atlas_lease_contracts import _invalid


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


def _accepted_parameter_extension_retry_once_v2(
        current, handoff, native_staged, lease, *,
        generated_grade_authority=None):
    """Authenticate one exact historical v2 A02 child before live-parent verification."""
    from bilqis_mlx.runtime.atlas_admission import (
        _accepted_run_lease_identity,
        read_accepted_atlas_factory_release,
        read_accepted_atlas_lease_v2,
    )
    from bilqis_mlx.runtime.bamf_bundle import (
        require_issued_a02_staged_vocabulary_extension,
    )
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import accepted_generation
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest,
    )
    from bilqis_mlx.runtime.bamf_bundle.atlas_admission import (
        ATLAS_ADMISSION_SCHEMA_V2, ATLAS_ADMISSION_SCHEMA_V3,
        ParsedAtlasAdmissionBinding,
    )
    from bilqis_mlx.factory.atlas_frontier_progress_validation import requested_keys

    native_staged = require_issued_a02_staged_vocabulary_extension(native_staged)
    pointer, accepted = accepted_generation(current.run_dir / "bamf-state.json")
    current_factory = read_accepted_atlas_factory_release(current.run_dir)
    source_authority = current.legacy.source_authority
    if current_factory.release_sha256 == handoff.staged_candidate.successor.release_sha256:
        from pathlib import Path
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        source_authority = AcceptedRuntimeHost(Path(current.run_dir)).source_authority()
    persisted = read_accepted_atlas_lease_v2(
        current.run_dir, source_authority=source_authority)
    if persisted is None or persisted != lease:
        _invalid("BAMF_ATLAS_V2_LEASE_CURRENT_AUTHORITY_DRIFT")
    lease.source_approval.verify_signature(current.legacy.registry)
    _require_exact_atlas_release(current, handoff, lease)
    candidate = native_staged.candidate
    retry = _accepted_native_retry(
        current.run_dir,
        candidate,
        candidate_identity=native_staged.receipt.candidate_identity_sha256,
        parent_feature=native_staged.receipt.parent_feature_receipt_sha256,
        staging_digest=native_staged.receipt.digest,
        atlas_lease=lease,
        proposal=handoff.proposal,
        selected=handoff.staged_candidate,
    )
    if retry is not None:
        binding = accepted_binding_for_manifest(
            current.run_dir, pointer["manifest_sha256"], accepted,
            expected_acceptance_sha256=pointer["acceptance_sha256"])
        expected_keys = set(requested_keys((handoff.receipt,)))
        if (isinstance(binding, ParsedAtlasAdmissionBinding)
                and binding.schema_version in {
                    ATLAS_ADMISSION_SCHEMA_V2, ATLAS_ADMISSION_SCHEMA_V3}
                and (binding.selection_receipt_sha256
                     != handoff.receipt.receipt_sha256
                     or not expected_keys.issubset(binding.selected_obligation_keys))):
            _invalid("BAMF_ATLAS_NATIVE_RETRY_DRIFT")
        expected_generated_grade = _generated_grade_digest(
            generated_grade_authority, handoff)
        if expected_generated_grade is not None and (
                not isinstance(binding, ParsedAtlasAdmissionBinding)
                or binding.schema_version != ATLAS_ADMISSION_SCHEMA_V3
                or binding.generated_grade_proposal_sha256
                   != expected_generated_grade):
            _invalid("BAMF_ATLAS_NATIVE_RETRY_DRIFT")
        cold = read_accepted_atlas_factory_release(current.run_dir)
        if cold.release_sha256 != handoff.staged_candidate.successor.release_sha256:
            _invalid("BAMF_ATLAS_NATIVE_RETRY_DRIFT")
        return retry
    accepted_identity = _accepted_run_lease_identity(current.run_dir)
    if (accepted.generation + 1 != candidate.generation
            or candidate.parent_manifest_sha256 != pointer["manifest_sha256"]
            or accepted_identity != current.legacy.run_identity
            or current.legacy.current_release.release_sha256
               != handoff.receipt.predecessor_release.release_sha256
            or handoff.proposal.current_release_sha256
               != handoff.receipt.predecessor_release.release_sha256
            or current_factory.release_sha256
               != handoff.receipt.predecessor_release.release_sha256):
        _invalid("BAMF_ATLAS_V2_PARAMETER_RETRY_CONFLICT")
    return None


def accepted_parameter_extension_retry_v2(
        current, handoff, native_staged, lease, *,
        generated_grade_authority=None):
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
                result = _accepted_parameter_extension_retry_once_v2(
                    current, handoff, native_staged, lease)
            else:
                result = _accepted_parameter_extension_retry_once_v2(
                    current, handoff, native_staged, lease,
                    generated_grade_authority=generated_grade_authority)
        except BilqisError:
            after, _student = accepted_generation(current.run_dir / "bamf-state.json")
            if identity(after) == identity(before):
                raise
            if attempt == 1:
                _invalid("BAMF_ATLAS_V2_PARAMETER_RETRY_CONFLICT")
            continue
        after, _student = accepted_generation(current.run_dir / "bamf-state.json")
        if identity(after) == identity(before):
            return result
        if attempt == 1:
            _invalid("BAMF_ATLAS_V2_PARAMETER_RETRY_CONFLICT")

    _invalid("BAMF_ATLAS_V2_PARAMETER_RETRY_CONFLICT")


def _revalidate_parameter_publication(
        runtime, selected, native_staged, atlas_lease, source_authority,
        *, current, checkpoint, handoff, generated_grade_authority=None):
    from bilqis_mlx.runtime.atlas_flywheel_runtime_context import (
        atlas_admission_checkpoint,
    )
    from bilqis_mlx.runtime.atlas_admission import (
        read_accepted_atlas_factory_release,
        read_accepted_atlas_lease_v2,
    )
    from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority

    persisted = read_accepted_atlas_lease_v2(
        runtime.run_dir, source_authority=source_authority)
    if persisted is None or persisted != atlas_lease:
        _invalid("BAMF_ATLAS_V2_LEASE_CURRENT_AUTHORITY_DRIFT")
    atlas_lease.source_approval.verify_signature(current.legacy.registry)
    _require_exact_atlas_release(current, handoff, atlas_lease)
    try:
        candidate = _authenticate_native_staged_candidate(
            runtime.run_dir, native_staged)
        parent, parent_manifest = load_bamf_generation_authority(
            runtime.run_dir / "bamf-state.json")
        persisted = read_accepted_atlas_lease_v2(
            runtime.run_dir, source_authority=source_authority)
        if persisted is None or persisted != atlas_lease:
            _invalid("BAMF_ATLAS_V2_LEASE_CURRENT_AUTHORITY_DRIFT")
        atlas_lease.source_approval.verify_signature(current.legacy.registry)
        _require_exact_atlas_release(current, handoff, atlas_lease)
        accepted_current = read_accepted_atlas_factory_release(runtime.run_dir)
        accepted_current.verify_semantic_catalog(runtime.graph)
        runtime_checkpoint = atlas_admission_checkpoint(runtime, accepted_current)
        if (accepted_current.release_sha256
                != handoff.receipt.predecessor_release.release_sha256
                or candidate.parent_manifest_sha256 != parent_manifest
                or parent.retained_state.optimizer_step != checkpoint.optimizer_step
                or runtime_checkpoint != checkpoint):
            _invalid("BAMF_ATLAS_RUNTIME_CONTEXT_CHANGED")
        from bilqis_mlx.factory.live_answers import live_answer_registry
        from bilqis_mlx.source_adapters.school import live_source_registry
        verify_current_implementations(
            selected.successor, live_source_registry(), live_answer_registry())
    except BilqisError:
        raced = accepted_parameter_extension_retry_v2(
            current, handoff, native_staged, atlas_lease,
            generated_grade_authority=generated_grade_authority)
        if raced is not None:
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
    return None, candidate, parent


def publish_native_staged_candidate_v2(
        runtime, selected, proposal, native_staged, atlas_lease,
        source_authority, *, current, checkpoint, handoff,
        generated_grade_authority=None):
    """Publish the exact A02 state using only the persisted v2 lease store."""
    from bilqis_mlx.runtime.atlas_admission import (
        _hold_current_atlas_lease_v2_publication,
    )
    with _hold_current_atlas_lease_v2_publication(runtime.run_dir, atlas_lease):
        return _publish_native_staged_candidate_v2_locked(
            runtime, selected, proposal, native_staged, atlas_lease,
            source_authority, current=current, checkpoint=checkpoint,
            handoff=handoff,
            generated_grade_authority=generated_grade_authority)


def _publish_native_staged_candidate_v2_locked(
        runtime, selected, proposal, native_staged, atlas_lease,
        source_authority, *, current, checkpoint, handoff,
        generated_grade_authority=None):
    """Publish A02 state while human v2 lease renewal is excluded."""
    from . import admission as runtime_admission
    from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_factory_release
    from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_obligation_credit
    from bilqis_mlx.runtime.bamf_bundle import (
        publish_atlas_admission_generation,
        require_issued_a02_staged_vocabulary_extension,
        require_staged_vocabulary_admission_headroom,
    )
    from bilqis_mlx.runtime.bamf_bundle.atlas_admission import (
        _issue_atlas_admission_binding,
    )
    from bilqis_mlx.semantics.domains import contract_digest
    from bilqis_mlx.factory.atlas_frontier_progress_validation import requested_keys

    native_staged = require_issued_a02_staged_vocabulary_extension(native_staged)
    candidate = native_staged.candidate
    staging_receipt = native_staged.receipt
    retry = accepted_parameter_extension_retry_v2(
        current, handoff, native_staged, atlas_lease,
        generated_grade_authority=generated_grade_authority)
    if retry is not None:
        return retry
    raced, candidate, parent = _revalidate_parameter_publication(
        runtime, selected, native_staged, atlas_lease, source_authority,
        current=current, checkpoint=checkpoint, handoff=handoff,
        generated_grade_authority=generated_grade_authority)
    if raced is not None:
        return raced
    from bilqis_mlx.factory.candidate_realizations import admitted_candidate_graph
    from bilqis_mlx.runtime.bamf_bundle.vocabulary.compiler_binding import (
        bind_parameter_extension_compiler_state,
    )
    successor_graph = admitted_candidate_graph(selected, runtime.graph)
    candidate = bind_parameter_extension_compiler_state(
        candidate, selected.successor, successor_graph)
    require_staged_vocabulary_admission_headroom(runtime.run_dir, native_staged)
    handoff.receipt.verify()
    inherited = read_accepted_atlas_obligation_credit(runtime.run_dir)
    accepted_obligation_keys = tuple(sorted(set(
        (() if inherited is None else inherited.obligation_keys)
        + tuple(requested_keys((handoff.receipt,)))
    )))
    release_file = runtime_admission._persist_executable_factory_release(
        runtime.run_dir, selected.successor)
    expected_release_file = "factory-releases/" + selected.successor.release_sha256 + ".json"
    if release_file != expected_release_file:
        _invalid("BAMF_ATLAS_FACTORY_RELEASE_DURABLE_DRIFT")
    binding = _issue_atlas_admission_binding(
        candidate, parent,
        lease_sha256=atlas_lease.digest(),
        source_approval_sha256=contract_digest(atlas_lease.source_approval),
        proposal_sha256=proposal.proposal_sha256,
        factory_release_sha256=selected.successor.release_sha256,
        staging_receipt_sha256=staging_receipt.digest,
        parent_feature_receipt_sha256=staging_receipt.parent_feature_receipt_sha256,
        selection_receipt_sha256=handoff.receipt.receipt_sha256,
        selected_obligation_keys=accepted_obligation_keys,
        predecessor_factory_release_sha256=
            handoff.receipt.predecessor_release.release_sha256,
        generated_grade_proposal_sha256=_generated_grade_digest(
            generated_grade_authority, handoff),
    )
    pointer = publish_atlas_admission_generation(
        runtime.run_dir, candidate, admission=binding,
        reserve_gib=float(runtime.reserve_gib))
    cold = read_accepted_atlas_factory_release(runtime.run_dir)
    if cold.release_sha256 != selected.successor.release_sha256:
        _invalid("BAMF_ATLAS_ACCEPTED_FACTORY_RELEASE_DRIFT")
    return pointer
