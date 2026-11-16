"""B13 refuses accepted successors whose C05 baseline custody drifted."""
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle.publication import authority
from bilqis_mlx.runtime.baseline.lifecycle import BaselineLedger
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    accepted_state, candidate, parent_state,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
    acceptance,
)


class BaselinePublicationTests(unittest.TestCase):
    def test_acceptance_requires_exact_expected_baseline_ledger(self):
        parent = parent_state()
        successor = candidate(accepted_state(parent), 1, "a" * 64)
        binding = acceptance(successor, parent=parent)
        empty_digest = BaselineLedger.empty().digest

        with patch.object(
                authority, "_issued_acceptance_baseline_ledger_sha256",
                return_value=empty_digest):
            self.assertIs(authority.require_acceptance(successor, binding), binding)

        with patch.object(
                authority, "_issued_acceptance_baseline_ledger_sha256",
                return_value="0" * 64), self.assertRaises(BilqisError) as caught:
            authority.require_acceptance(successor, binding)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C05_BASELINE_PUBLICATION_DRIFT")


if __name__ == "__main__":
    unittest.main()
