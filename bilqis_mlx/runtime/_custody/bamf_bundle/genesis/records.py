"""Immutable B13 generation-zero identity and bootstrap binding records."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Mapping

from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_for_canonical_consumer,
)
from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters

from ..records import canonical, invalid, sha
from ..run_identity import BamfRunIdentity, RUN_IDENTITY_SCHEMA

INITIAL_BINDING_SCHEMA = "bilqis.mlx.bamf-initial-generation-binding/v1"
_INITIAL_BINDING_ISSUER = object()


def _hex(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


@dataclass(frozen=True)
class InitialGenerationBinding:
    """Live B13 capability for exactly one generation-zero bundle."""

    run_id: str
    generation: int
    run_identity_sha256: str
    candidate_identity_sha256: str
    optimizer_hyperparameters_sha256: str
    feature_sha256: str
    optimizer_step: int
    schema_version: str = INITIAL_BINDING_SCHEMA
    _issuance: object = field(init=False, default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if (getattr(self, "_issuance", None) is not _INITIAL_BINDING_ISSUER
                or not isinstance(self.run_id, str) or not self.run_id
                or self.generation != 0 or self.optimizer_step != 0
                or self.schema_version != INITIAL_BINDING_SCHEMA
                or any(not _hex(value) for value in (
                    self.run_identity_sha256, self.candidate_identity_sha256,
                    self.optimizer_hyperparameters_sha256, self.feature_sha256))):
            invalid("BAMF_INITIAL_GENERATION_BINDING_INVALID")

    def _public_record(self) -> dict:
        return {name: getattr(self, name) for name in (
            "run_id", "generation", "run_identity_sha256",
            "candidate_identity_sha256", "optimizer_hyperparameters_sha256",
            "feature_sha256", "optimizer_step",
            "schema_version")}

    @property
    def digest(self) -> str:
        return sha(canonical(self._public_record()))

    def to_record(self) -> dict:
        return {**self._public_record(), "binding_sha256": self.digest}

    @classmethod
    def from_record(cls, record: Mapping) -> "ParsedInitialGenerationBinding":
        names = {
            "run_id", "generation", "run_identity_sha256",
            "candidate_identity_sha256", "optimizer_hyperparameters_sha256",
            "feature_sha256", "optimizer_step",
            "schema_version",
        }
        if not isinstance(record, Mapping) or set(record) != names | {"binding_sha256"}:
            invalid("BAMF_INITIAL_GENERATION_BINDING_INVALID")
        payload = {name: record[name] for name in names}
        if (payload["schema_version"] != INITIAL_BINDING_SCHEMA
                or not isinstance(payload["run_id"], str) or not payload["run_id"]
                or payload["generation"] != 0 or payload["optimizer_step"] != 0
                or any(not _hex(payload[name]) for name in (
                    "run_identity_sha256", "candidate_identity_sha256",
                    "optimizer_hyperparameters_sha256", "feature_sha256"))
                or record["binding_sha256"] != sha(canonical(payload))):
            invalid("BAMF_INITIAL_GENERATION_BINDING_INVALID")
        return ParsedInitialGenerationBinding(payload)


@dataclass(frozen=True)
class ParsedInitialGenerationBinding:
    """Verified historical bootstrap evidence, never a live publication token."""

    fields: dict

    def __getattr__(self, name: str):
        if name in self.fields:
            return self.fields[name]
        raise AttributeError(name)

    @property
    def digest(self) -> str:
        return sha(canonical(self.fields))


def optimizer_hyperparameters_digest(hyperparameters) -> str:
    if type(hyperparameters) is not AdamWHyperparameters:
        invalid("BAMF_INITIAL_GENERATION_BINDING_INVALID")
    hyperparameters.__post_init__()
    return sha(canonical(asdict(hyperparameters)))


def _candidate_identity_payload(candidate, *, allow_missing_run_identity: bool) -> dict:
    from ..motif.codec import snapshot_to_record

    state = candidate.retained_state
    identity = candidate.run_identity
    try:
        if identity is None:
            if not allow_missing_run_identity:
                invalid("BAMF_INITIAL_GENERATION_BINDING_INVALID")
            identity_digest = None
        else:
            identity_digest = identity.digest
        payload = {
            "run_id": candidate.run_id,
            "generation": candidate.generation,
            "parent_manifest_sha256": candidate.parent_manifest_sha256,
            "run_identity_sha256": identity_digest,
            "optimizer_state_sha256": candidate_identity_for_canonical_consumer(state),
            "optimizer_hyperparameters_sha256": optimizer_hyperparameters_digest(
                candidate.optimizer_hyperparameters),
            "implementation_sha256": candidate.implementation_sha256,
            "topology_sha256": candidate.topology.digest,
            "extents_sha256": candidate.extents.digest,
            "provenance_sha256": candidate.provenance.digest,
            "semantic_abi": dict(candidate.semantic_abi),
            "compiler_features": dict(candidate.compiler_features),
            "correction_frontier": dict(candidate.correction_frontier),
            "teacher_state": dict(candidate.teacher_state),
            "evaluation_contract": dict(candidate.evaluation_contract),
            "transition": dict(candidate.transition),
            "plasticity_policy": state.policy.to_record(),
            "motif_allocation": snapshot_to_record(state.allocations),
            "step_proofs": [proof.to_record() for proof in state.step_proofs],
            "state_schema_version": state.schema_version,
        }
        if candidate.baseline_evidence is not None:
            payload["baseline_evidence"] = dict(candidate.baseline_evidence)
        return payload
    except (AttributeError, KeyError, TypeError, ValueError):
        invalid("BAMF_INITIAL_GENERATION_BINDING_INVALID")


def initial_generation_candidate_identity_digest(candidate) -> str:
    """Digest every authority-relevant field of one exact generation-zero candidate."""
    return sha(canonical(_candidate_identity_payload(
        candidate, allow_missing_run_identity=False)))


def successor_candidate_identity_digest(candidate) -> str:
    """Digest an exact successor while preserving historical missing run identity."""
    return sha(canonical(_candidate_identity_payload(
        candidate, allow_missing_run_identity=True)))


def _mint_initial_generation_binding(candidate) -> InitialGenerationBinding:
    """Create the live binding only for the owner-replayed B13 issuance path."""
    identity = candidate.run_identity
    binding = object.__new__(InitialGenerationBinding)
    for name, value in (
            ("run_id", candidate.run_id), ("generation", 0),
            ("run_identity_sha256", identity.digest),
            ("candidate_identity_sha256",
             initial_generation_candidate_identity_digest(candidate)),
            ("optimizer_hyperparameters_sha256",
             optimizer_hyperparameters_digest(candidate.optimizer_hyperparameters)),
            ("feature_sha256", candidate.extents.factor_map_digest),
            ("optimizer_step", candidate.retained_state.optimizer_step),
            ("schema_version", INITIAL_BINDING_SCHEMA),
            ("_issuance", _INITIAL_BINDING_ISSUER)):
        object.__setattr__(binding, name, value)
    binding.__post_init__()
    return binding
