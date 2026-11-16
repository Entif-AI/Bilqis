"""Strict B13.1 generation records over the integrated B12 retained state."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from bilqis_mlx.data_plane import DataPlaneError
from bilqis_mlx.errors import ErrorBus, SCHOOL

from .motif.codec import snapshot_from_record, snapshot_to_record
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
from .sidecar_contracts import validate_identity_sidecars

BAMF_BUNDLE_SCHEMA = "bilqis.mlx.bamf-generation-bundle/v2"
ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA = "bilqis.mlx.bamf-generation-bundle/v3"
LEGACY_BAMF_POINTER_SCHEMA = "bilqis.mlx.bamf-generation-pointer/v1"
BAMF_POINTER_SCHEMA = "bilqis.mlx.bamf-generation-pointer/v2"
TRANSITION_SCHEMA = "bilqis.mlx.bamf-generation-transition/v1"
SIDECARS = MappingProxyType({
    "semantic_abi": "semantic-abi.json",
    "motif_allocation": "motif-allocation.json",
    "plasticity_policy": "plasticity-policy.json",
    "compiler_features": "compiler-features.json",
    "correction_frontier": "correction-frontier.json",
    "teacher_state": "teacher-state.json",
    "evaluation_contract": "evaluation-contract.json",
    "baseline_evidence": "baseline-evidence.json",
    "step_proofs": "step-proofs.json",
    "run_identity": "run-identity.json",
    "outbox": "outbox.json",
})
_TRANSITIONS = frozenset({"INITIAL", "RETAINED_CANDIDATE", "PARAMETER_EXTENSION", "MODEL_SWAP"})


@dataclass(frozen=True)
class BamfBundleCandidate:
    run_id: str
    generation: int
    parent_manifest_sha256: str | None
    implementation_sha256: str
    topology: object
    extents: object
    retained_state: object
    optimizer_hyperparameters: object
    provenance: object
    semantic_abi: Mapping
    compiler_features: Mapping
    correction_frontier: Mapping
    teacher_state: Mapping
    evaluation_contract: Mapping
    transition: Mapping
    outbox: tuple
    run_identity: object | None = None
    baseline_evidence: Mapping | None = None


@dataclass(frozen=True)
class CompleteStudent(BamfBundleCandidate):
    """Complete immutable generation with exact B12 retained custody.

    Instances normally come from a custody-validated cold load. B13 may also
    materialize the just-serialized child in memory for same-process outbox
    reconciliation; persisted retry/recovery still performs a full cold load.
    """


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
    parent_acceptance_sha256: str | None = None
    schema: str = BAMF_BUNDLE_SCHEMA

    def __post_init__(self) -> None:
        validate_generation_identity(self.run_id, self.generation,
                                     self.parent_manifest_sha256, self.implementation_sha256)
        if (self.schema not in {BAMF_BUNDLE_SCHEMA, ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA}
                or any(not isinstance(value, Mapping) for value in (
                    self.topology, self.extents, self.provenance, self.tensors,
                    self.optimizer, self.transition, self.sidecars))
                or (self.schema == BAMF_BUNDLE_SCHEMA
                    and self.parent_acceptance_sha256 is not None)
                or (self.schema == ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA
                    and ((self.generation == 0 and self.parent_acceptance_sha256 is not None)
                         or (self.generation > 0 and not _hex(self.parent_acceptance_sha256))))):
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
        if self.schema == ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA:
            record["parent_acceptance_sha256"] = self.parent_acceptance_sha256
        return record

    @classmethod
    def from_record(cls, record: Mapping) -> "BamfGenerationManifest":
        base = {"schema", "run_id", "generation", "parent_manifest_sha256",
                "implementation_sha256", "topology", "extents", "provenance",
                "tensors", "optimizer", "transition", "sidecars"}
        schema = record.get("schema") if isinstance(record, Mapping) else None
        expected = base | ({"parent_acceptance_sha256"}
                           if schema == ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA else set())
        if (not isinstance(record, Mapping) or set(record) != expected
                or schema not in {BAMF_BUNDLE_SCHEMA, ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA}):
            invalid()
        return cls(
            record["run_id"], record["generation"], record["parent_manifest_sha256"],
            record["implementation_sha256"], record["topology"], record["extents"],
            record["provenance"], record["tensors"], record["optimizer"],
            record["transition"], record["sidecars"],
            record.get("parent_acceptance_sha256"), schema)


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


def validate_sidecars(extents, provenance, records: Mapping):
    from bilqis_mlx.learning.atlas_engram import INITIAL_MOTIF_CAPACITY
    from bilqis_mlx.learning.atlas_plasticity import PlasticityPolicy
    optional = {"run_identity", "baseline_evidence"}
    required = set(SIDECARS) - optional
    if (not isinstance(records, Mapping)
            or not required <= set(records) <= set(SIDECARS)):
        invalid()
    if (any(not isinstance(records[name], Mapping) for name in records
            if name != "outbox") or type(records["outbox"]) not in (list, tuple)):
        invalid()
    proofs = records.get("step_proofs", {
        "schema": "bilqis.mlx.bamf-step-proofs/v1", "proofs": []})
    if (set(proofs) != {"schema", "proofs"}
            or proofs["schema"] != "bilqis.mlx.bamf-step-proofs/v1"
            or not isinstance(proofs["proofs"], list)):
        invalid()
    validate_identity_sidecars(extents, provenance, records, invalid)
    if "baseline_evidence" in records:
        from bilqis_mlx.runtime.baseline.lifecycle import BaselineLedger
        BaselineLedger.from_record(dict(records["baseline_evidence"]))
    try:
        motif = snapshot_from_record(records["motif_allocation"])
        policy = PlasticityPolicy.from_record(records["plasticity_policy"])
    except (TypeError, ValueError, KeyError) as exc:
        invalid("BAMF_SIDECAR_RECORD_INVALID")
    if (motif.manifest.digest != extents.motif_key_map_digest
            or motif.manifest.capacity // INITIAL_MOTIF_CAPACITY != extents.motif_page_count
            or any(row.bank_index >= extents.semantic_bank_count for row in policy.row_ages)):
        invalid()
    return motif, policy


def sidecar_records(candidate: BamfBundleCandidate) -> dict:
    from bilqis_mlx.learning.atlas_candidate import CandidateState
    from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters
    from bilqis_mlx.runtime.checkpoint_outbox import ordinary_outbox_lineage, with_delivery_outbox
    from bilqis_mlx.runtime.model_topology_v2 import GenerationExtents, GenerationProvenance, ModelTopologySpecV2
    if (type(candidate) not in (BamfBundleCandidate, CompleteStudent)
            or type(candidate.retained_state) is not CandidateState
            or type(candidate.topology) is not ModelTopologySpecV2
            or type(candidate.extents) is not GenerationExtents
            or type(candidate.optimizer_hyperparameters) is not AdamWHyperparameters
            or type(candidate.provenance) is not GenerationProvenance
            or not _hex(candidate.implementation_sha256)):
        invalid()
    validate_generation_identity(candidate.run_id, candidate.generation,
                                 candidate.parent_manifest_sha256, candidate.implementation_sha256)
    candidate.retained_state.__post_init__()
    validate_transition(candidate.generation, candidate.transition)
    lineage = {"run_id": candidate.run_id, "generation": candidate.generation}
    if type(candidate) is CompleteStudent:
        outbox = list(candidate.outbox)
        if not outbox or not ordinary_outbox_lineage(lineage, outbox):
            invalid("BAMF_OUTBOX_LINEAGE_INVALID")
    else:
        outbox = with_delivery_outbox(lineage, candidate.outbox)["delivery_outbox"]
    records = {
        "semantic_abi": dict(candidate.semantic_abi),
        "motif_allocation": snapshot_to_record(candidate.retained_state.allocations),
        "plasticity_policy": candidate.retained_state.policy.to_record(),
        "compiler_features": dict(candidate.compiler_features),
        "correction_frontier": dict(candidate.correction_frontier),
        "teacher_state": dict(candidate.teacher_state),
        "evaluation_contract": dict(candidate.evaluation_contract),
        "step_proofs": {
            "schema": "bilqis.mlx.bamf-step-proofs/v1",
            "proofs": [proof.to_record()
                       for proof in candidate.retained_state.step_proofs],
        },
        "outbox": outbox,
    }
    if candidate.baseline_evidence is not None:
        from bilqis_mlx.runtime.baseline.lifecycle import BaselineLedger
        baseline = BaselineLedger.from_record(dict(candidate.baseline_evidence))
        records["baseline_evidence"] = baseline.to_record()
    if candidate.run_identity is not None:
        from .genesis import BamfRunIdentity
        if type(candidate.run_identity) is not BamfRunIdentity:
            invalid("BAMF_RUN_IDENTITY_INVALID")
        records["run_identity"] = candidate.run_identity.to_record()
    validate_sidecars(candidate.extents, candidate.provenance, records)
    return records


def complete_student_from_candidate(candidate: BamfBundleCandidate) -> CompleteStudent:
    """Materialize the exact in-memory child that deterministic B13 serialization writes."""
    if type(candidate) is not BamfBundleCandidate:
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    records = sidecar_records(candidate)
    return CompleteStudent(
        candidate.run_id, candidate.generation, candidate.parent_manifest_sha256,
        candidate.implementation_sha256, candidate.topology, candidate.extents,
        candidate.retained_state, candidate.optimizer_hyperparameters,
        candidate.provenance, dict(candidate.semantic_abi),
        dict(candidate.compiler_features), dict(candidate.correction_frontier),
        dict(candidate.teacher_state), dict(candidate.evaluation_contract),
        dict(candidate.transition), tuple(records["outbox"]), candidate.run_identity,
        (dict(candidate.baseline_evidence)
         if candidate.baseline_evidence is not None else None))
