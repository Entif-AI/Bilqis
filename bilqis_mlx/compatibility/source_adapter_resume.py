"""Exact one-way source-adapter compatibility for sealed historical receipts.

Compatibility lives here rather than in the generic factory or the provider
implementation. That keeps grade/provider history out of generic control flow and
avoids changing the provider fingerprint merely to explain an old receipt.
"""
from __future__ import annotations

from dataclasses import replace
from bilqis_mlx.errors import ErrorBus, FACTORY
from .source_adapter_resume_edges import (
    SUPPORTED_SOURCE_PROVIDER_RESUME_EDGES, SourceProviderResumeEdge,
)


_NUMERIC_ADAPTER_ID = "source.finite-numeric/v2"
_NUMERIC_IMPLEMENTATION = (
    "2758cf678e9d2a45f3f5a1b5edd85d5ae513e54506c0d98853b9402b91572754")
_NUMERIC_MODULAR_IMPLEMENTATION = (
    "a52f346478852775053f07a79342e5a9e9266bc64a2df6fe953d6a64881c8b7d")
_NUMERIC_CURRENT_IMPLEMENTATION = (
    "621257de25895cc5cfcf0b9730c43fbe04260a3aa68732cfcc41a43988cd8141")
_GRADE_A_ADAPTER_ID = "source.micro.predicates/v1"
_GRADE_A_ACCEPTED_IMPLEMENTATION = (
    "c451c3e6bf5ab538450c691d504230036b9a729ddfc67b53163c6a1f106d62a9")
_GRADE_A_CURRENT_IMPLEMENTATION = (
    "7f05ec04d200d7394f32ed1811a3d9a47ce4cdb9267692bf558453e81e9fb04a")
_GRADE_A_1324082_IMPLEMENTATION = (
    "f8e5aec9398538adc633deabe9c41c485e69a96044b9b86a5f1075ce6e201778")
_GRADE_A_BASE_VARIATION_AXES = (
    "source-valid", "balanced-gold", "fresh-seed",
    "member-decoy-set-context-v1", "irrelevant-source-context-v2",
)
_GRADE_A_1324082_VARIATION_AXES = (
    *_GRADE_A_BASE_VARIATION_AXES, "generalization-only-source-context-v3",
)
_BOOLEAN_IDENTIFICATION_ADAPTER_ID = "source.micro.boolean-identification/v1"
_BOOLEAN_IDENTIFICATION_ACCEPTED_IMPLEMENTATION = (
    "6399dae052a289d46063df0e897e14f1392e2f1b99e90c2ae791fda9a8246743")
_BOOLEAN_IDENTIFICATION_CURRENT_IMPLEMENTATION = (
    "1404c511d7b5eab19025726d5c4c98073250cc0c75cf37b185344da92060edee")
_NUMERIC_STAIRCASE_RELEASE = "bilqis.mlx.numeric-staircase/20261017-v1"
_PRE_ADR106_NUMERIC_STAIRCASE_DIGEST = (
    "ec3b5338fc1604a6250a847ee99eae09956b5a5bb269a63f3ac8372205133e74")
_ADR106_NUMERIC_STAIRCASE_DIGEST = (
    "9faf5dd6183657c91753394c0bfa6376849c47594f7e9eb4cb4e5f86c008b235")


def _numeric_adr106_pair(admitted, current) -> bool:
    """Recognize only the exact pre-ADR-106 -> ADR-106 staircase repair."""
    if (admitted is None or
            admitted.adapter_id != current.adapter_id or
            admitted.adapter_id != _NUMERIC_ADAPTER_ID or
            admitted.implementation_sha256 != current.implementation_sha256 or
            admitted.implementation_sha256 not in (
                _NUMERIC_IMPLEMENTATION,
                _NUMERIC_MODULAR_IMPLEMENTATION,
                _NUMERIC_CURRENT_IMPLEMENTATION,
            )):
        return False
    admitted_releases = dict(admitted.cohort_releases)
    current_releases = dict(current.cohort_releases)
    if (set(admitted_releases) != set(current_releases) or
            admitted_releases.get(_NUMERIC_STAIRCASE_RELEASE) !=
            _PRE_ADR106_NUMERIC_STAIRCASE_DIGEST or
            current_releases.get(_NUMERIC_STAIRCASE_RELEASE) !=
            _ADR106_NUMERIC_STAIRCASE_DIGEST):
        return False
    if any(
            admitted_releases[name] != current_releases[name]
            for name in admitted_releases
            if name != _NUMERIC_STAIRCASE_RELEASE):
        return False
    return (
        admitted.generator_id == current.generator_id and
        admitted.accepted_oracle_ids == current.accepted_oracle_ids and
        admitted.cohort_generator_id == current.cohort_generator_id and
        admitted.variation_axes == current.variation_axes and
        admitted.teaching_option_ids == current.teaching_option_ids and
        admitted.profile_dimensions == current.profile_dimensions)


def _numeric_modular_pair(admitted, current) -> bool:
    """Exact behavior-preserving school-owner extraction; no arbitrary drift."""
    if (admitted is None or admitted.adapter_id != _NUMERIC_ADAPTER_ID
            or admitted.implementation_sha256 not in (
                _NUMERIC_IMPLEMENTATION, _NUMERIC_MODULAR_IMPLEMENTATION)
            or current.implementation_sha256 not in (
                _NUMERIC_MODULAR_IMPLEMENTATION, _NUMERIC_CURRENT_IMPLEMENTATION)):
        return False
    migrated = replace(admitted, implementation_sha256=current.implementation_sha256)
    return migrated == current or _numeric_adr106_pair(migrated, current)


def _cohort_bound_implementation_pair(
        admitted, current, *, adapter_id: str,
        admitted_sha256: str, current_sha256: str) -> bool:
    """Recognize an exact provider refresh whose cohort seal changed with its code seal."""
    if (admitted is None
            or admitted.adapter_id != adapter_id
            or current.adapter_id != adapter_id
            or admitted.implementation_sha256 != admitted_sha256
            or current.implementation_sha256 != current_sha256):
        return False
    migrated_cohorts = tuple(
        (release, current_sha256 if digest == admitted_sha256 else digest)
        for release, digest in admitted.cohort_releases
    )
    return replace(
        admitted,
        implementation_sha256=current_sha256,
        cohort_releases=migrated_cohorts,
    ) == current


def _accepted_school_provider_pair(admitted, current) -> bool:
    return (
        _grade_a_1324082_pair(admitted, current)
        or
        _cohort_bound_implementation_pair(
            admitted, current,
            adapter_id=_GRADE_A_ADAPTER_ID,
            admitted_sha256=_GRADE_A_ACCEPTED_IMPLEMENTATION,
            current_sha256=_GRADE_A_CURRENT_IMPLEMENTATION,
        )
        or _cohort_bound_implementation_pair(
            admitted, current,
            adapter_id=_BOOLEAN_IDENTIFICATION_ADAPTER_ID,
            admitted_sha256=_BOOLEAN_IDENTIFICATION_ACCEPTED_IMPLEMENTATION,
            current_sha256=_BOOLEAN_IDENTIFICATION_CURRENT_IMPLEMENTATION,
        )
    )


def _grade_a_1324082_pair(admitted, current) -> bool:
    """Compose the exact ADR-099 rollback identity through the current provider."""
    if (admitted is None
            or admitted.adapter_id != current.adapter_id
            or admitted.adapter_id != _GRADE_A_ADAPTER_ID
            or admitted.implementation_sha256 != _GRADE_A_1324082_IMPLEMENTATION
            or current.implementation_sha256 not in (
                _GRADE_A_ACCEPTED_IMPLEMENTATION, _GRADE_A_CURRENT_IMPLEMENTATION)
            or admitted.generator_id != current.generator_id
            or admitted.accepted_oracle_ids != current.accepted_oracle_ids
            or admitted.cohort_generator_id != current.cohort_generator_id
            or admitted.teaching_option_ids != current.teaching_option_ids
            or admitted.profile_dimensions != current.profile_dimensions
            or admitted.variation_axes != _GRADE_A_1324082_VARIATION_AXES
            or len(admitted.cohort_releases) != 1
            or len(current.cohort_releases) != 1
            or admitted.cohort_releases[0][0] != current.cohort_releases[0][0]
            or admitted.cohort_releases[0][1] != _GRADE_A_1324082_IMPLEMENTATION):
        return False
    intermediate = replace(
        admitted,
        implementation_sha256=_GRADE_A_ACCEPTED_IMPLEMENTATION,
        cohort_releases=((
            admitted.cohort_releases[0][0], _GRADE_A_ACCEPTED_IMPLEMENTATION),),
        variation_axes=_GRADE_A_BASE_VARIATION_AXES,
    )
    if current.implementation_sha256 == _GRADE_A_ACCEPTED_IMPLEMENTATION:
        return intermediate == current
    return _cohort_bound_implementation_pair(
        intermediate, current,
        adapter_id=_GRADE_A_ADAPTER_ID,
        admitted_sha256=_GRADE_A_ACCEPTED_IMPLEMENTATION,
        current_sha256=_GRADE_A_CURRENT_IMPLEMENTATION,
    )


def resume_adapter_compatible(admitted, current) -> bool:
    """Return true only for explicitly proven historical descriptor migrations."""
    if admitted is None or current is None:
        return False
    matches = tuple(
        edge for edge in SUPPORTED_SOURCE_PROVIDER_RESUME_EDGES
        if (edge.adapter_id == admitted.adapter_id == current.adapter_id
            and edge.admitted_implementation_sha256 == admitted.implementation_sha256
            and edge.current_implementation_sha256 == current.implementation_sha256)
    )
    for edge in matches:
        if edge.rule == "grade-a-1324082" and _grade_a_1324082_pair(admitted, current):
            return True
        if edge.rule == "cohort-bound" and _accepted_school_provider_pair(admitted, current):
            return True
        if edge.rule == "numeric-modular" and _numeric_modular_pair(admitted, current):
            return True
        if edge.rule == "numeric-adr106" and _numeric_adr106_pair(admitted, current):
            return True
    return False


def predecessor_compatible_source_registry(predecessor, current_registry):
    """Bind current callables to predecessor-sealed descriptors for successor staging.

    Candidate staging is append-only. Recompiling a successor must therefore not
    silently rewrite every predecessor capability merely because a behavior-
    preserving provider refactor has a newer implementation digest. This view
    retains the accepted descriptors only for exact, explicitly compatible pairs;
    genuinely new providers keep their current descriptor.
    """
    from bilqis_mlx.factory.adapters import (
        RegisteredSourceAdapter,
        SourceAdapterRegistry,
    )

    if not isinstance(current_registry, SourceAdapterRegistry):
        ErrorBus.Raise(
            FACTORY.SOURCE_ADAPTER.COMPATIBILITY_INVALID,
            reason="PREDECESSOR_COMPATIBLE_SOURCE_REGISTRY_REQUIRED")
    admitted = {
        descriptor.adapter_id: descriptor
        for descriptor in predecessor.source_adapters
    }
    if len(admitted) != len(predecessor.source_adapters):
        ErrorBus.Raise(
            FACTORY.SOURCE_ADAPTER.COMPATIBILITY_INVALID,
            reason="PREDECESSOR_SOURCE_ADAPTER_DUPLICATE")

    class _PredecessorCompatibleRegistry(SourceAdapterRegistry):
        def __init__(self):
            super().__init__()

        @staticmethod
        def _bind(registered):
            sealed = admitted.get(registered.descriptor.adapter_id)
            if sealed is None or sealed == registered.descriptor:
                return registered
            if not resume_adapter_compatible(sealed, registered.descriptor):
                raise ValueError(
                    "FACTORY_SOURCE_ADAPTER_RESUME_UNPROVEN:"
                    + registered.descriptor.adapter_id)
            return replace(registered, descriptor=sealed)

        def require(self, generator_id: str, oracle_id: str) -> RegisteredSourceAdapter:
            return self._bind(current_registry.require(generator_id, oracle_id))

        def resolve_owner(
                self, generator_id: str,
                oracle_id: str | None = None) -> RegisteredSourceAdapter:
            return self._bind(current_registry.resolve_owner(generator_id, oracle_id))

    registry = _PredecessorCompatibleRegistry()
    for descriptor in predecessor.source_adapters:
        registered = current_registry.resolve_owner(descriptor.generator_id)
        registry._bind(registered)
    return registry
