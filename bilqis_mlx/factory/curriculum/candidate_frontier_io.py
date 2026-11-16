"""Filesystem parsing and provenance checks for candidate frontier releases."""
from __future__ import annotations

from dataclasses import asdict
import csv
import hashlib
import json
from pathlib import Path

from .candidate_frontier import (
    BUILDER_SCHEMA, SCHEMA, _INPUT_FILES, _MANIFEST_INVALID, _OUTPUT_FILES,
    Candidate, CandidateFrontierRelease, CandidatePrerequisite, CandidateSense,
    _digest, _digest_value, _required,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _aggregate(files: dict[str, str]) -> str:
    return hashlib.sha256("".join(
        f"{name}:{digest}\n" for name, digest in sorted(files.items())).encode()).hexdigest()


def candidate_frontier_source_identity(
        source_dir: str | Path, builder_path: str | Path) -> tuple[str, str]:
    """Return the exact pinned builder + canonical source-input identity."""
    source_dir, builder_path = Path(source_dir), Path(builder_path)
    builder_sha256 = _sha256(builder_path)
    input_files = {name: _sha256(source_dir / name) for name in _INPUT_FILES}
    return builder_sha256, _aggregate(input_files)


def _read_csv(path: Path) -> tuple[dict[str, str], ...]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            return tuple(csv.DictReader(handle))
    except (OSError, csv.Error) as exc:
        raise ValueError("CANDIDATE_FRONTIER_ARTIFACT_UNREADABLE:" + path.name) from exc


def _validate_builder_manifest(
    artifact_dir: Path, source_dir: Path, expected_builder_sha256: str,
) -> dict:
    _digest_value(expected_builder_sha256, "CANDIDATE_FRONTIER_BUILDER_DIGEST_INVALID")
    try:
        manifest = json.loads((artifact_dir / "frontier_manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("CANDIDATE_FRONTIER_MANIFEST_UNREADABLE") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != BUILDER_SCHEMA:
        raise ValueError(_MANIFEST_INVALID)
    if manifest.get("builder_file_sha256") != expected_builder_sha256:
        raise ValueError("CANDIDATE_FRONTIER_BUILDER_STALE")
    for names, base, label in ((_INPUT_FILES, source_dir, "INPUT"),
                               (_OUTPUT_FILES, artifact_dir, "OUTPUT")):
        field = "input_files" if label == "INPUT" else "output_files"
        expected = manifest.get(field)
        if not isinstance(expected, dict) or set(expected) != set(names):
            raise ValueError("CANDIDATE_FRONTIER_MANIFEST_" + label + "_INVALID")
        actual = {name: _sha256(base / name) for name in names}
        if actual != expected:
            raise ValueError("CANDIDATE_FRONTIER_" + label + "_STALE")
        digest_field = "input_digest" if label == "INPUT" else "output_digest"
        if manifest.get(digest_field) != _aggregate(actual):
            raise ValueError("CANDIDATE_FRONTIER_" + label + "_DIGEST_INVALID")
    return manifest


def _candidate(row: dict[str, str]) -> Candidate:
    tier = _required(row.get("priority_tier"), "CANDIDATE_FRONTIER_CANDIDATE_INVALID")
    readiness = ["FACTORY_ADMISSION_REQUIRED", _required(
        row.get("source_readiness"), "CANDIDATE_FRONTIER_CANDIDATE_INVALID")]
    if not row.get("source_evidence_ids", "").strip():
        readiness.append("SOURCE_EVIDENCE_REFERENCE_REQUIRED")
    if row.get("modality_gate", "").strip():
        readiness.append("ANSWER_WORLD_IMPLEMENTATION_REQUIRED")
    return Candidate(
        candidate_id=_required(row.get("candidate_id"), "CANDIDATE_FRONTIER_CANDIDATE_INVALID"),
        priority_tier=tier,
        proposed_capability_id=row.get("working_capability", "").strip(),
        tranche=row.get("proposed_grade", "").strip(),
        root_form=_required(row.get("root_form"), "CANDIDATE_FRONTIER_CANDIDATE_INVALID"),
        root_id=_required(row.get("lexicon_root_id"), "CANDIDATE_FRONTIER_CANDIDATE_INVALID"),
        target_sense_id=row.get("target_sense_id", "").strip(),
        source_evidence_ids=tuple(item.strip() for item in row.get(
            "source_evidence_ids", "").split("|") if item.strip()),
        prerequisites=tuple(CandidatePrerequisite(item) for item in (
            value.strip() for value in row.get("prerequisites", "").split(";"))
            if item and item != "TO_BE_RESOLVED_FROM_MASTERED_CLOSURE"),
        rationale=_required(row.get("why_now"), "CANDIDATE_FRONTIER_CANDIDATE_INVALID"),
        downstream_unlocks=_required(row.get("downstream_unlocks"), "CANDIDATE_FRONTIER_CANDIDATE_INVALID"),
        answer_requirement=_required(row.get("answer_family"), "CANDIDATE_FRONTIER_CANDIDATE_INVALID"),
        world_requirement=_required(row.get("minimal_world_state"), "CANDIDATE_FRONTIER_CANDIDATE_INVALID"),
        modality_requirement=row.get("modality_gate", "").strip(),
        readiness_debt=tuple(readiness),
        advisory_anchors=tuple(item.strip() for item in row.get(
            "existing_abi_anchors", "").split("|") if item.strip()),
        disposition=_required(row.get("disposition"), "CANDIDATE_FRONTIER_CANDIDATE_INVALID"),
    )


def load_candidate_frontier(
    artifact_dir: str | Path, source_dir: str | Path, *, expected_builder_sha256: str,
) -> CandidateFrontierRelease:
    artifact_dir, source_dir = Path(artifact_dir), Path(source_dir)
    generated = _validate_builder_manifest(artifact_dir, source_dir, expected_builder_sha256)
    candidates = tuple(_candidate(row) for row in _read_csv(artifact_dir / "candidate_pool.csv"))
    senses = tuple(CandidateSense(
        sense_id=_required(row.get("lexicon_sense_id"), "CANDIDATE_FRONTIER_SENSE_IDENTITY_INVALID"),
        root_id=_required(row.get("lexicon_root_id"), "CANDIDATE_FRONTIER_SENSE_IDENTITY_INVALID"),
        root_form=_required(row.get("root_form"), "CANDIDATE_FRONTIER_SENSE_IDENTITY_INVALID"),
        stem=row.get("stem", ""), specification=row.get("specification", ""),
        source_wording=_required(row.get("sense_summary"), "CANDIDATE_FRONTIER_SENSE_IDENTITY_INVALID"),
        source_text_sha256=_digest_value(row.get("source_text_sha256"),
                                         "CANDIDATE_FRONTIER_SENSE_TEXT_DIGEST_INVALID"),
        semantic_disposition=_required(row.get("semantic_disposition"),
                                       "CANDIDATE_FRONTIER_SENSE_IDENTITY_INVALID"),
        selected_target_capability=row.get("selected_target_capability", ""),
    ) for row in _read_csv(artifact_dir / "sense_candidate_pool.csv"))
    source_senses = {row["lexicon_sense_id"]: row for row in _read_csv(
        source_dir / "lexicon_root_senses.csv")}
    source_evidence = {row["lexicon_evidence_id"]: row for row in _read_csv(
        source_dir / "lexicon_root_evidence.csv")}
    if {item.sense_id for item in senses} != set(source_senses):
        raise ValueError("CANDIDATE_FRONTIER_SENSE_INVENTORY_MISMATCH")
    source_roots = {(row["lexicon_root_id"], row["root_form_raw"])
                    for row in _read_csv(source_dir / "lexicon_roots.csv")}
    if any((item.root_id, item.root_form) not in source_roots for item in candidates):
        raise ValueError("CANDIDATE_FRONTIER_CANDIDATE_SOURCE_MISMATCH")
    for sense in senses:
        source = source_senses.get(sense.sense_id)
        if source is None or any((source["lexicon_root_id"] != sense.root_id,
                                  source["root_form_raw"] != sense.root_form,
                                  source["stem"] != sense.stem,
                                  source["specification"] != sense.specification,
                                  source["sense_summary"] != sense.source_wording,
                                  source["source_text_sha256"] != sense.source_text_sha256)):
            raise ValueError("CANDIDATE_FRONTIER_SENSE_SOURCE_MISMATCH")
    if any(any(source_evidence.get(evidence_id, {}).get("root_form_raw") != item.root_form
               for evidence_id in item.source_evidence_ids) for item in candidates):
        raise ValueError("CANDIDATE_FRONTIER_EVIDENCE_REFERENCE_INVALID")
    manifest = {
        "schema": SCHEMA,
        "builder_sha256": generated["builder_file_sha256"],
        "input_digest": generated["input_digest"],
        "output_digest": generated["output_digest"],
        "candidates": [asdict(item) for item in candidates],
        "senses": [asdict(item) for item in senses],
    }
    release = CandidateFrontierRelease(
        manifest["builder_sha256"], manifest["input_digest"], manifest["output_digest"],
        candidates, senses, _digest(manifest))
    release.verify()
    return release
