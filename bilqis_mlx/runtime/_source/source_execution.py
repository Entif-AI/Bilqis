"""Runtime inputs closed over one verified executable factory release."""
from __future__ import annotations

from bilqis_mlx.errors import ErrorBus, FACTORY, SCHOOL
from bilqis_mlx.factory.teaching import content_digest
from bilqis_mlx.semantics.domains import contract_digest

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from ..factory.adapters import SourceAdapterRegistry
from ..factory.answers import AnswerModalityRegistry
from ..factory.executable_release import ExecutableFactoryRelease


_SOURCE_BATCH_ISSUER = object()
_DERIVED_ROW_KEYS = frozenset(("grade", "native_output", "auxiliary_labels"))


@dataclass
class SourcePreparationMetrics:
    provider_draws: int = 0
    source_context_builds: int = 0
    compiled_source_builds: int = 0


def _invalid_source_batch(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_TRAINING_ADAPTER.INVALID, reason=reason)


def _source_content(rows) -> str:
    return content_digest(tuple(
        {key: value for key, value in row.items() if key not in _DERIVED_ROW_KEYS}
        for row in rows))


def source_content_digest(rows) -> str:
    """Digest source-owned row content without derived/reporting fields."""
    return _source_content(rows)


def _source_family(execution) -> str:
    """Stable fallback family for a released provider/capability binding.

    A draw seed identifies an episode/sample, never the underlying source family.
    Source-owned explicit family metadata takes precedence in ``bind_rows``.
    """
    return contract_digest({
        "schema": "bilqis.mlx.source-draw-family/v1",
        "provider": execution.provider_id,
        "implementation": execution.provider_implementation_sha256,
        "capability": execution.capability_id,
    })


def _source_episode(family: str, row: dict) -> str:
    declared = row.get("episode_id")
    return declared if isinstance(declared, str) and declared else row["id"]


def _source_family_for_rows(execution, rows) -> str:
    declared = tuple(row.get("source_family_id") for row in rows)
    present = tuple(value for value in declared if value is not None)
    if present:
        if (len(present) != len(declared)
                or any(not isinstance(value, str) or not value for value in present)
                or len(set(present)) != 1):
            _invalid_source_batch("FACTORY_SOURCE_FAMILY_IDENTITY_DRIFT")
        return present[0]
    return _source_family(execution)


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
        _invalid_source_batch("FACTORY_SOURCE_BATCH_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self):
        if (getattr(self, "_issuance", None) is not _SOURCE_BATCH_ISSUER
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
            _invalid_source_batch("FACTORY_SOURCE_BATCH_AUTHORITY_INVALID")


@dataclass(frozen=True)
class SourceExecutionContext:
    release: ExecutableFactoryRelease
    graph: dict
    source_root: Path | None
    source_registry: SourceAdapterRegistry
    answer_registry: AnswerModalityRegistry
    run_dir: Path | None = None
    _accepted_runtime_host: object | None = field(
        default=None, init=False, repr=False, compare=False)
    _accepted_feature_context: object | None = field(
        default=None, init=False, repr=False, compare=False)
    _source_preparation_metrics: SourcePreparationMetrics = field(
        default_factory=SourcePreparationMetrics, init=False, repr=False,
        compare=False)
    _execution_by_capability: object | None = field(
        default=None, init=False, repr=False, compare=False)

    @classmethod
    def from_admitted_release(
            cls, run_dir: Path, receipt: dict, *, graph: dict,
            source_root: Path | None, source_registry: SourceAdapterRegistry,
            answer_registry: AnswerModalityRegistry,
            accepted_runtime_host=None,
    ) -> SourceExecutionContext:
        from .admission import (
            _read_executable_factory_release_artifact as _read_executable_factory_release)

        release = _read_executable_factory_release(run_dir, receipt)
        if accepted_runtime_host is not None:
            from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
            if (type(accepted_runtime_host) is not AcceptedRuntimeHost
                    or accepted_runtime_host.run_dir.resolve()
                    != Path(run_dir).resolve()):
                _invalid_source_batch("FACTORY_SOURCE_CORRECTION_RUNTIME_REQUIRED")
            accepted_runtime_host.source_authority()
        context = cls(
            release=release, graph=graph, source_root=source_root,
            source_registry=source_registry, answer_registry=answer_registry,
            run_dir=Path(run_dir))
        if accepted_runtime_host is not None:
            object.__setattr__(context, "_accepted_runtime_host", accepted_runtime_host)
        return context

    def __post_init__(self) -> None:
        if not isinstance(self.release, ExecutableFactoryRelease):
            raise TypeError(FACTORY.EXECUTION.EXPECTED_AN_EXECUTABLEFACTORYRELEASE.legacy_codes[0])
        if not isinstance(self.source_registry, SourceAdapterRegistry):
            raise TypeError(FACTORY.EXECUTION.EXPECTED_A_SOURCEADAPTERREGISTRY.legacy_codes[0])
        if not isinstance(self.answer_registry, AnswerModalityRegistry):
            raise TypeError(FACTORY.EXECUTION.EXPECTED_AN_ANSWERMODALITYREGISTRY.legacy_codes[0])
        if self.run_dir is not None and not isinstance(self.run_dir, Path):
            _invalid_source_batch("FACTORY_SOURCE_RUN_DIR_INVALID")
        self.release.verify()
        self.release.verify_semantic_catalog(self.graph)
        execution_by_capability = {
            item.capability_id: item
            for item in self.release.execution_plan.capabilities
        }
        if len(execution_by_capability) != len(
                self.release.execution_plan.capabilities):
            _invalid_source_batch("FACTORY_SOURCE_EXECUTION_INDEX_INVALID")
        object.__setattr__(
            self, "_execution_by_capability",
            MappingProxyType(execution_by_capability))
        bindings = self.release.source_bindings.by_capability
        for capability in execution_by_capability.values():
            binding = bindings[capability.capability_id]
            self.source_registry.require(binding.generator_id, binding.oracle_id)
        self.answer_registry.validate_plan(self.release.execution_plan)

    def execution_for(self, capability_id: str):
        """Return one prevalidated execution contract without rebuilding plan maps."""
        index = self._execution_by_capability
        if (not isinstance(capability_id, str) or not capability_id
                or index is None):
            _invalid_source_batch("FACTORY_SOURCE_EXECUTION_INDEX_INVALID")
        execution = index.get(capability_id)
        if execution is None:
            _invalid_source_batch("FACTORY_EXECUTION_GENERATION_UNKNOWN_CAPABILITY")
        return execution

    def register_compiled_batch(self, batch) -> None:
        if self.run_dir is None:
            return
        self.require_accepted_runtime(self.run_dir)
        from bilqis_mlx.runtime.accepted_corrections import (
            register_compiled_batch,
        )
        register_compiled_batch(
            self.run_dir, batch)

    def register_solve_context(self, context) -> None:
        if self.run_dir is None:
            return
        self.require_accepted_runtime(self.run_dir)
        from bilqis_mlx.runtime.accepted_corrections import (
            register_solve_context,
        )
        register_solve_context(
            self.run_dir, context)

    def record_correction(self, event) -> str:
        if self.run_dir is None:
            _invalid_source_batch("FACTORY_SOURCE_CORRECTION_RUNTIME_REQUIRED")
        self.require_accepted_runtime(self.run_dir)
        return self._accepted_runtime_host.record_correction(event)

    def record_revalidation(self, frontier) -> str:
        if self.run_dir is None:
            _invalid_source_batch("FACTORY_SOURCE_CORRECTION_RUNTIME_REQUIRED")
        self.require_accepted_runtime(self.run_dir)
        return self._accepted_runtime_host.record_revalidation(frontier)

    def record_remediation(self, remediation) -> str:
        self.require_accepted_runtime(self.run_dir)
        return self._accepted_runtime_host.record_remediation(remediation)

    def record_derived_claim(self, claim):
        self.require_accepted_runtime(self.run_dir)
        return self._accepted_runtime_host.record_derived_claim(claim)

    def require_accepted_runtime(self, run_dir: Path | None) -> None:
        """Require host-owned accepted-run correction custody before execution."""
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost

        host = self._accepted_runtime_host
        if (self.run_dir is None or run_dir is None
                or Path(self.run_dir).resolve() != Path(run_dir).resolve()
                or type(host) is not AcceptedRuntimeHost
                or host.run_dir.resolve() != Path(run_dir).resolve()):
            _invalid_source_batch("FACTORY_SOURCE_CORRECTION_RUNTIME_REQUIRED")
        host.source_authority()

    def source_authority(self):
        """Return the opaque authority owned by this context's current accepted host."""
        self.require_accepted_runtime(self.run_dir)
        return self._accepted_runtime_host.source_authority()

    def require_capabilities(self, capabilities: tuple[str, ...]) -> None:
        """Check a complete host request before any of its providers run."""
        admitted = self.release.execution_plan.capability_map
        if any(capability not in admitted for capability in capabilities):
            raise ErrorBus.legacy_error(FACTORY.EXECUTION.EXECUTABLE_GENERATION_UNKNOWN_CAPABILITY)

    def draw_rows(self, *, seed: int, capability: str | None = None,
                  each: int | None = None) -> list[dict]:
        """Draw only the bound release's admitted capability/provider scope."""
        from ..factory.generation import draw_executable_release_rows

        self._source_preparation_metrics.provider_draws += 1
        return draw_executable_release_rows(
            self.source_root, self.graph, self.release, self.source_registry,
            seed=seed, capability=capability, each=each)

    def draw_bound_rows(self, *, seed: int, capability: str,
                        each: int) -> tuple[tuple[dict, ...], SourceBatchAuthority]:
        """Draw once and issue process-live authority for that exact source batch."""
        if (type(seed) is not int or seed < 0
                or not isinstance(capability, str) or not capability
                or type(each) is not int or each < 1):
            _invalid_source_batch("FACTORY_SOURCE_BATCH_BINDING_INVALID")
        self.require_capabilities((capability,))
        rows = tuple(self.draw_rows(seed=seed, capability=capability, each=each))
        if len(rows) != each or any(type(row) is not dict for row in rows):
            _invalid_source_batch("FACTORY_SOURCE_BATCH_BINDING_INVALID")
        execution = self.release.execution_plan.capability_map[capability]
        content = _source_content(rows)
        family = _source_family_for_rows(execution, rows)
        episodes = tuple(_source_episode(family, row) for row in rows)
        authority = object.__new__(SourceBatchAuthority)
        for name, value in (
                ("release_sha256", self.release.release_sha256),
                ("capability_id", capability),
                ("provider_id", execution.provider_id),
                ("provider_implementation_sha256",
                 execution.provider_implementation_sha256),
                ("seed", seed), ("each", each), ("content_sha256", content),
                ("source_family_id", family), ("episode_ids", episodes),
                ("_issuance", _SOURCE_BATCH_ISSUER)):
            object.__setattr__(authority, name, value)
        authority.__post_init__()
        return rows, authority

    def require_bound_rows(
            self, rows, authority: SourceBatchAuthority) -> SourceBatchAuthority:
        """Verify exact rows against owner-issued authority without redrawing them."""
        if (type(authority) is not SourceBatchAuthority
                or not isinstance(rows, (tuple, list))):
            _invalid_source_batch("FACTORY_SOURCE_BATCH_AUTHORITY_INVALID")
        authority.__post_init__()
        rows = tuple(rows)
        if (authority.release_sha256 != self.release.release_sha256
                or authority.capability_id
                not in self.release.execution_plan.capability_map
                or len(rows) != authority.each
                or any(type(row) is not dict for row in rows)):
            _invalid_source_batch("FACTORY_SOURCE_BATCH_AUTHORITY_INVALID")
        execution = self.release.execution_plan.capability_map[
            authority.capability_id]
        family = _source_family_for_rows(execution, rows)
        episodes = tuple(_source_episode(family, row) for row in rows)
        if (authority.provider_id != execution.provider_id
                or authority.provider_implementation_sha256
                != execution.provider_implementation_sha256
                or authority.content_sha256 != _source_content(rows)
                or authority.source_family_id != family
                or authority.episode_ids != episodes):
            _invalid_source_batch("FACTORY_SOURCE_BATCH_CONTENT_DRIFT")
        return authority

    def bind_rows(self, rows, *, seed: int, capability: str,
                  each: int) -> SourceBatchAuthority:
        """Issue process-live authority only for an exact owner-redrawn batch."""
        if (not isinstance(rows, (tuple, list)) or not rows
                or type(seed) is not int or seed < 0
                or not isinstance(capability, str) or not capability
                or type(each) is not int or each < 1):
            _invalid_source_batch("FACTORY_SOURCE_BATCH_BINDING_INVALID")
        expected, authority = self.draw_bound_rows(
            seed=seed, capability=capability, each=each)
        if _source_content(rows) != _source_content(expected):
            _invalid_source_batch("FACTORY_SOURCE_BATCH_CONTENT_DRIFT")
        return authority


__all__ = (
    "SourceBatchAuthority", "SourceExecutionContext", "SourcePreparationMetrics",
    "source_content_digest",
)
