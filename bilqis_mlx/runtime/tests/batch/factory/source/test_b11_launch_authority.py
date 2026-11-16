"""#1272 one-check-per-launch B11 source authority regressions."""
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
import bilqis_mlx.learning.frame_encoder.compiled as frame_encoder_compiled_impl
from bilqis_mlx.runtime.b11_source_execution_authority import (
    b11_source_authority_launch_epoch,
    b11_source_authority_launch_trusted,
)
import bilqis_mlx.runtime.b11_source_execution_authority as b11_authority_impl

from ..factory_training_bridge_support import FactoryTrainingBridgeFixture


class B11LaunchAuthorityTests(FactoryTrainingBridgeFixture):
    def test_launch_epoch_validates_source_once_and_trusts_inner_batch_checks(self):
        _rows, prepared = self.prepare("A.IDENTITY", 37124, 2)
        compiled = prepared.compiled_rows[0]
        authority = compiled.source_execution_authority
        row = compiled.compiled.compiled.rows[0]
        config = compiled.compiled.compiler_configs[0]
        source = compiled.sources[0]

        original_digest = b11_authority_impl._source_digest
        with patch.object(
                b11_authority_impl, "_source_digest", wraps=original_digest) as digest_call:
            with patch.object(
                    frame_encoder_compiled_impl, "project_context",
                    wraps=frame_encoder_compiled_impl.project_context) as project_call:
                with b11_source_authority_launch_epoch((compiled,)):
                    self.assertTrue(b11_source_authority_launch_trusted(
                        authority, row, config, source))
                    compiled.__post_init__()
                    compiled.compiled.__post_init__()
                self.assertFalse(b11_source_authority_launch_trusted(
                    authority, row, config, source))
                self.assertEqual(digest_call.call_count, 1)
                project_call.assert_not_called()

    def test_launch_epoch_rejects_in_place_row_drift_before_trust(self):
        _rows, prepared = self.prepare("A.IDENTITY", 37127, 2)
        compiled = prepared.compiled_rows[0]
        source_row = compiled.sources[0].source_row
        marker = object()
        previous = source_row.get("_launch_drift_test", marker)
        source_row["_launch_drift_test"] = True
        try:
            with self.assertRaises(BilqisError):
                with b11_source_authority_launch_epoch((compiled,)):
                    self.fail("drifted source row entered launch trust")
        finally:
            if previous is marker:
                source_row.pop("_launch_drift_test", None)
            else:
                source_row["_launch_drift_test"] = previous
