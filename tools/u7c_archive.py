"""Replay frozen U7C without modifying its frozen trainer or persisted traces.

Canonical archive JSON sorts object keys. Actual offered order remains in the
saved serialized native HTTP request, whose SHA-256 is authenticated here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from bilqis_u7c import run


def replay(path=run.RUN):
    original = run.verify_trace
    def verify_from_wire(trace):
        wire = trace["serialized_request"]
        if hashlib.sha256(wire.encode()).hexdigest() != trace["request_sha256"]:
            raise ValueError("native Kev actual request bytes changed")
        actual = json.loads(wire)
        if actual != trace["payload"]:
            raise ValueError("native Kev archived payload diverges from transmitted bytes")
        trace["payload"] = actual
        return original(trace)
    started = time.perf_counter()
    run.verify_trace = verify_from_wire
    try:
        receipt = run.replay(path)
    finally:
        run.verify_trace = original
    run.write(path/"archive-replay-receipt.json", {
        "status": "VERIFIED_LOSSLESS_REQUEST_ORDER",
        "original_direct_replay_observation": "ValueError teacher actual option order: canonical JSON object sorting",
        "archive_adaptation": "recover native option order exclusively from saved serialized_request bytes; no dataset, model, teacher, gradient or source changes",
        "code_sha256": run.sha(Path(__file__)), "native_calls_reexecuted": 0,
        "wall_seconds": time.perf_counter()-started,
        "frozen_trainer_source_unchanged": True, "replay": receipt})
    return receipt


if __name__ == "__main__":
    print(json.dumps(replay(),sort_keys=True))
