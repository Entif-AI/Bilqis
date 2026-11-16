"""Regression tests for the BAMF invariant-transfer integrity gate."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.check_bamf_invariant_transfer import MANIFEST, validate


class BamfInvariantTransferTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(Path(MANIFEST).read_text(encoding="utf-8"))

    def test_checked_in_manifest_is_closed_and_valid(self):
        self.assertEqual(validate(self.manifest), [])

    def test_missing_successor_test_breaks_transfer(self):
        changed = copy.deepcopy(self.manifest)
        changed["invariants"][0]["successor_evidence"][0]["test"] = "test_removed"
        self.assertTrue(any(
            problem.startswith("SUCCESSOR_TEST_MISSING")
            for problem in validate(changed)
        ))

    def test_deleted_successor_proof_breaks_transfer(self):
        changed = copy.deepcopy(self.manifest)
        changed["invariants"][0]["successor_evidence"][0]["path"] = "missing.py"
        self.assertTrue(any(
            problem.startswith("SUCCESSOR_PROOF_MISSING")
            for problem in validate(changed)
        ))

    def test_self_consistency_cannot_close_transferred_invariant(self):
        changed = copy.deepcopy(self.manifest)
        for proof in changed["invariants"][0]["successor_evidence"]:
            proof["kind"] = "self_consistency"
        self.assertIn(
            "INDEPENDENT_AUTHORITY_REQUIRED source.spawned-direct-live-equality",
            validate(changed),
        )

    def test_missing_status_fails_closed(self):
        changed = copy.deepcopy(self.manifest)
        changed["invariants"][0]["status"] = "MISSING"
        self.assertIn(
            "INVARIANT_MISSING source.spawned-direct-live-equality",
            validate(changed),
        )

    def test_superseded_requires_explicit_current_authority(self):
        changed = copy.deepcopy(self.manifest)
        changed["invariants"][0]["status"] = "SUPERSEDED"
        self.assertIn(
            "SUPERSEDING_AUTHORITY_REQUIRED source.spawned-direct-live-equality",
            validate(changed),
        )


if __name__ == "__main__":
    unittest.main()
