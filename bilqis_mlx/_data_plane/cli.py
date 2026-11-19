"""Shared workstation data plane for immutable state and integrity cache."""
from __future__ import annotations
import json
import time
from contextlib import ExitStack
from pathlib import Path
from .contracts import DataPlaneError, _error
from .file_retention import file_gc_report
from .maintenance import gc_report, migrate_legacy_payloads, vacuum

def _facade():
    import bilqis_mlx.data_plane as facade
    return facade
def data_plane(*args, **kwargs): return _facade().data_plane(*args, **kwargs)
def dedupe_bundle_payloads(*args, **kwargs): return _facade().dedupe_bundle_payloads(*args, **kwargs)
def sync_event_ledger(*args, **kwargs): return _facade().sync_event_ledger(*args, **kwargs)
def referenced_custody_files(*args, **kwargs): return _facade().referenced_custody_files(*args, **kwargs)
def verify_file_digest(*args, **kwargs): return _facade().verify_file_digest(*args, **kwargs)


def _lock_root(root: Path, stack: ExitStack) -> None:
    import fcntl
    if not root.is_dir():
        raise ValueError(DataPlaneError.MAINTENANCE_ROOT_INVALID.value)
    names = set()
    if ((root / "bamf-state.json").exists()
            or (root / "bamf-bundles").exists()
            or (root / ".bamf-operator.lock").exists()):
        names.add(".bamf-operator.lock")
    if ((root / "state.json").exists()
            or (root / "states").exists()
            or (root / ".grade-a-operator.lock").exists()):
        names.add(".grade-a-operator.lock")
    if not names:
        raise ValueError(DataPlaneError.MAINTENANCE_ROOT_UNRECOGNIZED.value)
    for name in sorted(names):
        path = root / name
        if path.is_symlink():
            raise ValueError(DataPlaneError.OPERATOR_LOCK_UNSAFE.value)
        stream = stack.enter_context(path.open("a+b"))
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError(DataPlaneError.HUMAN_TRAINING_ACTIVE.value) from None


def _maintenance(args) -> dict:
    roots = tuple(path.expanduser().resolve(strict=True) for path in args.scan_root)
    if not roots:
        raise ValueError(DataPlaneError.MAINTENANCE_SCAN_ROOT_REQUIRED.value)
    with ExitStack() as stack:
        for root in roots:
            _lock_root(root, stack)
        plane = data_plane()
        before = plane.stats()
        result = {
            "mode": ("DATA_PLANE_MAINTENANCE_APPLIED" if args.apply
                     else "DATA_PLANE_MAINTENANCE_DRY_RUN"),
            "scope": args.scope,
            "before": before,
        }
        if not args.apply:
            if args.scope in {"all", "migrate"}:
                result["migration"] = {
                    "legacy_objects": before["legacy_objects"],
                    "legacy_nodes": before["legacy_nodes"],
                }
            if args.scope in {"all", "gc"}:
                result["gc"] = gc_report(plane, roots)
            if args.scope in {"all", "file-gc"}:
                result["file_gc"] = file_gc_report(plane, roots)
            return result
        if args.scope in {"all", "migrate"}:
            result["migration"] = migrate_legacy_payloads(
                plane, max_records=args.max_records)
        if args.scope in {"all", "gc"}:
            result["gc"] = gc_report(plane, roots, apply=True)
        if args.scope in {"all", "file-gc"}:
            result["file_gc"] = file_gc_report(plane, roots, apply=True)
        if args.scope in {"all", "gc"}:
            result["compaction"] = {
                kind: plane.compact_archive(kind) for kind in ("objects", "nodes")}
        if args.vacuum:
            vacuum(plane)
        result["sqlite_integrity"] = plane._db.execute(
            "PRAGMA integrity_check").fetchone()[0]
        result["after"] = plane.stats()
        return result

def main(argv=None) -> int:
    """Inspect or prewarm the shared workstation data plane."""
    import argparse
    import fcntl
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=(
        "status", "warm-custody", "warm-events", "dedupe-bundles", "maintenance"))
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--scan-root", action="append", type=Path, default=[])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--scope", choices=("all", "migrate", "gc", "file-gc"), default="all")
    parser.add_argument("--max-records", type=int, default=0)
    parser.add_argument("--vacuum", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "status":
        print(json.dumps(data_plane().stats(), sort_keys=True))
        return 0
    if args.action == "maintenance":
        print(json.dumps(_maintenance(args), sort_keys=True))
        return 0
    if args.run_dir is None:
        from .paths import active_run_dir
        root = active_run_dir().expanduser().resolve(strict=True)
    else:
        root = args.run_dir.expanduser().resolve(strict=True)
    lock = root / ".grade-a-operator.lock"
    if lock.is_symlink():
        raise ValueError(DataPlaneError.OPERATOR_LOCK_UNSAFE.value)
    with lock.open("a+b") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError(DataPlaneError.HUMAN_TRAINING_ACTIVE.value) from None
        if args.action == "dedupe-bundles":
            print(json.dumps(dedupe_bundle_payloads(root), sort_keys=True))
            return 0
        if args.action == "warm-events":
            started = time.perf_counter()
            result = sync_event_ledger(root)
            print(json.dumps({**result,
                              "mode": "EVENT_LEDGER_INDEX_WARMED",
                              "elapsed_seconds": round(
                                  time.perf_counter() - started, 3)}, sort_keys=True))
            return 0
        from .state_dag import read_current
        before = data_plane().stats()
        started = time.perf_counter()
        files = referenced_custody_files(root, read_current(root))
        for path, expected in files:
            if path.is_symlink() or not path.is_file():
                raise ValueError(_error(DataPlaneError.CUSTODY_ARTIFACT_MISSING, path))
            if not verify_file_digest(path, expected):
                raise ValueError(_error(DataPlaneError.CUSTODY_DIGEST_DRIFT, path))
        after = data_plane().stats()
        print(json.dumps({
            "mode": "CUSTODY_CACHE_WARMED",
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "referenced_files": len(files),
            "verified_before": before["verified_files"],
            "verified_after": after["verified_files"],
            "data_plane": after,
        }, sort_keys=True))
        return 0
    raise AssertionError(args.action)


if __name__ == "__main__":
    raise SystemExit(main())
