"""Temporal adoption tests for anti-monolith change scoping."""
from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.quality import change_scope


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


class ChangeScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bilqis-change-scope-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "fixture@example.test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Fixture"], cwd=self.root, check=True)
        (self.root / "root.txt").write_text("root\n")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "root"], cwd=self.root, check=True)
        self.root_sha = git(self.root, "rev-parse", "HEAD")
        self.old_adoption = change_scope.GOVERNANCE_ADOPTION_COMMIT
        self.addCleanup(setattr, change_scope, "GOVERNANCE_ADOPTION_COMMIT", self.old_adoption)

    def commit_file(self, name: str, text: str, message: str) -> str:
        (self.root / name).write_text(text)
        subprocess.run(["git", "add", name], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", message], cwd=self.root, check=True)
        return git(self.root, "rev-parse", "HEAD")

    def test_long_lived_branch_starts_enforcement_at_adoption_merge(self):
        subprocess.run(["git", "branch", "feature", self.root_sha], cwd=self.root, check=True)
        adoption = self.commit_file("governance.txt", "rule\n", "governance")
        change_scope.GOVERNANCE_ADOPTION_COMMIT = adoption
        main_head = self.commit_file("main.txt", "main\n", "main followup")
        subprocess.run(["git", "switch", "-q", "feature"], cwd=self.root, check=True)
        legacy = self.commit_file("legacy.py", "VALUE = 1\n", "legacy feature")
        subprocess.run(["git", "merge", "--no-ff", "-qm", "adopt governance", "main"], cwd=self.root, check=True)
        self.commit_file("post.py", "VALUE = 2\n", "post adoption")
        self.assertEqual(change_scope.effective_base(self.root, main_head), legacy)
        _, scoped = change_scope.scoped_name_status(self.root, main_head)
        self.assertIn("post.py", scoped)
        self.assertNotIn("legacy.py", scoped)
        self.assertNotIn("main.txt", scoped)

    def test_branch_created_after_adoption_uses_normal_merge_base(self):
        adoption = self.commit_file("governance.txt", "rule\n", "governance")
        change_scope.GOVERNANCE_ADOPTION_COMMIT = adoption
        main_head = self.commit_file("main.txt", "main\n", "main followup")
        subprocess.run(["git", "switch", "-qc", "feature"], cwd=self.root, check=True)
        self.commit_file("feature.py", "VALUE = 3\n", "feature")
        self.assertEqual(change_scope.effective_base(self.root, main_head), main_head)
        _, scoped = change_scope.scoped_name_status(self.root, main_head)
        self.assertIn("feature.py", scoped)

    def test_synthetic_pr_merge_scopes_only_changes_after_requested_base(self):
        adoption = self.commit_file("governance.txt", "rule\n", "governance")
        change_scope.GOVERNANCE_ADOPTION_COMMIT = adoption
        base = self.commit_file("base_only.py", "VALUE = 1\n", "base only")
        subprocess.run(["git", "switch", "-qc", "feature"], cwd=self.root, check=True)
        self.commit_file("feature.py", "VALUE = 2\n", "feature")
        subprocess.run(["git", "switch", "-q", "main"], cwd=self.root, check=True)
        subprocess.run(["git", "merge", "--no-ff", "-qm", "synthetic pr merge", "feature"],
                       cwd=self.root, check=True)

        self.assertEqual(change_scope.effective_base(self.root, base), base)
        boundary, scoped = change_scope.scoped_name_status(self.root, base)
        self.assertEqual(boundary, base)
        self.assertIn("feature.py", scoped)
        self.assertNotIn("base_only.py", scoped)

    def test_later_base_merge_does_not_make_imported_file_an_encounter(self):
        subprocess.run(["git", "branch", "feature", self.root_sha], cwd=self.root, check=True)
        adoption = self.commit_file("governance.txt", "rule\n", "governance")
        change_scope.GOVERNANCE_ADOPTION_COMMIT = adoption
        subprocess.run(["git", "switch", "-q", "feature"], cwd=self.root, check=True)
        self.commit_file("legacy.py", "VALUE = 1\n", "legacy feature")
        subprocess.run(["git", "merge", "--no-ff", "-qm", "adopt governance", "main"], cwd=self.root, check=True)
        self.commit_file("feature.py", "VALUE = 2\n", "post adoption feature")
        subprocess.run(["git", "switch", "-q", "main"], cwd=self.root, check=True)
        main_head = self.commit_file("base_only.py", "VALUE = 9\n", "base only")
        subprocess.run(["git", "switch", "-q", "feature"], cwd=self.root, check=True)
        subprocess.run(["git", "merge", "--no-ff", "-qm", "sync base", "main"], cwd=self.root, check=True)
        _, scoped = change_scope.scoped_name_status(self.root, main_head)
        self.assertIn("feature.py", scoped)
        self.assertNotIn("base_only.py", scoped)

    def test_custom_merge_resolution_remains_in_scope(self):
        (self.root / "shared.py").write_text("VALUE = 'root'\n")
        subprocess.run(["git", "add", "shared.py"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "shared root"], cwd=self.root, check=True)
        common = git(self.root, "rev-parse", "HEAD")
        subprocess.run(["git", "branch", "feature", common], cwd=self.root, check=True)
        adoption = self.commit_file("governance.txt", "rule\n", "governance")
        change_scope.GOVERNANCE_ADOPTION_COMMIT = adoption
        subprocess.run(["git", "switch", "-q", "feature"], cwd=self.root, check=True)
        self.commit_file("shared.py", "VALUE = 'legacy feature'\n", "legacy shared edit")
        subprocess.run(["git", "merge", "--no-ff", "-qm", "adopt governance", "main"], cwd=self.root, check=True)
        subprocess.run(["git", "switch", "-q", "main"], cwd=self.root, check=True)
        main_head = self.commit_file("shared.py", "VALUE = 'main later'\n", "base shared edit")
        subprocess.run(["git", "switch", "-q", "feature"], cwd=self.root, check=True)
        merge = subprocess.run(["git", "merge", "--no-ff", "main"], cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(merge.returncode, 0)
        (self.root / "shared.py").write_text("VALUE = 'custom resolution'\n")
        subprocess.run(["git", "add", "shared.py"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "resolve shared"], cwd=self.root, check=True)
        _, scoped = change_scope.scoped_name_status(self.root, main_head)
        self.assertIn("shared.py", scoped)


if __name__ == "__main__":
    unittest.main()
