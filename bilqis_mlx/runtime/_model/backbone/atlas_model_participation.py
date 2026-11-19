"""B11 semantic, parameter, and correction participation accounting."""
from __future__ import annotations

from bilqis_mlx.learning.atlas_readout import AnswerPlan, DecisionKind
from bilqis_mlx.learning.frame_embeddings.banks import semantic_bank_views
from bilqis_mlx.runtime.atlas_training_authority import extend_training_dependencies
from bilqis_mlx.runtime.bamf_bundle.execution_cache import bind_motif_artifact_owner
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2, expected_bamf_shapes
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind

from .atlas_model_contracts import BamfCompiledBatch, _ForwardRecord, _invalid


def _row_motif_read(read, row_index):
    if read.hidden.shape[0] == 1:
        return read
    if (not read.row_participating_slots
            or row_index < 0 or row_index >= read.hidden.shape[0]):
        _invalid("B11_MOTIF_ROW_PARTICIPATION_REQUIRED")
    slots = read.row_participating_slots[row_index]
    from bilqis_mlx.learning.atlas_engram_reads import MotifReadResult
    return MotifReadResult(
        read.hidden[row_index:row_index + 1],
        (read.dispositions[row_index],), slots,
        (read.context_digests[row_index],), (slots,))


def _motif_reads(producer, row_index=0):
    return tuple(_row_motif_read(read, row_index) for read in (
        getattr(producer, "_input_motif_read", None), producer._motif_read)
        if read is not None)


def _bound_snapshot(batch: BamfCompiledBatch, plan: AnswerPlan):
    """Reuse the plan-bound immutable snapshot; never reopen A01 inside B11."""
    source = batch.sources[0]
    selection = source.selection
    snapshot = plan.snapshot
    if (
        snapshot.release_sha256 != selection.release_sha256
        or snapshot.bundle_id != selection.bundle_id
        or snapshot.source_bundle_id != selection.source_bundle_id
        or snapshot.release_sha256 != batch.compiled.features.semantic_release
    ):
        _invalid("B11_SEMANTIC_SNAPSHOT_MISMATCH")
    return snapshot


def _active_banks(parameters, batch: BamfCompiledBatch, plan: AnswerPlan):
    snapshot = _bound_snapshot(batch, plan)
    return semantic_bank_views(
        parameters, batch.compiled.extents, snapshot.release_sha256,
        batch.active_semantic_rows.active_indices)


def _executed_readout_parameters(plan, output):
    dense = {
        "readout.state_norm", "readout.output_norm", "readout.query",
        "readout.key", "readout.value", "readout.output",
    }
    executed_ids = {decision.decision_id for decision in output.decisions}
    kinds = {decision.kind for decision in output.decisions}
    if DecisionKind.CONTROL in kinds:
        dense.update(("readout.control", "readout.control_bias"))
    if DecisionKind.ROLE in kinds:
        dense.add("readout.role_query")
    if DecisionKind.EPISTEMIC in kinds:
        dense.update(("readout.epistemic", "readout.epistemic_bias"))
    if any(
        decision.decision_id in executed_ids and decision.depends_on
        for decision in plan.decisions
    ):
        dense.add("readout.feedback")
    return dense


def _execution_dependencies(batch, producer_or_reads, accepted_cache):
    motif_reads = (producer_or_reads if type(producer_or_reads) is tuple else tuple(
        read for read in (
            getattr(producer_or_reads, "_input_motif_read", None),
            getattr(producer_or_reads, "_motif_read", None))
        if read is not None))
    dependencies = set()
    feature = batch.atlas_feature_artifact_owner.current_node
    dependencies.update(
        ref for ref in feature.immediate_dependencies
        if ref.kind is not DependencyKind.ARTIFACT)
    row = batch.compiled.compiled.rows[0]
    for node in batch.compiled.packed_frame_artifact_owner.require_row(row):
        dependencies.update(
            ref for ref in node.immediate_dependencies
            if ref.kind is not DependencyKind.ARTIFACT)
    if (accepted_cache is not None
            and any(read.participating_slots for read in motif_reads)):
        owner = bind_motif_artifact_owner(accepted_cache, batch.compiled)
        node = owner.current_node
        dependencies.update(
            ref for ref in node.immediate_dependencies
            if ref.kind is not DependencyKind.ARTIFACT)
        dependencies.update(owner.source_dependencies)
    return tuple(sorted(dependencies))


def _forward_participation(
    params, batch, plan, output, producer, accepted_cache,
    refinement_roles=(), refinement_executed=False, refinement_routing=False,
    producer_row_index=0,
):
    source = batch.sources[0]
    snapshot = _bound_snapshot(batch, plan)
    row = batch.compiled.compiled.rows[0]
    visible = []
    feature_rows = set()
    for abi_index in tuple(source.source_row.get("tokens", ()))[:row.visible_end]:
        entry = snapshot.abi(abi_index)
        visible.append((entry.bank, entry.row))
        factors = batch.compiled.features.features_for(
            entry.semantic_id, "NONE", "NONE",
            batch.compiled.compiler_configs[0].task.scope,
        )
        feature_rows.update(("type", item) for item in factors.type_rows)
        feature_rows.add(("role", factors.role_row))
        feature_rows.add(("schema", factors.schema_row))
    feature_rows.add(("role", dict(batch.compiled.features.role_map)["NONE"]))
    motif_reads = _motif_reads(producer, producer_row_index)

    dense = {
        item.name for item in expected_bamf_shapes(
            ModelTopologySpecV2(), batch.compiled.extents)
        if item.name.startswith(("blocks.", "depth.", "plastic.group."))
    }
    dense.update((
        "features.gates", "features.project_type", "features.project_role",
        "features.project_schema", "features.project_graph", "features.norm",
    ))
    dense.update(_executed_readout_parameters(plan, output))
    for site_index, read in enumerate(motif_reads):
        if read.participating_slots:
            dense.update((
                f"motif.site.{site_index}.projection",
                f"motif.site.{site_index}.norm",
                f"motif.site.{site_index}.gate_hidden",
                f"motif.site.{site_index}.gate_feature",
                f"motif.site.{site_index}.bias",
            ))
    if refinement_roles:
        feature_rows.update(
            ("role", dict(batch.compiled.features.role_map)[role])
            for role in refinement_roles
        )
    if refinement_executed:
        dense.update(
            item.name for item in expected_bamf_shapes(
                ModelTopologySpecV2(), batch.compiled.extents)
            if item.name.startswith("refine.")
            and item.name not in ("refine.route", "refine.route_bias")
        )
    if refinement_routing:
        dense.update(("refine.route", "refine.route_bias"))
    if not dense <= set(params):
        _invalid("B11_EXECUTED_PARAMETER_CENSUS_MISMATCH")
    return _ForwardRecord(
        plan.generation_binding,
        None if accepted_cache is None else accepted_cache.run_id,
        None if accepted_cache is None else accepted_cache.generation,
        None if accepted_cache is None else accepted_cache.accepted_manifest_sha256,
        tuple(sorted(set(visible))),
        tuple(sorted(feature_rows)),
        (0,),
        tuple(sorted(dense)),
        motif_reads,
        batch.compiled.features.role_map,
        (None if batch.training_authority is None else extend_training_dependencies(
            batch.training_authority,
            _execution_dependencies(batch, motif_reads, accepted_cache))),
    )


__all__ = ("_active_banks", "_forward_participation")
