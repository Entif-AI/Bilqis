"""B13.3 derived attention caches never cross accepted-generation custody."""
from __future__ import annotations

from contextlib import ExitStack
from dataclasses import replace
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import mlx.core as mx
import numpy as np

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_candidate import CandidateState
from bilqis_mlx.runtime import mlx_checkpoint
from bilqis_mlx.runtime.atlas_attention import (
    ATTENTION_PARAMETER_NAMES, AttentionScope, ccgqa,
)
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
from bilqis_mlx.runtime.bamf_bundle import (
    publish_atlas_admission_generation, publish_bamf_generation,
)
from bilqis_mlx.runtime.bamf_bundle.atlas_admission import (
    _issue_atlas_admission_binding,
)
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.model_topology_v2 import (
    Initializer, ModelTopologySpecV2, ParameterGroup, ParameterSpec,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    DECLARED, acceptance, candidate, parent_state, publish_candidate,
)


ATTENTION_DECLARED = DECLARED + (
    ParameterSpec("blocks.0.query", (384, 768), Initializer.MATRIX, ParameterGroup.SLOW, True),
    ParameterSpec("blocks.0.key", (192, 768), Initializer.MATRIX, ParameterGroup.SLOW, True),
    ParameterSpec("blocks.0.value", (192, 768), Initializer.MATRIX, ParameterGroup.SLOW, True),
    ParameterSpec("blocks.0.output", (768, 384), Initializer.MATRIX, ParameterGroup.SLOW, True),
    ParameterSpec("blocks.0.conv_q", (384, 3), Initializer.CONV_IDENTITY, ParameterGroup.SLOW, True),
    ParameterSpec("blocks.0.conv_k", (192, 3), Initializer.CONV_IDENTITY, ParameterGroup.SLOW, True),
    ParameterSpec("blocks.0.conv_v", (192, 3), Initializer.CONV_IDENTITY, ParameterGroup.SLOW, True),
)


def _digest(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _shape_patch():
    from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
        genesis_feature_source_patch,
    )
    from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
        host_source_authority_patch,
    )

    stack = ExitStack()
    stack.enter_context(host_source_authority_patch())
    stack.enter_context(genesis_feature_source_patch())
    targets = (
        "bilqis_mlx.runtime.model_topology_v2.expected_bamf_shapes",
        "bilqis_mlx.runtime.topology_v2.ledger.expected_bamf_shapes",
        "bilqis_mlx.runtime.topology_v2.validation.expected_bamf_shapes",
        "bilqis_mlx.runtime.backbone_identity.expected_bamf_shapes",
        "bilqis_mlx.learning.atlas_participation_census.expected_bamf_shapes",
        "bilqis_mlx.learning._retention.atlas_participation_census.expected_bamf_shapes",
    )
    for target in targets:
        stack.enter_context(patch(target, return_value=ATTENTION_DECLARED))
    return stack


def _attention_state() -> CandidateState:
    base = parent_state()
    rng = np.random.default_rng(754)
    parameters = dict(base.optimizer.parameters)
    for item in ATTENTION_DECLARED[len(DECLARED):]:
        parameters[item.name] = mx.array(
            rng.normal(0, .02, item.shape).astype(np.float32))
    moments = {
        name: mx.zeros_like(value) if name not in base.optimizer.m else base.optimizer.m[name]
        for name, value in parameters.items()}
    variances = {
        name: mx.zeros_like(value) if name not in base.optimizer.v else base.optimizer.v[name]
        for name, value in parameters.items()}
    counts = dict(base.optimizer.update_counts)
    counts.update({name: mx.array(0, dtype=mx.uint64)
                   for name in parameters if name not in counts})
    optimizer = AdamWStateTree(parameters, moments, variances, counts)
    return CandidateState(
        optimizer, base.policy, base.allocations, base.optimizer_step, base.custody)


def _attention_view(state: CandidateState) -> dict:
    return {name: state.optimizer.parameters[f"blocks.0.{name}"]
            for name in ATTENTION_PARAMETER_NAMES}


def _publish(run: Path, bundle, *, parent_state_for_acceptance: CandidateState):
    return publish_bamf_generation(
        run, bundle,
        acceptance=acceptance(bundle, parent=parent_state_for_acceptance))


def _cache_for(run: Path, hidden, ids, valid):
    student = admission.load_accepted_generation(run)
    authority = admission.bind_accepted_execution_cache(run)
    params = _attention_view(student.retained_state)
    scope = AttentionScope(ids[:, :3], 0, authority.generation_binding, _digest("prefix"))
    first, cache = ccgqa(params, hidden[:, :3], valid[:, :3], scope)
    return student, authority, params, first, cache


def _assert_rebuild_matches(test, params, hidden, ids, valid, generation, stale):
    next_scope = AttentionScope(
        ids[:, 3:4], 0, generation, _digest("next"),
        parent_prefix_digest=_digest("prefix"))
    with test.assertRaises(BilqisError):
        ccgqa(params, hidden[:, 3:4], valid[:, 3:4], next_scope, cache=stale, offset=3)
    first_scope = AttentionScope(ids[:, :3], 0, generation, _digest("rebuilt"))
    first, rebuilt = ccgqa(params, hidden[:, :3], valid[:, :3], first_scope)
    second_scope = AttentionScope(
        ids[:, 3:4], 0, generation, _digest("rebuilt-next"),
        parent_prefix_digest=_digest("rebuilt"))
    second, _ = ccgqa(params, hidden[:, 3:4], valid[:, 3:4], second_scope,
                      cache=rebuilt, offset=3)
    fresh, _ = ccgqa(params, hidden, valid,
                     AttentionScope(ids, 0, generation, _digest("fresh")))
    np.testing.assert_allclose(
        np.asarray(mx.concatenate((first, second), axis=1)), np.asarray(fresh),
        atol=2e-6, rtol=3e-5)


class CacheSeparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        rng = np.random.default_rng(755)
        self.hidden = mx.array(rng.normal(0, .1, (1, 4, 768)).astype(np.float32))
        self.ids = mx.array([[7, 7, 7, 7]], dtype=mx.int32)
        self.valid = mx.ones((1, 4), dtype=mx.bool_)

    def _publish_initial(self, run: Path, state: CandidateState):
        with _shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_candidate(run, candidate(state))

    def test_generic_parameter_extension_stops_at_c07_boundary(self):
        run = self.root / "extension"
        state = _attention_state()
        first = self._publish_initial(run, state)
        with _shape_patch():
            parent, first_authority, _, _, stale = _cache_for(
                run, self.hidden, self.ids, self.valid)
        successor = replace(
            candidate(parent.retained_state, 1, first["manifest_sha256"]),
            run_identity=parent.run_identity,
            implementation_sha256=parent.implementation_sha256,
            topology=parent.topology,
            extents=parent.extents,
            provenance=parent.provenance,
            semantic_abi=dict(parent.semantic_abi),
            compiler_features=dict(parent.compiler_features),
            correction_frontier=dict(parent.correction_frontier),
            teacher_state=dict(parent.teacher_state),
            evaluation_contract=dict(parent.evaluation_contract),
        )
        extents = replace(successor.extents, active_semantic_digest="8" * 64)
        successor = replace(
            successor, extents=extents,
            semantic_abi={**parent.semantic_abi, "active_set_sha256": "8" * 64},
            transition={**successor.transition, "kind": "PARAMETER_EXTENSION",
                        "invalidate_derived_caches": True})
        with _shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            with self.assertRaises(BilqisError) as failure:
                _publish(
                    run, successor,
                    parent_state_for_acceptance=parent.retained_state)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_ATLAS_ADMISSION_EXECUTOR_REQUIRED")
        self.assertEqual(json.loads((run / "bamf-state.json").read_text())["generation"], 0)

    def test_c07_parameter_extension_invalidates_real_cache_and_rebuilds(self):
        run = self.root / "c07-extension"
        state = _attention_state()
        first = self._publish_initial(run, state)
        with _shape_patch():
            parent, first_authority, _, _, stale = _cache_for(
                run, self.hidden, self.ids, self.valid)
        successor = replace(
            candidate(parent.retained_state, 1, first["manifest_sha256"]),
            run_identity=parent.run_identity,
            implementation_sha256=parent.implementation_sha256,
            topology=parent.topology,
            extents=parent.extents,
            provenance=parent.provenance,
            semantic_abi=dict(parent.semantic_abi),
            compiler_features=dict(parent.compiler_features),
            correction_frontier=dict(parent.correction_frontier),
            teacher_state=dict(parent.teacher_state),
            evaluation_contract=dict(parent.evaluation_contract),
        )
        extents = replace(successor.extents, active_semantic_digest="8" * 64)
        successor = replace(
            successor, extents=extents,
            semantic_abi={**parent.semantic_abi, "active_set_sha256": "8" * 64},
            transition={**successor.transition, "kind": "PARAMETER_EXTENSION",
                        "invalidate_derived_caches": True})
        with _shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            admission = _issue_atlas_admission_binding(
                successor, parent,
                lease_sha256="9" * 64,
                source_approval_sha256="8" * 64,
                proposal_sha256="7" * 64,
                factory_release_sha256="6" * 64,
                staging_receipt_sha256="5" * 64,
                parent_feature_receipt_sha256="4" * 64)
            second = publish_atlas_admission_generation(
                run, successor, admission=admission, reserve_gib=0.)
            student, authority, params, _, _ = _cache_for(
                run, self.hidden, self.ids, self.valid)
        self.assertEqual(student.transition["kind"], "PARAMETER_EXTENSION")
        self.assertTrue(student.transition["invalidate_derived_caches"])
        self.assertEqual(second["generation"], 1)
        self.assertNotEqual(first_authority.generation_binding, authority.generation_binding)
        _assert_rebuild_matches(
            self, params, self.hidden, self.ids, self.valid,
            authority.generation_binding, stale)

    def test_published_model_swap_invalidates_real_cache_and_rebuilds(self):
        run = self.root / "model-swap"
        state = _attention_state()
        first = self._publish_initial(run, state)
        with _shape_patch():
            parent, first_authority, _, _, stale = _cache_for(
                run, self.hidden, self.ids, self.valid)
        params = dict(parent.retained_state.optimizer.parameters)
        params["blocks.0.query"] = params["blocks.0.query"] + mx.array(.001, dtype=mx.float32)
        changed_optimizer = AdamWStateTree(
            params, parent.retained_state.optimizer.m, parent.retained_state.optimizer.v,
            parent.retained_state.optimizer.update_counts)
        changed_state = CandidateState(
            changed_optimizer, parent.retained_state.policy,
            parent.retained_state.allocations, parent.retained_state.optimizer_step,
            parent.retained_state.custody)
        # BAMF-0.2 freezes one topology today. This controlled identity-only variant
        # drives B13's production MODEL_SWAP classifier without changing tensor shapes.
        with patch.object(ModelTopologySpecV2, "__post_init__", return_value=None):
            swapped_topology = replace(ModelTopologySpecV2(), default_run_seed=1)
            successor = replace(
                candidate(changed_state, 1, first["manifest_sha256"]),
                run_identity=parent.run_identity,
                implementation_sha256=parent.implementation_sha256,
                topology=swapped_topology,
                extents=parent.extents,
                provenance=parent.provenance,
                semantic_abi=dict(parent.semantic_abi),
                compiler_features=dict(parent.compiler_features),
                correction_frontier=dict(parent.correction_frontier),
                teacher_state=dict(parent.teacher_state),
                evaluation_contract=dict(parent.evaluation_contract),
                transition={"schema": "bilqis.mlx.bamf-generation-transition/v1",
                            "kind": "MODEL_SWAP", "invalidate_derived_caches": True})
            with _shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
                second = _publish(
                    run, successor,
                    parent_state_for_acceptance=parent.retained_state)
                student, authority, next_params, _, _ = _cache_for(
                    run, self.hidden, self.ids, self.valid)
        self.assertEqual(student.transition["kind"], "MODEL_SWAP")
        self.assertTrue(student.transition["invalidate_derived_caches"])
        self.assertEqual(second["generation"], 1)
        self.assertNotEqual(first_authority.generation_binding, authority.generation_binding)
        _assert_rebuild_matches(
            self, next_params, self.hidden, self.ids, self.valid,
            authority.generation_binding, stale)


if __name__ == "__main__":
    unittest.main()
