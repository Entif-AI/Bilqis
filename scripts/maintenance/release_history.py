"""Preserve constituent PR history that Release Please collapses into summaries."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
import tempfile


HEADER = re.compile(r"(?m)^## \[([^\]]+)\].*$")
PR_LINK = re.compile(r"\[#(\d+)\]\(https://github\.com/[^)]+/issues/\d+\)")
COMMIT_URL = re.compile(r"/commit/([0-9a-f]{7,40})")
MANAGED = re.compile(
    r"(?ms)\n*<!-- release-history:pr:(\d+):start -->.*?"
    r"<!-- release-history:pr:\1:end -->\n*"
)
TICK = chr(96)


@dataclass(frozen=True)
class CommitRecord:
    sha: str
    subject: str


@dataclass(frozen=True)
class PullRequestHistory:
    number: int
    title: str
    merge_sha: str
    commits: tuple[CommitRecord, ...]
    total_commits: int | None = None

    @property
    def original_count(self) -> int:
        return self.total_commits if self.total_commits is not None else len(self.commits)


def _merge_subject(subject: str) -> bool:
    return bool(re.match(r"(?i)^merge(?:\b|:)", subject.strip()))


def _release_bounds(text: str, version: str) -> tuple[int, int]:
    matches = list(HEADER.finditer(text))
    for index, match in enumerate(matches):
        if match.group(1) != version:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        footer = text.find(
            "\n---\nThis PR was generated with [Release Please]",
            match.end(),
            end,
        )
        if footer != -1:
            end = footer
        return match.start(), end
    raise ValueError(f"CHANGELOG_VERSION_MISSING:{version}")


def release_section(text: str, version: str) -> str:
    start, end = _release_bounds(text, version)
    return text[start:end].rstrip() + "\n"


def top_release_version(text: str) -> str:
    match = HEADER.search(text)
    if match is None:
        raise ValueError("CHANGELOG_RELEASE_SECTION_MISSING")
    return match.group(1)


def _plural(count: int, singular: str) -> str:
    return f"{count} {singular if count == 1 else singular + 's'}"


def _commit_lines(commits: list[CommitRecord], repository: str) -> str:
    return "\n".join(
        f"- [{TICK}{commit.sha[:10]}{TICK}]"
        f"(https://github.com/{repository}/commit/{commit.sha}) {commit.subject}"
        for commit in reversed(commits)
    )


def _inventory(history: PullRequestHistory, commits: list[CommitRecord],
               repository: str) -> str:
    sources = [commit for commit in commits if not _merge_subject(commit.subject)]
    merges = [commit for commit in commits if _merge_subject(commit.subject)]
    labels = [
        _plural(len(sources), "source commit"),
        _plural(len(merges), "internal merge commit"),
    ]
    summary = " and ".join(label for label in labels if not label.startswith("0 "))
    merge_link = (
        f"[{TICK}{history.merge_sha[:7]}{TICK}]"
        f"(https://github.com/{repository}/commit/{history.merge_sha})"
    )
    parts = [
        f"<!-- release-history:pr:{history.number}:start -->",
        f"### PR #{history.number} constituent commit inventory",
        "",
        f"Release Please summarized PR #{history.number} as {merge_link}. "
        f"This generated inventory preserves **{len(commits)} additional constituent "
        f"commits** that are newer than the prior release boundary but absent from "
        f"the generated release section: **{summary}**.",
    ]
    if sources:
        parts.extend([
            "",
            "<details>",
            f"<summary>{_plural(len(sources), 'source commit')} "
            "(newest-first PR order)</summary>",
            "",
            _commit_lines(sources, repository),
            "",
            "</details>",
        ])
    if merges:
        parts.extend([
            "",
            "<details>",
            f"<summary>{_plural(len(merges), 'internal merge commit')} "
            "(newest-first PR order)</summary>",
            "",
            _commit_lines(merges, repository),
            "",
            "</details>",
        ])
    parts.extend(["", f"<!-- release-history:pr:{history.number}:end -->"])
    return "\n".join(parts)


def augment_changelog(text: str, version: str,
                      histories: tuple[PullRequestHistory, ...],
                      repository: str) -> str:
    start, end = _release_bounds(text, version)
    original_section = text[start:end]
    cleaned_section = MANAGED.sub("\n", original_section)
    had_managed = cleaned_section != original_section
    section = cleaned_section.rstrip()
    represented = set(COMMIT_URL.findall(section))
    blocks = []
    for history in sorted(histories, key=lambda item: item.number):
        if history.original_count <= 1:
            continue
        if f"### PR #{history.number} constituent commit inventory" in section:
            continue
        missing = [commit for commit in history.commits if commit.sha not in represented]
        if missing:
            blocks.append(_inventory(history, missing, repository))
    if not blocks and not had_managed:
        return text
    if blocks:
        section = section + "\n\n" + "\n\n".join(blocks) + "\n"
    else:
        section = section + "\n"
    return text[:start] + section + text[end:]


def _run(*args: str) -> str:
    return subprocess.run(
        args, text=True, capture_output=True, check=True).stdout


def _commit_exists(sha: str) -> bool:
    result = subprocess.run(
        ("git", "cat-file", "-e", f"{sha}^{{commit}}"),
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


def _remote_repository(url: str) -> str:
    value = url.strip().removesuffix(".git")
    if value.startswith("git@github.com:"):
        return value.split(":", 1)[1]
    marker = "github.com/"
    if marker in value:
        return value.split(marker, 1)[1]
    return ""


def _github_remote(repository: str) -> str:
    for remote in _run("git", "remote").split():
        url = _run("git", "remote", "get-url", remote).strip()
        if _remote_repository(url).lower() == repository.lower():
            return remote
    raise RuntimeError(f"RELEASE_HISTORY_GITHUB_REMOTE_MISSING:{repository}")


def _ensure_pr_head(number: int, sha: str, repository: str) -> None:
    if _commit_exists(sha):
        return
    remote = _github_remote(repository)
    subprocess.run(
        ("git", "fetch", "--no-tags", remote, f"refs/pull/{number}/head"),
        text=True,
        capture_output=True,
        check=True,
    )
    if not _commit_exists(sha):
        raise RuntimeError(f"RELEASE_HISTORY_PR_HEAD_MISSING:{number}:{sha}")


def _first_parent(sha: str) -> str:
    fields = _run("git", "rev-list", "--parents", "-n1", sha).split()
    if len(fields) < 2:
        raise RuntimeError(f"RELEASE_HISTORY_MERGE_PARENT_MISSING:{sha}")
    return fields[1]


def _pr_only_commits(number: int, head_sha: str, merge_sha: str,
                     repository: str) -> tuple[CommitRecord, ...]:
    _ensure_pr_head(number, head_sha, repository)
    base_sha = _first_parent(merge_sha)
    shas = _run(
        "git", "rev-list", "--reverse", "--topo-order",
        head_sha, "--not", base_sha,
    ).split()
    return tuple(
        CommitRecord(sha=sha, subject=_run("git", "show", "-s", "--format=%s", sha).strip())
        for sha in shas
    )


def _history_for_pr(number: int, repository: str,
                    section: str) -> PullRequestHistory | None:
    result = subprocess.run(
        ("gh", "pr", "view", str(number), "--repo", repository,
         "--json", "title,mergeCommit,headRefOid"),
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    payload = json.loads(result.stdout)
    merge_sha = (payload.get("mergeCommit") or {}).get("oid") or ""
    if not merge_sha or merge_sha not in section:
        return None
    head_sha = payload.get("headRefOid") or ""
    if not head_sha:
        raise RuntimeError(f"RELEASE_HISTORY_PR_HEAD_UNAVAILABLE:{number}")
    commits = _pr_only_commits(number, head_sha, merge_sha, repository)
    return PullRequestHistory(
        number=number,
        title=payload.get("title") or f"PR {number}",
        merge_sha=merge_sha,
        commits=commits,
        total_commits=len(commits),
    )


def discover_histories(text: str, version: str,
                       repository: str) -> tuple[PullRequestHistory, ...]:
    section = release_section(text, version)
    histories = []
    for number in sorted({int(value) for value in PR_LINK.findall(section)}):
        history = _history_for_pr(number, repository, section)
        if history is not None:
            histories.append(history)
    return tuple(histories)


def _update_release_pr_body(number: int, version: str,
                            histories: tuple[PullRequestHistory, ...],
                            repository: str) -> bool:
    body = _run(
        "gh", "pr", "view", str(number), "--repo", repository,
        "--json", "body", "--jq", ".body",
    )
    updated = augment_changelog(body, version, histories, repository)
    if updated == body:
        return False
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(updated)
        path = handle.name
    try:
        _run("gh", "pr", "edit", str(number), "--repo", repository,
             "--body-file", path)
    finally:
        Path(path).unlink(missing_ok=True)
    return True


def reconcile(path: Path, version: str, repository: str) -> bool:
    original = path.read_text(encoding="utf-8")
    histories = discover_histories(original, version, repository)
    updated = augment_changelog(original, version, histories, repository)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
    return updated != original


def reconcile_body(path: Path, version: str, repository: str,
                   release_pr: int) -> bool:
    changelog = path.read_text(encoding="utf-8")
    histories = discover_histories(changelog, version, repository)
    return _update_release_pr_body(
        release_pr, version, histories, repository)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repository", required=True)
    common.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    sub.add_parser("reconcile-pr", parents=[common])
    reconcile_body_parser = sub.add_parser("reconcile-body", parents=[common])
    reconcile_body_parser.add_argument("--release-pr", type=int, required=True)
    backfill = sub.add_parser("backfill", parents=[common])
    backfill.add_argument("--version", required=True)
    args = parser.parse_args(argv)
    if args.command == "reconcile-pr":
        version = top_release_version(args.changelog.read_text(encoding="utf-8"))
        changed = reconcile(args.changelog, version, args.repository)
    elif args.command == "reconcile-body":
        version = top_release_version(args.changelog.read_text(encoding="utf-8"))
        changed = reconcile_body(
            args.changelog, version, args.repository, args.release_pr)
    else:
        changed = reconcile(args.changelog, args.version, args.repository)
    print("RELEASE_HISTORY_UPDATED" if changed else "RELEASE_HISTORY_CURRENT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
