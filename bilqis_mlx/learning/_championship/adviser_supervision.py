"""Owner-issued bounded mentor influence over already lawful source targets."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning._championship.champion_confidence import MAX_INFLUENCE
from bilqis_mlx.learning._teacher_strategy.population import effective_policy_key
from bilqis_mlx.runtime.source_execution import source_content_digest


SCHEMA = "bilqis.mlx.championship-mentor-supervision/v1"
ROW_SCHEMA = "bilqis.mlx.championship-mentor-row/v1"
_ISSUER = object()


def _invalid(reason):
    ErrorBus.raise_(SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID, reason=reason)


def _text(value) -> bool:
    return isinstance(value, str) and bool(value)


@dataclass(frozen=True)
class MentorRowInfluence:
    row_id: str
    capability_id: str
    source_row_sha256: str
    influence: float
    direct_votes: int
    soup_votes: float
    direct_advisers: tuple[dict, ...]
    soup_advisers: tuple[dict, ...]
    schema_version: str = ROW_SCHEMA

    def __post_init__(self):
        if (self.schema_version != ROW_SCHEMA
                or not _text(self.row_id) or not _text(self.capability_id)
                or not isinstance(self.source_row_sha256, str)
                or len(self.source_row_sha256) != SHA256_HEX_LENGTH
                or not math.isfinite(self.influence)
                or not 0.0 <= self.influence <= MAX_INFLUENCE + 1e-12
                or type(self.direct_votes) is not int or self.direct_votes < 0
                or not math.isfinite(self.soup_votes) or self.soup_votes < 0.0
                or type(self.direct_advisers) is not tuple
                or type(self.soup_advisers) is not tuple
                or any(not isinstance(item, dict) for item in
                       (*self.direct_advisers, *self.soup_advisers))):
            _invalid("MENTOR_ROW_INFLUENCE_INVALID")

    def to_record(self) -> dict:
        return {
            "schema": self.schema_version,
            "row_id": self.row_id,
            "capability_id": self.capability_id,
            "source_row_sha256": self.source_row_sha256,
            "influence": self.influence,
            "direct_votes": self.direct_votes,
            "soup_votes": self.soup_votes,
            "direct_advisers": [dict(item) for item in self.direct_advisers],
            "soup_advisers": [dict(item) for item in self.soup_advisers],
        }


@dataclass(frozen=True, init=False)
class MentorSupervision:
    accepted_manifest_sha256: str
    championship_epoch_sha256: str
    teacher_policy: str
    policy_binding_sha256: str
    source_seed: int
    rows: tuple[MentorRowInfluence, ...]
    physical_inference_launches: int
    logical_direct_votes: int
    logical_soup_votes: float
    schema_version: str = SCHEMA
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("MENTOR_SUPERVISION_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self):
        row_ids = tuple(item.row_id for item in self.rows)
        if (getattr(self, "_issuance", None) is not _ISSUER
                or self.schema_version != SCHEMA
                or not isinstance(self.accepted_manifest_sha256, str)
                or len(self.accepted_manifest_sha256) != SHA256_HEX_LENGTH
                or not isinstance(self.championship_epoch_sha256, str)
                or len(self.championship_epoch_sha256) != SHA256_HEX_LENGTH
                or not _text(self.teacher_policy)
                or not isinstance(self.policy_binding_sha256, str)
                or len(self.policy_binding_sha256) != SHA256_HEX_LENGTH
                or type(self.source_seed) is not int
                or type(self.rows) is not tuple
                or any(type(item) is not MentorRowInfluence for item in self.rows)
                or len(set(row_ids)) != len(row_ids)
                or type(self.physical_inference_launches) is not int
                or self.physical_inference_launches < 0
                or type(self.logical_direct_votes) is not int
                or self.logical_direct_votes < 0
                or not math.isfinite(self.logical_soup_votes)
                or self.logical_soup_votes < 0.0):
            _invalid("MENTOR_SUPERVISION_INVALID")
        for item in self.rows:
            item.__post_init__()

    def influence_for(self, compiled) -> float:
        """Bind the bounded scalar to the exact compiled source row."""
        sources = getattr(compiled, "sources", ())
        if type(sources) is not tuple or len(sources) != 1:
            _invalid("MENTOR_SUPERVISION_COMPILED_ROW_REQUIRED")
        row = sources[0].source_row
        if not isinstance(row, dict) or not _text(row.get("id")):
            _invalid("MENTOR_SUPERVISION_SOURCE_ROW_INVALID")
        digest = source_content_digest((row,))
        matches = tuple(item for item in self.rows if item.row_id == row["id"])
        if len(matches) != 1 or matches[0].source_row_sha256 != digest:
            _invalid("MENTOR_SUPERVISION_SOURCE_ROW_DRIFT")
        return matches[0].influence

    def require_current(self, accepted_manifest_sha256: str,
                        championship_epoch_sha256: str, teacher_policy: str,
                        policy_binding_sha256: str, source_seed: int) -> None:
        if (self.accepted_manifest_sha256 != accepted_manifest_sha256
                or self.championship_epoch_sha256 != championship_epoch_sha256
                or self.teacher_policy != teacher_policy
                or self.policy_binding_sha256 != policy_binding_sha256
                or self.source_seed != source_seed):
            _invalid("MENTOR_SUPERVISION_CURRENTNESS_DRIFT")

    def require_evidence(self, mentors, guidance) -> None:
        if mentors != self.to_record() or guidance != self.guidance_record():
            _invalid("MENTOR_SUPERVISION_EVIDENCE_DRIFT")

    def to_record(self) -> dict:
        return {
            "schema": self.schema_version,
            "accepted_manifest_sha256": self.accepted_manifest_sha256,
            "championship_epoch_sha256": self.championship_epoch_sha256,
            "teacher_policy": self.teacher_policy,
            "policy_binding_sha256": self.policy_binding_sha256,
            "source_seed": self.source_seed,
            "physical_inference_launches": self.physical_inference_launches,
            "logical_direct_votes": self.logical_direct_votes,
            "logical_soup_votes": self.logical_soup_votes,
            "rows": [item.to_record() for item in self.rows],
        }

    def guidance_record(self) -> dict:
        return {
            "schema": "bilqis.mlx.championship-guidance/v1",
            "rows": [
                {"row_id": item.row_id, "influence": item.influence}
                for item in self.rows
            ],
        }


def mentor_policy_binding(teacher_policy: str, teacher_strategy: dict) -> str:
    if not _text(teacher_policy) or not isinstance(teacher_strategy, dict):
        _invalid("MENTOR_SUPERVISION_POLICY_BINDING_INVALID")
    effective = effective_policy_key(teacher_strategy)
    raw = (
        "bilqis.mlx.championship-mentor-policy-binding/v1\0"
        + teacher_policy + "\0" + effective
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def issue_mentor_supervision(
        accepted_manifest_sha256: str, championship_epoch_sha256: str,
        teacher_policy: str,
        policy_binding_sha256: str,
        source_seed: int, rows: tuple[MentorRowInfluence, ...], *,
        physical_inference_launches: int,
        logical_direct_votes: int, logical_soup_votes: float) -> MentorSupervision:
    result = object.__new__(MentorSupervision)
    for name, value in (
            ("accepted_manifest_sha256", accepted_manifest_sha256),
            ("championship_epoch_sha256", championship_epoch_sha256),
            ("teacher_policy", teacher_policy),
            ("policy_binding_sha256", policy_binding_sha256),
            ("source_seed", source_seed), ("rows", rows),
            ("physical_inference_launches", physical_inference_launches),
            ("logical_direct_votes", logical_direct_votes),
            ("logical_soup_votes", logical_soup_votes),
            ("schema_version", SCHEMA), ("_issuance", _ISSUER)):
        object.__setattr__(result, name, value)
    result.__post_init__()
    return result


__all__ = (
    "MentorRowInfluence", "MentorSupervision", "issue_mentor_supervision",
    "mentor_policy_binding",
)
