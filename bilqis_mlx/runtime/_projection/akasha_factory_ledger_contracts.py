"""CT-052 immutable FactoryRelease/curriculum lifecycle read model for Akasha."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import re

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.model import FactoryRelease
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2


FACTORY_LEDGER_SCHEMA = "bilqis.akasha.factory-release-ledger/v1"
TOPOLOGY_VIEW_SCHEMA = "bilqis.akasha.factory-topology-view/v1"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
DEPENDENCY_EDGE_ARITY = 2


def _invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.BAMF_AKASHA.INVALID, reason=reason)


def _canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _sha(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value))


def _name(value: object) -> bool:
    return isinstance(value, str) and bool(value)


class FactoryLifecycleState(str, Enum):
    CURRICULUM_CANDIDATE = "CURRICULUM_CANDIDATE"
    FACTORY_VALIDATED = "FACTORY_VALIDATED"
    QUALIFIED = "QUALIFIED"
    STAGED = "STAGED"
    ADMITTED = "ADMITTED"
    PROMOTED = "PROMOTED"
    DEBT = "DEBT"
    SUPERSEDED = "SUPERSEDED"


class TopologyKnowledge(str, Enum):
    EXACT = "EXACT"
    HISTORICAL_COMPATIBILITY_REQUIRED = "HISTORICAL_COMPATIBILITY_REQUIRED"


@dataclass(frozen=True)
class FactoryReleaseView:
    factory_release_rid: str
    factory_release_sha256: str
    semantic_release_sha256: str
    course_sha256: str
    artifact_receipt_sha256: str
    capability_ids: tuple[str, ...]
    dependency_edges: tuple[tuple[str, str], ...]
    manifest_json: str

    def __post_init__(self) -> None:
        if (not _name(self.factory_release_rid)
                or not all(_sha(value) for value in (
                    self.factory_release_sha256, self.semantic_release_sha256,
                    self.course_sha256, self.artifact_receipt_sha256))
                or not isinstance(self.capability_ids, tuple)
                or len(set(self.capability_ids)) != len(self.capability_ids)
                or any(not _name(value) for value in self.capability_ids)
                or not isinstance(self.dependency_edges, tuple)):
            _invalid("AKASHA_FACTORY_RELEASE_VIEW_INVALID")
        try:
            manifest = json.loads(self.manifest_json)
        except (TypeError, ValueError):
            _invalid("AKASHA_FACTORY_RELEASE_MANIFEST_INVALID")
        if (self.manifest_json != _canonical(manifest)
                or hashlib.sha256(self.manifest_json.encode()).hexdigest()
                != self.factory_release_sha256
                or manifest.get("course_sha256") != self.course_sha256
                or _digest(manifest.get("semantic_release")) != self.semantic_release_sha256):
            _invalid("AKASHA_FACTORY_RELEASE_IDENTITY_DRIFT")
        capabilities = tuple(item.get("capability_id") for item in manifest.get("capabilities", ()))
        dependencies = tuple(sorted(
            (item.get("capability_id"), prerequisite)
            for item in manifest.get("capabilities", ())
            for prerequisite in item.get("prerequisites", ())))
        if capabilities != self.capability_ids or dependencies != self.dependency_edges:
            _invalid("AKASHA_FACTORY_RELEASE_DEPENDENCY_DRIFT")

    @classmethod
    def from_release(cls, factory_release_rid: str, release: FactoryRelease,
                     artifact_receipt_sha256: str) -> "FactoryReleaseView":
        if not isinstance(release, FactoryRelease):
            _invalid("AKASHA_FACTORY_RELEASE_REQUIRED")
        try:
            release.verify()
        except ValueError:
            _invalid("AKASHA_FACTORY_RELEASE_INVALID")
        manifest = release.manifest()
        capabilities = tuple(item.capability_id for item in release.capabilities)
        dependencies = tuple(sorted(
            (item.capability_id, prerequisite)
            for item in release.capabilities for prerequisite in item.prerequisites))
        return cls(
            factory_release_rid=factory_release_rid,
            factory_release_sha256=release.release_sha256,
            semantic_release_sha256=_digest(asdict(release.semantic_release)),
            course_sha256=release.course.digest(),
            artifact_receipt_sha256=artifact_receipt_sha256,
            capability_ids=capabilities,
            dependency_edges=dependencies,
            manifest_json=_canonical(manifest),
        )

    def to_record(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CurriculumCandidateView:
    candidate_sha256: str
    semantic_release_sha256: str
    artifact_receipt_sha256: str
    capability_ids: tuple[str, ...]
    dependency_edges: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if (not all(_sha(value) for value in (
                    self.candidate_sha256, self.semantic_release_sha256,
                    self.artifact_receipt_sha256))
                or not self.capability_ids
                or len(set(self.capability_ids)) != len(self.capability_ids)
                or any(not _name(item) for item in self.capability_ids)
                or any(len(edge) != DEPENDENCY_EDGE_ARITY or not all(_name(value) for value in edge)
                       for edge in self.dependency_edges)):
            _invalid("AKASHA_FACTORY_CANDIDATE_INVALID")

    def to_record(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class FactoryLifecycleReceipt:
    ordinal: int
    state: FactoryLifecycleState
    receipt_sha256: str
    semantic_release_sha256: str
    candidate_sha256: str | None = None
    factory_release_sha256: str | None = None
    predecessor_factory_release_sha256: str | None = None
    successor_factory_release_sha256: str | None = None
    capability_id: str | None = None
    checkpoint_sha256: str | None = None
    transition_sha256: str | None = None

    def __post_init__(self) -> None:
        optional_digests = (
            self.candidate_sha256, self.factory_release_sha256,
            self.predecessor_factory_release_sha256,
            self.successor_factory_release_sha256,
            self.checkpoint_sha256, self.transition_sha256,
        )
        if (type(self.ordinal) is not int or self.ordinal < 0
                or not isinstance(self.state, FactoryLifecycleState)
                or not _sha(self.receipt_sha256)
                or not _sha(self.semantic_release_sha256)
                or any(value is not None and not _sha(value) for value in optional_digests)
                or (self.capability_id is not None and not _name(self.capability_id))):
            _invalid("AKASHA_FACTORY_LIFECYCLE_INVALID")
        candidate_states = {
            FactoryLifecycleState.CURRICULUM_CANDIDATE,
            FactoryLifecycleState.FACTORY_VALIDATED,
            FactoryLifecycleState.QUALIFIED,
            FactoryLifecycleState.STAGED,
        }
        if self.state in candidate_states and self.candidate_sha256 is None:
            _invalid("AKASHA_FACTORY_CANDIDATE_EVIDENCE_REQUIRED")
        if self.state not in candidate_states and self.factory_release_sha256 is None:
            _invalid("AKASHA_FACTORY_RELEASE_EVIDENCE_REQUIRED")
        if (self.state is FactoryLifecycleState.SUPERSEDED
                and self.successor_factory_release_sha256 is None):
            _invalid("AKASHA_FACTORY_SUCCESSOR_EVIDENCE_REQUIRED")

    def to_record(self) -> dict:
        return {**asdict(self), "state": self.state.value}


@dataclass(frozen=True)
class TopologyView:
    knowledge: TopologyKnowledge
    topology_schema: str | None
    topology_digest: str | None
    topology_record_json: str | None
    architecture_id: str | None
    layers: int | None
    query_heads: int | None
    kv_heads: int | None
    model_dimension: int | None
    feed_forward_dimension: int | None
    context_length: int | None
    compatibility_ref: str | None = None
    schema_version: str = TOPOLOGY_VIEW_SCHEMA

    def __post_init__(self) -> None:
        if (not isinstance(self.knowledge, TopologyKnowledge)
                or self.schema_version != TOPOLOGY_VIEW_SCHEMA):
            _invalid("AKASHA_FACTORY_TOPOLOGY_INVALID")
        exact = self.knowledge is TopologyKnowledge.EXACT
        values = (self.topology_schema, self.topology_digest, self.topology_record_json,
                  self.architecture_id, self.layers, self.query_heads, self.kv_heads,
                  self.model_dimension, self.feed_forward_dimension, self.context_length)
        if not exact:
            if any(value is not None for value in values) or not _name(self.compatibility_ref):
                _invalid("AKASHA_FACTORY_TOPOLOGY_UNKNOWN_INVALID")
            return
        if (self.compatibility_ref is not None or not _name(self.topology_schema)
                or not _sha(self.topology_digest)
                or not _name(self.topology_record_json)
                or not _name(self.architecture_id)
                or any(type(value) is not int or value < 1 for value in (
                    self.layers, self.query_heads, self.kv_heads,
                    self.model_dimension, self.feed_forward_dimension,
                    self.context_length))):
            _invalid("AKASHA_FACTORY_TOPOLOGY_EXACT_INVALID")
        try:
            record = json.loads(self.topology_record_json)
            restored = ModelTopologySpecV2.from_record(record)
        except (TypeError, ValueError):
            _invalid("AKASHA_FACTORY_TOPOLOGY_RECORD_INVALID")
        if (self.topology_record_json != _canonical(record)
                or restored.digest != self.topology_digest
                or record.get("schema") != self.topology_schema
                or (restored.architecture_id, restored.layers, restored.query_heads,
                    restored.kv_heads, restored.width, restored.ffn_dimension,
                    restored.context) != (
                    self.architecture_id, self.layers, self.query_heads, self.kv_heads,
                    self.model_dimension, self.feed_forward_dimension,
                    self.context_length)):
            _invalid("AKASHA_FACTORY_TOPOLOGY_IDENTITY_DRIFT")

    @classmethod
    def exact_v2(cls, topology: ModelTopologySpecV2) -> "TopologyView":
        if not isinstance(topology, ModelTopologySpecV2):
            _invalid("AKASHA_FACTORY_TOPOLOGY_V2_REQUIRED")
        record = topology.to_record()
        return cls(
            TopologyKnowledge.EXACT, record["schema"], topology.digest,
            _canonical(record), topology.architecture_id, topology.layers,
            topology.query_heads, topology.kv_heads, topology.width,
            topology.ffn_dimension, topology.context)

    @classmethod
    def historical_unknown(cls, compatibility_ref: str) -> "TopologyView":
        return cls(
            TopologyKnowledge.HISTORICAL_COMPATIBILITY_REQUIRED,
            None, None, None, None, None, None, None, None, None, None,
            compatibility_ref)

    def to_record(self) -> dict:
        return {**asdict(self), "knowledge": self.knowledge.value}


@dataclass(frozen=True)
class CheckpointLineageView:
    run_id: str
    checkpoint_lineage_id: str
    generation_manifest_sha256: str
    checkpoint_sha256: str
    checkpoint_receipt_sha256: str
    factory_release_sha256: str
    semantic_release_sha256: str
    topology: TopologyView

    def __post_init__(self) -> None:
        if (not _name(self.run_id) or not _name(self.checkpoint_lineage_id)
                or not all(_sha(value) for value in (
                    self.generation_manifest_sha256, self.checkpoint_sha256,
                    self.checkpoint_receipt_sha256, self.factory_release_sha256,
                    self.semantic_release_sha256))
                or not isinstance(self.topology, TopologyView)):
            _invalid("AKASHA_FACTORY_CHECKPOINT_INVALID")

    def to_record(self) -> dict:
        return {**asdict(self), "topology": self.topology.to_record()}
