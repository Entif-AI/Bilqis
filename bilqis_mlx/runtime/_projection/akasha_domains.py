"""Logical Akasha domain/authority contracts.

Akasha may share a physical service, but these contracts keep canonical owners,
rebuild sources, identities and cross-domain references logically federated.
They deliberately do not choose a command broker or grant Mission Control write
authority; those are separate security/topology decisions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType

from bilqis_mlx.errors import ErrorBus, SCHOOL


DOMAIN_CONTRACT_SCHEMA = "bilqis.akasha.domain-contract/v1"
PROJECTION_IDENTITY_SCHEMA = "bilqis.akasha.projection-identity/v1"
SHA256_HEX_LENGTH = len(hashlib.sha256().hexdigest())


class AkashaDomain(str, Enum):
    SEMANTIC_GRAPH = "semantic-graph"
    LEARNER_EVIDENCE = "learner-evidence"
    FACTORY_RELEASE_LEDGER = "factory-release-ledger"
    RUN_HISTORY = "run-history"
    RECEIPT_PROVENANCE = "receipt-provenance"
    PROGRAM_OPERATIONS = "program-operations"


def _invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.BAMF_AKASHA.INVALID, reason=reason)


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class DomainContract:
    domain: AkashaDomain
    authority_owner: str
    allowed_operations: tuple[str, ...]
    stable_identity_classes: tuple[str, ...]
    exact_identity_classes: tuple[str, ...]
    rebuild_sources: tuple[str, ...]
    projection_schema: str
    stale_behavior: str
    cross_domain_targets: tuple[AkashaDomain, ...]
    schema_version: str = DOMAIN_CONTRACT_SCHEMA

    def __post_init__(self) -> None:
        sequences = (
            self.allowed_operations,
            self.stable_identity_classes,
            self.exact_identity_classes,
            self.rebuild_sources,
        )
        if (not isinstance(self.domain, AkashaDomain)
                or not self.authority_owner
                or not self.projection_schema
                or not self.stale_behavior
                or self.schema_version != DOMAIN_CONTRACT_SCHEMA
                or any(not values or len(values) != len(set(values))
                       for values in sequences)
                or len(self.cross_domain_targets) != len(set(self.cross_domain_targets))
                or self.domain in self.cross_domain_targets):
            _invalid("AKASHA_DOMAIN_CONTRACT_INVALID")

    def to_record(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "domain": self.domain.value,
            "authority_owner": self.authority_owner,
            "allowed_operations": self.allowed_operations,
            "stable_identity_classes": self.stable_identity_classes,
            "exact_identity_classes": self.exact_identity_classes,
            "rebuild_sources": self.rebuild_sources,
            "projection_schema": self.projection_schema,
            "stale_behavior": self.stale_behavior,
            "cross_domain_targets": tuple(item.value for item in self.cross_domain_targets),
        }

    @property
    def digest(self) -> str:
        return _digest(self.to_record())


def _contract(domain, owner, operations, stable, exact, rebuild, projection, targets):
    return DomainContract(
        domain, owner, operations, stable, exact, rebuild, projection,
        "reject-stale-or-mismatched-projection-identity",
        targets,
    )


_DOMAIN_CONTRACTS = (
    _contract(
        AkashaDomain.SEMANTIC_GRAPH, "semantic-release-authority",
        ("materialize", "rebuild", "supersede"),
        ("semantic_rid", "external_xid"),
        ("semantic_release_sha256", "rdf_digest", "materialization_receipt_sha256"),
        ("immutable_semantic_release", "materialization_receipt"),
        "bilqis.akasha.semantic-graph/v1",
        (AkashaDomain.FACTORY_RELEASE_LEDGER, AkashaDomain.RECEIPT_PROVENANCE),
    ),
    _contract(
        AkashaDomain.LEARNER_EVIDENCE, "accepted-learner-evidence-authority",
        ("append", "project", "rebuild"),
        ("run_id", "capability_id"),
        ("generation_manifest_sha256", "acceptance_receipt_sha256", "event_id"),
        ("accepted_generation_manifests", "immutable_assessment_and_learning_events"),
        "bilqis.akasha.learner-evidence/v1",
        (AkashaDomain.RUN_HISTORY, AkashaDomain.RECEIPT_PROVENANCE),
    ),
    _contract(
        AkashaDomain.FACTORY_RELEASE_LEDGER, "factory-release-authority",
        ("append", "project", "rebuild", "supersede"),
        ("factory_release_rid", "capability_id"),
        ("factory_release_sha256", "semantic_release_sha256", "admission_receipt_sha256"),
        ("immutable_factory_releases", "factory_lifecycle_receipts"),
        "bilqis.akasha.factory-release-ledger/v1",
        (AkashaDomain.SEMANTIC_GRAPH, AkashaDomain.RUN_HISTORY,
         AkashaDomain.RECEIPT_PROVENANCE),
    ),
    _contract(
        AkashaDomain.RUN_HISTORY, "bamf-run-authority",
        ("append", "project", "rebuild"),
        ("run_id", "checkpoint_lineage_id"),
        ("generation_manifest_sha256", "checkpoint_sha256", "topology_digest"),
        ("immutable_run_identity", "generation_manifests", "checkpoint_manifests"),
        "bilqis.akasha.run-history/v1",
        (AkashaDomain.FACTORY_RELEASE_LEDGER, AkashaDomain.LEARNER_EVIDENCE,
         AkashaDomain.RECEIPT_PROVENANCE),
    ),
    _contract(
        AkashaDomain.RECEIPT_PROVENANCE, "receipt-source-authority",
        ("append", "index", "rebuild"),
        ("source_rid", "run_id"),
        ("receipt_sha256", "source_receipt_sha256", "event_id"),
        ("immutable_receipts", "accepted_outbox_events"),
        "bilqis.akasha.receipt-provenance/v1",
        tuple(domain for domain in AkashaDomain if domain is not AkashaDomain.RECEIPT_PROVENANCE),
    ),
    _contract(
        AkashaDomain.PROGRAM_OPERATIONS, "program-gate-authority",
        ("append", "project", "rebuild"),
        ("program_id", "run_id"),
        ("gate_receipt_sha256", "policy_digest", "operator_event_id"),
        ("immutable_program_policy", "gate_and_operator_receipts"),
        "bilqis.akasha.program-operations/v1",
        (AkashaDomain.RUN_HISTORY, AkashaDomain.RECEIPT_PROVENANCE),
    ),
)

DOMAIN_CONTRACTS = MappingProxyType(
    dict((contract.domain, contract) for contract in _DOMAIN_CONTRACTS))


@dataclass(frozen=True)
class ProjectionIdentity:
    domain: AkashaDomain
    contract_sha256: str
    source_frontier_sha256: str
    projection_sha256: str
    schema_version: str = PROJECTION_IDENTITY_SCHEMA

    def __post_init__(self) -> None:
        if (self.domain not in DOMAIN_CONTRACTS
                or self.contract_sha256 != DOMAIN_CONTRACTS[self.domain].digest
                or any(not isinstance(value, str) or len(value) != SHA256_HEX_LENGTH
                       for value in (self.source_frontier_sha256, self.projection_sha256))
                or self.schema_version != PROJECTION_IDENTITY_SCHEMA):
            _invalid("AKASHA_PROJECTION_IDENTITY_INVALID")


def rebuild_projection_identity(domain: AkashaDomain, source_records: tuple[dict, ...]):
    contract = DOMAIN_CONTRACTS.get(domain)
    if contract is None or not isinstance(source_records, tuple):
        _invalid("AKASHA_REBUILD_INPUT_INVALID")
    source_frontier = _digest(source_records)
    projection = _digest((contract.to_record(), source_records))
    return ProjectionIdentity(domain, contract.digest, source_frontier, projection)


def require_current_projection(identity: ProjectionIdentity, expected_source_records):
    expected = rebuild_projection_identity(identity.domain, tuple(expected_source_records))
    if identity != expected:
        _invalid("AKASHA_PROJECTION_STALE")
    return identity


def require_domain_operation(domain: AkashaDomain, authority_owner: str, operation: str):
    contract = DOMAIN_CONTRACTS.get(domain)
    if (contract is None or authority_owner != contract.authority_owner
            or operation not in contract.allowed_operations):
        _invalid("AKASHA_DOMAIN_OPERATION_FORBIDDEN")
    return contract


def require_cross_domain_reference(source: AkashaDomain, target: AkashaDomain,
                                   *, stable_identity_class: str,
                                   exact_identity_class: str):
    source_contract = DOMAIN_CONTRACTS.get(source)
    target_contract = DOMAIN_CONTRACTS.get(target)
    if (source_contract is None or target_contract is None
            or target not in source_contract.cross_domain_targets
            or stable_identity_class not in target_contract.stable_identity_classes
            or exact_identity_class not in target_contract.exact_identity_classes):
        _invalid("AKASHA_CROSS_DOMAIN_REFERENCE_FORBIDDEN")
    return target_contract


__all__ = (
    "AkashaDomain", "DomainContract", "DOMAIN_CONTRACTS", "ProjectionIdentity",
    "rebuild_projection_identity", "require_current_projection",
    "require_domain_operation", "require_cross_domain_reference",
)
