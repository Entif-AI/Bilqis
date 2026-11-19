"""Versioned optimizer-step custody proofs."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from .common import (
    CLOSURE_STEP_PROOF_SCHEMA,
    LEGACY_STEP_PROOF_SCHEMA, LOGICAL_BATCH_STEP_PROOF_SCHEMA,
    LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA,
    OBJECTIVE_CLOSURE_STEP_PROOF_SCHEMA,
    OBJECTIVE_LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA,
    OBJECTIVE_LOGICAL_BATCH_STEP_PROOF_SCHEMA,
    OBJECTIVE_MINIMAL_STEP_PROOF_SCHEMA, OBJECTIVE_STEP_PROOF_SCHEMA,
    PREVIOUS_STEP_PROOF_SCHEMA, STEP_PROOF_SCHEMA,
    invalid, is_digest,
)

_LEGACY_FIELDS = ("step_index", "provenance_sha256", "participation_sha256",
                  "mask_sha256", "parameter_names", "loss_bearing", "schema_version")
_V2_FIELDS = _LEGACY_FIELDS[:-1] + ("source_release_sha256",
    "training_batch_sha256", "target_capability_id", "training_authority_sha256",
    "schema_version")
_V3_FIELDS = _V2_FIELDS[:-1] + (
    "source_family_id", "episode_id", "schema_version")
_V4_FIELDS = _V2_FIELDS[:-1] + (
    "training_authority_members", "schema_version")
_V5_FIELDS = _V3_FIELDS[:-1] + (
    "artifact_closure_sha256", "schema_version")
_V6_FIELDS = _V4_FIELDS[:-1] + (
    "artifact_closure_sha256", "schema_version")
_V7_FIELDS = _V3_FIELDS[:-1] + (
    "training_objective_digest", "schema_version")
_V8_FIELDS = _V4_FIELDS[:-1] + (
    "training_objective_digest", "schema_version")
_V9_FIELDS = _V5_FIELDS[:-1] + (
    "training_objective_digest", "schema_version")
_V10_FIELDS = _V6_FIELDS[:-1] + (
    "training_objective_digest", "schema_version")
_V11_FIELDS = _LEGACY_FIELDS[:-1] + (
    "training_objective_digest", "schema_version")
_FIELDS_BY_SCHEMA = MappingProxyType({
    LEGACY_STEP_PROOF_SCHEMA: _LEGACY_FIELDS,
    PREVIOUS_STEP_PROOF_SCHEMA: _V2_FIELDS,
    STEP_PROOF_SCHEMA: _V3_FIELDS,
    LOGICAL_BATCH_STEP_PROOF_SCHEMA: _V4_FIELDS,
    CLOSURE_STEP_PROOF_SCHEMA: _V5_FIELDS,
    LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA: _V6_FIELDS,
    OBJECTIVE_STEP_PROOF_SCHEMA: _V7_FIELDS,
    OBJECTIVE_LOGICAL_BATCH_STEP_PROOF_SCHEMA: _V8_FIELDS,
    OBJECTIVE_CLOSURE_STEP_PROOF_SCHEMA: _V9_FIELDS,
    OBJECTIVE_LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA: _V10_FIELDS,
    OBJECTIVE_MINIMAL_STEP_PROOF_SCHEMA: _V11_FIELDS,
})
_LOGICAL_BATCH_MIN_MEMBERS = 2
_LOGICAL_BATCH_MEMBER_WIDTH = 3


def _valid_logical_batch_member(item) -> bool:
    if type(item) is not tuple or len(item) != _LOGICAL_BATCH_MEMBER_WIDTH:
        return False
    digest, family, episode = item
    return (is_digest(digest)
            and isinstance(family, str) and bool(family)
            and isinstance(episode, str) and bool(episode))

_CLOSURE_SCHEMAS = frozenset({
    CLOSURE_STEP_PROOF_SCHEMA,
    LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA,
    OBJECTIVE_CLOSURE_STEP_PROOF_SCHEMA,
    OBJECTIVE_LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA,
})
_OBJECTIVE_SCHEMAS = frozenset({
    OBJECTIVE_STEP_PROOF_SCHEMA,
    OBJECTIVE_LOGICAL_BATCH_STEP_PROOF_SCHEMA,
    OBJECTIVE_CLOSURE_STEP_PROOF_SCHEMA,
    OBJECTIVE_LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA,
    OBJECTIVE_MINIMAL_STEP_PROOF_SCHEMA,
})
_MINIMAL_SCHEMAS = frozenset({
    LEGACY_STEP_PROOF_SCHEMA, OBJECTIVE_MINIMAL_STEP_PROOF_SCHEMA,
})
_SINGLE_AUTHORITY_SCHEMAS = frozenset({
    STEP_PROOF_SCHEMA, CLOSURE_STEP_PROOF_SCHEMA,
    OBJECTIVE_STEP_PROOF_SCHEMA, OBJECTIVE_CLOSURE_STEP_PROOF_SCHEMA,
})
_LOGICAL_AUTHORITY_SCHEMAS = frozenset({
    LOGICAL_BATCH_STEP_PROOF_SCHEMA,
    LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA,
    OBJECTIVE_LOGICAL_BATCH_STEP_PROOF_SCHEMA,
    OBJECTIVE_LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA,
})


def _validate_core(proof) -> None:
    if (type(proof.step_index) is not int or proof.step_index < 1
            or not is_digest(proof.provenance_sha256)
            or not is_digest(proof.participation_sha256)
            or not is_digest(proof.mask_sha256)
            or type(proof.parameter_names) is not tuple
            or proof.parameter_names != tuple(sorted(set(proof.parameter_names)))
            or any(not isinstance(name, str) or not name
                   for name in proof.parameter_names)
            or type(proof.loss_bearing) is not bool
            or proof.schema_version not in _FIELDS_BY_SCHEMA):
        invalid()


def _validate_optional_bindings(proof) -> None:
    if ((proof.schema_version in _OBJECTIVE_SCHEMAS
         and not is_digest(proof.training_objective_digest))
            or (proof.schema_version not in _OBJECTIVE_SCHEMAS
                and proof.training_objective_digest is not None)):
        invalid()
    if ((proof.schema_version in _CLOSURE_SCHEMAS
         and not is_digest(proof.artifact_closure_sha256))
            or (proof.schema_version not in _CLOSURE_SCHEMAS
                and proof.artifact_closure_sha256 is not None)):
        invalid()


def _validate_authority_identity(proof) -> None:
    authority = (
        proof.source_release_sha256, proof.training_batch_sha256,
        proof.target_capability_id, proof.training_authority_sha256)
    if proof.schema_version in _MINIMAL_SCHEMAS:
        if (authority != (None, None, None, None)
                or proof.source_family_id is not None
                or proof.episode_id is not None
                or proof.training_authority_members):
            invalid()
        return
    if (not is_digest(proof.source_release_sha256)
            or not is_digest(proof.training_batch_sha256)
            or not isinstance(proof.target_capability_id, str)
            or not proof.target_capability_id
            or not is_digest(proof.training_authority_sha256)):
        invalid()


def _validate_authority_shape(proof) -> None:
    if proof.schema_version == PREVIOUS_STEP_PROOF_SCHEMA:
        if (proof.source_family_id is not None or proof.episode_id is not None
                or proof.training_authority_members):
            invalid()
        return
    if proof.schema_version in _SINGLE_AUTHORITY_SCHEMAS:
        if (not isinstance(proof.source_family_id, str) or not proof.source_family_id
                or not isinstance(proof.episode_id, str) or not proof.episode_id
                or proof.training_authority_members):
            invalid()
        return
    if proof.schema_version not in _LOGICAL_AUTHORITY_SCHEMAS:
        return
    members = proof.training_authority_members
    if (proof.source_family_id is not None or proof.episode_id is not None
            or type(members) is not tuple
            or len(members) < _LOGICAL_BATCH_MIN_MEMBERS
            or any(not _valid_logical_batch_member(item) for item in members)
            or len({item[0] for item in members}) != len(members)
            or len({item[1] for item in members}) != 1):
        invalid()


@dataclass(frozen=True)
class CandidateStepProof:
    """Owner-bound proof of one executed optimizer step.

    The proof records digests of the owner-issued execution provenance and its
    derived participation and mask. It never stores a caller mask mapping.
    """

    step_index: int
    provenance_sha256: str
    participation_sha256: str
    mask_sha256: str
    parameter_names: tuple[str, ...]
    loss_bearing: bool
    source_release_sha256: str | None = None
    training_batch_sha256: str | None = None
    target_capability_id: str | None = None
    training_authority_sha256: str | None = None
    source_family_id: str | None = None
    episode_id: str | None = None
    schema_version: str = STEP_PROOF_SCHEMA
    training_authority_members: tuple[tuple[str, str, str], ...] = ()
    artifact_closure_sha256: str | None = None
    training_objective_digest: str | None = None

    def __post_init__(self) -> None:
        _validate_core(self)
        _validate_optional_bindings(self)
        _validate_authority_identity(self)
        _validate_authority_shape(self)

    @property
    def digest(self) -> str:
        """Content identity of one owner-bound step proof."""
        payload = json.dumps(self._payload(), sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _payload(self) -> dict:
        names = _FIELDS_BY_SCHEMA.get(self.schema_version)
        if names is None:
            invalid()
        return {name: getattr(self, name) for name in names}

    def to_record(self) -> dict:
        """Durable custody record of one owner-bound step proof."""
        record = self._payload()
        record["proof_sha256"] = self.digest
        return record

    @classmethod
    def from_record(cls, record) -> "CandidateStepProof":
        schema = record.get("schema_version") if isinstance(record, dict) else None
        names = _FIELDS_BY_SCHEMA.get(schema, ())
        if (not isinstance(record, dict)
                or set(record) != set(names) | {"proof_sha256"}):
            invalid()
        values = {}
        for name in names:
            value = record[name]
            if name == "parameter_names":
                value = tuple(value)
            elif name == "training_authority_members":
                value = tuple(tuple(item) for item in value)
            values[name] = value
        proof = cls(**values)
        if record["proof_sha256"] != proof.digest:
            invalid()
        return proof
