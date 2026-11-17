"""Historical C09 verification path for frozen-grade correction authority."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.runtime.active_generated_grade_correction import (
    _historical_accepted_corrections,
)


class HistoricalCorrectionReplayTests(unittest.TestCase):
    def test_replay_uses_historical_bundle_registry_and_ledger(self):
        manifest = "a" * 64
        student = SimpleNamespace(correction_frontier={"epoch": 7})
        registry = object()
        records = (object(),)
        accepted = (("b" * 64, object()),)

        with TemporaryDirectory() as directory, patch(
            "bilqis_mlx.runtime.bamf_bundle.codec.load_bamf_bundle",
            return_value=student,
        ) as load, patch(
            "bilqis_mlx.runtime.bamf_bundle.source_authority_custody."
            "resolve_source_authority_registry",
            return_value=registry,
        ) as resolve, patch(
            "bilqis_mlx.runtime.accepted_correction_ledger."
            "read_records",
            return_value=records,
        ) as read_records, patch(
            "bilqis_mlx.runtime.accepted_correction_ledger."
            "_accepted_corrections_from_records",
            return_value=accepted,
        ) as verify:
            root = Path(directory)
            result = _historical_accepted_corrections(root, manifest)

        self.assertEqual(result, accepted)
        load.assert_called_once_with(
            root / "bamf-bundles" / manifest,
            expected_manifest_sha256=manifest,
        )
        resolve.assert_called_once_with(root, student.correction_frontier)
        read_records.assert_called_once_with(root, manifest)
        verify.assert_called_once_with(records, registry)


if __name__ == "__main__":
    unittest.main()
