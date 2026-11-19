"""C10.3 verifies source records again at promotion boundaries."""
from pathlib import Path
import tempfile
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.akasha_staging import (
    build_staging_projection, promote_staging_projection,
    read_active_projection, verify_staging_projection,
)
from bilqis_mlx.runtime.tests.projection.staging_helpers import _event, _contract, _projected


class StagingRevalidationTests(unittest.TestCase):
    def test_promotion_rejects_mutated_public_event_and_keeps_prior_pointer(self):
        for field, value in (('kind', 'REQUALIFICATION'), ('kind', []),
                             ('event_id', []), ('recorded_at', -1),
                             ('subject_digest', '/private/source'),
                             ('payload_digest', 'not-a-digest')):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as folder:
                domain = _contract(Path(folder) / 'outbox.sqlite3')
                first = verify_staging_projection(build_staging_projection(
                    (_projected(_event('capability:prior'), domain),), domain))
                database = Path(folder) / 'staging.sqlite3'
                promote_staging_projection(database, first, expected_active_digest=None)
                candidate = build_staging_projection(
                    (_projected(_event('capability:next'), domain),), domain)
                object.__setattr__(candidate.public_events[0], field, value)
                with self.assertRaises(BilqisError):
                    verified = verify_staging_projection(candidate)
                    promote_staging_projection(database, verified,
                                               expected_active_digest=first.stage.stage_digest)
                self.assertEqual(read_active_projection(database), first.stage)

    def test_verification_rejects_mutated_census_and_identity(self):
        domain = _contract(Path('/tmp/nonexistent-c521-query-outbox'))
        for field, value in (('census', (('REQUALIFICATION', 42),)),
                             ('domain_digest', '0' * 64),
                             ('stage_digest', '0' * 64)):
            with self.subTest(field=field):
                stage = build_staging_projection(
                    (_projected(_event('capability:tampered'), domain),), domain)
                object.__setattr__(stage, field, value)
                with self.assertRaises(BilqisError):
                    verify_staging_projection(stage)

    def test_public_query_rejects_mutated_private_text_before_returning_records(self):
        from bilqis_mlx.runtime.akasha_staging import query_public_projection
        domain = _contract(Path('/tmp/nonexistent-c521-private-query-outbox'))
        stage = build_staging_projection(
            (_projected(_event('capability:private-query'), domain),), domain)
        object.__setattr__(stage.public_events[0], 'subject_digest', '/private/source.txt')
        with self.assertRaises(BilqisError):
            query_public_projection(stage, limit=1)
