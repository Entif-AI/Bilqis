"""Independent historical prefix and external-policy behavior tests."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from bilqis_mlx.semantics.foundation.abi import (
    HISTORICAL_ABI, HISTORICAL_GRAPH_REGISTRY, HISTORICAL_PREFIX_SIZE,
    fingerprint_graph_prefix,
    fingerprint_sheet_prefix, fingerprint_sheet_source_fields,
    load_historical_graph,
    prefix_preserving_vocab_size, require_external_expected,
    require_historical_prefix,
)
from scripts.check_historical_abi import check_abi, detect_literal_prefix_count


ROOT = Path(__file__).resolve().parents[4]
SNAPSHOT = ROOT / "docs/provenance/CURRICULUM_REGISTRY_SNAPSHOT_20261015.json"


class HistoricalAbiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    def test_independent_prefix_fingerprint_from_real_snapshot(self):
        fingerprint = fingerprint_sheet_prefix(self.source)
        self.assertEqual(fingerprint, "f4b02ca311146df741eef1b05f1446640898b82f1a4fb12b2327059a0ad28eb2")
        require_historical_prefix(fingerprint)
        self.assertEqual(fingerprint_sheet_source_fields(self.source),
                         "25be81dbb10fb5acc1a638e9f3226c927eb7ff733e2c06ec6ba070af8ebd7a46")

    def test_original_whole_student_checkpoint_matches_independent_index_receipt(self):
        original = (ROOT / "vendor" / "legacy-v16" /
                    "runs/primitive-consolidation-v16-triplets" /
                    "student-116760-7e9af4651f28.pt")
        if not original.exists():
            self.skipTest("Full historical checkpoint not mounted")
        from bilqis_mlx.token_atlas import read_historic_graph
        graph = read_historic_graph(original)
        self.assertEqual(fingerprint_graph_prefix(graph),
                         HISTORICAL_ABI.index_contract_sha256)
        self.assertEqual(prefix_preserving_vocab_size(graph),
                         HISTORICAL_PREFIX_SIZE)

    def test_architecture_neutral_historical_graph_matches_checkpoint_contract(self):
        graph = load_historical_graph()
        self.assertEqual(len(graph["tokens"]), HISTORICAL_PREFIX_SIZE)
        self.assertEqual(fingerprint_graph_prefix(graph),
                         HISTORICAL_ABI.index_contract_sha256)
        self.assertEqual(prefix_preserving_vocab_size(graph),
                         HISTORICAL_PREFIX_SIZE)

    def test_architecture_neutral_graph_rejects_nonsemantic_registry_drift(self):
        evidence = json.loads(HISTORICAL_GRAPH_REGISTRY.read_text(encoding="utf-8"))
        evidence["graph"]["version"] = "tampered-version"
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "registry.json"
            source.write_text(json.dumps(evidence), encoding="utf-8")
            with self.assertRaisesRegex(
                    ValueError, "SCHOOL.STATE.HISTORICAL_ARTIFACT_INVALID"):
                load_historical_graph(source)

    def test_sheet_reordering_does_not_mutate_semantic_identity(self):
        source = deepcopy(self.source)
        source["tabs"]["Token Atlas"]["rows"][1:4] = list(reversed(
            source["tabs"]["Token Atlas"]["rows"][1:4]))
        self.assertEqual(fingerprint_sheet_prefix(source), HISTORICAL_ABI.index_contract_sha256)

    def test_meaning_index_and_token_mutations_falsify_invariant(self):
        changed = deepcopy(self.source)
        rows = changed["tabs"]["Token Atlas"]["rows"]
        rows[1][1], rows[2][1] = rows[2][1], rows[1][1]
        with self.assertRaisesRegex(ValueError, "SOURCE_FIELDS_MISMATCH"):
            require_historical_prefix(fingerprint_sheet_prefix(changed))
        changed = deepcopy(self.source)
        changed["tabs"]["Token Atlas"]["rows"][1][13] = "a" * 64
        with self.assertRaisesRegex(ValueError, "SOURCE_FIELDS_MISMATCH"):
            require_historical_prefix(fingerprint_sheet_prefix(changed))

    def test_source_meaning_and_signature_cannot_lie_behind_claimed_hash(self):
        for column, poison in ((3, "forged source meaning"),
                               (4, "Entity->Entity"),
                               (11, "999")):
            with self.subTest(column=column):
                changed = deepcopy(self.source)
                changed["tabs"]["Token Atlas"]["rows"][1][column] = poison
                with self.assertRaisesRegex(ValueError, "SOURCE_FIELDS_MISMATCH"):
                    fingerprint_sheet_prefix(changed)

    def test_graph_name_must_match_node_name(self):
        original = (ROOT / "vendor" / "legacy-v16" /
                    "runs/primitive-consolidation-v16-triplets" /
                    "student-116760-7e9af4651f28.pt")
        if not original.exists():
            self.skipTest("Full historical checkpoint not mounted")
        from bilqis_mlx.token_atlas import read_historic_graph
        graph = deepcopy(read_historic_graph(original))
        graph["tokens"][0] = "swapped-but-node-and-claim-left-intact"
        with self.assertRaisesRegex(ValueError, "SOURCE_NODE_DRIFT"):
            fingerprint_graph_prefix(graph)

    def test_missing_and_duplicate_index_fail_closed(self):
        changed = deepcopy(self.source)
        changed["tabs"]["Token Atlas"]["rows"].pop(1)
        with self.assertRaisesRegex(ValueError, "SNAPSHOT_INDEX_DRIFT"):
            fingerprint_sheet_prefix(changed)
        changed = deepcopy(self.source)
        changed["tabs"]["Token Atlas"]["rows"][1][0] = changed["tabs"]["Token Atlas"]["rows"][2][0]
        with self.assertRaisesRegex(ValueError, "SNAPSHOT_INDEX_DRIFT"):
            fingerprint_sheet_prefix(changed)

    def test_growth_outside_immutable_prefix_does_not_change_fingerprint(self):
        added = deepcopy(self.source)
        row = deepcopy(added["tabs"]["Token Atlas"]["rows"][-1])
        row[0] = str(HISTORICAL_PREFIX_SIZE)
        row[1] = "synthetic.extra"
        row[2] = "legacy:synthetic.extra"
        added["tabs"]["Token Atlas"]["rows"].append(row)
        self.assertEqual(fingerprint_sheet_prefix(added), HISTORICAL_ABI.index_contract_sha256)

    def test_external_guard_is_optional_only_in_advisory_mode(self):
        self.assertFalse(require_external_expected(None))
        with self.assertRaisesRegex(ValueError, "EXTERNAL_REFERENCE_MISSING"):
            require_external_expected(None, required=True)
        with self.assertRaisesRegex(ValueError, "EXTERNAL_REFERENCE_MISMATCH"):
            require_external_expected("a" * 64, required=True)
        self.assertTrue(require_external_expected(HISTORICAL_ABI.source_fields_sha256,
                                                  required=True))

    def test_scanner_rejects_source_literal_but_not_documentation_or_string(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package = root / "bilqis_mlx"
            package.mkdir()
            tests = package / "semantics" / "tests"
            tests.mkdir(parents=True)
            (package / "example.py").write_text(
                'MODEL_SIZE = '+str(HISTORICAL_PREFIX_SIZE)+'\n'
                'MESSAGE = "historical '+str(HISTORICAL_PREFIX_SIZE)+' tokens"\n', encoding="utf-8")
            (tests / "test_fixture.py").write_text(
                'EXPECTED_MODEL_SIZE = '+str(HISTORICAL_PREFIX_SIZE)+'\n', encoding="utf-8")
            self.assertEqual(len(detect_literal_prefix_count(root, HISTORICAL_PREFIX_SIZE)), 1)

    def test_real_checker_is_advisory_without_external_policy(self):
        result = check_abi(SNAPSHOT, expected=None, require_external=False)
        self.assertFalse(result["external_expected_verified"])
        self.assertEqual(result["prohibited_executable_literals"], 0)

    def test_command_line_required_mode_fails_without_external_reference(self):
        env = dict(os.environ)
        env.pop("BILQIS_EXPECTED_ABI_SHA256", None)
        command = [sys.executable, "-B", "scripts/check_historical_abi.py", "--require-external"]
        missing = subprocess.run(command, cwd=ROOT, env=env,
                                 text=True, capture_output=True, check=False)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("EXTERNAL_REFERENCE_MISSING", missing.stderr)
        env["BILQIS_EXPECTED_ABI_SHA256"] = HISTORICAL_ABI.source_fields_sha256
        passing = subprocess.run(command, cwd=ROOT, env=env,
                                 text=True, capture_output=True, check=False)
        self.assertEqual(passing.returncode, 0, passing.stderr)
        self.assertTrue(json.loads(passing.stdout)["external_expected_verified"])


if __name__ == "__main__":
    unittest.main()
