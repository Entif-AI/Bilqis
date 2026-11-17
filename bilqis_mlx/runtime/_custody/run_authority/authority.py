"""Live typed authority capability over existing experiment-run budget custody."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import time

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.bamf_bundle.records import canonical, sha
from bilqis_mlx.runtime.experiment_runs import ExperimentRunBudget, MAX_RUNS

from .records import RunAuthorityIdentity


def _invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.BAMF_RUN_AUTHORITY.INVALID, reason=reason)


class RunAuthority(ABC):
    """Runtime capability consumed by native BAMF without knowing its backend."""

    @property
    @abstractmethod
    def identity(self) -> RunAuthorityIdentity:
        raise NotImplementedError

    @abstractmethod
    def assert_current(self, run_dir: Path, *, expected_run_id: str,
                       now: float | None = None) -> RunAuthorityIdentity:
        raise NotImplementedError


def _policy_epoch(owner: ExperimentRunBudget) -> str:
    return sha(canonical({
        "schema": "bilqis.mlx.experiment-run-budget-policy/v1",
        "issue_number": owner.issue_number,
        "max_runs": MAX_RUNS,
        "max_bytes": owner.max_bytes,
        "reserve_bytes": owner.reserve_bytes,
    }))


def _identity(owner: ExperimentRunBudget, run_dir: Path, run_id: str, *,
              owner_identity: str, expires_at_unix_seconds: int | None) -> RunAuthorityIdentity:
    manifest = owner.register(run_dir)
    report = owner.assert_within_budget()
    policy_epoch = _policy_epoch(owner)
    custody = sha(canonical({
        "schema": "bilqis.mlx.experiment-run-custody-identity/v1",
        "owner_identity": owner_identity,
        "policy_epoch_sha256": policy_epoch,
        "manifest": manifest,
    }))
    return RunAuthorityIdentity.issue(
        run_id=run_id, owner_identity=owner_identity,
        policy_epoch_sha256=policy_epoch,
        collective_max_bytes=report["max_bytes"],
        local_max_bytes=report["max_bytes"] - report["reserve_bytes"],
        custody_sha256=custody,
        expires_at_unix_seconds=expires_at_unix_seconds)


class ExperimentRunAuthority(RunAuthority):
    """Compatibility adapter from ADR-077 experiment custody to R17 authority."""

    def __init__(self, owner: ExperimentRunBudget, run_dir: Path, run_id: str, *,
                 owner_identity: str,
                 expires_at_unix_seconds: int | None = None) -> None:
        if not isinstance(owner, ExperimentRunBudget):
            _invalid("BAMF_RUN_AUTHORITY_OWNER_INVALID")
        self._owner = owner
        supplied = Path(run_dir).expanduser()
        self._owner_run_dir = owner.root / supplied.name
        if supplied.resolve() != self._owner_run_dir.resolve():
            _invalid("BAMF_RUN_AUTHORITY_TARGET_DRIFT")
        self._run_dir = supplied.resolve()
        self._owner_identity = owner_identity
        self._expires_at = expires_at_unix_seconds
        self._identity = _identity(
            owner, self._owner_run_dir, run_id, owner_identity=owner_identity,
            expires_at_unix_seconds=expires_at_unix_seconds)

    @property
    def identity(self) -> RunAuthorityIdentity:
        return self._identity

    def assert_current(self, run_dir: Path, *, expected_run_id: str,
                       now: float | None = None) -> RunAuthorityIdentity:
        target = Path(run_dir).expanduser().resolve()
        if target != self._run_dir or expected_run_id != self._identity.run_id:
            _invalid("BAMF_RUN_AUTHORITY_TARGET_DRIFT")
        instant = time.time() if now is None else now
        if (self._expires_at is not None and instant >= self._expires_at):
            _invalid("BAMF_RUN_AUTHORITY_EXPIRED")
        current = _identity(
            self._owner, self._owner_run_dir, expected_run_id,
            owner_identity=self._owner_identity,
            expires_at_unix_seconds=self._expires_at)
        if current.digest != self._identity.digest:
            _invalid("BAMF_RUN_AUTHORITY_CUSTODY_DRIFT")
        return current


def issue_experiment_run_authority(
        owner: ExperimentRunBudget, run_dir: Path, run_id: str, *,
        owner_identity: str | None = None,
        expires_at_unix_seconds: int | None = None) -> ExperimentRunAuthority:
    """Adapt the still-authoritative ADR-077 owner behind the generic R17 type."""
    identity = owner_identity or f"github:Entif-AI/Bilqis-MLX#{owner.issue_number}"
    return ExperimentRunAuthority(
        owner, run_dir, run_id, owner_identity=identity,
        expires_at_unix_seconds=expires_at_unix_seconds)
