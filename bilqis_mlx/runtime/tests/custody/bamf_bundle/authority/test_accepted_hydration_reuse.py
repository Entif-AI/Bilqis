"""Issue #1230: one numerical hydration per unchanged accepted generation."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
    _reset_execution_cache_owner_for_tests,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache, load_accepted_generation,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, next_accepted_step, parent_state, publish_candidate, shape_patch,
)


class AcceptedHydrationReuseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        _reset_execution_cache_owner_for_tests()
        self.environment.stop()
        self.temporary.cleanup()

    def publish(self, source):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_candidate(self.run, source)

    def test_unchanged_generation_reuses_exact_student_after_one_payload_load(self):
        self.publish(candidate(parent_state()))
        _reset_execution_cache_owner_for_tests()
        original = mlx_checkpoint.load_bamf_state_payload
        with shape_patch(), patch.object(
                mlx_checkpoint, "load_bamf_state_payload", wraps=original) as payload:
            first = load_accepted_generation(self.run)
            cache = bind_accepted_execution_cache(self.run)
            second = load_accepted_generation(self.run)
            rebound = bind_accepted_execution_cache(self.run)
        self.assertIs(second, first)
        self.assertIs(rebound, cache)
        self.assertEqual(payload.call_count, 1)

    def test_new_generation_hydrates_once_and_cold_reset_rechecks_lineage(self):
        first_pointer = self.publish(candidate(parent_state()))
        _reset_execution_cache_owner_for_tests()
        original = mlx_checkpoint.load_bamf_state_payload
        with shape_patch(), patch.object(
                mlx_checkpoint, "load_bamf_state_payload", wraps=original) as payload:
            first = load_accepted_generation(self.run)
            self.assertIs(load_accepted_generation(self.run), first)
        self.assertEqual(payload.call_count, 1)

        successor = candidate(
            next_accepted_step(parent_state()), generation=1,
            parent=first_pointer["manifest_sha256"])
        self.publish(successor)
        with shape_patch(), patch.object(
                mlx_checkpoint, "load_bamf_state_payload", wraps=original) as payload:
            second = load_accepted_generation(self.run)
            self.assertIs(load_accepted_generation(self.run), second)
        self.assertIsNot(second, first)
        self.assertEqual(payload.call_count, 1)

        _reset_execution_cache_owner_for_tests()
        with shape_patch(), patch.object(
                mlx_checkpoint, "load_bamf_state_payload", wraps=original) as payload:
            cold = load_accepted_generation(self.run)
            self.assertIs(load_accepted_generation(self.run), cold)
        self.assertEqual(cold.generation, 1)
        # A true process restart intentionally rehydrates the historical parent
        # once as part of the pre-existing acceptance-lineage verification.
        self.assertEqual(payload.call_count, 2)


if __name__ == "__main__":
    unittest.main()
