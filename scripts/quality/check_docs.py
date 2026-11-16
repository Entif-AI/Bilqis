#!/usr/bin/env python3
"""Check the authored Markdown link graph and documentation taxonomy."""

from __future__ import annotations

import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ALLOWED_DOCS_DIRECTORIES = frozenset(
    {
        "architecture",
        "evidence",
        "history",
        "operations",
        "provenance",
        "specifications",
        "tasks",
    }
)
IGNORED_DIRECTORIES = frozenset({".git", "node_modules", "runs", "vendor"})
INLINE_LINK = re.compile(
    r"(?<!!)\[[^]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\s*\)"
)
REFERENCE_LINK = re.compile(
    r"(?m)^[ \t]{0,3}\[[^]]+\]:\s*(?:<([^>]+)>|([^\s]+))"
)


def _markdown_paths(root: Path) -> tuple[Path, ...]:
    paths = []
    for current, directories, files in os.walk(root):
        directories[:] = sorted(
            directory for directory in directories if directory not in IGNORED_DIRECTORIES
        )
        current_path = Path(current)
        paths.extend(current_path / filename for filename in sorted(files) if filename.endswith(".md"))
    return tuple(paths)


def _link_targets(content: str) -> tuple[tuple[int, str], ...]:
    targets = []
    for pattern in (INLINE_LINK, REFERENCE_LINK):
        for match in pattern.finditer(content):
            target = match.group(1) or match.group(2)
            targets.append((content.count("\n", 0, match.start()) + 1, target))
    return tuple(targets)


def _is_local_target(target: str) -> bool:
    if not target or target.startswith(("#", "/", "//")):
        return False
    parsed = urlsplit(target)
    return not parsed.scheme and not parsed.netloc


def _target_exists(path: Path, target: str, root: Path) -> bool:
    parsed = urlsplit(target)
    decoded_path = unquote(parsed.path)
    if not decoded_path:
        return True
    candidates = ((path.parent / decoded_path).resolve(), (root / decoded_path).resolve())
    for candidate in candidates:
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if candidate.exists():
            return True
    return False


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _has_authored_files(directory: Path) -> bool:
    return any(
        path.is_file() and not path.name.startswith(".") for path in directory.rglob("*")
    )


def inspect_docs(root: Path) -> tuple[str, ...]:
    """Return deterministic violations without mutating documentation."""
    root = root.resolve()
    problems: list[str] = []
    docs = root / "docs"
    if docs.is_dir():
        for path in sorted(docs.iterdir()):
            if path.is_file() and not path.name.startswith(".") and path.name != "README.md":
                problems.append(f"{_relative(path, root)} DOCS_ROOT_FILE")
            elif (
                path.is_dir()
                and path.name not in ALLOWED_DOCS_DIRECTORIES
                and _has_authored_files(path)
            ):
                problems.append(f"{_relative(path, root)} DOCS_TOP_LEVEL_DIRECTORY")

    for path in _markdown_paths(root):
        content = path.read_text(encoding="utf-8")
        for line, target in _link_targets(content):
            if _is_local_target(target) and not _target_exists(path, target, root):
                problems.append(f"{_relative(path, root)}:{line} BROKEN_MARKDOWN_LINK {target}")
    return tuple(sorted(problems))


def main(argv: list[str] | None = None) -> int:
    del argv
    issues = inspect_docs(Path(__file__).resolve().parents[2])
    for issue in issues:
        print(issue)
    if issues:
        return 1
    print("DOCS_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
