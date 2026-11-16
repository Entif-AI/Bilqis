"""Typed evidence, teaching, ledger, and work-item contracts."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

def _require_teaching_provenance(condition: bool) -> None:
    if not condition:
        raise ValueError("AUTONOMY_TEACHING_RECEIPT_PROVENANCE_INVALID")

class EvidenceKind(str, Enum):
    """Learner-facing proof families, distinct from source-generation hygiene."""

    DIRECT = "DIRECT"
    PREREQUISITE = "PREREQUISITE"
    COMPOSITION = "COMPOSITION"
    PROJECTION = "PROJECTION"


@dataclass(frozen=True)
class EvidenceObligation:
    obligation_id: str
    capability_id: str
    kind: EvidenceKind
    key: str
    minimum_specimens: int
    generation_axes: tuple[str, ...]
    requires_capabilities: tuple[str, ...] = ()
    proof_axes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (not self.obligation_id or not self.capability_id or not self.key or
                not isinstance(self.kind, EvidenceKind) or
                type(self.minimum_specimens) is not int or self.minimum_specimens < 1 or
                not self.generation_axes or
                len(set(self.generation_axes)) != len(self.generation_axes) or
                any(not isinstance(item, str) or not item for item in self.generation_axes) or
                len(set(self.requires_capabilities)) != len(self.requires_capabilities) or
                any(not isinstance(item, str) or not item
                    for item in self.requires_capabilities) or
                len(set(self.proof_axes)) != len(self.proof_axes) or
                any(not isinstance(item, str) or not item
                    for item in self.proof_axes)):
            raise ValueError("AUTONOMY_EVIDENCE_OBLIGATION_INVALID")


@dataclass(frozen=True)
class EvidenceReceipt:
    """One observed result for one obligation on one exact student/cohort."""

    obligation_id: str
    evidence_id: str
    checkpoint_sha256: str
    optimizer_step: int
    cohort_sha256: str
    specimen_count: int
    passed: bool

    def __post_init__(self) -> None:
        if not self.obligation_id or not self.evidence_id:
            raise ValueError("AUTONOMY_EVIDENCE_RECEIPT_IDENTITY_INVALID")
        for value, code in (
                (self.checkpoint_sha256, "AUTONOMY_EVIDENCE_CHECKPOINT_INVALID"),
                (self.cohort_sha256, "AUTONOMY_EVIDENCE_COHORT_INVALID")):
            if (not isinstance(value, str) or len(value) != 64 or
                    any(char not in "0123456789abcdef" for char in value)):
                raise ValueError(code)
        if (type(self.optimizer_step) is not int or self.optimizer_step < 0 or
                type(self.specimen_count) is not int or self.specimen_count < 1 or
                type(self.passed) is not bool):
            raise ValueError("AUTONOMY_EVIDENCE_RECEIPT_VALUE_INVALID")


@dataclass(frozen=True)
class TeachingReceipt:
    """One bounded teaching intervention after one failed evidence receipt."""

    obligation_id: str
    intervention_id: str
    teaching_option_id: str
    parent_checkpoint_sha256: str
    parent_optimizer_step: int
    checkpoint_sha256: str
    optimizer_step: int
    # These fields are optional only so historical snapshots remain readable.
    # New interventions are rejected by record_teaching_intervention unless all
    # provenance is present and bound to the released construction boundary.
    selected_provider_id: str | None = None
    provider_implementation_sha256: str | None = None
    specimen_ids: tuple[str, ...] = ()
    specimen_content_sha256: str | None = None
    variation_axes: tuple[str, ...] = ()
    optimizer_step_delta: int | None = None

    def __post_init__(self) -> None:
        # JSON state decoding yields lists; normalize them back to the durable
        # tuple form before validating or comparing the released contract.
        _require_teaching_provenance(
            isinstance(self.specimen_ids, (tuple, list)) and
            isinstance(self.variation_axes, (tuple, list)))
        object.__setattr__(self, "specimen_ids", tuple(self.specimen_ids))
        object.__setattr__(self, "variation_axes", tuple(self.variation_axes))
        if (not self.obligation_id or not self.intervention_id or
                not self.teaching_option_id):
            raise ValueError("AUTONOMY_TEACHING_RECEIPT_IDENTITY_INVALID")
        for value in (self.parent_checkpoint_sha256, self.checkpoint_sha256):
            if (not isinstance(value, str) or len(value) != 64 or
                    any(char not in "0123456789abcdef" for char in value)):
                raise ValueError("AUTONOMY_TEACHING_RECEIPT_CHECKPOINT_INVALID")
        if (type(self.parent_optimizer_step) is not int or
                type(self.optimizer_step) is not int or
                self.parent_optimizer_step < 0 or
                self.optimizer_step <= self.parent_optimizer_step or
                self.checkpoint_sha256 == self.parent_checkpoint_sha256):
            raise ValueError("AUTONOMY_TEACHING_RECEIPT_NO_CHECKPOINT_PROGRESS")
        if self.optimizer_step_delta is not None and (
                type(self.optimizer_step_delta) is not int or
                self.optimizer_step_delta < 1 or
                self.optimizer_step_delta !=
                self.optimizer_step - self.parent_optimizer_step):
            raise ValueError("AUTONOMY_TEACHING_RECEIPT_STEP_DELTA_INVALID")
        _require_teaching_provenance(
            not (self.selected_provider_id is not None and
                 (not isinstance(self.selected_provider_id, str) or
                  not self.selected_provider_id)) and
            not (self.provider_implementation_sha256 is not None and
                 (not isinstance(self.provider_implementation_sha256, str) or
                  len(self.provider_implementation_sha256) != 64 or
                  any(char not in "0123456789abcdef"
                      for char in self.provider_implementation_sha256))) and
            len(set(self.specimen_ids)) == len(self.specimen_ids) and
            all(isinstance(item, str) and item for item in self.specimen_ids) and
            not (self.specimen_content_sha256 is not None and
                 (not isinstance(self.specimen_content_sha256, str) or
                  len(self.specimen_content_sha256) != 64 or
                  any(char not in "0123456789abcdef"
                      for char in self.specimen_content_sha256))) and
            len(set(self.variation_axes)) == len(self.variation_axes) and
            all(isinstance(item, str) and item for item in self.variation_axes))


@dataclass(frozen=True)
class RejectedTeachingAttemptReceipt:
    """One source-grounded teaching attempt that did not advance custody."""

    obligation_id: str
    parent_evidence_id: str
    attempt_id: str
    teaching_option_id: str
    retained_checkpoint_sha256: str
    retained_optimizer_step: int
    candidate_optimizer_step: int
    retention_reason: str
    selected_provider_id: str
    provider_implementation_sha256: str
    specimen_content_sha256: str

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) and value for value in (
                self.obligation_id, self.parent_evidence_id, self.attempt_id,
                self.teaching_option_id, self.retention_reason,
                self.selected_provider_id)):
            raise ValueError("AUTONOMY_REJECTED_ATTEMPT_IDENTITY_INVALID")
        for value in (
                self.retained_checkpoint_sha256,
                self.provider_implementation_sha256,
                self.specimen_content_sha256):
            if (not isinstance(value, str) or len(value) != 64 or
                    any(char not in "0123456789abcdef" for char in value)):
                raise ValueError("AUTONOMY_REJECTED_ATTEMPT_DIGEST_INVALID")
        if (type(self.retained_optimizer_step) is not int or
                type(self.candidate_optimizer_step) is not int or
                self.retained_optimizer_step < 0 or
                self.candidate_optimizer_step <= self.retained_optimizer_step):
            raise ValueError("AUTONOMY_REJECTED_ATTEMPT_STEP_INVALID")


@dataclass(frozen=True)
class EvidenceLedger:
    """Append-only evidence history bound to one release and autonomy plan."""

    factory_release_sha256: str
    autonomy_plan_sha256: str
    receipts: tuple[EvidenceReceipt, ...] = ()
    interventions: tuple[TeachingReceipt, ...] = ()
    rejected_attempts: tuple[RejectedTeachingAttemptReceipt, ...] = ()

    def __post_init__(self) -> None:
        if (not isinstance(self.factory_release_sha256, str) or
                len(self.factory_release_sha256) != 64 or
                any(char not in "0123456789abcdef"
                    for char in self.factory_release_sha256) or
                not isinstance(self.autonomy_plan_sha256, str) or
                len(self.autonomy_plan_sha256) != 64 or
                any(char not in "0123456789abcdef"
                    for char in self.autonomy_plan_sha256) or
                any(not isinstance(item, EvidenceReceipt) for item in self.receipts) or
                len({item.evidence_id for item in self.receipts}) != len(self.receipts) or
                any(not isinstance(item, TeachingReceipt) for item in self.interventions) or
                len({item.intervention_id for item in self.interventions}) !=
                len(self.interventions) or
                any(not isinstance(item, RejectedTeachingAttemptReceipt)
                    for item in self.rejected_attempts) or
                len({item.attempt_id for item in self.rejected_attempts}) !=
                len(self.rejected_attempts)):
            raise ValueError("AUTONOMY_EVIDENCE_LEDGER_INVALID")


@dataclass(frozen=True)
class CurriculumWorkItem:
    capability_id: str
    obligation: EvidenceObligation
    teaching_option_ids: tuple[str, ...]
    evidence_complete_prerequisites: tuple[str, ...]

    def __post_init__(self) -> None:
        if (not self.capability_id or self.obligation.capability_id != self.capability_id or
                not self.teaching_option_ids or
                len(set(self.teaching_option_ids)) != len(self.teaching_option_ids)):
            raise ValueError("AUTONOMY_WORK_ITEM_INVALID")


@dataclass(frozen=True)
class TeachingWorkItem:
    capability_id: str
    obligation: EvidenceObligation
    teaching_option_ids: tuple[str, ...]
    failed_evidence: EvidenceReceipt

    def __post_init__(self) -> None:
        if (not self.capability_id or
                self.obligation.capability_id != self.capability_id or
                self.failed_evidence.obligation_id != self.obligation.obligation_id or
                not self.teaching_option_ids or
                len(set(self.teaching_option_ids)) != len(self.teaching_option_ids)):
            raise ValueError("AUTONOMY_TEACHING_WORK_ITEM_INVALID")
