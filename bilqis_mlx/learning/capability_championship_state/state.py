"""B13 championship sidecar shape, validation, and compact persistence."""
from copy import deepcopy

from bilqis_mlx.semantics.domains import contract_digest

from ..championship_witnesses import championship_role_qualified, verified_battery
from ..mentor_epoch import _pointer
from .identity import (
    _invalid,
    _sha,
    comparison_context_sha256,
    settlement_epoch_sha256,
    validate_championship_epoch_identity,
)


SCHEMA_V1 = "bilqis.bamf.capability-championship-state/v1"
SCHEMA = "bilqis.bamf.capability-championship-state/v2"
HISTORY_REF_SCHEMA = "bilqis.bamf.capability-championship-history-ref/v1"
LEGACY_SETTLED_MATCH_KEY_ARITY = 3
SETTLED_MATCH_KEY_ARITY = 4


def _validate_history_reference(reference):
    if (not isinstance(reference, dict)
            or set(reference) != {
                "schema", "source_manifest_sha256", "source_generation",
                "championship_state_sha256", "identity_sha256",
                "settlement_epoch_sha256", "comparison_context_sha256",
                "settled_matchups_sha256", "reason", "sha256",
            }
            or reference.get("schema") != HISTORY_REF_SCHEMA
            or type(reference.get("source_generation")) is not int
            or reference["source_generation"] < 0
            or not isinstance(reference.get("reason"), str)
            or not reference["reason"]
            or any(not _sha(reference.get(field)) for field in (
                "source_manifest_sha256", "championship_state_sha256",
                "identity_sha256", "settlement_epoch_sha256",
                "comparison_context_sha256", "settled_matchups_sha256", "sha256",
            ))):
        _invalid("CHAMPIONSHIP_HISTORY_REFERENCE_INVALID")
    payload = {key: value for key, value in reference.items() if key != "sha256"}
    if contract_digest(payload) != reference["sha256"]:
        _invalid("CHAMPIONSHIP_HISTORY_REFERENCE_INVALID")
    return reference


def _normalize_settled_matchups(settled_matchups, identity):
    if not isinstance(settled_matchups, dict):
        _invalid("CHAMPIONSHIP_SETTLED_MATCH_INVALID")
    settlement_epoch = settlement_epoch_sha256(identity)
    context = comparison_context_sha256(identity)
    identity_sha256 = contract_digest(identity)
    normalized = {}
    for key, receipt in settled_matchups.items():
        parts = key.split("|") if isinstance(key, str) else ()
        if len(parts) == LEGACY_SETTLED_MATCH_KEY_ARITY:
            capability, left_sha256, right_sha256 = parts
            key = "|".join((capability, context, left_sha256, right_sha256))
            receipt = {
                **deepcopy(receipt),
                "comparison_identity_sha256": identity_sha256,
                "comparison_context_sha256": context,
                "settlement_epoch_sha256": settlement_epoch,
            }
        elif len(parts) == SETTLED_MATCH_KEY_ARITY:
            receipt = deepcopy(receipt)
        else:
            _invalid("CHAMPIONSHIP_SETTLED_MATCH_INVALID")
        if key in normalized and normalized[key] != receipt:
            _invalid("CHAMPIONSHIP_SETTLED_MATCH_INVALID")
        normalized[key] = receipt
    return normalized


def validate_championship_state(record):
    fields = {"schema", "identity", "active_roles", "settled_matchups"}
    schema = record.get("schema") if isinstance(record, dict) else None
    if schema == SCHEMA:
        fields.update((
            "settlement_epoch_sha256", "comparison_context_sha256", "epoch_history"))
    if (
        not isinstance(record, dict)
        or set(record) != fields
        or schema not in {SCHEMA_V1, SCHEMA}
        or not isinstance(record.get("active_roles"), dict)
        or not isinstance(record.get("settled_matchups"), dict)
        or (schema == SCHEMA and not isinstance(record.get("epoch_history"), list))
        or (schema == SCHEMA and record.get("settlement_epoch_sha256")
            != settlement_epoch_sha256(record.get("identity")))
        or (schema == SCHEMA and record.get("comparison_context_sha256")
            != comparison_context_sha256(record.get("identity")))
    ):
        _invalid("CHAMPIONSHIP_STATE_INVALID")
    validate_championship_epoch_identity(record["identity"])
    for reference in record.get("epoch_history", ()):
        _validate_history_reference(reference)
    _validate_roles(record["active_roles"])
    _validate_settlements(record)
    return record


def _validate_roles(roles):
    for capability, role in roles.items():
        provenance = role.get("complete_solver_provenance")
        if (
            not isinstance(capability, str) or not capability
            or not isinstance(role, dict) or role.get("capability") != capability
            or not isinstance(role.get("capability_group"), str)
            or not role["capability_group"]
            or not isinstance(role.get("checkpoint_origin_group"), str)
            or not role["checkpoint_origin_group"]
            or not isinstance(provenance, dict)
            or provenance.get("weight_sha256") != role.get("checkpoint", {}).get("sha256")
            or not _sha(provenance.get("generation_digest"))
            or not isinstance(provenance.get("solver_contracts"), (tuple, list))
            or not provenance["solver_contracts"]
            or any(not _sha(contract) for contract in provenance["solver_contracts"])
            or len(set(provenance["solver_contracts"])) != len(provenance["solver_contracts"])
            or not championship_role_qualified(role)
        ):
            _invalid("CHAMPIONSHIP_ACTIVE_ROLE_INVALID")
        _pointer(role.get("checkpoint"))
        verified_battery(role)


def _validate_settlements(record):
    schema = record["schema"]
    for key, receipt in record["settled_matchups"].items():
        parts = key.split("|") if isinstance(key, str) else ()
        expected_arity = (
            LEGACY_SETTLED_MATCH_KEY_ARITY if schema == SCHEMA_V1
            else SETTLED_MATCH_KEY_ARITY)
        if len(parts) != expected_arity:
            _invalid("CHAMPIONSHIP_SETTLED_MATCH_INVALID")
        if schema == SCHEMA_V1:
            capability, left_sha256, right_sha256 = parts
            context = None
        else:
            capability, context, left_sha256, right_sha256 = parts
        if (not _sha(left_sha256) or not _sha(right_sha256)
                or not isinstance(receipt, dict)
                or receipt.get("capability") != capability
                or (schema == SCHEMA and (
                    not _sha(context)
                    or receipt.get("comparison_context_sha256") != context
                    or not _sha(receipt.get("comparison_identity_sha256"))
                    or receipt.get("settlement_epoch_sha256")
                    != record["settlement_epoch_sha256"]))):
            _invalid("CHAMPIONSHIP_SETTLED_MATCH_INVALID")


def active_checkpoint_references(record) -> tuple[dict, ...]:
    """Return only checkpoints that still own at least one live capability title."""
    validate_championship_state(record)
    unique = {}
    for role in record["active_roles"].values():
        pointer = _pointer(role["checkpoint"])
        unique[pointer["sha256"]] = pointer
    return tuple(deepcopy(unique[key]) for key in sorted(unique))


def compact_championship_state(epoch, identity):
    """Persist title/history authority owned by R03/R06, never soup state."""
    validate_championship_epoch_identity(identity)
    state = {
        "schema": SCHEMA,
        "identity": deepcopy(identity),
        "active_roles": deepcopy(epoch.get("active_roles", {})),
        "settled_matchups": _normalize_settled_matchups(
            epoch.get("settled_matchups", {}), identity),
        "settlement_epoch_sha256": settlement_epoch_sha256(identity),
        "comparison_context_sha256": comparison_context_sha256(identity),
        "epoch_history": deepcopy(epoch.get("epoch_history", [])),
    }
    validate_championship_state(state)
    return state
