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

SCHEMA = 'bilqis.bamf.trainer-observed/v1'


class TrainerObservation:
    def __init__(self, run_dir: Path, visit_index: int, *, heartbeat_seconds=1.0):
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / 'trainer-observed.json'
        self.interval = heartbeat_seconds
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.enabled = True
        self.started = time.monotonic()
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
            peak_rss_bytes=None, disk_free_bytes=None)
        self.visits = []
        try:
            with self.path.open('rb') as stream:
                raw = stream.read(65537)
            data = json.loads(raw) if len(raw) <= 65536 else {}
            if (data.get('schema') == SCHEMA and isinstance(data.get('visits'), list)
                    and all(isinstance(item, dict) for item in data['visits'])):
                self.visits = data['visits'][-7:]
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
        if exc_type is not None or self.record['outcome'] == 'RUNNING':
            self.finish('INTERRUPTED')
        return False

    def _heartbeat(self):
        while not self.stop.wait(self.interval):
            self.update()

    def update(self, **fields):
        with self.lock:
            if not self.enabled:
                return
            self.record.update(fields)
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
            temporary = None
            try:
                payload = json.dumps({'schema': SCHEMA, 'visits': [*self.visits, self.record]},
                                     allow_nan=False).encode()
                while len(payload) > 65536 and self.visits:
                    self.visits.pop(0)
                    payload = json.dumps({'schema': SCHEMA, 'visits': [*self.visits, self.record]},
                                         allow_nan=False).encode()
                if len(payload) > 65536:
                    raise ValueError('observation exceeds bounded snapshot')
                fd, temporary = tempfile.mkstemp(prefix='.trainer-observed-', dir=self.run_dir)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(payload)
                os.replace(temporary, self.path)
            except (OSError, ValueError, TypeError):
                self.enabled = False
            finally:
                if temporary and os.path.exists(temporary):
                    try:
                        os.unlink(temporary)
                    except OSError:
                        pass

    def bind_parent(self, parent):
        try:
            pointer = json.loads((self.run_dir / 'bamf-state.json').read_text())
            if pointer.get('run_id') != parent.run_id or pointer.get('generation') != parent.generation:
                raise ValueError('accepted pointer changed')
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
