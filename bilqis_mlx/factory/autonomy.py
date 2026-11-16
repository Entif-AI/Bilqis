"""Stable public facade for deterministic, neural-inert autonomy planning."""
from ._autonomy.contracts import (AutonomyPlan, ProjectionEvidenceSpec, SourceCompositionEdge,
                                  SupplementalEvidenceSpec, is_factory_release,
                                  release_capabilities)
from ._autonomy.planning import compile_autonomy_plan, next_source_coverage_debt
from ._autonomy.evidence_contracts import (CurriculumWorkItem, EvidenceKind, EvidenceLedger,
                                           EvidenceObligation, EvidenceReceipt,
                                           RejectedTeachingAttemptReceipt, TeachingReceipt,
                                           TeachingWorkItem)
from ._autonomy.obligations import (closed_obligations, evidence_complete_capabilities,
                                    initial_evidence_ledger, obligations_for_capability)
from ._autonomy.recording import (record_evidence, record_rejected_teaching_attempt,
                                  record_teaching_intervention)
from ._autonomy.scheduling import (AutonomyAction, AutonomyActionKind, next_action, next_work)
from ._autonomy.lineage import rebind_evidence_ledger, reconcile_successor_evidence

__all__ = tuple(name for name in globals() if not name.startswith("_"))
