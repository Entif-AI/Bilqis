"""Pure BMF v0.3.8 objective identity and literal split witness."""
from __future__ import annotations

import math
import unittest

from bilqis_mlx.runtime.training_objective import (
    FAMILY_WEIGHTS, FP32_ATOL, FP32_RTOL, INACTIVE_FAMILIES,
    TRAINING_OBJECTIVE_ID, TRAINING_OBJECTIVE_SCHEMA,
    current_training_objective,
)


class TrainingObjectiveContractTests(unittest.TestCase):
    def test_current_contract_is_canonical_and_round_trips(self):
        contract = current_training_objective()
        self.assertEqual(contract.objective_id, TRAINING_OBJECTIVE_ID)
        self.assertEqual(contract.schema_version, TRAINING_OBJECTIVE_SCHEMA)
        self.assertEqual(contract.family_weights, FAMILY_WEIGHTS)
        self.assertEqual(INACTIVE_FAMILIES, ("FRAME_ATOMIC_CONSISTENCY",))
        self.assertEqual(len(contract.digest), 64)
        self.assertEqual(
            type(contract).from_record(contract.to_record()), contract)

    def test_literal_heterogeneous_split_witness(self):
        q4 = 1.05
        row_gradients = (-0.5, 0.05, -0.04, 0.05 * q4 / 3.0)
        row_losses = (
            math.log(2.0),
            0.10 * math.log(2.0),
            0.05 * math.log(5.0),
            0.05 * q4 * math.log(3.0),
        )
        unsplit_loss = sum(row_losses) / 4.0
        unsplit_gradient = sum(row_gradients) / 4.0
        split_3_1 = (
            (sum(row_gradients[:3]) / 3.0) * (3.0 / 4.0)
            + row_gradients[3] * (1.0 / 4.0))
        split_1_3 = (
            row_gradients[0] * (1.0 / 4.0)
            + (sum(row_gradients[1:]) / 3.0) * (3.0 / 4.0))
        self.assertTrue(math.isclose(
            unsplit_loss, 0.22515273484818016,
            rel_tol=FP32_RTOL, abs_tol=FP32_ATOL))
        self.assertTrue(math.isclose(
            unsplit_gradient, -0.118125,
            rel_tol=FP32_RTOL, abs_tol=FP32_ATOL))
        self.assertTrue(math.isclose(
            split_3_1, unsplit_gradient,
            rel_tol=FP32_RTOL, abs_tol=FP32_ATOL))
        self.assertTrue(math.isclose(
            split_1_3, unsplit_gradient,
            rel_tol=FP32_RTOL, abs_tol=FP32_ATOL))


if __name__ == "__main__":
    unittest.main()
