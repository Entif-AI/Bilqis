"""Local discovery records joining CLI operators to Admin Main Frame CP01."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
from uuid import uuid4

from bilqis_mlx._data_plane.contracts import default_path as data_plane_path
from bilqis_mlx.errors import ErrorBus, SCHOOL


SCHEMA = "bilqis.bamf.control-plane.active-endpoint/v1"
_DIRECTORY = "active-control-planes"


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID, reason=reason)


@dataclass(frozen=True)
class ActiveControlPlaneEndpoint:
    run_dir: Path
    socket_path: Path
    pid: int
    role: str


def default_socket_path(run_dir: Path) -> Path:
    run_dir = Path(run_dir).expanduser().resolve()
    return run_dir.parent / f".{run_dir.name}.control-plane.sock"


def _registry_root() -> Path:
    configured = os.environ.get("BILQIS_ACTIVE_CONTROL_PLANE_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return data_plane_path().parent / _DIRECTORY


def _prepare_registry_root() -> Path:
    root = _registry_root()
    if root.is_symlink():
        _invalid("CONTROL_PLANE_ACTIVE_ENDPOINT_ROOT_UNSAFE")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    observed = root.stat(follow_symlinks=False)
    if not stat.S_ISDIR(observed.st_mode):
        _invalid("CONTROL_PLANE_ACTIVE_ENDPOINT_ROOT_UNSAFE")
    os.chmod(root, 0o700)
    return root


def _pid_live(pid: int) -> bool:
    if type(pid) is not int or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _decode_endpoint(path: Path) -> ActiveControlPlaneEndpoint | None:
    try:
        observed = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(observed.st_mode) or path.is_symlink():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return None
    pid, role = payload.get("pid"), payload.get("role")
    run_raw, socket_raw = payload.get("run_dir"), payload.get("socket_path")
    if (not _pid_live(pid) or role not in {"operator", "service"}
            or not isinstance(run_raw, str) or not run_raw
            or not isinstance(socket_raw, str) or not socket_raw):
        return None
    run_dir, socket_path = Path(run_raw), Path(socket_raw)
    if not run_dir.is_absolute() or not socket_path.is_absolute():
        return None
    return ActiveControlPlaneEndpoint(
        run_dir.resolve(), socket_path.resolve(), pid, role)


def discover_active_endpoint(*, run_dir: Path | None = None) -> ActiveControlPlaneEndpoint | None:
    """Return one unambiguous live run/socket target, never guess across runs."""
    root = _registry_root()
    if not root.exists() or root.is_symlink() or not root.is_dir():
        return None
    requested = Path(run_dir).expanduser().resolve() if run_dir is not None else None
    endpoints: list[ActiveControlPlaneEndpoint] = []
    for path in root.glob("*.json"):
        endpoint = _decode_endpoint(path)
        if endpoint is None or (requested is not None and endpoint.run_dir != requested):
            continue
        endpoints.append(endpoint)
    operators = [item for item in endpoints if item.role == "operator"]
    candidates = operators if operators else endpoints
    grouped: dict[tuple[Path, Path], list[ActiveControlPlaneEndpoint]] = {}
    for endpoint in candidates:
        grouped.setdefault((endpoint.run_dir, endpoint.socket_path), []).append(endpoint)
    if len(grouped) != 1:
        return None
    endpoints = next(iter(grouped.values()))
    return next((item for item in endpoints if item.role == "service"), endpoints[0])


@contextmanager
def advertise_active_endpoint(
        run_dir: Path, *, socket_path: Path | None = None, role: str = "operator"):
    if role not in {"operator", "service"}:
        _invalid("CONTROL_PLANE_ACTIVE_ENDPOINT_ROLE_INVALID")
    run_dir = Path(run_dir).expanduser().resolve()
    socket_path = (default_socket_path(run_dir) if socket_path is None
                   else Path(socket_path).expanduser().resolve())
    root = _prepare_registry_root()
    pid = os.getpid()
    target = root / f"{pid}-{role}.json"
    if target.is_symlink():
        _invalid("CONTROL_PLANE_ACTIVE_ENDPOINT_PATH_UNSAFE")
    payload = json.dumps({
        "schema": SCHEMA,
        "pid": pid,
        "role": role,
        "run_dir": str(run_dir),
        "socket_path": str(socket_path),
    }, sort_keys=True, separators=(",", ":")) + "\n"
    temporary = root / f".{target.name}.{uuid4().hex}.tmp"
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        yield ActiveControlPlaneEndpoint(run_dir, socket_path, pid, role)
    finally:
        try:
            if target.is_file() and not target.is_symlink() and target.read_text(encoding="utf-8") == payload:
                target.unlink()
        except OSError:
            pass
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


__all__ = (
    "ActiveControlPlaneEndpoint", "advertise_active_endpoint",
    "default_socket_path", "discover_active_endpoint",
)
