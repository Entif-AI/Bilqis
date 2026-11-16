"""Human-run bridge from the pure autonomy planner to admitted live sources."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..curriculum.scheduler import SchoolState
from ..factory.autonomy import (
    AutonomyAction,
    AutonomyPlan,
    CurriculumWorkItem,
    EvidenceLedger,
    RejectedTeachingAttemptReceipt,
    TeachingReceipt,
    evidence_complete_capabilities,
    next_action,
    record_evidence,
    record_rejected_teaching_attempt,
    record_teaching_intervention,
)
from ..factory.model import FactoryRelease
from ..source_adapters.school import live_source_registry
from ._autonomy_live.frontier import (
    propose_source_frontier_work as _propose_source_frontier_work,
    resolve_ready_proposal as _resolve_ready_proposal,
)
from ._autonomy_live.planning import (
    advance_if_scheduled_evidence_complete,
    build_live_autonomy_plan,
    measure_live_evidence,
    reconcile_live_autonomy_state,
    reconcile_successor_evidence_or_reset,
    reroute_failed_teaching,
    scheduled_teaching_matches,
)
from ._autonomy_live.recovery import (
    recover_rejected_attempts_from_events as _recover_rejected_attempts_from_events,
    recover_teaching as _recover_teaching,
    rejected_attempt_from_event as _rejected_attempt_from_event,
    rejected_attempt_id as _rejected_attempt_id,
)
from .autonomy_state import persist_autonomy_state


@dataclass
class LiveAutonomySession:
    """Durable neural-inert autonomy state for one human-operated trainer."""

    run_dir: Path
    source_root: Path
    release: FactoryRelease
    plan: AutonomyPlan
    ledger: EvidenceLedger

    @classmethod
    def open(cls, run_dir: Path, source_root: Path, release: FactoryRelease):
        plan = build_live_autonomy_plan(release, source_root)
        ledger = reconcile_live_autonomy_state(run_dir, release, plan)
        session = cls(Path(run_dir), Path(source_root), release, plan, ledger)
        session.recover_rejected_attempts_from_events()
        return session

    def refresh_release(self, release: FactoryRelease) -> None:
        if release.release_sha256 == self.release.release_sha256:
            return
        plan = build_live_autonomy_plan(release, self.source_root)
        try:
            ledger = reconcile_successor_evidence_or_reset(
                self.release, release, self.ledger,
                previous_plan=self.plan, current_plan=plan)
            persist_autonomy_state(
                self.run_dir, release, plan=plan, ledger=ledger)
        except TypeError:
            ledger = reconcile_live_autonomy_state(
                self.run_dir, release, plan)
        self.release, self.plan, self.ledger = release, plan, ledger

    def action(self, checkpoint) -> AutonomyAction:
        return next_action(
            self.release, self.ledger, plan=self.plan,
            current_checkpoint_sha256=checkpoint.sha256,
            current_optimizer_step=checkpoint.optimizer_step)

    def measure(self, graph, work: CurriculumWorkItem, *, checkpoint: dict,
                seed: int, predictor=None, source_bound_predictor=None):
        evidence = measure_live_evidence(
            self.source_root, graph, self.release, work,
            checkpoint=checkpoint, seed=seed, predictor=predictor,
            source_bound_predictor=source_bound_predictor)
        self.ledger = record_evidence(
            self.release, self.ledger, evidence, plan=self.plan,
            current_checkpoint_sha256=checkpoint["sha256"],
            current_optimizer_step=checkpoint["optimizer_step"])
        persist_autonomy_state(
            self.run_dir, self.release, plan=self.plan, ledger=self.ledger)
        return evidence

    def record_teaching(
            self, receipt: TeachingReceipt, *, parent_checkpoint) -> None:
        self.ledger = record_teaching_intervention(
            self.release, self.ledger, receipt, plan=self.plan,
            current_checkpoint_sha256=parent_checkpoint.sha256,
            current_optimizer_step=parent_checkpoint.optimizer_step)
        persist_autonomy_state(
            self.run_dir, self.release, plan=self.plan, ledger=self.ledger)

    def record_rejected_attempt(
            self, receipt: RejectedTeachingAttemptReceipt) -> None:
        self.ledger = record_rejected_teaching_attempt(
            self.release, self.ledger, receipt, plan=self.plan,
            current_checkpoint_sha256=receipt.retained_checkpoint_sha256,
            current_optimizer_step=receipt.retained_optimizer_step)
        persist_autonomy_state(
            self.run_dir, self.release, plan=self.plan, ledger=self.ledger)

    @staticmethod
    def _rejected_attempt_id(
            event: dict, delivery: dict, obligation_id: str) -> str:
        return _rejected_attempt_id(event, delivery, obligation_id)

    def rejected_attempt_from_event(self, event: dict, failed):
        return _rejected_attempt_from_event(self, event, failed)

    def recover_rejected_attempts_from_events(self) -> int:
        return _recover_rejected_attempts_from_events(self)

    def recover_teaching(self, school_receipt: dict, checkpoint):
        return _recover_teaching(self, school_receipt, checkpoint)

    def _obligations_for_capability(self, capability_id: str):
        from ..factory.autonomy import obligations_for_capability
        return obligations_for_capability(
            self.release, capability_id, plan=self.plan)

    def evidence_complete(self, checkpoint) -> tuple[str, ...]:
        return evidence_complete_capabilities(
            self.release, self.ledger, plan=self.plan,
            current_checkpoint_sha256=checkpoint.sha256,
            current_optimizer_step=checkpoint.optimizer_step)

    def advance_if_complete(
        self, school: SchoolState, capability_id: str,
    ) -> SchoolState:
        return advance_if_scheduled_evidence_complete(
            self.release, self.plan, self.ledger, school, capability_id)

    def reroute_teaching(
        self, school: SchoolState, capability_id: str,
    ) -> SchoolState:
        return reroute_failed_teaching(
            self.release, school, capability_id)

    def propose_source_frontier_work(self, checkpoint, graph=None):
        return _propose_source_frontier_work(
            self, checkpoint, graph, live_source_registry())

    def resolve_ready_proposal(self, checkpoint, proposal):
        return _resolve_ready_proposal(
            self, checkpoint, proposal, live_source_registry())
