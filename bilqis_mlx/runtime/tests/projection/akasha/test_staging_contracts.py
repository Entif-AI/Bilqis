"""C10.3 contracts behavior."""
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
    def test_staging_census_bounded_queries_and_private_payload_exclusion(self):
        with tempfile.TemporaryDirectory() as folder:
            contract = _contract(Path(folder) / "outbox.sqlite3")
            private = AkashaEvent.from_payload(
                kind=AkashaEventKind.REQUALIFICATION,
                subject_id="/private/users/alpha",
                source_receipt_sha256="9" * 64,
                payload={
                    "capability_id": "capability:private",
                    "retained_generation_sha256": "a" * 64,
                    "status": "REQUALIFICATION_REQUIRED",
                    "raw_private_input": "SECRET_SOURCE_TEXT",
                    "private_path": "/private/users/alpha/source.txt",
                },
                source_time=570, effective_time=575,
                observed_at=580, recorded_at=585,
            )
            events = (
                _projected(private, contract),
                _projected(_event("capability:public"), contract),
            )
            stage = build_staging_projection(events, contract)
            verified = verify_staging_projection(stage)
            self.assertEqual(len(stage.public_events), 2)
            self.assertEqual(stage.census, (("REQUALIFICATION", 2),))
            self.assertNotIn("SECRET_SOURCE_TEXT", stage.canonical_json)
            self.assertNotIn("/private/users/alpha", stage.canonical_json)
            self.assertNotIn("private_path", stage.canonical_json)
            self.assertEqual(len(query_public_projection(stage, limit=1)), 1)
            self.assertEqual(len(query_public_projection(stage, limit=2)), 2)
            self.assertEqual(
                query_public_projection(stage, limit=2, as_of=580), ())
            with self.assertRaises(BilqisError):
                query_public_projection(stage, limit=101)
            self.assertEqual(verified.stage.stage_digest, stage.stage_digest)
            future_effective = AkashaEvent.from_payload(
                kind=AkashaEventKind.REQUALIFICATION,
                subject_id="capability:future",
                source_receipt_sha256="9" * 64,
                payload={
                    "capability_id": "capability:future",
                    "retained_generation_sha256": "a" * 64,
                    "status": "REQUALIFICATION_REQUIRED",
                },
                source_time=570, effective_time=620,
                observed_at=580, recorded_at=585,
            )
            future_stage = build_staging_projection(
                (_projected(future_effective, contract),), contract)
            self.assertEqual(
                query_public_projection(future_stage, limit=1, as_of=600), ())
            self.assertEqual(len(query_public_projection(
                future_stage, limit=1, as_of=630)), 1)



class StagingCompatibilityTests(unittest.TestCase):
    def test_pre_extraction_canonical_bytes_and_digest_are_unchanged(self):
        domain = _contract(Path('/tmp/nonexistent-c521-fixture-outbox'))
        stage = build_staging_projection(
            (_projected(_event('capability:compatibility'), domain),), domain)
        expected = (Path(__file__).parent / 'fixtures' / 'staging-v1.json').read_text()
        self.assertEqual(stage.canonical_json, expected)
        self.assertEqual(stage.stage_digest,
                         'f2e8dd9fd48787ceb1d360798f77011bf84be2ff574ff9fa127d8c693901cd90')

    def test_public_record_classes_keep_canonical_module_identity(self):
        from bilqis_mlx.runtime import akasha_staging as api
        import importlib
        for name in ('PublicEvent', 'StagingProjection', 'VerifiedStage', 'PromotionReceipt'):
            record = getattr(api, name)
            with self.subTest(name=name):
                self.assertEqual(record.__module__, 'bilqis_mlx.runtime.akasha_staging')
                self.assertIs(getattr(importlib.import_module(record.__module__), name), record)
