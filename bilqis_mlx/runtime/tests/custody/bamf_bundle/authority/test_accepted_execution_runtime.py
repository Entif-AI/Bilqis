"""Focused accepted execution-cache custody witnesses."""
from dataclasses import replace
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_candidate import begin_candidate
from bilqis_mlx.runtime.bamf_bundle import source_authority_custody as custody
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache, load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    AcceptedExecutionCache, CandidateExecutionCache,
    bind_candidate_execution_cache, require_accepted_execution_cache,
    require_candidate_execution_cache,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, publish_candidate, shape_patch as _shape_patch,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY


def shape_patch():
    stack = _shape_patch()
    stack.enter_context(patch.object(
        custody, "read_host_system_source_authority_registry",
        return_value=AUTHORITY))
    return stack


class AcceptedExecutionRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def publish(self, source):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_candidate(self.run, source)

    def test_only_accepted_b13_custody_mints_live_execution_cache(self):
        self.publish(candidate(parent_state()))
        with shape_patch():
            cache = bind_accepted_execution_cache(self.run)
            rebound = bind_accepted_execution_cache(self.run)
            self.assertIs(require_accepted_execution_cache(cache), cache)
            self.assertIs(rebound, cache)
            accepted = load_accepted_generation(self.run)
        self.assertEqual(cache.run_id, "fixture-run")
        self.assertEqual(
            cache.motif_manifest.digest,
            accepted.retained_state.allocations.manifest.digest)
        with self.assertRaises(BilqisError):
            AcceptedExecutionCache()

    def test_candidate_execution_cache_is_bound_to_current_parent_and_transaction(self):
        self.publish(candidate(parent_state()))
        with shape_patch():
            accepted = load_accepted_generation(self.run)
            cache = bind_accepted_execution_cache(self.run)
            transaction = begin_candidate(accepted.retained_state)
            speculative = bind_candidate_execution_cache(
                cache, accepted, transaction,
                spec=accepted.topology, extents=accepted.extents)
            self.assertIs(require_candidate_execution_cache(speculative), speculative)
        self.assertEqual(speculative.run_id, accepted.run_id)
        self.assertEqual(speculative.generation, accepted.generation)
        self.assertEqual(
            speculative.accepted_manifest_sha256, cache.accepted_manifest_sha256)
        self.assertEqual(speculative.generation_binding, cache.generation_binding)
        with self.assertRaises(BilqisError):
            CandidateExecutionCache()
        foreign_parent = replace(accepted, retained_state=parent_state())
        with shape_patch(), self.assertRaises(BilqisError):
            bind_candidate_execution_cache(
                cache, foreign_parent, transaction,
                spec=accepted.topology, extents=accepted.extents)


if __name__ == "__main__":
    unittest.main()
