"""Comparable baseline currentness for ADR-142 / #1298."""
from __future__ import annotations

from dataclasses import dataclass

from bilqis_mlx.semantics.domains import contract_digest

from ..capability_evaluation import _invalid, _sha
from .lifecycle import (
    COMPARISON_SCHEMA,
    BaselineComparisonIdentity,
    BaselineLedger,
    BaselineLifecycleState,
)


@dataclass(frozen=True)
class BaselineComparisonEpoch:
    factory_release_sha256: str
    semantic_catalog_sha256: str
    rubric_sha256: str
    scope_sha256: str
    policy_sha256: str
    source_sha256: str
    source_authority_registry_sha256: str | None
    correction_frontier_sha256: str
    evaluation_contract_sha256: str
    fixed_cohort_sha256: str
    evidence_stage: str
    schema: str = "bilqis.mlx.c05-baseline-comparison-epoch/v1"

    def __post_init__(self):
        digests = (
            self.factory_release_sha256,
            self.semantic_catalog_sha256,
            self.rubric_sha256,
            self.scope_sha256,
            self.policy_sha256,
            self.source_sha256,
            self.correction_frontier_sha256,
            self.evaluation_contract_sha256,
            self.fixed_cohort_sha256,
        )
        if (any(not _sha(value) for value in digests)
                or (self.source_authority_registry_sha256 is not None
                    and not _sha(self.source_authority_registry_sha256))
                or not isinstance(self.evidence_stage, str) or not self.evidence_stage
                or self.schema != "bilqis.mlx.c05-baseline-comparison-epoch/v1"):
            _invalid("BAMF_C05_BASELINE_COMPARISON_EPOCH_INVALID")

    @property
    def digest(self) -> str:
        return contract_digest(self)

    def identity(self, capability_id: str) -> BaselineComparisonIdentity:
        return BaselineComparisonIdentity(
            capability_id=capability_id,
            factory_release_sha256=self.factory_release_sha256,
            semantic_catalog_sha256=self.semantic_catalog_sha256,
            rubric_sha256=self.rubric_sha256,
            scope_sha256=self.scope_sha256,
            policy_sha256=self.policy_sha256,
            source_sha256=self.source_sha256,
            source_authority_registry_sha256=self.source_authority_registry_sha256,
            correction_frontier_sha256=self.correction_frontier_sha256,
            evaluation_contract_sha256=self.evaluation_contract_sha256,
            fixed_cohort_sha256=self.fixed_cohort_sha256,
            evidence_stage=self.evidence_stage,
            schema=COMPARISON_SCHEMA,
        )


@dataclass(frozen=True)
class BaselineCoverage:
    measured_capabilities: tuple[str, ...]
    unmeasured_capabilities: tuple[str, ...]
    group_denominators: tuple[tuple[str, int, int], ...]
    measured_denominator: int
    total_capabilities: int
    epoch_sha256: str
    schema: str = "bilqis.mlx.c05-baseline-coverage/v1"

    def __post_init__(self):
        measured = set(self.measured_capabilities)
        unmeasured = set(self.unmeasured_capabilities)
        group_names = tuple(group for group, _measured, _total in self.group_denominators)
        if (len(measured) != len(self.measured_capabilities)
                or len(unmeasured) != len(self.unmeasured_capabilities)
                or measured.intersection(unmeasured)
                or len(set(group_names)) != len(group_names)
                or self.measured_denominator != len(self.measured_capabilities)
                or self.total_capabilities != len(measured | unmeasured)
                or sum(item[1] for item in self.group_denominators)
                != self.measured_denominator
                or sum(item[2] for item in self.group_denominators)
                != self.total_capabilities
                or not _sha(self.epoch_sha256)
                or any(not isinstance(group, str) or not group
                       or type(measured_count) is not int or type(total_count) is not int
                       or not 0 <= measured_count <= total_count
                       for group, measured_count, total_count in self.group_denominators)
                or self.schema != "bilqis.mlx.c05-baseline-coverage/v1"):
            _invalid("BAMF_C05_BASELINE_COVERAGE_INVALID")

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "epoch_sha256": self.epoch_sha256,
            "measured_capabilities": list(self.measured_capabilities),
            "unmeasured_capabilities": list(self.unmeasured_capabilities),
            "measured_denominator": self.measured_denominator,
            "total_capabilities": self.total_capabilities,
            "group_denominators": [
                {"group": group, "measured": measured, "total": total}
                for group, measured, total in self.group_denominators
            ],
        }

    @classmethod
    def from_record(cls, record) -> "BaselineCoverage":
        if (not isinstance(record, dict)
                or set(record) != {
                    "schema", "epoch_sha256", "measured_capabilities",
                    "unmeasured_capabilities", "measured_denominator",
                    "total_capabilities", "group_denominators",
                }
                or not isinstance(record.get("measured_capabilities"), list)
                or not isinstance(record.get("unmeasured_capabilities"), list)
                or not isinstance(record.get("group_denominators"), list)
                or any(not isinstance(item, dict)
                       or set(item) != {"group", "measured", "total"}
                       for item in record.get("group_denominators", []))):
            _invalid("BAMF_C05_BASELINE_COVERAGE_INVALID")
        return cls(
            tuple(record["measured_capabilities"]),
            tuple(record["unmeasured_capabilities"]),
            tuple((item["group"], item["measured"], item["total"])
                  for item in record["group_denominators"]),
            record["measured_denominator"],
            record["total_capabilities"],
            record["epoch_sha256"],
            record["schema"],
        )

    def protected_capabilities(self, target_capability: str) -> tuple[str, ...]:
        return tuple(
            capability for capability in self.measured_capabilities
            if capability != target_capability)


def baseline_coverage(
        ledger: BaselineLedger,
        epoch: BaselineComparisonEpoch,
        capability_groups: tuple[tuple[str, str], ...],
) -> BaselineCoverage:
    if type(ledger) is not BaselineLedger or type(epoch) is not BaselineComparisonEpoch:
        _invalid("BAMF_C05_BASELINE_COVERAGE_INPUT_INVALID")
    capabilities = tuple(capability for capability, _group in capability_groups)
    groups = tuple(dict.fromkeys(group for _capability, group in capability_groups))
    if (not capabilities or len(set(capabilities)) != len(capabilities)
            or not groups):
        _invalid("BAMF_C05_BASELINE_COVERAGE_INPUT_INVALID")
    measured = tuple(
        capability for capability in capabilities
        if ledger.state_for(epoch.identity(capability)) is not BaselineLifecycleState.UNMEASURED)
    measured_set = set(measured)
    unmeasured = tuple(capability for capability in capabilities if capability not in measured_set)
    denominators = tuple(
        (
            group,
            sum(1 for capability, member_group in capability_groups
                if member_group == group and capability in measured_set),
            sum(1 for _capability, member_group in capability_groups if member_group == group),
        )
        for group in groups
    )
    return BaselineCoverage(
        measured,
        unmeasured,
        denominators,
        len(measured),
        len(capabilities),
        epoch.digest,
    )


__all__ = (
    "BaselineComparisonEpoch",
    "BaselineCoverage",
    "baseline_coverage",
)
