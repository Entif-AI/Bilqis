"""Authenticated BAMF semantic contexts remain owner-issued only."""
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import (
    AuthenticatedCandidateFeatureContext,
    AuthenticatedGenerationFeatureContext,
)


class FeatureContextIssuanceTests(unittest.TestCase):
    def test_candidate_context_rejects_caller_construction(self):
        with self.assertRaises(BilqisError):
            AuthenticatedCandidateFeatureContext()

    def test_generation_context_rejects_caller_construction(self):
        with self.assertRaises(BilqisError):
            AuthenticatedGenerationFeatureContext()


if __name__ == "__main__":
    unittest.main()
