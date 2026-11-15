"""A03 source-release frame-schema body witnesses.

The issuer freezes the existing FrameSchema bodies and SchemaTagMap; it does
not define a second schema registry. A consumer must load the frozen bytes
against the digest supplied by the accepted A03 release, never a digest
invented alongside an untrusted candidate schema.
"""
from __future__ import annotations

from ._public_identity.module_identity import restore_public_module as _restore_public_module

from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
from pathlib import Path
import re

from ..errors import BilqisError, ErrorBus, SEMANTIC_FRAME
from .atlas_projection import FrozenAtlasSnapshot
from .atlas.snapshot import AtlasArtifactSelection, load_pinned_atlas_snapshot
from .frame_codec import (
    SchemaTagEntry, SchemaTagMap, _canonical_bytes,
)
from .frame_schema import FrameSchema, frame_schema_from_bytes

from ._released_schemas.contracts import (
    _fail, _sha, _unique_pairs,
    _json, MANIFEST_SCHEMA, BODY_SCHEMA,
    WITNESS_SCHEMA, SOURCE_PIN_REGISTRY_SCHEMA, SOURCE_PIN_REGISTRY_SHA256,
    SOURCE_PIN_STATUS, _SHA,
)
from ._released_schemas.models import (
    ReleasedSchemaBody, ReleasedFrameSchemaManifest, ReleasedSchemaBodyWitness,
    VerifiedReleasedFrameSchemas,
)
from ._released_schemas.io import (
    seal_released_frame_schemas, load_released_frame_schemas, persist_released_frame_schemas,
)
from ._released_schemas.pins import (
    _source_pins, _load_pinned_released_frame_schemas,
    _load_pinned_released_frame_schemas_from_snapshot, lookup_source_pinned_frame_schema,
    verify_source_pinned_frame_schema, verify_source_pinned_frame_schema_bytes,
)




# Preserve canonical identities for released-schema public contracts.
for _public in (
    _fail, _sha, _unique_pairs,
    _json, ReleasedSchemaBody, ReleasedFrameSchemaManifest,
    ReleasedSchemaBodyWitness, VerifiedReleasedFrameSchemas, seal_released_frame_schemas,
    load_released_frame_schemas, persist_released_frame_schemas, _source_pins,
    _load_pinned_released_frame_schemas, _load_pinned_released_frame_schemas_from_snapshot,
    lookup_source_pinned_frame_schema, verify_source_pinned_frame_schema,
    verify_source_pinned_frame_schema_bytes,
):
    _restore_public_module(_public, __name__)
