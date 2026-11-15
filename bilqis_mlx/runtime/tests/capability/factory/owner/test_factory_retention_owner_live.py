"""Detached full-model C05 diagnostics and B13.2 continuation tests."""
from __future__ import annotations

BILQIS_LEAF_GATE_POLICY = "DETACHED_ONLY"

import json
import os
from pathlib import Path
import tempfile
import unittest

import mlx.core as mx

from bilqis_mlx.learning.atlas_readout import ExecutionMode
from bilqis_mlx.learning.source_atoms.tests.backbone_test_support import SourceBackboneTestBase
from bilqis_mlx.runtime.atlas_model import forward_bamf
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.bamf_bundle import authenticate_bamf_execution_feature_context
from bilqis_mlx.runtime.atlas_capability_support_owner import load_capability_support_owner
from bilqis_mlx.runtime.factory_evaluation_compiler import compile_factory_evaluation_batch
from bilqis_mlx.runtime.factory_retention_owner import _candidate_from_live_parent
from bilqis_mlx.runtime.factory_task_authority import factory_task_authority
from bilqis_mlx.runtime.task_goal_readout import task_goal_route_plan
from bilqis_mlx.runtime.tests.capability.factory.retention.diagnostics.factory_retention_lesson_diagnostic import diagnose_factory_retention_lesson
from bilqis_mlx.runtime.tests.capability.factory.retention.factory_retention_live_support import live_factory_context
from bilqis_mlx.runtime.tests.capability.factory.retention.next_step.factory_retention_next_step_witness import prove_source_qualified_continuation
from bilqis_mlx.runtime.tests.capability.factory.retention.diagnostics.factory_retention_target_diagnostic import diagnose_factory_retention_target
from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
    host_source_authority_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import (
    selection_teacher,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY
from bilqis_mlx.runtime.tests.capability.factory.retention.owner_live_support import (
    TARGET, TRAIN_SEED, _assert_published_generation_one,
    _initialize_generation, _publish_c05_successor,
    _publish_disposable_source_qualified_successor,
    _source_owned_candidate_step, _teacher_selected_source_owned_candidate_step_evidence,
)


def _evaluation_output(source_context, bundle, artifact, row):
    generation = execution_generation_digest(
        bundle.retained_state.optimizer.parameters,
        spec=bundle.topology, extents=bundle.extents)
    compiled = compile_factory_evaluation_batch(
        source_context, bundle, str(artifact), row,
        source_seed=TRAIN_SEED, source_each=1)
    authority = factory_task_authority(
        source_context, compiled, generation_binding=generation)
    feature_context = authenticate_bamf_execution_feature_context(
        bundle, str(artifact), source_context.run_dir)
    plan = task_goal_route_plan(
        authority.goal, compiled, feature_context.snapshot, generation)
    output = forward_bamf(
        bundle.retained_state.optimizer.parameters,
        compiled, plan, ExecutionMode.INFERENCE, None)
    return compiled, output


def _target_summary(output, target):
    record = next(
        item for item in output.decisions
        if item.decision_id == target.decision_id)
    logits = [float(value) for value in record.logits.tolist()]
    index = record.candidates.index(target.value)
    others = [value for offset, value in enumerate(logits) if offset != index]
    return {
        "candidates": list(record.candidates),
        "logits": logits,
        "gold": target.value,
        "gold_margin": logits[index] - max(others),
        "committed": next(
            item.value for item in output.committed
            if item.decision_id == target.decision_id),
    }

class FactoryRetentionOwnerLiveTests(SourceBackboneTestBase):
    def setUp(self):
        if not mx.metal.is_available():
            self.skipTest("B13.2 source witness requires Apple Metal")
        artifact = os.environ.get("BILQIS_A01_ATLAS_BUNDLE")
        if not artifact:
            self.skipTest("BILQIS_A01_ATLAS_BUNDLE fixture is not mounted")
        self.artifact = Path(artifact)
        if not self.artifact.is_dir():
            self.skipTest("BILQIS_A01_ATLAS_BUNDLE fixture is not mounted")
        previous_device = mx.default_device()
        mx.set_default_device(mx.gpu)
        self.addCleanup(mx.set_default_device, previous_device)
        super().setUp()
        self.enterContext(host_source_authority_patch(AUTHORITY))
        self.root = Path.cwd()
        self.source = (self.root / "vendor/legacy-v16").resolve()
        if not self.source.is_dir():
            self.skipTest("pinned legacy source fixture is not mounted")

    def test_source_owned_c05_target_diagnostic(self):
        source_context, _ = live_factory_context(self.root, self.source)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            parent, cache, source_context = _initialize_generation(
                run_dir, source_context, self.snapshot, self.artifact)
            transaction = _source_owned_candidate_step(
                run_dir, source_context, parent, cache, self.artifact)
            receipt = diagnose_factory_retention_target(
                source_context, transaction, str(self.artifact), TARGET,
                run_dir=run_dir)
            self.assertFalse(receipt["authorizing"])
            self.assertEqual(receipt["total"], 6)
            print("C05_TARGET_DIAGNOSTIC " + json.dumps(receipt, sort_keys=True))

    def test_source_owned_c05_lesson_diagnostic(self):
        source_context, _ = live_factory_context(self.root, self.source)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            parent, cache, source_context = _initialize_generation(
                run_dir, source_context, self.snapshot, self.artifact)
            transaction = _source_owned_candidate_step(
                run_dir, source_context, parent, cache, self.artifact)
            receipt = diagnose_factory_retention_lesson(
                source_context, transaction, str(self.artifact), TARGET,
                run_dir=run_dir)
            self.assertFalse(receipt["authorizing"])
            self.assertEqual(receipt["total"], 24)
            self.assertEqual(len(receipt["lesson_capabilities"]), 4)
            print("C05_LESSON_DIAGNOSTIC " + json.dumps(receipt, sort_keys=True))

    def test_source_owned_training_step_diagnostic(self):
        source_context, _ = live_factory_context(self.root, self.source)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            parent, cache, source_context = _initialize_generation(
                run_dir, source_context, self.snapshot, self.artifact)
            transaction, gradient, row, targets, teacher = _teacher_selected_source_owned_candidate_step_evidence(
                run_dir, source_context, parent, cache, self.artifact)
            _, candidate_bundle, _, _ = _candidate_from_live_parent(run_dir, transaction)
            target = targets[0]
            parent_compiled, before = _evaluation_output(
                source_context, parent, self.artifact, row)
            candidate_compiled, after = _evaluation_output(
                source_context, candidate_bundle, self.artifact, row)
            self.assertEqual(parent_compiled.sources, candidate_compiled.sources)
            self.assertEqual(
                parent_compiled.compiled.compiled,
                candidate_compiled.compiled.compiled)
            before_summary = _target_summary(before, target)
            after_summary = _target_summary(after, target)
            self.assertEqual(before_summary["candidates"], after_summary["candidates"])
            self.assertGreater(
                after_summary["gold_margin"], before_summary["gold_margin"])
            legacy_teacher = selection_teacher()
            self.assertIn(teacher["policy_key"], legacy_teacher["strategies"])
            self.assertEqual(
                teacher["policy"], legacy_teacher["strategies"][teacher["policy_key"]])
            receipt = {
                "schema": "bilqis.mlx.c05-training-step-diagnostic/v1",
                "authorizing": False,
                "row_id": row["id"],
                "gold": row["gold"],
                "loss_total": float(gradient.loss_total.item()),
                "before": before_summary,
                "after": after_summary,
                "gold_margin_gain": (
                    after_summary["gold_margin"] - before_summary["gold_margin"]),
                "teacher": teacher,
                "parent_generation": before.generation_binding,
                "candidate_generation": after.generation_binding,
            }
            print("C05_TRAINING_STEP_DIAGNOSTIC " + json.dumps(receipt, sort_keys=True))

    def test_source_qualified_candidate_can_publish_then_continue(self):
        source_context, _ = live_factory_context(self.root, self.source)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            parent, cache, source_context = _initialize_generation(
                run_dir, source_context, self.snapshot, self.artifact)
            transaction = _source_owned_candidate_step(
                run_dir, source_context, parent, cache, self.artifact)
            successor, retained, published = _publish_disposable_source_qualified_successor(
                run_dir, parent, cache, transaction)
            _assert_published_generation_one(run_dir, retained, published)
            witness = prove_source_qualified_continuation(
                run_dir, source_context, self.artifact, successor, published,
                root=self.root, source=self.source, target=TARGET)
            self.assertTrue(witness["no_generation_2"])
            print("B13_2_BACKEND_HANDOFF " + json.dumps(witness, sort_keys=True))

    def test_accepted_c05_candidate_materializes_capability_support(self):
        source_context, _ = live_factory_context(self.root, self.source)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            parent, cache, source_context = _initialize_generation(
                run_dir, source_context, self.snapshot, self.artifact)
            transaction, _gradient, row, targets, teacher = (
                _teacher_selected_source_owned_candidate_step_evidence(
                    run_dir, source_context, parent, cache, self.artifact))
            _, candidate_bundle, _, _ = _candidate_from_live_parent(run_dir, transaction)
            target = targets[0]
            parent_compiled, before = _evaluation_output(
                source_context, parent, self.artifact, row)
            candidate_compiled, after = _evaluation_output(
                source_context, candidate_bundle, self.artifact, row)
            self.assertEqual(parent_compiled.sources, candidate_compiled.sources)
            self.assertEqual(
                parent_compiled.compiled.compiled,
                candidate_compiled.compiled.compiled)
            before_summary = _target_summary(before, target)
            after_summary = _target_summary(after, target)
            self.assertEqual(before_summary["candidates"], after_summary["candidates"])
            self.assertGreater(
                after_summary["gold_margin"], before_summary["gold_margin"])
            self.assertGreater(after_summary["gold_margin"], 0.0)
            self.assertNotEqual(before_summary["committed"], target.value)
            self.assertEqual(after_summary["committed"], target.value)
            legacy_teacher = selection_teacher()
            self.assertIn(teacher["policy_key"], legacy_teacher["strategies"])
            self.assertEqual(
                teacher["policy"], legacy_teacher["strategies"][teacher["policy_key"]])
            _successor, _retained, published = _publish_c05_successor(
                run_dir, source_context, parent, cache, self.artifact, transaction)
            owner = load_capability_support_owner(run_dir, TARGET)
            self.assertEqual(
                owner.support.retained_generation_sha256,
                published["manifest_sha256"])
            self.assertEqual(owner.capability_id, TARGET)
            self.assertTrue(owner.support.source_anchor_ids)


if __name__ == "__main__":
    unittest.main()
