"""Retention-owner acceptance binding for accepted candidate generations.

Live bindings attest the C05 screen and both optimizer identities. Historical
records remain parseable but cannot become publication capabilities.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from bilqis_mlx.errors import ErrorBus, SCHOOL

from .atlas_retention_decision import CandidateRetentionDecision
from bilqis_mlx.learning._retention._atlas_candidate.identity import candidate_identity_digest
from ._atlas_acceptance_records import (
    ACCEPTANCE_SCHEMA, CLOSURE_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
    EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
    EXACT_MOTIF_ACCEPTANCE_SCHEMA, EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
    CLOSURE_BINDING_FIELDS, MOTIF_CLOSURE_BINDING_FIELDS,
    EXACT_BINDING_FIELDS, EXACT_CLOSURE_BINDING_FIELDS, normalize_artifact_closures,
    BINDING_FIELDS as _BINDING_FIELDS,
    LEGACY_ACCEPTANCE_SCHEMA, MOTIF_ACCEPTANCE_SCHEMA,
    MOTIF_BINDING_FIELDS as _MOTIF_BINDING_FIELDS,
    PREVIOUS_ACCEPTANCE_SCHEMA, PREVIOUS_DEPENDENCY_ACCEPTANCE_SCHEMA,
    PREVIOUS_SOURCE_ACCEPTANCE_SCHEMA,
    ParsedAcceptedCandidateBinding, canonical as _canonical,
    is_digest as _is_digest, parse_accepted_candidate_binding,
    valid_source_anchors as _valid_source_anchors,
)


def _new_binding_owner():
    """Track live acceptance bindings by mint-owned object identity."""
    issued = {}

    def require(value):
        if issued.get(id(value)) is not value:
            _invalid()
        return value

    def issue(values):
        binding = object.__new__(AcceptedCandidateBinding)
        for name, value in values:
            object.__setattr__(binding, name, value)
        issued[id(binding)] = binding
        binding.__post_init__()
        return binding

    return require, issue


def _invalid() -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


def _dependency_record(authority) -> tuple[tuple[str, str], ...]:
    return tuple(
        (ref.kind.value, ref.key) for ref in authority.immediate_dependencies)


def _source_anchors(training_authorities, state) -> tuple[tuple, ...]:
    if training_authorities is None:
        if any(proof.training_authority_sha256 is not None
               for proof in state.step_proofs):
            _invalid()
        return ()
    if type(training_authorities) is not tuple:
        _invalid()
    from bilqis_mlx.runtime.atlas_training_authority import (
        BamfLogicalBatchTrainingAuthority, BamfTrainingAuthority,
    )
    if len(training_authorities) != len(state.step_proofs):
        _invalid()
    anchors = []
    for proof, authority in zip(state.step_proofs, training_authorities):
        if type(authority) is BamfTrainingAuthority:
            authority.__post_init__()
            members = (authority,)
            if (proof.training_authority_sha256 != authority.digest
                    or proof.source_release_sha256 != authority.release_sha256
                    or proof.training_batch_sha256 != authority.training_batch_sha256
                    or proof.target_capability_id != authority.delivery_capability
                    or proof.source_family_id != authority.source_family_id
                    or proof.episode_id != authority.episode_id):
                _invalid()
        elif type(authority) is BamfLogicalBatchTrainingAuthority:
            authority.__post_init__()
            members = authority.members
            if (proof.training_authority_sha256 != authority.digest
                    or proof.source_release_sha256 != authority.release_sha256
                    or proof.training_batch_sha256 != authority.training_batch_sha256
                    or proof.target_capability_id != authority.delivery_capability
                    or proof.training_authority_members != tuple(
                        (member.digest, member.source_family_id, member.episode_id)
                        for member in members)):
                _invalid()
        else:
            _invalid()
        anchors.extend((
            member.delivery_capability,
            member.source_row_id,
            member.source_row_sha256,
            member.source_family_id,
            member.episode_id,
            member.release_sha256,
            member.training_batch_sha256,
            member.generation_binding,
            member.digest,
            _dependency_record(member),
        ) for member in members)
    return tuple(anchors)


@dataclass(frozen=True)
class AcceptedCandidateBinding:
    """Live owner-issued acceptance for one exact candidate and parent."""

    run_id: str
    generation: int
    candidate_identity_sha256: str
    parent_candidate_identity_sha256: str
    feature_sha256: str
    optimizer_step: int
    retention_reason: str
    decision_sha256: str
    evidence_sha256: str
    policy_sha256: str
    step_proof_sha256: tuple = ()
    source_anchors: tuple = ()
    source_authority_registry_sha256: str | None = None
    teacher_state_sha256: str | None = None
    generation_authority_sha256: str | None = None
    artifact_closures: tuple = ()
    schema_version: str = ACCEPTANCE_SCHEMA

    def __post_init__(self) -> None:
        _require_issued_binding(self)
        if (not isinstance(self.run_id, str) or not self.run_id
                or type(self.generation) is not int or self.generation < 0
                or any(not _is_digest(value) for value in (
                    self.candidate_identity_sha256,
                    self.parent_candidate_identity_sha256, self.feature_sha256,
                    self.decision_sha256, self.evidence_sha256, self.policy_sha256))
                or type(self.optimizer_step) is not int or self.optimizer_step < 0
                or not isinstance(self.retention_reason, str) or not self.retention_reason
                or type(self.step_proof_sha256) is not tuple
                or any(not _is_digest(value) for value in self.step_proof_sha256)
                or not _valid_source_anchors(
                    self.source_anchors, self.schema_version)
                or (self.source_authority_registry_sha256 is not None
                    and not _is_digest(self.source_authority_registry_sha256))
                or self.schema_version not in {
                    ACCEPTANCE_SCHEMA, MOTIF_ACCEPTANCE_SCHEMA,
                    CLOSURE_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
                    EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
                    EXACT_MOTIF_ACCEPTANCE_SCHEMA, EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA}
                or (self.schema_version in (ACCEPTANCE_SCHEMA, CLOSURE_ACCEPTANCE_SCHEMA)
                    and self.generation_authority_sha256 is not None)
                or (self.schema_version in (
                        ACCEPTANCE_SCHEMA, MOTIF_ACCEPTANCE_SCHEMA,
                        CLOSURE_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA)
                    and self.teacher_state_sha256 is not None)
                or (self.schema_version in (
                        MOTIF_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
                        EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
                        EXACT_MOTIF_ACCEPTANCE_SCHEMA, EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA)
                    and not _is_digest(self.generation_authority_sha256))
                or (self.schema_version in (
                        EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
                        EXACT_MOTIF_ACCEPTANCE_SCHEMA, EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA)
                    and not _is_digest(self.teacher_state_sha256))
                or (self.schema_version in (
                        ACCEPTANCE_SCHEMA, MOTIF_ACCEPTANCE_SCHEMA, EXACT_ACCEPTANCE_SCHEMA,
                        EXACT_MOTIF_ACCEPTANCE_SCHEMA)
                    and self.artifact_closures)
                or (self.schema_version in (
                        CLOSURE_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
                        EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
                        EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA)
                    and not self.artifact_closures)):
            _invalid()
        if self.artifact_closures:
            normalize_artifact_closures(self.artifact_closures)

    def _public_record(self) -> dict:
        names = (EXACT_CLOSURE_BINDING_FIELDS
                 if self.schema_version in (
                     EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
                     EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA)
                 else EXACT_BINDING_FIELDS if self.schema_version in (
                     EXACT_ACCEPTANCE_SCHEMA, EXACT_MOTIF_ACCEPTANCE_SCHEMA)
                 else CLOSURE_BINDING_FIELDS if self.schema_version == CLOSURE_ACCEPTANCE_SCHEMA
                 else MOTIF_CLOSURE_BINDING_FIELDS if self.schema_version == MOTIF_CLOSURE_ACCEPTANCE_SCHEMA
                 else _MOTIF_BINDING_FIELDS if self.schema_version == MOTIF_ACCEPTANCE_SCHEMA
                 else _BINDING_FIELDS)
        return {name: getattr(self, name) for name in names}

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical(self._public_record())).hexdigest()

    def to_record(self) -> dict:
        return {**self._public_record(), "binding_sha256": self.digest}

    @classmethod
    def from_record(cls, record) -> "ParsedAcceptedCandidateBinding":
        """Validate a historical v1/v2 record without restoring live authority."""
        return parse_accepted_candidate_binding(record)


_require_issued_binding, _raw_issue_binding = _new_binding_owner()


def _binding_schema(decision, generation_authority_sha256, teacher_state_sha256):
    from .atlas_retention_decision import (
        _issued_decision_generation_authority,
        _require_issued_decision_generation_authority,
    )

    required = _issued_decision_generation_authority(decision)
    if required is not None:
        if generation_authority_sha256 != required or not _is_digest(required):
            _invalid()
        _require_issued_decision_generation_authority(decision, required)
        return (EXACT_MOTIF_ACCEPTANCE_SCHEMA
                if teacher_state_sha256 is not None else MOTIF_ACCEPTANCE_SCHEMA)
    if generation_authority_sha256 is None:
        return ACCEPTANCE_SCHEMA
    if not _is_digest(generation_authority_sha256):
        _invalid()
    return EXACT_ACCEPTANCE_SCHEMA


def _artifact_closures(state, training_authorities):
    from bilqis_mlx.semantics.dependencies.closure import closure_digest, encode_closure_nodes

    closures = []
    for proof, authority in zip(state.step_proofs, training_authorities or ()):
        digest = getattr(authority, 'artifact_closure_sha256', None)
        if digest is not None:
            node_ids = {node.artifact_id for node in authority.artifact_nodes}
            if any(ref.kind.value == "ARTIFACT" and ref.key not in node_ids
                   for ref in authority.immediate_dependencies):
                _invalid()
            if (proof.artifact_closure_sha256 != digest
                    or closure_digest(authority.artifact_nodes) != digest):
                _invalid()
            closures.append({
                'step_index': proof.step_index,
                'training_authority_sha256': authority.digest,
                'artifact_closure_sha256': digest,
                'nodes': encode_closure_nodes(authority.artifact_nodes),
            })
        elif proof.artifact_closure_sha256 is not None:
            _invalid()
    return tuple(closures)


def _make_acceptance_minter(raw_issue):
    def mint_acceptance_binding(
            decision: CandidateRetentionDecision, state, *,
            run_id: str, generation: int, feature_sha256: str,
            training_authorities=None,
            source_authority_registry_sha256: str | None = None,
            teacher_state_sha256: str | None = None,
            generation_authority_sha256: str | None = None,
    ) -> AcceptedCandidateBinding:
        """Bind a C05-approved decision to the exact B12 optimizer state."""
        from .atlas_retention_decision import (
            _require_issued_decision,
        )

        state_digest = candidate_identity_digest(state)
        if type(decision) is not CandidateRetentionDecision:
            _invalid()
        _require_issued_decision(decision)
        decision.__post_init__()
        if (not decision.accepted or decision.candidate_generation != state_digest):
            _invalid()
        schema = _binding_schema(
            decision, generation_authority_sha256, teacher_state_sha256)
        source_anchors = _source_anchors(training_authorities, state)
        closures = _artifact_closures(state, training_authorities)
        if closures:
            schema = (MOTIF_CLOSURE_ACCEPTANCE_SCHEMA
                      if schema == MOTIF_ACCEPTANCE_SCHEMA
                      else EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA
                      if schema == EXACT_MOTIF_ACCEPTANCE_SCHEMA
                      else EXACT_CLOSURE_ACCEPTANCE_SCHEMA
                      if schema == EXACT_ACCEPTANCE_SCHEMA
                      else CLOSURE_ACCEPTANCE_SCHEMA)
        values = [
            ("run_id", run_id), ("generation", generation),
            ("candidate_identity_sha256", state_digest),
            ("parent_candidate_identity_sha256", decision.parent_generation),
            ("feature_sha256", feature_sha256),
            ("optimizer_step", state.optimizer_step),
            ("retention_reason", decision.reason),
            ("step_proof_sha256", tuple(proof.digest for proof in state.step_proofs)),
            ("decision_sha256", decision.digest),
            ("evidence_sha256", decision.evidence_sha256),
            ("policy_sha256", decision.policy_sha256),
            ("source_anchors", source_anchors),
            ("source_authority_registry_sha256",
             source_authority_registry_sha256),
        ]
        values.append(("artifact_closures", closures))
        values.append(("teacher_state_sha256", teacher_state_sha256))
        if schema in (
                MOTIF_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
                EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
                EXACT_MOTIF_ACCEPTANCE_SCHEMA, EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA):
            values.append(("generation_authority_sha256", generation_authority_sha256))
        else:
            values.append(("generation_authority_sha256", None))
        values.append(("schema_version", schema))
        return raw_issue(tuple(values))

    return mint_acceptance_binding


mint_acceptance_binding = _make_acceptance_minter(_raw_issue_binding)
del _raw_issue_binding
