"""B13 execution-generation binding currentness and reuse witnesses."""
from dataclasses import replace
import json
import os
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import mlx.core as mx

import bilqis_mlx.runtime.backbone_identity as identity
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_candidate import begin_candidate, candidate_step
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache, load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    bind_candidate_execution_cache, bind_execution_generation,
    require_candidate_execution_cache,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    HP, NAME, candidate, execution_provenance, parent_state, publish_candidate,
    shape_patch,
)


class ExecutionGenerationBindingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_candidate(self.run, candidate(parent_state()))
            self.parent = load_accepted_generation(self.run)
            self.accepted = bind_accepted_execution_cache(self.run)

    def test_accepted_state_hashes_once_then_reuses_exact_object_binding(self):
        parameters = self.parent.retained_state.optimizer.parameters
        original = identity.bamf_parameter_tree_digest
        with shape_patch(), patch.object(
                identity, "bamf_parameter_tree_digest", wraps=original) as digest:
            first = bind_execution_generation(
                self.accepted, parameters,
                spec=self.parent.topology, extents=self.parent.extents)
            second = bind_execution_generation(
                self.accepted, parameters,
                spec=self.parent.topology, extents=self.parent.extents)
        self.assertIs(first, second)
        self.assertEqual(first.generation_digest, self.accepted.generation_binding)
        self.assertEqual(digest.call_count, 1)

    def test_candidate_state_hashes_once_and_substitution_cannot_reuse_binding(self):
        transaction = begin_candidate(self.parent.retained_state)
        original = identity.bamf_parameter_tree_digest
        with shape_patch(), patch.object(
                identity, "bamf_parameter_tree_digest", wraps=original) as digest:
            speculative = bind_candidate_execution_cache(
                self.accepted, self.parent, transaction,
                spec=self.parent.topology, extents=self.parent.extents)
            first = bind_execution_generation(
                speculative, transaction.optimizer.parameters,
                spec=self.parent.topology, extents=self.parent.extents)
            second = bind_execution_generation(
                speculative, transaction.optimizer.parameters,
                spec=self.parent.topology, extents=self.parent.extents)
        self.assertIs(first, second)
        self.assertEqual(digest.call_count, 1)

        substituted = dict(transaction.optimizer.parameters)
        substituted[NAME] = mx.array(substituted[NAME])
        with shape_patch(), self.assertRaises(BilqisError):
            bind_execution_generation(
                speculative, substituted,
                spec=self.parent.topology, extents=self.parent.extents)

    def test_topology_or_extents_drift_cannot_reuse_candidate_binding(self):
        transaction = begin_candidate(self.parent.retained_state)
        with shape_patch():
            speculative = bind_candidate_execution_cache(
                self.accepted, self.parent, transaction,
                spec=self.parent.topology, extents=self.parent.extents)
        drifted = replace(self.parent.extents, active_semantic_digest="f" * 64)
        with shape_patch(), self.assertRaises(BilqisError):
            bind_execution_generation(
                speculative, transaction.optimizer.parameters,
                spec=self.parent.topology, extents=drifted)

        foreign_topology = SimpleNamespace(digest="e" * 64)
        with shape_patch(), self.assertRaises(BilqisError):
            bind_execution_generation(
                speculative, transaction.optimizer.parameters,
                spec=foreign_topology, extents=self.parent.extents)

    def test_accepted_parent_pointer_drift_invalidates_bound_generation(self):
        parameters = self.parent.retained_state.optimizer.parameters
        with shape_patch():
            bind_execution_generation(
                self.accepted, parameters,
                spec=self.parent.topology, extents=self.parent.extents)
        pointer_path = self.run / "bamf-state.json"
        original = pointer_path.read_bytes()
        pointer = json.loads(original)
        pointer["generation"] += 1
        pointer_path.write_text(json.dumps(pointer, separators=(",", ":")))
        try:
            with shape_patch(), self.assertRaises(BilqisError):
                bind_execution_generation(
                    self.accepted, parameters,
                    spec=self.parent.topology, extents=self.parent.extents)
        finally:
            pointer_path.write_bytes(original)

    def test_optimizer_update_requires_a_fresh_candidate_binding(self):
        transaction = begin_candidate(self.parent.retained_state)
        with shape_patch():
            before = bind_candidate_execution_cache(
                self.accepted, self.parent, transaction,
                spec=self.parent.topology, extents=self.parent.extents)
            updated = candidate_step(
                transaction,
                {NAME: mx.array([[.25, -.5], [0., 0.]], dtype=mx.float32)},
                execution_provenance(
                    transaction.parent, rows=(0,), candidate_step=1,
                    extents=self.parent.extents),
                HP, spec=self.parent.topology, extents=self.parent.extents,
                loss_bearing=True, max_norm=1.)
            with self.assertRaises(BilqisError):
                bind_execution_generation(
                    before, updated.optimizer.parameters,
                    spec=self.parent.topology, extents=self.parent.extents)
            after = bind_candidate_execution_cache(
                self.accepted, self.parent, updated,
                spec=self.parent.topology, extents=self.parent.extents)
            require_candidate_execution_cache(after)
        self.assertIsNot(before._execution_binding, after._execution_binding)
        self.assertNotEqual(before.generation_binding, after.generation_binding)


if __name__ == "__main__":
    unittest.main()
