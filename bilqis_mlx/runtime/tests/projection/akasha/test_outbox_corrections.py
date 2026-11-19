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


class AkashaOutboxCorrectionTests(unittest.TestCase):
    def test_signed_c09_requalification_intent_enqueues_once_into_c10(self):
        private = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("11" * 32))
        public = private.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw).hex()
        authority = SourceAuthorityRegistry((
            SourceAuthorityKey(
                "source:owner", public,
                (SourceAuthorityScope(DependencyKind.SOURCE, "source:"),)),
        ))
        correction = CorrectionEvent(
            event_id="correction:fixture",
            dependency=DependencyRef(DependencyKind.SOURCE, "source:row"),
            source_owner="source:owner",
            source_receipt_sha256="9" * 64,
            old_evidence_sha256="a" * 64,
            new_evidence_sha256="b" * 64,
            source_time=570, effective_time=575,
            observed_at=580, recorded_at=585,
            reason_code="SOURCE_CORRECTION",
            source_signature_hex="0" * 128,
        )
        correction = replace(
            correction, source_signature_hex=private.sign(
                correction.signing_bytes()).hex())
        intent = C10InvalidationIntent.from_correction(
            correction, ("motif:1",), ("capability:1",))
        ledger = RequalificationLedger((
            CapabilitySupport(
                capability_id="capability:1",
                support_artifact_ids=("capability:1",),
                source_anchor_ids=("source:row",),
                retained_generation_sha256="c" * 64,
                observation_ids=("observation:1",),
                status=RequalificationStatus.REQUALIFICATION_REQUIRED,
            ),
        ))
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "outbox.sqlite3"
            self.assertEqual(append_c09_intent(
                db, intent, correction, ledger, authority), 1)
            self.assertEqual(append_c09_intent(
                db, intent, correction, ledger, authority), 0)
            pending = pending_events(db)
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0].kind,
                             AkashaEventKind.REQUALIFICATION)
            self.assertEqual(pending[0].source_receipt_sha256, "9" * 64)
            self.assertIn(intent.event_id, pending[0].payload_json)
            with self.assertRaises(BilqisError) as caught:
                append_c09_intent(
                    db, intent, replace(correction,
                                        new_evidence_sha256="0" * 64),
                    ledger, authority)
            self.assertEqual(caught.exception.context["reason"],
                             "BAMF_C09_SOURCE_SIGNATURE_INVALID")
            self.assertEqual(len(read_outbox(db)), 1)
