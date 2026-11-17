"""Pure release metadata/commit contract, no GitHub mutations."""
import json
from pathlib import Path
import unittest

from scripts.maintenance.release_version import changelog_section, conventional, VERSION


ROOT = Path(__file__).resolve().parents[2]


class ReleaseVersionTests(unittest.TestCase):
    def test_conventional_commits(self):
        for subject in ("feat(training): consolidate custody", "fix: repair Finder metadata",
                        "chore(release)!: update contracts", "docs: update operator instructions"):
            self.assertTrue(conventional(subject), subject)
        for subject in ("add some stuff", "Merge pull request #5", "feat: ", "feat(scope): hi"):
            self.assertFalse(conventional(subject), subject)

    def test_release_please_treats_refactors_as_user_facing(self):
        config = json.loads((ROOT / "release-please-config.json").read_text(encoding="utf-8"))
        sections = {entry["type"]: entry for entry in config["packages"]["."]["changelog-sections"]}
        expected_visibility = {
            "feat": False,
            "feature": False,
            "fix": False,
            "perf": False,
            "revert": False,
            "docs": True,
            "style": True,
            "chore": True,
            "refactor": False,
            "test": True,
            "build": True,
            "ci": True,
        }
        self.assertEqual(set(expected_visibility), set(sections))
        self.assertEqual(
            {kind: section["hidden"] for kind, section in sections.items()},
            expected_visibility,
        )
        self.assertEqual(sections["refactor"]["section"], "Code Refactoring")

    def test_semver_and_versioned_changelog(self):
        self.assertTrue(VERSION.fullmatch("0.2.0"))
        self.assertFalse(VERSION.fullmatch("01.2.0"))
        example = "# Changes\n\n## [0.2.0] - 2026-10-17\n\n### Added\n- Source custody\n\n## [0.1.0] - 2026-10-15\n### Added\n- Old\n"
        self.assertIn("Source custody", changelog_section(example, "0.2.0"))
        self.assertNotIn("Old", changelog_section(example, "0.2.0"))
        release_please = (
            "# Changes\n\n"
            "## [1.0.0](https://github.com/Entif-AI/Bilqis-MLX/compare/v0.2.0...v1.0.0) "
            "(2026-11-13)\n\n### Features\n- Generated release notes\n"
        )
        self.assertIn("Generated release notes", changelog_section(release_please, "1.0.0"))
        with self.assertRaisesRegex(ValueError, "CHANGELOG_VERSION_MISSING"):
            changelog_section(example, "0.3.0")


if __name__ == "__main__":
    unittest.main()
