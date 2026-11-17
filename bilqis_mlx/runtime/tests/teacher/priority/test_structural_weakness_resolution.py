"""R13 source-scored structural weakness closure proofs."""
from types import SimpleNamespace

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime import structural_weakness_replay as weakness_replay
from bilqis_mlx.runtime.capability_retention import (
    EvaluationCohort, EvidenceKind, EvidenceStage, case_census_digest,
    evaluate_capabilities,
)
from bilqis_mlx.runtime.factory_task_template import _source_view
from bilqis_mlx.runtime.source_execution import source_content_digest
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    _cases, _solver,
)
from bilqis_mlx.runtime.tests.teacher.priority.test_structural_weakness_replay import (
    CAPABILITY, _SourceContext, _selection_for_context, _weakness_record,
)


def _proof(monkeypatch, tmp_path):
    fresh_row = {
        "id": "fresh:0", "capability": CAPABILITY,
        "shape": ["edge", 2], "answer_kind": "typed-z",
    }
    context = _SourceContext((fresh_row,))
    selection = _selection_for_context(context)
    rejected = {
        "id": "old", "capability": CAPABILITY,
        "shape": ["edge", 2], "answer_kind": "typed-z",
    }
    weakness = _weakness_record(selection, rejected)
    evidence = {
        "capability": CAPABILITY,
        "retention_reason": "NO_MEASURABLE_TARGET_GAIN",
        "candidate_evidence": {"object": {"sha256": "e" * 64}},
        "how_outcome": {"outcome_sha256": "f" * 64},
        "structural_weaknesses": [weakness],
    }
    teacher = weakness_replay.apply_rejection_weaknesses({}, evidence, "9" * 64)
    carried = weakness_replay.carried_structural_weaknesses(teacher)
    cases, contexts = _cases(CAPABILITY, "Z", 1, "fresh")
    cohort = EvaluationCohort(
        EvidenceKind.FRESH_TARGET, cases, ((CAPABILITY, "Z"),),
        "1" * 64, "2" * 64, "3" * 64, "4" * 64,
        ("training-family",), ("training-episode",),
        case_census_digest(cases), evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION)
    assessment = evaluate_capabilities(
        _solver(contexts, {cases[0].case_id}), cohort, "5" * 64)

    class _Instrument:
        def __init__(self, source_row):
            self.case = cases[0]
            self.source_row = source_row
            self.compiled_case = SimpleNamespace(task_template=SimpleNamespace(
                source_row_id=source_row["id"], capability_id=CAPABILITY,
                release_sha256=context.release.release_sha256,
                source_row_sha256=source_content_digest((_source_view(source_row),)),
            ))

    monkeypatch.setattr(
        "bilqis_mlx.runtime.factory_complete_solver.FactoryEvaluationInstrument",
        _Instrument)
    monkeypatch.setattr(
        "bilqis_mlx.runtime.bamf_operator.evidence_validation.read_candidate_horizon_evidence",
        lambda _run_dir, _receipt: {"source_objects": {"old": rejected}})
    return context, selection, teacher, carried[0], evidence, assessment, fresh_row, _Instrument


def test_closure_requires_fresh_source_scored_equivalent_bytes(monkeypatch, tmp_path):
    context, selection, teacher, wrapper, evidence, assessment, fresh, instrument = (
        _proof(monkeypatch, tmp_path))
    closed = weakness_replay.resolve_structural_weakness(
        teacher, run_dir=tmp_path, wrapper=wrapper, source_context=context,
        selection=selection, assessment=assessment, instruments=(instrument(fresh),))
    assert weakness_replay.carried_structural_weaknesses(closed) == ()
    item = next(iter(closed["structural_weaknesses"]["classes"].values()))
    assert item["state"] == "RESOLVED"
    assert len(item["resolution_evidence_sha256"]) == 64
    replayed = weakness_replay.apply_rejection_weaknesses(closed, evidence, "9" * 64)
    assert weakness_replay.carried_structural_weaknesses(replayed) == ()


def test_same_id_different_source_bytes_cannot_close(monkeypatch, tmp_path):
    context, selection, teacher, wrapper, _evidence, assessment, fresh, instrument = (
        _proof(monkeypatch, tmp_path))
    drifted = instrument(fresh)
    drifted.source_row = {**fresh, "shape": ["edge", 99]}
    with pytest.raises(BilqisError) as failure:
        weakness_replay.resolve_structural_weakness(
            teacher, run_dir=tmp_path, wrapper=wrapper, source_context=context,
            selection=selection, assessment=assessment, instruments=(drifted,))
    assert failure.value.context["reason"] == "BAMF_WEAKNESS_RESOLUTION_ASSESSED_ROW_DRIFT"
