#!/usr/bin/env python3
"""Launch a long-running command detached from the agent socket.

The launcher writes durable PID/log/receipt files and asks macOS Notification
Center to alert the operator when the command exits. Interactive agents should
launch once, report the returned paths, and yield instead of polling.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


SCHEMA = "bilqis.bamf.detached-long-run/v2"
SNAPSHOT_IGNORED_NAMES = frozenset({
    ".git", ".local", ".pytest_cache", ".venv", "__pycache__",
    "node_modules", "venv",
})
MUTATION_IGNORED_NAMES = SNAPSHOT_IGNORED_NAMES | frozenset({
    ".testmondata", ".testmondata-journal", ".testmondata-shm", ".testmondata-wal",
    "_private", "runs",
})
SOURCE_MUTATED_EXIT = 86


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _snapshot_ignore(_directory: str, names: list[str]) -> set[str]:
    return set(names).intersection(SNAPSHOT_IGNORED_NAMES)


def _snapshot_entries(root: Path, *, ignored_names=SNAPSHOT_IGNORED_NAMES):
    root = root.resolve()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in ignored_names for part in relative.parts):
            continue
        yield path, relative


def _tree_digest(root: Path, *, ignored_names=SNAPSHOT_IGNORED_NAMES) -> str:
    digest = hashlib.sha256()
    for path, relative in _snapshot_entries(root, ignored_names=ignored_names):
        identity = relative.as_posix().encode("utf-8")
        mode = f"{path.lstat().st_mode & 0o7777:o}".encode("ascii")
        if path.is_symlink():
            digest.update(b"L\0" + identity + b"\0" + mode + b"\0")
            digest.update(os.readlink(path).encode("utf-8") + b"\0")
            continue
        if path.is_dir():
            digest.update(b"D\0" + identity + b"\0" + mode + b"\0")
            continue
        if not path.is_file():
            raise RuntimeError(f"unsupported detached source entry: {path}")
        digest.update(b"F\0" + identity + b"\0" + mode + b"\0")
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_snapshot_symlinks(root: Path) -> None:
    root = root.resolve()
    for path, _relative in _snapshot_entries(root):
        if not path.is_symlink():
            continue
        raw_target = Path(os.readlink(path))
        target = (path.parent / raw_target).resolve(strict=False)
        if not target.is_relative_to(root):
            raise RuntimeError(f"detached source symlink escapes workdir: {path}")


def _git_toplevel(source: Path) -> Path | None:
    completed = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False,
    )
    if completed.returncode:
        return None
    return Path(completed.stdout.strip()).resolve()


def _prepare_git_snapshot(source: Path, snapshot: Path) -> bool:
    """Create a real detached Git worktree when source is one repository root."""
    if _git_toplevel(source) != source:
        return False
    completed = subprocess.run(
        ["git", "-C", str(source), "worktree", "add", "--detach", str(snapshot), "HEAD"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            "detached git worktree creation failed: " + completed.stderr.strip())
    for child in snapshot.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    shutil.copytree(
        source, snapshot, symlinks=True, ignore=_snapshot_ignore,
        copy_function=shutil.copy2, dirs_exist_ok=True,
    )
    return True


def _bind_local_runtime(source: Path, snapshot: Path) -> None:
    """Expose an ignored local venv without copying it into every snapshot."""
    source_venv = source / ".venv"
    snapshot_venv = snapshot / ".venv"
    if not source_venv.exists() or snapshot_venv.exists():
        return
    snapshot_venv.symlink_to(source_venv, target_is_directory=True)


def _discard_snapshot(source: Path, snapshot: Path, *, git_snapshot: bool) -> None:
    if git_snapshot:
        subprocess.run(
            ["git", "-C", str(source), "worktree", "remove", "--force", str(snapshot)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
    shutil.rmtree(snapshot, ignore_errors=True)


def _snapshot_workdir(source: Path, snapshot: Path) -> dict[str, str]:
    """Copy one stable worktree image for every process in a detached run."""
    source = Path(source).resolve()
    snapshot = Path(snapshot).resolve()
    if not source.is_dir():
        raise RuntimeError(f"detached source workdir missing: {source}")
    if snapshot.exists():
        raise RuntimeError(f"detached source snapshot already exists: {snapshot}")
    if snapshot.is_relative_to(source):
        relative = snapshot.relative_to(source)
        if not relative.parts or relative.parts[0] not in SNAPSHOT_IGNORED_NAMES:
            raise RuntimeError("detached source snapshot must not recurse into its source")

    _validate_snapshot_symlinks(source)
    before = _tree_digest(source)
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    git_snapshot = False
    try:
        git_snapshot = _prepare_git_snapshot(source, snapshot)
        if not git_snapshot:
            shutil.copytree(
                source, snapshot, symlinks=True, ignore=_snapshot_ignore,
                copy_function=shutil.copy2,
            )
        _bind_local_runtime(source, snapshot)
        after = _tree_digest(source)
        copied = _tree_digest(snapshot)
        if before != after:
            raise RuntimeError("detached source changed while snapshot was being copied")
        if copied != after:
            raise RuntimeError("detached source snapshot digest mismatch")
    except Exception:
        _discard_snapshot(source, snapshot, git_snapshot=git_snapshot)
        raise
    return {"source_sha256": after, "snapshot_sha256": copied}


def _notify(label: str, returncode: int) -> None:
    status = "PASS" if returncode == 0 else f"FAIL ({returncode})"
    title = "Bilqis long run finished"
    body = f"{label}: {status}"
    script = (
        f"display notification {json.dumps(body)} "
        f"with title {json.dumps(title)} sound name \"Glass\""
    )
    result = subprocess.run(
        ["/usr/bin/osascript", "-e", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode and Path("/System/Library/Sounds/Glass.aiff").is_file():
        subprocess.Popen(
            ["/usr/bin/afplay", "/System/Library/Sounds/Glass.aiff"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )


def _worker(args) -> int:
    workdir = args.workdir.resolve()
    source_workdir = (args.source_workdir or args.workdir).resolve()
    log = args.log.resolve()
    receipt = args.receipt.resolve()
    pid_file = args.pid_file.resolve()
    log.parent.mkdir(parents=True, exist_ok=True)
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(f"{os.getpid()}\n", encoding="utf-8")
    started = _utc_now()
    snapshot_sha256 = _tree_digest(workdir)
    mutation_guard_sha256 = _tree_digest(
        workdir, ignored_names=MUTATION_IGNORED_NAMES)
    if args.snapshot_sha256 and snapshot_sha256 != args.snapshot_sha256:
        raise SystemExit("detached source snapshot changed before worker start")
    initial = {
        "schema": SCHEMA,
        "status": "RUNNING",
        "label": args.label,
        "pid": os.getpid(),
        "source_workdir": str(source_workdir),
        "workdir": str(workdir),
        "source_sha256": args.source_sha256 or snapshot_sha256,
        "snapshot_sha256": snapshot_sha256,
        "mutation_guard_sha256": mutation_guard_sha256,
        "command": args.command,
        "log": str(log),
        "started_at": started,
    }
    _write_json(receipt, initial)
    with log.open("ab", buffering=0) as stream:
        stream.write(
            (f"DETACHED_LONG_RUN_START {started} label={args.label!r} "
             f"pid={os.getpid()} command={args.command!r}\n").encode()
        )
        environment = os.environ.copy()
        environment.update({
            "BILQIS_DETACHED_SOURCE_WORKDIR": str(source_workdir),
            "BILQIS_DETACHED_SOURCE_SNAPSHOT": str(workdir),
            "BILQIS_DETACHED_SOURCE_SHA256": snapshot_sha256,
        })
        completed = subprocess.run(
            args.command,
            cwd=workdir,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
            env=environment,
        )
        finished = _utc_now()
        final_snapshot_sha256 = _tree_digest(workdir)
        final_mutation_guard_sha256 = _tree_digest(
            workdir, ignored_names=MUTATION_IGNORED_NAMES)
        source_mutated = final_mutation_guard_sha256 != mutation_guard_sha256
        returncode = SOURCE_MUTATED_EXIT if source_mutated else completed.returncode
        stream.write(
            (f"DETACHED_LONG_RUN_END {finished} label={args.label!r} "
             f"returncode={returncode} source_mutated={source_mutated}\n").encode()
        )
    final = {
        **initial,
        "status": "PASS" if returncode == 0 else "FAIL",
        "returncode": returncode,
        "command_returncode": completed.returncode,
        "source_mutated": source_mutated,
        "final_snapshot_sha256": final_snapshot_sha256,
        "final_mutation_guard_sha256": final_mutation_guard_sha256,
        "finished_at": finished,
    }
    _write_json(receipt, final)
    if not args.no_notify:
        _notify(args.label, returncode)
    return returncode


def _launch(args) -> int:
    if not args.command:
        raise SystemExit("command required after --")
    source_workdir = args.workdir.resolve()
    snapshot = (args.snapshot or (args.receipt.resolve().parent / "source-snapshot")).resolve()
    snapshot_receipt = _snapshot_workdir(source_workdir, snapshot)
    launcher = Path(__file__).resolve()
    try:
        worker_script = snapshot / launcher.relative_to(source_workdir)
    except ValueError:
        worker_script = launcher
    worker_args = [
        sys.executable, str(worker_script), "_worker",
        "--label", args.label,
        "--workdir", str(snapshot),
        "--source-workdir", str(source_workdir),
        "--source-sha256", snapshot_receipt["source_sha256"],
        "--snapshot-sha256", snapshot_receipt["snapshot_sha256"],
        "--log", str(args.log),
        "--receipt", str(args.receipt),
        "--pid-file", str(args.pid_file),
    ]
    if args.no_notify:
        worker_args.append("--no-notify")
    worker_args.extend(["--", *args.command])
    process = subprocess.Popen(
        worker_args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    print(json.dumps({
        "schema": SCHEMA,
        "status": "LAUNCHED",
        "label": args.label,
        "launcher_pid": process.pid,
        "source_workdir": str(source_workdir),
        "source_snapshot": str(snapshot),
        **snapshot_receipt,
        "log": str(args.log.resolve()),
        "receipt": str(args.receipt.resolve()),
        "pid_file": str(args.pid_file.resolve()),
        "continuation": (
            "After the desktop notification, return to the controlling chat and "
            f"ask it to resume from receipt {args.receipt.resolve()}"
        ),
    }, indent=2, sort_keys=True))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    for mode in ("launch", "_worker"):
        subparser = subparsers.add_parser(mode)
        subparser.add_argument("--label", required=True)
        subparser.add_argument("--workdir", type=Path, required=True)
        subparser.add_argument("--log", type=Path, required=True)
        subparser.add_argument("--receipt", type=Path, required=True)
        subparser.add_argument("--pid-file", type=Path, required=True)
        subparser.add_argument("--snapshot", type=Path)
        subparser.add_argument("--source-workdir", type=Path)
        subparser.add_argument("--source-sha256")
        subparser.add_argument("--snapshot-sha256")
        subparser.add_argument("--no-notify", action="store_true")
        subparser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    return _worker(args) if args.mode == "_worker" else _launch(args)


if __name__ == "__main__":
    raise SystemExit(main())
