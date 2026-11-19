"""Regression coverage for Release Please constituent-history preservation."""
from pathlib import Path
import unittest

from scripts.maintenance.release_history import (
    CommitRecord,
    PullRequestHistory,
    augment_changelog,
)


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "Entif-AI/Bilqis-MLX"
TICK = chr(96)


def history(number: int, merge_sha: str, *commits: tuple[str, str]):
    return PullRequestHistory(
        number=number,
        title=f"PR {number}",
        merge_sha=merge_sha,
        commits=tuple(CommitRecord(sha=sha, subject=subject) for sha, subject in commits),
    )


class ReleaseHistoryTests(unittest.TestCase):
    def test_multi_commit_prs_are_expanded_without_replacing_release_please_summary(self):
        changelog = """# Changelog

## [1.2.5](https://github.com/Entif-AI/Bilqis-MLX/compare/v1.2.4...v1.2.5) (2026-11-19)

### Bug Fixes

* **data-plane:** bound SQLite growth ([#1440](https://github.com/Entif-AI/Bilqis-MLX/issues/1440)) ([ccccccc](https://github.com/Entif-AI/Bilqis-MLX/commit/cccccccccccccccccccccccccccccccccccccccc))

### Performance Improvements

* **bamf:** speed up training ([#1408](https://github.com/Entif-AI/Bilqis-MLX/issues/1408)) ([ddddddd](https://github.com/Entif-AI/Bilqis-MLX/commit/dddddddddddddddddddddddddddddddddddddddd))

## [1.2.4](https://example.test) (2026-11-18)
"""
        histories = (
            history(
                1408,
                "d" * 40,
                ("1" * 40, "perf(bamf): first"),
                ("2" * 40, "fix(bamf): second"),
                ("3" * 40, "Merge branch 'main' into feature"),
            ),
            history(
                1440,
                "c" * 40,
                ("4" * 40, "fix(data-plane): first"),
                ("5" * 40, "refactor(data-plane): second"),
            ),
        )

        result = augment_changelog(changelog, "1.2.5", histories, REPOSITORY)

        self.assertIn("* **bamf:** speed up training", result)
        self.assertIn("### PR #1408 constituent commit inventory", result)
        self.assertIn("**3 additional constituent commits**", result)
        self.assertIn("2 source commits", result)
        self.assertIn("1 internal merge commit", result)
        self.assertIn("### PR #1440 constituent commit inventory", result)
        self.assertLess(
            result.index(f"{TICK}2222222222{TICK}"),
            result.index(f"{TICK}1111111111{TICK}"),
        )
        self.assertIn(f"{TICK}3333333333{TICK}", result)

    def test_constituents_already_listed_by_release_please_are_not_repeated(self):
        first = "4" * 40
        second = "5" * 40
        changelog = f"""# Changelog

## [1.2.5](https://example.test) (2026-11-19)
* first ([{first[:7]}](https://github.com/{REPOSITORY}/commit/{first}))
* second ([{second[:7]}](https://github.com/{REPOSITORY}/commit/{second}))
* summary ([#1440](https://github.com/{REPOSITORY}/issues/1440)) ([ccccccc](https://github.com/{REPOSITORY}/commit/{'c' * 40}))
"""
        histories = (
            history(
                1440,
                "c" * 40,
                (first, "fix(data-plane): first"),
                (second, "refactor(data-plane): second"),
            ),
        )

        result = augment_changelog(changelog, "1.2.5", histories, REPOSITORY)

        self.assertNotIn("PR #1440 constituent commit inventory", result)

    def test_single_commit_prs_do_not_get_redundant_inventory(self):
        changelog = """# Changelog

## [1.2.6](https://example.test) (2026-11-19)

### Bug Fixes
* fix ([#1442](https://github.com/Entif-AI/Bilqis-MLX/issues/1442)) ([aaaaaaa](https://github.com/Entif-AI/Bilqis-MLX/commit/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa))


## [1.2.5](https://example.test) (2026-11-19)
"""
        histories = (history(1442, "a" * 40, ("b" * 40, "fix(ci): one")),)

        result = augment_changelog(changelog, "1.2.6", histories, REPOSITORY)

        self.assertEqual(changelog, result)

    def test_augmentation_is_idempotent(self):
        changelog = """# Changelog

## [1.2.5](https://example.test) (2026-11-19)
* fix ([#1408](https://github.com/Entif-AI/Bilqis-MLX/issues/1408)) ([ddddddd](https://github.com/Entif-AI/Bilqis-MLX/commit/dddddddddddddddddddddddddddddddddddddddd))
"""
        histories = (
            history(
                1408,
                "d" * 40,
                ("1" * 40, "fix(bamf): first"),
                ("2" * 40, "fix(bamf): second"),
            ),
        )

        once = augment_changelog(changelog, "1.2.5", histories, REPOSITORY)
        twice = augment_changelog(once, "1.2.5", histories, REPOSITORY)

        self.assertEqual(once, twice)
        self.assertEqual(1, once.count("release-history:pr:1408:start"))

    def test_existing_manual_inventory_is_preserved_without_generated_duplicate(self):
        changelog = """# Changelog

## [1.2.2](https://example.test) (2026-11-17)
* summary ([#1377](https://github.com/Entif-AI/Bilqis-MLX/issues/1377)) ([aaaaaaa](https://github.com/Entif-AI/Bilqis-MLX/commit/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa))

### PR #1377 constituent commit inventory

Historical manually restored inventory.
"""
        histories = (
            history(
                1377,
                "a" * 40,
                ("1" * 40, "fix(bamf): first"),
                ("2" * 40, "fix(bamf): second"),
            ),
        )

        result = augment_changelog(changelog, "1.2.2", histories, REPOSITORY)

        self.assertEqual(changelog, result)

    def test_release_please_footer_stays_after_generated_inventory(self):
        changelog = """## [1.2.5](https://example.test) (2026-11-19)
* summary ([#1408](https://github.com/Entif-AI/Bilqis-MLX/issues/1408)) ([ddddddd](https://github.com/Entif-AI/Bilqis-MLX/commit/dddddddddddddddddddddddddddddddddddddddd))

---
This PR was generated with [Release Please](https://github.com/googleapis/release-please).
"""
        histories = (
            history(
                1408,
                "d" * 40,
                ("1" * 40, "fix(bamf): first"),
                ("2" * 40, "fix(bamf): second"),
            ),
        )

        result = augment_changelog(changelog, "1.2.5", histories, REPOSITORY)

        self.assertLess(
            result.index("PR #1408 constituent commit inventory"),
            result.index("---\nThis PR was generated with"),
        )
        self.assertTrue(result.rstrip().endswith(
            "This PR was generated with [Release Please]"
            "(https://github.com/googleapis/release-please)."
        ))

    def test_release_workflow_reconciles_release_pr_after_release_please(self):
        workflow = (ROOT / ".github/workflows/release-please.yml").read_text(
            encoding="utf-8")

        self.assertIn("id: release", workflow)
        self.assertIn("steps.release.outputs.prs_created", workflow)
        self.assertIn("release_history.py reconcile-pr", workflow)
        self.assertIn("release_history.py reconcile-body", workflow)
        self.assertLess(
            workflow.index('git push origin "HEAD:'),
            workflow.index("release_history.py reconcile-body"),
        )


if __name__ == "__main__":
    unittest.main()
