"""B13.4 joins the real expanded B01 constructor to complete B13 custody."""
from dataclasses import replace
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import mlx.core as mx

import bilqis_mlx.runtime.bamf_bundle.publication as publication
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_candidate import CandidateState
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
from bilqis_mlx.runtime.bamf_bundle import (
    load_bamf_bundle, publish_bamf_generation, save_bamf_bundle,
)
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
    _reset_execution_cache_owner_for_tests,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    derive_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle.publication.instrumentation import (
    publication_bundle_load, publication_measurement,
)
from bilqis_mlx.runtime.mlx_checkpoint import save_bamf_state_payload
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, bamf_storage_key, create_unbound_bamf_state,
    expected_bamf_shapes,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, publish_genesis,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    genesis_feature_source_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
    acceptance, host_source_authority_patch,
)


@unittest.skipUnless(os.environ.get("BILQIS_BAMF_FULL_WITNESS"),
                     "full disposable B01/B13 CPU schema witness is opt-in")
class ParameterSchemaTests(unittest.TestCase):
    def test_expanded_constructor_manifest_and_full_bundle_have_one_ledger(self):
        previous_device = mx.default_device()
        mx.set_default_device(mx.cpu)
        try:
            self._exercise_complete_schema()
        finally:
            mx.set_default_device(previous_device)

    def _exercise_complete_schema(self):
        original = candidate(parent_state())
        spec = original.topology
        extents = replace(original.extents, semantic_bank_count=2)
        declared = expected_bamf_shapes(spec, extents)
        parameters, initialized, construction = create_unbound_bamf_state(
            spec, extents, run_seed=481)
        names = {item.name for item in declared}
        self.assertEqual(len(names), 215)
        self.assertEqual(sum(item.parameter_count for item in declared), 85_761_254)
        self.assertEqual(set(parameters), names)
        self.assertEqual(set(initialized) - {"step", "learning_rate"}, names)
        self.assertEqual(construction["initialization_status"], "UNBOUND")
        self.assertEqual(GenerationExtents.from_record(
            construction["generation_extents"]), extents)
        self.assertEqual(construction["parameters"], [
            {"name": item.name, "shape": list(item.shape), "dtype": item.dtype,
             "parameters": item.parameter_count, "category": item.category.value,
             "initializer": item.initializer.value, "group": item.group.value,
             "decay": item.decay,
             "storage_keys": {part: bamf_storage_key(item.name, part)
                              for part in ("weight", "m", "v")}}
            for item in declared])
        # An expanded bank must not duplicate shared feature/depth tensors.
        base = expected_bamf_shapes(spec, original.extents)
        self.assertEqual(names - {item.name for item in base},
                         {"identity.bank.1"})
        counts = {item.name: mx.zeros(
            (item.shape[0],) if item.name.startswith(("identity.bank.", "motif.page."))
            or item.name in {"features.type", "features.role", "features.schema"}
            else (), dtype=mx.uint64) for item in declared}
        numerical = AdamWStateTree(
            parameters, {name: initialized[name]["m"] for name in names},
            {name: initialized[name]["v"] for name in names}, counts)
        retained = CandidateState(numerical, original.retained_state.policy,
                                  original.retained_state.allocations, 0)
        value = replace(
            original, extents=extents, retained_state=retained,
            semantic_abi={**original.semantic_abi, "semantic_bank_count": 2,
                          "bank_identities": ["bank:0", "bank:1"]})
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(os.environ, {"BILQIS_DATA_PLANE": str(root / "plane.db")}):
                self._reject_parameter_drift(root, spec, extents, numerical)
                bundle = root / "complete"
                steady_metrics = []
                with publication_measurement(steady_metrics.append):
                    manifest = save_bamf_bundle(value, bundle)
                self.assertEqual(manifest["tensors"]["tensor_count"], 860)
                self.assertEqual(manifest["topology"], spec.to_record())
                self.assertEqual(manifest["extents"], extents.to_record())
                self.assertEqual(manifest["optimizer"]["step"], 0)
                expected_bytes = sum(array.nbytes for tree in (
                    numerical.parameters, numerical.m, numerical.v, numerical.update_counts)
                    for array in tree.values())
                self.assertEqual(manifest["tensors"]["uncompressed_bytes"], expected_bytes)
                self.assertEqual(steady_metrics[0].tensor_bytes_read, 0)
                self.assertGreaterEqual(steady_metrics[0].write_bytes, expected_bytes)
                cold_metrics = []
                with publication_measurement(cold_metrics.append), publication_bundle_load("child"):
                    restored = load_bamf_bundle(
                        bundle, expected_manifest_sha256=manifest["manifest_sha256"])
                self.assertEqual(cold_metrics[0].child_bundle_loads, 1)
                self.assertEqual(cold_metrics[0].tensor_bytes_read, expected_bytes)
                for field in ("parameters", "m", "v", "update_counts"):
                    before = getattr(numerical, field)
                    after = getattr(restored.retained_state.optimizer, field)
                    self.assertEqual(set(after), names)
                    for name in names:
                        self.assertEqual(after[name].shape, before[name].shape, (field, name))
                        self.assertEqual(after[name].dtype, before[name].dtype, (field, name))
                        self.assertTrue(bool(mx.array_equal(after[name], before[name])),
                                        (field, name))
                self.assertEqual(restored.topology, spec)
                self.assertEqual(restored.extents, extents)
                self.assertEqual(restored.teacher_state, value.teacher_state)
                self.assertEqual(restored.retained_state.allocations, retained.allocations)

    def test_realistic_publication_reuses_hot_state_and_cold_retry_rehydrates(self):
        previous_device = mx.default_device()
        mx.set_default_device(mx.cpu)
        try:
            with TemporaryDirectory() as temporary:
                root = Path(temporary)
                run = root / "run"
                with patch.dict(os.environ, {"BILQIS_DATA_PLANE": str(root / "plane.db")}), patch.object(
                        mlx_checkpoint, "assert_headroom"), genesis_feature_source_patch(), \
                        host_source_authority_patch():
                    pointer = publish_genesis(run)
                    _reset_execution_cache_owner_for_tests()
                    parent = load_accepted_generation(run)
                    expected_bytes = sum(
                        array.nbytes
                        for tree in (
                            parent.retained_state.optimizer.parameters,
                            parent.retained_state.optimizer.m,
                            parent.retained_state.optimizer.v,
                            parent.retained_state.optimizer.update_counts,
                        )
                        for array in tree.values())
                    self.assertGreater(expected_bytes, 900_000_000)

                    successor = self._successor(parent, pointer, "FULL_HOT")
                    steady = []
                    pointer = publish_bamf_generation(
                        run, successor,
                        acceptance=acceptance(successor, parent=parent.retained_state),
                        reserve_gib=0., publication_observer=steady.append)
                    self.assertEqual(steady[0].parent_bundle_loads, 0)
                    self.assertEqual(steady[0].child_bundle_loads, 0)
                    self.assertEqual(steady[0].tensor_bytes_read, 0)
                    self.assertGreaterEqual(steady[0].write_bytes, expected_bytes)

                    parent = load_accepted_generation(run)
                    retry = self._successor(parent, pointer, "FULL_RETRY")
                    with patch.object(publication, "_atomic_pointer", side_effect=RuntimeError("crash")):
                        with self.assertRaisesRegex(RuntimeError, "crash"):
                            publish_bamf_generation(
                                run, retry,
                                acceptance=acceptance(retry, parent=parent.retained_state),
                                reserve_gib=0.)

                    _reset_execution_cache_owner_for_tests()
                    recovered = []
                    published = publish_bamf_generation(
                        run, retry,
                        acceptance=acceptance(retry, parent=parent.retained_state),
                        reserve_gib=0., publication_observer=recovered.append)
                    self.assertEqual(published["generation"], retry.generation)
                    # Cold generation-2 recovery authenticates generation 1 and
                    # its generation-0 acceptance ancestor before trusting the
                    # already-written generation-2 child.
                    self.assertEqual(recovered[0].parent_bundle_loads, 2)
                    self.assertEqual(recovered[0].child_bundle_loads, 1)
                    self.assertEqual(recovered[0].tensor_bytes_read, expected_bytes * 3)
        finally:
            _reset_execution_cache_owner_for_tests()
            mx.set_default_device(previous_device)

    @staticmethod
    def _successor(parent, pointer, event):
        retained = replace(
            parent.retained_state,
            optimizer_step=parent.retained_state.optimizer_step + 1)
        return derive_successor_bundle(
            parent, retained,
            parent_manifest_sha256=pointer["manifest_sha256"],
            delivery_events=({"event": event},))

    def _reject_parameter_drift(self, root, spec, extents, numerical):
        for kind in ("missing", "extra", "misowned"):
            trees = [dict(getattr(numerical, name))
                     for name in ("parameters", "m", "v", "update_counts")]
            for tree in trees:
                if kind == "missing":
                    del tree["depth.norm"]
                elif kind == "extra":
                    tree["frame.depth.norm"] = tree["depth.norm"]
                else:
                    tree["frame.depth.norm"] = tree.pop("depth.norm")
            malformed = AdamWStateTree(*trees)
            path = root / (kind + ".safetensors")
            with self.subTest(kind=kind), self.assertRaises(BilqisError):
                save_bamf_state_payload(path, spec, extents, malformed, optimizer_step=0)
            self.assertFalse(path.exists())
