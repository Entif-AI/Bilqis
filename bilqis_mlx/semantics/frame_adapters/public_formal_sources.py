"""Resolve canonical A/B/C source owners before public-formal grants exist."""
from dataclasses import dataclass, field
from pathlib import Path

from ...factory.adapters import RegisteredSourceAdapter
from ...factory.source_identity import canonical_source_adapter
from ...generated_assessment import digest
from bilqis_mlx.b11_observation import note_provider_draw
from ..atlas_projection import FrozenAtlasSnapshot
from ..context_eligibility import (
    PUBLIC_FORMAL, ApprovedContextProjection, ContextPolicy, SourceFrontier,
    TaskScope,
)
from ..domains import contract_digest
from ..frame_schema import SourceSpan
from .common import MAX_PUBLIC_FORMAL_DRAW_EACH, _adapter_fail
from .registry import source_graph_for_adapter as _strategy_graph_for_adapter


_PROJECTION_ISSUER = object()


@dataclass(frozen=True, init=False)
class _PublicFormalProjectionAuthority:
    """Process-local proof that the source owner minted this exact projection."""

    projection: ApprovedContextProjection
    projection_contract_sha256: str
    source_adapter_id: str
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _adapter_fail(
            "BAMF_CONTEXT_PUBLIC_FORMAL_AUTHORITY_CALLER_CONSTRUCTION_FORBIDDEN",
            "<unknown>", SourceSpan(0, 0), "<public-formal>")

    def __post_init__(self) -> None:
        if (
            getattr(self, "_issuance", None) is not _PROJECTION_ISSUER
            or type(self.projection) is not ApprovedContextProjection
            or not isinstance(self.source_adapter_id, str)
            or not self.source_adapter_id
            or self.projection_contract_sha256 != contract_digest(self.projection)
        ):
            _adapter_fail(
                "BAMF_CONTEXT_PUBLIC_FORMAL_AUTHORITY_INVALID",
                self.source_adapter_id, SourceSpan(0, 0), "<public-formal>")


def _issue_public_formal_projection_authority(
    projection: ApprovedContextProjection,
    source_adapter_id: str,
) -> None:
    if type(projection) is not ApprovedContextProjection:
        _adapter_fail(
            "BAMF_CONTEXT_PUBLIC_FORMAL_AUTHORITY_INVALID",
            source_adapter_id, SourceSpan(0, 0), "<public-formal>")
    projection.__post_init__()
    authority = object.__new__(_PublicFormalProjectionAuthority)
    for name, value in (
        ("projection", projection),
        ("projection_contract_sha256", contract_digest(projection)),
        ("source_adapter_id", source_adapter_id),
        ("_issuance", _PROJECTION_ISSUER),
    ):
        object.__setattr__(authority, name, value)
    authority.__post_init__()
    object.__setattr__(projection, "_public_formal_authority", authority)


def _require_public_formal_projection_authority(
    projection: ApprovedContextProjection,
    source_adapter_id: str,
) -> None:
    if type(projection) is not ApprovedContextProjection:
        _adapter_fail(
            "BAMF_CONTEXT_PUBLIC_FORMAL_AUTHORITY_REQUIRED",
            source_adapter_id, SourceSpan(0, 0), "<public-formal>")
    authority = getattr(projection, "_public_formal_authority", None)
    if type(authority) is not _PublicFormalProjectionAuthority:
        _adapter_fail(
            "BAMF_CONTEXT_PUBLIC_FORMAL_AUTHORITY_REQUIRED",
            source_adapter_id, SourceSpan(0, 0), "<public-formal>")
    authority.__post_init__()
    if authority.projection is not projection or authority.source_adapter_id != source_adapter_id:
        _adapter_fail(
            "BAMF_CONTEXT_PUBLIC_FORMAL_AUTHORITY_INVALID",
            source_adapter_id, SourceSpan(0, 0), "<public-formal>")


def canonical_adapter(source_adapter, span):
    """A copied frozen adapter record does not own its supplied callables."""
    adapter_id = getattr(getattr(source_adapter, "descriptor", None), "adapter_id", "<unknown>")
    if not isinstance(source_adapter, RegisteredSourceAdapter):
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_ADAPTER_UNTRUSTED",
                      adapter_id, span, "<public-formal>")
    try:
        canonical = canonical_source_adapter(source_adapter)
    except (IndexError, TypeError, ValueError):
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_ADAPTER_UNTRUSTED",
                      adapter_id, span, "<public-formal>")
    if (source_adapter.descriptor != canonical.descriptor
            or any(getattr(source_adapter, name) is not getattr(canonical, name)
                   for name in ("check", "draw", "enrich", "witness", "dependencies", "semantic_footprint"))):
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_ADAPTER_UNTRUSTED",
                      adapter_id, span, "<public-formal>")
    return canonical


def canonical_graph(source_root, graph, adapter_id, span, row=None):
    root, canonical = source_graph_for_adapter(adapter_id, row=row)
    if Path(source_root).resolve() != root.resolve():
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_SOURCE_ROOT_DRIFT",
                      adapter_id, span, "<public-formal>")
    if digest(graph) != digest(canonical):
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_GRAPH_DRIFT",
                      adapter_id, span, "<public-formal>")
    return root, canonical


def source_graph_for_adapter(adapter_id: str, row=None):
    """Return the repository-owned source graph for a registered formal adapter."""
    return _strategy_graph_for_adapter(adapter_id, row=row)


def verify_draw(adapter, row, source_root, graph, span, seed, each, profile, course):
    adapter_id = adapter.descriptor.adapter_id
    if (type(row) is not dict or type(seed) is not int or type(each) is not int
            or not 1 <= each <= MAX_PUBLIC_FORMAL_DRAW_EACH):
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_DRAW_PROVENANCE_INVALID",
                      adapter_id, span, "<public-formal>")
    arguments = dict(source_root=source_root, graph=graph, course=course,
                     capability=row.get("capability"), seed=seed, each=each)
    if profile is not None:
        arguments["profile_parameters"] = profile
    try:
        note_provider_draw()
        rows = adapter.draw(**arguments)
    except (KeyError, TypeError, ValueError):
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_DRAW_PROVENANCE_INVALID",
                      adapter_id, span, "<public-formal>")
    if not isinstance(rows, (tuple, list)):
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_ROW_IDENTITY_UNVERIFIED",
                      adapter_id, span, "<public-formal>")
    matched = next((candidate for candidate in rows
                    if type(candidate) is dict and candidate == row), None)
    if matched is None:
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_ROW_IDENTITY_UNVERIFIED",
                      adapter_id, span, "<public-formal>")
    return matched


def validate_policy(snapshot, task, frontier, policy, adapter_id, span):
    if (not isinstance(task, TaskScope)
            or not isinstance(frontier, SourceFrontier)
            or not isinstance(policy, ContextPolicy)
            or not isinstance(snapshot, FrozenAtlasSnapshot)
            or snapshot.release_sha256 != task.semantic_release
            or task.purpose is None or task.purpose not in policy.allowed_purposes
            or PUBLIC_FORMAL not in policy.allowed_regimes
            or PUBLIC_FORMAL not in policy.allowed_join_classes
            or policy.rights_epoch != frontier.rights_epoch):
        _adapter_fail("BAMF_CONTEXT_PUBLIC_FORMAL_POLICY_INVALID",
                      adapter_id, span, "<public-formal>")
