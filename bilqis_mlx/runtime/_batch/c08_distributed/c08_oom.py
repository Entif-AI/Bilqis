"""Shared MLX allocator failure classification for local and worker C08 paths."""
from __future__ import annotations

import re


_ALLOCATOR_OOM = re.compile(r"\[malloc\] Unable to allocate [0-9]+ bytes\.")
_METAL_PREFIX = "[METAL] Command buffer execution failed: "
_METAL_OOM_CODE = "kIOGPUCommandBufferCallbackErrorOutOfMemory"


def mlx_oom_message(value) -> str | None:
    """Return the exact retryable MLX OOM line, never a generic worker failure."""
    text = str(value)
    for line in text.splitlines():
        message = line.strip()
        if (_ALLOCATOR_OOM.fullmatch(message) is not None
                or (message.startswith(_METAL_PREFIX)
                    and _METAL_OOM_CODE in message)):
            return message
    return None


def is_mlx_oom(value) -> bool:
    return mlx_oom_message(value) is not None


__all__ = ("is_mlx_oom", "mlx_oom_message")
