"""Disposable full-model C05/C16 learning diagnostics and B13.2 continuation.

This module is not the #708 feature-authority acceptance surface.  It exercises
real source-backed MLX learning behavior and may be expensive; #708 provenance is
covered by the custody/feature-authority suites.
"""
from __future__ import annotations

# This module executes real MLX/source-backed acceptance and diagnostics. Ordinary
# differential leaf verification must not schedule it on an interactive socket;
# run its witnesses explicitly through scripts/bamf/detached_long_run.py.

import json
import os
import random
from dataclasses import replace
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import mlx.core as mx
from bilqis_mlx.learning.atlas_acceptance import (
    candidate_identity_digest, mint_acceptance_binding,
)
from bilqis_mlx.learning.atlas_candidate import begin_candidate, resolve_candidate
from bilqis_mlx.learning.atlas_readout import DecisionOutput, ExecutionMode
from bilqis_mlx.learning.atlas_retention_decision import issue_factory_retention_decision
from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.learning.learning_experiment import Settings
from bilqis_mlx.learning.source_atoms.tests.backbone_test_support import SourceBackboneTestBase
from bilqis_mlx.compatibility import historical_teacher_policy
from bilqis_mlx.runtime.accepted_teacher_custody import select_accepted_teacher_visit
from bilqis_mlx.runtime.atlas_visit_provenance import BamfVisitProvenance
from bilqis_mlx.runtime.atlas_model import (
    bamf_value_and_grad, bind_compiled_training_batch, forward_bamf, model_backend,
)
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, admit_uninterrupted_candidate_step,
    bind_accepted_execution_cache, derive_successor_bundle,
    load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle import (
    authenticate_bamf_execution_feature_context,
    issue_initial_foundation_feature_authority,
    prepare_initial_generation,
    publish_bamf_generation,
    publish_initial_generation,
)
from bilqis_mlx.runtime.bamf_bundle.genesis.foundation import initial_foundation_sidecars
from bilqis_mlx.runtime.bamf_bundle.genesis.preparation_authority import (
    _factory_generation_provenance,
)
from bilqis_mlx.runtime.factory_complete_solver import factory_evaluation_instrument
from bilqis_mlx.runtime.factory_evaluation_compiler import compile_factory_evaluation_batch
from bilqis_mlx.runtime.factory_retention_owner import (
    _candidate_from_live_parent, bind_current_retention_protection_plan,
    bind_current_retention_source_rows,
    evaluate_factory_retention_candidate,
)
from bilqis_mlx.runtime.factory_task_authority import factory_task_authority
from bilqis_mlx.runtime.model_topology_v2 import (
    b01_generation_authority, b01_generation_extents,
)
from bilqis_mlx.runtime.task_goal_readout import task_goal_route_decisions, task_goal_route_plan
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.tests.capability.factory.retention.factory_retention_live_support import (
    C05_GENESIS_SEED, C05_TRAINING_LEARNING_RATE, HP, live_factory_context,
)
from bilqis_mlx.runtime.tests.capability.factory.retention.next_step.factory_retention_next_step_witness import (
    prove_source_qualified_continuation,
)
from bilqis_mlx.runtime.tests.capability.factory.retention.diagnostics.factory_retention_lesson_diagnostic import (
    diagnose_factory_retention_lesson,
)
from bilqis_mlx.runtime.tests.capability.factory.retention.diagnostics.factory_retention_target_diagnostic import (
    diagnose_factory_retention_target,
)
from bilqis_mlx.runtime.tests.capability.factory.retention.source_training_support import (
    source_training_batch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import retention_decision
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    issue_factory_authority,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
    host_source_authority_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import (
    adaptation, selection_teacher,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection


TARGET = "B.IDBOOLOPS"
TRAIN_SEED = 46117


def _initialize_generation(run_dir, source_context, snapshot, artifact):
    run_id = f"factory-c05-live-{run_dir.name}"
    selection = AtlasArtifactSelection(
        str(artifact), snapshot.bundle_id, snapshot.release_sha256,
        snapshot.source_bundle_id)
    features = issue_initial_foundation_feature_authority(selection)
    origin = Checkpoint(
        "7" * 64, "bundles/c05-closeout-origin", 0, True)
    factory = issue_factory_authority(
        source_context.release, source_context.graph, origin)
    provenance = _factory_generation_provenance(
        source_context.release, features)
    with host_source_authority_patch(AUTHORITY):
        semantic, compiler, *_ = initial_foundation_sidecars(
            source_context.release, factory.admission, source_context.graph,
            run_seed=C05_GENESIS_SEED, feature_authority=features)
        motif = MotifManifest(provenance.release_digest)
        extents = b01_generation_extents(
            semantic_abi=semantic, compiler_features=compiler,
            motif_page_count=1, motif_key_map_digest=motif.digest)
        prepared = prepare_initial_generation(
            run_id=run_id, run_seed=C05_GENESIS_SEED,
            graph=source_context.graph, factory_authority=factory,
            model_authority=b01_generation_authority(extents),
            optimizer_hyperparameters=HP, provenance=provenance,
            foundation_features=features,
            delivery_events=({
                "event": "FACTORY_C05_GENESIS", "optimizer_step": 0},))
        with patch(
            "bilqis_mlx.runtime.bamf_bundle.codec.assert_headroom",
            return_value=None,
        ):
            publish_initial_generation(run_dir, prepared, reserve_gib=0.)
    parent = load_accepted_generation(run_dir)
    cache = bind_accepted_execution_cache(run_dir)
    accepted_context = AcceptedRuntimeHost(run_dir).source_context(
        graph=source_context.graph,
        source_root=source_context.source_root,
    )
    bind_current_retention_protection_plan(
        accepted_context, parent, cache)
    bind_current_retention_source_rows(
        accepted_context, cache, TARGET)
    return parent, cache, accepted_context


def _execute_source_owned_candidate_step_evidence(
        run_dir, source_context, parent, cache, artifact, *,
        teacher_policy=None, teacher_visit_provenance=None,
        learning_rate=C05_TRAINING_LEARNING_RATE):
    backend = model_backend(parent.topology)
    if "gpu" not in backend.device.lower():
        raise AssertionError(f"C05 source-owned MLX backend is not GPU: {backend.device}")
    print("FACTORY_C05_DEVICE " + json.dumps({
        "default_device": str(mx.default_device()),
        "model_backend": backend.device,
        "metal_available": mx.metal.is_available(),
    }, sort_keys=True), flush=True)
    row = source_context.draw_rows(
        seed=TRAIN_SEED, capability=TARGET, each=1)[0]
    generation = execution_generation_digest(
        parent.retained_state.optimizer.parameters,
        spec=parent.topology, extents=parent.extents)
    training = source_training_batch(
        source_context, parent, artifact, row, generation,
        capability=TARGET, source_seed=TRAIN_SEED,
        optimizer_step_seed=parent.retained_state.optimizer_step,
        teacher_strategy=teacher_policy,
        teacher_visit_provenance=teacher_visit_provenance)
    compiled = compile_factory_evaluation_batch(
        source_context, parent, str(artifact), row,
        source_seed=TRAIN_SEED, source_each=1)
    live_batch = bind_compiled_training_batch(
        training, compiled.compiled, compiled.sources, compiled.feature_schema,
        active_semantic_rows=compiled.active_semantic_rows)
    authority = factory_task_authority(source_context, live_batch)
    feature_context = authenticate_bamf_execution_feature_context(
        parent, str(artifact), source_context.run_dir)
    plan = task_goal_route_plan(
        authority.goal, live_batch, feature_context.snapshot, generation)
    targets, mask = _source_targets(
        source_context, parent, artifact, row, authority)
    gradient = bamf_value_and_grad(
        dict(parent.retained_state.optimizer.parameters),
        live_batch, plan, targets, mask, cache)
    transaction = admit_uninterrupted_candidate_step(
        run_dir, parent, loss_bearing_target=True, gradient_execution=gradient,
        teacher_hparams=replace(HP, learning_rate=float(learning_rate)),
        max_norm=1.0)
    if transaction.update_steps != 1 or len(transaction.training_authorities) != 1:
        raise AssertionError("C05 source-owned step did not execute exactly once")
    return transaction, gradient, row, targets


def _teacher_selected_source_owned_candidate_step_evidence(
        run_dir, source_context, parent, cache, artifact):
    school = SimpleNamespace(
        stage="RECOVERY_1",
        current_student=SimpleNamespace(
            sha256=candidate_identity_digest(parent.retained_state)),
    )
    bootstrap = {}
    if "c03_lineage" not in parent.teacher_state:
        bootstrap = {
            "legacy_receipt": {"teacher": selection_teacher()},
            "adaptation": adaptation(),
            "prior_region": "legacy-region",
        }
    bound, teacher_policy, teacher_metadata = select_accepted_teacher_visit(
        run_dir, historical_teacher_policy, school, random.Random(17), Settings(),
        "factory/7", {}, "B", capability_id=TARGET, total_capabilities=20,
        **bootstrap)
    visit = BamfVisitProvenance.from_c03_record(bound.identity.to_record())
    transaction, gradient, row, targets = _execute_source_owned_candidate_step_evidence(
        run_dir, source_context, parent, cache, artifact,
        teacher_policy=teacher_policy, teacher_visit_provenance=visit,
        learning_rate=teacher_policy["lr"])
    return transaction, gradient, row, targets, {
        "policy_key": bound.identity.policy_key,
        "policy": teacher_policy,
        "selection_reason": teacher_metadata["selection_reason"],
        "visit": bound.identity.to_record(),
    }


def _source_owned_candidate_step_evidence(run_dir, source_context, parent, cache, artifact):
    return _execute_source_owned_candidate_step_evidence(
        run_dir, source_context, parent, cache, artifact)


def _source_owned_candidate_step(run_dir, source_context, parent, cache, artifact):
    return _source_owned_candidate_step_evidence(
        run_dir, source_context, parent, cache, artifact)[0]


def _source_targets(source_context, parent, artifact, row, authority):
    expected = factory_evaluation_instrument(
        source_context, parent, str(artifact), row,
        source_seed=TRAIN_SEED, source_each=1).case.gold
    route = task_goal_route_decisions(authority.goal)
    if len(route) != 1:
        raise AssertionError("C05 source-owned route decision drift")
    node = authority.goal.expression_or_holes.nodes[0]
    handle = next(
        item.typed.source_handle for item in authority.binding.operands
        if item.typed.type_name == expected.type_name
        and item.typed.value == expected.value)
    selected = next(
        item for item in node.candidate_operand_refs[0]
        if item.source_handle == handle)
    return (DecisionOutput(route[0].decision_id, selected.identity),), {
        route[0].decision_id: True}


def _publish_c05_successor(run_dir, source_context, parent, cache, artifact, transaction):
    evaluation = evaluate_factory_retention_candidate(
        source_context, transaction, str(artifact), TARGET, run_dir=run_dir)
    decision = issue_factory_retention_decision(evaluation)
    if not decision.accepted:
        raise AssertionError(
            "C05 Factory retention did not accept source-owned candidate: "
            f"reason={decision.reason} evidence={decision.evidence_sha256} "
            f"policy={decision.policy_sha256} "
            f"blocking_capability={evaluation.decision.blocking_capability}")
    retained = resolve_candidate(transaction, accepted=True)
    successor = derive_successor_bundle(
        parent, retained, parent_manifest_sha256=cache.accepted_manifest_sha256,
        delivery_events=({
            "event": "BAMF_GENERATION_ACCEPTED",
            "optimizer_step": retained.optimizer_step,
        },))
    with patch(
        "bilqis_mlx.runtime.bamf_bundle.codec.assert_headroom",
        return_value=None,
    ):
        published = accept_and_publish(
            run_dir, successor, retained, decision=decision,
            feature_sha256=successor.extents.factor_map_digest,
            training_authorities=transaction.training_authorities)
    return successor, retained, published


def _publish_disposable_source_qualified_successor(
        run_dir, parent, cache, transaction):
    """Publish a real source-trained step without treating it as C05 learning proof.

    The candidate step itself is produced by the live Factory/B11/B12 path.  The
    acceptance token is deliberately the test-only C05 fixture so B13.2 can
    exercise pointer/lock/cold-resume continuation independently of the separate
    retained-learning acceptance witness.
    """
    retained = resolve_candidate(transaction, accepted=True)
    successor = derive_successor_bundle(
        parent, retained, parent_manifest_sha256=cache.accepted_manifest_sha256,
        delivery_events=({
            "event": "BAMF_GENERATION_ACCEPTED",
            "optimizer_step": retained.optimizer_step,
        },))
    decision = retention_decision(
        parent=parent.retained_state, retained=retained)
    binding = mint_acceptance_binding(
        decision, retained, run_id=successor.run_id,
        generation=successor.generation,
        feature_sha256=successor.extents.factor_map_digest)
    with patch(
        "bilqis_mlx.runtime.bamf_bundle.codec.assert_headroom",
        return_value=None,
    ):
        published = publish_bamf_generation(
            run_dir, successor, acceptance=binding)
    return successor, retained, published


def _assert_published_generation_one(run_dir, retained, published):
    cold = load_accepted_generation(run_dir)
    if (cold.generation != 1
            or candidate_identity_digest(cold.retained_state)
            != candidate_identity_digest(retained)
            or published["generation"] != 1):
        raise AssertionError("C05 source-owned generation-one publication drift")


