"""Immutable BAMF batch records and exact release-consumption boundary."""
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.semantics.atlas_features import FeatureRow
from bilqis_mlx.semantics.cognitive_dependencies import DependencyRef
from bilqis_mlx.semantics.frame_compiler import CompiledFrameBatch

from .atlas_visit_provenance import BamfVisitProvenance


@dataclass(frozen=True)
class BamfModelInput:
    prefix: CompiledFrameBatch
    features: tuple[FeatureRow, ...]
    eligibility_digest: str
    answer_plan: tuple

    def __post_init__(self) -> None:
        if (type(self.prefix) is not CompiledFrameBatch
                or type(self.features) is not tuple
                or any(type(item) is not FeatureRow for item in self.features)
                or not isinstance(self.eligibility_digest, str)
                or type(self.answer_plan) is not tuple):
            _invalid('MODEL_INPUT_INVALID')


@dataclass(frozen=True)
class BamfTarget:
    kind: str
    value: Any
    token_id: Any
    mask: bool | tuple[bool, ...]


@dataclass(frozen=True)
class BamfTargetEvidence:
    gold: Any
    answer_plan: Any
    auxiliary_labels: Any


@dataclass(frozen=True)
class BamfDeliveryProvenance:
    row_id: str
    source_row_content_sha256: str
    source_id: str | None
    capability_id: str
    operation_id: str | None
    teacher_strategy: tuple
    requested_count: int
    delivered_count: int
    rehearsal: str | None
    optimizer_step_seed: int
    visit: BamfVisitProvenance
    source_family_id: str | None = None
    episode_id: str | None = None
    immediate_dependencies: tuple[DependencyRef, ...] = ()

    def __post_init__(self) -> None:
        if type(self.visit) is not BamfVisitProvenance:
            _invalid("VISIT_PROVENANCE_CAPABILITY_MISMATCH")
        rehearsal_roles = {"prior", "preservation", "retention_support"}
        if (self.visit.capability_id != self.capability_id
                and self.rehearsal not in rehearsal_roles):
            _invalid("VISIT_PROVENANCE_CAPABILITY_MISMATCH")
        if self.rehearsal is not None and self.rehearsal not in rehearsal_roles:
            _invalid("DELIVERY_PROVENANCE_REHEARSAL_INVALID")
        if (type(self.immediate_dependencies) is not tuple
                or any(not isinstance(item, DependencyRef)
                       for item in self.immediate_dependencies)
                or self.immediate_dependencies != tuple(sorted(
                    set(self.immediate_dependencies)))):
            _invalid('DELIVERY_PROVENANCE_DEPENDENCIES_INVALID')


@dataclass(frozen=True)
class BamfTrainingRow:
    model_input: BamfModelInput
    target: BamfTarget
    native_target: BamfTarget | None
    provenance: BamfDeliveryProvenance
    auxiliaries: tuple = ()
    rule_policy: tuple = ()


_TRAINING_BATCH_ISSUER = object()


@dataclass(frozen=True, init=False)
class BamfTrainingBatch:
    release_sha256: str
    generation_binding: str
    delivered_content_sha256: str
    delivery_capability: str
    rows: tuple[BamfTrainingRow, ...]
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid('TRAINING_BATCH_CALLER_CONSTRUCTION_FORBIDDEN')

    def __post_init__(self):
        if (getattr(self, '_issuance', None) is not _TRAINING_BATCH_ISSUER
                or not all(isinstance(value, str) and value for value in (
                    self.release_sha256, self.generation_binding,
                    self.delivered_content_sha256, self.delivery_capability))
                or type(self.rows) is not tuple or not self.rows
                or any(type(row) is not BamfTrainingRow for row in self.rows)):
            _invalid('TRAINING_BATCH_INVALID')

    @property
    def authority_digest(self) -> str:
        payload = {
            'release_sha256': self.release_sha256,
            'generation_binding': self.generation_binding,
            'delivered_content_sha256': self.delivered_content_sha256,
            'delivery_capability': self.delivery_capability,
            'rows': tuple(_canonical_json_value(row.provenance)
                          for row in self.rows),
        }
        wire = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(wire.encode()).hexdigest()


def _issue_training_batch(release_sha256, generation_binding, delivered_content_sha256,
                          delivery_capability, rows):
    batch = object.__new__(BamfTrainingBatch)
    for name, value in (
            ('release_sha256', release_sha256),
            ('generation_binding', generation_binding),
            ('delivered_content_sha256', delivered_content_sha256),
            ('delivery_capability', delivery_capability),
            ('rows', tuple(rows)), ('_issuance', _TRAINING_BATCH_ISSUER)):
        object.__setattr__(batch, name, value)
    batch.__post_init__()
    return batch


def _reissue_training_batch(batch: BamfTrainingBatch, *, rows):
    batch.__post_init__()
    return _issue_training_batch(
        batch.release_sha256, batch.generation_binding,
        batch.delivered_content_sha256, batch.delivery_capability, rows)


@dataclass(frozen=True)
class PaddedMicrobatch:
    row_indices: tuple[int, ...]
    positions: tuple
    padding_mask: tuple


def _invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.BAMF_TRAINING_ADAPTER.INVALID, reason=reason)


def _freeze(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return tuple((key, _freeze(value[key])) for key in sorted(value))
    _invalid('UNSUPPORTED_SOURCE_OR_PROVENANCE_VALUE')


def _canonical_json_value(value):
    """Convert exact C02 records into an unambiguous JSON-safe digest form."""
    if type(value) is BamfVisitProvenance:
        value = value.to_c03_record()
    elif is_dataclass(value):
        # Process-local issuer tokens prove authority; they are not portable row data.
        value = {
            item.name: getattr(value, item.name)
            for item in fields(value)
            if not item.name.startswith("_")
        }
    if value is None or type(value) in (str, bool, int, float):
        return value
    if isinstance(value, bytes):
        return {"__bilqis_bytes_hex__": value.hex()}
    if isinstance(value, Enum):
        return {
            "__bilqis_enum__": (
                value.__class__.__module__, value.__class__.__qualname__,
                _canonical_json_value(value.value),
            )
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_json_value(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return {key: _canonical_json_value(value[key]) for key in sorted(value)}
    _invalid('UNSUPPORTED_CANONICAL_DIGEST_VALUE')


def _canonical_digest(value, *, trailing_newline: bool = False) -> str:
    payload = json.dumps(
        _canonical_json_value(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    )
    if trailing_newline:
        payload += "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def require_current_release(batch: BamfTrainingBatch, source_context: SourceExecutionContext, *,
                            generation_binding: str) -> None:
    """Refuse a prepared batch after its Factory release or semantic graph changes."""
    if not isinstance(batch, BamfTrainingBatch) or not isinstance(source_context, SourceExecutionContext):
        _invalid('SOURCE_CONTEXT_REQUIRED')
    batch.__post_init__()
    source_context.release.verify()
    source_context.release.verify_semantic_catalog(source_context.graph)
    if (batch.release_sha256 != source_context.release.release_sha256 or
            not isinstance(generation_binding, str) or not generation_binding or
            batch.generation_binding != generation_binding):
        _invalid('STALE_FACTORY_RELEASE')
