"""Portable C08 Factory-step capsule and rank-local authority reconstruction."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bilqis_mlx.factory.live_answers import live_answer_registry
from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.runtime.atlas_model_contracts import (
    _issue_bamf_active_semantic_rows, bind_candidate_active_semantic_rows,
)
from bilqis_mlx.runtime.atlas_training_authority import bind_compiled_training_batch
from bilqis_mlx.runtime.atlas_training_contracts import _issue_training_batch
from bilqis_mlx.runtime.atlas_training_contracts import (
    BamfDeliveryProvenance, BamfTrainingRow,
)
from bilqis_mlx.runtime.atlas_visit_provenance import BamfVisitProvenance
from bilqis_mlx.runtime.jit_adoption import verify_current_implementations
from bilqis_mlx.runtime.b11_source_execution_authority import (
    bind_b11_source_execution_authority,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    DistributedExecutionCacheWitness, bind_distributed_execution_cache,
    issue_distributed_execution_cache_witness,
)
from bilqis_mlx.runtime.factory_task_authority import (
    bind_factory_task_compiled_batch, factory_task_authority,
)
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.runtime.salience_training import portable_salience_supervision
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.source_adapters.school import live_source_registry


@dataclass(frozen=True)
class PortableSourceContext:
    release: object
    graph: dict
    source_root: str

    def materialize(self) -> SourceExecutionContext:
        source_registry = live_source_registry()
        answer_registry = live_answer_registry()
        verify_current_implementations(
            self.release, source_registry, answer_registry)
        context = SourceExecutionContext(
            release=self.release, graph=self.graph, source_root=Path(self.source_root),
            source_registry=source_registry, answer_registry=answer_registry)
        context.__post_init__()
        return context


@dataclass(frozen=True)
class PortableTrainingRow:
    model_input: object
    target: object
    native_target: object
    provenance: tuple
    visit_record: dict
    auxiliaries: tuple
    rule_policy: tuple

    @classmethod
    def from_row(cls, row):
        provenance = row.provenance
        names = (
            "row_id", "source_row_content_sha256", "source_id", "capability_id",
            "operation_id", "teacher_strategy", "requested_count", "delivered_count",
            "rehearsal", "optimizer_step_seed", "source_family_id", "episode_id",
            "immediate_dependencies",
        )
        return cls(
            row.model_input, row.target, row.native_target,
            tuple((name, getattr(provenance, name)) for name in names),
            provenance.visit.to_c03_record(), row.auxiliaries, row.rule_policy)

    def materialize(self) -> BamfTrainingRow:
        provenance = BamfDeliveryProvenance(
            **dict(self.provenance),
            visit=BamfVisitProvenance.from_c03_record(self.visit_record))
        provenance.__post_init__()
        return BamfTrainingRow(
            self.model_input, self.target, self.native_target, provenance,
            self.auxiliaries, self.rule_policy)


@dataclass(frozen=True)
class PortableTrainingBatch:
    release_sha256: str
    generation_binding: str
    delivered_content_sha256: str
    delivery_capability: str
    rows: tuple

    def materialize(self):
        return _issue_training_batch(
            self.release_sha256, self.generation_binding,
            self.delivered_content_sha256, self.delivery_capability,
            tuple(row.materialize() for row in self.rows))


@dataclass(frozen=True)
class PortableCompiledRow:
    compiled_rows: object
    compiler_configs: tuple
    features: object
    extents: object
    source_asts: tuple | None
    partial_forest_receipts: tuple | None
    sources: tuple
    feature_schema: object
    active_run_id: str
    active_generation: int
    active_indices: tuple[int, ...]
    row_index: int

    @classmethod
    def from_compiled(cls, compiled, row_index: int):
        value = compiled.compiled
        active = compiled.active_semantic_rows
        return cls(
            value.compiled, value.compiler_configs, value.features, value.extents,
            value.source_asts, value.partial_forest_receipts, compiled.sources,
            compiled.feature_schema, active.run_id, active.generation,
            active.active_indices, row_index)

    def materialize(self, training, source_context, feature_snapshot):
        compiled = CompiledEncoderInput(
            self.compiled_rows, self.compiler_configs, self.features, self.extents,
            source_asts=self.source_asts,
            partial_forest_receipts=self.partial_forest_receipts)
        active = _issue_bamf_active_semantic_rows(
            self.active_run_id, self.active_generation, self.extents,
            self.features, self.active_indices)
        source = self.sources[0]
        adapter = source_context.source_registry.resolve_owner(
            source.source_row.get("generator"))
        source_authority = bind_b11_source_execution_authority(
            compiled.compiled.rows[0], compiled.compiler_configs[0], source,
            adapter, feature_snapshot, compiled.features,
            source_registry=source_context.source_registry)
        return bind_compiled_training_batch(
            training, compiled, self.sources, self.feature_schema,
            active_semantic_rows=active, row_index=self.row_index,
            source_execution_authority=source_authority)


@dataclass(frozen=True)
class DistributedFactoryStepCapsule:
    parameters: object
    source_context: PortableSourceContext
    training_batch: PortableTrainingBatch
    compiled_rows: tuple[PortableCompiledRow, ...]
    feature_snapshot: object
    generation: str
    cache_witness: DistributedExecutionCacheWitness
    resource_plan: object
    manifest: object
    source_loss_multipliers: tuple[float, ...]
    salience_supervision: object | None

    def materialize(self):
        source_context = self.source_context.materialize()
        training = self.training_batch.materialize()
        compiled = tuple(
            row.materialize(training, source_context, self.feature_snapshot)
            for row in self.compiled_rows)
        cache = bind_distributed_execution_cache(
            self.cache_witness, self.parameters, spec=ModelTopologySpecV2(),
            extents=compiled[0].compiled.extents)
        return (
            self.parameters, compiled, source_context, self.feature_snapshot,
            self.generation, cache, self.resource_plan, self.manifest,
            self.source_loss_multipliers, self.salience_supervision,
        )


def issue_distributed_factory_step_capsule(
        *, parameters, prepared, source_context, feature_snapshot, generation, cache,
        resource_plan, manifest, salience_supervision=None, mentor_supervision=None):
    """Strip process-live owners and retain only portable rank execution inputs."""
    compiled_rows = tuple(prepared.compiled_rows)
    extents = compiled_rows[0].compiled.extents
    witness = issue_distributed_execution_cache_witness(
        cache, parameters, spec=ModelTopologySpecV2(), extents=extents)
    multipliers = tuple(
        1.0 if mentor_supervision is None
        else float(mentor_supervision.influence_for(compiled)) + 1.0
        for compiled in compiled_rows)
    salience = portable_salience_supervision(salience_supervision, compiled_rows)
    return DistributedFactoryStepCapsule(
        parameters=parameters,
        source_context=PortableSourceContext(
            source_context.release, source_context.graph, str(source_context.source_root)),
        training_batch=PortableTrainingBatch(
            prepared.training_batch.release_sha256,
            prepared.training_batch.generation_binding,
            prepared.training_batch.delivered_content_sha256,
            prepared.training_batch.delivery_capability,
            tuple(PortableTrainingRow.from_row(row)
                  for row in prepared.training_batch.rows)),
        compiled_rows=tuple(
            PortableCompiledRow.from_compiled(compiled, index)
            for index, compiled in enumerate(compiled_rows)),
        feature_snapshot=feature_snapshot, generation=generation,
        cache_witness=witness, resource_plan=resource_plan, manifest=manifest,
        source_loss_multipliers=multipliers, salience_supervision=salience)


__all__ = (
    "DistributedFactoryStepCapsule", "issue_distributed_factory_step_capsule",
)
