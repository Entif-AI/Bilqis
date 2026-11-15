"""#1238 process-local full CandidateState identity-binding witnesses."""
from types import MappingProxyType
from unittest import TestCase
from unittest.mock import patch

import mlx.core as mx
import numpy as np

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_candidate import CandidateCustodyIdentity, CandidateState
from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.learning.atlas_engram_transaction import MotifAllocationSnapshot
from bilqis_mlx.learning.atlas_plasticity import IdentityRowAge, PlasticityPolicy
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
from bilqis_mlx.runtime.model_topology_v2 import GenerationExtents, ModelTopologySpecV2
from bilqis_mlx.learning._retention._atlas_candidate.identity import candidate_identity_digest
from bilqis_mlx.learning._retention._atlas_candidate.identity_binding import (
    _reset_candidate_identity_metrics_for_tests,
    bind_candidate_identity,
    candidate_identity_for_state,
    candidate_identity_metrics_snapshot,
    mark_candidate_state_unbindable,
    require_candidate_identity_binding,
)


RELEASE = "f" * 64


def _state():
    name = "identity.bank.0"
    values = mx.array([[.5, -.25], [1., 2.]], dtype=mx.float32)
    optimizer = AdamWStateTree(
        {name: values}, {name: mx.ones_like(values) * .1},
        {name: mx.ones_like(values) * .01},
        {name: mx.array([2, 3], dtype=mx.uint64)})
    allocations = MotifAllocationSnapshot(MotifManifest(RELEASE))
    topology = ModelTopologySpecV2()
    extents = GenerationExtents(
        1, 1, "a" * 64, allocations.manifest.digest, "c" * 64)
    state = CandidateState(
        optimizer,
        PlasticityPolicy("ADAPTIVE", 7, (
            IdentityRowAge(0, 0, 7), IdentityRowAge(0, 1, 2))),
        allocations, 11,
        CandidateCustodyIdentity(
            "fixture-run", 0, "6" * 64, topology.digest, extents.digest))
    return state, topology.digest, extents.digest


class CandidateIdentityBindingTests(TestCase):
    def setUp(self):
        _reset_candidate_identity_metrics_for_tests()

    def test_first_bind_hashes_once_and_require_reuses_without_hashing(self):
        state, topology, extents = _state()
        expected = candidate_identity_digest(state)
        _reset_candidate_identity_metrics_for_tests()
        binding = bind_candidate_identity(
            state, topology, extents, expected_digest=expected)
        first = candidate_identity_metrics_snapshot()
        self.assertEqual(first["candidate_identity_full_computations"], 1)
        self.assertGreater(first["candidate_identity_numerical_bytes_hashed"], 0)

        self.assertIs(
            require_candidate_identity_binding(state, topology, extents), binding)
        self.assertIs(bind_candidate_identity(state, topology, extents), binding)
        after = candidate_identity_metrics_snapshot()
        self.assertEqual(after["candidate_identity_full_computations"], 1)
        self.assertGreaterEqual(after["candidate_identity_require_calls"], 2)
        self.assertEqual(after["candidate_identity_binding_issues"], 1)
        self.assertEqual(after["candidate_identity_binding_reuses"], 1)

    def test_protected_storage_rejects_mlx_numpy_memoryview_and_dlpack_mutation(self):
        state, topology, extents = _state()
        bind_candidate_identity(state, topology, extents)
        array = state.optimizer.parameters["identity.bank.0"]
        with self.assertRaises(RuntimeError):
            array[0, 0] = 9
        exported = np.asarray(array)
        self.assertFalse(exported.flags.writeable)
        self.assertTrue(memoryview(array).readonly)
        with self.assertRaises(ValueError):
            exported[0, 0] = 9
        with self.assertRaises(RuntimeError):
            array.__dlpack__()

    def test_currentness_rejects_topology_policy_and_tensor_object_drift(self):
        state, topology, extents = _state()
        binding = bind_candidate_identity(state, topology, extents)
        with self.assertRaises(BilqisError):
            require_candidate_identity_binding(state, "b" * 64, extents, binding)

        original_policy = state.policy
        object.__setattr__(state, "policy", PlasticityPolicy(
            "ADAPTIVE", 8, original_policy.row_ages))
        with self.assertRaises(BilqisError):
            require_candidate_identity_binding(state, topology, extents, binding)
        object.__setattr__(state, "policy", original_policy)

        original = state.optimizer.parameters
        replacement = dict(original)
        replacement["identity.bank.0"] = mx.array(replacement["identity.bank.0"])
        object.__setattr__(state.optimizer, "parameters", MappingProxyType(replacement))
        with self.assertRaises(BilqisError):
            require_candidate_identity_binding(state, topology, extents, binding)

    def test_expected_digest_mismatch_never_issues_binding(self):
        state, topology, extents = _state()
        with self.assertRaises(BilqisError):
            bind_candidate_identity(
                state, topology, extents, expected_digest="0" * 64)
        metrics = candidate_identity_metrics_snapshot()
        self.assertEqual(metrics["candidate_identity_full_computations"], 1)
        self.assertEqual(metrics["candidate_identity_binding_issues"], 0)

    def test_explicit_unbindable_state_uses_canonical_fallback(self):
        state, topology, extents = _state()
        mark_candidate_state_unbindable(state, "CALLER_OWNED_NUMERICAL_STATE")
        with patch(
            "bilqis_mlx.learning._retention._atlas_candidate.identity_binding."
            "candidate_identity_binding_supported", return_value=False,
        ):
            self.assertEqual(
                candidate_identity_for_state(state, topology, extents),
                candidate_identity_digest(state))

