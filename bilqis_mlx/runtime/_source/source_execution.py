"""Runtime inputs closed over one verified executable factory release."""
from __future__ import annotations

from bilqis_mlx.errors import ErrorBus, FACTORY, SCHOOL
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from ..factory.adapters import SourceAdapterRegistry
from ..factory.answers import AnswerModalityRegistry
from ..factory.executable_release import ExecutableFactoryRelease


from .source_batch_authority import (
    SourceBatchAuthority, bind_delivery_rows as _bind_delivery_rows,
    bind_rows as _bind_rows, draw_bound_rows as _draw_bound_rows,
    _source_family,
    require_bound_rows as _require_bound_rows,
    source_content_digest,
)


@dataclass
class SourcePreparationMetrics:
    provider_draws: int = 0
    source_context_builds: int = 0
    compiled_source_builds: int = 0


def _invalid_source_batch(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_TRAINING_ADAPTER.INVALID, reason=reason)


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
        return _draw_bound_rows(self, seed=seed, capability=capability, each=each)

    def require_bound_rows(
            self, rows, authority: SourceBatchAuthority) -> SourceBatchAuthority:
        """Verify exact rows against owner-issued authority without redrawing them."""
        return _require_bound_rows(self, rows, authority)

    def bind_rows(self, rows, *, seed: int, capability: str,
                  each: int) -> SourceBatchAuthority:
        """Issue process-live authority only for an exact owner-redrawn batch."""
        return _bind_rows(self, rows, seed=seed, capability=capability, each=each)

    def bind_delivery_rows(self, rows, *, seed: int, capability: str,
                           direct_each: int) -> SourceBatchAuthority:
        """Bind the exact direct draw plus Factory-released optional teaching rows."""
        return _bind_delivery_rows(
            self, rows, seed=seed, capability=capability, direct_each=direct_each)


__all__ = (
    "SourceBatchAuthority", "SourceExecutionContext", "SourcePreparationMetrics",
    "source_content_digest",
)
