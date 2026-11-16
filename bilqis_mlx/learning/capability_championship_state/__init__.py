"""Authenticated B13 sidecar for live per-capability championship authority."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.semantics.domains import contract_digest

from ..championship_witnesses import (
    championship_role_qualified,
    verified_battery,
)
from ..mentor_epoch import _pointer


SCHEMA = "bilqis.bamf.capability-championship-state/v1"
IDENTITY_SCHEMA = "bilqis.bamf.capability-championship-epoch/v1"
SHA256_HEX_LENGTH = 64
CAPABILITY_GROUP_ARITY = 2
SETTLED_MATCH_KEY_ARITY = 3

_IDENTITY_FIELDS = (
    "factory_release_sha256",
    "semantic_catalog_sha256",
    "curriculum_sha256",
    "capability_groups_sha256",
    "fixed_cohort_sha256",
    "rubric_sha256",
    "scope_sha256",
    "source_sha256",
    "policy_sha256",
    "topology_sha256",
    "extents_sha256",
    "semantic_abi_sha256",
)
_SEMANTIC_EPOCH_FIELDS = (
    "semantic_catalog_sha256",
    "semantic_abi_sha256",
    "capability_groups_sha256",
)


def _sha(value) -> bool:
    return (
        isinstance(value, str)
        and len(value) == SHA256_HEX_LENGTH
        and all(char in "0123456789abcdef" for char in value)
    )


def _invalid(reason):
    ErrorBus.raise_(SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID, reason=reason)


def championship_epoch_identity(
        *, factory_release_sha256, semantic_catalog_sha256, curriculum_sha256,
        capability_groups=None, capability_groups_sha256=None,
        fixed_cohort_sha256, rubric_sha256, scope_sha256,
        source_sha256, policy_sha256, topology_sha256, extents_sha256,
        semantic_abi):
    """Bind every comparison surface that can invalidate a live title."""
    if capability_groups_sha256 is None:
        groups = tuple(capability_groups or ())
        if (
            not groups
            or any(
                not isinstance(pair, tuple)
                or len(pair) != CAPABILITY_GROUP_ARITY
                or not all(isinstance(value, str) and value for value in pair)
                for pair in groups
            )
            or len(dict(groups)) != len(groups)
        ):
            _invalid("CHAMPIONSHIP_CAPABILITY_GROUP_CENSUS_INVALID")
        capability_groups_sha256 = contract_digest(groups)
    elif not _sha(capability_groups_sha256) or capability_groups is not None:
        _invalid("CHAMPIONSHIP_CAPABILITY_GROUP_CENSUS_INVALID")
    identity = {
        "schema": IDENTITY_SCHEMA,
        "factory_release_sha256": factory_release_sha256,
        "semantic_catalog_sha256": semantic_catalog_sha256,
        "curriculum_sha256": curriculum_sha256,
        "capability_groups_sha256": capability_groups_sha256,
        "fixed_cohort_sha256": fixed_cohort_sha256,
        "rubric_sha256": rubric_sha256,
        "scope_sha256": scope_sha256,
        "source_sha256": source_sha256,
        "policy_sha256": policy_sha256,
        "topology_sha256": topology_sha256,
        "extents_sha256": extents_sha256,
        "semantic_abi_sha256": contract_digest(dict(semantic_abi)),
    }
    validate_championship_epoch_identity(identity)
    return identity


def validate_championship_epoch_identity(identity):
    if (
        not isinstance(identity, dict)
        or set(identity) != {"schema", *_IDENTITY_FIELDS}
        or identity.get("schema") != IDENTITY_SCHEMA
        or any(not _sha(identity.get(field)) for field in _IDENTITY_FIELDS)
    ):
        _invalid("CHAMPIONSHIP_EPOCH_IDENTITY_INVALID")
    return identity


def empty_championship_state(identity):
    """Start a new semantic epoch with no inherited title authority."""
    validate_championship_epoch_identity(identity)
    return {
        "schema": SCHEMA,
        "identity": deepcopy(identity),
        "active_roles": {},
        "settled_matchups": {},
    }


def reset_championship_state(prior, identity):
    """Clear live titles on any identity drift; clear settlements only for new semantics."""
    validate_championship_state(prior)
    validate_championship_epoch_identity(identity)
    reset = empty_championship_state(identity)
    if not any(
            prior["identity"][field] != identity[field]
            for field in _SEMANTIC_EPOCH_FIELDS):
        reset["settled_matchups"] = deepcopy(prior["settled_matchups"])
    return reset


def clear_active_championship_titles(record):
    """Clear live title custody while retaining identity and epoch-local settlements."""
    validate_championship_state(record)
    cleared = deepcopy(record)
    cleared["active_roles"] = {}
    return cleared


def validate_championship_state(record):
    if (
        not isinstance(record, dict)
        or set(record) != {"schema", "identity", "active_roles", "settled_matchups"}
        or record.get("schema") != SCHEMA
        or not isinstance(record.get("active_roles"), dict)
        or not isinstance(record.get("settled_matchups"), dict)
    ):
        _invalid("CHAMPIONSHIP_STATE_INVALID")
    validate_championship_epoch_identity(record["identity"])
    for capability, role in record["active_roles"].items():
        provenance = role.get("complete_solver_provenance")
        if (
            not isinstance(capability, str)
            or not capability
            or not isinstance(role, dict)
            or role.get("capability") != capability
            or not isinstance(role.get("capability_group"), str)
            or not role["capability_group"]
            or not isinstance(role.get("checkpoint_origin_group"), str)
            or not role["checkpoint_origin_group"]
            or not isinstance(provenance, dict)
            or provenance.get("weight_sha256")
            != role.get("checkpoint", {}).get("sha256")
            or not _sha(provenance.get("generation_digest"))
            or not isinstance(provenance.get("solver_contracts"), (tuple, list))
            or not provenance["solver_contracts"]
            or any(not _sha(contract) for contract in provenance["solver_contracts"])
            or len(set(provenance["solver_contracts"])) != len(
                provenance["solver_contracts"])
            or not championship_role_qualified(role)
        ):
            _invalid("CHAMPIONSHIP_ACTIVE_ROLE_INVALID")
        _pointer(role.get("checkpoint"))
        verified_battery(role)
    for key, receipt in record["settled_matchups"].items():
        if not isinstance(key, str) or not key:
            _invalid("CHAMPIONSHIP_SETTLED_MATCH_INVALID")
        parts = key.split("|")
        if len(parts) != SETTLED_MATCH_KEY_ARITY:
            _invalid("CHAMPIONSHIP_SETTLED_MATCH_INVALID")
        capability, left_sha256, right_sha256 = parts
        if (not _sha(left_sha256) or not _sha(right_sha256)
                or not isinstance(receipt, dict)
                or receipt.get("capability") != capability):
            _invalid("CHAMPIONSHIP_SETTLED_MATCH_INVALID")
    return record


def active_checkpoint_references(record) -> tuple[dict, ...]:
    """Return only checkpoints that still own at least one live capability title."""
    validate_championship_state(record)
    unique = {}
    for role in record["active_roles"].values():
        pointer = _pointer(role["checkpoint"])
        unique[pointer["sha256"]] = pointer
    return tuple(deepcopy(unique[key]) for key in sorted(unique))


def compact_championship_state(epoch, identity):
    """Persist only title authority owned by #1326, never soup/mentor state."""
    validate_championship_epoch_identity(identity)
    state = {
        "schema": SCHEMA,
        "identity": deepcopy(identity),
        "active_roles": deepcopy(epoch.get("active_roles", {})),
        "settled_matchups": deepcopy(epoch.get("settled_matchups", {})),
    }
    validate_championship_state(state)
    return state
