"""Visit-scoped heavy source preparation for one selected C03 offer."""
from __future__ import annotations

from dataclasses import dataclass, replace

from bilqis_mlx.runtime.source_execution import _invalid_source_batch
from bilqis_mlx.semantics.frame_compiler import (
    CompiledFrameRows, validate_partial_visible_forest,
)
from bilqis_mlx.source_adapters.atoms.admission import (
    authorize_public_formal_prefix,
)


@dataclass(frozen=True)
class PreparedPrioritySourceMaterialization:
    """Immutable source/compiler inputs shared by every candidate step in a visit."""

    offer: object
    rows: tuple
    adapter: object
    manifest: object
    profile: object
    source_rows: tuple
    model_sources: tuple
    motif_inputs: tuple
    b11_sources: tuple
    prefixes: tuple
    semantic_context: object
    feature_owner: object
    packed_owner: object
    source_owner: object

    def __post_init__(self):
        count = len(self.rows)
        if (count < 1
                or any(type(value) is not tuple for value in (
                    self.rows, self.source_rows, self.model_sources,
                    self.motif_inputs, self.b11_sources, self.prefixes))
                or any(len(value) != count for value in (
                    self.source_rows, self.model_sources, self.motif_inputs,
                    self.b11_sources, self.prefixes))):
            _invalid_source_batch("BAMF_PRIORITY_SOURCE_MATERIALIZATION_INVALID")

    def require_current(self):
        self.__post_init__()
        self.feature_owner.require(self.semantic_context.features)
        self.source_owner.require()
        for source in self.b11_sources:
            source.require_current()
        for prefix in self.prefixes:
            self.packed_owner.require_row(prefix)
        return self


def _prepare_model_sources(source_context, authenticated, manifest, source_rows):
    from bilqis_mlx.runtime.atlas_training_adapter import (
        prepare_model_source_input,
    )

    prepared, configs, atlas_features = [], [], None
    for item in source_rows:
        visible = tuple(item.row["tokens"])
        frames = (() if item.projection is None else item.projection.envelopes)
        current, atlas_features = prepare_model_source_input(
            item.row, item.row["capability"], visible,
            source_context=source_context, source_ast=item.ast, frames=frames,
            task_scope=item.task, source_frontier=item.frontier,
            eligibility_policy=item.policy, compiler_config=item.config,
            atlas_selection=authenticated.selection, feature_artifact_path=None,
            semantic_context=authenticated, released_manifest=manifest,
            atlas_features=atlas_features,
            prepared_inventory=item.source_inventory)
        config = (item.config if item.projection is None
                  else replace(item.config, approved=item.projection))
        config = authorize_public_formal_prefix(item.ast, current.prefix, config)
        if item.projection is not None:
            validate_partial_visible_forest(current.prefix, item.ast, config)
        prepared.append(current)
        configs.append(config)
    return tuple(prepared), tuple(configs)


def _owners(offer, authenticated, rows, prefixes):
    from bilqis_mlx.runtime.atlas_artifact_owner import AtlasFeatureArtifactOwner
    from bilqis_mlx.runtime.atlas_packed_frame_owner import PackedFrameArtifactOwner
    from bilqis_mlx.runtime.salience_evidence_owner import SalienceEvidenceArtifactOwner

    width = max(len(prefix.positions) for prefix in prefixes)
    compiled = CompiledFrameRows(
        prefixes,
        tuple(prefix.positions + (None,) * (width - len(prefix.positions))
              for prefix in prefixes),
        tuple((True,) * len(prefix.positions) + (False,) * (width - len(prefix.positions))
              for prefix in prefixes))
    return (
        AtlasFeatureArtifactOwner(authenticated.features, authenticated.schema),
        PackedFrameArtifactOwner(compiled),
        SalienceEvidenceArtifactOwner.for_source_offer(
            offer.source_authority, rows, prefixes),
    )


def _register_and_require(offer, materialized):
    registrar = offer._planning_generation._target_registrar
    for kind, owner in (
            ("ATLAS_FEATURE", materialized.feature_owner),
            ("PACKED_FRAME", materialized.packed_owner),
            ("SALIENCE_EVIDENCE", materialized.source_owner)):
        registrar.register(kind, owner)
    return materialized.require_current()


def prepare_priority_source_materialization(
        offer, source_context, parent, *, prepared_rows=None):
    """Build source AST/formal/prefix state once after the option is selected."""
    rows = offer.require_qualified_current(
        source_context, parent, prepared_rows=prepared_rows)
    cached = offer._materialized.get("value")
    if cached is not None:
        if (type(cached) is not PreparedPrioritySourceMaterialization
                or cached.offer is not offer or cached.rows != rows):
            _invalid_source_batch("BAMF_PRIORITY_SOURCE_MATERIALIZATION_DRIFT")
        return _register_and_require(offer, cached)

    authenticated = offer._planning_generation._authenticated_features
    from bilqis_mlx.runtime.factory_training_bridge import (
        _motif_planning_input, _prepare_b11_source_binding,
        _prepare_factory_source_rows,
    )

    source_context._source_preparation_metrics.source_context_builds += 1
    adapter, manifest, profile, source_rows = _prepare_factory_source_rows(
        source_context, authenticated, rows, capability=offer.capability_id,
        source_seed=offer.source_seed, source_each=offer.source_each,
        source_authority=offer.source_authority)
    if len({tuple(item.row["tokens"]) for item in source_rows}) != len(rows):
        _invalid_source_batch("FACTORY_TRAINING_AMBIGUOUS_SOURCE_PREFIX")
    model_sources, b11_configs = _prepare_model_sources(
        source_context, authenticated, manifest, source_rows)
    if (len(model_sources) != len(source_rows)
            or len(b11_configs) != len(source_rows)):
        _invalid_source_batch("BAMF_PRIORITY_SOURCE_MATERIALIZATION_INVALID")
    b11_sources = tuple(
        _prepare_b11_source_binding(
            source_context, authenticated, adapter, profile, item,
            model.prefix, config, source_seed=offer.source_seed,
            source_each=offer.source_each)
        for item, model, config in zip(source_rows, model_sources, b11_configs)
    )
    prefixes = tuple(item.prefix for item in model_sources)
    motif_inputs = tuple(_motif_planning_input(
        source_context, authenticated, adapter, profile, item,
        source_seed=offer.source_seed, source_each=offer.source_each)
        for item in source_rows)
    source_context._source_preparation_metrics.compiled_source_builds += 1
    feature_owner, packed_owner, source_owner = _owners(
        offer, authenticated, rows, prefixes)
    materialized = PreparedPrioritySourceMaterialization(
        offer, rows, adapter, manifest, profile, source_rows, model_sources,
        motif_inputs, b11_sources, prefixes, authenticated, feature_owner,
        packed_owner, source_owner)
    offer._materialized["value"] = materialized
    return _register_and_require(offer, materialized)


__all__ = (
    "PreparedPrioritySourceMaterialization",
    "prepare_priority_source_materialization",
)
