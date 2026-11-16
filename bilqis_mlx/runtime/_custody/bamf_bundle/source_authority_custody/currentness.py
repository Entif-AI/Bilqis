"""Process-live currentness witness for the owner-selected C09 trust root."""
from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import stat

from . import (
    HOST_SYSTEM_SOURCE_AUTHORITY_ORIGIN,
    SOURCE_AUTHORITY_REGISTRY_FILE,
    _BINDING_INVALID,
    _MAX_REGISTRY_BYTES,
    _TRUST_ROOT_INVALID,
    _TRUST_ROOT_MISMATCH,
    _binding_parts,
    invalid,
    resolve_source_authority_registry,
)


_ISSUER = object()


def _stat_identity(info) -> tuple[int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _trust_root_snapshot(run_dir: Path, correction_frontier):
    """Stat the exact owner-selected C09 trust root without parsing it."""
    (origin_present, origin, record_present, _record,
     digest_present, _digest) = _binding_parts(correction_frontier)
    if origin_present:
        if (origin != HOST_SYSTEM_SOURCE_AUTHORITY_ORIGIN
                or not record_present or not digest_present):
            invalid(_BINDING_INVALID)
        from .._darwin_source_authority import open_host_source_authority_registry_fd
        fd = open_host_source_authority_registry_fd(max_bytes=_MAX_REGISTRY_BYTES)
        try:
            return (HOST_SYSTEM_SOURCE_AUTHORITY_ORIGIN, *_stat_identity(os.fstat(fd)))
        except OSError:
            invalid(_TRUST_ROOT_INVALID)
        finally:
            os.close(fd)
    if record_present != digest_present:
        invalid(_BINDING_INVALID)
    if not record_present:
        return None
    path = Path(run_dir) / SOURCE_AUTHORITY_REGISTRY_FILE
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        invalid(_TRUST_ROOT_INVALID)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode)
                or info.st_size <= 0 or info.st_size > _MAX_REGISTRY_BYTES):
            invalid(_TRUST_ROOT_INVALID)
        return ("PROVISIONED", *_stat_identity(info))
    except OSError:
        invalid(_TRUST_ROOT_INVALID)
    finally:
        os.close(fd)


@dataclass(frozen=True, init=False, eq=False)
class SourceAuthorityCurrentness:
    """Proof that the deeply resolved fixed C09 trust root has not changed."""

    registry_sha256: str | None
    _run_dir: Path = field(repr=False)
    _trust_root: object = field(repr=False)
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        invalid(_TRUST_ROOT_INVALID)


def bind_source_authority_currentness(run_dir: Path, correction_frontier, expected_registry):
    """Resolve C09 once under a stable owner-selected trust-root identity."""
    root = Path(run_dir).resolve()
    before = _trust_root_snapshot(root, correction_frontier)
    actual = resolve_source_authority_registry(root, correction_frontier)
    after = _trust_root_snapshot(root, correction_frontier)
    if before != after or actual != expected_registry:
        invalid(_TRUST_ROOT_MISMATCH)
    result = object.__new__(SourceAuthorityCurrentness)
    for name, value in (
        ("registry_sha256", None if actual is None else actual.digest),
        ("_run_dir", root),
        ("_trust_root", after),
        ("_issuance", _ISSUER),
    ):
        object.__setattr__(result, name, value)
    return result


def require_source_authority_currentness(
        witness, run_dir: Path, correction_frontier, expected_registry):
    """Reject live C09 trust-root drift without rebuilding the registry."""
    expected_digest = None if expected_registry is None else expected_registry.digest
    if (type(witness) is not SourceAuthorityCurrentness
            or getattr(witness, "_issuance", None) is not _ISSUER
            or witness._run_dir != Path(run_dir).resolve()
            or witness.registry_sha256 != expected_digest
            or _trust_root_snapshot(witness._run_dir, correction_frontier)
            != witness._trust_root):
        invalid(_TRUST_ROOT_MISMATCH)
    return expected_registry


__all__ = (
    "SourceAuthorityCurrentness",
    "bind_source_authority_currentness",
    "require_source_authority_currentness",
)
