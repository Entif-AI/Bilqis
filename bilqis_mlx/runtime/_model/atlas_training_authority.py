"""Bind one source-owned Factory training batch to the exact B11 source row."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.source_execution import source_content_digest
from bilqis_mlx.semantics.atlas_features import FeatureSchema
from bilqis_mlx.semantics.cognitive_dependencies import DependencyRef, DependencyKind, ArtifactNode
from bilqis_mlx.semantics.dependencies.closure import closure_digest
from bilqis_mlx.runtime.atlas_training_contracts import BamfTrainingBatch, _canonical_digest

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ISSUER = object()
_BATCH_ISSUER = object()
_LOGICAL_BATCH_MIN_ROWS = 2


def _invalid(reason):
    ErrorBus.raise_(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


@dataclass(frozen=True, init=False)
class BamfTrainingAuthority:
    release_sha256: str
    generation_binding: str
    training_batch_sha256: str
    delivery_capability: str
    source_row_id: str
    source_row_sha256: str
    source_family_id: str
    episode_id: str
    visit_id: str
    immediate_dependencies: tuple[DependencyRef, ...]
    auxiliary_labels_sha256: str | None = None
    artifact_nodes: tuple = ()
    artifact_closure_sha256: str | None = None
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("B11_TRAINING_AUTHORITY_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self):
        if (getattr(self, "_issuance", None) is not _ISSUER
                or not all(isinstance(value, str) and value for value in (
                    self.delivery_capability, self.source_row_id,
                    self.source_family_id, self.episode_id))
                or not all(isinstance(value, str) and _SHA.fullmatch(value)
                           for value in (self.release_sha256,
                               self.generation_binding,
                               self.training_batch_sha256,
                               self.source_row_sha256, self.visit_id))
                or (self.auxiliary_labels_sha256 is not None
                    and (not isinstance(self.auxiliary_labels_sha256, str)
                         or not _SHA.fullmatch(self.auxiliary_labels_sha256)))
                or type(self.immediate_dependencies) is not tuple
                or not self.immediate_dependencies
                or any(not isinstance(item, DependencyRef)
                       for item in self.immediate_dependencies)
                or self.immediate_dependencies != tuple(sorted(
                    set(self.immediate_dependencies)))):
            _invalid("B11_TRAINING_AUTHORITY_INVALID")

        if type(self.artifact_nodes) is not tuple:
            _invalid("B11_TRAINING_ARTIFACT_CLOSURE_INVALID")
        if self.artifact_nodes:
            try:
                digest = closure_digest(self.artifact_nodes)
            except (TypeError, ValueError):
                _invalid("B11_TRAINING_ARTIFACT_CLOSURE_INVALID")
            if (digest != self.artifact_closure_sha256
                    or any(ref.kind is DependencyKind.ARTIFACT
                           and ref.key not in {node.artifact_id for node in self.artifact_nodes}
                           for ref in self.immediate_dependencies)):
                _invalid("B11_TRAINING_ARTIFACT_CLOSURE_INVALID")
        elif (self.artifact_closure_sha256 is not None
              or any(ref.kind is DependencyKind.ARTIFACT for ref in self.immediate_dependencies)):
            _invalid("B11_TRAINING_ARTIFACT_CLOSURE_INVALID")

    @property
    def digest(self):
        payload = {
            "release": self.release_sha256,
            "generation": self.generation_binding,
            "batch": self.training_batch_sha256,
            "capability": self.delivery_capability,
            "row": self.source_row_id,
            "row_sha256": self.source_row_sha256,
            "source_family": self.source_family_id,
            "episode": self.episode_id,
            "visit_id": self.visit_id,
            "immediate_dependencies": tuple(
                (ref.kind.value, ref.key)
                for ref in self.immediate_dependencies),
        }
        if self.auxiliary_labels_sha256 is not None:
            payload["auxiliary_labels_sha256"] = self.auxiliary_labels_sha256
        if self.artifact_nodes:
            payload["artifact_closure_sha256"] = self.artifact_closure_sha256
        wire = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(wire.encode()).hexdigest()


def _issue(batch, source, provenance, auxiliaries=()):
    if (not provenance.source_family_id or not provenance.episode_id
            or not provenance.immediate_dependencies):
        _invalid("B11_TRAINING_SOURCE_INDEPENDENCE_REQUIRED")
    authority = object.__new__(BamfTrainingAuthority)
    for name, value in (
        ("release_sha256", batch.release_sha256),
        ("generation_binding", batch.generation_binding),
        ("training_batch_sha256", batch.authority_digest),
        ("delivery_capability", batch.delivery_capability),
        ("source_row_id", source.source_row["id"]),
        ("source_row_sha256", provenance.source_row_content_sha256),
        ("source_family_id", provenance.source_family_id),
        ("episode_id", provenance.episode_id),
        ("visit_id", provenance.visit.visit_id),
        ("immediate_dependencies", provenance.immediate_dependencies),
        ("auxiliary_labels_sha256", _canonical_digest(auxiliaries) if auxiliaries else None),
        ("artifact_nodes", ()),
        ("artifact_closure_sha256", None),
        ("_issuance", _ISSUER),
    ):
        object.__setattr__(authority, name, value)
    authority.__post_init__()
    return authority


def extend_training_dependencies(
    authority: BamfTrainingAuthority,
    dependencies: tuple[DependencyRef, ...],
    *, artifact_nodes: tuple = (),
) -> BamfTrainingAuthority:
    """Return the same source authority with execution-observed C09 inputs added.

    C02 can freeze source-owned premises before B11 runs, but retained motifs and
    correction-owned artifacts are only knowable after the real forward path has
    executed.  The B11 owner therefore extends, never replaces, that frontier.
    """
    if (type(authority) is not BamfTrainingAuthority
            or type(artifact_nodes) is not tuple
            or any(type(node) is not ArtifactNode for node in artifact_nodes)
            or type(dependencies) is not tuple
            or any(not isinstance(item, DependencyRef) for item in dependencies)):
        _invalid("B11_TRAINING_EXECUTION_DEPENDENCIES_INVALID")
    authority.__post_init__()
    merged = tuple(sorted(set((*authority.immediate_dependencies, *dependencies))))
    nodes = {node.artifact_id: node for node in authority.artifact_nodes}
    for node in artifact_nodes:
        if node.artifact_id in nodes and nodes[node.artifact_id] != node:
            _invalid("B11_TRAINING_ARTIFACT_CLOSURE_CONFLICT")
        nodes[node.artifact_id] = node
    closed = tuple(nodes[key] for key in sorted(nodes))
    digest = closure_digest(closed) if closed else None
    if merged == authority.immediate_dependencies and closed == authority.artifact_nodes:
        return authority
    extended = object.__new__(BamfTrainingAuthority)
    for name in (
        "release_sha256", "generation_binding", "training_batch_sha256",
        "delivery_capability", "source_row_id", "source_row_sha256",
        "source_family_id", "episode_id", "visit_id", "auxiliary_labels_sha256",
    ):
        object.__setattr__(extended, name, getattr(authority, name))
    object.__setattr__(extended, "artifact_nodes", closed)
    object.__setattr__(extended, "artifact_closure_sha256", digest)
    object.__setattr__(extended, "immediate_dependencies", merged)
    object.__setattr__(extended, "_issuance", _ISSUER)
    extended.__post_init__()
    return extended


@dataclass(frozen=True, init=False)
class BamfLogicalBatchTrainingAuthority:
    """C08 owner proof for one logical batch composed of final B11 row authorities."""

    release_sha256: str
    generation_binding: str
    training_batch_sha256: str
    delivery_capability: str
    visit_id: str
    members: tuple[BamfTrainingAuthority, ...]
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("C08_LOGICAL_BATCH_AUTHORITY_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self):
        if (getattr(self, "_issuance", None) is not _BATCH_ISSUER
                or not all(isinstance(value, str) and value for value in (
                    self.delivery_capability,))
                or not all(isinstance(value, str) and _SHA.fullmatch(value)
                           for value in (
                               self.release_sha256, self.generation_binding,
                               self.training_batch_sha256, self.visit_id))
                or type(self.members) is not tuple
                or len(self.members) < _LOGICAL_BATCH_MIN_ROWS
                or any(type(member) is not BamfTrainingAuthority
                       for member in self.members)
                or len({member.source_row_id for member in self.members})
                != len(self.members)
                or len({member.source_family_id for member in self.members}) != 1):
            _invalid("C08_LOGICAL_BATCH_AUTHORITY_INVALID")
        for member in self.members:
            member.__post_init__()
            if (member.release_sha256 != self.release_sha256
                    or member.generation_binding != self.generation_binding
                    or member.training_batch_sha256 != self.training_batch_sha256
                    or member.delivery_capability != self.delivery_capability
                    or member.visit_id != self.visit_id):
                _invalid("C08_LOGICAL_BATCH_AUTHORITY_INVALID")
        # Validate cross-member closure aliases at issuance, not only when a
        # downstream consumer happens to inspect the aggregate.
        self.artifact_nodes

    @property
    def digest(self):
        payload = {
            "schema": "bilqis.mlx.c08-logical-batch-training-authority/v1",
            "release": self.release_sha256,
            "generation": self.generation_binding,
            "batch": self.training_batch_sha256,
            "capability": self.delivery_capability,
            "visit_id": self.visit_id,
            "members": tuple(member.digest for member in self.members),
        }
        wire = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(wire.encode()).hexdigest()

    @property
    def artifact_nodes(self):
        """Canonical union of member-owned executed artifact closures."""
        nodes = {}
        for member in self.members:
            for node in member.artifact_nodes:
                previous = nodes.get(node.artifact_id)
                if previous is not None and previous != node:
                    _invalid("C08_LOGICAL_BATCH_ARTIFACT_CLOSURE_CONFLICT")
                nodes[node.artifact_id] = node
        return tuple(nodes[key] for key in sorted(nodes))

    @property
    def artifact_closure_sha256(self):
        nodes = self.artifact_nodes
        return closure_digest(nodes) if nodes else None

    @property
    def immediate_dependencies(self):
        return tuple(sorted({
            dependency
            for member in self.members
            for dependency in member.immediate_dependencies
        }))


def bind_logical_batch_training_authority(
        batch: BamfTrainingBatch,
        authorities: tuple[BamfTrainingAuthority, ...],
) -> BamfLogicalBatchTrainingAuthority:
    """Bind exact row-complete B11 authorities into one C08 optimizer-step authority."""
    if (type(batch) is not BamfTrainingBatch
            or type(authorities) is not tuple
            or len(authorities) != len(batch.rows)
            or len(authorities) < _LOGICAL_BATCH_MIN_ROWS):
        _invalid("C08_LOGICAL_BATCH_AUTHORITY_INPUT_INVALID")
    batch.__post_init__()
    for row, authority in zip(batch.rows, authorities):
        if type(authority) is not BamfTrainingAuthority:
            _invalid("C08_LOGICAL_BATCH_AUTHORITY_INPUT_INVALID")
        authority.__post_init__()
        provenance = row.provenance
        if (authority.release_sha256 != batch.release_sha256
                or authority.generation_binding != batch.generation_binding
                or authority.training_batch_sha256 != batch.authority_digest
                or authority.delivery_capability != batch.delivery_capability
                or authority.source_row_id != provenance.row_id
                or authority.source_row_sha256 != provenance.source_row_content_sha256
                or authority.source_family_id != provenance.source_family_id
                or authority.episode_id != provenance.episode_id
                or authority.visit_id != provenance.visit.visit_id):
            _invalid("C08_LOGICAL_BATCH_AUTHORITY_DRIFT")
    authority = object.__new__(BamfLogicalBatchTrainingAuthority)
    first = authorities[0]
    for name, value in (
        ("release_sha256", first.release_sha256),
        ("generation_binding", first.generation_binding),
        ("training_batch_sha256", first.training_batch_sha256),
        ("delivery_capability", first.delivery_capability),
        ("visit_id", first.visit_id),
        ("members", authorities),
        ("_issuance", _BATCH_ISSUER),
    ):
        object.__setattr__(authority, name, value)
    authority.__post_init__()
    return authority


def bind_compiled_training_batch(
        batch, compiled, sources, feature_schema, *, active_semantic_rows, row_index=0,
        source_execution_authority=None):
    """Issue one B11 row from an exact source-owned C02 delivery batch."""
    from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
    from bilqis_mlx.learning.source_atoms import SourceAtomRow
    from bilqis_mlx.runtime.atlas_model_contracts import (
        BamfActiveSemanticRows, BamfCompiledBatch,
    )

    if (type(batch) is not BamfTrainingBatch
            or type(compiled) is not CompiledEncoderInput
            or type(sources) is not tuple or len(sources) != 1
            or type(sources[0]) is not SourceAtomRow
            or type(feature_schema) is not FeatureSchema
            or type(active_semantic_rows) is not BamfActiveSemanticRows
            or type(row_index) is not int
            or not 0 <= row_index < len(batch.rows)):
        _invalid("B11_TRAINING_AUTHORITY_INPUT_INVALID")
    batch.__post_init__()
    provenance = batch.rows[row_index].provenance
    source = sources[0]
    source_row = source.source_row
    if (source_content_digest((source_row,)) != provenance.source_row_content_sha256
            or source_row.get("id") != provenance.row_id
            or source_row.get("capability") != provenance.capability_id):
        _invalid("B11_TRAINING_SOURCE_ROW_MISMATCH")
    return BamfCompiledBatch(
        compiled, sources, feature_schema, active_semantic_rows,
        training_authority=_issue(batch, source, provenance, batch.rows[row_index].auxiliaries),
        visit_provenance=provenance.visit,
        source_execution_authority=source_execution_authority)
