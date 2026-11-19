"""Pull-request integration scope regressions for long-lived BAMF branches."""
from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.quality import pr_scope


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


class PullRequestScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bilqis-pr-scope-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "fixture@example.test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Fixture"], cwd=self.root, check=True)
        self.commit("root.txt", "root\n", "chore: root")

    def commit(self, name: str, text: str, message: str) -> str:
        (self.root / name).write_text(text, encoding="utf-8")
        subprocess.run(["git", "add", name], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", message], cwd=self.root, check=True)
        return git(self.root, "rev-parse", "HEAD")

    def test_synthetic_merge_uses_current_first_parent_when_event_base_is_stale(self):
        requested_base = git(self.root, "rev-parse", "HEAD")
        subprocess.run(["git", "switch", "-qc", "feature"], cwd=self.root, check=True)
        pr_head = self.commit("feature.py", "VALUE = 1\n", "fix: feature")
        subprocess.run(["git", "switch", "-q", "main"], cwd=self.root, check=True)
        current_base = self.commit("main.py", "VALUE = 2\n", "fix: main moved")
        subprocess.run(["git", "merge", "--no-ff", "-qm", "synthetic pr merge", "feature"],
                       cwd=self.root, check=True)

        self.assertEqual(
            pr_scope.comparison_base(
                self.root,
                event_name="pull_request",
                requested_base=requested_base,
                pr_head_sha=pr_head,
                push_base="",
            ),
            current_base,
        )

    def test_unified_commit_scope_begins_at_prospective_enforcement_baseline(self):
        requested_base = git(self.root, "rev-parse", "HEAD")
        historical = self.commit("legacy.py", "VALUE = 1\n", "Fix historical debt")
        current = self.commit("current.py", "VALUE = 2\n", "fix(ci): current repair")

        rows = pr_scope.commit_rows(
            self.root,
            base_sha=requested_base,
            head_sha=current,
            head_ref="codex/bamf-unified-base-20261028",
            unified_baseline=historical,
        )

        self.assertEqual(rows, [(current, "fix(ci): current repair")])

    def test_ordinary_pr_scope_keeps_the_full_commit_range(self):
        requested_base = git(self.root, "rev-parse", "HEAD")
        first = self.commit("first.py", "VALUE = 1\n", "fix: first")
        second = self.commit("second.py", "VALUE = 2\n", "fix: second")

        self.assertEqual(
            pr_scope.commit_rows(
                self.root,
                base_sha=requested_base,
                head_sha=second,
                head_ref="codex/ordinary-feature",
                unified_baseline=first,
            ),
            [(second, "fix: second"), (first, "fix: first")],
        )

    def test_ordinary_pr_scope_skips_merge_subjects_but_keeps_authored_commits(self):
        requested_base = git(self.root, "rev-parse", "HEAD")
        subprocess.run(["git", "switch", "-qc", "feature"], cwd=self.root, check=True)
        feature_commit = self.commit("feature.py", "VALUE = 1\n", "fix: feature")
        subprocess.run(["git", "switch", "-q", "main"], cwd=self.root, check=True)
        self.commit("base.py", "VALUE = 2\n", "fix: base moved")
        subprocess.run(["git", "switch", "-q", "feature"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "merge", "--no-ff", "-qm", "Merge main into feature", "main"],
            cwd=self.root,
            check=True,
        )
        current = self.commit("current.py", "VALUE = 3\n", "fix(ci): current repair")

        rows = pr_scope.commit_rows(
            self.root,
            base_sha=requested_base,
            head_sha=current,
            head_ref="codex/ordinary-feature",
            unified_baseline=feature_commit,
        )

        self.assertIn((feature_commit, "fix: feature"), rows)
        self.assertIn((current, "fix(ci): current repair"), rows)
        self.assertNotIn("Merge main into feature", [subject for _, subject in rows])

    def test_unified_lookalike_branch_gets_no_historical_exemption(self):
        requested_base = git(self.root, "rev-parse", "HEAD")
        historical = self.commit("legacy.py", "VALUE = 1\n", "Fix historical debt")
        current = self.commit("current.py", "VALUE = 2\n", "fix(ci): current repair")

        self.assertEqual(
            pr_scope.commit_rows(
                self.root,
                base_sha=requested_base,
                head_sha=current,
                head_ref="codex/bamf-unified-base-lookalike",
                unified_baseline=historical,
            ),
            [(current, "fix(ci): current repair"), (historical, "Fix historical debt")],
        )

    def test_unified_scope_revalidates_nonmerge_commits_from_merged_children(self):
        baseline = git(self.root, "rev-parse", "HEAD")
        subprocess.run(["git", "switch", "-qc", "child"], cwd=self.root, check=True)
        child = self.commit("child.py", "VALUE = 1\n", "Fix hidden child")
        subprocess.run(["git", "switch", "-q", "main"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "merge", "--no-ff", "-qm", "Merge child", "child"],
            cwd=self.root,
            check=True,
        )
        current = self.commit("current.py", "VALUE = 2\n", "fix(ci): current repair")

        rows = pr_scope.commit_rows(
            self.root,
            base_sha=baseline,
            head_sha=current,
            head_ref=pr_scope.UNIFIED_HEAD_REF,
            unified_baseline=baseline,
        )

        self.assertIn((child, "Fix hidden child"), rows)
        self.assertIn((current, "fix(ci): current repair"), rows)


if __name__ == "__main__":
    unittest.main()
