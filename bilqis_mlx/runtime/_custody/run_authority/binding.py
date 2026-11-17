"""Run-root binding and repeated currentness checks for native BAMF authority."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import json
from pathlib import Path
from typing import Iterator

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.paths import storage_root
from bilqis_mlx.runtime.bamf_bundle import inspect_accepted_generation
from bilqis_mlx.runtime.disk import atomic_text
from bilqis_mlx.runtime.experiment_runs import require_training_run

from .authority import RunAuthority
from .records import RunAuthorityBindingRecord

_BINDING_NAME = ".bamf-run-authority-manifest.json"
_LOCK_NAME = ".bamf-run-authority-manifest.lock"


def _invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.BAMF_RUN_AUTHORITY.INVALID, reason=reason)


def _binding_path(run_dir: Path) -> Path:
    return run_dir / _BINDING_NAME


@contextmanager
def _binding_lock(run_dir: Path) -> Iterator[None]:
    if run_dir.is_symlink() or not run_dir.is_dir():
        _invalid("BAMF_RUN_AUTHORITY_ROOT_INVALID")
    lock = run_dir / _LOCK_NAME
    if lock.is_symlink():
        _invalid("BAMF_RUN_AUTHORITY_CUSTODY_UNSAFE")
    with lock.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _read_binding(path: Path) -> RunAuthorityBindingRecord | None:
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file():
        _invalid("BAMF_RUN_AUTHORITY_CUSTODY_UNSAFE")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        return RunAuthorityBindingRecord.from_record(record)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as error:
        _invalid("BAMF_RUN_AUTHORITY_CUSTODY_INVALID")


@dataclass(frozen=True)
class NativeRunAuthorityBinding:
    """Process-live capability tied to one persisted run-authority receipt."""

    run_dir: Path
    authority: RunAuthority
    record: RunAuthorityBindingRecord

    def assert_current(self, *, now: float | None = None) -> None:
        current = self.authority.assert_current(
            self.run_dir, expected_run_id=self.record.run_id, now=now)
        if current.digest != self.record.authority.digest:
            _invalid("BAMF_RUN_AUTHORITY_RESUME_DRIFT")
        with _binding_lock(self.run_dir):
            persisted = _read_binding(_binding_path(self.run_dir))
            if persisted is None or persisted.digest != self.record.digest:
                _invalid("BAMF_RUN_AUTHORITY_CUSTODY_DRIFT")


def bind_native_run_authority(
        run_dir: Path, authority: RunAuthority | None, *, persist: bool = True,
        local_runs: Path | None = None,
        now: float | None = None) -> NativeRunAuthorityBinding | None:
    """Bind authority before source/GPU/neural work, or enforce local isolation."""
    run_dir = Path(run_dir).expanduser().resolve()
    path = _binding_path(run_dir)
    if authority is None:
        if path.exists() or path.is_symlink():
            _invalid("BAMF_RUN_AUTHORITY_REQUIRED")
        require_training_run(run_dir, storage_root() if local_runs is None else local_runs)
        return None
    if not isinstance(authority, RunAuthority):
        _invalid("BAMF_RUN_AUTHORITY_INVALID")
    inspection = inspect_accepted_generation(run_dir / "bamf-state.json")
    identity = authority.assert_current(
        run_dir, expected_run_id=inspection.run_id, now=now)
    record = RunAuthorityBindingRecord(
        inspection.run_id, inspection.run_identity_sha256, identity)
    with _binding_lock(run_dir):
        persisted = _read_binding(path)
        if persisted is not None and persisted.digest != record.digest:
            _invalid("BAMF_RUN_AUTHORITY_RESUME_DRIFT")
        if persisted is None and persist:
            atomic_text(path, json.dumps(record.to_record(), sort_keys=True) + "\n")
            persisted = _read_binding(path)
            if persisted is None or persisted.digest != record.digest:
                _invalid("BAMF_RUN_AUTHORITY_CUSTODY_DRIFT")
    binding = NativeRunAuthorityBinding(run_dir, authority, record)
    if persist:
        binding.assert_current(now=now)
    return binding
