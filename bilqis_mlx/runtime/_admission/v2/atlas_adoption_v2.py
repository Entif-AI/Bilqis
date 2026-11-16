"""C07 v2 mutation owners for capability-only and A02 successor adoption."""
from __future__ import annotations

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.atlas_lease_contracts import AtlasAdmissionLeaseV2, _invalid
from bilqis_mlx.runtime.jit_adoption import (
    _PreparedSuccessorRuntime,
    verify_current_implementations,
)


def advance_atlas_frontier_v2(*args, **kwargs):
    """Late-bound verifier seam; keeps legacy import order and test patching stable."""
    from bilqis_mlx.runtime.atlas_admission_policy_v2 import (
        advance_atlas_frontier_v2 as advance,
    )
    return advance(*args, **kwargs)


def replay_atlas_delta_scope_handoff_v2(*args, **kwargs):
    """Late-bound A09 replay seam; avoids policy/admission import recursion."""
    from bilqis_mlx.runtime.atlas_admission_policy_v2 import (
        replay_atlas_delta_scope_handoff_v2 as replay,
    )
    return replay(*args, **kwargs)


def _adopted_result(handoff, lease, pointer, reason):
    from bilqis_mlx.runtime.atlas_admission_policy import AdmissionResult, AdmissionStatus

    successor = handoff.staged_candidate.successor.release_sha256
    return AdmissionResult(
        AdmissionStatus.ADOPTED,
        handoff.proposal.proposal_sha256,
        lease.digest(),
        successor,
        successor,
        reason,
        "Cold-resume from accepted B13 custody before further neural work.",
        state_adopted=True,
        requires_cold_resume=True,
        accepted_generation=pointer["generation"],
        accepted_manifest_sha256=pointer["manifest_sha256"],
    )


def adopt_capability_only_atlas_successor_v2(
        current, delta, lease, *, generated_grade_authority=None):
    """Publish one exact zero-ID Factory successor after v2 verification."""
    from bilqis_mlx.runtime.atlas_admission_policy import AdmissionStatus
    from bilqis_mlx.runtime.atlas_admission_policy_v2 import (
        AtlasAdmissionContextV2,
        AtlasDeltaEnvelopeV2,
    )
    from bilqis_mlx.runtime.atlas_capability_adoption_v2 import (
        _accepted_capability_only_retry_state_v2,
        accepted_capability_only_retry_v2,
        publish_capability_only_factory_successor,
    )
    from bilqis_mlx.runtime.atlas_flywheel_runtime_context import (
        is_atlas_admission_runtime,
    )

    if (not isinstance(current, AtlasAdmissionContextV2)
            or not isinstance(delta, AtlasDeltaEnvelopeV2)
            or not isinstance(lease, AtlasAdmissionLeaseV2)):
        _invalid("BAMF_ATLAS_V2_ARGUMENT_INVALID")
    handoff = delta.handoff
    handoff.verify()
    legacy = current.legacy
    unavailable = (
        not is_atlas_admission_runtime(current.runtime)
        or current.source_authority is None
        or current.runtime.run_dir != current.run_dir
        or legacy.source_registry is None
        or legacy.answer_registry is None
        or any(value is not None for value in (
            legacy.runtime, legacy.native_staged, legacy.source_authority))
        or delta.native_staged is not None
        or tuple(handoff.receipt.selection.introduced_semantic_ids)
        or not tuple(handoff.receipt.selection.introduced_capability_ids)
    )
    if unavailable:
        _invalid("BAMF_ATLAS_V2_CAPABILITY_OWNER_UNAVAILABLE")
    if generated_grade_authority is None:
        retry, parent_pointer = _accepted_capability_only_retry_state_v2(
            current, handoff, lease)
    else:
        retry, parent_pointer = _accepted_capability_only_retry_state_v2(
            current, handoff, lease,
            generated_grade_authority=generated_grade_authority)
    if isinstance(retry, dict):
        return _adopted_result(handoff, lease, retry, "ADOPTED_CAPABILITY_ONLY")
    try:
        verified = advance_atlas_frontier_v2(current, delta, lease)
    except BilqisError:
        raced = accepted_capability_only_retry_v2(current, handoff, lease)
        if isinstance(raced, dict):
            return _adopted_result(
                handoff, lease, raced, "ADOPTED_CAPABILITY_ONLY")
        raise
    if (verified.status is not AdmissionStatus.STAGED
            or verified.reason != "V2_CAPABILITY_ONLY_AUTHORITY_VERIFIED"):
        return verified
    staged = replay_atlas_delta_scope_handoff_v2(current, handoff)
    if current.runtime is not None:
        from bilqis_mlx.factory.live_answers import live_answer_registry
        from bilqis_mlx.source_adapters.school import live_source_registry
        source_registry, answer_registry = live_source_registry(), live_answer_registry()
    else:
        source_registry, answer_registry = legacy.source_registry, legacy.answer_registry
    verify_current_implementations(staged.successor, source_registry, answer_registry)
    if generated_grade_authority is None:
        pointer = publish_capability_only_factory_successor(
            current, handoff, lease, expected_parent_pointer=parent_pointer)
    else:
        pointer = publish_capability_only_factory_successor(
            current, handoff, lease, expected_parent_pointer=parent_pointer,
            generated_grade_authority=generated_grade_authority)
    return _adopted_result(handoff, lease, pointer, "ADOPTED_CAPABILITY_ONLY")


def adopt_parameter_extension_atlas_successor_v2(
        current, delta, lease, *, generated_grade_authority=None):
    """Publish one exact A02 parameter extension using persisted v2 lease authority."""
    from bilqis_mlx.runtime.atlas_admission_policy import AdmissionStatus
    from bilqis_mlx.runtime.atlas_admission_policy_v2 import (
        AtlasAdmissionContextV2,
        AtlasDeltaEnvelopeV2,
    )
    from bilqis_mlx.runtime.atlas_parameter_adoption_v2 import (
        accepted_parameter_extension_retry_v2,
        publish_native_staged_candidate_v2,
    )
    from bilqis_mlx.runtime.bamf_bundle import require_issued_a02_staged_vocabulary_extension
    from bilqis_mlx.runtime.atlas_flywheel_runtime_context import (
        is_atlas_admission_runtime,
    )

    if (not isinstance(current, AtlasAdmissionContextV2)
            or not isinstance(delta, AtlasDeltaEnvelopeV2)
            or not isinstance(lease, AtlasAdmissionLeaseV2)):
        _invalid("BAMF_ATLAS_V2_ARGUMENT_INVALID")
    handoff = delta.handoff
    handoff.verify()
    legacy = current.legacy
    native = delta.native_staged
    unavailable = (
        current.runtime is not None
        or current.source_authority is not None
        or not is_atlas_admission_runtime(legacy.runtime)
        or legacy.runtime.run_dir != current.run_dir
        or legacy.native_staged is not native
        or legacy.source_authority is None
        or legacy.source_registry is None
        or legacy.answer_registry is None
        or not tuple(handoff.receipt.selection.introduced_semantic_ids)
        or native is None
    )
    if unavailable:
        _invalid("BAMF_ATLAS_V2_PARAMETER_OWNER_UNAVAILABLE")
    native = require_issued_a02_staged_vocabulary_extension(native)
    if generated_grade_authority is None:
        retry = accepted_parameter_extension_retry_v2(
            current, handoff, native, lease)
    else:
        retry = accepted_parameter_extension_retry_v2(
            current, handoff, native, lease,
            generated_grade_authority=generated_grade_authority)
    if retry is not None:
        return _adopted_result(
            handoff, lease, retry, "ADOPTED_PARAMETER_EXTENSION_V2")
    try:
        verified = advance_atlas_frontier_v2(current, delta, lease)
    except BilqisError:
        raced = accepted_parameter_extension_retry_v2(
            current, handoff, native, lease)
        if raced is not None:
            return _adopted_result(
                handoff, lease, raced, "ADOPTED_PARAMETER_EXTENSION_V2")
        raise
    if (verified.status is not AdmissionStatus.STAGED
            or verified.reason != "V2_DELTA_AUTHORITY_VERIFIED"):
        return verified
    staged = replay_atlas_delta_scope_handoff_v2(current, handoff)
    from bilqis_mlx.factory.live_answers import live_answer_registry
    from bilqis_mlx.source_adapters.school import live_source_registry
    verify_current_implementations(
        staged.successor, live_source_registry(), live_answer_registry())
    kwargs = dict(
        current=current, checkpoint=legacy.checkpoint, handoff=handoff)
    if generated_grade_authority is not None:
        kwargs["generated_grade_authority"] = generated_grade_authority
    pointer = publish_native_staged_candidate_v2(
        legacy.runtime, staged, handoff.proposal, native, lease,
        legacy.source_authority, **kwargs)
    return _adopted_result(
        handoff, lease, pointer, "ADOPTED_PARAMETER_EXTENSION_V2")
