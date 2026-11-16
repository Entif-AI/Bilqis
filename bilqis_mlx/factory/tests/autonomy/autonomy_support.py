from dataclasses import replace
import hashlib
import unittest

from bilqis_mlx.curriculum import AnswerFamily, BINARY, Capability, Course, Grade
from bilqis_mlx.factory.adapters import RegisteredSourceAdapter, SourceAdapterRegistry
from bilqis_mlx.factory.autonomy import (
    AutonomyActionKind,
    EvidenceKind,
    EvidenceReceipt,
    RejectedTeachingAttemptReceipt,
    ProjectionEvidenceSpec,
    compile_autonomy_plan,
    initial_evidence_ledger,
    evidence_complete_capabilities,
    next_action,
    next_work,
    obligations_for_capability,
    record_evidence,
    record_rejected_teaching_attempt,
)
from bilqis_mlx.factory.model import SourceAdapter
from bilqis_mlx.factory.release import compile_factory_release


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class AutonomyFixture:
    def setUp(self):
        names = ("A.BASE", "A.OTHER", "A.COMPOSITE", "A.F3", "A.F4", "A.F5")
        caps = []
        for name in names:
            prerequisites = (("A.BASE", "A.OTHER") if name == "A.COMPOSITE" else ())
            caps.append(Capability(
                id=name, difficulty="fixture", source_anchor="repo:fixture/autonomy",
                taught_roots=("fixture." + name.lower(),),
                examined_roots=("fixture." + name.lower(),),
                prerequisites=prerequisites, composed_of=prerequisites,
                answer_families=(AnswerFamily("binary", BINARY),),
                lesson_generator="fixture.autonomy-generator/v1",
                independent_oracle="fixture.autonomy-oracle/v1",
            ))
        grade = Grade(
            "A", tuple(caps), assessment_sha256="a" * 64,
            exam_item_counts=tuple((name, 4) for name in names),
            teaching_stages=(("A.BASE", "A.OTHER"),
                             ("A.COMPOSITE", "A.F3", "A.F4", "A.F5")),
        )
        course = Course((grade,), "fixture.autonomy/v1", "b" * 64, "a" * 64)
        descriptor = SourceAdapter(
            "fixture.autonomy-adapter/v1", "fixture.autonomy-generator/v1",
            ("fixture.autonomy-oracle/v1",), "d" * 64,
            teaching_option_ids=("fixture.transfer",),
        )
        registry = SourceAdapterRegistry((RegisteredSourceAdapter(
            descriptor, lambda **_: (), lambda row, **_: True),))
        self.release = compile_factory_release(course, registry)
        self.receipt_index = 0

    def coverage_report(self, *, status="SOURCE_CONTRAST_COVERED", debt=False):
        from bilqis_mlx.curriculum_compiler import compile_ast
        return {
            "schema": "bilqis.mlx.semantic-composition-coverage/v1",
            "ast_sha256": compile_ast(self.release.course).digest(),
            "registry_sha256": "9" * 64,
            "capabilities": tuple(item.capability_id for item in self.release.capabilities),
            "obligations": ({
                "consumer": "A.F3",
                "producer": "A.BASE",
                "operand_slot": 0,
                "operand_type": "Boolean",
                "declared_prerequisite": True,
                "status": status,
                "coverage_debt": debt,
                "witness_ids": ("witness-1",) if not debt else (),
            },),
            "unresolved": (),
            "source_witness_cohort_sha256": "8" * 64,
            "training_authorized": False,
        }

    def receipt(self, obligation, passed=True, specimen_count=None):
        self.receipt_index += 1
        count = obligation.minimum_specimens if specimen_count is None else specimen_count
        return EvidenceReceipt(
            obligation_id=obligation.obligation_id,
            evidence_id=f"evidence-{self.receipt_index}",
            checkpoint_sha256="e" * 64,
            optimizer_step=self.receipt_index,
            cohort_sha256=_sha(f"cohort-{self.receipt_index}"),
            specimen_count=count,
            passed=passed,
        )

    def teaching_receipt(self, failed, *, intervention_id="teach-1",
                         teaching_option_id=None, checkpoint_sha256="f" * 64,
                         optimizer_step=None, **overrides):
        adapter = self.release.source_adapters[0]
        coverage = next(item for item in self.release.coverage_plans
                        if item.capability_id == failed.obligation_id.split("/", 1)[0])
        values = {
            "obligation_id": failed.obligation_id,
            "intervention_id": intervention_id,
            "teaching_option_id": teaching_option_id or
                "source.direct/" + failed.obligation_id.split("/", 1)[0],
            "parent_checkpoint_sha256": failed.checkpoint_sha256,
            "parent_optimizer_step": failed.optimizer_step,
            "checkpoint_sha256": checkpoint_sha256,
            "optimizer_step": (failed.optimizer_step + 1 if optimizer_step is None
                               else optimizer_step),
            "selected_provider_id": adapter.adapter_id,
            "provider_implementation_sha256": adapter.implementation_sha256,
            "specimen_ids": ("teaching-specimen-" + intervention_id,),
            "specimen_content_sha256": _sha("teaching-content-" + intervention_id),
            "variation_axes": coverage.variation_axes,
            "optimizer_step_delta": 1,
        }
        values.update(overrides)
        from bilqis_mlx.factory.autonomy import TeachingReceipt
        return TeachingReceipt(**values)

    def close_current_capability(self, ledger):
        capability = next_work(self.release, ledger).capability_id
        while True:
            work = next_work(self.release, ledger)
            if work is None or work.capability_id != capability:
                return ledger
            ledger = record_evidence(self.release, ledger, self.receipt(work.obligation))
