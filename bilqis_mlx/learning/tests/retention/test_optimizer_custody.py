"""Optimizer custody."""
import unittest
from unittest.mock import patch

from bilqis_mlx.learning.tests.test_learning_experiment import (
    CausalTeacherExperimentTests, commit_trial, fork_student, np,
)


class OptimizerCustodyTests(CausalTeacherExperimentTests):
    def _parent(self):
        import mlx.core as mx
        import mlx.optimizers as optim
        mx.set_default_device(mx.cpu)
        weights = {
            "embedding.weight":
                mx.array(np.arange(12).reshape(3, 4).astype(np.float32))
        }
        parent = optim.AdamW(learning_rate=.00013, bias_correction=True)
        parent.update(
            weights,
            {"embedding.weight": mx.zeros_like(weights["embedding.weight"])},
        )
        mx.eval(weights, parent.state)
        return mx, optim, weights, parent

    def test_candidate_creation_never_round_trips_through_numpy(self):
        _, _, weights, parent = self._parent()
        import mlx.core as mx
        with patch.object(np, "asarray",
                          side_effect=AssertionError("HOST_NUMPY_CLONE")):
            branch, branch_opt = fork_student(mx, weights, parent)
        mx.eval(branch, branch_opt.state)

    def test_direct_candidate_leaf_mutation_cannot_reach_parent(self):
        mx, _, weights, parent = self._parent()
        parent_weight = np.asarray(weights["embedding.weight"]).copy()
        parent_m = np.asarray(parent.state["embedding.weight"]["m"]).copy()
        parent_v = np.asarray(parent.state["embedding.weight"]["v"]).copy()
        parent_step = int(parent.state["step"].item())

        branch, branch_opt = fork_student(mx, weights, parent)
        branch["embedding.weight"][0, 0] = -999.
        branch_opt.state["embedding.weight"]["m"][0, 0] = -888.
        branch_opt.state["embedding.weight"]["v"][0, 0] = -777.
        branch_opt.state["step"][...] = parent_step + 50
        mx.eval(branch, branch_opt.state)

        np.testing.assert_array_equal(
            np.asarray(weights["embedding.weight"]), parent_weight)
        np.testing.assert_array_equal(
            np.asarray(parent.state["embedding.weight"]["m"]), parent_m)
        np.testing.assert_array_equal(
            np.asarray(parent.state["embedding.weight"]["v"]), parent_v)
        self.assertEqual(int(parent.state["step"].item()), parent_step)

    def test_parent_adamw_remains_unchanged_until_trial_committed(self):
        mx, _, weights, parent = self._parent()
        parent_weight = np.asarray(weights["embedding.weight"]).copy()
        parent_moment = np.asarray(parent.state["embedding.weight"]["m"]).copy()
        parent_variance = np.asarray(
            parent.state["embedding.weight"]["v"]).copy()
        parent_step = int(parent.state["step"].item())
        branch, branch_opt = fork_student(mx, weights, parent)
        branch_opt.update(branch, {"embedding.weight": mx.ones_like(branch["embedding.weight"])})
        mx.eval(branch,branch_opt.state)
        self.assertEqual(int(parent.state["step"].item()), parent_step)
        np.testing.assert_array_equal(np.asarray(weights["embedding.weight"]), parent_weight)
        np.testing.assert_array_equal(np.asarray(parent.state["embedding.weight"]["m"]), parent_moment)
        np.testing.assert_array_equal(
            np.asarray(parent.state["embedding.weight"]["v"]), parent_variance)
        self.assertNotEqual(int(branch_opt.state["step"].item()), parent_step)
        trained_weight = branch["embedding.weight"]
        trained_state = branch_opt.state
        commit_trial(weights, parent, branch, branch_opt)
        self.assertEqual(int(parent.state["step"].item()), parent_step+1)
        self.assertFalse(np.array_equal(np.asarray(weights["embedding.weight"]), parent_weight))
        self.assertIs(weights["embedding.weight"], trained_weight)
        self.assertIs(parent.state, trained_state)

    def test_dense_and_sparse_adamw_updates_match_historical_clone(self):
        import mlx.core as mx

        def historical_clone(parameters, optimizer):
            import mlx.optimizers as optim

            def copy_value(value):
                if isinstance(value, mx.array):
                    return mx.array(np.asarray(value).copy())
                if isinstance(value, dict):
                    return {key: copy_value(item)
                            for key, item in value.items()}
                raise ValueError("UNKNOWN_STATE")

            copied = copy_value(parameters)
            copied_optimizer = optim.AdamW(
                learning_rate=float(optimizer.learning_rate),
                betas=list(optimizer.betas),
                eps=optimizer.eps,
                weight_decay=optimizer.weight_decay,
                bias_correction=optimizer.bias_correction,
            )
            copied_optimizer.state = copy_value(optimizer.state)
            mx.eval(copied, copied_optimizer.state)
            return copied, copied_optimizer

        for name, gradient in (
                ("dense", np.ones((3, 4), dtype=np.float32)),
                ("sparse_rows", np.array([
                    [1., 1., 1., 1.],
                    [0., 0., 0., 0.],
                    [2., 2., 2., 2.],
                ], dtype=np.float32))):
            with self.subTest(name=name):
                mx, _, weights, parent = self._parent()
                current, current_opt = fork_student(mx, weights, parent)
                historical, historical_opt = historical_clone(weights, parent)
                grad = {"embedding.weight": mx.array(gradient)}
                current_opt.update(current, grad)
                historical_opt.update(historical, grad)
                mx.eval(current, current_opt.state,
                        historical, historical_opt.state)

                np.testing.assert_array_equal(
                    np.asarray(current["embedding.weight"]),
                    np.asarray(historical["embedding.weight"]))
                for leaf in ("m", "v"):
                    np.testing.assert_array_equal(
                        np.asarray(
                            current_opt.state["embedding.weight"][leaf]),
                        np.asarray(
                            historical_opt.state["embedding.weight"][leaf]))
                self.assertEqual(
                    int(current_opt.state["step"].item()),
                    int(historical_opt.state["step"].item()))
