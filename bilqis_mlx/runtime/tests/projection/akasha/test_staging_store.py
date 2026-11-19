"""C10.3 store behavior."""
from pathlib import Path
import tempfile
import unittest
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.akasha_outbox import AkashaEvent, AkashaEventKind
from bilqis_mlx.runtime.akasha_staging import (
    build_staging_projection, promote_staging_projection,
    query_public_projection, read_active_projection,
    read_staging_projection, verify_staging_projection,
)
from bilqis_mlx.runtime.tests.projection.staging_helpers import _event, _contract, _projected


class StagingTests(unittest.TestCase):
    def test_atomic_staging_promotion_preserves_old_generation_and_pointer(self):
        with tempfile.TemporaryDirectory() as folder:
            contract = _contract(Path(folder) / "outbox.sqlite3")
            stage_db = Path(folder) / "staging.sqlite3"
            first = verify_staging_projection(build_staging_projection(
                (_projected(_event("capability:1"), contract),), contract))
            receipt = promote_staging_projection(
                stage_db, first, expected_active_digest=None)
            self.assertEqual(receipt.active_digest, first.stage.stage_digest)
            self.assertEqual(read_active_projection(stage_db), first.stage)
            second = verify_staging_projection(build_staging_projection(
                tuple(_projected(
                    _event("capability:" + str(index)), contract)
                    for index in range(2)), contract))
            with self.assertRaises(BilqisError) as caught:
                promote_staging_projection(
                    stage_db, second, expected_active_digest=None)
            self.assertEqual(caught.exception.context["reason"],
                             "BAMF_C10_STAGING_POINTER_CONFLICT")
            self.assertEqual(read_active_projection(stage_db), first.stage)
            promoted = promote_staging_projection(
                stage_db, second,
                expected_active_digest=first.stage.stage_digest)
            self.assertEqual(promoted.previous_digest,
                             first.stage.stage_digest)
            self.assertEqual(read_active_projection(stage_db), second.stage)
            self.assertEqual(read_staging_projection(
                stage_db, first.stage.stage_digest), first.stage)
            self.assertEqual(read_staging_projection(
                stage_db, second.stage.stage_digest), second.stage)


class StoredStageIdentityTests(unittest.TestCase):
    def test_read_rejects_valid_stage_substituted_under_another_digest(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as folder:
            domain = _contract(Path(folder) / 'outbox.sqlite3')
            database = Path(folder) / 'staging.sqlite3'
            first = verify_staging_projection(build_staging_projection(
                (_projected(_event('capability:first'), domain),), domain))
            other = verify_staging_projection(build_staging_projection(
                (_projected(_event('capability:other'), domain),), domain))
            promote_staging_projection(database, first, expected_active_digest=None)
            # Simulate corruption outside the append-only writer, without
            # modifying either canonical stage or its independently valid digest.
            with sqlite3.connect(database) as connection:
                connection.execute('DROP TRIGGER akasha_stages_no_update')
                connection.execute('UPDATE akasha_stages SET canonical_json=?',
                                   (other.stage.canonical_json,))
            with self.assertRaises(BilqisError):
                read_staging_projection(database, first.stage.stage_digest)
            with self.assertRaises(BilqisError):
                read_active_projection(database)
