"""Portable B11 participation evidence for distributed C08 execution."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Mapping

import mlx.core as mx

from bilqis_mlx.runtime.atlas_model import require_bamf_loss_execution
from bilqis_mlx.runtime.atlas_training_authority import (
    BamfTrainingAuthority, extend_training_dependencies,
)
from bilqis_mlx.runtime._atlas_resources.distributed_contracts import _sha
from bilqis_mlx.semantics.cognitive_dependencies import (
    ArtifactKind, ArtifactNode, DependencyKind, DependencyRef,
)

from .c08_gradient_accumulation import _invalid


_TRAINING_DEPENDENCY_RECORD_WIDTH = 2


@dataclass(frozen=True)
class DistributedB11Evidence:
    manifest_digest: str
    rank: int
    row_index: int
    row_id: str
    generation_binding: str
    custody_run_id: str
    custody_generation: int
    custody_manifest_sha256: str
    visible_identity_rows: tuple[tuple[int, int], ...]
    feedback_identity_rows: tuple[tuple[int, int], ...]
    semantic_denominator_identity_rows: tuple[tuple[int, int], ...]
    feature_rows: tuple[tuple[str, int], ...]
    semantic_denominator_feature_rows: tuple[tuple[str, int], ...]
    role_read_feature_rows: tuple[tuple[str, int], ...]
    local_slot_rows: tuple[int, ...]
    dense_parameter_names: tuple[str, ...]
    motif_slots: tuple[int, ...]
    training_authority_digest: str
    training_dependency_rows: tuple[tuple[str, str], ...]
    training_artifact_json: str
    schema_version: str = "bilqis.c08.distributed-b11-evidence/v2"

    def __post_init__(self) -> None:
        ordered = (
            self.visible_identity_rows, self.feedback_identity_rows,
            self.semantic_denominator_identity_rows, self.feature_rows,
            self.semantic_denominator_feature_rows, self.role_read_feature_rows,
            self.local_slot_rows, self.dense_parameter_names, self.motif_slots,
            self.training_dependency_rows)
        if (not all(isinstance(value, str) and value for value in (
                self.manifest_digest, self.row_id, self.generation_binding,
                self.custody_run_id, self.custody_manifest_sha256,
                self.training_authority_digest, self.training_artifact_json))
                or any(not _sha(value) for value in (
                    self.manifest_digest, self.generation_binding,
                    self.custody_manifest_sha256, self.training_authority_digest))
                or type(self.rank) is not int or self.rank < 0
                or type(self.row_index) is not int or self.row_index < 0
                or type(self.custody_generation) is not int
                or self.custody_generation < 0
                or any(type(value) is not tuple for value in ordered)
                or any(value != tuple(sorted(set(value))) for value in ordered)
                or any(len(item) != _TRAINING_DEPENDENCY_RECORD_WIDTH
                       or item[0] not in {kind.value for kind in DependencyKind}
                       or not item[1]
                       for item in self.training_dependency_rows)
                or self.schema_version != "bilqis.c08.distributed-b11-evidence/v2"):
            _invalid("C08_DISTRIBUTED_B11_EVIDENCE_INVALID")
        try:
            _load_training_artifacts(self.training_artifact_json)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            _invalid("C08_DISTRIBUTED_B11_TRAINING_EXTENSION_INVALID")

    @property
    def digest(self) -> str:
        payload = asdict(self)
        wire = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(wire.encode()).hexdigest()


def issue_distributed_b11_evidence(
        execution, *, manifest_digest: str, rank: int, row_index: int,
        row_id: str, base_training_authority=None) -> DistributedB11Evidence:
    """Project only participation/custody facts from a genuine local B11 witness."""
    execution = require_bamf_loss_execution(execution)
    authority = execution.training_authority
    if authority is None:
        _invalid("C08_DISTRIBUTED_TRAINING_AUTHORITY_REQUIRED")
    dependencies = authority.immediate_dependencies
    artifact_nodes = authority.artifact_nodes
    if base_training_authority is not None:
        if type(base_training_authority) is not BamfTrainingAuthority:
            _invalid("C08_DISTRIBUTED_B11_BASE_AUTHORITY_INVALID")
        base_training_authority.__post_init__()
        base_dependencies = set(base_training_authority.immediate_dependencies)
        dependencies = tuple(
            ref for ref in authority.immediate_dependencies
            if ref not in base_dependencies)
        base_nodes = {
            node.artifact_id: node for node in base_training_authority.artifact_nodes}
        artifact_nodes = tuple(
            node for node in authority.artifact_nodes
            if node.artifact_id not in base_nodes)
        reconstructed = extend_training_dependencies(
            base_training_authority, dependencies, artifact_nodes=artifact_nodes)
        if reconstructed.digest != authority.digest:
            _invalid("C08_DISTRIBUTED_B11_BASE_AUTHORITY_DRIFT")
    return DistributedB11Evidence(
        manifest_digest, rank, row_index, row_id,
        execution.output.generation_binding, execution.custody_run_id,
        execution.custody_generation, execution.custody_manifest_sha256,
        execution.visible_identity_rows, execution.feedback_identity_rows,
        execution.semantic_denominator_identity_rows, execution.feature_rows,
        execution.semantic_denominator_feature_rows,
        execution.role_read_feature_rows, execution.local_slot_rows,
        execution.dense_parameter_names,
        tuple(sorted({slot for read in execution.motif_reads
                      for slot in read.participating_slots})),
        authority.digest,
        tuple((ref.kind.value, ref.key) for ref in dependencies),
        _training_artifact_json(artifact_nodes))


def _training_artifact_json(nodes: tuple[ArtifactNode, ...]) -> str:
    return json.dumps([{
        "artifact_id": node.artifact_id,
        "kind": node.kind.value,
        "content_digest": node.content_digest,
        "eligible": node.eligible,
        "immediate_dependencies": [
            [ref.kind.value, ref.key] for ref in node.immediate_dependencies],
        "impact": node.impact,
        "exigency": node.exigency,
    } for node in nodes], sort_keys=True, separators=(",", ":"))


def _load_training_artifacts(payload: str) -> tuple[ArtifactNode, ...]:
    records = json.loads(payload)
    if not isinstance(records, list):
        _invalid("C08_DISTRIBUTED_B11_TRAINING_EXTENSION_INVALID")
    return tuple(ArtifactNode(
        record["artifact_id"], ArtifactKind(record["kind"]),
        record["content_digest"], record["eligible"],
        tuple(sorted(DependencyRef(
            DependencyKind(ref[0]), ref[1])
            for ref in record["immediate_dependencies"])),
        record["impact"], record["exigency"])
        for record in records)


def evidence_record(evidence: DistributedB11Evidence) -> dict:
    evidence.__post_init__()
    record = asdict(evidence)
    record["digest"] = evidence.digest
    return record


def load_evidence_record(record: Mapping) -> DistributedB11Evidence:
    if not isinstance(record, Mapping):
        _invalid("C08_DISTRIBUTED_B11_EVIDENCE_RECORD_INVALID")
    try:
        fields = {key: value for key, value in record.items() if key != "digest"}
        for key in (
                "visible_identity_rows", "feedback_identity_rows",
                "semantic_denominator_identity_rows", "feature_rows",
                "semantic_denominator_feature_rows", "role_read_feature_rows",
                "training_dependency_rows"):
            fields[key] = tuple(tuple(item) for item in fields[key])
        for key in ("local_slot_rows", "dense_parameter_names", "motif_slots"):
            fields[key] = tuple(fields[key])
        evidence = DistributedB11Evidence(**fields)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        _invalid("C08_DISTRIBUTED_B11_EVIDENCE_RECORD_INVALID")
    if record.get("digest") != evidence.digest:
        _invalid("C08_DISTRIBUTED_B11_EVIDENCE_DIGEST_DRIFT")
    return evidence


def evidence_training_extension(
        evidence: DistributedB11Evidence,
) -> tuple[tuple[DependencyRef, ...], tuple[ArtifactNode, ...]]:
    """Decode only the execution-observed extension of coordinator-owned authority."""
    if type(evidence) is not DistributedB11Evidence:
        _invalid("C08_DISTRIBUTED_B11_EVIDENCE_REQUIRED")
    evidence.__post_init__()
    dependencies = tuple(DependencyRef(
        DependencyKind(kind), key) for kind, key in evidence.training_dependency_rows)
    return dependencies, _load_training_artifacts(evidence.training_artifact_json)


def all_gather_b11_evidence(local: tuple[DistributedB11Evidence, ...], group):
    """Gather variable-length JSON evidence records through MLX collectives."""
    if (type(local) is not tuple or not local or group is None
            or any(type(item) is not DistributedB11Evidence for item in local)):
        _invalid("C08_DISTRIBUTED_B11_EVIDENCE_GATHER_INVALID")
    payload = json.dumps(
        [evidence_record(item) for item in local], sort_keys=True,
        separators=(",", ":")).encode()
    lengths = mx.distributed.all_gather(
        mx.array([len(payload)], dtype=mx.int32), group=group)
    mx.eval(lengths)
    sizes = tuple(int(value) for value in lengths.tolist())
    width = max(sizes)
    padded = payload + b"\0" * (width - len(payload))
    gathered = mx.distributed.all_gather(
        mx.array(list(padded), dtype=mx.uint8), group=group)
    mx.eval(gathered)
    raw = bytes(gathered.tolist())
    result = []
    for rank, size in enumerate(sizes):
        records = json.loads(raw[rank * width:rank * width + size].decode())
        result.extend(load_evidence_record(record) for record in records)
    return tuple(result)


__all__ = (
    "DistributedB11Evidence", "all_gather_b11_evidence", "evidence_record",
    "evidence_training_extension", "issue_distributed_b11_evidence",
    "load_evidence_record",
)
