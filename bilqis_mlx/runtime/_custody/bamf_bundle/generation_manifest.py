"""Versioned B13 generation-manifest identity and transition law."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping

from bilqis_mlx.data_plane import DataPlaneError
from bilqis_mlx.errors import ErrorBus, SCHOOL

from .package_import_transition import (
    PACKAGE_IMPORT_TRANSITION_SCHEMA, validate_package_import_transition,
)
from .factory_release_adoption import (
    is_factory_release_adoption_transition,
    validate_factory_release_adoption_transition,
)
from .motif.transition import (
    is_motif_allocation_transition,
    validate_motif_allocation_transition,
)

BAMF_BUNDLE_SCHEMA = "bilqis.mlx.bamf-generation-bundle/v2"
ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA = "bilqis.mlx.bamf-generation-bundle/v3"
OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA = "bilqis.mlx.bamf-generation-bundle/v4"
OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA = "bilqis.mlx.bamf-generation-bundle/v5"
TRANSITION_SCHEMA = "bilqis.mlx.bamf-generation-transition/v1"
_TRANSITIONS = frozenset({"INITIAL", "RETAINED_CANDIDATE", "PARAMETER_EXTENSION", "MODEL_SWAP"})



@dataclass(frozen=True)
class BamfGenerationManifest:
    run_id: str
    generation: int
    parent_manifest_sha256: str | None
    implementation_sha256: str
    topology: Mapping
    extents: Mapping
    provenance: Mapping
    tensors: Mapping
    optimizer: Mapping
    transition: Mapping
    sidecars: Mapping
    training_objective_ref: str | None = None
    training_objective_digest: str | None = None
    parent_acceptance_sha256: str | None = None
    schema: str = BAMF_BUNDLE_SCHEMA

    def __post_init__(self) -> None:
        validate_generation_identity(self.run_id, self.generation,
                                     self.parent_manifest_sha256, self.implementation_sha256)
        schemas = {
            BAMF_BUNDLE_SCHEMA, ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
            OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA,
            OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
        }
        objective_bound = self.schema in {
            OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA,
            OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
        }
        acceptance_bound = self.schema in {
            ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
            OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
        }
        if (self.schema not in schemas
                or any(not isinstance(value, Mapping) for value in (
                    self.topology, self.extents, self.provenance, self.tensors,
                    self.optimizer, self.transition, self.sidecars))):
            invalid()
        if objective_bound:
            from bilqis_mlx.runtime.training_objective import (
                current_training_objective,
            )
            objective = current_training_objective()
            if (self.training_objective_ref != objective.ref
                    or self.training_objective_digest != objective.digest):
                invalid("TRAINING_OBJECTIVE_CONTRACT_DRIFT")
        elif (self.training_objective_ref is not None
                or self.training_objective_digest is not None):
            invalid("TRAINING_OBJECTIVE_CONTRACT_UNBOUND")
        if ((not acceptance_bound and self.parent_acceptance_sha256 is not None)
                or (acceptance_bound
                    and ((self.generation == 0
                          and self.parent_acceptance_sha256 is not None)
                         or (self.generation > 0
                             and not _hex(self.parent_acceptance_sha256))))):
            invalid()
        validate_transition(self.generation, self.transition)

    def to_record(self) -> dict:
        record = {
            "schema": self.schema, "run_id": self.run_id,
            "generation": self.generation,
            "parent_manifest_sha256": self.parent_manifest_sha256,
            "implementation_sha256": self.implementation_sha256,
            "topology": dict(self.topology), "extents": dict(self.extents),
            "provenance": dict(self.provenance), "tensors": dict(self.tensors),
            "optimizer": dict(self.optimizer), "transition": dict(self.transition),
            "sidecars": dict(self.sidecars),
        }
        if self.schema in {
                OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA,
                OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA}:
            record["training_objective_ref"] = self.training_objective_ref
            record["training_objective_digest"] = self.training_objective_digest
        if self.schema in {
                ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
                OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA}:
            record["parent_acceptance_sha256"] = self.parent_acceptance_sha256
        return record

    @classmethod
    def from_record(cls, record: Mapping) -> "BamfGenerationManifest":
        base = {"schema", "run_id", "generation", "parent_manifest_sha256",
                "implementation_sha256", "topology", "extents", "provenance",
                "tensors", "optimizer", "transition", "sidecars"}
        schema = record.get("schema") if isinstance(record, Mapping) else None
        objective_bound = schema in {
            OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA,
            OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
        }
        acceptance_bound = schema in {
            ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
            OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
        }
        expected = base
        if objective_bound:
            expected |= {"training_objective_ref", "training_objective_digest"}
        if acceptance_bound:
            expected |= {"parent_acceptance_sha256"}
        if (not isinstance(record, Mapping) or set(record) != expected
                or schema not in {
                    BAMF_BUNDLE_SCHEMA, ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
                    OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA,
                    OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA}):
            invalid()
        return cls(
            record["run_id"], record["generation"], record["parent_manifest_sha256"],
            record["implementation_sha256"], record["topology"], record["extents"],
            record["provenance"], record["tensors"], record["optimizer"],
            record["transition"], record["sidecars"],
            training_objective_ref=record.get("training_objective_ref"),
            training_objective_digest=record.get("training_objective_digest"),
            parent_acceptance_sha256=record.get("parent_acceptance_sha256"),
            schema=schema)



def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _hex(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def invalid(code=DataPlaneError.BUNDLE_MANIFEST_INVALID):
    reason = code.value if isinstance(code, DataPlaneError) else str(code)
    ErrorBus.Raise(SCHOOL.STATE.HISTORICAL_ARTIFACT_INVALID, reason=reason)


def validate_generation_identity(run_id, generation, parent, implementation):
    if (not isinstance(run_id, str) or not run_id
            or type(generation) is not int or generation < 0
            or not _hex(implementation)
            or (parent is not None if generation == 0 else not _hex(parent))):
        invalid()


def validate_transition(generation: int, transition: Mapping) -> None:
    if is_motif_allocation_transition(transition):
        if generation == 0:
            invalid("BAMF_GENERATION_TRANSITION_INVALID")
        validate_motif_allocation_transition(transition)
        return
    if isinstance(transition, Mapping) and transition.get("schema") == PACKAGE_IMPORT_TRANSITION_SCHEMA:
        if generation == 0:
            invalid("BAMF_GENERATION_TRANSITION_INVALID")
        validate_package_import_transition(transition)
        return
    if is_factory_release_adoption_transition(transition):
        if generation == 0:
            invalid("BAMF_GENERATION_TRANSITION_INVALID")
        validate_factory_release_adoption_transition(transition)
        return
    if (set(transition) != {"schema", "kind", "invalidate_derived_caches"}
            or transition.get("schema") != TRANSITION_SCHEMA
            or transition.get("kind") not in _TRANSITIONS
            or type(transition.get("invalidate_derived_caches")) is not bool
            or (generation == 0) != (transition["kind"] == "INITIAL")
            or (transition["kind"] in {"PARAMETER_EXTENSION", "MODEL_SWAP"}
                and not transition["invalidate_derived_caches"])):
        invalid("BAMF_GENERATION_TRANSITION_INVALID")



__all__ = (
    "ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA", "BAMF_BUNDLE_SCHEMA",
    "BamfGenerationManifest", "OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA",
    "OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA", "TRANSITION_SCHEMA", "_hex",
    "canonical", "invalid", "sha", "validate_generation_identity",
    "validate_transition",
)
