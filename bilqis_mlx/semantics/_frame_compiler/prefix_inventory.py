"""A05 identity for the complete compiled source-prefix inventory."""
from __future__ import annotations

import hashlib
import json

from .._public_identity.facade_dependency import public_facade as _public_facade
from .batch import CompiledFrameBatch


def _public():
    return _public_facade("bilqis_mlx.semantics.frame_compiler")

PREFIX_INVENTORY_SCHEMA = "bilqis.mlx.refinement-prefix-inventory/v1"


def prefix_inventory_handle(source_id: str, prediction_boundary: int) -> str:
    if (not isinstance(source_id, str) or not source_id
            or type(prediction_boundary) is not int or prediction_boundary < 0):
        _public()._invalid("BAMF_PREFIX_INVENTORY_HANDLE_INVALID")
    return f"source:refinement-prefix:{source_id}:{prediction_boundary}"


def prefix_inventory_evidence_digest(compiled: CompiledFrameBatch) -> str:
    """Bind the complete p-local A05 closure inventory and compiler identity."""
    if type(compiled) is not CompiledFrameBatch:
        _public()._invalid("BAMF_PREFIX_INVENTORY_EVIDENCE_INVALID")
    compiled.__post_init__()
    payload = json.dumps({
        "schema": PREFIX_INVENTORY_SCHEMA,
        "source_instance_id": compiled.source_instance_id,
        "prediction_boundary": compiled.visible_end,
        "semantic_release": compiled.semantic_release,
        "compiled_cache_key": compiled.cache_key,
        "context_digest": compiled.context_digest,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256((payload + "\n").encode("utf-8")).hexdigest()
