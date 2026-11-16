"""Detach a one-shot CP05 worker from the long-lived control-plane service."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def launch_command_worker(
    *, store_root: Path, run_dir: Path, operation_id: str,
) -> int:
    """Return the child PID only after the worker process was created."""
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "bilqis_mlx.control_plane.command.worker",
            "--store-root",
            str(Path(store_root).expanduser().resolve()),
            "--run-dir",
            str(Path(run_dir).expanduser().resolve()),
            "--operation-id",
            operation_id,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
        env=os.environ.copy(),
    )
    return process.pid
