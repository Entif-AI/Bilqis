"""BAMF Admin Main Frame typed records and bounded CP03 query contracts."""
from .contracts.codec import canonical_json, decode_json, decode_record, encode_record
from .contracts.envelopes import (
    ErrorEnvelope, EventEnvelope, PartialEnvelope, StaleEnvelope,
    StreamPosition, UnavailableEnvelope, UnavailableReason,
)
from .contracts.events import (
    CandidateDecision, CandidateOutcome, CorrectionEvent, FrameCompileReceipt,
    LearningEpisode, SalienceEvent,
)
from .contracts.model import (
    AuthorityClass, ContractErrorCode, CoverageState, DataValue,
    MissionControlContractError, RecordMeta, RunRef, ValueOrigin, ValueState,
)
from .contracts.observability import (
    GenerationManifest, MemorySnapshot, NeuralRuntimeSample, ResourceSample,
    SemanticAtlasSnapshot, TeacherSnapshot,
)
from .contracts.operator import (
    ActionParameter, ActionReceiptState, OperatorActionReceipt,
    OperatorActionReceiptV2, OperatorActionRequest, OperatorActionRequestV2,
)
from .query_contracts import (
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, QUERY_PAGE_SCHEMA, QUERY_REQUEST_SCHEMA,
    QueryFamily, QueryLink, QueryMode, QueryPage, QueryRequest, QueryState,
)
from .query_catalog import MissionControlQueryCatalog
from .projection import (
    PROJECTION_SCHEMA, PROJECTION_SCHEMA_VERSION, MissionControlProjection,
    ProjectionFrontierState, ProjectionFrontierStatus, ProjectionStats,
)
from .contracts.registry import ALL_RECORD_TYPES, RECORD_BY_SCHEMA
from .contracts.schema import record_schema, schema_bundle
from .semantic import (
    SemanticAdmissionState, SemanticBankSnapshot, SemanticConceptSnapshot,
    SemanticGenerationState, SemanticHeldMappingSnapshot, SemanticLabel,
    SemanticRealization, SemanticRelation, SemanticSimilaritySnapshot,
    SemanticSourceRow,
)
from .contracts.snapshots import (
    CapabilitySnapshot, CurriculumFrontier, OperatorView, RunContext,
    SchoolSnapshot,
)

__all__ = (
    "ALL_RECORD_TYPES", "ActionParameter", "ActionReceiptState",
    "AuthorityClass", "CandidateDecision", "CandidateOutcome",
    "CapabilitySnapshot", "ContractErrorCode", "CorrectionEvent",
    "CoverageState", "CurriculumFrontier", "DataValue", "ErrorEnvelope",
    "EventEnvelope", "FrameCompileReceipt", "GenerationManifest",
    "LearningEpisode", "MemorySnapshot", "MissionControlContractError",
    "MissionControlQueryCatalog",
    "MissionControlProjection", "PROJECTION_SCHEMA", "PROJECTION_SCHEMA_VERSION",
    "ProjectionFrontierState", "ProjectionFrontierStatus", "ProjectionStats",
    "NeuralRuntimeSample", "OperatorActionReceipt", "OperatorActionReceiptV2",
    "OperatorActionRequest", "OperatorActionRequestV2",
    "OperatorView", "PartialEnvelope", "RECORD_BY_SCHEMA", "RecordMeta",
    "ResourceSample", "RunContext", "RunRef", "SalienceEvent",
    "DEFAULT_PAGE_SIZE", "MAX_PAGE_SIZE", "QUERY_PAGE_SCHEMA",
    "QUERY_REQUEST_SCHEMA", "QueryFamily", "QueryLink", "QueryMode",
    "QueryPage", "QueryRequest", "QueryState",
    "SchoolSnapshot", "SemanticAtlasSnapshot", "StaleEnvelope",
    "SemanticAdmissionState", "SemanticBankSnapshot", "SemanticConceptSnapshot",
    "SemanticGenerationState", "SemanticHeldMappingSnapshot", "SemanticLabel",
    "SemanticRealization", "SemanticRelation", "SemanticSimilaritySnapshot",
    "SemanticSourceRow",
    "StreamPosition", "TeacherSnapshot", "UnavailableEnvelope",
    "UnavailableReason", "ValueOrigin", "ValueState", "canonical_json",
    "decode_json", "decode_record", "encode_record", "record_schema",
    "schema_bundle",
)

# Preserve accepted CP02 deep-import paths while contracts have one owner.
import sys as _sys
from importlib import import_module as _import_module

for _name in ('codec', 'model', 'envelopes', 'events', 'snapshots', 'observability', 'operator', 'registry', 'schema', 'fixtures'):
    _module = _import_module(f".contracts.{_name}", __name__)
    _sys.modules[f"{__name__}.{_name}"] = _module
    globals()[_name] = _module
