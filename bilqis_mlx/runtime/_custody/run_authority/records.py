"""Immutable records for R17 run authority and cold-resume binding."""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Mapping

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.bamf_bundle.records import canonical, sha

RUN_AUTHORITY_SCHEMA = "bilqis.mlx.run-authority/v1"
RUN_AUTHORITY_BINDING_SCHEMA = "bilqis.mlx.run-authority-binding/v1"


def _invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.BAMF_RUN_AUTHORITY.INVALID, reason=reason)


def _hex(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


@dataclass(frozen=True)
class RunAuthorityIdentity:
    """Serializable identity of one exact typed experiment/run authority."""

    run_id: str
    owner_identity: str
    policy_epoch_sha256: str
    collective_max_bytes: int
    local_max_bytes: int
    custody_sha256: str
    resume_identity_sha256: str
    expires_at_unix_seconds: int | None = None
    schema_version: str = RUN_AUTHORITY_SCHEMA

    def __post_init__(self) -> None:
        if (self.schema_version != RUN_AUTHORITY_SCHEMA
                or not isinstance(self.run_id, str) or not self.run_id
                or not isinstance(self.owner_identity, str) or not self.owner_identity
                or not _hex(self.policy_epoch_sha256)
                or type(self.collective_max_bytes) is not int
                or self.collective_max_bytes < 1
                or type(self.local_max_bytes) is not int
                or not 0 <= self.local_max_bytes <= self.collective_max_bytes
                or not _hex(self.custody_sha256)
                or not _hex(self.resume_identity_sha256)
                or (self.expires_at_unix_seconds is not None
                    and (type(self.expires_at_unix_seconds) is not int
                         or self.expires_at_unix_seconds < 0))):
            _invalid("BAMF_RUN_AUTHORITY_IDENTITY_FIELDS_INVALID")
        if self.resume_identity_sha256 != self._expected_resume_identity():
            _invalid("BAMF_RUN_AUTHORITY_RESUME_IDENTITY_INVALID")

    def _resume_payload(self) -> dict:
        return {
            "schema": "bilqis.mlx.run-authority-resume-identity/v1",
            "run_id": self.run_id,
            "owner_identity": self.owner_identity,
            "policy_epoch_sha256": self.policy_epoch_sha256,
            "collective_max_bytes": self.collective_max_bytes,
            "local_max_bytes": self.local_max_bytes,
            "custody_sha256": self.custody_sha256,
            "expires_at_unix_seconds": self.expires_at_unix_seconds,
        }

    def _expected_resume_identity(self) -> str:
        return sha(canonical(self._resume_payload()))

    @property
    def digest(self) -> str:
        return sha(canonical(asdict(self)))

    def to_record(self) -> dict:
        return {**asdict(self), "run_authority_sha256": self.digest}

    @classmethod
    def issue(cls, *, run_id: str, owner_identity: str,
              policy_epoch_sha256: str, collective_max_bytes: int,
              local_max_bytes: int, custody_sha256: str,
              expires_at_unix_seconds: int | None = None) -> "RunAuthorityIdentity":
        partial = {
            "run_id": run_id, "owner_identity": owner_identity,
            "policy_epoch_sha256": policy_epoch_sha256,
            "collective_max_bytes": collective_max_bytes,
            "local_max_bytes": local_max_bytes, "custody_sha256": custody_sha256,
            "expires_at_unix_seconds": expires_at_unix_seconds,
        }
        resume = sha(canonical({
            "schema": "bilqis.mlx.run-authority-resume-identity/v1", **partial,
        }))
        return cls(**partial, resume_identity_sha256=resume)

    @classmethod
    def from_record(cls, record: Mapping) -> "RunAuthorityIdentity":
        names = {field.name for field in fields(cls)}
        if (not isinstance(record, Mapping)
                or set(record) != names | {"run_authority_sha256"}):
            _invalid("BAMF_RUN_AUTHORITY_IDENTITY_RECORD_INVALID")
        value = cls(**{name: record[name] for name in names})
        if record["run_authority_sha256"] != value.digest:
            _invalid("BAMF_RUN_AUTHORITY_IDENTITY_DIGEST_INVALID")
        return value


@dataclass(frozen=True)
class RunAuthorityBindingRecord:
    """Run-root receipt binding authority to the immutable B13 birth identity."""

    run_id: str
    run_identity_sha256: str
    authority: RunAuthorityIdentity
    schema_version: str = RUN_AUTHORITY_BINDING_SCHEMA

    def __post_init__(self) -> None:
        if (self.schema_version != RUN_AUTHORITY_BINDING_SCHEMA
                or not isinstance(self.run_id, str) or not self.run_id
                or not _hex(self.run_identity_sha256)
                or type(self.authority) is not RunAuthorityIdentity
                or self.authority.run_id != self.run_id):
            _invalid("BAMF_RUN_AUTHORITY_BINDING_FIELDS_INVALID")

    @property
    def digest(self) -> str:
        return sha(canonical({
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "run_identity_sha256": self.run_identity_sha256,
            "authority": self.authority.to_record(),
        }))

    def to_record(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "run_identity_sha256": self.run_identity_sha256,
            "authority": self.authority.to_record(),
            "binding_sha256": self.digest,
        }

    @classmethod
    def from_record(cls, record: Mapping) -> "RunAuthorityBindingRecord":
        expected = {
            "schema_version", "run_id", "run_identity_sha256",
            "authority", "binding_sha256",
        }
        if not isinstance(record, Mapping) or set(record) != expected:
            _invalid("BAMF_RUN_AUTHORITY_BINDING_RECORD_INVALID")
        value = cls(
            record["run_id"], record["run_identity_sha256"],
            RunAuthorityIdentity.from_record(record["authority"]),
            record["schema_version"])
        if record["binding_sha256"] != value.digest:
            _invalid("BAMF_RUN_AUTHORITY_BINDING_DIGEST_INVALID")
        return value
