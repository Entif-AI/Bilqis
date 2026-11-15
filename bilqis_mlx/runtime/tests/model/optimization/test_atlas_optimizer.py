"""Private native AdamW count proofs on disposable numerical tensors."""
import unittest
from unittest.mock import patch

import mlx.core as mx
import mlx.optimizers as optim
import numpy as np

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters, AdamWStateTree, _adamw_update
from .optimizer_step_probe import realistic_step_report


class AdamWCountsTests(unittest.TestCase):
    def setUp(self):
        self.hp=AdamWHyperparameters(.00013,(.9,.95),1e-8,.01)

    def state(self, rowwise=True):
        parameters={"fixture.bank":mx.array([[.5,-.25],[1.,2.],[3.,4.]],dtype=mx.float32)}
        counts=mx.array([0,2,0],dtype=mx.uint64) if rowwise else mx.array(0,dtype=mx.uint64)
        return AdamWStateTree(parameters,{name:mx.zeros_like(value) for name,value in parameters.items()},
                             {name:mx.zeros_like(value) for name,value in parameters.items()},
                             {"fixture.bank":counts})

    def update(self,parent,mask,gradient=None,decay=True,loss_bearing=True):
        gradient=mx.full((3,2),.2,dtype=mx.float32) if gradient is None else gradient
        return _adamw_update(parent,{"fixture.bank":gradient},{"fixture.bank":mask},self.hp,
                             decay={"fixture.bank":decay},loss_bearing=loss_bearing)

    def test_whole_tensor_step_is_exact_native_mlx_adamw(self):
        parent=self.state(False)
        gradient=mx.full((3,2),.2,dtype=mx.float32)
        actual=self.update(parent,mx.array(True),gradient)
        native=optim.AdamW(learning_rate=self.hp.learning_rate,betas=self.hp.betas,eps=self.hp.eps,
                           weight_decay=self.hp.weight_decay,bias_correction=True)
        expected=native.apply_gradients({"fixture.bank":gradient},dict(parent.parameters))
        np.testing.assert_array_equal(np.asarray(actual.parameters["fixture.bank"]),np.asarray(expected["fixture.bank"]))
        for field in ("m","v"):
            np.testing.assert_array_equal(np.asarray(getattr(actual,field)["fixture.bank"]),
                                          np.asarray(native.state["fixture.bank"][field]))
        self.assertEqual(int(actual.update_counts["fixture.bank"]),1)
        self.assertEqual(int(parent.update_counts["fixture.bank"]),0)

    def test_divergent_row_counts_match_independent_native_rows_and_freeze_others(self):
        parent=self.state()
        gradient=mx.array([[.1,.3],[.2,-.5],[99999.,-99999.]],dtype=mx.float32)
        actual=self.update(parent,mx.array([True,True,False]),gradient)
        for row in (0,1):
            native=optim.AdamW(learning_rate=self.hp.learning_rate,betas=self.hp.betas,eps=self.hp.eps,
                               weight_decay=self.hp.weight_decay,bias_correction=True)
            native.state={"step":parent.update_counts["fixture.bank"][row],
                          "learning_rate":mx.array(self.hp.learning_rate,dtype=mx.float32),
                          "p":{"m":parent.m["fixture.bank"][row],"v":parent.v["fixture.bank"][row]}}
            expected=native.apply_gradients({"p":gradient[row]},{"p":parent.parameters["fixture.bank"][row]})
            np.testing.assert_array_equal(np.asarray(actual.parameters["fixture.bank"][row]),np.asarray(expected["p"]))
        for field in ("parameters","m","v","update_counts"):
            np.testing.assert_array_equal(np.asarray(getattr(actual,field)["fixture.bank"][2]),
                                          np.asarray(getattr(parent,field)["fixture.bank"][2]))
        np.testing.assert_array_equal(np.asarray(actual.update_counts["fixture.bank"]),[1,3,0])

    def test_two_fast_then_full_preserves_row_local_history(self):
        actual=self.state()
        natives=[]
        for row in range(3):
            native=optim.AdamW(learning_rate=self.hp.learning_rate,betas=self.hp.betas,eps=self.hp.eps,
                               weight_decay=self.hp.weight_decay,bias_correction=True)
            native.state={"step":actual.update_counts["fixture.bank"][row],
                          "learning_rate":mx.array(self.hp.learning_rate,dtype=mx.float32),
                          "p":{"m":actual.m["fixture.bank"][row],"v":actual.v["fixture.bank"][row]}}
            natives.append((native,actual.parameters["fixture.bank"][row]))
        for mask in ([True,False,False],[True,False,False],[True,True,True]):
            actual=self.update(actual,mx.array(mask))
            for row,participates in enumerate(mask):
                if participates:
                    optimizer,value=natives[row]
                    natives[row]=(optimizer,optimizer.apply_gradients({"p":mx.full((2,),.2)}, {"p":value})["p"])
        np.testing.assert_array_equal(np.asarray(actual.parameters["fixture.bank"]),
                                      np.stack([np.asarray(value) for _,value in natives]))
        np.testing.assert_array_equal(np.asarray(actual.update_counts["fixture.bank"]),[3,3,1])

    def test_zero_gradient_participates_but_frozen_and_no_loss_preserve_objects(self):
        parent=self.state()
        actual=self.update(parent,mx.array([True,False,False]),mx.zeros((3,2)))
        self.assertEqual(int(actual.update_counts["fixture.bank"][0]),1)
        self.assertLess(float(actual.parameters["fixture.bank"][0,0]),float(parent.parameters["fixture.bank"][0,0]))
        no_decay=self.update(parent,mx.array([True,False,False]),mx.zeros((3,2)),decay=False)
        np.testing.assert_array_equal(np.asarray(no_decay.parameters["fixture.bank"]),np.asarray(parent.parameters["fixture.bank"]))
        self.assertIs(self.update(parent,mx.array([False,False,False])),parent)
        self.assertIs(self.update(parent,mx.array([True,True,True]),loss_bearing=False),parent)

    def test_invalid_masks_nonfinite_gradient_and_count_overflow_fail_without_mutation(self):
        parent=self.state()
        before=np.asarray(parent.parameters["fixture.bank"]).copy()
        for mask in (mx.array([1,0,0]),mx.array(True),mx.array([True,False])):
            with self.assertRaises(BilqisError):
                self.update(parent,mask)
        with self.assertRaises(BilqisError):
            self.update(parent,mx.array([True,False,False]),mx.full((3,2),float("nan")))
        counts=mx.array(np.array([2**64-1,2,0],dtype=np.uint64))
        overflow=AdamWStateTree(parent.parameters,parent.m,parent.v,{"fixture.bank":counts})
        with self.assertRaises(BilqisError):
            self.update(overflow,mx.array([True,False,False]))
        np.testing.assert_array_equal(np.asarray(parent.parameters["fixture.bank"]),before)

    def test_invalid_state_and_hyperparameters_fail_closed(self):
        parent = self.state()
        for counts in (mx.array([0, 0, 0]), mx.zeros((3, 1), dtype=mx.uint64)):
            with self.assertRaises(BilqisError):
                AdamWStateTree(parent.parameters, parent.m, parent.v, {"fixture.bank": counts})
        with self.assertRaises(BilqisError):
            AdamWStateTree(parent.parameters, {}, parent.v, parent.update_counts)
        with self.assertRaises(BilqisError):
            AdamWStateTree(parent.parameters, parent.m, {"fixture.bank": -mx.ones((3, 2))},
                           parent.update_counts)
        for values in ((float("nan"), (.9, .95), 1e-8, .01),
                       (.1, (1., .95), 1e-8, .01), (.1, (.9, .95), 0., .01),
                       (.1, (.9, .95), 1e-8, -1.)):
            with self.assertRaises(BilqisError):
                AdamWHyperparameters(*values)

    def test_frozen_max_count_and_parent_moments_preserved(self):
        parent = self.state()
        parent = AdamWStateTree(parent.parameters,
                               {"fixture.bank": mx.full((3, 2), .1)},
                               {"fixture.bank": mx.full((3, 2), .2)},
                               {"fixture.bank": mx.array(np.array([0, 2**64-1, 0], dtype=np.uint64))})
        before = {field: np.asarray(getattr(parent, field)["fixture.bank"]).copy()
                  for field in ("parameters", "m", "v", "update_counts")}
        actual = self.update(parent, mx.array([True, False, False]))
        for field, value in before.items():
            np.testing.assert_array_equal(np.asarray(getattr(parent, field)["fixture.bank"]), value)
            np.testing.assert_array_equal(np.asarray(getattr(actual, field)["fixture.bank"])[1:], value[1:])

    def test_no_loss_and_invalid_calls_preserve_mapping_identity(self):
        parent = self.state()
        fields = ("parameters", "m", "v", "update_counts")
        original = tuple(getattr(parent, field) for field in fields)
        self.assertIs(self.update(parent, mx.array([True, True, True]), loss_bearing=False), parent)
        for field, value in zip(fields, original):
            self.assertIs(getattr(parent, field), value)
        with self.assertRaises(BilqisError):
            self.update(parent, mx.array(True))
        for field, value in zip(fields, original):
            self.assertIs(getattr(parent, field), value)

    def test_scalar_overflow_rejects_and_no_loss_preserves_parent(self):
        parent = self.state(False)
        parent = AdamWStateTree(parent.parameters, parent.m, parent.v,
                               {"fixture.bank": mx.array(np.array(2**64-1, dtype=np.uint64))})
        mappings = tuple(getattr(parent, field) for field in ("parameters", "m", "v", "update_counts"))
        with self.assertRaises(BilqisError):
            self.update(parent, mx.array(True))
        self.assertIs(self.update(parent, mx.array(True), loss_bearing=False), parent)
        for field, value in zip(("parameters", "m", "v", "update_counts"), mappings):
            self.assertIs(getattr(parent, field), value)

    def test_zero_gradient_nonzero_moments_match_native(self):
        parent = self.state()
        parent = AdamWStateTree(parent.parameters, {"fixture.bank": mx.full((3, 2), .1)},
                               {"fixture.bank": mx.full((3, 2), .2)}, parent.update_counts)
        native = optim.AdamW(learning_rate=self.hp.learning_rate, betas=self.hp.betas,
                             eps=self.hp.eps, weight_decay=0., bias_correction=True)
        native.state = {"step": parent.update_counts["fixture.bank"][1],
                        "learning_rate": mx.array(self.hp.learning_rate, dtype=mx.float32),
                        "p": {"m": parent.m["fixture.bank"][1], "v": parent.v["fixture.bank"][1]}}
        expected = native.apply_gradients({"p": mx.zeros((2,))}, {"p": parent.parameters["fixture.bank"][1]})
        actual = self.update(parent, mx.array([False, True, False]), mx.zeros((3, 2)), decay=False)
        np.testing.assert_array_equal(np.asarray(actual.parameters["fixture.bank"][1]), np.asarray(expected["p"]))
        for field in ("m", "v"):
            np.testing.assert_array_equal(np.asarray(getattr(actual, field)["fixture.bank"][1]),
                                          np.asarray(native.state["p"][field]))
        self.assertEqual(int(actual.update_counts["fixture.bank"][1]), 3)
        for field in ("parameters", "m", "v", "update_counts"):
            for row in (0, 2):
                np.testing.assert_array_equal(np.asarray(getattr(actual, field)["fixture.bank"][row]),
                                              np.asarray(getattr(parent, field)["fixture.bank"][row]))

    def test_mask_precedes_global_clip_even_for_huge_frozen_gradients(self):
        from bilqis_mlx.runtime.atlas_optimizer import _masked_clipped_gradients
        parent = self.state()
        mask = {"fixture.bank": mx.array([True, False, False])}
        small = {"fixture.bank": mx.array([[3., 4.], [0., 0.], [0., 0.]])}
        huge = {"fixture.bank": mx.array([[3., 4.], [3e38, -3e38], [3e38, 3e38]])}
        clipped, norm = _masked_clipped_gradients(parent, huge, mask, max_norm=1.)
        reference, reference_norm = _masked_clipped_gradients(parent, small, mask, max_norm=1.)
        self.assertEqual(float(norm), 5.)
        self.assertEqual(float(reference_norm), 5.)
        np.testing.assert_array_equal(np.asarray(clipped["fixture.bank"]), np.asarray(reference["fixture.bank"]))
        np.testing.assert_allclose(np.asarray(clipped["fixture.bank"])[0],
                                   np.array([3., 4.]) / (5. + 1e-6), rtol=1e-6)
        actual = _adamw_update(parent, huge, mask, self.hp, decay={"fixture.bank": True}, max_norm=1.)
        expected = _adamw_update(parent, reference, mask, self.hp, decay={"fixture.bank": True})
        for field in ("parameters", "m", "v", "update_counts"):
            np.testing.assert_array_equal(np.asarray(getattr(actual, field)["fixture.bank"]),
                                          np.asarray(getattr(expected, field)["fixture.bank"]))

    def test_one_clipped_step_has_one_parent_and_one_child_full_validation(self):
        parent = self.state()
        original_validate = AdamWStateTree.validate
        calls = []

        def counted_validate(state):
            calls.append(state)
            return original_validate(state)

        with patch.object(AdamWStateTree, "validate", counted_validate):
            actual = _adamw_update(
                parent,
                {"fixture.bank": mx.full((3, 2), .2, dtype=mx.float32)},
                {"fixture.bank": mx.array([True, False, False])},
                self.hp,
                decay={"fixture.bank": True},
                max_norm=1.,
            )
        self.assertIsNot(actual, parent)
        self.assertEqual(len(calls), 2)
        self.assertIs(calls[0], parent)
        self.assertIs(calls[1], actual)

    def test_rowwise_update_does_not_construct_optimizer_or_extract_numpy_indices(self):
        parent = self.state()
        gradient = mx.array([[.1, .3], [.2, -.5], [99999., -99999.]], dtype=mx.float32)
        mask = mx.array([True, True, False])
        with (patch.object(optim, "AdamW",
                    side_effect=AssertionError("per-leaf AdamW dispatch")),
              patch("bilqis_mlx.runtime.atlas_optimizer.np.asarray",
                    side_effect=AssertionError("host row-index extraction"))):
            actual = self.update(parent, mask, gradient)
        self.assertEqual(int(actual.update_counts["fixture.bank"][0]), 1)
        self.assertEqual(int(actual.update_counts["fixture.bank"][1]), 3)
        self.assertEqual(int(actual.update_counts["fixture.bank"][2]), 0)

    def test_authority_selected_rows_match_generic_mask_path_exactly(self):
        parent = self.state()
        gradient = mx.array([[.1, .3], [.2, -.5], [99999., -99999.]], dtype=mx.float32)
        mask = {"fixture.bank": mx.array([True, True, False])}
        expected = _adamw_update(
            parent, {"fixture.bank": gradient}, mask, self.hp,
            decay={"fixture.bank": True})
        actual = _adamw_update(
            parent, {"fixture.bank": gradient}, mask, self.hp,
            decay={"fixture.bank": True},
            participation_authority={"fixture.bank": (False, (0, 1))})
        for field in ("parameters", "m", "v", "update_counts"):
            np.testing.assert_array_equal(
                np.asarray(getattr(actual, field)["fixture.bank"]),
                np.asarray(getattr(expected, field)["fixture.bank"]))

    def test_realistic_214_leaf_step_has_constant_validation_boundaries(self):
        report = realistic_step_report()
        self.assertEqual(report.leaf_count, 214)
        self.assertEqual(report.full_state_validations, 2)
        self.assertEqual(report.numpy_mask_readbacks, 0)
        self.assertEqual(report.optimizer_instances, 0)
        self.assertEqual(report.explicit_eval_batches, 4)
        self.assertGreater(report.wall_seconds, 0.)

    def test_clipping_rejects_nonfinite_norm_and_invalid_limit(self):
        from bilqis_mlx.runtime.atlas_optimizer import _masked_clipped_gradients
        parent = self.state(False)
        gradient = {"fixture.bank": mx.full((3, 2), 3e38)}
        mask = {"fixture.bank": mx.array(True)}
        for limit in (0., -1., float("nan"), True):
            with self.assertRaises(BilqisError):
                _masked_clipped_gradients(parent, gradient, mask, max_norm=limit)
        with self.assertRaises(BilqisError):
            _masked_clipped_gradients(parent, gradient, mask, max_norm=1.)
        self.assertEqual(int(parent.update_counts["fixture.bank"]), 0)

    def test_unbound_constructor_consumes_complete_b01_ledger(self):
        from bilqis_mlx.runtime.atlas_optimizer import _create_unbound_bamf_optimizer
        from bilqis_mlx.runtime.model_topology_v2 import (
            ModelTopologySpecV2, GenerationExtents, expected_bamf_shapes,
        )
        spec = ModelTopologySpecV2()
        extents = GenerationExtents(1, 1, "a" * 64, "b" * 64, "c" * 64)
        state, decay, manifest = _create_unbound_bamf_optimizer(spec, extents, run_seed=474)
        ledger = expected_bamf_shapes(spec, extents)
        self.assertEqual(set(state.parameters), {item.name for item in ledger})
        self.assertEqual(dict(decay), {item.name: item.decay for item in ledger})
        self.assertEqual(manifest["initialization_status"], "UNBOUND")
        self.assertEqual(manifest["topology_digest"], spec.digest)
        self.assertEqual(manifest["generation_extents_digest"], extents.digest)
        for item in ledger:
            self.assertEqual(state.parameters[item.name].shape, item.shape)
            for field in ("m", "v", "update_counts"):
                self.assertTrue(bool(mx.all(getattr(state, field)[item.name] == 0)))
            self.assertEqual(state.update_counts[item.name].dtype, mx.uint64)
        for name, count_shape in (("identity.bank.0", (8192,)), ("motif.page.0", (16384,)),
                                  ("features.type", (512,)), ("features.role", (512,)),
                                  ("features.schema", (512,)), ("features.local_slot", (16,)),
                                  ("blocks.0.query", ()), ("frame.empty_seed", ())):
            self.assertEqual(state.update_counts[name].shape, count_shape)
        self.assertEqual(float(state.parameters["frame.pool_gate"][0]), -2.)
        self.assertTrue(bool(mx.all(state.parameters["plastic.group.0.B"] == 0)))
        self.assertFalse(decay["features.norm"])
        self.assertTrue(decay["blocks.0.query"])


if __name__ == "__main__":
    unittest.main()
