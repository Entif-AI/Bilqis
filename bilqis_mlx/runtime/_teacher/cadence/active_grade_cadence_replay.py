"""Authenticated terminal-attempt replay for #1333 cadence recovery."""
from __future__ import annotations

import json
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _canonical(value) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False)


def _accepted_chain(run_dir: Path):
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest,
        accepted_generation,
        parent_acceptance_anchor_from_manifest,
    )

    root = Path(run_dir)
    pointer, student = accepted_generation(root / "bamf-state.json")
    manifest = pointer["manifest_sha256"]
    acceptance = pointer["acceptance_sha256"]
    result = {}
    while True:
        accepted_binding_for_manifest(
            root, manifest, student,
            expected_acceptance_sha256=acceptance)
        result[student.generation] = (student, manifest)
        if student.generation == 0:
            break
        parent_manifest = student.parent_manifest_sha256
        parent_acceptance = parent_acceptance_anchor_from_manifest(root, manifest)
        if parent_manifest is None or parent_acceptance is None:
            break
        student = load_bamf_bundle(
            root / "bamf-bundles" / parent_manifest,
            expected_manifest_sha256=parent_manifest)
        manifest, acceptance = parent_manifest, parent_acceptance
    return result


def _accepted_cadence_events(chain):
    events = {}
    for generation, (student, _manifest) in chain.items():
        parent = chain.get(generation - 1)
        for event in student.outbox:
            cadence = event.get("cadence") if isinstance(event, dict) else None
            if event.get("event") != "BAMF_C16_3_ACCEPTED" or not isinstance(cadence, dict):
                continue
            if (generation < 1 or parent is None
                    or event.get("parent_generation") != generation - 1
                    or event.get("accepted_manifest_sha256") != parent[1]
                    or event.get("capability") not in cadence.get(
                        "authorized_capability_ids", ())):
                _invalid("BAMF_ACTIVE_GRADE_CADENCE_ACCEPTED_EVENT_INVALID")
            events[_canonical(event)] = (generation, event)
    return events


def authenticated_cadence_attempts(run_dir: Path):
    """Return terminal cadence attempts in durable event order.

    Accepted events are authenticated by immutable B13 ancestry/outboxes. Rejected
    events are authenticated by the existing C16.3 rejection authority + receipt.
    An accepted outbox event missing from events.jsonl after a crash is appended as
    the final durable attempt because B13 publication already committed it.
    """
    root = Path(run_dir)
    if not (root / "bamf-state.json").exists():
        return ()
    chain = _accepted_chain(root)
    accepted = _accepted_cadence_events(chain)
    seen_accepted = set()
    attempts = []
    journal = root / "events.jsonl"
    if journal.exists():
        if journal.is_symlink() or not journal.is_file():
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_EVENT_LEDGER_UNSAFE")
        with journal.open(encoding="utf-8") as stream:
            for raw in stream:
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    _invalid("BAMF_ACTIVE_GRADE_CADENCE_EVENT_LEDGER_INVALID")
                if not isinstance(event, dict):
                    continue
                if event.get("event") == "BAMF_C16_3_ACCEPTED" and isinstance(
                        event.get("cadence"), dict):
                    key = _canonical(event)
                    if key not in accepted:
                        _invalid("BAMF_ACTIVE_GRADE_CADENCE_ACCEPTED_EVENT_INVALID")
                    if key not in seen_accepted:
                        seen_accepted.add(key)
                        attempts.append((event["cadence"], event["capability"]))
                    continue
                evidence = event.get("evidence")
                cadence = evidence.get("cadence") if isinstance(evidence, dict) else None
                if event.get("event") != "BAMF_CANDIDATE_REJECTED" or not isinstance(
                        cadence, dict):
                    continue
                generation = event.get("generation")
                parent = chain.get(generation)
                if parent is None:
                    _invalid("BAMF_ACTIVE_GRADE_CADENCE_REJECTION_GENERATION_INVALID")
                from .priority_rejection_replay import authenticated_rejection_event
                if not authenticated_rejection_event(event, parent[0], parent[1]):
                    _invalid("BAMF_ACTIVE_GRADE_CADENCE_REJECTION_EVENT_INVALID")
                capability = evidence.get("capability")
                if capability not in cadence.get("authorized_capability_ids", ()):
                    _invalid("BAMF_ACTIVE_GRADE_CADENCE_REJECTION_EVENT_INVALID")
                attempts.append((cadence, capability))
    for key, (generation, event) in sorted(
            accepted.items(), key=lambda item: item[1][0]):
        if key not in seen_accepted:
            attempts.append((event["cadence"], event["capability"]))
    return tuple(attempts)


__all__ = ("authenticated_cadence_attempts",)
