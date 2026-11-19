"""Disposable, observational trainer snapshots; never part of custody."""
from __future__ import annotations

import json
import os
from pathlib import Path
import resource
import shutil
import sys
import tempfile
import threading
import time
import uuid

from .performance import (
    PERFORMANCE_FIELDS, RETENTION_PROFILE_FIELDS, VISIT_PERFORMANCE_FIELDS,
)

SCHEMA = 'bilqis.bamf.trainer-observed/v6'
LEGACY_SCHEMA_V5 = 'bilqis.bamf.trainer-observed/v5'
LEGACY_SCHEMA_V4 = 'bilqis.bamf.trainer-observed/v4'
LEGACY_SCHEMA = 'bilqis.bamf.trainer-observed/v1'
LEGACY_SCHEMA_V2 = 'bilqis.bamf.trainer-observed/v2'
LEGACY_SCHEMA_V3 = 'bilqis.bamf.trainer-observed/v3'
MAX_SNAPSHOT_BYTES = 64 * 1024
STEP_HISTORY_LIMIT = 64
LEARNING_HISTORY_LIMIT = 48
MAX_ERROR_TEXT = 256


def _bounded_error_text(value):
    if not isinstance(value, str):
        value = str(value)
    value = value.strip().replace('\n', ' ')
    return value[:MAX_ERROR_TEXT] or None


def _exception_fields(exc_type, exc):
    code = getattr(exc, 'code', None)
    if not isinstance(code, str) or not code:
        code = getattr(exc_type, '__name__', None) or 'Exception'
    context = getattr(exc, 'context', None)
    detail = context.get('reason') if hasattr(context, 'get') else None
    if detail is None and exc is not None and str(exc) != code:
        detail = str(exc)
    return _bounded_error_text(code), _bounded_error_text(detail) if detail is not None else None


class TrainerObservation:
    def __init__(self, run_dir: Path, visit_index: int, *, heartbeat_seconds=1.0):
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / 'trainer-observed.json'
        self.interval = heartbeat_seconds
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.enabled = True
        self.started = time.monotonic()
        self.step_started = None
        try:
            pointer = json.loads((self.run_dir / 'bamf-state.json').read_text())
            run_id, manifest = pointer.get('run_id'), pointer.get('manifest_sha256')
        except (OSError, ValueError, AttributeError):
            run_id = manifest = None
        self.record = dict(
            observation_id=str(uuid.uuid4()), revision=0, process_id=os.getpid(),
            run_id=run_id, parent_manifest_sha256=manifest, visit_index=visit_index,
            observed_at=None, elapsed_ms=None, capability_id=None, phase='PREPARING',
            outcome='RUNNING', candidate_optimizer_step=None, candidate_step=None,
            candidate_horizon=None, retention_completed=None, retention_total=None,
            retention_subject=None, retention_role=None, cpu_seconds=None,
            retention_evaluated_capability_count=None,
            retention_protection_plan_sha256=None,
            retention_broad_certification_trigger=None,
            peak_rss_bytes=None, disk_free_bytes=None, error_code=None,
            error_detail=None, candidate_steps=[], visit_evidence=None,
            generated_grade_evidence=None, retention_stage_timings=[],
            learning_health=None,
            **{name: None for name in PERFORMANCE_FIELDS},
            **{name: None for name in RETENTION_PROFILE_FIELDS})
        self.visits = []
        self.learning_health_by_capability = {}
        try:
            with self.path.open('rb') as stream:
                raw = stream.read(MAX_SNAPSHOT_BYTES + 1)
            data = json.loads(raw) if len(raw) <= MAX_SNAPSHOT_BYTES else {}
            if (data.get('schema') in {LEGACY_SCHEMA, LEGACY_SCHEMA_V2,
                                       LEGACY_SCHEMA_V3, LEGACY_SCHEMA_V4,
                                       LEGACY_SCHEMA_V5, SCHEMA}
                    and isinstance(data.get('visits'), list)
                    and all(isinstance(item, dict) for item in data['visits'])):
                self.visits = data['visits'][-7:]
                if self.visits and self.visits[-1].get('run_id') != run_id:
                    # Reused filesystem does not grant another run's trajectory.
                    self.visits = []
                    self.learning_health_by_capability = {}
        except (OSError, ValueError, AttributeError):
            pass
        self.thread = threading.Thread(target=self._heartbeat, daemon=True)

    def __enter__(self):
        self.update()
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop.set()
        self.thread.join()
        if exc_type is not None:
            error_code, error_detail = _exception_fields(exc_type, exc)
            self.update(error_code=error_code, error_detail=error_detail)
            self.finish('INTERRUPTED')
        elif self.record['outcome'] == 'RUNNING':
            self.update(
                error_code='UNFINISHED_VISIT',
                error_detail='Visit exited without a terminal operator outcome')
            self.finish('INTERRUPTED')
        return False

    def _heartbeat(self):
        while not self.stop.wait(self.interval):
            self.update()

    def update(self, **fields):
        with self.lock:
            if not self.enabled:
                return
            scorecard = fields.pop('retention_scorecard', None)
            if scorecard is not None:
                from .evidence_projection import merge_retention_scorecard
                current = self.record.get('visit_evidence') or {
                    'schema': 'bilqis.bamf.visit-evidence/v1', 'state': 'PARTIAL'}
                self.record['visit_evidence'] = merge_retention_scorecard(
                    current, scorecard)
            timing = fields.pop('retention_stage_timing', None)
            if timing is not None:
                self.record.setdefault('retention_stage_timings', []).append(timing)
                seconds = timing.get('wall_seconds') if isinstance(timing, dict) else None
                subject = timing.get('subject') if isinstance(timing, dict) else None
                target = (self.record.get('visit_evidence') or {}).get('capability_id')
                if type(seconds) in (int, float) and seconds >= 0:
                    field = ('target_evaluation_wall_seconds' if target is not None
                             and subject == target else 'protected_retention_wall_seconds')
                    self.record[field] = float(self.record.get(field) or 0.0) + float(seconds)
            self.record.update(fields)
            health = fields.get('learning_health')
            if isinstance(health, dict) and health.get('state') == 'MEASURED':
                capability = health.get('capability_id')
                if isinstance(capability, str) and capability:
                    self.learning_health_by_capability.pop(capability, None)
                    self.learning_health_by_capability[capability] = health
                    while len(self.learning_health_by_capability) > LEARNING_HISTORY_LIMIT:
                        self.learning_health_by_capability.pop(
                            next(iter(self.learning_health_by_capability)))
            if (self.step_started is not None
                    and self.record.get('phase') == 'TRAINING'):
                self.record['candidate_step_wall_seconds'] = max(
                    0.0, time.perf_counter() - self.step_started)
            self.record['revision'] += 1
            self.record['observed_at'] = int(time.time() * 1000)
            self.record['elapsed_ms'] = int((time.monotonic() - self.started) * 1000)
            try:
                usage = resource.getrusage(resource.RUSAGE_SELF)
                self.record['cpu_seconds'] = usage.ru_utime + usage.ru_stime
                self.record['peak_rss_bytes'] = int(usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024))
            except (OSError, ValueError):
                pass
            try:
                self.record['disk_free_bytes'] = shutil.disk_usage(self.run_dir).free
            except OSError:
                pass
            self._persist_snapshot()

    def _persist_snapshot(self):
        temporary = None
        try:
            payload = json.dumps({'schema': SCHEMA,
                                  'learning_health_run_id': self.record['run_id'],
                                  'visits': [*self.visits, self.record],
                                  'learning_health_by_capability': self.learning_health_by_capability},
                                 allow_nan=False).encode()
            # Preserve the established recent-visit window before
            # expendable per-capability summary history.
            while len(payload) > MAX_SNAPSHOT_BYTES and self.learning_health_by_capability:
                self.learning_health_by_capability.pop(
                    next(iter(self.learning_health_by_capability)))
                payload = json.dumps({'schema': SCHEMA,
                                      'learning_health_run_id': self.record['run_id'],
                                      'visits': [*self.visits, self.record],
                                      'learning_health_by_capability': self.learning_health_by_capability},
                                     allow_nan=False).encode()
            while len(payload) > MAX_SNAPSHOT_BYTES and self.visits:
                self.visits.pop(0)
                payload = json.dumps({'schema': SCHEMA,
                                      'learning_health_run_id': self.record['run_id'],
                                      'visits': [*self.visits, self.record],
                                      'learning_health_by_capability': self.learning_health_by_capability},
                                     allow_nan=False).encode()
            # Live telemetry must degrade in detail before it disappears entirely.
            # A fully populated candidate-step history can approach the snapshot
            # byte ceiling.  Preserve the newest completed steps and the active
            # visit itself instead of permanently disabling observation when the
            # current record alone no longer fits beside older detail.
            steps = self.record.get('candidate_steps')
            while (len(payload) > MAX_SNAPSHOT_BYTES
                   and isinstance(steps, list) and len(steps) > 1):
                steps.pop(0)
                payload = json.dumps(
                    {'schema': SCHEMA,
                     'learning_health_run_id': self.record['run_id'],
                     'visits': [*self.visits, self.record],
                     'learning_health_by_capability': self.learning_health_by_capability},
                    allow_nan=False).encode()
            while len(payload) > MAX_SNAPSHOT_BYTES and self.learning_health_by_capability:
                self.learning_health_by_capability.pop(
                    next(iter(self.learning_health_by_capability)))
                payload = json.dumps(
                    {'schema': SCHEMA,
                     'learning_health_run_id': self.record['run_id'],
                     'visits': [*self.visits, self.record],
                     'learning_health_by_capability': self.learning_health_by_capability},
                    allow_nan=False).encode()
            if len(payload) > MAX_SNAPSHOT_BYTES:
                # Do not permanently blind Mission Control.  A later phase
                # update may reduce optional detail enough to fit, and the
                # next heartbeat should be allowed to retry.
                return
            fd, temporary = tempfile.mkstemp(prefix='.trainer-observed-', dir=self.run_dir)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(payload)
            os.replace(temporary, self.path)
        except OSError:
            # Filesystem failures can be transient.  Observation is
            # explicitly best-effort, so retry on the next heartbeat rather
            # than turning one failed write into a visit-long blackout.
            pass
        except (ValueError, TypeError):
            # Deterministic serialization failures cannot heal without a
            # producer-side field change; avoid a tight retry loop.
            self.enabled = False
        finally:
            if temporary and os.path.exists(temporary):
                try:
                    os.unlink(temporary)
                except OSError:
                    pass

    def stage(self, **fields):
        """Update best-effort fields without forcing another synchronous write."""
        with self.lock:
            if self.enabled:
                self.record.update(fields)

    def begin_step(self, candidate_step: int, candidate_optimizer_step: int):
        """Expose one active step immediately; completed history stays immutable."""
        with self.lock:
            if not self.enabled:
                return
            self.step_started = time.perf_counter()
            self.record.update(
                candidate_step=candidate_step,
                candidate_optimizer_step=candidate_optimizer_step,
                **{name: None for name in PERFORMANCE_FIELDS
                   if name not in VISIT_PERFORMANCE_FIELDS})
        self.update()

    def complete_step(self, **fields):
        """Freeze one completed step for click-through inspection, then publish it."""
        with self.lock:
            if not self.enabled:
                return
            self.record.update(fields)
            step_fields = [
                name for name in PERFORMANCE_FIELDS
                if name not in {'retention_wall_seconds',
                                'evidence_finalization_wall_seconds',
                                'publishing_wall_seconds'}]
            snapshot = {
                key: self.record.get(key)
                for key in ('candidate_step', 'candidate_optimizer_step', *step_fields)
            }
            history = [
                item for item in self.record.get('candidate_steps', [])
                if item.get('candidate_step') != snapshot['candidate_step']
            ]
            history.append(snapshot)
            self.record['candidate_steps'] = history[-STEP_HISTORY_LIMIT:]
            self.step_started = None
        self.update()

    def bind_parent(self, parent):
        try:
            pointer = json.loads((self.run_dir / 'bamf-state.json').read_text())
            if pointer.get('run_id') != parent.run_id or pointer.get('generation') != parent.generation:
                self.update(run_id=None, parent_manifest_sha256=None)
                return
            self.update(run_id=parent.run_id, parent_manifest_sha256=pointer['manifest_sha256'],
                        candidate_optimizer_step=parent.retained_state.optimizer_step)
        except (OSError, ValueError, KeyError, AttributeError, TypeError):
            self.update(run_id=None, parent_manifest_sha256=None)

    def finish(self, outcome):
        self.update(phase='COMPLETED', outcome=outcome)


def emit(observer, **fields):
    """Best-effort observation must never change an authority decision."""
    if observer is not None:
        try:
            observer(fields)
        except Exception:
            pass
