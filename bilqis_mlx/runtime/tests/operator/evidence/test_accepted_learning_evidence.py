from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory import candidate_realizations
from bilqis_mlx.factory.autonomy import (
    AutonomyActionKind, EvidenceKind, compile_autonomy_plan,
    obligations_for_capability,
)
from bilqis_mlx.factory.evidence import measure_evidence
from bilqis_mlx.factory.tests.events.support import (
    EventCandidateRealizationFixture, LEGACY,
)
from bilqis_mlx.semantics.cognitive_operators import TypedValue, ValueState
from bilqis_mlx.source_adapters import event_frames
from bilqis_mlx.source_adapters.atom_binding import verify_source_row


def _work(capability, obligation):
    return SimpleNamespace(
        capability_id=capability,
        obligation=SimpleNamespace(obligation_id=obligation),
    )


def test_accepted_evidence_refresh_stops_when_owner_requests_teaching():
    from bilqis_mlx.runtime.bamf_operator import accepted_learning_evidence as subject

    checkpoint = SimpleNamespace(sha256="c" * 64, optimizer_step=7)
    context = SimpleNamespace(
        source_root=Path("/source"), release=object(), graph=object())
    parent = object()
    first = _work("A.IDENTITY", "A.IDENTITY/direct")
    second = _work("D.EVENT_OCCURRENCE", "D.EVENT_OCCURRENCE/direct")
    session = Mock()
    session.action.side_effect = (
        SimpleNamespace(
            kind=AutonomyActionKind.LEARNING_EVIDENCE, evidence_work=first),
        SimpleNamespace(
            kind=AutonomyActionKind.LEARNING_EVIDENCE, evidence_work=second),
        SimpleNamespace(kind=AutonomyActionKind.TEACHING, evidence_work=None),
    )
    session.measure.side_effect = (
        SimpleNamespace(passed=True),
        SimpleNamespace(passed=False),
    )

    with patch.object(
            subject, "_execution_context",
            return_value=(parent, context, Path("/atlas"), Path("/features"))), patch.object(
            subject, "_accepted_checkpoint", return_value=checkpoint), patch.object(
            subject.LiveAutonomySession, "open", return_value=session), patch.object(
            subject, "_accepted_predictions", return_value={"row": "TRUE"}):
        result = subject.refresh_accepted_learning_evidence(
            Path("/run"), max_measurements=4)

    assert result.measured == 2
    assert result.passed == 1
    assert result.final_action == AutonomyActionKind.TEACHING.value
    assert session.measure.call_count == 2
    assert session.action.call_count == 3
    assert session.measure.call_args_list[0].args[:2] == (context.graph, first)
    assert session.measure.call_args_list[1].args[:2] == (context.graph, second)
    assert (
        session.measure.call_args_list[0].kwargs["checkpoint"]["sha256"]
        == checkpoint.sha256
    )


def test_accepted_evidence_refresh_fails_closed_at_bound():
    from bilqis_mlx.runtime.bamf_operator import accepted_learning_evidence as subject

    checkpoint = SimpleNamespace(sha256="c" * 64, optimizer_step=7)
    context = SimpleNamespace(
        source_root=Path("/source"), release=object(), graph=object())
    session = Mock()
    session.action.return_value = SimpleNamespace(
        kind=AutonomyActionKind.LEARNING_EVIDENCE,
        evidence_work=_work("A.IDENTITY", "A.IDENTITY/direct"),
    )
    session.measure.return_value = SimpleNamespace(passed=True)

    with patch.object(
            subject, "_execution_context",
            return_value=(object(), context, Path("/atlas"), Path("/features"))), patch.object(
            subject, "_accepted_checkpoint", return_value=checkpoint), patch.object(
            subject.LiveAutonomySession, "open", return_value=session), patch.object(
            subject, "_accepted_predictions", return_value={"row": "TRUE"}), pytest.raises(
            BilqisError) as failure:
        subject.refresh_accepted_learning_evidence(
            Path("/run"), max_measurements=1)

    assert failure.value.context["reason"] == (
        "BAMF_OPERATOR_ACCEPTED_EVIDENCE_BOUND_EXHAUSTED")


def test_boundary_reentry_refreshes_evidence_before_c07():
    from bilqis_mlx.runtime.bamf_operator import session as operator
    from bilqis_mlx.runtime.bamf_operator.accepted_learning_evidence import (
        AcceptedLearningEvidenceRefresh,
    )

    order = []
    with patch(
            "bilqis_mlx.runtime.bamf_operator.accepted_learning_evidence."
            "refresh_accepted_learning_evidence",
            side_effect=lambda *_args, **_kwargs: (
                order.append("evidence")
                or AcceptedLearningEvidenceRefresh(2, 2, "QUALIFICATION")
            )), patch.object(
            operator, "_accepted_admission_reentry",
            side_effect=lambda *_args, **_kwargs: (
                order.append("c07") or ("WAITING_FOR_EVIDENCE", 1, None)
            )):
        result = operator._accepted_learning_reentry(
            Path("/run"), {"@graph": []}, 0.0)

    assert order == ["evidence", "c07"]
    assert result == ("WAITING_FOR_EVIDENCE", 1, None)


@pytest.mark.parametrize(
    ("answer", "expected"),
    (
        (TypedValue("Boolean", True, "a" * 64), "TRUE"),
        (TypedValue("Boolean", False, "a" * 64), "FALSE"),
        (TypedValue("Number", 17, "a" * 64), "17"),
        (TypedValue("OperatorId", "B.AND", "a" * 64), "B.AND"),
        (TypedValue("Boolean", None, "a" * 64, None, ValueState.UNRESOLVED),
         "__UNRESOLVED__"),
    ),
)
def test_factory_answer_text_preserves_assessment_modalities(answer, expected):
    from bilqis_mlx.runtime.bamf_operator.accepted_learning_evidence import (
        _answer_text,
    )

    assert _answer_text(answer) == expected


class AcceptedEvidenceSourceDrawTests(
        EventCandidateRealizationFixture, unittest.TestCase):
    def test_event_prerequisite_keeps_exact_source_draw_through_measurement(self):
        staged = candidate_realizations.prepare_realized_candidate(
            self.frontier,
            self.current,
            self.parent_graph,
            event_frames.atlas_semantic_id("D.EVENT_OCCURRENCE"),
            source_root=LEGACY,
            source_registry=self.source_registry,
            answer_registry=self.answer_registry,
        )
        release = staged.successor
        graph = candidate_realizations.admitted_candidate_graph(
            staged, self.parent_graph)
        plan = compile_autonomy_plan(release)
        obligation = next(
            item for item in obligations_for_capability(
                release, "D.EVENT_OCCURRENCE", plan=plan)
            if (item.kind is EvidenceKind.PREREQUISITE
                and item.key == "A.IDENTITY")
        )
        self.assertEqual(obligation.minimum_specimens, 1)
        observed = []

        def source_bound_predictor(rows, source_draws):
            execution = release.execution_plan.capability_map[
                "D.EVENT_OCCURRENCE"]
            profile = (
                dict(execution.provider_parameters)
                if execution.provider_parameters else None)
            for row, draw in zip(rows, source_draws, strict=True):
                verify_source_row(
                    row,
                    graph,
                    source_root=LEGACY,
                    source_seed=draw.source_seed,
                    source_each=draw.source_each,
                    course=release.curriculum,
                    source_profile_parameters=profile,
                )
                observed.append(draw)
            return {row["id"]: row["gold"] for row in rows}

        receipt = measure_evidence(
            LEGACY,
            graph,
            release,
            self.source_registry,
            obligation,
            checkpoint={
                "sha256": "c" * 64,
                "optimizer_step": 7,
                "model_and_native_adamw": True,
            },
            seed=23,
            predictor=None,
            source_bound_predictor=source_bound_predictor,
        )

        self.assertTrue(receipt.passed)
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0].source_each, 8)
