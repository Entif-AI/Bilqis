"""Small real-consumer adapters over the CP02 OperatorView contract."""
from __future__ import annotations

from collections.abc import Mapping

from .contracts.codec import decode_record
from .contracts.model import ContractErrorCode, MissionControlContractError
from .contracts.snapshots import OperatorView


def decode_operator_view(payload: Mapping) -> OperatorView:
    record = decode_record(payload)
    if type(record) is not OperatorView:
        raise MissionControlContractError(ContractErrorCode.SCHEMA_TYPE_MISMATCH)
    return record


def terminal_status(view: OperatorView) -> tuple[str, ...]:
    """Render the shared operator record without inventing a terminal-only model."""
    run = view.meta.run
    if type(view) is not OperatorView or run is None:
        raise TypeError
    return (
        f"ADMIN MAIN FRAME | run {run.run_id} | generation {run.generation}",
        f"STATE | {view.learner_state} | stage {view.stage}",
        f"RECORD | {view.meta.record_id} | coverage {view.meta.coverage.value}",
    )
