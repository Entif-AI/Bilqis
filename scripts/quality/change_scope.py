"""Derive mechanically enforceable change scope for long-lived feature branches."""
from __future__ import annotations

from pathlib import Path
import subprocess

GOVERNANCE_ADOPTION_COMMIT = "f3c33e2ef06650a04914d2660ca9cc5e14f0f08b"


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=check)


def _is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return _git(root, "merge-base", "--is-ancestor", ancestor, descendant, check=False).returncode == 0


def _adoption_point(root: Path, head: str) -> str | None:
    if not _is_ancestor(root, GOVERNANCE_ADOPTION_COMMIT, head):
        return None
    first_parent = _git(root, "rev-list", "--first-parent", "--reverse", head).stdout.splitlines()
    return next((commit for commit in first_parent
                 if _is_ancestor(root, GOVERNANCE_ADOPTION_COMMIT, commit)), None)


def effective_base(root: Path, requested_base: str, head: str = "HEAD") -> str:
    """Return the pre-adoption comparison state for debt/regression measurement."""
    ordinary = _git(root, "merge-base", requested_base, head).stdout.strip()
    ancestry = _git(root, "rev-list", "--parents", "-n", "1", head).stdout.split()
    if len(ancestry) > 2 and ancestry[1] == ordinary:
        # GitHub Actions checks out a synthetic pull-request merge whose first
        # parent is the requested base. Treat that exact base as the temporal
        # boundary; walking the merge's first-parent trunk would otherwise make
        # unrelated mainline work look branch-owned.
        return ordinary
    adoption = _adoption_point(root, head)
    if not adoption or adoption == GOVERNANCE_ADOPTION_COMMIT:
        return ordinary
    parent = _git(root, "rev-parse", f"{adoption}^1", check=False)
    return parent.stdout.strip() if parent.returncode == 0 and parent.stdout.strip() else ordinary


def _blob(root: Path, revision: str, path: str) -> str | None:
    result = _git(root, "rev-parse", f"{revision}:{path}", check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def _changed_names(root: Path, before: str, after: str) -> set[str]:
    result = _git(root, "diff", "--name-only", before, after)
    return {line for line in result.stdout.splitlines() if line}


def _custom_merge_paths(root: Path, commit: str, parents: list[str]) -> set[str]:
    candidates: set[str] = set()
    for parent in parents:
        candidates.update(_changed_names(root, parent, commit))
    custom = set()
    for path in candidates:
        result_blob = _blob(root, commit, path)
        parent_blobs = [_blob(root, parent, path) for parent in parents]
        if all(result_blob != parent_blob for parent_blob in parent_blobs):
            custom.add(path)
    return custom


def _post_adoption_touched_paths(root: Path, adoption: str, head: str) -> set[str]:
    touched = set()
    adoption_ancestry = _git(root, "rev-list", "--parents", "-n", "1", adoption).stdout.split()
    adoption_parents = adoption_ancestry[1:]
    if len(adoption_parents) > 1:
        touched.update(_custom_merge_paths(root, adoption, adoption_parents))
    commits = _git(root, "rev-list", "--first-parent", "--reverse", f"{adoption}..{head}").stdout.splitlines()
    for commit in commits:
        ancestry = _git(root, "rev-list", "--parents", "-n", "1", commit).stdout.split()
        parents = ancestry[1:]
        if len(parents) <= 1:
            if parents:
                touched.update(_changed_names(root, parents[0], commit))
            continue
        touched.update(_custom_merge_paths(root, commit, parents))
    return touched


def _record_paths(line: str) -> tuple[str, ...]:
    fields = line.split("\t")
    if not fields:
        return ()
    if fields[0].startswith(("R", "C")):
        return tuple(fields[1:3])
    return tuple(fields[1:2])


def scoped_name_status(
    root: Path,
    requested_base: str,
    head: str = "HEAD",
    *,
    diff_filter: str = "ACMRD",
) -> tuple[str, str]:
    """Return comparison ref plus branch-owned post-adoption name-status changes.

    Imported base commits are not encounters. For a long-lived branch, only
    post-adoption non-merge edits and custom merge resolutions are mechanically
    scoped. Pre-adoption branch history remains outside the changed-path gate.
    """
    ordinary = _git(root, "merge-base", requested_base, head).stdout.strip()
    boundary = effective_base(root, requested_base, head)
    result = _git(root, "diff", "--name-status", "-M", f"--diff-filter={diff_filter}", boundary, head)
    adoption = _adoption_point(root, head)
    if boundary == ordinary or not adoption:
        return boundary, result.stdout
    touched = _post_adoption_touched_paths(root, adoption, head)
    lines = [line for line in result.stdout.splitlines()
             if touched.intersection(_record_paths(line))]
    return boundary, "\n".join(lines) + ("\n" if lines else "")
