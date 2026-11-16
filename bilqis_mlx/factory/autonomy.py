"""Public autonomy API backed by focused implementation modules."""
from ._autonomy.evidence_contracts import (
    EvidenceKind,
    EvidenceLedger,
    EvidenceObligation,
    EvidenceReceipt,
    RejectedTeachingAttemptReceipt,
    TeachingReceipt,
)
from ._autonomy.ledger import (
    closed_obligations,
    evidence_complete_capabilities,
    initial_evidence_ledger,
)
from ._autonomy.obligations import obligations_for_capability
from ._autonomy.plan_contracts import (
    AutonomyPlan,
    ProjectionEvidenceSpec,
    SourceCompositionEdge,
    SupplementalEvidenceSpec,
)
from ._autonomy.planning import (
    compile_autonomy_plan,
    is_factory_release,
    next_source_coverage_debt,
    release_capabilities,
)
from ._autonomy.rebind import rebind_evidence_ledger, reconcile_successor_evidence
from ._autonomy.recording import (
    record_evidence,
    record_rejected_teaching_attempt,
    record_teaching_intervention,
)
from ._autonomy.routing import next_action, next_work
from ._autonomy.work_contracts import (
    AutonomyAction,
    AutonomyActionKind,
    CurriculumWorkItem,
    TeachingWorkItem,
)

_PUBLIC_RECORDS = (
    AutonomyAction, AutonomyActionKind, AutonomyPlan, CurriculumWorkItem,
    EvidenceKind, EvidenceLedger, EvidenceObligation, EvidenceReceipt,
    ProjectionEvidenceSpec, RejectedTeachingAttemptReceipt,
    SourceCompositionEdge, SupplementalEvidenceSpec, TeachingReceipt,
    TeachingWorkItem,
)
for _record in _PUBLIC_RECORDS:
    _record.__module__ = __name__

__all__ = tuple(
    name for name in globals()
    if not name.startswith("_") and name not in {"annotations"})
