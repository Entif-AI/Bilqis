"""Low-level durable filesystem mechanics for CP05 operation facts."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
from uuid import uuid4

from .model import operation_directory_name
from ..transport import _invalid


REQUEST_BINDING_SCHEMA = "bilqis.bamf.control-plane.command-request-binding/v1"


def canonical_fact(payload: dict) -> bytes:
    try:
        return (json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n").encode("utf-8")
    except (TypeError, ValueError):
        _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")


def _require_safe_directory(path: Path) -> None:
    if path.is_symlink():
        _invalid("CONTROL_PLANE_COMMAND_STORE_UNSAFE")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    observed = path.stat(follow_symlinks=False)
    if not stat.S_ISDIR(observed.st_mode):
        _invalid("CONTROL_PLANE_COMMAND_STORE_UNSAFE")
    os.chmod(path, 0o700)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_immutable(path: Path, payload: dict) -> None:
    raw = canonical_fact(payload)
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != raw:
            _invalid("CONTROL_PLANE_COMMAND_FACT_DRIFT")
        return
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as stream:
            os.chmod(temporary, 0o600)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
        result[key] = value
    return result


def _nonfinite(_value):
    _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")


def read_json(path: Path) -> dict | None:
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file():
        _invalid("CONTROL_PLANE_COMMAND_STORE_UNSAFE")
    try:
        payload = json.loads(
            path.read_bytes(),
            object_pairs_hook=_pairs,
            parse_constant=_nonfinite,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
    if not isinstance(payload, dict):
        _invalid("CONTROL_PLANE_COMMAND_RECORD_INVALID")
    return payload


@contextmanager
def _file_lock(path: Path, *, nonblocking: bool = False):
    if path.is_symlink():
        _invalid("CONTROL_PLANE_COMMAND_STORE_UNSAFE")
    descriptor = os.open(
        path,
        os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.fchmod(descriptor, 0o600)
        operation = fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0)
        try:
            fcntl.flock(descriptor, operation)
        except BlockingIOError:
            _invalid("CONTROL_PLANE_COMMAND_WORKER_ALREADY_RUNNING")
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


class CommandStorage:
    """Safe directories, locks and immutable fact primitives."""

    def __init__(self, root: Path):
        requested = Path(root).expanduser()
        if requested.is_symlink():
            _invalid("CONTROL_PLANE_COMMAND_STORE_UNSAFE")
        self.root = requested.resolve()
        _require_safe_directory(self.root)
        self.requests_root = self.root / "request-index"
        _require_safe_directory(self.requests_root)

    def operation_dir(self, operation_id: str) -> Path:
        path = self.root / operation_directory_name(operation_id)
        _require_safe_directory(path)
        return path

    def submission_lock(self):
        return _file_lock(self.root / ".submission.lock")

    def operation_lock(self, operation_id: str):
        return _file_lock(self.operation_dir(operation_id) / ".lock")

    def execution_lock(self, operation_id: str):
        return _file_lock(
            self.operation_dir(operation_id) / ".worker.lock",
            nonblocking=True,
        )

    def bind_request_id(
        self, request_id: str, operation_id: str, semantic_sha256: str,
    ) -> None:
        digest = hashlib.sha256(request_id.encode("utf-8")).hexdigest()
        path = self.requests_root / f"{digest}.json"
        record = {
            "schema": REQUEST_BINDING_SCHEMA,
            "request_id": request_id,
            "operation_id": operation_id,
            "intent_sha256": semantic_sha256,
        }
        existing = read_json(path)
        if existing is not None and existing != record:
            _invalid("CONTROL_PLANE_COMMAND_REQUEST_ID_CONFLICT")
        write_immutable(path, record)

    def write_fact(self, operation_id: str, name: str, payload: dict) -> None:
        write_immutable(self.operation_dir(operation_id) / name, payload)

    def read_fact(self, operation_id: str, name: str) -> dict | None:
        return read_json(self.operation_dir(operation_id) / name)

    def stdout_path(self, operation_id: str) -> Path:
        return self.operation_dir(operation_id) / "stdout.log"

    def stderr_path(self, operation_id: str) -> Path:
        return self.operation_dir(operation_id) / "stderr.log"
