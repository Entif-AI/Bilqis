"""CT-053 governed immutable receipt ingestion and rebuild proof."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.akasha_outbox import AkashaEventKind
from bilqis_mlx.runtime.bamf_projection import read_projection_outbox
from bilqis_mlx.runtime.governed_ingestion import (
    materialization_event_from_receipt,
    rebuild_immutable_events,
)
from bilqis_mlx.runtime.tests.projection.test_akasha_outbox import _event
from bilqis_mlx.runtime.tests.projection.test_bamf_projection import _contract


def _materialization_receipt() -> bytes:
    receipt = {
        "schema": "bilqis.skos.materialization/v1",
        "version": "1.0.0",
        "status": "complete",
        "timestamp": "1970-01-01T00:09:40+00:00",
        "graph": "bilqis-fixture",
        "owner": "fixture-owner",
        "canonical_rdf_sha256": "1" * 64,
        "projection_version": "1.0.0",
        "semantic_coverage": {"ref": "coverage.json", "sha256": "2" * 64},
        "coverage_status": "complete",
        "importer": {
            "version": "2.0.0",
            "implementation_sha256": "3" * 64,
            "git_commit": "4" * 40,
            "dirty_source": False,
        },
        "nodes_by_label": {"RdfTerm": 2},
        "edges_by_type": {"RDF": 1},
        "indexes": [{"label": "RdfTerm", "property": "iri", "present": True}],
        "smoke_suite": {
            "schema": "bilqis.skos.smoke-report/v1",
            "suite_version": "1.0.0",
            "suite_sha256": "5" * 64,
            "canonical_sha256": "1" * 64,
            "passed": True,
            "cases": [{"id": "lookup", "passed": True, "expected": [], "actual": []}],
        },
    }
    return json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()


class GovernedIngestionTests(unittest.TestCase):
    def test_materialization_receipt_projects_exact_source_and_semantic_identity(self):
        raw = _materialization_receipt()
        event = materialization_event_from_receipt(raw)
        payload = json.loads(event.payload_json)
        self.assertIs(event.kind, AkashaEventKind.MATERIALIZATION)
        self.assertEqual(event.source_receipt_sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(payload["canonical_rdf_sha256"], "1" * 64)
        self.assertEqual(
            payload["materialization_receipt_sha256"], event.source_receipt_sha256)
        self.assertEqual(payload["semantic_coverage_sha256"], "2" * 64)
        self.assertEqual(payload["smoke_suite_sha256"], "5" * 64)

    def test_unknown_or_incomplete_materialization_receipt_fails_closed(self):
        raw = json.loads(_materialization_receipt())
        for changed in (
            {**raw, "schema": "unknown/v1"},
            {**raw, "status": "incomplete", "reason": "fixture"},
        ):
            with self.subTest(changed=changed["status"]), self.assertRaises(BilqisError):
                materialization_event_from_receipt(
                    json.dumps(changed, sort_keys=True, separators=(",", ":")).encode())

    def test_four_required_receipt_families_rebuild_identically_and_retry_converges(self):
        events = (
            materialization_event_from_receipt(_materialization_receipt()),
            _event(AkashaEventKind.FACTORY_RELEASE),
            _event(AkashaEventKind.CHECKPOINT_PUBLICATION),
            _event(AkashaEventKind.CAPABILITY_OUTCOME),
        )
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first_domain = _contract(root / "first.sqlite3")
            second_domain = replace(first_domain, outbox_path=root / "second.sqlite3")
            first = rebuild_immutable_events(events, first_domain)
            retry = rebuild_immutable_events(events, first_domain)
            second = rebuild_immutable_events(events, second_domain)
            self.assertEqual(first.appended_count, 4)
            self.assertEqual(retry.appended_count, 0)
            self.assertEqual(retry.duplicate_count, 4)
            self.assertEqual(second.appended_count, 4)
            self.assertEqual(
                read_projection_outbox(first_domain.outbox_path),
                read_projection_outbox(second_domain.outbox_path),
            )


if __name__ == "__main__":
    unittest.main()
