"""Versioned acceptance-binding records for Factory-release adoption."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from ..records import canonical, invalid, sha


FACTORY_RELEASE_ADMISSION_SCHEMA_V1 = (
    "bilqis.mlx.bamf-factory-release-admission-binding/v1")
FACTORY_RELEASE_ADMISSION_SCHEMA_V2 = (
    "bilqis.mlx.bamf-factory-release-admission-binding/v2")
FACTORY_RELEASE_ADMISSION_SCHEMA_V3 = (
    "bilqis.mlx.bamf-factory-release-admission-binding/v3")
FACTORY_RELEASE_ADMISSION_SCHEMA_V4 = (
    "bilqis.mlx.bamf-factory-release-admission-binding/v4")
FACTORY_RELEASE_ADMISSION_SCHEMA = FACTORY_RELEASE_ADMISSION_SCHEMA_V3
FACTORY_RELEASE_ADMISSION_SCHEMAS = frozenset({
    FACTORY_RELEASE_ADMISSION_SCHEMA_V1,
    FACTORY_RELEASE_ADMISSION_SCHEMA_V2,
    FACTORY_RELEASE_ADMISSION_SCHEMA_V3,
    FACTORY_RELEASE_ADMISSION_SCHEMA_V4,
})
_SHA256_HEX_LENGTH = 64
_OBLIGATION_KEY_PARTS = 2
_ISSUER = object()
_FIELDS_V1 = (
    "run_id", "generation", "candidate_identity_sha256",
    "parent_candidate_identity_sha256", "feature_sha256", "optimizer_step",
    "lease_sha256", "source_approval_sha256", "handoff_sha256",
    "proposal_sha256", "selection_receipt_sha256",
    "predecessor_factory_release_sha256", "factory_release_sha256",
    "transition_sha256", "adoption_event_sha256", "schema_version",
)
_FIELDS_V2 = (
    *_FIELDS_V1[:-1], "accepted_obligation_keys", "schema_version",
)
_FIELDS_V3 = (
    *_FIELDS_V2[:-1], "generated_grade_proposal_sha256", "schema_version",
)

_FIELDS_V4 = (
    "run_id", "generation", "candidate_identity_sha256",
    "parent_candidate_identity_sha256", "feature_sha256", "optimizer_step",
    "predecessor_factory_release_sha256", "factory_release_sha256", "profile_sha256",
    "parent_manifest_sha256", "lease_sha256", "source_approval_sha256",
    "profile_transition_sha256", "transition_sha256", "adoption_event_sha256",
    "accepted_obligation_keys", "schema_version",
)


def _hex(value: object) -> bool:
    return (isinstance(value, str) and len(value) == _SHA256_HEX_LENGTH
            and all(char in "0123456789abcdef" for char in value))


def _valid_obligation_keys(value: object) -> bool:
    return (type(value) is tuple
            and value == tuple(sorted(set(value)))
            and all(type(item) is tuple and len(item) == _OBLIGATION_KEY_PARTS
                    and isinstance(item[0], str) and bool(item[0])
                    and _hex(item[1]) for item in value))


def _invalid() -> None:
    invalid("BAMF_FACTORY_RELEASE_ADMISSION_BINDING_INVALID")


@dataclass(frozen=True)
class FactoryReleaseAdmissionBinding:
    """Live B13/C07 capability for one exact Factory-only successor."""

    run_id: str
    generation: int
    candidate_identity_sha256: str
    parent_candidate_identity_sha256: str
    feature_sha256: str
    optimizer_step: int
    lease_sha256: str
    source_approval_sha256: str
    handoff_sha256: str
    proposal_sha256: str
    selection_receipt_sha256: str
    predecessor_factory_release_sha256: str
    factory_release_sha256: str
    transition_sha256: str
    adoption_event_sha256: str
    profile_sha256: str | None = None
    parent_manifest_sha256: str | None = None
    profile_transition_sha256: str | None = None
    accepted_obligation_keys: tuple[tuple[str, str], ...] = ()
    generated_grade_proposal_sha256: str | None = None
    schema_version: str = FACTORY_RELEASE_ADMISSION_SCHEMA_V1
    _issuance: object = field(init=False, default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if (getattr(self, "_issuance", None) is not _ISSUER
                or not isinstance(self.run_id, str) or not self.run_id
                or type(self.generation) is not int or self.generation < 1
                or type(self.optimizer_step) is not int or self.optimizer_step < 0
                or self.schema_version not in FACTORY_RELEASE_ADMISSION_SCHEMAS
                or any(not _hex(getattr(self, name)) for name in (_FIELDS_V4 if self.schema_version == FACTORY_RELEASE_ADMISSION_SCHEMA_V4 else _FIELDS_V1)
                       if name.endswith("_sha256"))
                or (self.schema_version == FACTORY_RELEASE_ADMISSION_SCHEMA_V1
                    and self.accepted_obligation_keys)
                or (self.schema_version == FACTORY_RELEASE_ADMISSION_SCHEMA_V2
                    and (not _valid_obligation_keys(self.accepted_obligation_keys)
                         or not self.accepted_obligation_keys))):
            _invalid()
        if (self.schema_version == FACTORY_RELEASE_ADMISSION_SCHEMA_V4
                and not _valid_obligation_keys(self.accepted_obligation_keys)):
            _invalid()
        if (self.schema_version == FACTORY_RELEASE_ADMISSION_SCHEMA_V3
                and (not _valid_obligation_keys(self.accepted_obligation_keys)
                     or not self.accepted_obligation_keys
                     or not _hex(self.generated_grade_proposal_sha256))):
            _invalid()

    def _public_record(self) -> dict:
        fields = (_FIELDS_V4 if self.schema_version == FACTORY_RELEASE_ADMISSION_SCHEMA_V4
                  else _FIELDS_V3
                  if self.schema_version == FACTORY_RELEASE_ADMISSION_SCHEMA_V3
                  else _FIELDS_V2
                  if self.schema_version == FACTORY_RELEASE_ADMISSION_SCHEMA_V2
                  else _FIELDS_V1)
        return {name: getattr(self, name) for name in fields}

    @property
    def digest(self) -> str:
        return sha(canonical(self._public_record()))

    def to_record(self) -> dict:
        return {**self._public_record(), "binding_sha256": self.digest}

    @classmethod
    def from_record(cls, record: Mapping) -> "ParsedFactoryReleaseAdmissionBinding":
        if not isinstance(record, Mapping):
            _invalid()
        schema = record.get("schema_version")
        fields = (_FIELDS_V4 if schema == FACTORY_RELEASE_ADMISSION_SCHEMA_V4
                  else _FIELDS_V3 if schema == FACTORY_RELEASE_ADMISSION_SCHEMA_V3
                  else _FIELDS_V2 if schema == FACTORY_RELEASE_ADMISSION_SCHEMA_V2
                  else _FIELDS_V1
                  if schema == FACTORY_RELEASE_ADMISSION_SCHEMA_V1 else ())
        if not fields or set(record) != set(fields) | {"binding_sha256"}:
            _invalid()
        payload = {name: record[name] for name in fields}
        if schema in {
                FACTORY_RELEASE_ADMISSION_SCHEMA_V2,
                FACTORY_RELEASE_ADMISSION_SCHEMA_V3,
                FACTORY_RELEASE_ADMISSION_SCHEMA_V4}:
            raw_keys = payload["accepted_obligation_keys"]
            if not isinstance(raw_keys, (list, tuple)):
                _invalid()
            payload["accepted_obligation_keys"] = tuple(
                tuple(item) if isinstance(item, (list, tuple)) else item
                for item in raw_keys)
        if (payload["schema_version"] not in FACTORY_RELEASE_ADMISSION_SCHEMAS
                or not isinstance(payload["run_id"], str) or not payload["run_id"]
                or type(payload["generation"]) is not int or payload["generation"] < 1
                or type(payload["optimizer_step"]) is not int
                or payload["optimizer_step"] < 0
                or any(not _hex(payload[name]) for name in fields
                       if name.endswith("_sha256"))
                or (schema == FACTORY_RELEASE_ADMISSION_SCHEMA_V4
                    and not _valid_obligation_keys(payload["accepted_obligation_keys"]))
                or (schema == FACTORY_RELEASE_ADMISSION_SCHEMA_V2
                    and (not _valid_obligation_keys(payload["accepted_obligation_keys"])
                         or not payload["accepted_obligation_keys"]))
                or (schema == FACTORY_RELEASE_ADMISSION_SCHEMA_V3
                    and (not _valid_obligation_keys(payload["accepted_obligation_keys"])
                         or not payload["accepted_obligation_keys"]
                         or not _hex(payload["generated_grade_proposal_sha256"])))
                or record["binding_sha256"] != sha(canonical(payload))):
            _invalid()
        return ParsedFactoryReleaseAdmissionBinding(payload)


@dataclass(frozen=True)
class ParsedFactoryReleaseAdmissionBinding:
    """Verified historical Factory-only acceptance; never live authority."""

    fields: dict

    def __getattr__(self, name: str):
        if name in self.fields:
            return self.fields[name]
        raise AttributeError(name)

    @property
    def digest(self) -> str:
        return sha(canonical(self.fields))

    def to_record(self) -> dict:
        return {**self.fields, "binding_sha256": self.digest}


def _mint_binding(**values) -> FactoryReleaseAdmissionBinding:
    binding = object.__new__(FactoryReleaseAdmissionBinding)
    for name, value in (*values.items(), ("_issuance", _ISSUER)):
        object.__setattr__(binding, name, value)
    binding.__post_init__()
    return binding


def _require_live_binding(value) -> FactoryReleaseAdmissionBinding:
    if (type(value) is not FactoryReleaseAdmissionBinding
            or getattr(value, "_issuance", None) is not _ISSUER):
        _invalid()
    value.__post_init__()
    return value
