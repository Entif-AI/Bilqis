"""CP01 Unix-socket ownership and request-handler mechanics."""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import socket
import socketserver
import stat

from bilqis_mlx.errors import ErrorBus, SCHOOL


MAX_REQUEST_BYTES = 64 * 1024
MAX_UNIX_SOCKET_PATH_BYTES = 100


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_CONTROL_PLANE.INVALID, reason=reason)


def _socket_identity(path: Path) -> tuple[int, int] | None:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISSOCK(observed.st_mode):
        return None
    return observed.st_dev, observed.st_ino


def _unlink_socket_if_identity(
        path: Path, identity: tuple[int, int] | None) -> bool:
    if identity is None or _socket_identity(path) != identity:
        return False
    path.unlink()
    return True


def _acquire_service_lock(socket_path: Path) -> int:
    lock_path = Path(f"{socket_path}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.is_symlink():
        _invalid("CONTROL_PLANE_SERVICE_LOCK_UNSAFE")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | nofollow, 0o600)
    except OSError:
        _invalid("CONTROL_PLANE_SERVICE_LOCK_UNSAFE")
    try:
        opened = os.fstat(fd)
        named = os.stat(lock_path, follow_symlinks=False)
        if (not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(named.st_mode)
                or (opened.st_dev, opened.st_ino)
                != (named.st_dev, named.st_ino)):
            _invalid("CONTROL_PLANE_SERVICE_LOCK_UNSAFE")
        os.fchmod(fd, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            _invalid("CONTROL_PLANE_SOCKET_ALREADY_ACTIVE")
        return fd
    except Exception:
        os.close(fd)
        raise


def _release_service_lock(fd: int | None) -> None:
    if fd is None:
        return
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)


def _prepare_socket_path(path: Path) -> None:
    if len(os.fsencode(str(path))) > MAX_UNIX_SOCKET_PATH_BYTES:
        _invalid("CONTROL_PLANE_SOCKET_PATH_TOO_LONG")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISSOCK(observed.st_mode):
        _invalid("CONTROL_PLANE_SOCKET_PATH_OCCUPIED")
    observed_identity = (observed.st_dev, observed.st_ino)
    probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        probe.settimeout(0.1)
        probe.connect(str(path))
    except (ConnectionRefusedError, FileNotFoundError):
        if _socket_identity(path) != observed_identity:
            _invalid("CONTROL_PLANE_SOCKET_CHANGED_DURING_STARTUP")
        _unlink_socket_if_identity(path, observed_identity)
        return
    finally:
        probe.close()
    _invalid("CONTROL_PLANE_SOCKET_ALREADY_ACTIVE")


class _ThreadedUnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


class _RequestHandler(socketserver.StreamRequestHandler):
    def _read_request(self) -> tuple[dict | None, str | None]:
        raw = self.rfile.readline(MAX_REQUEST_BYTES + 2)
        if not raw:
            return None, None
        if len(raw) > MAX_REQUEST_BYTES + 1:
            return None, "CONTROL_PLANE_REQUEST_TOO_LARGE"
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None, "CONTROL_PLANE_REQUEST_INVALID"
        if not isinstance(payload, dict):
            return None, "CONTROL_PLANE_REQUEST_INVALID"
        return payload, None

    def _write(self, payload: dict) -> None:
        self.wfile.write(json.dumps(
            payload, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n")
        self.wfile.flush()

    def handle(self) -> None:
        service = self.server.control_plane
        request, error = self._read_request()
        if error is not None:
            self._write(service.rejected_handshake(error))
            return
        if request is None:
            return
        response, session = service.handshake(request)
        self._write(response)
        if session is None:
            return
        while True:
            request, error = self._read_request()
            if request is None:
                if error is not None:
                    self._write(service.rejected_request(session, error))
                return
            if request.get("type") == "event-subscribe":
                service.stream_events(session, request, self._write)
                return
            self._write(service.dispatch(session, request))
