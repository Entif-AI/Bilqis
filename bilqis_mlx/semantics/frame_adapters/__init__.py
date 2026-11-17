"""Registered source frame adapters and public formal admission."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Callable
from ...errors import ErrorBus, SEMANTIC_FRAME
from ...factory.adapters import RegisteredSourceAdapter
from ...generated_assessment import digest
from ..source_numeric_decode import decode as decode_numeric
from ..source_structure import inspect_source_query
from ..atlas_projection import FrozenAtlasSnapshot
from ..context_eligibility import PUBLIC_FORMAL, ApprovedContextProjection, ContextEligibility, ContextHold, ContextMember, ContextPolicy, SourceFrontier, SourceGrant, TaskScope, frame_evidence_digest, member_evidence_digest, project_context
from ..core import Apply, Literal, Signature
from ..numeric import CONTRACT as NUMERIC_CONTRACT
from ..frame_schema import ChildFrameRef, ConceptRef, FrameInstance, FrameSchema, FrameTree, RoleOccurrence, RoleSpec, SourceSpan, ast_construct_id, atomic_fallback, bind_frame_instance, occurrence_id, validate_frame_tree
from .common import (
    MICRO_PREDICATE_ADAPTER,
    BOOLEAN_CONNECTIVE_ADAPTER,
    BOOLEAN_COMPOSITE_ADAPTER,
    BOOLEAN_IDENTIFICATION_ADAPTER,
    C13_EPISODE_ADAPTER,
    FINITE_NUMERIC_ADAPTER,
    PUBLIC_FORMAL_TIMELESS_EPOCH,
    MAX_PUBLIC_FORMAL_DRAW_EACH,
    _SHA256,
    _APPEND_ONLY_NUMERIC_NODES,
    _adapter_fail,
    _source_id,
    _abi_entry_for_symbol,
    _concept_ref,
    _graph_signature,
    _schema_for_symbol,
    _source_terminal,
)
from .micro import (
    _bind_source_expression,
    _bind_source_row,
)
from .numeric import (
    _numeric_literal_tree,
    _bind_numeric_expression,
    _bind_numeric_row,
)
from .registry import (
    _bind_identification_row,
    RowBinder,
    _ROW_BINDERS,
    ReleasedFrameAdapter,
    released_frame_adapter_ids,
    released_frame_adapter,
    source_frame_strategy,
    source_graph_for_adapter,
    bind_registered_source_row,
)
from .public_formal import (
    public_formal_context,
)
