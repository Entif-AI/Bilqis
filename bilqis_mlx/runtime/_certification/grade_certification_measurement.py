"""Inference-only Factory measurement backend for #1334 certification."""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path

from bilqis_mlx.factory import assessment_scope_contract
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_readout import ExecutionMode
from bilqis_mlx.runtime.atlas_model import forward_bamf
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.bamf_bundle import (
    BamfBundleCandidate,
    authenticate_bamf_execution_feature_context,
)
from bilqis_mlx.runtime.factory_evaluation_compiler import (
    compile_factory_evaluation_batch,
)
from bilqis_mlx.runtime.factory_task_authority import (
    factory_task_authority,
    factory_task_training_goal,
)
from bilqis_mlx.runtime.task_goal_readout import (
    task_goal_route_plan,
    task_goal_training_targets,
)

from .grade_certification_contracts import (
    CertificationObligationScore,
    GradeCertificationRequest,
)
from .grade_certification_common import _invalid
from .grade_certification_execution import CertificationMeasurement


def _seed(request: GradeCertificationRequest, purpose: str) -> int:
    raw = hashlib.sha256(
        f"{request.attempt_sha256}:{purpose}".encode()).digest()
    return int.from_bytes(raw[:8], "big") & ((1 << 63) - 1)


class GradeCertificationMeasurementBackend:
    """Measure one immutable accepted learner without optimizer mutation."""

    def __init__(
        self,
        run_dir: Path,
        request: GradeCertificationRequest,
        source_context,
        accepted_student: BamfBundleCandidate,
        artifact_path: str,
    ):
        self.run_dir = Path(run_dir)
        self.request = request
        self.source_context = source_context
        self.student = accepted_student
        self.artifact_path = artifact_path
        scope = assessment_scope_contract(
            source_context.release, request.assessment_capabilities)
        if (
            accepted_student.run_id != request.run_id
            or accepted_student.generation != request.accepted_generation
            or candidate_identity_digest(accepted_student.retained_state)
               != request.learner_checkpoint_sha256
            or accepted_student.retained_state.optimizer_step
               != request.optimizer_step
            or source_context.release.release_sha256
               != request.factory_release_sha256
            or scope.capabilities != request.assessment_capabilities
            or scope.rubric_sha256 != request.assessment_rubric_sha256
            or scope.source_sha256 != request.assessment_source_sha256
            or scope.generator_version != request.assessment_generator_version
            or scope.semantic_catalog_sha256 != request.semantic_catalog_sha256
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_MEASUREMENT_AUTHORITY_DRIFT")
        self.generation_binding = execution_generation_digest(
            accepted_student.retained_state.optimizer.parameters,
            spec=accepted_student.topology,
            extents=accepted_student.extents,
        )
        self.feature_context = authenticate_bamf_execution_feature_context(
            accepted_student, artifact_path, self.run_dir)

    def _draw(self, capabilities, purpose):
        from bilqis_mlx.runtime.assessment import (
            _draw_executable_scope_cohort,
            _persist_executable_cohort,
        )
        cohort, contract = _draw_executable_scope_cohort(
            self.source_context.source_root,
            self.source_context.graph,
            self.source_context.release,
            self.source_context.source_registry,
            capabilities=tuple(capabilities),
            seed=_seed(self.request, purpose),
        )
        _persist_executable_cohort(
            self.run_dir,
            {"manifest_sha256": self.request.accepted_manifest_sha256},
            contract,
            cohort,
        )
        return cohort

    def _row_correct(self, row, cohort_seed: int) -> bool:
        capability = row["capability"]
        source_each = self.source_context.execution_for(
            capability).exam_item_count
        compiled = compile_factory_evaluation_batch(
            self.source_context,
            self.student,
            self.artifact_path,
            row,
            source_seed=cohort_seed,
            source_each=source_each,
        )
        authority = factory_task_authority(
            self.source_context,
            compiled,
            generation_binding=self.generation_binding,
        )
        plan = task_goal_route_plan(
            authority.goal,
            compiled,
            self.feature_context.snapshot,
            self.generation_binding,
        )
        output = forward_bamf(
            self.student.retained_state.optimizer.parameters,
            compiled,
            plan,
            ExecutionMode.INFERENCE,
            None,
        )
        resolved = factory_task_training_goal(
            self.source_context, compiled, authority)
        targets, _mask = task_goal_training_targets(
            authority.goal, resolved)
        expected = {item.decision_id: item.value for item in targets}
        actual = {
            item.decision_id: item.value for item in output.committed
            if item.decision_id in expected
        }
        return actual == expected

    def _measure(self, capabilities, purpose, owner_by_capability):
        cohort = self._draw(capabilities, purpose)
        correct = Counter()
        total = Counter()
        for row in cohort.rows:
            capability = row["capability"]
            total[capability] += 1
            if self._row_correct(row, cohort.seed):
                correct[capability] += 1
        scores = tuple(
            CertificationObligationScore(
                owner_by_capability[capability],
                capability,
                correct[capability],
                total[capability],
            )
            for capability in capabilities
        )
        return CertificationMeasurement(cohort.digest, scores)

    def trigger(self) -> CertificationMeasurement:
        owners = {
            capability: (
                "ACTIVE"
                if capability in self.request.active_obligations
                else "PROTECTED")
            for capability in self.request.assessment_capabilities
        }
        return self._measure(
            self.request.assessment_capabilities,
            "TRIGGER",
            owners,
        )

    def obligation(self, capability: str) -> CertificationMeasurement:
        if capability not in self.request.active_obligations:
            _invalid("BAMF_GRADE_CERTIFICATION_ACTIVE_OBLIGATION_REQUIRED")
        return self._measure(
            (capability,),
            f"OBLIGATION:{capability}",
            {capability: "ACTIVE"},
        )


__all__ = ("GradeCertificationMeasurementBackend",)
