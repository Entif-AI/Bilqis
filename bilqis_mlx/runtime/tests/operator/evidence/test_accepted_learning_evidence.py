from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.autonomy import AutonomyActionKind
from bilqis_mlx.semantics.cognitive_operators import TypedValue, ValueState


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


def test_post_accept_reentry_refreshes_evidence_before_c07():
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
