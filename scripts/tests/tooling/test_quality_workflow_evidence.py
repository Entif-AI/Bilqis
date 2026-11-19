"""CI cannot reuse an unproven expensive-suite result."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/quality.yml"


class QualityWorkflowEvidenceTests(unittest.TestCase):
    def test_expensive_suite_reuse_is_disabled_until_proof_bound(self):
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn(
            "EXPENSIVE_SUITE_REUSE_DISABLED_UNTIL_PROOF_BOUND", text)
        self.assertNotIn("reusing prior passing evidence", text)
        self.assertNotIn("Record reused passing test evidence", text)
        self.assertNotIn("expensive_tests=false", text)
        self.assertNotIn("semantic=${SKOS_ACTION:-REUSED}", text)

    def test_bamf_readiness_allows_for_macos_runner_queueing(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        match = re.search(
            r"(?ms)^  bamf-readiness:\n.*?^    timeout-minutes: (\d+)$",
            text,
        )
        self.assertIsNotNone(match)
        self.assertGreaterEqual(int(match.group(1)), 30)


if __name__ == "__main__":
    unittest.main()
