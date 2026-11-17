"""B13 custody record for one C07-authorized Atlas parameter extension."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest

from .records import BamfBundleCandidate, CompleteStudent, canonical, invalid, sha


ATLAS_ADMISSION_SCHEMA_V1 = "bilqis.mlx.bamf-atlas-admission-binding/v1"
ATLAS_ADMISSION_SCHEMA_V2 = "bilqis.mlx.bamf-atlas-admission-binding/v2"
ATLAS_ADMISSION_SCHEMA_V3 = "bilqis.mlx.bamf-atlas-admission-binding/v3"
ATLAS_ADMISSION_SCHEMA_V4 = "bilqis.mlx.bamf-atlas-admission-binding/v4"
ATLAS_ADMISSION_SCHEMA = ATLAS_ADMISSION_SCHEMA_V4
ATLAS_ADMISSION_SCHEMAS = frozenset({
    ATLAS_ADMISSION_SCHEMA_V1, ATLAS_ADMISSION_SCHEMA_V2,
    ATLAS_ADMISSION_SCHEMA_V3, ATLAS_ADMISSION_SCHEMA_V4,
})
_ISSUER = object()
_FIELDS_V1 = (
    "run_id", "generation", "candidate_identity_sha256",
    "parent_candidate_identity_sha256", "feature_sha256", "optimizer_step",
    "lease_sha256", "source_approval_sha256", "proposal_sha256",
    "factory_release_sha256", "staging_receipt_sha256",
    "parent_feature_receipt_sha256", "schema_version",
)
_FIELDS_V2 = (
    *_FIELDS_V1[:-1],
    "selection_receipt_sha256", "selected_obligation_keys", "schema_version",
)
_FIELDS_V3 = (
    *_FIELDS_V2[:-1],
    "predecessor_factory_release_sha256",
    "generated_grade_proposal_sha256",
    "schema_version",
)
_FIELDS_V4 = (
    *_FIELDS_V3[:-1],
    "championship_state_sha256",
    "schema_version",
)


def _hex(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def _valid_obligation_keys(value: object) -> bool:
    return (type(value) is tuple
            and value == tuple(sorted(set(value)))
            and all(type(item) is tuple and len(item) == 2
                    and isinstance(item[0], str) and bool(item[0])
                    and _hex(item[1]) for item in value))


@dataclass(frozen=True)
class AtlasAdmissionBinding:
    """Live C07 admission capability for one exact B13 successor generation."""

    run_id: str
    generation: int
    candidate_identity_sha256: str
    parent_candidate_identity_sha256: str
    feature_sha256: str
    optimizer_step: int
    lease_sha256: str
    source_approval_sha256: str
    proposal_sha256: str
    factory_release_sha256: str
    staging_receipt_sha256: str
    parent_feature_receipt_sha256: str
    selection_receipt_sha256: str | None = None
    selected_obligation_keys: tuple[tuple[str, str], ...] = ()
    predecessor_factory_release_sha256: str | None = None
    generated_grade_proposal_sha256: str | None = None
    championship_state_sha256: str | None = None
    schema_version: str = ATLAS_ADMISSION_SCHEMA_V1
    _issuance: object = field(init=False, default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if (getattr(self, "_issuance", None) is not _ISSUER
                or not isinstance(self.run_id, str) or not self.run_id
                or type(self.generation) is not int or self.generation < 1
                or type(self.optimizer_step) is not int or self.optimizer_step < 0
                or any(not _hex(getattr(self, name)) for name in (
                    "candidate_identity_sha256", "parent_candidate_identity_sha256",
                    "feature_sha256", "lease_sha256", "source_approval_sha256",
                    "proposal_sha256", "factory_release_sha256",
                    "staging_receipt_sha256", "parent_feature_receipt_sha256"))
                or self.schema_version not in ATLAS_ADMISSION_SCHEMAS
                or (self.schema_version != ATLAS_ADMISSION_SCHEMA_V4
                    and self.championship_state_sha256 is not None)
                or (self.schema_version == ATLAS_ADMISSION_SCHEMA_V1
                    and (self.selection_receipt_sha256 is not None
                         or self.selected_obligation_keys))
                or (self.schema_version == ATLAS_ADMISSION_SCHEMA_V2
                    and (not _hex(self.selection_receipt_sha256)
                         or not _valid_obligation_keys(self.selected_obligation_keys)
                         or not self.selected_obligation_keys))):
            invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
        if (self.schema_version == ATLAS_ADMISSION_SCHEMA_V3
                and (not _hex(self.selection_receipt_sha256)
                     or not _valid_obligation_keys(self.selected_obligation_keys)
                     or not self.selected_obligation_keys
                     or not _hex(self.predecessor_factory_release_sha256)
                     or not _hex(self.generated_grade_proposal_sha256))):
            invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
        if self.schema_version == ATLAS_ADMISSION_SCHEMA_V4:
            if not _hex(self.championship_state_sha256):
                invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
            has_v3 = self.generated_grade_proposal_sha256 is not None
            has_v2 = has_v3 or self.selection_receipt_sha256 is not None or bool(
                self.selected_obligation_keys)
            if (has_v2 and (
                    not _hex(self.selection_receipt_sha256)
                    or not _valid_obligation_keys(self.selected_obligation_keys)
                    or not self.selected_obligation_keys)):
                invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
            if (not has_v2 and (
                    self.selection_receipt_sha256 is not None
                    or self.selected_obligation_keys)):
                invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
            if (has_v3 and (
                    not _hex(self.predecessor_factory_release_sha256)
                    or not _hex(self.generated_grade_proposal_sha256))):
                invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
            if (not has_v3 and (
                    self.predecessor_factory_release_sha256 is not None
                    or self.generated_grade_proposal_sha256 is not None)):
                invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")

    def _public_record(self) -> dict:
        fields = (_FIELDS_V4 if self.schema_version == ATLAS_ADMISSION_SCHEMA_V4
                  else _FIELDS_V3 if self.schema_version == ATLAS_ADMISSION_SCHEMA_V3
                  else _FIELDS_V2 if self.schema_version == ATLAS_ADMISSION_SCHEMA_V2
                  else _FIELDS_V1)
        return {name: getattr(self, name) for name in fields}

    @property
    def digest(self) -> str:
        return sha(canonical(self._public_record()))

    def to_record(self) -> dict:
        return {**self._public_record(), "binding_sha256": self.digest}

    @classmethod
    def from_record(cls, record: Mapping) -> "ParsedAtlasAdmissionBinding":
        if not isinstance(record, Mapping):
            invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
        schema = record.get("schema_version")
        fields = (_FIELDS_V4 if schema == ATLAS_ADMISSION_SCHEMA_V4
                  else _FIELDS_V3 if schema == ATLAS_ADMISSION_SCHEMA_V3
                  else _FIELDS_V2 if schema == ATLAS_ADMISSION_SCHEMA_V2
                  else _FIELDS_V1 if schema == ATLAS_ADMISSION_SCHEMA_V1 else ())
        if not fields or set(record) != set(fields) | {"binding_sha256"}:
            invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
        payload = {name: record[name] for name in fields}
        if schema in {
                ATLAS_ADMISSION_SCHEMA_V2, ATLAS_ADMISSION_SCHEMA_V3,
                ATLAS_ADMISSION_SCHEMA_V4}:
            raw_keys = payload["selected_obligation_keys"]
            if not isinstance(raw_keys, (list, tuple)):
                invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
            payload["selected_obligation_keys"] = tuple(
                tuple(item) if isinstance(item, (list, tuple)) else item
                for item in raw_keys)
        if (payload["schema_version"] not in ATLAS_ADMISSION_SCHEMAS
                or not isinstance(payload["run_id"], str) or not payload["run_id"]
                or type(payload["generation"]) is not int or payload["generation"] < 1
                or type(payload["optimizer_step"]) is not int
                or payload["optimizer_step"] < 0
                or any(not _hex(payload[name]) for name in (
                    "candidate_identity_sha256", "parent_candidate_identity_sha256",
                    "feature_sha256", "lease_sha256", "source_approval_sha256",
                    "proposal_sha256", "factory_release_sha256",
                    "staging_receipt_sha256", "parent_feature_receipt_sha256"))
                or (schema == ATLAS_ADMISSION_SCHEMA_V2
                    and (not _hex(payload["selection_receipt_sha256"])
                         or not _valid_obligation_keys(payload["selected_obligation_keys"])
                         or not payload["selected_obligation_keys"]))
                or (schema == ATLAS_ADMISSION_SCHEMA_V3
                    and (not _hex(payload["selection_receipt_sha256"])
                         or not _valid_obligation_keys(payload["selected_obligation_keys"])
                         or not payload["selected_obligation_keys"]
                         or not _hex(payload["predecessor_factory_release_sha256"])
                         or not _hex(payload["generated_grade_proposal_sha256"])))
                or (schema == ATLAS_ADMISSION_SCHEMA_V4
                    and (not _hex(payload["championship_state_sha256"])
                         or ((payload["selection_receipt_sha256"] is not None
                              or payload["selected_obligation_keys"])
                             and (not _hex(payload["selection_receipt_sha256"])
                                  or not _valid_obligation_keys(
                                      payload["selected_obligation_keys"])
                                  or not payload["selected_obligation_keys"]))
                         or ((payload["predecessor_factory_release_sha256"] is not None
                              or payload["generated_grade_proposal_sha256"] is not None)
                             and (not _hex(payload["predecessor_factory_release_sha256"])
                                  or not _hex(payload["generated_grade_proposal_sha256"])))))
                or record["binding_sha256"] != sha(canonical(payload))):
            invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
        return ParsedAtlasAdmissionBinding(payload)


@dataclass(frozen=True)
class ParsedAtlasAdmissionBinding:
    """Verified historical admission evidence; never live C07 authority."""

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


def validate_parsed_atlas_championship_state(
        student: CompleteStudent, binding: ParsedAtlasAdmissionBinding) -> None:
    """Recheck the v4 championship sidecar seal after cold B13 replay."""
    if type(student) is not CompleteStudent or type(binding) is not ParsedAtlasAdmissionBinding:
        invalid("BAMF_ATLAS_ADMISSION_BINDING_DRIFT")
    if binding.schema_version != ATLAS_ADMISSION_SCHEMA_V4:
        return
    state = student.championship_state
    if (state is None
            or binding.championship_state_sha256 != sha(canonical(dict(state)))):
        invalid("BAMF_ATLAS_ADMISSION_BINDING_DRIFT")


def _issue_atlas_admission_binding(
        candidate: BamfBundleCandidate, parent: CompleteStudent, *,
        lease_sha256: str, source_approval_sha256: str, proposal_sha256: str,
        factory_release_sha256: str, staging_receipt_sha256: str,
        parent_feature_receipt_sha256: str,
        selection_receipt_sha256: str | None = None,
        selected_obligation_keys: tuple[tuple[str, str], ...] = (),
        predecessor_factory_release_sha256: str | None = None,
        generated_grade_proposal_sha256: str | None = None,
) -> AtlasAdmissionBinding:
    """Mint C07 authority only after its caller has replayed lease and staging proof."""
    transition = dict(candidate.transition)
    championship_reset_valid = True
    if parent.championship_state is None:
        championship_reset_valid = candidate.championship_state is None
    else:
        if candidate.championship_state is None:
            championship_reset_valid = False
        else:
            from bilqis_mlx.learning.capability_championship_state import (
                validate_championship_state,
            )
            state = dict(candidate.championship_state)
            validate_championship_state(state)
            history = state.get("epoch_history", ())
            championship_reset_valid = (
                state.get("active_roles") == {}
                and state.get("settled_matchups") == {}
                and bool(history)
                and history[-1].get("source_generation") == parent.generation
                and history[-1].get("reason") == "NEW_SEMANTIC_ADMISSION"
            )
    if (type(candidate) is not BamfBundleCandidate or type(parent) is not CompleteStudent
            or candidate.run_identity is None or candidate.run_identity != parent.run_identity
            or candidate.run_id != parent.run_id
            or candidate.generation != parent.generation + 1
            or candidate.retained_state.optimizer_step != parent.retained_state.optimizer_step
            or not championship_reset_valid
            or transition != {
                "schema": "bilqis.mlx.bamf-generation-transition/v1",
                "kind": "PARAMETER_EXTENSION",
                "invalidate_derived_caches": True,
            }):
        invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
    obligation_keys = tuple(sorted(set(selected_obligation_keys)))
    v3 = generated_grade_proposal_sha256 is not None
    v2 = v3 or selection_receipt_sha256 is not None or bool(obligation_keys)
    v4 = candidate.championship_state is not None
    if v2 and (not _hex(selection_receipt_sha256)
               or not _valid_obligation_keys(obligation_keys)
               or not obligation_keys):
        invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
    if v3 and (not _hex(predecessor_factory_release_sha256)
               or not _hex(generated_grade_proposal_sha256)):
        invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
    binding = object.__new__(AtlasAdmissionBinding)
    for name, value in (
            ("run_id", candidate.run_id), ("generation", candidate.generation),
            ("candidate_identity_sha256", candidate_identity_digest(
                candidate.retained_state)),
            ("parent_candidate_identity_sha256", candidate_identity_digest(
                parent.retained_state)),
            ("feature_sha256", candidate.extents.factor_map_digest),
            ("optimizer_step", candidate.retained_state.optimizer_step),
            ("lease_sha256", lease_sha256),
            ("source_approval_sha256", source_approval_sha256),
            ("proposal_sha256", proposal_sha256),
            ("factory_release_sha256", factory_release_sha256),
            ("staging_receipt_sha256", staging_receipt_sha256),
            ("parent_feature_receipt_sha256", parent_feature_receipt_sha256),
            ("selection_receipt_sha256", selection_receipt_sha256),
            ("selected_obligation_keys", obligation_keys),
            ("predecessor_factory_release_sha256", predecessor_factory_release_sha256),
            ("generated_grade_proposal_sha256", generated_grade_proposal_sha256),
            ("championship_state_sha256", (
                sha(canonical(dict(candidate.championship_state))) if v4 else None)),
            ("schema_version", (
                ATLAS_ADMISSION_SCHEMA_V4 if v4
                else ATLAS_ADMISSION_SCHEMA_V3 if v3
                else ATLAS_ADMISSION_SCHEMA_V2 if v2
                else ATLAS_ADMISSION_SCHEMA_V1)),
            ("_issuance", _ISSUER)):
        object.__setattr__(binding, name, value)
    binding.__post_init__()
    return binding


def require_issued_atlas_admission_binding(value) -> AtlasAdmissionBinding:
    if type(value) is not AtlasAdmissionBinding or getattr(value, "_issuance", None) is not _ISSUER:
        invalid("BAMF_ATLAS_ADMISSION_BINDING_INVALID")
    value.__post_init__()
    return value


def require_atlas_admission_binding(
        candidate: BamfBundleCandidate, value) -> AtlasAdmissionBinding:
    """Bind one live C07 capability to the exact candidate it authorizes."""
    binding = require_issued_atlas_admission_binding(value)
    if (binding.run_id != candidate.run_id
            or binding.generation != candidate.generation
            or binding.candidate_identity_sha256
            != candidate_identity_digest(candidate.retained_state)
            or binding.feature_sha256 != candidate.extents.factor_map_digest
            or binding.optimizer_step != candidate.retained_state.optimizer_step
            or (binding.schema_version == ATLAS_ADMISSION_SCHEMA_V4
                and (candidate.championship_state is None
                     or binding.championship_state_sha256
                     != sha(canonical(dict(candidate.championship_state)))))):
        invalid("BAMF_ATLAS_ADMISSION_BINDING_DRIFT")
    if candidate.championship_state is not None:
        from bilqis_mlx.learning.capability_championship_state import (
            validate_championship_state,
        )
        state = dict(candidate.championship_state)
        validate_championship_state(state)
        history = state.get("epoch_history", ())
        if (state.get("active_roles") != {}
                or state.get("settled_matchups") != {}
                or not history
                or history[-1].get("reason") != "NEW_SEMANTIC_ADMISSION"):
            invalid("BAMF_ATLAS_ADMISSION_BINDING_DRIFT")
    return binding
