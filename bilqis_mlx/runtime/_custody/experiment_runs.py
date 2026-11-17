"""Custody for issue 349's two isolated, disposable experiment runs.

This owner deliberately knows nothing about models or optimizer state.  It only
creates and accounts for issue-owned directories, leaving training authority to
the caller.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
from typing import Iterator, Sequence
from uuid import uuid4

from bilqis_mlx.runtime.disk import atomic_text


ISSUE_NUMBER = 349
DEFAULT_MAX_BYTES = 100_000_000_000
MAX_RUNS = 2
_REGISTRY_NAME = ".issue349-experiment-runs.json"
_LOCK_NAME = ".issue349-experiment-runs.lock"
_MANIFEST_NAME = ".experiment-run.json"
_RECEIPTS_DIR = "cleanup-receipts"
_BASE_PROTECTED = frozenset({
    "current", "best", "recovery", "state", "state.json",
    "run-state.json", "run_state.json", "events.jsonl", "factory-releases",
    "autonomy",
    "manifest", "manifests", "source-manifest.json", "source_manifest.json",
    "bundle", "bundles", "receipts", _RECEIPTS_DIR, _MANIFEST_NAME,
})


class ExperimentRunBudget:
    """Fail-closed registry and block-accounting owner for a dedicated root."""

    def __init__(self, root: Path, *, max_bytes: int = DEFAULT_MAX_BYTES,
                 reserve_bytes: int = 0, issue_number: int = ISSUE_NUMBER) -> None:
        if issue_number != ISSUE_NUMBER:
            raise ValueError("EXPERIMENT_RUN_WRONG_ISSUE")
        if max_bytes < 1 or reserve_bytes < 0 or reserve_bytes > max_bytes:
            raise ValueError("INVALID_EXPERIMENT_DISK_BUDGET")
        self.root = Path(root)
        self.max_bytes = max_bytes
        self.reserve_bytes = reserve_bytes
        self.issue_number = issue_number

    @property
    def registry_path(self) -> Path:
        return self.root / _REGISTRY_NAME

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self._assert_safe_root_path()
        self.root.mkdir(parents=True, exist_ok=True)
        lock = self.root / _LOCK_NAME
        with lock.open("a+", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def create(self, name: str, *, required_paths: Sequence[str] = (),
               required_bytes: int = 0) -> Path:
        """Atomically create one new registered run; existing paths are never adopted."""
        with self._locked():
            self._assert_root_shape()
            target = self._run_path(name)
            if target.exists() or target.is_symlink():
                raise RuntimeError("EXPERIMENT_RUN_UNREGISTERED_PATH")
            registry = self._read_registry()
            if len(registry["runs"]) >= MAX_RUNS:
                raise RuntimeError("EXPERIMENT_RUN_LIMIT")
            self._assert_create_preflight(registry, required_bytes)
            target.mkdir(mode=0o700)
            manifest = self._manifest(target, required_paths)
            try:
                atomic_text(target / _MANIFEST_NAME,
                            json.dumps(manifest, sort_keys=True) + "\n")
                registry["runs"].append(name)
                self._write_registry(registry)
                self._assert_consistent(registry)
            except Exception:
                # A partial directory is intentionally left visible for operator
                # reconciliation rather than silently deleting custody evidence.
                raise
            return target

    def register(self, run: Path) -> dict:
        """Read back an already-created registration; arbitrary adoption is forbidden."""
        with self._locked():
            registry = self._read_registry()
            target = self._checked_registered_path(run, registry)
            return self._read_manifest(target)

    def check(self) -> dict:
        with self._locked():
            registry = self._read_registry()
            self._assert_consistent(registry)
            used = sum(self._allocated_bytes(self.root / name) for name in registry["runs"])
            return {"issue_number": self.issue_number, "run_count": len(registry["runs"]),
                    "max_bytes": self.max_bytes, "reserve_bytes": self.reserve_bytes,
                    "used_bytes": used,
                    "within_budget": used + self.reserve_bytes <= self.max_bytes,
                    "runs": tuple(registry["runs"])}

    def enforce(self) -> dict:
        """Periodic monitor entry point; callers decide when to invoke it."""
        return self.assert_within_budget()

    def assert_within_budget(self) -> dict:
        report = self.check()
        if not report["within_budget"]:
            raise RuntimeError("EXPERIMENT_DISK_BUDGET_EXHAUSTED")
        return report

    def assert_can_allocate(self, required_bytes: int = 0) -> dict:
        """Fail before a bounded write when collective measured use is too high."""
        with self._locked():
            registry = self._read_registry()
            self._assert_consistent(registry)
            self._assert_create_preflight(registry, required_bytes)
            used = sum(
                self._allocated_bytes(self.root / name)
                for name in registry["runs"])
            return {
                "issue_number": self.issue_number,
                "run_count": len(registry["runs"]),
                "max_bytes": self.max_bytes,
                "reserve_bytes": self.reserve_bytes,
                "used_bytes": used,
                "required_bytes": required_bytes,
                "within_budget": True,
                "runs": tuple(registry["runs"]),
            }

    def prune(self, run: Path, disposable_paths: Sequence[str]) -> Path:
        """Delete only explicitly named non-required regular files, then receipt it."""
        with self._locked():
            registry = self._read_registry()
            target = self._checked_registered_path(run, registry)
            manifest = self._read_manifest(target)
            protected = set(manifest["protected_paths"]) | set(manifest["required_paths"])
            deleted: list[str] = []
            for relative in disposable_paths:
                artifact = self._contained_path(target, relative)
                normalized = artifact.relative_to(target).as_posix()
                if self._is_protected(normalized, protected):
                    raise RuntimeError("EXPERIMENT_RUN_PROTECTED_ARTIFACT")
                if artifact.is_symlink() or not artifact.is_file():
                    raise RuntimeError("EXPERIMENT_RUN_DISPOSABLE_REQUIRED")
                artifact.unlink()
                deleted.append(normalized)
            receipt_dir = target / _RECEIPTS_DIR
            receipt_dir.mkdir(mode=0o700, exist_ok=True)
            receipt = receipt_dir / (uuid4().hex + ".json")
            atomic_text(receipt, json.dumps({"issue_number": ISSUE_NUMBER,
                                              "run": target.name,
                                              "deleted": deleted}, sort_keys=True) + "\n")
            self._assert_consistent(registry)
            return receipt

    def _run_path(self, name: str) -> Path:
        if not name or Path(name).name != name or name.startswith("."):
            raise ValueError("INVALID_EXPERIMENT_RUN_NAME")
        target = self.root / name
        if target.parent != self.root:
            raise RuntimeError("EXPERIMENT_RUN_PATH_ESCAPE")
        return target

    def _contained_path(self, root: Path, relative: str) -> Path:
        relative_path = Path(relative)
        candidate = root / relative_path
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise RuntimeError("EXPERIMENT_RUN_PATH_ESCAPE") from error
        # lexical containment catches '..' without following links.
        if ".." in relative_path.parts or candidate == root:
            raise RuntimeError("EXPERIMENT_RUN_PATH_ESCAPE")
        # Never follow a symlink at any depth.  Checking only the final artifact
        # would allow run/escape/file to unlink outside custody when escape is a
        # symlink to canonical or historical evidence.
        current = root
        for part in relative_path.parts:
            current = current / part
            if current.is_symlink():
                raise RuntimeError("EXPERIMENT_RUN_SYMLINK")
        return candidate

    def _assert_root_shape(self) -> None:
        for entry in self.root.iterdir():
            if entry.name in {_REGISTRY_NAME, _LOCK_NAME}:
                continue
            if entry.is_symlink():
                raise RuntimeError("EXPERIMENT_RUN_SYMLINK")
            if entry.is_dir():
                registry = self._read_registry()
                if entry.name not in registry["runs"]:
                    raise RuntimeError("EXPERIMENT_RUN_UNREGISTERED_PATH")
            else:
                raise RuntimeError("EXPERIMENT_RUN_REGISTRY_DRIFT")

    def _assert_safe_root_path(self) -> None:
        """Reject symlinks before opening the lock or creating the root."""
        current = self.root.absolute()
        while not current.exists() and not current.is_symlink():
            if current.parent == current:
                break
            current = current.parent
        if current.is_symlink():
            raise RuntimeError("EXPERIMENT_RUN_SYMLINK")

    def _assert_create_preflight(self, registry: dict, required_bytes: int) -> None:
        if not isinstance(required_bytes, int) or required_bytes < 0:
            raise ValueError("INVALID_EXPERIMENT_REQUIRED_BYTES")
        self._assert_budget_identity(registry)
        used = sum(self._allocated_bytes(self.root / name) for name in registry["runs"])
        if used + required_bytes + self.reserve_bytes > self.max_bytes:
            raise RuntimeError("EXPERIMENT_DISK_PRECHECK_EXHAUSTED")

    def _empty_registry(self) -> dict:
        return {"issue_number": ISSUE_NUMBER, "schema": 2, "runs": [],
                "max_bytes": self.max_bytes, "reserve_bytes": self.reserve_bytes}

    def _read_registry(self) -> dict:
        if not self.registry_path.exists():
            return self._empty_registry()
        if self.registry_path.is_symlink():
            raise RuntimeError("EXPERIMENT_RUN_SYMLINK")
        try:
            registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError("EXPERIMENT_RUN_REGISTRY_DRIFT") from error
        if (registry.get("issue_number") != ISSUE_NUMBER or registry.get("schema") != 2
                or not isinstance(registry.get("runs"), list)
                or any(not isinstance(name, str) for name in registry["runs"])
                or len(registry["runs"]) != len(set(registry["runs"]))):
            raise RuntimeError("EXPERIMENT_RUN_REGISTRY_DRIFT")
        self._assert_budget_identity(registry)
        return registry

    def _assert_budget_identity(self, registry: dict) -> None:
        if (registry.get("max_bytes") != self.max_bytes
                or registry.get("reserve_bytes") != self.reserve_bytes):
            raise RuntimeError("EXPERIMENT_RUN_BUDGET_DRIFT")

    def _write_registry(self, registry: dict) -> None:
        if self.registry_path.is_symlink():
            raise RuntimeError("EXPERIMENT_RUN_SYMLINK")
        temporary = self.root / ("." + _REGISTRY_NAME + "." + uuid4().hex + ".tmp")
        try:
            with temporary.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(registry, sort_keys=True) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.registry_path)
            directory_fd = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temporary.unlink(missing_ok=True)

    def _manifest(self, run: Path, required_paths: Sequence[str]) -> dict:
        required = sorted({self._contained_path(run, path).relative_to(run).as_posix()
                           for path in required_paths})
        return {"issue_number": ISSUE_NUMBER, "protected_paths": sorted(_BASE_PROTECTED),
                "required_paths": required, "run_name": run.name, "schema": 2}

    def _read_manifest(self, run: Path) -> dict:
        manifest_path = run / _MANIFEST_NAME
        if manifest_path.is_symlink():
            raise RuntimeError("EXPERIMENT_RUN_SYMLINK")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError("EXPERIMENT_RUN_REGISTRY_DRIFT") from error
        if (manifest.get("issue_number") != ISSUE_NUMBER or manifest.get("schema") != 2
                or manifest.get("run_name") != run.name
                or not isinstance(manifest.get("required_paths"), list)
                or manifest.get("protected_paths") != sorted(_BASE_PROTECTED)):
            raise RuntimeError("EXPERIMENT_RUN_REGISTRY_DRIFT")
        for value in manifest["required_paths"]:
            if not isinstance(value, str):
                raise RuntimeError("EXPERIMENT_RUN_REGISTRY_DRIFT")
            self._contained_path(run, value)
        return manifest

    def _is_protected(self, relative: str, protected: set[str]) -> bool:
        parts = Path(relative).parts
        for protected_path in protected:
            protected_parts = Path(protected_path).parts
            if parts[:len(protected_parts)] == protected_parts:
                return True
            if protected_parts[:len(parts)] == parts:
                return True
        return any("manifest" in part.lower() or "bundle" in part.lower() for part in parts)

    def _checked_registered_path(self, run: Path, registry: dict) -> Path:
        supplied = Path(run)
        if supplied.is_symlink():
            raise RuntimeError("EXPERIMENT_RUN_SYMLINK")
        target = self._run_path(supplied.name)
        if supplied != target or target.name not in registry["runs"]:
            raise RuntimeError("EXPERIMENT_RUN_UNREGISTERED_PATH")
        return target

    def _assert_consistent(self, registry: dict) -> None:
        self._assert_root_shape()
        if len(registry["runs"]) > MAX_RUNS:
            raise RuntimeError("EXPERIMENT_RUN_LIMIT")
        for name in registry["runs"]:
            run = self._run_path(name)
            if run.is_symlink():
                raise RuntimeError("EXPERIMENT_RUN_SYMLINK")
            if not run.is_dir():
                raise RuntimeError("EXPERIMENT_RUN_REGISTRY_DRIFT")
            self._read_manifest(run)

    def _allocated_bytes(self, root: Path) -> int:
        total = 0
        for directory, subdirs, files in os.walk(root, followlinks=False):
            path = Path(directory)
            if path.is_symlink():
                raise RuntimeError("EXPERIMENT_RUN_SYMLINK")
            total += os.lstat(path).st_blocks * 512
            for name in [*subdirs, *files]:
                entry = path / name
                if entry.is_symlink():
                    raise RuntimeError("EXPERIMENT_RUN_SYMLINK")
                if not entry.is_dir():
                    # Charge every directory entry: hard links cannot hide usage.
                    total += os.lstat(entry).st_blocks * 512
        return total


def require_training_run(run_dir: Path, local_runs: Path, *,
                         issue_budget: ExperimentRunBudget | None = None) -> None:
    """Enforce custody only for explicitly issue-owned learning experiments.

    ``local_runs`` is retained for call-site compatibility with the historical
    checkout-local guard. Ordinary operator runs are not location-scoped.
    """
    if issue_budget is None:
        return
    if not isinstance(issue_budget, ExperimentRunBudget):
        raise TypeError("EXPERIMENT_BUDGET_GUARD_INVALID")
    issue_budget.register(Path(run_dir).expanduser())
    issue_budget.assert_within_budget()
