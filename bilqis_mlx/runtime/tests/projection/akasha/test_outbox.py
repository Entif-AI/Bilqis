"""C10.1 durable, append-only, idempotent Akasha event/outbox witnesses."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
from types import MappingProxyType
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.akasha_outbox import (
    AkashaEvent, AkashaEventKind, append_c09_intent, append_outbox, pending_events,
    project_event, read_outbox, record_delivery_attempt,
)
from bilqis_mlx.runtime.atlas_revalidation import (
    CorrectionEvent, SourceAuthorityKey, SourceAuthorityRegistry,
    SourceAuthorityScope,
)
from bilqis_mlx.runtime.atlas_requalification import (
    C10InvalidationIntent, CapabilitySupport, RequalificationLedger,
    RequalificationStatus,
)
from bilqis_mlx.semantics.cognitive_dependencies import (
    DependencyKind, DependencyRef,
)


PAYLOADS = MappingProxyType({
    AkashaEventKind.MATERIALIZATION: {
        "graph": "fixture-graph", "owner": "fixture-owner",
        "canonical_rdf_sha256": "1" * 64,
        "materialization_receipt_sha256": "2" * 64,
        "projection_version": "1.0.0", "coverage_status": "complete",
        "semantic_coverage_sha256": "3" * 64,
        "importer_implementation_sha256": "4" * 64,
        "smoke_suite_sha256": "5" * 64,
    },
    **{kind: {"owner_source_event_id": "fixture:event", "producer_id": "fixture:producer",
              "artifact_schema": "fixture:opaque/v1", "artifact_sha256": "a" * 64, "verification_mode": "DISPOSABLE_CONTRACT"}
       for kind in (AkashaEventKind.BANK_ALLOCATION, AkashaEventKind.PLASTICITY_EPOCH, AkashaEventKind.PACKAGE_EXPORT)},
    **{kind: {"native_event_id": "b" * 64, "native_event_digest": "a" * 64,
              "run_id": "fixture:run", "generation": 1, "native_event_type": {AkashaEventKind.TEACHER_VISIT: "SCHOOL_TEACHER_VISIT_COMMITTED",
                  AkashaEventKind.FACTORY_RELEASE: "SCHOOL_FACTORY_RELEASE_MIGRATED",
                  AkashaEventKind.CAPABILITY_OUTCOME: "SCHOOL_CAPABILITY_BEST_COMMITTED"}[kind]}
       for kind in (AkashaEventKind.TEACHER_VISIT, AkashaEventKind.FACTORY_RELEASE, AkashaEventKind.CAPABILITY_OUTCOME)},
    AkashaEventKind.SOURCE_CORRECTION: {
        "correction_event_id": "correction:1",
        "source_owner": "source:owner",
        "dependency_key": "source:row",
        "old_digest": "a" * 64, "new_digest": "b" * 64,
    },
    AkashaEventKind.REVALIDATION: {
        "artifact_id": "frame:1",
        "old_digest": "a" * 64, "new_digest": "b" * 64,
        "eligible": True,
    },
    AkashaEventKind.REQUALIFICATION: {
        "capability_id": "capability:1",
        "retained_generation_sha256": "c" * 64,
        "status": "REQUALIFICATION_REQUIRED",
    },
    AkashaEventKind.CAPABILITY_GRADUATION: {
        "capability_id": "capability:1",
        "generation_sha256": "c" * 64,
        "assessment_receipt_sha256": "d" * 64,
    },
    AkashaEventKind.MOTIF_CANDIDATE: {
        "motif_id": "motif:1",
        "source_refs": ["source:row"],
        "eligibility_digest": "e" * 64,
    },
    AkashaEventKind.PROCESS_FAULT: {
        "fault_id": "fault:1",
        "original_source_event_id": "event:1",
        "correction_event_id": "correction:1",
        "remediation_id": "remediation:1",
        "derived_path": ["feature:1", "motif:1"],
    },
    AkashaEventKind.CHECKPOINT_PUBLICATION: {
        "checkpoint_digest": "f" * 64,
        "generation_sha256": "c" * 64,
        "manifest_digest": "1" * 64,
    },
})


def _event(kind=AkashaEventKind.SOURCE_CORRECTION):
    return AkashaEvent.from_payload(
        kind=kind, subject_id="subject:fixture",
        source_receipt_sha256="9" * 64,
        payload=PAYLOADS[kind],
        source_time=570, effective_time=575,
        observed_at=580, recorded_at=585,
    )


class AkashaOutboxTests(unittest.TestCase):
    def test_all_projection_kinds_are_typed_and_source_bound(self):
        for kind in AkashaEventKind:
            with self.subTest(kind=kind):
                event = _event(kind)
                projection = project_event(event)
                self.assertEqual(projection.kind, kind)
                self.assertEqual(projection.event_id, event.event_id)
                self.assertEqual(projection.payload_digest,
                                 event.payload_digest)
                self.assertEqual(projection.source_receipt_sha256, "9" * 64)
                self.assertEqual(projection.visibility, "INTERNAL_ONLY")
                self.assertEqual(event, _event(kind))
                with self.assertRaises(BilqisError):
                    AkashaEvent.from_payload(
                        kind=kind, subject_id="subject:fixture",
                        source_receipt_sha256="9" * 64,
                        payload={}, source_time=570, effective_time=575,
                        observed_at=580, recorded_at=585)

    def test_repeated_enqueue_and_delivery_retries_never_duplicate_event(self):
        event = _event()
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "outbox.sqlite3"
            self.assertTrue(append_outbox(db, event))
            self.assertFalse(append_outbox(db, event))
            self.assertEqual(read_outbox(db), (event,))
            self.assertEqual(pending_events(db), (event,))
            self.assertTrue(record_delivery_attempt(
                db, event.event_id, "attempt:1", "FAILED", "a" * 64, 590))
            self.assertFalse(record_delivery_attempt(
                db, event.event_id, "attempt:1", "FAILED", "a" * 64, 590))
            self.assertEqual(pending_events(db), (event,))
            self.assertTrue(record_delivery_attempt(
                db, event.event_id, "attempt:2", "DELIVERED", "b" * 64, 595))
            self.assertEqual(pending_events(db), ())
            self.assertEqual(read_outbox(db), (event,))
            with sqlite3.connect(db) as connection:
                self.assertEqual(connection.execute(
                    "SELECT COUNT(*) FROM akasha_events").fetchone()[0], 1)
                self.assertEqual(connection.execute(
                    "SELECT COUNT(*) FROM akasha_delivery_attempts"
                ).fetchone()[0], 2)

    def test_conflicting_duplicate_id_or_delivery_attempt_fails_closed(self):
        event = _event()
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "outbox.sqlite3"
            append_outbox(db, event)
            with self.assertRaises(BilqisError) as caught:
                replace(event, payload_digest="0" * 64)
            self.assertEqual(caught.exception.context["reason"],
                             "BAMF_C10_EVENT_CONSTRUCTION_FORBIDDEN")
            with sqlite3.connect(db) as connection:
                with self.assertRaisesRegex(
                        sqlite3.IntegrityError, "AKASHA_APPEND_ONLY"):
                    connection.execute(
                        "UPDATE akasha_events SET payload_digest = ?",
                        ("0" * 64,))
                connection.execute("DROP TRIGGER akasha_events_no_update")
                connection.execute(
                    "UPDATE akasha_events SET payload_digest = ?",
                    ("0" * 64,))
            with self.assertRaises(BilqisError) as caught:
                append_outbox(db, event)
            self.assertEqual(caught.exception.context["reason"],
                             "BAMF_C10_EVENT_ID_CONFLICT")
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "outbox.sqlite3"
            append_outbox(db, event)
            record_delivery_attempt(
                db, event.event_id, "attempt:1", "FAILED", "a" * 64, 590)
            with self.assertRaises(BilqisError) as caught:
                record_delivery_attempt(
                    db, event.event_id, "attempt:1", "DELIVERED",
                    "b" * 64, 591)
            self.assertEqual(caught.exception.context["reason"],
                             "BAMF_C10_DELIVERY_ATTEMPT_CONFLICT")

    def test_restart_replays_only_undelivered_events_and_preserves_receipts(self):
        event_a = _event(AkashaEventKind.SOURCE_CORRECTION)
        event_b = _event(AkashaEventKind.PROCESS_FAULT)
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "outbox.sqlite3"
            append_outbox(db, event_a)
            append_outbox(db, event_b)
            record_delivery_attempt(
                db, event_a.event_id, "attempt:a", "DELIVERED", "a" * 64, 600)
            self.assertEqual(pending_events(db), (event_b,))
            self.assertEqual(read_outbox(db), (event_a, event_b))
            self.assertEqual(event_a.source_receipt_sha256, "9" * 64)


if __name__ == "__main__":
    unittest.main()
