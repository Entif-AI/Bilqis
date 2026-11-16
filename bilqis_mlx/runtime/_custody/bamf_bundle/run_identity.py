"""Portable BAMF run identity record with no numerical-runtime dependency."""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Mapping

from .records import canonical, invalid, sha


RUN_IDENTITY_SCHEMA = "bilqis.mlx.bamf-run-identity/v1"


def _hex(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


@dataclass(frozen=True)
class BamfRunIdentity:
    """Immutable birth identity shared by every generation in one BAMF run."""

    run_id: str
    run_seed: int
    origin_checkpoint_sha256: str
    origin_checkpoint_filename: str
    origin_optimizer_step: int
    factory_release_sha256: str
    semantic_graph_sha256: str
    initial_candidate_identity_sha256: str
    initial_topology_digest: str
    initial_extents_digest: str
    initial_implementation_sha256: str
    initial_source_identity: str
    initial_release_digest: str
    initial_teacher_identity: str
    initial_teacher_epoch: int
    schema_version: str = RUN_IDENTITY_SCHEMA

    def __post_init__(self) -> None:
        digests = (
            self.origin_checkpoint_sha256, self.factory_release_sha256,
            self.semantic_graph_sha256, self.initial_candidate_identity_sha256,
            self.initial_topology_digest, self.initial_extents_digest,
            self.initial_implementation_sha256, self.initial_release_digest,
        )
        if (self.schema_version != RUN_IDENTITY_SCHEMA
                or not isinstance(self.run_id, str) or not self.run_id
                or type(self.run_seed) is not int or self.run_seed < 0
                or not isinstance(self.origin_checkpoint_filename, str)
                or not self.origin_checkpoint_filename
                or type(self.origin_optimizer_step) is not int
                or self.origin_optimizer_step < 0
                or any(not _hex(value) for value in digests)
                or not isinstance(self.initial_source_identity, str)
                or not self.initial_source_identity
                or not isinstance(self.initial_teacher_identity, str)
                or not self.initial_teacher_identity
                or type(self.initial_teacher_epoch) is not int
                or self.initial_teacher_epoch < 0):
            invalid("BAMF_RUN_IDENTITY_INVALID")

    @property
    def digest(self) -> str:
        return sha(canonical(asdict(self)))

    def to_record(self) -> dict:
        return {**asdict(self), "run_identity_sha256": self.digest}

    @classmethod
    def from_record(cls, record: Mapping) -> "BamfRunIdentity":
        names = {item.name for item in fields(cls)}
        if not isinstance(record, Mapping) or set(record) != names | {"run_identity_sha256"}:
            invalid("BAMF_RUN_IDENTITY_INVALID")
        identity = cls(**{name: record[name] for name in names})
        if record["run_identity_sha256"] != identity.digest:
            invalid("BAMF_RUN_IDENTITY_INVALID")
        return identity


__all__ = ("BamfRunIdentity", "RUN_IDENTITY_SCHEMA")
