"""Strict B13.1 generation records over the integrated B12 retained state."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from bilqis_mlx.data_plane import DataPlaneError

from .motif.codec import snapshot_from_record, snapshot_to_record
from .sidecar_contracts import validate_identity_sidecars
from .generation_manifest import (
    ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA, BAMF_BUNDLE_SCHEMA,
    BamfGenerationManifest, OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
    OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA, TRANSITION_SCHEMA, _hex, canonical,
    invalid, sha, validate_generation_identity, validate_transition,
)

LEGACY_BAMF_POINTER_SCHEMA = "bilqis.mlx.bamf-generation-pointer/v1"
BAMF_POINTER_SCHEMA = "bilqis.mlx.bamf-generation-pointer/v2"
SIDECARS = MappingProxyType({
    "semantic_abi": "semantic-abi.json",
    "motif_allocation": "motif-allocation.json",
    "plasticity_policy": "plasticity-policy.json",
    "compiler_features": "compiler-features.json",
    "correction_frontier": "correction-frontier.json",
    "teacher_state": "teacher-state.json",
    "evaluation_contract": "evaluation-contract.json",
    "baseline_evidence": "baseline-evidence.json",
    "learning_health_state": "learning-health-state.json",
    "championship_state": "championship-state.json",
    "step_proofs": "step-proofs.json",
    "run_identity": "run-identity.json",
    "outbox": "outbox.json",
})

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
    learning_health_state: Mapping | None = None
    championship_state: Mapping | None = None


@dataclass(frozen=True)
class CompleteStudent(BamfBundleCandidate):
    """Complete immutable generation with exact B12 retained custody.

    Instances normally come from a custody-validated cold load. B13 may also
    materialize the just-serialized child in memory for same-process outbox
    reconciliation; persisted retry/recovery still performs a full cold load.
    """


def validate_sidecars(extents, provenance, records: Mapping):
    from bilqis_mlx.learning.atlas_engram import INITIAL_MOTIF_CAPACITY
    from bilqis_mlx.learning.atlas_plasticity import PlasticityPolicy
    optional = {
        "run_identity", "baseline_evidence", "learning_health_state",
        "championship_state",
    }
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
    if "learning_health_state" in records:
        from bilqis_mlx.diagnostics.learning_health import validate_learning_health_state
        validate_learning_health_state(dict(records["learning_health_state"]))
    if "championship_state" in records:
        from bilqis_mlx.learning.capability_championship_state import (
            validate_championship_state,
        )
        validate_championship_state(dict(records["championship_state"]))
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
    if candidate.learning_health_state is not None:
        from bilqis_mlx.diagnostics.learning_health import validate_learning_health_state
        state = dict(candidate.learning_health_state)
        validate_learning_health_state(state)
        records["learning_health_state"] = state
    if candidate.championship_state is not None:
        from bilqis_mlx.learning.capability_championship_state import (
            validate_championship_state,
        )
        state = dict(candidate.championship_state)
        validate_championship_state(state)
        records["championship_state"] = state
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
         if candidate.baseline_evidence is not None else None),
        (dict(candidate.learning_health_state)
         if candidate.learning_health_state is not None else None),
        (dict(candidate.championship_state)
         if candidate.championship_state is not None else None))
