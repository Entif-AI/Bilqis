"""Generic literal samples spanning CP02 top-level record types."""
from __future__ import annotations

from bilqis_mlx.mission_control.envelopes import (
    ErrorEnvelope, EventEnvelope, PartialEnvelope, StaleEnvelope,
    StreamPosition, UnavailableEnvelope, UnavailableReason, event_cursor_sha256,
)
from bilqis_mlx.mission_control.events import (
    CandidateDecision, CandidateOutcome, CorrectionEvent, FrameCompileReceipt,
    LearningEpisode, SalienceEvent,
)
from bilqis_mlx.mission_control.model import (
    AuthorityClass, CoverageState, DataValue, RecordMeta, RunRef,
    ValueOrigin, ValueState,
)
from bilqis_mlx.mission_control.observability import (
    GenerationManifest, MemorySnapshot, NeuralRuntimeSample, ResourceSample,
    SemanticAtlasSnapshot, TeacherSnapshot,
)
from bilqis_mlx.mission_control.operator import (
    ActionParameter, ActionReceiptState, OperatorActionReceipt,
    OperatorActionReceiptV2, OperatorActionRequest, OperatorActionRequestV2,
)
from bilqis_mlx.mission_control.semantic import (
    SemanticAdmissionState, SemanticBankSnapshot, SemanticConceptSnapshot,
    SemanticGenerationState, SemanticHeldMappingSnapshot, SemanticLabel,
    SemanticRealization, SemanticRelation, SemanticSimilaritySnapshot,
    SemanticSourceRow,
)
from bilqis_mlx.mission_control.contracts.dossier import CapabilityDossier
from bilqis_mlx.mission_control.snapshots import (
    CapabilitySnapshot, CurriculumFrontier, OperatorView, RunContext,
    SchoolSnapshot,
)


D1, D2, D3, D4 = (char * 64 for char in "1234")
RUN = RunRef("run-7", D4, 7, D1, D2, D2, D3, D4)


def meta(name: str, *, run=RUN, authority=AuthorityClass.DERIVED,
         coverage=CoverageState.COMPLETE, as_of=118) -> RecordMeta:
    return RecordMeta(
        record_id=name, run=run, materialized_at=120, observed_at=118, as_of=as_of,
        coverage=coverage, authority=authority,
        source_refs=("source:a",), evidence_refs=("evidence:a",),
        receipt_refs=("receipt:a",),
    )


def value(number, units="count", origin=ValueOrigin.MEASURED) -> DataValue:
    return DataValue(ValueState.PRESENT, origin, number, units)


SEMANTIC_ID = "https://github.com/Entif-AI/Bilqis-MLX/id/sense/source/root/STEM%201/BSC"
SEMANTIC_CONCEPT_ID = f"semantic-concept:{D1}:{SEMANTIC_ID}"
SEMANTIC_SOURCE_META = RecordMeta(
    record_id=SEMANTIC_CONCEPT_ID, run=None, materialized_at=120,
    observed_at=118, as_of=118, coverage=CoverageState.COMPLETE,
    authority=AuthorityClass.SOURCE_AUTHORITATIVE,
    source_refs=("atlas-bundle:fixture",), evidence_refs=(), receipt_refs=(),
)
SEMANTIC_HELD_META = RecordMeta(
    record_id=f"semantic-held:{D1}:fixture", run=None, materialized_at=120,
    observed_at=118, as_of=118, coverage=CoverageState.COMPLETE,
    authority=AuthorityClass.SOURCE_AUTHORITATIVE,
    source_refs=("atlas-bundle:fixture",), evidence_refs=(), receipt_refs=(),
)

BASE_SAMPLES = (
    RunContext(meta("run-context"), "READY", 42, "ASSESS_MAIN"),
    OperatorView(meta("operator-view"), "READY", "ASSESS_MAIN", "B.EXAMPLE", ("school",)),
    SchoolSnapshot(meta("school"), "ACTIVE", "B", ("A", "B"), value(9), value(4)),
    CapabilitySnapshot(meta("capability"), "B.EXAMPLE", "B", "LEARNING",
                       value(7), value(10), value(2)),
    CurriculumFrontier(meta("frontier"), "frontier-7", ("B.NEXT",), ("C.HELD",),
                       ("A.DONE",)),
    LearningEpisode(meta("episode"), "episode-1", "B.EXAMPLE", "visit-1",
                    "COMPLETED", 100, 110),
    CandidateDecision(meta("decision"), "candidate-1", "B.EXAMPLE",
                      CandidateOutcome.ACCEPTED, "SOURCE_GOLD_PASS"),
    SemanticAtlasSnapshot(meta("atlas"), D2, D1, D3,
                          value(30), value(40), value(10)),
    FrameCompileReceipt(meta("frame"), "frame-1", D1, D2, False, 2),
    NeuralRuntimeSample(meta("runtime"), 42, value(12.5, "ms"),
                        value(1000, "parameters"), value(0.25, "fraction")),
    MemorySnapshot(meta("memory"), value(100, "bytes"), value(1000, "bytes"),
                   value(8), value(2), value(1)),
    TeacherSnapshot(meta("teacher"), "teacher-a", 3, "strategy-2",
                    value(10), value(7), value(3)),
    SalienceEvent(meta("salience"), "salience-1", "B.EXAMPLE",
                  value(3, "ordinal", ValueOrigin.SOURCE_AUTHORITATIVE),
                  value(2, "ordinal", ValueOrigin.DERIVED),
                  value(4, "ordinal", ValueOrigin.INFERRED), "TEACHING"),
    CorrectionEvent(meta("correction"), "correction-1", 4, "source:a", D1, D2,
                    "REQUALIFICATION_REQUIRED"),
    GenerationManifest(meta("generation"), D1, D2, D3, D4, "ACCEPTED"),
    ResourceSample(meta("resources"), value(100, "bytes"), value(1000, "bytes"),
                   value(500, "bytes"), value(1.5, "steps/minute")),
    SemanticConceptSnapshot(
        SEMANTIC_SOURCE_META, D1, SEMANTIC_ID, "sense", ("skos:Concept",),
        (SemanticLabel("definition", "self-same entity", "en"),),
        (SemanticRealization("č", None, None),),
        ("lexicon:1.3:2",),
        (SemanticSourceRow("lexicon", "lexicon_root_senses", "LEXSENSE-fixture"),),
        (SemanticRelation("skos:broader", "semantic:root"),),
        9, 0, 9, "ADMITTED", True, "SOURCE_ELIGIBLE",
        ("frame:fixture/v1",), ("D.COPULAR_IDENTITY",),
    ),
    SemanticGenerationState(
        meta("semantic-state"), SEMANTIC_ID, SEMANTIC_CONCEPT_ID,
        9, 0, 9, SemanticAdmissionState.ACTIVE, True, True, False,
    ),
    SemanticBankSnapshot(meta("semantic-bank"), 0, 8192, 10, 4, 6, 1, 2, 1),
    SemanticHeldMappingSnapshot(
        SEMANTIC_HELD_META, D1, "mapping", "lexicon_mapping", "held-1",
        "semantic:held", "SOURCE_HELD", "IMPLEMENTATION_UNCOVERED",
        "AMBIGUOUS_MAPPING", "HOLD_FOR_REVIEW", "#55",
    ),
    SemanticSimilaritySnapshot(
        meta("semantic-similarity", authority=AuthorityClass.DERIVED),
        SEMANTIC_ID, "semantic:distinct", "embedding:fixture",
        value(0.91, "similarity", ValueOrigin.DERIVED), False,
    ),
    OperatorActionRequest(meta("action-request"), "request-1", "idem-1", "dry-run",
                          (ActionParameter("mode", "bounded"),), True, 119),
    OperatorActionReceipt(meta("action-receipt"), "request-1", "operation-1",
                          ActionReceiptState.COMPLETED, 120, "postcondition:a", None),
    OperatorActionRequestV2(
        meta("action-request-v2", run=None),
        "request-v2", "idem-v2", "create",
        (ActionParameter("run_id", "run-v2"),),
        True, False, 119,
    ),
    OperatorActionReceiptV2(
        meta("action-receipt-v2", run=None),
        "request-v2", D1, "operation-v2", ActionReceiptState.ACCEPTED,
        120, f"command-target:{D2}", None, None,
    ),
    ErrorEnvelope(meta("error", run=None), "RUN_NOT_FOUND", "run unavailable", None),
    UnavailableEnvelope(meta("unavailable", run=None, coverage=CoverageState.UNKNOWN),
                        "run:missing", UnavailableReason.MISSING, None),
    StaleEnvelope(meta("stale", coverage=CoverageState.PARTIAL, as_of=100),
                  "operator-view", 100, 118),
    PartialEnvelope(meta("partial", coverage=CoverageState.PARTIAL), "school",
                    ("mastered_count",)),
    EventEnvelope(
        meta("event"),
        "event-9",
        StreamPosition(
            "run-7:candidate",
            "epoch-1",
            9,
            event_cursor_sha256(
                stream_id="run-7:candidate",
                epoch_id="epoch-1",
                ordinal=9,
                event_id="event-9",
                payload_schema_version=CandidateDecision.SCHEMA,
                payload_record_id="decision",
                payload_sha256=D1,
                previous_cursor_sha256=D4,
            ),
            D4,
        ),
        "candidate",
        CandidateDecision.SCHEMA,
        "decision",
        D1,
        "evidence:event-9",
    ),
)

BASE_SAMPLES += (CapabilityDossier(meta("dossier-sample"), "B.EXAMPLE", "Example",
    value(7), value(8), value(12), value(5), value("WATCH"), value("ELIGIBLE"),
    value("QUALIFIED"), value("HELD"), ()),)
