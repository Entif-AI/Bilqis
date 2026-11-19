"""B11 compatibility for immutable historical Grade-A source-row identity."""
from pathlib import Path
from unittest import TestCase

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.source_atoms.inputs import SourceAtomRow
import bilqis_mlx.runtime.b11_source_execution_authority as b11
from bilqis_mlx.source_adapters.school import live_source_registry


class B11GradeAOwnerCompatibilityTests(TestCase):
    def setUp(self):
        self.registry = live_source_registry()
        self.owner = self.registry.require(
            "bilqis_mlx.grade_a_probe.make_record",
            "bilqis.mlx.grade-a-record-oracle/v2",
        )

    @staticmethod
    def _source(oracle: str) -> SourceAtomRow:
        return SourceAtomRow(
            None,
            {
                "generator": "bilqis.mlx.grade-a-live-constructor/v1",
                "oracle": oracle,
                "capability": "A.EDGE",
            },
            {},
            Path("."),
            0,
            1,
        )

    def test_historical_grade_a_oracle_resolves_exact_current_owner(self):
        resolved = b11._require_row_owner(
            self.owner,
            self.registry,
            self._source("original+independent+grade_a_oracle"),
            drift=False,
        )
        self.assertIs(resolved, self.owner)

    def test_unregistered_grade_a_oracle_remains_unavailable(self):
        with self.assertRaises(BilqisError) as caught:
            b11._require_row_owner(
                self.owner,
                self.registry,
                self._source("forged.oracle"),
                drift=False,
            )
        self.assertEqual(
            caught.exception.context["reason"],
            "B11_SOURCE_EXECUTION_OWNER_UNAVAILABLE",
        )


if __name__ == "__main__":
    import unittest
    unittest.main()
