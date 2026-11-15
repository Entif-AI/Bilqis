"""Versioned output-head records; structural coordinates stay outside semantic ABI."""
from dataclasses import dataclass
import re
import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.answers import RegisteredAnswerModality
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.semantics.atlas_projection import FrozenAtlasSnapshot
from bilqis_mlx.semantics.frame_schema import ConceptRef, FrameSchema, RoleOccurrence
from bilqis_mlx.semantics.released_frame_schemas import VerifiedReleasedFrameSchemas


VALUE_BINDING_SCHEMA = 'bilqis.mlx.value-head-binding/v1'
FRAME_DOMAIN_SCHEMA = 'bilqis.mlx.frame-output-domain/v1'
HEAD_LOGITS_SCHEMA = 'bilqis.mlx.typed-head-logits/v1'
ROLE_MODALITY = 'answer.role-selection/v1'
FRAME_MODALITY = 'answer.structured-frame/v1'
WIDTH = ModelTopologySpecV2.width
_SHA = re.compile(r"[0-9a-f]{64}\Z")


def _text(value):
    return type(value) is str and bool(value)


def _sha(value):
    return type(value) is str and bool(_SHA.fullmatch(value))


def invalid():
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


def validate_hidden(hidden):
    if (not isinstance(hidden, mx.array) or hidden.ndim < 1
            or min(hidden.shape) < 1 or hidden.shape[-1] != WIDTH
            or hidden.dtype != mx.float32):
        invalid()


@dataclass(frozen=True)
class ValueHeadBinding:
    kind: str
    modality_id: str
    values: tuple[str, ...]
    identities: tuple[str, ...]
    abi_indices: tuple[int, ...]
    snapshot: FrozenAtlasSnapshot
    adapter: RegisteredAnswerModality | None
    schema_version: str = VALUE_BINDING_SCHEMA

    def __post_init__(self):
        if (self.schema_version != VALUE_BINDING_SCHEMA
                or not _text(self.kind) or not _text(self.modality_id)
                or type(self.snapshot) is not FrozenAtlasSnapshot
                or not _sha(self.snapshot.release_sha256)
                or not _sha(self.snapshot.active_set_sha256)
                or any(type(items) is not tuple or not items
                       for items in (self.values, self.identities, self.abi_indices))
                or not len(self.values) == len(self.identities) == len(self.abi_indices)
                or any(not _text(v) for v in self.values + self.identities)
                or len(set(self.values)) != len(self.values)
                or len(set(self.identities)) != len(self.identities)
                or any(type(i) is not int or i < 0 for i in self.abi_indices)
                or (self.kind == 'semantic_token' and self.adapter is not None)
                or (self.kind != 'semantic_token'
                    and type(self.adapter) is not RegisteredAnswerModality)):
            invalid()

    @property
    def semantic_release(self):
        return self.snapshot.release_sha256

    @property
    def active_semantic_digest(self):
        return self.snapshot.active_set_sha256


@dataclass(frozen=True)
class RoleCandidate:
    schema_id: str
    revision: int
    role_id: str
    occurrence_index: int

    def __post_init__(self):
        if (not _text(self.schema_id) or not _text(self.role_id)
                or type(self.revision) is not int or self.revision < 1
                or type(self.occurrence_index) is not int or self.occurrence_index < 0):
            invalid()


@dataclass(frozen=True)
class FrameOutputDomain:
    schema: FrameSchema
    released_schemas: VerifiedReleasedFrameSchemas
    feature_digest: str
    modality_id: str = FRAME_MODALITY
    schema_version: str = FRAME_DOMAIN_SCHEMA

    def __post_init__(self):
        if (self.schema_version != FRAME_DOMAIN_SCHEMA
                or self.modality_id != FRAME_MODALITY
                or type(self.schema) is not FrameSchema
                or type(self.released_schemas) is not VerifiedReleasedFrameSchemas
                or not _sha(self.feature_digest)):
            invalid()
        self.released_schemas.__post_init__()
        self.released_schemas.require_schema(self.schema, self.released_schemas.lookup(
            self.schema.schema_id, self.schema.revision))


@dataclass(frozen=True)
class TypedHeadLogits:
    logits: mx.array
    candidates: tuple[str | ConceptRef | RoleOccurrence | RoleCandidate, ...]
    modality_id: str
    semantic_release: str
    schema_version: str = HEAD_LOGITS_SCHEMA

    def __post_init__(self):
        if (self.schema_version != HEAD_LOGITS_SCHEMA
                or not _text(self.modality_id) or not _sha(self.semantic_release)
                or not isinstance(self.logits, mx.array)
                or self.logits.dtype != mx.float32
                or self.logits.ndim < 1 or min(self.logits.shape) < 1
                or type(self.candidates) is not tuple or not self.candidates
                or any(type(c) not in (str, ConceptRef, RoleOccurrence, RoleCandidate)
                       for c in self.candidates)
                or any(type(c) is str and not c for c in self.candidates)
                or len(set(self.candidates)) != len(self.candidates)
                or len({type(c) for c in self.candidates}) != 1
                or self.logits.shape[-1] != len(self.candidates)
                or (host_tensor_validation_enabled()
                    and not bool(mx.all(mx.isfinite(self.logits))))):
            invalid()
        for candidate in self.candidates:
            if type(candidate) in (ConceptRef, RoleOccurrence, RoleCandidate):
                candidate.__post_init__()
