"""Publication half of C07 capability-only Factory release adoption."""
from __future__ import annotations

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.atlas_lease_contracts import _invalid


def _owner_retry_state(*args, **kwargs):
    from bilqis_mlx.runtime.atlas_capability_adoption_v2 import (
        _accepted_capability_only_retry_state_v2,
    )
    return _accepted_capability_only_retry_state_v2(*args, **kwargs)


def _owner_retry(*args, **kwargs):
    from bilqis_mlx.runtime.atlas_capability_adoption_v2 import (
        accepted_capability_only_retry_v2,
    )
    return accepted_capability_only_retry_v2(*args, **kwargs)


def _owner_require_exact_release(*args, **kwargs):
    from bilqis_mlx.runtime.atlas_capability_adoption_v2 import (
        _require_exact_atlas_release,
    )
    return _require_exact_atlas_release(*args, **kwargs)


def _owner_verify_current_implementations(*args, **kwargs):
    from bilqis_mlx.runtime.atlas_capability_adoption_v2 import (
        verify_current_implementations,
    )
    return verify_current_implementations(*args, **kwargs)


def _owner_generated_grade_digest(*args, **kwargs):
    from bilqis_mlx.runtime.atlas_capability_adoption_v2 import (
        _generated_grade_digest,
    )
    return _generated_grade_digest(*args, **kwargs)


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
        _owner_require_exact_release(current, handoff, lease)
        accepted_current = read_accepted_atlas_factory_release(runtime.run_dir)
        runtime_checkpoint = atlas_admission_checkpoint(runtime, accepted_current)
        if (accepted_current.release_sha256
                != handoff.receipt.predecessor_release.release_sha256
                or parent.retained_state.optimizer_step
                   != current.legacy.checkpoint.optimizer_step
                or runtime_checkpoint != current.legacy.checkpoint):
            raced = _owner_retry(
                current, handoff, lease,
                generated_grade_authority=generated_grade_authority)
            if isinstance(raced, dict):
                return raced, None, None
            _invalid("BAMF_ATLAS_RUNTIME_CONTEXT_CHANGED")
        read_capability_only_admission_facts_v2(runtime.run_dir, handoff)
        _owner_verify_current_implementations(
            handoff.staged_candidate.successor,
            live_source_registry(), live_answer_registry())
    except BilqisError:
        raced = _owner_retry(
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
    from bilqis_mlx.runtime.atlas_admission import (
        read_accepted_atlas_obligation_credit,
    )

    runtime = current.runtime
    source_authority = current.source_authority
    from bilqis_mlx.runtime.atlas_flywheel_runtime_context import (
        is_atlas_admission_runtime,
    )
    if not is_atlas_admission_runtime(runtime):
        _invalid("BAMF_ATLAS_V2_CAPABILITY_OWNER_UNAVAILABLE")
    refreshed, current_parent_pointer = _owner_retry_state(
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
    return _publish_revalidated_factory_successor(
        current, handoff, lease, runtime, parent, parent_manifest,
        read_accepted_atlas_obligation_credit,
        generated_grade_authority=generated_grade_authority)


def _publish_revalidated_factory_successor(
        current, handoff, lease, runtime, parent, parent_manifest,
        read_accepted_atlas_obligation_credit, *, generated_grade_authority=None):
    """Issue and publish one fully revalidated neural-inert Factory successor."""
    from . import admission as runtime_admission
    from bilqis_mlx.factory.atlas_frontier_progress_validation import requested_keys
    from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_factory_release
    from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
        _issue_factory_release_admission_binding,
    )
    from bilqis_mlx.runtime.bamf_bundle.factory_release_adoption import (
        _issue_factory_release_adoption_transition,
        derive_factory_release_adoption_candidate,
    )
    from bilqis_mlx.runtime.bamf_bundle.publication import (
        publish_factory_release_adoption_generation,
    )
    from bilqis_mlx.semantics.domains import contract_digest

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
    generated_grade_digest = _owner_generated_grade_digest(
        generated_grade_authority, handoff)
    candidate_args = (
        {"new_semantic_admission": True}
        if generated_grade_digest is not None else {})
    candidate = derive_factory_release_adoption_candidate(
        parent, parent_manifest_sha256=parent_manifest, transition=transition,
        **candidate_args)
    binding = _issue_factory_release_admission_binding(
        candidate, parent, transition=transition,
        accepted_obligation_keys=accepted_obligation_keys,
        generated_grade_proposal_sha256=generated_grade_digest)
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
