"""B12 optimizer-step validation multiplicity and corruption boundaries."""
from unittest import TestCase
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_candidate import begin_candidate
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
from bilqis_mlx.learning._retention.tests.test_atlas_candidate import (
    CandidateTransactionTests,
)


class OptimizerStepValidationTests(TestCase):
    def setUp(self):
        self.fixture = CandidateTransactionTests(methodName="runTest")
        self.fixture.setUp()

    def test_one_step_performs_only_parent_and_result_numerical_validation(self):
        candidate = begin_candidate(self.fixture.parent)
        original_validate = AdamWStateTree.validate
        calls = []

        def counted_validate(state):
            calls.append(state)
            return original_validate(state)

        with patch.object(AdamWStateTree, "validate", counted_validate):
            stepped = self.fixture.step(candidate)
        self.assertEqual(len(calls), 2)
        self.assertIs(calls[0], candidate.optimizer)
        self.assertIs(calls[1], stepped.optimizer)

    def test_mutated_issued_parent_is_rejected_at_step_boundary(self):
        candidate = begin_candidate(self.fixture.parent)
        candidate.optimizer.parameters[self.fixture.name][0, 0] = float("nan")
        with self.assertRaises(BilqisError):
            self.fixture.step(candidate)


if __name__ == "__main__":
    import unittest
    unittest.main()
