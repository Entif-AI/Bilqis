"""B13-authenticated rejection replay for C03.4 priority recency."""
import hashlib
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

from bilqis_mlx.data_plane import data_plane
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime import checkpoint_outbox
from bilqis_mlx.runtime.bamf_bundle.records import canonical
from .priority_rejection_projection import RejectionProjection


SHA256_HEX_LENGTH = 64


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


@lru_cache(maxsize=16)
def _projection(_identity):
    return RejectionProjection()


def _validated_rejection(event, parent, cache):
    if event.get("event") != "BAMF_CANDIDATE_REJECTED":
        return None
    if event.get("generation") != cache.generation:
        return None
    if (event.get("student_manifest_sha256") != cache.accepted_manifest_sha256
            or event.get("optimizer_step") != parent.retained_state.optimizer_step):
        _invalid("BAMF_PRIORITY_REJECTION_IDENTITY_DRIFT")
    lineage = {"run_id": cache.run_id, "generation": cache.generation}
    if not checkpoint_outbox.ordinary_outbox_lineage(lineage, [event]):
        _invalid("BAMF_PRIORITY_REJECTION_OUTBOX_INVALID")
    evidence = event.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("schema") != "bilqis.bamf.c16.3-rejection/v2":
        return None
    authority_sha256 = event.get("rejection_authority_sha256")
    if (not isinstance(authority_sha256, str)
            or len(authority_sha256) != SHA256_HEX_LENGTH
            or any(char not in "0123456789abcdef" for char in authority_sha256)):
        _invalid("BAMF_PRIORITY_REJECTION_AUTHORITY_INVALID")
    authority = {
        "schema": "bilqis.mlx.bamf-rejection-authority/v1",
        "run_id": cache.run_id,
        "generation": cache.generation,
        "student_manifest_sha256": cache.accepted_manifest_sha256,
        "optimizer_step": parent.retained_state.optimizer_step,
        "evidence": evidence,
    }
    try:
        authority_raw = data_plane().get_object(authority_sha256)
    except ValueError:
        _invalid("BAMF_PRIORITY_REJECTION_AUTHORITY_INVALID")
    if authority_raw != canonical(authority):
        _invalid("BAMF_PRIORITY_REJECTION_AUTHORITY_DRIFT")
    receipt = {
        "schema": "bilqis.mlx.bamf-rejection-receipt/v1",
        "run_id": cache.run_id,
        "generation": cache.generation,
        "student_manifest_sha256": cache.accepted_manifest_sha256,
        "event": event,
    }
    receipt_raw = canonical(receipt)
    receipt_sha256 = hashlib.sha256(receipt_raw).hexdigest()
    try:
        stored_receipt = data_plane().get_object(receipt_sha256)
    except ValueError:
        _invalid("BAMF_PRIORITY_REJECTION_RECEIPT_INVALID")
    if stored_receipt != receipt_raw:
        _invalid("BAMF_PRIORITY_REJECTION_RECEIPT_DRIFT")
    selected = evidence.get("capability")
    visit_id = evidence.get("visit_id")
    candidate_step = evidence.get("candidate_optimizer_step")
    retained_step = evidence.get("retained_optimizer_step")
    reason = evidence.get("retention_reason")
    rejection_attempt_ordinal = evidence.get("rejection_attempt_ordinal")
    rejection_journal_ordinal = evidence.get("rejection_journal_ordinal")
    if (not isinstance(selected, str) or not selected
            or not isinstance(visit_id, str) or not visit_id
            or type(candidate_step) is not int
            or candidate_step <= parent.retained_state.optimizer_step
            or retained_step != parent.retained_state.optimizer_step
            or not isinstance(reason, str) or not reason
            or (rejection_attempt_ordinal is not None
                and (type(rejection_attempt_ordinal) is not int
                     or rejection_attempt_ordinal < 1))
            or (rejection_journal_ordinal is not None
                and (type(rejection_journal_ordinal) is not int
                     or rejection_journal_ordinal < 1))):
        _invalid("BAMF_PRIORITY_REJECTION_EVIDENCE_INVALID")
    from bilqis_mlx.runtime.structural_weakness_replay import (
        validate_rejection_weaknesses,
    )
    weaknesses = validate_rejection_weaknesses(evidence, receipt_sha256)
    return (
        receipt_sha256,
        (selected, visit_id, reason, receipt_sha256),
        rejection_attempt_ordinal,
        rejection_journal_ordinal,
        weaknesses,
    )


def _current_projection(run_dir, parent, cache):
    path_key = str(Path(run_dir).absolute())
    identity = (
        path_key,
        cache.run_id,
        cache.generation,
        cache.accepted_manifest_sha256,
        parent.retained_state.optimizer_step,
    )
    projection = _projection(identity)
    projection.refresh(
        Path(run_dir),
        "|".join(str(value) for value in identity[1:]),
        data_plane(),
        lambda event: _validated_rejection(event, parent, cache),
        _invalid,
    )
    return projection


def current_rejections(run_dir, parent, cache):
    """O(1)-snapshot view of authenticated current-generation rejection rows."""
    return _current_projection(run_dir, parent, cache).rows_view()


def authenticated_rejection_event(event, parent, manifest_sha256):
    """Validate one persisted C16.3 rejection against its accepted generation."""
    cache = SimpleNamespace(
        run_id=parent.run_id,
        generation=parent.generation,
        accepted_manifest_sha256=manifest_sha256,
    )
    return _validated_rejection(event, parent, cache) is not None


def ordered_rejections(run_dir, parent, cache):
    """Rows whose cross-capability order is authenticated by journal ordinals."""
    return _current_projection(run_dir, parent, cache).ordered_rows_view()


def rejection_attempt_ordinals(run_dir, parent, cache, capability):
    """Return next global and per-capability authenticated rejection ordinals."""
    return _current_projection(run_dir, parent, cache).next_ordinals(capability)


def rejection_pressure(run_dir, parent, cache, capability):
    """Return bounded aggregates without folding the complete rejection sequence."""
    return _current_projection(run_dir, parent, cache).pressure(capability)


def rejection_recency(run_dir, parent, cache):
    """Return total rejection count and latest global position for each capability."""
    return _current_projection(run_dir, parent, cache).recency()


def current_structural_weaknesses(
        run_dir, parent, cache, source_context, selection, capability=None):
    """Return deduplicated unresolved debt; downstream repair owns closure evidence."""
    from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
    from bilqis_mlx.runtime.structural_weakness_replay import (
        carried_structural_weaknesses, weakness_is_current,
    )

    projection = _current_projection(run_dir, parent, cache)
    selected = capability or selection.visit.identity.capability_id
    current = {}
    # Generation-zero parent custody intentionally precedes C03 bootstrap.
    # The issued visit already owns the authenticated current teacher projection.
    teacher = restore_teacher_lineage(selection.visit.projection.teacher_state).teacher()
    candidates = (
        *carried_structural_weaknesses(teacher),
        *projection.weaknesses_view(),
    )
    for item in candidates:
        weakness = item["weakness"]
        if (weakness["capability_id"] == selected
                and weakness_is_current(item, source_context, selection)):
            current[weakness["weakness_class"]["class_sha256"]] = item
    return tuple(current[key] for key in sorted(current))


def candidate_step_horizon(run_dir, parent, cache, capability, configured_steps):
    """Project authenticated C16.3 rejection pressure into the teacher horizon rule.

    Rejections do not mutate the accepted teacher state.  The accepted-generation
    journal is therefore the authoritative pressure source for the current
    speculative lineage.  Feed only that bounded projection into the existing
    candidate-step policy rather than inventing a second shortening cadence.
    """
    from bilqis_mlx.learning.learning_experiment import candidate_step_budget

    reasons, consecutive_interference = rejection_pressure(
        run_dir, parent, cache, capability)
    projected_teacher = {
        "causal_experiment": {
            "capability_stagnation": {
                capability + "|": {
                    "current_rejection_reasons": reasons,
                    "consecutive_interference_rejections": consecutive_interference,
                },
            },
        },
    }
    return candidate_step_budget(configured_steps, projected_teacher, capability)


__all__ = (
    "authenticated_rejection_event", "candidate_step_horizon",
    "current_rejections", "ordered_rejections",
    "current_structural_weaknesses",
    "rejection_attempt_ordinals",
    "rejection_pressure", "rejection_recency",
)
