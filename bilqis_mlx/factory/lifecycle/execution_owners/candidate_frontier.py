"""Read the source-grounded Ithkuil research frontier without admitting it.

The builder lives under ``lib/ithkuil``.  This factory owner deliberately only
reads its hash-bound artifacts: candidate provenance can inform a later JIT
proposal, but cannot construct a course, release, grade, or teaching work.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json


SCHEMA = "bilqis.mlx.candidate-frontier-release/v1"
BUILDER_SCHEMA = "bilqis.ithkuil.frontier-manifest/v1"
_MANIFEST_INVALID = "CANDIDATE_FRONTIER_MANIFEST_INVALID"
_INPUT_FILES = (
    "lexicon_roots.csv", "lexicon_root_senses.csv", "lexicon_root_evidence.csv",
    "bilqis_ithkuil_crosswalk.csv",
)
_OUTPUT_FILES = (
    "candidate_pool.csv", "grade_map.csv", "sense_candidate_pool.csv",
    "source_inventory.csv", "deferred_codec.csv", "grade_rationale.csv",
    "frontier_plan.json",
)


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode()).hexdigest()


def _required(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(code)
    return value


def _digest_value(value: object, code: str) -> str:
    value = _required(value, code)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(code)
    return value


class PrerequisiteStatus(str, Enum):
    """A frontier dependency is advisory until normal factory admission."""

    HYPOTHESIS = "HYPOTHESIS"
    SOURCE_SUPPORTED = "SOURCE_SUPPORTED"
    CONSTRUCTION_WITNESSED = "CONSTRUCTION_WITNESSED"
    ADMITTED_EXECUTABLE = "ADMITTED_EXECUTABLE"


@dataclass(frozen=True)
class CandidatePrerequisite:
    capability_id: str
    status: PrerequisiteStatus = PrerequisiteStatus.HYPOTHESIS

    def __post_init__(self) -> None:
        _required(self.capability_id, "CANDIDATE_FRONTIER_PREREQUISITE_INVALID")
        if not isinstance(self.status, PrerequisiteStatus):
            raise ValueError("CANDIDATE_FRONTIER_PREREQUISITE_STATUS_INVALID")


@dataclass(frozen=True)
class CandidateSense:
    sense_id: str
    root_id: str
    root_form: str
    stem: str
    specification: str
    source_wording: str
    source_text_sha256: str
    semantic_disposition: str
    selected_target_capability: str = ""

    def __post_init__(self) -> None:
        for value in (self.sense_id, self.root_id, self.root_form,
                      self.source_wording, self.semantic_disposition):
            _required(value, "CANDIDATE_FRONTIER_SENSE_IDENTITY_INVALID")
        _digest_value(self.source_text_sha256,
                      "CANDIDATE_FRONTIER_SENSE_TEXT_DIGEST_INVALID")


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    priority_tier: str
    proposed_capability_id: str
    tranche: str
    root_form: str
    root_id: str
    target_sense_id: str
    source_evidence_ids: tuple[str, ...]
    prerequisites: tuple[CandidatePrerequisite, ...]
    rationale: str
    downstream_unlocks: str
    answer_requirement: str
    world_requirement: str
    modality_requirement: str
    readiness_debt: tuple[str, ...]
    advisory_anchors: tuple[str, ...]
    disposition: str

    def __post_init__(self) -> None:
        for value in (self.candidate_id, self.priority_tier, self.root_form,
                      self.root_id, self.rationale, self.downstream_unlocks,
                      self.answer_requirement, self.world_requirement,
                      self.disposition):
            _required(value, "CANDIDATE_FRONTIER_CANDIDATE_INVALID")
        if (any(not isinstance(item, str) or not item
                    for item in self.source_evidence_ids) or
                len(set(self.source_evidence_ids)) != len(self.source_evidence_ids) or
                any(not isinstance(item, CandidatePrerequisite)
                    for item in self.prerequisites) or
                any(item.status is not PrerequisiteStatus.HYPOTHESIS
                    for item in self.prerequisites) or
                len({item.capability_id for item in self.prerequisites}) !=
                len(self.prerequisites) or
                len(set(self.readiness_debt)) != len(self.readiness_debt) or
                any(not isinstance(item, str) or not item
                    for item in self.readiness_debt) or
                len(set(self.advisory_anchors)) != len(self.advisory_anchors) or
                any(not isinstance(item, str) or not item
                    for item in self.advisory_anchors)):
            raise ValueError("CANDIDATE_FRONTIER_CANDIDATE_INVALID")
        if self.priority_tier == "CORE_D_O":
            if (not self.proposed_capability_id or not self.tranche or
                    not self.target_sense_id or
                    self.disposition != "PROPOSED_NOT_ADMITTED" or
                    "FACTORY_ADMISSION_REQUIRED" not in self.readiness_debt):
                raise ValueError("CANDIDATE_FRONTIER_SELECTED_TARGET_INVALID")
        elif self.priority_tier == "NEXT_96":
            if (self.proposed_capability_id or self.tranche or self.target_sense_id or
                    self.disposition != "CANDIDATE_RESERVE" or
                    "FACTORY_ADMISSION_REQUIRED" not in self.readiness_debt):
                raise ValueError("CANDIDATE_FRONTIER_RESERVE_INVALID")
        else:
            raise ValueError("CANDIDATE_FRONTIER_PRIORITY_INVALID")


@dataclass(frozen=True)
class CandidateFrontierRelease:
    """Content-addressed, non-admitted view of the generated research frontier."""

    builder_sha256: str
    input_digest: str
    output_digest: str
    candidates: tuple[Candidate, ...]
    senses: tuple[CandidateSense, ...]
    release_sha256: str

    def __post_init__(self) -> None:
        for value in (self.builder_sha256, self.input_digest, self.output_digest,
                      self.release_sha256):
            _digest_value(value, "CANDIDATE_FRONTIER_RELEASE_DIGEST_INVALID")
        if (any(not isinstance(item, Candidate) for item in self.candidates) or
                len({item.candidate_id for item in self.candidates}) != len(self.candidates) or
                any(not isinstance(item, CandidateSense) for item in self.senses) or
                len({item.sense_id for item in self.senses}) != len(self.senses)):
            raise ValueError("CANDIDATE_FRONTIER_RELEASE_INVALID")

    def manifest(self) -> dict:
        return {
            "schema": SCHEMA,
            "builder_sha256": self.builder_sha256,
            "input_digest": self.input_digest,
            "output_digest": self.output_digest,
            "candidates": [asdict(item) for item in self.candidates],
            "senses": [asdict(item) for item in self.senses],
        }

    def expected_digest(self) -> str:
        return _digest(self.manifest())

    def verify(self) -> None:
        if self.release_sha256 != self.expected_digest():
            raise ValueError("CANDIDATE_FRONTIER_RELEASE_DIGEST_MISMATCH")
        selected = tuple(item for item in self.candidates if item.priority_tier == "CORE_D_O")
        reserve = tuple(item for item in self.candidates if item.priority_tier == "NEXT_96")
        if (not self.senses or not selected or not reserve or
                {item.root_form for item in selected} &
                {item.root_form for item in reserve}):
            raise ValueError("CANDIDATE_FRONTIER_PROVENANCE_POOL_INVALID")
        senses = {item.sense_id: item for item in self.senses}
        if (len({item.target_sense_id for item in selected}) != len(selected) or
                any(item.target_sense_id not in senses for item in selected) or
                any(senses[item.target_sense_id].selected_target_capability !=
                    item.proposed_capability_id or
                    senses[item.target_sense_id].root_id != item.root_id or
                    senses[item.target_sense_id].root_form != item.root_form
                    for item in selected)):
            raise ValueError("CANDIDATE_FRONTIER_SELECTED_SENSE_LINK_INVALID")

    @classmethod
    def from_manifest(cls, manifest: dict, release_sha256: str) -> "CandidateFrontierRelease":
        if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
            raise ValueError(_MANIFEST_INVALID)
        try:
            candidates = tuple(Candidate(
                **{**item, "source_evidence_ids": tuple(item["source_evidence_ids"]),
                   "prerequisites": tuple(CandidatePrerequisite(
                       capability_id=edge["capability_id"],
                       status=PrerequisiteStatus(edge["status"]))
                       for edge in item["prerequisites"]),
                   "readiness_debt": tuple(item["readiness_debt"]),
                   "advisory_anchors": tuple(item["advisory_anchors"])} )
                for item in manifest["candidates"])
            senses = tuple(CandidateSense(**item) for item in manifest["senses"])
            release = cls(manifest["builder_sha256"], manifest["input_digest"],
                          manifest["output_digest"], candidates, senses, release_sha256)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(_MANIFEST_INVALID) from exc
        release.verify()
        return release


def load_candidate_frontier(
    artifact_dir, source_dir, *, expected_builder_sha256: str,
) -> CandidateFrontierRelease:
    """Load and verify a non-admitted source frontier generated by the builder."""
    from .candidate_frontier_io import load_candidate_frontier as load
    return load(artifact_dir, source_dir, expected_builder_sha256=expected_builder_sha256)


def candidate_frontier_source_identity(source_dir, builder_path) -> tuple[str, str]:
    """Return the canonical builder/source identity before any cache is trusted."""
    from .candidate_frontier_io import candidate_frontier_source_identity as identity
    return identity(source_dir, builder_path)
