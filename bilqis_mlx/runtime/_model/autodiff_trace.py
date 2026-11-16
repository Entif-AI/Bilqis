"""Process-local policy for deferring host-visible tensor validation in MLX traces."""
from contextlib import contextmanager
from contextvars import ContextVar


_DEFER_HOST_VALIDATION = ContextVar("bamf_defer_host_tensor_validation", default=False)


def host_tensor_validation_enabled() -> bool:
    """Return whether validation may synchronize MLX tensors to Python now."""
    return not _DEFER_HOST_VALIDATION.get()


@contextmanager
def defer_host_tensor_validation():
    """Keep structural checks, but move tensor-value validation past autodiff."""
    token = _DEFER_HOST_VALIDATION.set(True)
    try:
        yield
    finally:
        _DEFER_HOST_VALIDATION.reset(token)


__all__ = ("defer_host_tensor_validation", "host_tensor_validation_enabled")
