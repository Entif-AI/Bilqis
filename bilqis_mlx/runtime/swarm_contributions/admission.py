"""C14.4 non-neural independent evaluation and common decision receipts."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .contracts import (
    DECISION_SCHEMA, EVALUATION_SCHEMA, ContributionClass,
    ContributionDisposition, RemoteWorkManifest, digest, finite, invalid, text,
)
from .receipts import ReplayLedger, WorkerReceipt, verify_remote_receipt
from .replay import replay_store_for_run
from .school import require_current_school_identity


@dataclass(frozen=True)
class IndependentEvaluation:
    passed: bool
    score: float
    evidence_digest: str
    retention_outcome: str
    schema_version: str = field(default=EVALUATION_SCHEMA, init=False)

    def __post_init__(self) -> None:
        if (type(self.passed) is not bool
                or not finite(self.score)
                or not 0.0 <= float(self.score) <= 1.0
                or not digest(self.evidence_digest)
                or not text(self.retention_outcome)
                or self.schema_version != EVALUATION_SCHEMA):
            invalid("BAMF_C14_INDEPENDENT_EVALUATION_INVALID")


@dataclass(frozen=True)
class ContributionDecision:
    disposition: ContributionDisposition
    manifest_digest: str
    receipt_digest: str
    canonical_evidence_digest: str
    replay_ledger: ReplayLedger
    reason: str
    canonical_generation: str | None = None
    schema_version: str = field(default=DECISION_SCHEMA, init=False)

    def __post_init__(self) -> None:
        if (type(self.disposition) is not ContributionDisposition
                or not digest(self.manifest_digest)
                or not digest(self.receipt_digest)
                or not digest(self.canonical_evidence_digest)
                or type(self.replay_ledger) is not ReplayLedger
                or not text(self.reason)
                or (self.canonical_generation is not None
                    and not digest(self.canonical_generation))
                or self.schema_version != DECISION_SCHEMA):
            invalid("BAMF_C14_CONTRIBUTION_DECISION_INVALID")


def admit_remote_observation(
        manifest: RemoteWorkManifest, receipt: WorkerReceipt, *,
        now: int, run_dir: Path, target_capability: str,
        independent_evaluator: Callable[
            [RemoteWorkManifest, WorkerReceipt], IndependentEvaluation],
) -> ContributionDecision:
    """Admit or reject non-neural evidence without canonical-school mutation."""
    if (manifest.contribution_class in {
            ContributionClass.ADAPTER_DELTA, ContributionClass.DENSE_UPDATE}
            or not callable(independent_evaluator)):
        invalid("BAMF_C14_OBSERVATIONAL_ADMISSION_INVALID")
    verified = verify_remote_receipt(
        manifest, receipt, now=now, replay_ledger=ReplayLedger())
    require_current_school_identity(manifest, run_dir)
    if manifest.capability_id != target_capability:
        invalid("BAMF_C14_CANONICAL_CAPABILITY_MISMATCH")
    evaluation = independent_evaluator(manifest, receipt)
    if type(evaluation) is not IndependentEvaluation:
        invalid("BAMF_C14_INDEPENDENT_EVALUATION_REQUIRED")
    evaluation.__post_init__()
    ledger = replay_store_for_run(run_dir).claim(
        manifest.replay_id, manifest.digest, verified.receipt_digest)
    passes = (
        evaluation.passed
        and evaluation.score >= manifest.acceptance.minimum_score
        and (not manifest.acceptance.requires_retention
             or evaluation.retention_outcome == "retention:pass"))
    return ContributionDecision(
        ContributionDisposition.ADMITTED if passes
        else ContributionDisposition.REJECTED,
        manifest.digest, verified.receipt_digest, evaluation.evidence_digest,
        ledger, evaluation.retention_outcome)
