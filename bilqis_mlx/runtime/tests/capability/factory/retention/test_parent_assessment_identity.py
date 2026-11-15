"""Exercise real candidate identity through the parent assessment cache.

Only the accepted-cache authentication boundary is isolated; this is not a
live publication-authority test.
"""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.learning._retention._atlas_candidate.identity import (
    LEGACY_IDENTITY_SCHEME, RAW_IDENTITY_SCHEME,
)
from bilqis_mlx.learning.atlas_candidate import CandidateState
from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.learning.atlas_engram_transaction import MotifAllocationSnapshot
from bilqis_mlx.learning.atlas_plasticity import PlasticityPolicy
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
from bilqis_mlx.runtime.capability_retention import CompleteSolver
from bilqis_mlx.runtime._factory_parent_assessment_cache import (
    clear_parent_assessment_cache, factory_parent_assessment_identity,
    use_parent_assessment,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    PARENT, _screen_inputs,
)


def _state(scheme):
    name = "weight"
    optimizer = AdamWStateTree(
        {name: mx.array([[1.0], [2.0]], dtype=mx.float32)},
        {name: mx.array([[0.1], [0.2]], dtype=mx.float32)},
        {name: mx.array([[0.3], [0.4]], dtype=mx.float32)},
        {name: mx.array([2, 2], dtype=mx.uint64)},
    )
    return CandidateState(
        optimizer, PlasticityPolicy("ADAPTIVE", 0, ()),
        MotifAllocationSnapshot(MotifManifest("a" * 64)), 2,
        identity_scheme=scheme,
    )


class ParentAssessmentIdentityIntegrationTests(unittest.TestCase):
    def setUp(self):
        clear_parent_assessment_cache()
        parent_solver, _, _, _, cohorts = _screen_inputs()
        self.cohort = cohorts[2]
        self.calls = []

        def counted(goal, generation):
            self.calls.append(goal.goal_id)
            return parent_solver.context_for(goal, generation)

        self.solver = CompleteSolver(counted, parent_solver.budget)
        self.cache = SimpleNamespace(
            run_id="identity-cache-test", generation=1,
            accepted_manifest_sha256="1" * 64, generation_binding=PARENT,
            source_authority_registry_sha256="2" * 64,
        )
        self.context = SimpleNamespace(
            release=SimpleNamespace(release_sha256="3" * 64,
                                    semantic_catalog_sha256="4" * 64),
            graph={},
        )

    def tearDown(self):
        clear_parent_assessment_cache()

    def identity(self, state):
        parent = SimpleNamespace(
            run_id=self.cache.run_id, generation=self.cache.generation,
            retained_state=state, implementation_sha256="5" * 64,
            topology=SimpleNamespace(digest="6" * 64),
            extents=SimpleNamespace(digest="7" * 64),
            correction_frontier={}, semantic_abi={}, compiler_features={},
            evaluation_contract={},
        )
        with patch(
                "bilqis_mlx.runtime._factory_parent_assessment_cache."
                "require_accepted_execution_cache", return_value=self.cache):
            return factory_parent_assessment_identity(
                self.context, parent, self.cache, self.cohort, self.solver, PARENT)

    def assess(self, identity):
        return use_parent_assessment(identity, self.solver, self.cohort, PARENT)[1]

    def test_mutable_optimizer_content_invalidates_reuse_for_both_schemes(self):
        for scheme in (LEGACY_IDENTITY_SCHEME, RAW_IDENTITY_SCHEME):
            for group in ("parameters", "m", "v", "update_counts"):
                with self.subTest(scheme=scheme, group=group):
                    clear_parent_assessment_cache()
                    state = _state(scheme)
                    identity = self.identity(state)
                    start = len(self.calls)
                    self.assertFalse(self.assess(identity).reused)
                    self.assertTrue(self.assess(self.identity(state)).reused)
                    self.assertEqual(len(self.calls) - start, len(self.cohort.cases))

                    tensor = getattr(state.optimizer, group)["weight"]
                    if group == "update_counts":
                        tensor[0] = mx.array(3, dtype=mx.uint64)
                    else:
                        tensor[0] = 5.0
                    changed = self.identity(state)
                    self.assertNotEqual(changed.parent_candidate_sha256,
                                        identity.parent_candidate_sha256)
                    self.assertFalse(self.assess(changed).reused)
                    self.assertEqual(len(self.calls) - start, 2 * len(self.cohort.cases))

    def test_equal_numerical_state_in_different_schemes_does_not_reuse(self):
        legacy = self.identity(_state(LEGACY_IDENTITY_SCHEME))
        raw = self.identity(_state(RAW_IDENTITY_SCHEME))
        self.assertNotEqual(legacy.parent_candidate_sha256, raw.parent_candidate_sha256)
        self.assertFalse(self.assess(legacy).reused)
        self.assertFalse(self.assess(raw).reused)


if __name__ == "__main__":
    unittest.main()
