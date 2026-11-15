"""Differentiable raw-atom vectors from the actual released B01 parameters."""
import mlx.core as mx

from ...runtime.atlas_artifact_owner import AtlasFeatureArtifactOwner
from ...semantics.atlas_features import build_feature_manifest
from ...semantics.atlas.snapshot import load_pinned_atlas_snapshot
from ...semantics.source_atom_binding.common import invalid
from ...source_adapters.atom_binding import (
    _build_source_atom_handoff_from_snapshot, _require_embedding_ready_from_snapshot,
)
from ..frame_embeddings import (
    SemanticBankView, _released_factor_terms, _validate_banks,
    embedding_parameter_view,
)
from ...runtime.model_topology_v2 import ModelTopologySpecV2
from .inputs import SourceAtomRow


def _source_embedding_authority(
    compiled, config, source, features, feature_schema, artifact_owner,
    snapshot, source_execution_authority,
):
    if (type(source) is not SourceAtomRow
            or type(artifact_owner) is not AtlasFeatureArtifactOwner):
        invalid("BAMF_SOURCE_ATOM_INPUT_INVALID")
    handoff = None
    if source_execution_authority is not None:
        from bilqis_mlx.runtime.b11_source_execution_authority import (
            require_b11_source_execution_authority,
        )
        authority = require_b11_source_execution_authority(
            source_execution_authority, compiled, config, source)
        if snapshot is not None and snapshot is not authority.snapshot:
            invalid("BAMF_SOURCE_ATOM_GENERATION_DRIFT")
        snapshot, handoff = authority.snapshot, authority.source_handoff
    elif snapshot is None:
        snapshot = load_pinned_atlas_snapshot(source.selection)
        expected_features = build_feature_manifest(snapshot, feature_schema)
        if features != expected_features:
            invalid("BAMF_SOURCE_ATOM_GENERATION_DRIFT")
    artifact_owner.require(features)
    if handoff is None:
        handoff = _build_source_atom_handoff_from_snapshot(
            compiled, config, source.selection, snapshot, source.source_row,
            source.graph, **source.replay_arguments())
        _require_embedding_ready_from_snapshot(
            handoff, compiled, config, source.selection, snapshot,
            source.source_row, source.graph, **source.replay_arguments())
    else:
        handoff.__post_init__()
        if not handoff.embedding_ready:
            invalid("BAMF_SOURCE_ATOM_BINDING_HELD")
    return snapshot, handoff


def _source_embedding_parameters(
    parameters, source, features, extents, banks, snapshot,
):
    selection = source.selection
    if (snapshot.release_sha256 != selection.release_sha256
            or snapshot.bundle_id != selection.bundle_id
            or snapshot.source_bundle_id != selection.source_bundle_id
            or features.semantic_release != selection.release_sha256
            or features.atlas_bundle_id != selection.bundle_id
            or features.source_bundle_id != selection.source_bundle_id
            or extents.factor_map_digest != features.digest
            or type(banks) is not tuple or not banks
            or any(type(bank) is not SemanticBankView for bank in banks)):
        invalid("BAMF_SOURCE_ATOM_GENERATION_DRIFT")
    spec = ModelTopologySpecV2()
    owned = embedding_parameter_view(parameters, spec=spec, extents=extents)
    _validate_banks(banks)
    active_indices = tuple(
        bank.bank_index * spec.semantic_bank_rows + row
        for bank in banks for row in bank.active_rows)
    if (len(banks) != extents.semantic_bank_count
            or banks[0].semantic_release != snapshot.release_sha256
            or banks[0].active_semantic_digest != extents.active_semantic_digest
            or any(bank.weights is not owned.get(f"identity.bank.{bank.bank_index}")
                   for bank in banks)
            or any(index >= len(snapshot.abi_entries)
                   or snapshot.abi_entries[index].index != index
                   for index in active_indices)):
        invalid("BAMF_SOURCE_ATOM_GENERATION_DRIFT")
    return spec, owned


def _source_binding_vectors(
    handoff, config, features, banks, spec, owned,
):
    vectors = []
    for binding in handoff.bindings:
        row = features.features_for(
            binding.candidate_semantic_id, "NONE", "NONE", config.task.scope)
        if row.abi_index != binding.candidate_abi_index:
            invalid("BAMF_SOURCE_ATOM_FEATURE_ABI_DRIFT")
        bank_index, bank_row = divmod(row.abi_index, spec.semantic_bank_rows)
        if bank_row not in banks[bank_index].active_rows:
            invalid("BAMF_SOURCE_ATOM_INACTIVE_IDENTITY")
        factors = _released_factor_terms(owned, row)
        value = banks[bank_index].weights[bank_row]
        for term in factors:
            value = value + term
        value = value + owned["features.local_slot"][0]
        vectors.append(value)
    combined = mx.stack(vectors)
    return combined * mx.rsqrt(
        mx.mean(combined * combined, axis=-1, keepdims=True)
        + spec.rms_norm_epsilon
    ) * owned["features.norm"]


def source_atom_vectors(
    parameters, compiled, config, source, features, feature_schema, extents,
    banks, artifact_owner, *, snapshot=None, source_execution_authority=None,
):
    """Recheck source/rights before gathering any identity tensor.

    Native formal signatures remain source metadata. A06 alone owns categorical
    feature types. Unframed atoms use its existing NONE role/schema and local
    slot zero, without casting the atom to a caller-created ConceptRef.
    """
    snapshot, handoff = _source_embedding_authority(
        compiled, config, source, features, feature_schema, artifact_owner,
        snapshot, source_execution_authority)
    spec, owned = _source_embedding_parameters(
        parameters, source, features, extents, banks, snapshot)
    vectors = _source_binding_vectors(
        handoff, config, features, banks, spec, owned)
    return vectors, banks, handoff

