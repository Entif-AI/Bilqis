"""Exact emitted-row source-owner identity and currentness for B11."""
from __future__ import annotations

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.adapters import RegisteredSourceAdapter, SourceAdapterRegistry
from bilqis_mlx.learning.source_atoms.inputs import SourceAtomRow


_OWNER_CALLABLES = (
    "draw", "check", "enrich", "witness", "dependencies", "semantic_footprint",
)

_LEGACY_ROW_ORACLE_ALIAS = (
    "bilqis.mlx.grade-a-live-constructor/v1",
    "original+independent+grade_a_oracle",
    "bilqis.mlx.grade-a-record-oracle/v2",
)


def invalid_source_execution_authority(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.BAMF_TRAINING_ADAPTER.INVALID, reason=reason)


def _registered_owner_identity(owner: RegisteredSourceAdapter) -> tuple:
    if type(owner) is not RegisteredSourceAdapter:
        invalid_source_execution_authority("B11_SOURCE_EXECUTION_OWNER_INVALID")
    return (
        owner.descriptor,
        *(getattr(owner, name) for name in _OWNER_CALLABLES),
    )


def row_owner_contract(owner: RegisteredSourceAdapter, source: SourceAtomRow) -> tuple:
    row = source.source_row
    descriptor = owner.descriptor
    generator = row.get("generator")
    oracle = row.get("oracle")
    if (not isinstance(generator, str) or not generator
            or not isinstance(oracle, str) or not oracle):
        invalid_source_execution_authority(
            "B11_SOURCE_EXECUTION_OWNER_INPUT_INVALID")
    return (
        generator,
        oracle,
        descriptor.adapter_id,
        descriptor.generator_id,
        descriptor.cohort_generator_id,
        descriptor.implementation_sha256,
    )


def _legacy_row_oracle_alias(generator, oracle):
    legacy_generator, legacy_oracle, canonical_oracle = _LEGACY_ROW_ORACLE_ALIAS
    if (generator, oracle) == (legacy_generator, legacy_oracle):
        return canonical_oracle
    return None


def _current_row_owner(
        registry: SourceAdapterRegistry, source: SourceAtomRow) -> RegisteredSourceAdapter:
    if not isinstance(registry, SourceAdapterRegistry):
        invalid_source_execution_authority(
            "B11_SOURCE_EXECUTION_OWNER_REGISTRY_INVALID")
    row = source.source_row
    generator = row.get("generator")
    oracle = row.get("oracle")
    try:
        return registry.resolve_owner(generator, oracle)
    except (KeyError, TypeError, ValueError):
        canonical_oracle = _legacy_row_oracle_alias(generator, oracle)
        if canonical_oracle is not None:
            try:
                return registry.resolve_owner(generator, canonical_oracle)
            except (KeyError, TypeError, ValueError):
                pass
        invalid_source_execution_authority(
            "B11_SOURCE_EXECUTION_OWNER_UNAVAILABLE")


def require_row_owner(
        owner, registry: SourceAdapterRegistry, source: SourceAtomRow, *, drift: bool):
    current = _current_row_owner(registry, source)
    if _registered_owner_identity(owner) != _registered_owner_identity(current):
        invalid_source_execution_authority(
            "B11_SOURCE_EXECUTION_OWNER_DRIFT"
            if drift else "B11_SOURCE_EXECUTION_OWNER_MISMATCH")
    return current


def require_row_owner_contract(
        owner_contract: tuple, registry: SourceAdapterRegistry, source: SourceAtomRow):
    """Revalidate a sealed owner contract against the accepted execution registry."""
    if type(owner_contract) is not tuple:
        invalid_source_execution_authority("B11_SOURCE_EXECUTION_OWNER_INVALID")
    current = _current_row_owner(registry, source)
    if row_owner_contract(current, source) != owner_contract:
        invalid_source_execution_authority("B11_SOURCE_EXECUTION_OWNER_DRIFT")
    return current


def require_bound_row_owner_current(authority, registry, source: SourceAtomRow):
    """Check the sealed row-owner contract against the live accepted registry."""
    if getattr(authority, "_source", None) is not source:
        invalid_source_execution_authority("B11_SOURCE_EXECUTION_OWNER_INPUT_INVALID")
    require_row_owner_contract(authority.source_owner_contract, registry, source)
    return authority


__all__ = (
    "invalid_source_execution_authority", "require_row_owner",
    "require_bound_row_owner_current", "require_row_owner_contract", "row_owner_contract",
)
