"""Immutable release artifact and manifest contract."""
from __future__ import annotations

from dataclasses import dataclass, field
from ..answers import AnswerModality
from ..curriculum_definition import CurriculumDefinition, SourceBindingSet
from ..execution import CurriculumDelta, CurriculumProfile, ExecutionPlan
from ..model import ProviderDimensionPolicy, SourceAdapter
from .primitives import AnswerHeadBinding, ExecutableVerificationReceipt

from .. import executable_release as _api


@dataclass(frozen=True)
class ExecutableFactoryRelease:
    """Version-2 FactoryRelease; the complete executable authority artifact."""

    schema: str
    curriculum: CurriculumDefinition
    source_bindings: SourceBindingSet
    profile: CurriculumProfile
    execution_plan: ExecutionPlan
    foundation_capability_ids: tuple[str, ...] | None
    semantic_catalog: tuple[str, ...]
    semantic_catalog_sha256: str
    source_adapters: tuple[SourceAdapter, ...]
    answer_modalities: tuple[AnswerModality, ...]
    answer_heads: tuple[AnswerHeadBinding, ...]
    verification: ExecutableVerificationReceipt
    predecessor_release_sha256: str | None
    transition: CurriculumDelta | None
    release_sha256: str
    semantic_graph_sha256: str | None = None
    provider_dimension_policies: tuple[ProviderDimensionPolicy, ...] = ()
    _provider_dimension_policy_wire: bool = field(
        default=True, compare=False, repr=False)
    _foundation_capability_wire: bool = field(
        default=True, compare=False, repr=False)

    def __post_init__(self) -> None:
        if self.semantic_graph_sha256 is not None:
            _api._require_sha256(self.semantic_graph_sha256, _api._ReleaseError.SEMANTIC_GRAPH_INVALID)
        if self.schema != _api.SCHEMA:
            raise ValueError("FACTORY_EXECUTABLE_RELEASE_SCHEMA_INVALID")
        if self.predecessor_release_sha256 is not None:
            _api._require_sha256(
                self.predecessor_release_sha256,
                "FACTORY_EXECUTABLE_RELEASE_PREDECESSOR_INVALID")
        _api._require(
            bool(self.semantic_catalog) and
            len(set(self.semantic_catalog)) == len(self.semantic_catalog) and
            all(isinstance(item, str) and item for item in self.semantic_catalog),
            _api._ReleaseError.CATALOG_INVALID,
        )
        _api._require_sha256(
            self.semantic_catalog_sha256,
            _api._ReleaseError.CATALOG_INVALID)
        _api._require_sha256(
            self.release_sha256, "FACTORY_EXECUTABLE_RELEASE_DIGEST_INVALID")

    def manifest(self) -> dict:
        payload = {
            "schema": self.schema,
            "curriculum": _api.asdict(self.curriculum),
            "source_bindings": _api.asdict(self.source_bindings),
            "profile": _api.asdict(self.profile),
            "execution_plan": _api.asdict(self.execution_plan),
            "semantic_catalog": self.semantic_catalog,
            "semantic_catalog_sha256": self.semantic_catalog_sha256,
            "source_adapters": [
                _api._source_adapter_record(item) for item in self.source_adapters],
            "answer_modalities": [_api.asdict(item) for item in self.answer_modalities],
            "answer_heads": [_api.asdict(item) for item in self.answer_heads],
            "verification": _api.asdict(self.verification),
            "predecessor_release_sha256": self.predecessor_release_sha256,
            "transition": (
                None if self.transition is None else _api.asdict(self.transition)),
        }

        if self._foundation_capability_wire:
            payload["foundation_capability_ids"] = self.foundation_capability_ids
        if self.semantic_graph_sha256 is not None:
            payload["semantic_graph_sha256"] = self.semantic_graph_sha256
        if self._provider_dimension_policy_wire:
            payload["provider_dimension_policies"] = [
                _api.asdict(item) for item in self.provider_dimension_policies]
        return payload

    def expected_digest(self) -> str:
        return _api._digest(self.manifest())

    def require_foundation_capability_ids(self) -> tuple[str, ...]:
        """Return signed foundation authority; historical releases cannot fabricate it."""
        if (not self._foundation_capability_wire
                or self.foundation_capability_ids is None):
            raise ValueError(
                _api._ReleaseError.FOUNDATION_CAPABILITY_IDS_REQUIRED)
        self.verify()
        return self.foundation_capability_ids

    def verify(self) -> None:
        answer_kinds = _api._verify_release_structure(self)
        _api._verify_release_providers(self)
        _api._verify_release_answers(self, answer_kinds)
        _api._verify_release_evidence(self)
        _api._verify_release_assessments(self)
        _api._verify_release_lineage(self)

    def verify_semantic_catalog(self, graph: dict) -> None:
        """Bind the offline release artifact to the exact loaded semantic ABI."""
        names = graph.get("tokens") if isinstance(graph, dict) else None
        _api._require(
            isinstance(names, list) and bool(names) and
            len(set(names)) == len(names) and
            all(isinstance(name, str) and name for name in names),
            _api._ReleaseError.CATALOG_INVALID,
        )
        _api._require(
            tuple(names) == self.semantic_catalog and
            _api._digest(tuple(names)) == self.semantic_catalog_sha256,
            _api._ReleaseError.CATALOG_DRIFT,
        )
        if self.semantic_graph_sha256 is not None:
            _api._require(_api._digest(graph) == self.semantic_graph_sha256,
                     _api._ReleaseError.SEMANTIC_GRAPH_DRIFT)
        for head in self.answer_heads:
            if any(
                    token_id >= len(names) or
                    names[token_id] != identity
                    for identity, token_id in zip(
                        head.semantic_identities, head.token_ids)):
                raise ValueError(
                    "FACTORY_EXECUTABLE_RELEASE_ANSWER_HEAD_CATALOG_DRIFT")

    def verify_successor_of(self, predecessor: "ExecutableFactoryRelease") -> None:
        """Verify persisted lineage against the actual predecessor artifact."""
        if not isinstance(predecessor, _api.ExecutableFactoryRelease):
            raise TypeError("FACTORY_EXECUTABLE_RELEASE_PREDECESSOR_REQUIRED")
        predecessor.verify()
        self.verify()
        if (self.predecessor_release_sha256 != predecessor.release_sha256 or
                self.transition is None or
                self.transition.previous_plan_sha256 !=
                predecessor.execution_plan.digest() or
                self.transition.previous_curriculum_sha256 !=
                predecessor.execution_plan.curriculum_sha256 or
                self.transition.previous_source_binding_sha256 !=
                predecessor.execution_plan.source_binding_sha256):
            raise ValueError("FACTORY_EXECUTABLE_RELEASE_PREDECESSOR_DRIFT")
        previous = predecessor.semantic_catalog
        current = self.semantic_catalog
        if current == previous:
            expected = _api.SemanticGeometryChange.UNCHANGED.value
        elif current[:len(previous)] == previous:
            expected = _api.SemanticGeometryChange.APPEND_ONLY_EXPANSION.value
        else:
            expected = _api.SemanticGeometryChange.INCOMPATIBLE.value
        if (expected == _api.SemanticGeometryChange.INCOMPATIBLE.value or
                self.transition.semantic_geometry != expected):
            raise ValueError(_api._ReleaseError.LINEAGE_DRIFT)

    @classmethod
    def from_manifest(
            cls, payload: dict, release_sha256: str) -> "ExecutableFactoryRelease":
        """Decode v2 data without importing provider implementations."""
        try:
            curriculum = _api._decode_curriculum(payload["curriculum"])
            bindings = _api._decode_source_bindings(payload["source_bindings"])
            profile = _api._decode_profile(payload["profile"])
            plan = _api._decode_plan(payload["execution_plan"])
            verification = _api._decode_verification(payload["verification"])
            foundation_wire = "foundation_capability_ids" in payload
            policy_wire = "provider_dimension_policies" in payload
            policies = tuple(
                _api.ProviderDimensionPolicy(**_api._tuples(item))
                for item in payload.get("provider_dimension_policies", ()))
            transition = (
                None if payload["transition"] is None
                else _api.CurriculumDelta(**_api._tuples(payload["transition"])))
            release = cls(
                schema=payload["schema"],
                curriculum=curriculum,
                source_bindings=bindings,
                profile=profile,
                execution_plan=plan,
                foundation_capability_ids=(
                    _api._tuples(payload["foundation_capability_ids"])
                    if foundation_wire else None),
                semantic_catalog=_api._tuples(payload["semantic_catalog"]),
                semantic_catalog_sha256=payload["semantic_catalog_sha256"],
                source_adapters=tuple(
                    _api.SourceAdapter(**_api._tuples(item))
                    for item in payload["source_adapters"]),
                answer_modalities=tuple(
                    _api.AnswerModality(**item) for item in payload["answer_modalities"]),
                answer_heads=tuple(
                    _api.AnswerHeadBinding(**_api._tuples(item))
                    for item in payload["answer_heads"]),
                verification=verification,
                predecessor_release_sha256=payload["predecessor_release_sha256"],
                transition=transition,
                release_sha256=release_sha256,
                semantic_graph_sha256=payload.get("semantic_graph_sha256"),
                provider_dimension_policies=policies,
                _provider_dimension_policy_wire=policy_wire,
                _foundation_capability_wire=foundation_wire,
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError("FACTORY_EXECUTABLE_RELEASE_MANIFEST_INVALID") from exc
        if _api._digest(payload) != release_sha256:
            raise ValueError("FACTORY_EXECUTABLE_RELEASE_MANIFEST_CONTENT_DRIFT")
        release.verify()
        return release
