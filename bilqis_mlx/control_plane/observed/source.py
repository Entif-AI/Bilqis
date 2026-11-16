"""Read disposable trainer posture without granting it accepted-state authority."""
from dataclasses import fields
import json
import os
from pathlib import Path
import time

from bilqis_mlx.mission_control.contracts.model import (
    AuthorityClass, CoverageState, RecordMeta, is_time,
)
from bilqis_mlx.mission_control.contracts.trainer import (
    TrainerObservation, TrainerObservationV2, TrainerObservationV3,
)


MAX_BYTES = 64 * 1024
MAX_VISITS = 8
MAX_HEARTBEAT_AGE_MS = 10_000
MAX_FUTURE_SKEW_MS = 5_000
_SCHEMAS = frozenset({
    'bilqis.bamf.trainer-observed/v1',
    'bilqis.bamf.trainer-observed/v2',
    'bilqis.bamf.trainer-observed/v3',
})
_FIELDS = {field.name for field in fields(TrainerObservation)} - {
    'meta', 'posture', 'connection_state'}
_OPTIONAL_FIELDS = frozenset(('error_code', 'error_detail'))
_V2_FIELDS = {field.name for field in fields(TrainerObservationV2)} - {
    'meta', 'posture', 'connection_state'}
_V2_ONLY = _V2_FIELDS - _FIELDS
_V3_FIELDS = {field.name for field in fields(TrainerObservationV3)} - {
    'meta', 'posture', 'connection_state'}
_V3_ONLY = _V3_FIELDS - _V2_FIELDS


def process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _connection(row, now_ms):
    if row.get('outcome') != 'RUNNING':
        return 'FINISHED'
    age = now_ms - row['observed_at']
    pid = row.get('process_id')
    if type(pid) is not int or pid <= 0 or age > MAX_HEARTBEAT_AGE_MS or age < -MAX_FUTURE_SKEW_MS:
        return 'DISCONNECTED'
    return 'LIVE' if process_exists(pid) else 'DISCONNECTED'


def _record(row, runs, now_ms):
    parent = runs.get((row.get('run_id'), row.get('parent_manifest_sha256')))
    if parent is None or not is_time(row.get('observed_at')):
        return None
    state = _connection(row, now_ms)
    identifier = f"trainer-observed:{row['observation_id']}:{row['revision']}:{state}"
    observed_at_seconds = row['observed_at'] // 1000
    meta = RecordMeta(
        record_id=identifier, run=parent, materialized_at=observed_at_seconds,
        observed_at=observed_at_seconds, as_of=None, coverage=CoverageState.PARTIAL,
        authority=AuthorityClass.MEASURED,
        source_refs=(f"trainer-observed:{row['observation_id']}",),
    )
    record_type = (
        TrainerObservationV3 if _V3_ONLY <= set(row) else
        TrainerObservationV2 if _V2_ONLY <= set(row) else TrainerObservation)
    record_fields = (
        _V3_FIELDS if record_type is TrainerObservationV3 else
        _V2_FIELDS if record_type is TrainerObservationV2 else _FIELDS)
    values = {
        key: row.get(key) if key in _OPTIONAL_FIELDS else row[key]
        for key in record_fields
    }
    if record_type is TrainerObservationV3:
        from bilqis_mlx.mission_control.contracts.trainer import CandidateStepPerformance
        values['candidate_steps'] = tuple(
            CandidateStepPerformance(**item) for item in values['candidate_steps'])
    return record_type(
        meta=meta, posture='OBSERVED', connection_state=state, **values)


def observed_records(run_dir: Path, runs, *, now_ms=None) -> tuple[TrainerObservation, ...]:
    """Bound input bytes and rows; malformed observations cannot hide accepted state."""
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    try:
        with (Path(run_dir) / 'trainer-observed.json').open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return ()
        payload = json.loads(raw)
        if (not isinstance(payload, dict) or payload.get('schema') not in _SCHEMAS
                or not isinstance(payload.get('visits'), list)):
            return ()
    except (OSError, ValueError, UnicodeError, RecursionError):
        return ()
    parents = {(run.run_id, run.generation_manifest_sha256): run for run in runs}
    records = {}
    # Older or interrupted producers may leave more history than the current
    # reader budget.  Currentness is in the tail, so bound the projection rather
    # than discarding every observation from an otherwise valid snapshot.
    for row in payload['visits'][-MAX_VISITS:]:
        try:
            record = _record(row, parents, now_ms)
            if record is not None:
                records[record.observation_id] = record
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            continue
    return tuple(records.values())
