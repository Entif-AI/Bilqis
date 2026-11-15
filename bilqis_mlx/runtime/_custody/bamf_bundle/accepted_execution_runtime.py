"""Compatibility imports for the canonical accepted execution-cache owner."""
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest

from .accepted_execution_cache import (
    _require_owned_execution_cache,
    _reset_execution_cache_owner_for_tests,
    bind_accepted_execution_cache,
    load_accepted_generation,
)
from .accepted_runtime import _accepted_correction_registry


__all__ = (
    "_accepted_correction_registry",
    "_require_owned_execution_cache",
    "_reset_execution_cache_owner_for_tests",
    "bind_accepted_execution_cache",
    "execution_generation_digest",
    "load_accepted_generation",
)
