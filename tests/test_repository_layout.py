"""Release boundaries for the small public reference checkout."""

from __future__ import annotations

import json
import re
import tomllib
import unittest
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


class PublicSourceLayoutTests(unittest.TestCase):
    def test_historical_experiment_outputs_are_not_in_the_current_tree(self):
        self.assertFalse((ROOT / "docs/evidence").exists())
        self.assertFalse((ROOT / "docs/development").exists())
        self.assertFalse((ROOT / "FEATURE_LOG.md").exists())

    def test_current_reference_has_required_entrypoints(self):
        for path in (
            "bilqis_ref/run.py",
            "configs/smoke-bilqis-ternary.json",
            "docs/PROVENANCE.md",
            "docs/RELEASE_HISTORY.md",
            "docs/GOLDEN_RELEASE_GATE.md",
            "AGENTS.md",
        ):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file(), path)

    def test_python_package_version_matches_source_release_manifest(self):
        metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
        manifest = json.loads((ROOT / ".release-please-manifest.json").read_text())
        self.assertEqual(metadata["project"]["version"], manifest["."])
        release = json.loads((ROOT / "release-please-config.json").read_text())
        self.assertIn(
            {"type": "toml", "path": "pyproject.toml", "jsonpath": "$.project.version"},
            release["packages"]["."]["extra-files"],
        )

    def test_current_documentation_has_no_broken_relative_links(self):
        paths = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "AGENTS.md"]
        paths.extend((ROOT / "docs").rglob("*.md"))
        links = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
        for document in paths:
            for raw in links.findall(document.read_text()):
                target = unquote(raw.strip().split("#", 1)[0])
                if not target or target.startswith(("https://", "http://", "mailto:")):
                    continue
                self.assertTrue(
                    (document.parent / target).exists(),
                    f"{document.relative_to(ROOT)} has broken relative link: {raw}",
                )


if __name__ == "__main__":
    unittest.main()
