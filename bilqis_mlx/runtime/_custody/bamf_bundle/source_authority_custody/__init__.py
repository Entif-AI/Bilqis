"""Independent host custody for the C09 source-authority trust root."""
from __future__ import annotations

import contextlib
import fcntl
import json
import os
from pathlib import Path
import stat
from collections.abc import Mapping

from ..records import invalid


SOURCE_AUTHORITY_REGISTRY_FILE = "source-authority-registry.json"
SOURCE_AUTHORITY_REGISTRY_LOCK = ".source-authority-registry.lock"
_MAX_REGISTRY_BYTES = 256 * 1024
HOST_SYSTEM_SOURCE_AUTHORITY_ORIGIN = "HOST_SYSTEM_V1"

_BINDING_INVALID = "BAMF_C09_SOURCE_AUTHORITY_BINDING_INVALID"
_BINDING_REQUIRED = "BAMF_C09_SOURCE_AUTHORITY_BINDING_REQUIRED"
_TRUST_ROOT_INVALID = "BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_INVALID"
_TRUST_ROOT_MISMATCH = "BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_MISMATCH"


@contextlib.contextmanager
def source_authority_registry_lock(run_dir: Path):
    """Serialize the project-owned trust-root provisioner with authority leases."""
    from ..publication.storage import _require_run_root

    root = Path(run_dir)
    _require_run_root(root)
    path = root / SOURCE_AUTHORITY_REGISTRY_LOCK
    if path.is_symlink():
        invalid("BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_INVALID")
    fd = os.open(
        path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            invalid("BAMF_C09_SOURCE_AUTHORITY_WRITER_ACTIVE")
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _read_provisioned_source_authority_registry_unlocked(run_dir: Path):
    path = Path(run_dir) / SOURCE_AUTHORITY_REGISTRY_FILE
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        return None
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode)
                or info.st_size <= 0 or info.st_size > _MAX_REGISTRY_BYTES):
            invalid("BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_INVALID")
        raw = os.read(fd, info.st_size + 1)
        if len(raw) != info.st_size:
            invalid("BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_INVALID")
    except OSError:
        invalid("BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_INVALID")
    finally:
        os.close(fd)
    try:
        record = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        invalid("BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_INVALID")
    from bilqis_mlx.runtime.atlas_source_authority import SourceAuthorityRegistry
    return SourceAuthorityRegistry.from_record(record)


def read_provisioned_source_authority_registry(run_dir: Path):
    """Read trusted registry material provisioned outside generation publication."""
    with source_authority_registry_lock(run_dir):
        return _read_provisioned_source_authority_registry_unlocked(run_dir)


def _bind_host_source_authority_registry(run_dir: Path, correction_frontier):
    """Project an already-provisioned host trust root into accepted custody material.

    This never writes or selects registry material.  The only authority source is the
    host-owned file already present under ``run_dir``; callers can supply only the run
    root and the owner-derived correction frontier that will be bound to it.
    """
    if not isinstance(correction_frontier, dict):
        invalid("BAMF_C09_SOURCE_AUTHORITY_BINDING_INVALID")
    if (correction_frontier.get("source_authority_registry") is not None
            or correction_frontier.get("source_authority_registry_sha256") is not None):
        invalid("BAMF_C09_SOURCE_AUTHORITY_BINDING_INVALID")
    registry_path = Path(run_dir) / SOURCE_AUTHORITY_REGISTRY_FILE
    if not registry_path.exists() and not registry_path.is_symlink():
        return dict(correction_frontier)
    trusted = read_provisioned_source_authority_registry(run_dir)
    if trusted is None:
        return dict(correction_frontier)
    return {
        **correction_frontier,
        "source_authority_registry_sha256": trusted.digest,
        "source_authority_registry": trusted.to_record(),
    }


def read_host_system_source_authority_registry():
    """Read the one fixed account-scoped C09 root without a caller-selected path."""
    from .._darwin_source_authority import open_host_source_authority_registry_fd

    fd = open_host_source_authority_registry_fd(max_bytes=_MAX_REGISTRY_BYTES)
    try:
        info = os.fstat(fd)
        chunks = []
        remaining = info.st_size + 1
        while remaining:
            chunk = os.read(fd, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) != info.st_size:
            invalid(_TRUST_ROOT_INVALID)
    except OSError:
        invalid(_TRUST_ROOT_INVALID)
    finally:
        os.close(fd)
    try:
        record = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        invalid(_TRUST_ROOT_INVALID)
    from bilqis_mlx.runtime.atlas_source_authority import SourceAuthorityRegistry
    try:
        return SourceAuthorityRegistry.from_record(record)
    except Exception:
        invalid(_TRUST_ROOT_INVALID)


def _binding_parts(frontier: Mapping[str, object]):
    if not isinstance(frontier, Mapping):
        invalid(_BINDING_INVALID)
    origin_present = "source_authority_registry_origin" in frontier
    record_present = "source_authority_registry" in frontier
    digest_present = "source_authority_registry_sha256" in frontier
    origin = frontier.get("source_authority_registry_origin")
    record = frontier.get("source_authority_registry")
    digest = frontier.get("source_authority_registry_sha256")
    return origin_present, origin, record_present, record, digest_present, digest


def _registry_from_binding(record, digest):
    if record is None or not isinstance(digest, str):
        invalid(_BINDING_INVALID)
    from bilqis_mlx.runtime.atlas_source_authority import SourceAuthorityRegistry
    try:
        registry = SourceAuthorityRegistry.from_record(record)
    except Exception:
        invalid(_BINDING_INVALID)
    if registry.digest != digest:
        invalid(_BINDING_INVALID)
    return registry


def resolve_source_authority_registry(
        run_dir: Path, correction_frontier: Mapping[str, object]):
    """Resolve C09 from authenticated custody metadata, never caller branch selection."""
    (origin_present, origin, record_present, record,
     digest_present, digest) = _binding_parts(correction_frontier)
    if origin_present:
        if origin != HOST_SYSTEM_SOURCE_AUTHORITY_ORIGIN:
            invalid(_BINDING_INVALID)
        if not record_present or not digest_present:
            invalid(_BINDING_REQUIRED)
        candidate = _registry_from_binding(record, digest)
        trusted = read_host_system_source_authority_registry()
        if candidate != trusted or candidate.digest != trusted.digest:
            invalid(_TRUST_ROOT_MISMATCH)
        return trusted
    if record_present != digest_present:
        invalid(_BINDING_INVALID)
    if not record_present:
        return None
    if record is None or digest is None:
        invalid(_BINDING_INVALID)
    with source_authority_registry_lock(run_dir):
        return _require_provisioned_source_authority_registry_unlocked(
            run_dir, correction_frontier)


def require_source_authority_successor_inheritance(
        run_dir: Path,
        parent_frontier: Mapping[str, object],
        candidate_frontier: Mapping[str, object],
        *,
        allow_historical_anchor: bool,
):
    """Verify one successor against the authenticated parent's exact C09 branch."""
    if type(allow_historical_anchor) is not bool:
        invalid(_BINDING_INVALID)
    parent = _binding_parts(parent_frontier)
    candidate = _binding_parts(candidate_frontier)
    p_origin_present, p_origin, p_record_present, p_record, p_digest_present, p_digest = parent
    c_origin_present, c_origin, c_record_present, c_record, c_digest_present, c_digest = candidate

    if p_origin_present:
        if (p_origin != HOST_SYSTEM_SOURCE_AUTHORITY_ORIGIN
                or not p_record_present or not p_digest_present
                or not c_origin_present or c_origin != p_origin
                or not c_record_present or not c_digest_present
                or c_record != p_record or c_digest != p_digest):
            invalid(_BINDING_INVALID)
        return resolve_source_authority_registry(run_dir, candidate_frontier)

    if p_record_present != p_digest_present:
        invalid(_BINDING_INVALID)
    if p_record_present:
        if p_record is None or p_digest is None:
            invalid(_BINDING_INVALID)
        if (c_origin_present or not c_record_present or not c_digest_present
                or c_record != p_record or c_digest != p_digest):
            invalid(_BINDING_INVALID)
        return resolve_source_authority_registry(run_dir, candidate_frontier)

    if c_origin_present:
        invalid(_BINDING_INVALID)
    if not c_record_present and not c_digest_present:
        return None
    if (not allow_historical_anchor or not c_record_present or not c_digest_present
            or c_record is None or c_digest is None):
        invalid(_BINDING_INVALID)
    return resolve_source_authority_registry(run_dir, candidate_frontier)


def require_provisioned_source_authority_registry(
        run_dir: Path, correction_frontier):
    """Bind candidate/live C09 material to an independent host-provisioned root."""
    with source_authority_registry_lock(run_dir):
        return _require_provisioned_source_authority_registry_unlocked(
            run_dir, correction_frontier)


def _require_provisioned_source_authority_registry_unlocked(
        run_dir: Path, correction_frontier):
    trusted = _read_provisioned_source_authority_registry_unlocked(run_dir)
    record = correction_frontier.get("source_authority_registry")
    digest = correction_frontier.get("source_authority_registry_sha256")
    if trusted is None:
        if record is not None or digest is not None:
            invalid("BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_REQUIRED")
        return None
    if record is None or digest is None:
        invalid("BAMF_C09_SOURCE_AUTHORITY_BINDING_REQUIRED")
    from bilqis_mlx.runtime.atlas_source_authority import SourceAuthorityRegistry
    candidate = SourceAuthorityRegistry.from_record(record)
    if candidate.digest != digest or candidate != trusted:
        invalid("BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_MISMATCH")
    return trusted


from .currentness import (
    SourceAuthorityCurrentness,
    bind_source_authority_currentness,
    require_source_authority_currentness,
)


__all__ = (
    "HOST_SYSTEM_SOURCE_AUTHORITY_ORIGIN",
    "SOURCE_AUTHORITY_REGISTRY_FILE",
    "SOURCE_AUTHORITY_REGISTRY_LOCK",
    "SourceAuthorityCurrentness",
    "_require_provisioned_source_authority_registry_unlocked",
    "bind_source_authority_currentness",
    "read_host_system_source_authority_registry",
    "read_provisioned_source_authority_registry",
    "require_source_authority_successor_inheritance",
    "require_provisioned_source_authority_registry",
    "require_source_authority_currentness",
    "resolve_source_authority_registry",
    "source_authority_registry_lock",
)
