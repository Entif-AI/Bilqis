"""Read disposable trainer posture without granting it accepted-state authority."""
from dataclasses import fields
import json
import os
from pathlib import Path
import time

from bilqis_mlx.mission_control.contracts.model import (
    AuthorityClass, CoverageState, RecordMeta, is_time,
)
from bilqis_mlx.mission_control.contracts.trainer import TrainerObservation


MAX_BYTES = 64 * 1024
MAX_VISITS = 8
MAX_HEARTBEAT_AGE_MS = 10_000
MAX_FUTURE_SKEW_MS = 5_000
_SCHEMA = 'bilqis.bamf.trainer-observed/v1'
_FIELDS = {field.name for field in fields(TrainerObservation)} - {
    'meta', 'posture', 'connection_state'}
_OPTIONAL_FIELDS = {'error_code', 'error_detail'}


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
    return TrainerObservation(
        meta=meta, posture='OBSERVED', connection_state=state,
        **{key: row.get(key) if key in _OPTIONAL_FIELDS else row[key]
           for key in _FIELDS},
    )


def observed_records(run_dir: Path, runs, *, now_ms=None) -> tuple[TrainerObservation, ...]:
    """Bound input bytes and rows; malformed observations cannot hide accepted state."""
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    try:
        with (Path(run_dir) / 'trainer-observed.json').open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return ()
        payload = json.loads(raw)
        if (not isinstance(payload, dict) or payload.get('schema') != _SCHEMA
                or not isinstance(payload.get('visits'), list)
                or len(payload['visits']) > MAX_VISITS):
            return ()
    except (OSError, ValueError, UnicodeError, RecursionError):
        return ()
    parents = {(run.run_id, run.generation_manifest_sha256): run for run in runs}
    records = {}
    for row in payload['visits']:
        try:
            record = _record(row, parents, now_ms)
            if record is not None:
                records[record.observation_id] = record
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            continue
    return tuple(records.values())
