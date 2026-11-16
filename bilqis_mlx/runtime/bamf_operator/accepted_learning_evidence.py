"""Refresh accepted A09 learner evidence before post-accept C07 re-entry."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.autonomy import (
    AutonomyActionKind,
    obligations_for_capability,
)
from bilqis_mlx.runtime.atlas_flywheel_runtime import _accepted_checkpoint
from bilqis_mlx.runtime.autonomy_live import LiveAutonomySession
from bilqis_mlx.runtime.factory_complete_solver import (
    factory_complete_solver,
    factory_evaluation_instrument,
)
from bilqis_mlx.semantics.cognitive_operators import TypedValue, ValueState

from .session_support import _execution_context


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.BAMF_OPERATOR.INVALID, reason=reason)


@dataclass(frozen=True)
class AcceptedLearningEvidenceRefresh:
    """Bounded receipt for synchronous accepted-checkpoint evidence refresh."""

    measured: int
    passed: int
    final_action: str


def _answer_text(answer: TypedValue) -> str:
    """Render one solver answer in the Factory cohort's canonical gold form."""
    if not isinstance(answer, TypedValue):
        _invalid("BAMF_OPERATOR_ACCEPTED_EVIDENCE_ANSWER_INVALID")
    if answer.state is not ValueState.VALUE:
        return "__UNRESOLVED__"
    if answer.type_name == "Boolean":
        return "TRUE" if answer.value else "FALSE"
    if answer.type_name == "Number":
        return str(answer.value)
    if answer.type_name == "OperatorId":
        return str(answer.value)
    _invalid("BAMF_OPERATOR_ACCEPTED_EVIDENCE_MODALITY_UNSUPPORTED")


def _accepted_predictions(
    source_context,
    parent,
    atlas_artifact_path: Path,
    rows,
    source_draws,
    *,
    seed: int,
) -> dict[str, str]:
    """Evaluate fresh A09 evidence rows with the exact accepted BAMF solver."""
    rows = tuple(rows)
    if not rows:
        _invalid("BAMF_OPERATOR_ACCEPTED_EVIDENCE_ROWS_REQUIRED")
    source_by_id = {item.row_id: item for item in source_draws}
    if (len(source_by_id) != len(rows)
            or set(source_by_id) != {row["id"] for row in rows}):
        _invalid("BAMF_OPERATOR_ACCEPTED_EVIDENCE_SOURCE_DRAW_DRIFT")
    instruments = tuple(
        factory_evaluation_instrument(
            source_context,
            parent,
            str(atlas_artifact_path),
            row,
            source_seed=source_by_id[row["id"]].source_seed,
            source_each=source_by_id[row["id"]].source_each,
        )
        for row in rows
    )
    solver, generation = factory_complete_solver(
        source_context, parent, str(atlas_artifact_path), instruments)
    measurements = solver.evaluate_cases(
        tuple(item.case.goal for item in instruments), generation)
    if len(measurements) != len(rows):
        _invalid("BAMF_OPERATOR_ACCEPTED_EVIDENCE_RESULT_COUNT_DRIFT")
    return {
        row["id"]: _answer_text(result.answer)
        for row, (result, _contract) in zip(rows, measurements, strict=True)
    }


def _measurement_seed(checkpoint, obligation_id: str, offset: int) -> int:
    if (not isinstance(obligation_id, str) or not obligation_id
            or type(offset) is not int or offset < 0):
        _invalid("BAMF_OPERATOR_ACCEPTED_EVIDENCE_SEED_INPUT_INVALID")
    payload = (
        "bilqis.bamf.accepted-learning-evidence/v1\n"
        + checkpoint.sha256 + "\n"
        + str(checkpoint.optimizer_step) + "\n"
        + obligation_id + "\n"
        + str(offset)
    ).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _measurement_bound(session: LiveAutonomySession) -> int:
    """Bound one checkpoint refresh by the owner's current obligation census."""
    capability_ids = tuple(
        item.capability_id
        for item in session.release.execution_plan.capabilities)
    return max(
        1,
        sum(
            len(obligations_for_capability(
                session.release, capability_id, plan=session.plan))
            for capability_id in capability_ids
        ),
    )


def refresh_accepted_learning_evidence(
    run_dir: Path,
    *,
    progress=None,
    max_measurements: int | None = None,
) -> AcceptedLearningEvidenceRefresh:
    """Run only owner-requested A09 evidence work on the accepted checkpoint.

    This phase is neural-inert with respect to optimizer state. It may perform
    inference for fresh evidence cohorts, but it stops immediately when A09
    requests teaching, source work, qualification, or any other non-evidence
    action. C07 remains the sole successor-admission owner.
    """
    if (not isinstance(run_dir, Path)
            or (max_measurements is not None
                and (type(max_measurements) is not int or max_measurements < 1))):
        _invalid("BAMF_OPERATOR_ACCEPTED_EVIDENCE_INPUT_INVALID")
    parent, source_context, atlas_artifact_path, _feature_path = (
        _execution_context(run_dir))
    checkpoint = _accepted_checkpoint(run_dir)
    session = LiveAutonomySession.open(
        run_dir, Path(source_context.source_root), source_context.release)
    measurement_limit = (
        _measurement_bound(session)
        if max_measurements is None else max_measurements)
    measured = 0
    passed = 0
    while True:
        action = session.action(checkpoint)
        if action.kind is not AutonomyActionKind.LEARNING_EVIDENCE:
            return AcceptedLearningEvidenceRefresh(
                measured, passed, action.kind.value)
        if measured >= measurement_limit:
            _invalid("BAMF_OPERATOR_ACCEPTED_EVIDENCE_BOUND_EXHAUSTED")
        work = action.evidence_work
        if work is None:
            _invalid("BAMF_OPERATOR_ACCEPTED_EVIDENCE_WORK_REQUIRED")
        seed = _measurement_seed(
            checkpoint, work.obligation.obligation_id, measured)
        evidence = session.measure(
            source_context.graph,
            work,
            checkpoint={
                "sha256": checkpoint.sha256,
                "optimizer_step": checkpoint.optimizer_step,
                "model_and_native_adamw": True,
            },
            seed=seed,
            source_bound_predictor=(
                lambda rows, source_draws, _seed=seed: _accepted_predictions(
                source_context,
                parent,
                atlas_artifact_path,
                rows,
                source_draws,
                seed=_seed,
            )),
        )
        measured += 1
        passed += int(evidence.passed)
        if progress is not None:
            progress(
                "evidence: measured "
                + work.capability_id
                + " "
                + ("PASS" if evidence.passed else "FAIL"))


__all__ = (
    "AcceptedLearningEvidenceRefresh",
    "refresh_accepted_learning_evidence",
)
