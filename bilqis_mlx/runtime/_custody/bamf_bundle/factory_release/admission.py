"""C07/B13 acceptance for neural-inert Factory-release adoption."""
from __future__ import annotations

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest

from ..factory_release_adoption import (
    FACTORY_RELEASE_ADOPTION_EVENT,
    FACTORY_RELEASE_ADOPTION_EVENT_SCHEMA,
    FACTORY_RELEASE_ADOPTION_KIND,
    FACTORY_RELEASE_ADOPTION_TRANSITION_SCHEMA,
    require_issued_factory_release_adoption_transition,
)
from ..records import BamfBundleCandidate, CompleteStudent, canonical, invalid, sha
from .admission_binding import (
    FACTORY_RELEASE_ADMISSION_SCHEMA,
    FACTORY_RELEASE_ADMISSION_SCHEMA_V1,
    FACTORY_RELEASE_ADMISSION_SCHEMA_V2,
    FACTORY_RELEASE_ADMISSION_SCHEMA_V3,
    FACTORY_RELEASE_ADMISSION_SCHEMAS,
    FactoryReleaseAdmissionBinding,
    ParsedFactoryReleaseAdmissionBinding,
    _mint_binding,
    _require_live_binding,
    _valid_obligation_keys,
)


_EVENT_FIELDS = frozenset({
    "event", "schema", "run_id", "generation", "optimizer_step",
    "predecessor_factory_release_sha256", "factory_release_sha256",
    "handoff_sha256", "proposal_sha256", "selection_receipt_sha256",
    "lease_sha256", "source_approval_sha256", "transition_sha256",
})
_PROVENANCE_FIELDS = (
    "predecessor_factory_release_sha256", "factory_release_sha256",
    "handoff_sha256", "proposal_sha256", "selection_receipt_sha256",
    "lease_sha256", "source_approval_sha256", "transition_sha256",
)


def _invalid(reason="BAMF_FACTORY_RELEASE_ADMISSION_BINDING_INVALID") -> None:
    invalid(reason)


def _same_inert_state(parent: CompleteStudent, candidate: BamfBundleCandidate) -> bool:
    parent_state = parent.retained_state
    candidate_state = candidate.retained_state
    return (
        parent.run_identity == candidate.run_identity
        and parent.run_id == candidate.run_id
        and parent.generation + 1 == candidate.generation
        and parent.implementation_sha256 == candidate.implementation_sha256
        and parent.topology == candidate.topology
        and parent.extents == candidate.extents
        # B13 deliberately cold-reloads the accepted parent under publication
        # lock.  Compare durable retained-state value identities, never Python
        # object identity or MLX array equality.
        and candidate_identity_digest(parent_state)
            == candidate_identity_digest(candidate_state)
        and parent_state.optimizer_step == candidate_state.optimizer_step
        and parent_state.policy.to_record() == candidate_state.policy.to_record()
        and parent_state.allocations.digest == candidate_state.allocations.digest
        and parent_state.custody == candidate_state.custody
        and tuple(proof.digest for proof in parent_state.step_proofs)
            == tuple(proof.digest for proof in candidate_state.step_proofs)
        and parent.optimizer_hyperparameters == candidate.optimizer_hyperparameters
        and parent.provenance == candidate.provenance
        and dict(parent.semantic_abi) == dict(candidate.semantic_abi)
        and dict(parent.compiler_features) == dict(candidate.compiler_features)
        and dict(parent.correction_frontier) == dict(candidate.correction_frontier)
        and dict(parent.teacher_state) == dict(candidate.teacher_state)
        and dict(parent.evaluation_contract) == dict(candidate.evaluation_contract)
    )


def require_factory_release_inert_state(
        parent: CompleteStudent,
        candidate: BamfBundleCandidate) -> None:
    """Require the complete neural-inert B13 parent/child state contract."""
    if (type(parent) is not CompleteStudent
            or type(candidate) is not BamfBundleCandidate
            or not _same_inert_state(parent, candidate)):
        _invalid("BAMF_FACTORY_RELEASE_ADOPTION_STATE_DRIFT")


def _owner_event(candidate) -> dict:
    if type(candidate.outbox) is not tuple or len(candidate.outbox) != 1:
        _invalid()
    event = candidate.outbox[0]
    if (not isinstance(event, dict) or set(event) != _EVENT_FIELDS
            or event.get("event") != FACTORY_RELEASE_ADOPTION_EVENT
            or event.get("schema") != FACTORY_RELEASE_ADOPTION_EVENT_SCHEMA
            or "event_id" in event):
        _invalid()
    return event


def _issue_factory_release_admission_binding(
        candidate: BamfBundleCandidate, parent: CompleteStudent, *, transition,
        accepted_obligation_keys: tuple[tuple[str, str], ...] = (),
        generated_grade_proposal_sha256: str | None = None,
) -> FactoryReleaseAdmissionBinding:
    transition = require_issued_factory_release_adoption_transition(transition)
    event = _owner_event(candidate)
    if (type(candidate) is not BamfBundleCandidate
            or type(parent) is not CompleteStudent
            or not _same_inert_state(parent, candidate)
            or dict(candidate.transition) != transition.to_record()
            or candidate.retained_state.optimizer_step
            != parent.retained_state.optimizer_step
            or event["run_id"] != candidate.run_id
            or event["generation"] != candidate.generation
            or event["optimizer_step"] != candidate.retained_state.optimizer_step
            or any(event[name] != getattr(transition, name)
                   for name in _PROVENANCE_FIELDS if name != "transition_sha256")
            or event["transition_sha256"] != transition.digest):
        _invalid()
    obligation_keys = tuple(sorted(set(accepted_obligation_keys)))
    if obligation_keys and not _valid_obligation_keys(obligation_keys):
        _invalid()
    schema_version = (
        FACTORY_RELEASE_ADMISSION_SCHEMA_V3
        if generated_grade_proposal_sha256 is not None
        else FACTORY_RELEASE_ADMISSION_SCHEMA_V2
        if obligation_keys
        else FACTORY_RELEASE_ADMISSION_SCHEMA_V1
    )
    return _mint_binding(
        run_id=candidate.run_id, generation=candidate.generation,
        candidate_identity_sha256=candidate_identity_digest(candidate.retained_state),
        parent_candidate_identity_sha256=candidate_identity_digest(parent.retained_state),
        feature_sha256=candidate.extents.factor_map_digest,
        optimizer_step=candidate.retained_state.optimizer_step,
        lease_sha256=transition.lease_sha256,
        source_approval_sha256=transition.source_approval_sha256,
        handoff_sha256=transition.handoff_sha256,
        proposal_sha256=transition.proposal_sha256,
        selection_receipt_sha256=transition.selection_receipt_sha256,
        predecessor_factory_release_sha256=transition.predecessor_factory_release_sha256,
        factory_release_sha256=transition.factory_release_sha256,
        transition_sha256=transition.digest,
        adoption_event_sha256=sha(canonical(event)),
        accepted_obligation_keys=obligation_keys,
        generated_grade_proposal_sha256=generated_grade_proposal_sha256,
        schema_version=schema_version,
    )


def require_factory_release_admission_binding(
        candidate: BamfBundleCandidate, value) -> FactoryReleaseAdmissionBinding:
    value = _require_live_binding(value)
    transition = require_issued_factory_release_adoption_transition(
        candidate.transition)
    event = _owner_event(candidate)
    if (value.run_id != candidate.run_id
            or value.generation != candidate.generation
            or value.candidate_identity_sha256
            != candidate_identity_digest(candidate.retained_state)
            or value.feature_sha256 != candidate.extents.factor_map_digest
            or value.optimizer_step != candidate.retained_state.optimizer_step
            or value.transition_sha256 != transition.digest
            or value.adoption_event_sha256 != sha(canonical(event))
            or any(event[name] != getattr(value, name)
                   for name in _PROVENANCE_FIELDS)
            or event["run_id"] != value.run_id
            or event["generation"] != value.generation
            or event["optimizer_step"] != value.optimizer_step):
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT")
    return value


def validate_parsed_factory_release_admission_binding(
        student: CompleteStudent,
        binding: ParsedFactoryReleaseAdmissionBinding,
        expected_acceptance_sha256: str) -> None:
    """Authenticate historical Factory-specific transition and outbox provenance."""
    if (type(student) is not CompleteStudent
            or type(binding) is not ParsedFactoryReleaseAdmissionBinding
            or binding.digest != expected_acceptance_sha256
            or binding.run_id != student.run_id
            or binding.generation != student.generation
            or binding.feature_sha256 != student.extents.factor_map_digest
            or binding.optimizer_step != student.retained_state.optimizer_step
            or binding.candidate_identity_sha256
            != candidate_identity_digest(student.retained_state)):
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT")
    transition = dict(student.transition)
    if (transition.get("schema") != FACTORY_RELEASE_ADOPTION_TRANSITION_SCHEMA
            or transition.get("kind") != FACTORY_RELEASE_ADOPTION_KIND):
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_INVALID")
    transition_sha256 = sha(canonical(transition))
    if transition_sha256 != binding.transition_sha256:
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT")
    events = tuple(
        event for event in student.outbox
        if isinstance(event, dict)
        and event.get("event") == FACTORY_RELEASE_ADOPTION_EVENT
        and event.get("schema") == FACTORY_RELEASE_ADOPTION_EVENT_SCHEMA)
    if len(student.outbox) != 1 or len(events) != 1:
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_INVALID")
    stored = events[0]
    if set(stored) != _EVENT_FIELDS | {"event_id"}:
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_INVALID")
    owner_event = {key: value for key, value in stored.items() if key != "event_id"}
    from bilqis_mlx.runtime.checkpoint_outbox import (
        ordinary_outbox_lineage, with_delivery_outbox,
    )
    lineage = {"run_id": student.run_id, "generation": student.generation}
    expected = with_delivery_outbox(lineage, (owner_event,))["delivery_outbox"]
    if (not ordinary_outbox_lineage(lineage, list(student.outbox))
            or len(expected) != 1 or expected[0] != stored
            or sha(canonical(owner_event)) != binding.adoption_event_sha256
            or owner_event["run_id"] != binding.run_id
            or owner_event["generation"] != binding.generation
            or owner_event["optimizer_step"] != binding.optimizer_step
            or owner_event["transition_sha256"] != transition_sha256):
        _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT")
    for name in _PROVENANCE_FIELDS:
        expected_value = transition_sha256 if name == "transition_sha256" else transition[name]
        if (getattr(binding, name) != expected_value
                or owner_event[name] != expected_value):
            _invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT")


__all__ = (
    "FACTORY_RELEASE_ADMISSION_SCHEMA",
    "FACTORY_RELEASE_ADMISSION_SCHEMA_V1",
    "FACTORY_RELEASE_ADMISSION_SCHEMA_V2",
    "FACTORY_RELEASE_ADMISSION_SCHEMA_V3",
    "FACTORY_RELEASE_ADMISSION_SCHEMAS",
    "FactoryReleaseAdmissionBinding",
    "ParsedFactoryReleaseAdmissionBinding",
    "_issue_factory_release_admission_binding",
    "require_factory_release_inert_state",
    "require_factory_release_admission_binding",
    "validate_parsed_factory_release_admission_binding",
)
