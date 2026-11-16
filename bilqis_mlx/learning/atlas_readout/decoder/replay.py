"""Replay one model-derived causal trajectory without host scalar extraction."""
from __future__ import annotations

from bilqis_mlx.errors import BilqisError

from ..control import ControlAction
from ..decisions import (
    DecodeStatus, commit_decisions, ready_decisions, start_decoding,
)
from ..frames import publish_frame
from ..records import invalid
from .inputs import validate_decoder_inputs
from .math import prepare_memory
from .prediction import (
    ExecutionMode, ModelOutput, _issue_output, _ready_outputs,
)


def predict_typed_replay(
    memory, eligible_context, answer_plan, active_semantics, readout_params,
    replay_output: ModelOutput,
) -> ModelOutput:
    """Recompute logits while preserving an inference-derived branch history."""
    validate_decoder_inputs(
        memory, eligible_context, answer_plan, active_semantics, readout_params)
    if (type(replay_output) is not ModelOutput
            or replay_output.plan != answer_plan
            or replay_output.execution_mode is not ExecutionMode.INFERENCE):
        invalid()

    prepared = prepare_memory(memory, readout_params, active_semantics)
    state = start_decoding(answer_plan)
    records = []
    trajectory = replay_output.committed
    cursor = 0
    while state.status is DecodeStatus.ACTIVE:
        ready = ready_decisions(state)
        if cursor >= len(trajectory):
            return _issue_output(ModelOutput(
                answer_plan, tuple(records), state.committed,
                DecodeStatus.UNRESOLVED, ExecutionMode.INFERENCE,
                None, True), fingerprint=False)

        if trajectory[cursor].value is ControlAction.END_FRAME:
            expected = trajectory[cursor:cursor + 1]
            if expected[0].decision_id not in {
                    item.decision_id for item in ready}:
                invalid()
        else:
            expected = trajectory[cursor:cursor + len(ready)]
            if (len(expected) != len(ready)
                    or tuple(item.decision_id for item in expected)
                    != tuple(item.decision_id for item in ready)):
                invalid()

        replay_values = {item.decision_id: item.value for item in expected}
        batch, outputs = _ready_outputs(
            memory, state, active_semantics, readout_params, prepared, {},
            trace=True, replay_values=replay_values)
        if tuple(outputs) != tuple(expected):
            invalid()
        try:
            state = commit_decisions(state, outputs)
        except BilqisError:
            invalid()
        committed_ids = {item.decision_id for item in outputs}
        records.extend(
            record for record in batch if record.decision_id in committed_ids)
        cursor += len(outputs)

    if cursor != len(trajectory):
        invalid()
    status, frame = state.status, None
    if status is DecodeStatus.COMPLETE and not answer_plan.route_only:
        try:
            frame = publish_frame(state)
        except BilqisError:
            status = DecodeStatus.UNRESOLVED
    if (status is not replay_output.status
            or state.committed != replay_output.committed):
        invalid()
    return _issue_output(ModelOutput(
        answer_plan, tuple(records), state.committed, status,
        ExecutionMode.INFERENCE, frame, status is not DecodeStatus.COMPLETE),
        fingerprint=False)


__all__ = ("predict_typed_replay",)
