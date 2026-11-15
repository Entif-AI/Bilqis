"""BAMF embedding banks owner."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from typing import Mapping
import mlx.core as mx
from lib.ithkuil.src.skos.publication import json_bytes
from bilqis_mlx.runtime.model_topology_v2 import GenerationExtents, ModelTopologySpecV2, SHA256_HEX_LENGTH
from bilqis_mlx.semantics.atlas.vocabulary import CandidateState, STAGED_ONLY, VocabularyExtension
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from .common import ACTIVE_BANK_SCHEMA, BANK_ROWS, EMBEDDING_INPUT_SCHEMA, INDEXED_LOGITS_SCHEMA, UINT32_MAX, WIDTH, _invalid
from .requests import FeatureRequest
from .composition import compose_factor_features


@dataclass(frozen=True)
class SemanticBankView:
    """Read-only adapter input from allocation custody, not an admission grant."""

    bank_index: int
    weights: mx.array
    active_rows: tuple[int, ...]
    semantic_release: str
    active_semantic_digest: str
    schema_version: str = ACTIVE_BANK_SCHEMA

    def __post_init__(self) -> None:
        if (self.schema_version != ACTIVE_BANK_SCHEMA or
                type(self.bank_index) is not int or self.bank_index < 0 or
                (self.bank_index + 1) * BANK_ROWS - 1 > UINT32_MAX or
                not isinstance(self.weights, mx.array) or self.weights.shape != (BANK_ROWS, WIDTH) or
                self.weights.dtype != mx.float32 or type(self.active_rows) is not tuple or
                any(type(row) is not int or not 0 <= row < BANK_ROWS for row in self.active_rows) or
                self.active_rows != tuple(sorted(set(self.active_rows))) or
                any(not isinstance(value, str) or len(value) != SHA256_HEX_LENGTH or
                    any(character not in "0123456789abcdef" for character in value)
                    for value in (self.semantic_release, self.active_semantic_digest))):
            _invalid()

@dataclass(frozen=True)
class ConceptBatch:
    requests: tuple[tuple[FeatureRequest, ...], ...]
    banks: tuple[SemanticBankView, ...]
    extents: GenerationExtents
    schema_version: str = EMBEDDING_INPUT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != EMBEDDING_INPUT_SCHEMA or type(self.extents) is not GenerationExtents:
            _invalid()

@dataclass(frozen=True)
class IndexedLogits:
    logits: mx.array
    indices: tuple[int, ...]
    schema_version: str = INDEXED_LOGITS_SCHEMA

def _validate_banks(banks):
    if (type(banks) is not tuple or not banks or any(type(bank) is not SemanticBankView for bank in banks) or
            tuple(bank.bank_index for bank in banks) != tuple(range(len(banks))) or
            any((bank.semantic_release, bank.active_semantic_digest) !=
                (banks[0].semantic_release, banks[0].active_semantic_digest) for bank in banks)):
        _invalid()
    # A01's active-set receipt hashes the canonical ordered global ABI index list.
    indices = [bank.bank_index * BANK_ROWS + row for bank in banks for row in bank.active_rows]
    digest = hashlib.sha256(json_bytes(indices)).hexdigest()
    if banks[0].active_semantic_digest != digest:
        _invalid()


def semantic_bank_views(
    parameters: Mapping[str, mx.array], extents: GenerationExtents,
    semantic_release: str, active_indices: tuple[int, ...],
) -> tuple[SemanticBankView, ...]:
    """Project one generation's owner-bound active ABI into read-only bank views."""
    if (not isinstance(parameters, Mapping) or type(extents) is not GenerationExtents
            or not isinstance(semantic_release, str)
            or len(semantic_release) != SHA256_HEX_LENGTH
            or any(character not in "0123456789abcdef" for character in semantic_release)
            or type(active_indices) is not tuple or not active_indices
            or active_indices != tuple(sorted(set(active_indices)))
            or any(type(index) is not int or not 0 <= index
                   < extents.semantic_bank_count * BANK_ROWS for index in active_indices)):
        _invalid()
    rows = [[] for _ in range(extents.semantic_bank_count)]
    for index in active_indices:
        bank, row = divmod(index, BANK_ROWS)
        rows[bank].append(row)
    banks = tuple(
        SemanticBankView(
            bank, parameters.get(f"identity.bank.{bank}"), tuple(active_rows),
            semantic_release, extents.active_semantic_digest,
        )
        for bank, active_rows in enumerate(rows)
    )
    _validate_banks(banks)
    if tuple(bank.bank_index * BANK_ROWS + row
             for bank in banks for row in bank.active_rows) != active_indices:
        _invalid()
    return banks


def semantic_bank_views_from_vocabulary_candidate(
    candidate: CandidateState, plan: VocabularyExtension,
) -> tuple[SemanticBankView, ...]:
    """Borrow A02's staged bank tensors without turning the view into authority."""
    if (type(candidate) is not CandidateState or type(plan) is not VocabularyExtension or
            candidate.status != STAGED_ONLY or plan.status != STAGED_ONLY or
            candidate.parent_generation_id != plan.parent_generation_id or
            candidate.source_allocation_digest != plan.source_allocation_digest or
            candidate.extents.semantic_bank_count != plan.bank_count or
            candidate.extents.active_semantic_digest != plan.active_semantic_digest or
            candidate.active_indices != plan.active_indices or
            tuple(index for index, _ in candidate.output_domain) != candidate.active_indices or
            candidate.registry_mirror_delta != plan.allocations or
            len(candidate.weights) != plan.bank_count):
        _invalid()
    return semantic_bank_views(
        {f"identity.bank.{index}": weights
         for index, weights in enumerate(candidate.weights)},
        candidate.extents, plan.semantic_release, candidate.active_indices)

def embed_atoms(
    parameters: Mapping[str, mx.array], batch: ConceptBatch, features: AtlasFeatures,
    *, atlas_selection=None, qualified_feature_rows=None,
) -> mx.array:
    """Gather active identities and add the actual released factor composition."""
    if (type(batch) is not ConceptBatch or type(batch.extents) is not GenerationExtents or
            type(features) is not AtlasFeatures or not isinstance(parameters, Mapping)):
        _invalid()
    _validate_banks(batch.banks)
    if (len(batch.banks) != batch.extents.semantic_bank_count or
            batch.banks[0].semantic_release != features.semantic_release or
            batch.banks[0].active_semantic_digest != batch.extents.active_semantic_digest or
            any(bank.weights is not parameters.get(f"identity.bank.{bank.bank_index}") for bank in batch.banks)):
        _invalid()
    factors = compose_factor_features(
        parameters, batch.requests, features, extents=batch.extents,
        atlas_selection=atlas_selection,
        qualified_feature_rows=qualified_feature_rows)
    identities = []
    active = tuple(frozenset(bank.active_rows) for bank in batch.banks)
    for row in batch.requests:
        values = []
        for request in row:
            bank_index, bank_row = divmod(request.concept.abi_index, BANK_ROWS)
            if bank_index >= len(batch.banks) or bank_row not in active[bank_index]:
                _invalid()
            values.append(batch.banks[bank_index].weights[bank_row])
        identities.append(mx.stack(values))
    combined = mx.stack(identities) + factors.all_factors
    return combined * mx.rsqrt(mx.mean(combined*combined, axis=-1, keepdims=True) +
                                ModelTopologySpecV2.rms_norm_epsilon) * parameters["features.norm"]

def semantic_logits(hidden: mx.array, active_banks: tuple[SemanticBankView, ...]) -> IndexedLogits:
    """Project only legal active rows, preserving their full global ABI addresses."""
    _validate_banks(active_banks)
    if (not isinstance(hidden, mx.array) or hidden.ndim < 1 or hidden.shape[-1] != WIDTH or
            hidden.dtype != mx.float32):
        _invalid()
    logits, indices = [], []
    for bank in active_banks:
        if bank.active_rows:
            rows = mx.array(bank.active_rows, dtype=mx.int32)
            logits.append(hidden @ bank.weights[rows].T)
            indices.extend(bank.bank_index * BANK_ROWS + row for row in bank.active_rows)
    if not indices:
        _invalid()
    return IndexedLogits(mx.concatenate(logits, axis=-1), tuple(indices))
