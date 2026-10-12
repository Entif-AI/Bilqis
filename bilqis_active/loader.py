"""Fail-closed resolver for Bilqis's ONE retained cumulative neural learner.

Do not fall back to random student initialization or stale U6 checkpoints.
An unavailable custodied model is a missing artifact, not a reason to forget
everything the student has learned.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import state_hash
from bilqis_development.continuation import load

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/development/ACTIVE_LEARNER.json"
VERSION = "bilqis.active-learner/v1"


def locate(manifest=MANIFEST):
    document = json.loads(Path(manifest).read_text())
    if (document.get("schema") != VERSION or
        document.get("status") != "CONTINUING_STUDENT" or
        not document.get("no_silent_fallback")):
        raise ValueError("BAD_ACTIVE_LEARNER_MANIFEST")
    filename = document.get("checkpoint_file")
    if not isinstance(filename, str) or Path(filename).name != filename or filename.startswith("."):
        raise ValueError("INVALID_CUSTODIED_FILENAME")
    dirname = os.environ.get("BILQIS_CUSTODY_DIR")
    custody = Path(dirname).expanduser() if dirname else Path.home() / "Code" / document["checkpoint_custody"]
    checkpoint = custody.resolve() / filename
    if not checkpoint.is_file():
        raise FileNotFoundError(f"ACTIVELY_LEARNED_CHECKPOINT_UNAVAILABLE: {checkpoint}")
    if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != document["checkpoint_sha256"]:
        raise ValueError("ACTIVE_CHECKPOINT_CUSTODY_HASH_MISMATCH")
    return checkpoint, document


def load_active(manifest=MANIFEST):
    checkpoint, document = locate(manifest)
    model, optimizer, payload = load(checkpoint)
    if (state_hash(model) != document["model_state_sha256"] or
        optimizer_receipt(optimizer)["state_sha256"] != document["optimizer_state_sha256"] or
        optimizer_receipt(optimizer)["steps"] != [document["optimizer_step"]] or
        len(payload["graph"]["tokens"]) != document["semantic_token_count"] or
        model.config.vocab_size != document["semantic_token_count"]):
        raise ValueError("ACTIVE_LEARNER_NEURAL_OR_SEMANTIC_STATE_MISMATCH")
    return model, optimizer, payload, document
