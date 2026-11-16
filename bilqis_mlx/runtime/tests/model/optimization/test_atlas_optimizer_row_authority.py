"""Fail-closed B09 row-selection authority at the B12 optimizer boundary."""
import unittest

import mlx.core as mx
import numpy as np

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.atlas_optimizer import (
    AdamWHyperparameters, AdamWStateTree, _adamw_update,
)


class AdamWRowAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.hp = AdamWHyperparameters(.00013, (.9, .95), 1e-8, .01)
        self.name = "fixture.bank"

    def state(self, rowwise=True):
        parameter = mx.array([[.5, -.25], [1., 2.], [3., 4.]], dtype=mx.float32)
        count = mx.array([0, 2, 0], dtype=mx.uint64) if rowwise else mx.array(0, dtype=mx.uint64)
        return AdamWStateTree(
            {self.name: parameter}, {self.name: mx.zeros_like(parameter)},
            {self.name: mx.zeros_like(parameter)}, {self.name: count})

    def update(self, parent, mask, authority):
        return _adamw_update(
            parent, {self.name: mx.full((3, 2), .2, dtype=mx.float32)},
            {self.name: mask}, self.hp, decay={self.name: True},
            participation_authority=authority)

    def test_row_selection_mismatch_fails_closed_without_mutation(self):
        parent = self.state()
        with self.assertRaises(BilqisError):
            self.update(parent, mx.array([True, False, False]),
                        {self.name: (False, (1,))})
        np.testing.assert_array_equal(np.asarray(parent.update_counts[self.name]), [0, 2, 0])

    def test_dense_selection_mismatch_fails_closed(self):
        with self.assertRaises(BilqisError):
            self.update(self.state(False), mx.array(True), {self.name: (False, ())})

    def test_malformed_row_selection_authority_fails_closed(self):
        parent = self.state()
        mask = mx.array([True, False, False])
        invalid = (
            {}, {self.name: (False, (0,)), "extra": (False, ())},
            {self.name: [False, (0,)]}, {self.name: (1, (0,))},
            {self.name: (False, [0])}, {self.name: (False, (0, 0))},
            {self.name: (False, ([0],))},
            {self.name: (False, (-1,))}, {self.name: (True, (0,))},
            {self.name: (False, (3,))},
        )
        for authority in invalid:
            with self.subTest(authority=authority), self.assertRaises(BilqisError):
                self.update(parent, mask, authority)

    def test_scalar_row_selection_is_rejected(self):
        with self.assertRaises(BilqisError):
            self.update(self.state(False), mx.array(True), {self.name: (False, (0,))})


if __name__ == "__main__":
    unittest.main()
