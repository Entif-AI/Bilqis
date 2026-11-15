"""B13.4 joins the real expanded B01 constructor to complete B13 custody."""
from dataclasses import replace
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_candidate import CandidateState
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
from bilqis_mlx.runtime.bamf_bundle import load_bamf_bundle, save_bamf_bundle
from bilqis_mlx.runtime.bamf_bundle.publication.instrumentation import (
    publication_bundle_load, publication_measurement,
)
from bilqis_mlx.runtime.mlx_checkpoint import save_bamf_state_payload
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, bamf_storage_key, create_unbound_bamf_state,
    expected_bamf_shapes,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state,
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
