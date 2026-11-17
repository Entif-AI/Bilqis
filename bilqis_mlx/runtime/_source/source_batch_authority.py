"""Process-live authority for exact source and Factory-composed delivery batches."""
from __future__ import annotations

from dataclasses import dataclass, field

from bilqis_mlx.factory.teaching import content_digest, optional_teaching_rows
from bilqis_mlx.semantics.domains import contract_digest


_ISSUER = object()
_DERIVED_ROW_KEYS = frozenset(("grade", "native_output", "auxiliary_labels"))


def _invalid(reason: str):
    from bilqis_mlx.errors import ErrorBus, SCHOOL
    ErrorBus.raise_(SCHOOL.BAMF_TRAINING_ADAPTER.INVALID, reason=reason)


def source_content_digest(rows) -> str:
    """Digest source-owned row content without derived/reporting fields."""
    return content_digest(tuple(
        {key: value for key, value in row.items() if key not in _DERIVED_ROW_KEYS}
        for row in rows))


def _source_family(execution) -> str:
    return contract_digest({
        "schema": "bilqis.mlx.source-draw-family/v1",
        "provider": execution.provider_id,
        "implementation": execution.provider_implementation_sha256,
        "capability": execution.capability_id,
    })


def _source_family_for_rows(execution, rows) -> str:
    declared = tuple(row.get("source_family_id") for row in rows)
    present = tuple(value for value in declared if value is not None)
    if present:
        if (len(present) != len(declared)
                or any(not isinstance(value, str) or not value for value in present)
                or len(set(present)) != 1):
            _invalid("FACTORY_SOURCE_FAMILY_IDENTITY_DRIFT")
        return present[0]
    return _source_family(execution)


def _source_episode(family: str, row: dict) -> str:
    declared = row.get("episode_id")
    return declared if isinstance(declared, str) and declared else row["id"]


@dataclass(frozen=True, init=False)
class SourceBatchAuthority:
    release_sha256: str
    capability_id: str
    provider_id: str
    provider_implementation_sha256: str
    seed: int
    each: int
    content_sha256: str
    source_family_id: str
    episode_ids: tuple[str, ...]
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("FACTORY_SOURCE_BATCH_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self):
        if (getattr(self, "_issuance", None) is not _ISSUER
                or not all(isinstance(value, str) and value for value in (
                    self.release_sha256, self.capability_id, self.provider_id,
                    self.provider_implementation_sha256, self.content_sha256,
                    self.source_family_id))
                or type(self.seed) is not int or self.seed < 0
                or type(self.each) is not int or self.each < 1
                or type(self.episode_ids) is not tuple
                or len(self.episode_ids) != self.each
                or any(not isinstance(value, str) or not value
                       for value in self.episode_ids)):
            _invalid("FACTORY_SOURCE_BATCH_AUTHORITY_INVALID")


def _issue(context, rows, *, seed: int, capability: str) -> SourceBatchAuthority:
    execution = context.release.execution_plan.capability_map[capability]
    family = _source_family_for_rows(execution, rows)
    authority = object.__new__(SourceBatchAuthority)
    values = (
        ("release_sha256", context.release.release_sha256), ("capability_id", capability),
        ("provider_id", execution.provider_id),
        ("provider_implementation_sha256", execution.provider_implementation_sha256),
        ("seed", seed), ("each", len(rows)), ("content_sha256", source_content_digest(rows)),
        ("source_family_id", family),
        ("episode_ids", tuple(_source_episode(family, row) for row in rows)),
        ("_issuance", _ISSUER),
    )
    for name, value in values:
        object.__setattr__(authority, name, value)
    authority.__post_init__()
    return authority


def draw_bound_rows(context, *, seed: int, capability: str, each: int):
    if (type(seed) is not int or seed < 0 or not isinstance(capability, str)
            or not capability or type(each) is not int or each < 1):
        _invalid("FACTORY_SOURCE_BATCH_BINDING_INVALID")
    context.require_capabilities((capability,))
    rows = tuple(context.draw_rows(seed=seed, capability=capability, each=each))
    if len(rows) != each or any(type(row) is not dict for row in rows):
        _invalid("FACTORY_SOURCE_BATCH_BINDING_INVALID")
    return rows, _issue(context, rows, seed=seed, capability=capability)


def require_bound_rows(context, rows, authority: SourceBatchAuthority):
    if type(authority) is not SourceBatchAuthority or not isinstance(rows, (tuple, list)):
        _invalid("FACTORY_SOURCE_BATCH_AUTHORITY_INVALID")
    authority.__post_init__()
    rows = tuple(rows)
    if (authority.release_sha256 != context.release.release_sha256
            or authority.capability_id not in context.release.execution_plan.capability_map
            or len(rows) != authority.each
            or any(type(row) is not dict for row in rows)):
        _invalid("FACTORY_SOURCE_BATCH_AUTHORITY_INVALID")
    expected = _issue(context, rows, seed=authority.seed, capability=authority.capability_id)
    if any(getattr(authority, name) != getattr(expected, name) for name in (
            "provider_id", "provider_implementation_sha256", "content_sha256",
            "source_family_id", "episode_ids")):
        _invalid("FACTORY_SOURCE_BATCH_CONTENT_DRIFT")
    return authority


def bind_rows(context, rows, *, seed: int, capability: str, each: int):
    if not isinstance(rows, (tuple, list)) or not rows:
        _invalid("FACTORY_SOURCE_BATCH_BINDING_INVALID")
    expected, authority = draw_bound_rows(
        context, seed=seed, capability=capability, each=each)
    if source_content_digest(rows) != source_content_digest(expected):
        _invalid("FACTORY_SOURCE_BATCH_CONTENT_DRIFT")
    return authority


def bind_delivery_rows(context, rows, *, seed: int, capability: str, direct_each: int):
    if not isinstance(rows, (tuple, list)) or not rows or type(direct_each) is not int or direct_each < 1:
        _invalid("FACTORY_SOURCE_BATCH_BINDING_INVALID")
    direct = tuple(context.draw_rows(seed=seed, capability=capability, each=direct_each))
    enrichment = optional_teaching_rows(
        context.source_root, context.graph, context.release, context.source_registry,
        capability=capability, seed=seed, enabled=True)
    expected = (*direct, *enrichment)
    if source_content_digest(rows) != source_content_digest(expected):
        _invalid("FACTORY_SOURCE_BATCH_CONTENT_DRIFT")
    return _issue(context, tuple(rows), seed=seed, capability=capability)


# Preserve the historical import identity while implementation lives in this owner module.
SourceBatchAuthority.__module__ = "bilqis_mlx.runtime._source.source_execution"

__all__ = (
    "SourceBatchAuthority", "bind_delivery_rows", "bind_rows", "draw_bound_rows",
    "require_bound_rows", "source_content_digest",
)
