"""Versioned identity contracts for native BAMF championship authority."""
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.semantics.domains import contract_digest


IDENTITY_SCHEMA = "bilqis.bamf.capability-championship-epoch/v1"
SHA256_HEX_LENGTH = 64
CAPABILITY_GROUP_ARITY = 2

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
_SETTLEMENT_EPOCH_FIELDS = (
    "semantic_catalog_sha256",
    "semantic_abi_sha256",
    "capability_groups_sha256",
    "policy_sha256",
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


def settlement_epoch_sha256(identity):
    """Bind the no-rematch epoch without conflating comparison-context reset."""
    validate_championship_epoch_identity(identity)
    return contract_digest({field: identity[field] for field in _SETTLEMENT_EPOCH_FIELDS})


def comparison_context_sha256(identity):
    """Bind source/rubric context for one logically comparable fight."""
    validate_championship_epoch_identity(identity)
    return contract_digest({
        "settlement_epoch_sha256": settlement_epoch_sha256(identity),
        "source_sha256": identity["source_sha256"],
        "rubric_sha256": identity["rubric_sha256"],
    })
