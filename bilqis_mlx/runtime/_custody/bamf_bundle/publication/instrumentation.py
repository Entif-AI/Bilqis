"""Disposable B13 publication IO counters; never custody authority."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class PublicationMetrics:
    parent_bundle_loads: int
    child_bundle_loads: int
    tensor_bytes_read: int
    write_bytes: int
    fsync_bytes: int

    def to_record(self) -> dict:
        return {
            "parent_bundle_loads": self.parent_bundle_loads,
            "child_bundle_loads": self.child_bundle_loads,
            "tensor_bytes_read": self.tensor_bytes_read,
            "write_bytes": self.write_bytes,
            "fsync_bytes": self.fsync_bytes,
        }


@dataclass
class _MutablePublicationMetrics:
    parent_bundle_loads: int = 0
    child_bundle_loads: int = 0
    tensor_bytes_read: int = 0
    write_bytes: int = 0
    fsync_bytes: int = 0

    def freeze(self) -> PublicationMetrics:
        return PublicationMetrics(
            self.parent_bundle_loads, self.child_bundle_loads,
            self.tensor_bytes_read, self.write_bytes, self.fsync_bytes)


_ACTIVE = ContextVar("bamf_publication_metrics", default=None)
_LOAD_ROLE = ContextVar("bamf_publication_load_role", default=None)


@contextmanager
def publication_measurement(observer=None):
    existing = _ACTIVE.get()
    if existing is not None:
        yield existing
        return
    metrics = _MutablePublicationMetrics()
    token = _ACTIVE.set(metrics)
    try:
        yield metrics
    except BaseException:
        raise
    else:
        if observer is not None:
            try:
                observer(metrics.freeze())
            except Exception:
                pass
    finally:
        _ACTIVE.reset(token)


@contextmanager
def publication_bundle_load(role: str):
    token = _LOAD_ROLE.set(role)
    try:
        yield
    finally:
        _LOAD_ROLE.reset(token)


def note_bundle_load(manifest: dict) -> None:
    metrics = _ACTIVE.get()
    role = _LOAD_ROLE.get()
    if metrics is None or role not in {"parent", "child"}:
        return
    if role == "parent":
        metrics.parent_bundle_loads += 1
    else:
        metrics.child_bundle_loads += 1
    tensor = manifest.get("tensors") if isinstance(manifest, dict) else None
    size = tensor.get("uncompressed_bytes") if isinstance(tensor, dict) else None
    if type(size) is int and size >= 0:
        metrics.tensor_bytes_read += size


def note_write(size: int) -> None:
    metrics = _ACTIVE.get()
    if metrics is not None and type(size) is int and size >= 0:
        metrics.write_bytes += size


def note_fsync(size: int) -> None:
    metrics = _ACTIVE.get()
    if metrics is not None and type(size) is int and size >= 0:
        metrics.fsync_bytes += size


__all__ = ("PublicationMetrics", "publication_measurement")
