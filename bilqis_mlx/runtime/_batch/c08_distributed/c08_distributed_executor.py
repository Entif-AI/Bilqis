"""Coordinator-owned launcher for one bounded MLX distributed C08 step."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from importlib.metadata import version
import math
import os
from pathlib import Path
import pickle
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory

from bilqis_mlx.runtime.atlas_resources import (
    DistributedExecutionProfile, DistributedRank, require_distributed_backend,
)

from .c08_distributed_outcome import DistributedStepOutcome
from .c08_distributed_capsule import issue_distributed_factory_step_capsule
from .c08_gradient_accumulation import _invalid
from .c08_oom import mlx_oom_message


_ISSUER = object()
_WORKER_MODULE = (
    "bilqis_mlx.runtime._batch.c08_distributed.c08_distributed_worker")
_WORKER_SCRIPT = (
    "bilqis_mlx/runtime/_batch/c08_distributed/c08_distributed_worker.py")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_bytes(path: Path, payload: bytes) -> None:
    with path.open("wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _terminate_cohort(process: subprocess.Popen) -> None:
    """Terminate the launcher and every rank/ssh child in its owned session."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.communicate(timeout=5.0)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()


@dataclass(frozen=True, init=False)
class DistributedExecutorBinding:
    """One coordinator-launched worker cohort; never an optimizer/publication owner."""
    profile: DistributedExecutionProfile
    hosts: tuple[str, ...]
    python_executable: str
    working_directory: str
    worker_timeout_seconds: float
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("C08_DISTRIBUTED_EXECUTOR_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self) -> None:
        world_size = len(self.profile.workers)
        if (getattr(self, "_issuance", None) is not _ISSUER
                or type(self.profile) is not DistributedExecutionProfile
                or type(self.hosts) is not tuple or not self.hosts
                or len(self.hosts) not in (1, world_size)
                or self.hosts[0] != "127.0.0.1"
                or any(not isinstance(host, str) or not host for host in self.hosts)
                or not isinstance(self.python_executable, str)
                or not self.python_executable
                or not isinstance(self.working_directory, str)
                or not self.working_directory
                or not isinstance(self.worker_timeout_seconds, (int, float))
                or isinstance(self.worker_timeout_seconds, bool)
                or not math.isfinite(self.worker_timeout_seconds)
                or self.worker_timeout_seconds <= 0):
            _invalid("C08_DISTRIBUTED_EXECUTOR_BINDING_INVALID")
        self.profile.__post_init__()

    def _command(self, request: Path, response: Path, digest: str) -> list[str]:
        command = [
            "mlx.launch", "--backend", self.profile.backend,
            "--hosts", ",".join(self.hosts),
            "--env", f"BILQIS_C08_BACKEND={self.profile.backend}",
        ]
        if len(self.hosts) == 1:
            command.extend(("-n", str(len(self.profile.workers))))
        command.extend((
            "--cwd", self.working_directory,
            "--python", self.python_executable, _WORKER_SCRIPT,
            "--request", str(request), "--response", str(response),
            "--request-sha256", digest,
        ))
        return command

    def _run_capsule(self, capsule) -> object:
        """Run one digest-bound capsule through the production worker cohort."""
        self.__post_init__()
        try:
            payload = pickle.dumps(capsule, protocol=5)
        except (pickle.PickleError, TypeError, AttributeError):
            _invalid("C08_DISTRIBUTED_EXECUTION_CAPSULE_INVALID")
        digest = _sha256(payload)
        with TemporaryDirectory(prefix="bilqis-c08-distributed-") as root_value:
            root = Path(root_value)
            request = root / "request.pkl"
            response = root / "response.pkl"
            response_digest = root / "response.sha256"
            _write_bytes(request, payload)
            process = subprocess.Popen(
                self._command(request, response, digest),
                cwd=self.working_directory,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                start_new_session=True)
            try:
                stdout, stderr = process.communicate(
                    timeout=self.worker_timeout_seconds)
            except subprocess.TimeoutExpired:
                _terminate_cohort(process)
                _invalid("C08_DISTRIBUTED_WORKER_COHORT_TIMEOUT")
            if process.returncode != 0:
                oom = mlx_oom_message(
                    "\n".join((stderr or "", stdout or "")))
                if oom is not None:
                    raise RuntimeError(oom)
                _invalid("C08_DISTRIBUTED_WORKER_COHORT_FAILED")
            if not response.is_file() or not response_digest.is_file():
                _invalid("C08_DISTRIBUTED_WORKER_RESPONSE_MISSING")
            response_payload = response.read_bytes()
            if response_digest.read_text().strip() != _sha256(response_payload):
                _invalid("C08_DISTRIBUTED_WORKER_RESPONSE_DIGEST_DRIFT")
            try:
                outcome = pickle.loads(response_payload)
            except (pickle.PickleError, EOFError, TypeError, AttributeError):
                _invalid("C08_DISTRIBUTED_WORKER_RESPONSE_INVALID")
        return outcome

    def execute(self, **kwargs) -> DistributedStepOutcome:
        """Launch C08-only ranks; return rank-0 outcome to the sovereign coordinator."""
        request = issue_distributed_factory_step_capsule(**kwargs)
        outcome = self._run_capsule({"kind": "factory-step", "request": request})
        if type(outcome) is not DistributedStepOutcome:
            _invalid("C08_DISTRIBUTED_WORKER_RESPONSE_INVALID")
        outcome.__post_init__()
        return outcome

    def probe(self) -> dict:
        """Exercise this exact launcher/worker topology without BAMF mutation."""
        outcome = self._run_capsule({"kind": "collective-probe"})
        expected_ranks = tuple(range(len(self.profile.workers)))
        expected_sum = sum(rank + 1 for rank in expected_ranks)
        if (not isinstance(outcome, dict)
                or outcome.get("schema") != "bilqis.c08.worker-cohort-probe/v1"
                or tuple(outcome.get("ranks", ())) != expected_ranks
                or outcome.get("world_size") != len(self.profile.workers)
                or outcome.get("sum") != float(expected_sum)):
            _invalid("C08_DISTRIBUTED_WORKER_PROBE_INVALID")
        return outcome


def configure_mlx_distributed_execution(
        workers: tuple[DistributedRank, ...], *, hosts: tuple[str, ...],
        partition_seed: int, backend: str, python_executable: str | None = None,
        working_directory: str | Path | None = None,
        worker_timeout_seconds: float = 900.0) -> DistributedExecutorBinding:
    """Bind a cohort with coordinator-local rank 0 and identical remote code paths."""
    normalized = require_distributed_backend(backend)
    profile = DistributedExecutionProfile(
        partition_seed=partition_seed, workers=workers,
        mlx_version=version("mlx"), backend=normalized,
        numeric_precision="fp32", reduction_policy="fp32_weighted_mean")
    binding = object.__new__(DistributedExecutorBinding)
    for name, value in (
            ("profile", profile), ("hosts", tuple(hosts)),
            ("python_executable", python_executable or sys.executable),
            ("working_directory", str(
                Path(working_directory or Path.cwd()).resolve())),
            ("worker_timeout_seconds", float(worker_timeout_seconds)),
            ("_issuance", _ISSUER)):
        object.__setattr__(binding, name, value)
    binding.__post_init__()
    return binding


__all__ = ("DistributedExecutorBinding", "configure_mlx_distributed_execution")
