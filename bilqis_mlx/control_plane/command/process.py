"""Fail-closed trainer process launch and identity custody."""
from __future__ import annotations

import hashlib
from pathlib import Path
import signal
import subprocess
import sys

from bilqis_mlx.errors import BilqisError


def process_identity_sha256(pid: int) -> str | None:
    try:
        completed = subprocess.run(
            ["ps", "-p", str(pid), "-o", "lstart=,command="],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            text=False,
        )
    except OSError:
        return None
    identity = completed.stdout.strip()
    if completed.returncode != 0 or not identity:
        return None
    return hashlib.sha256(identity).hexdigest()


def run_trainer(
    *, argv, stdout_path: Path, stderr_path: Path, store, operation_id: str,
    identity_resolver=process_identity_sha256,
) -> tuple[int | None, str | None]:
    try:
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            process = subprocess.Popen(
                [sys.executable, "-m", "bilqis_mlx.cli", *argv],
                stdout=stdout,
                stderr=stderr,
            )
            try:
                if store is not None:
                    identity_sha256 = identity_resolver(process.pid)
                    if identity_sha256 is None:
                        raise RuntimeError
                    store.write_trainer_process(
                        operation_id,
                        pid=process.pid,
                        identity_sha256=identity_sha256,
                    )
            except (BilqisError, OSError, RuntimeError) as error:
                process.send_signal(signal.SIGINT)
                process.wait()
                digest = hashlib.sha256(
                    f"{type(error).__name__}:{error}".encode("utf-8")
                ).hexdigest()
                return None, f"command-error:custody:{digest}"
            returncode = process.wait()
    except OSError as error:
        digest = hashlib.sha256(
            f"{type(error).__name__}:{error}".encode("utf-8")
        ).hexdigest()
        return None, f"command-error:spawn:{digest}"
    if returncode != 0:
        digest = hashlib.sha256(stderr_path.read_bytes()).hexdigest()
        return returncode, f"command-error:{returncode}:{digest}"
    return 0, None
