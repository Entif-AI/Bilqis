"""#1172 real-Factory C08 vectorized microbatch execution witnesses."""
from __future__ import annotations

import unittest

from bilqis_mlx.runtime.factory_candidate_microbatch import (
    execute_factory_logical_batch,
)
from bilqis_mlx.runtime.factory_candidate_training import _resource_plan

from .factory_training_bridge_support import FactoryTrainingBridgeFixture


class FactoryTrainingMicrobatchTests(FactoryTrainingBridgeFixture):
    def test_four_distinct_factory_rows_use_one_vectorized_gradient_launch(self):
        rows, prepared = self.prepare("A.IDENTITY", 37172, 4)
        resource_plan, _ = _resource_plan(prepared, self.candidate, None)
        gradient, authorities, targets = execute_factory_logical_batch(
            dict(self.candidate.retained_state.optimizer.parameters),
            prepared, self.context, self.feature_context.snapshot,
            self.generation, None, resource_plan)
        row_ids = tuple(row["id"] for row in rows)

        self.assertEqual(resource_plan.groups, ((0, 1, 2, 3),))
        self.assertEqual(gradient.gradient_launches, 1)
        self.assertEqual(gradient.vectorized_microbatches, 1)
        self.assertEqual(len(gradient.loss_executions), 4)
        self.assertEqual(len(targets), 4)
        self.assertEqual(
            tuple(item.source_row_id for item in authorities), row_ids)
        self.assertEqual(
            tuple(item.training_authority.source_row_id
                  for item in gradient.loss_executions),
            row_ids)


if __name__ == "__main__":
    unittest.main()
