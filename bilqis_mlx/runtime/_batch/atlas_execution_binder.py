"""B09.2 binder consuming only B11-issued production execution authority."""
from __future__ import annotations

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.atlas_execution_provenance import (
    StepExecutionProvenance, issue_execution_provenance,
)
from bilqis_mlx.learning.atlas_participation import (
    ActiveAdmittedRows, RoleReadParticipation, SemanticDenominator,
    StepParticipation, StepParticipationInputs,
)
from .c08_distributed_evidence import DistributedB11Evidence
from bilqis_mlx.learning.atlas_participation_census import validate_group_census
from bilqis_mlx.runtime.atlas_model import require_bamf_loss_execution

_LOGICAL_BATCH_MIN_ROWS = 2


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def bind_execution_provenance(
        *, loss_bearing_target: bool,
        loss_execution=None,
        group_eligible,
        spec, extents, run_id: str, generation: int,
        parent_manifest_sha256: str, parent_candidate_identity_sha256: str,
        parent_optimizer_step: int, topology_digest: str,
        candidate_step_ordinal: int) -> StepExecutionProvenance:
    """Issue inert no-loss provenance or bind the exact B11 loss execution."""
    if type(loss_bearing_target) is not bool:
        _invalid("LOSS_BEARING_TARGET_REQUIRED")
    validate_group_census(group_eligible, spec, extents)
    if not loss_bearing_target:
        if loss_execution is not None:
            _invalid("B11_EXECUTION_AUTHORITY_UNEXPECTED")
        inputs = StepParticipationInputs(loss_bearing_target=False)
        active_admitted = ActiveAdmittedRows()
    else:
        execution = require_bamf_loss_execution(loss_execution)
        inputs = StepParticipationInputs(
            visible_identity_rows=execution.visible_identity_rows,
            feedback_identity_rows=execution.feedback_identity_rows,
            visible_feature_rows=execution.feature_rows,
            local_slot_rows=execution.local_slot_rows,
            executed_parameter_names=execution.dense_parameter_names,
            loss_bearing_target=True,
        )
        active_admitted = ActiveAdmittedRows(
            identity_rows=group_eligible.admitted_identity_rows,
            motif_slots=tuple(sorted({
                slot
                for result in execution.motif_reads
                for slot in result.participating_slots
            })),
            feature_rows=execution.feature_rows,
            local_slot_rows=execution.local_slot_rows,
        )
    provenance = issue_execution_provenance(
        inputs, SemanticDenominator(
            identity_rows=execution.semantic_denominator_identity_rows,
            feature_rows=execution.semantic_denominator_feature_rows,
        ) if loss_bearing_target else SemanticDenominator(), (
            execution.motif_reads if loss_bearing_target else ()),
        RoleReadParticipation(execution.role_read_feature_rows)
        if loss_bearing_target else RoleReadParticipation(),
        group_eligible, active_admitted, spec=spec, extents=extents,
        run_id=run_id, generation=generation,
        parent_manifest_sha256=parent_manifest_sha256,
        parent_candidate_identity_sha256=parent_candidate_identity_sha256,
        parent_optimizer_step=parent_optimizer_step,
        topology_digest=topology_digest,
        candidate_step_ordinal=candidate_step_ordinal)
    if loss_bearing_target:
        from bilqis_mlx.learning.atlas_execution_provenance import (
            _bind_execution_training_authority,
        )
        _bind_execution_training_authority(provenance, loss_execution)
    return provenance


def bind_execution_provenance_many(
        *, loss_executions: tuple,
        group_eligible, spec, extents, run_id: str, generation: int,
        parent_manifest_sha256: str, parent_candidate_identity_sha256: str,
        parent_optimizer_step: int, topology_digest: str,
        candidate_step_ordinal: int) -> StepExecutionProvenance:
    """Union exact row-scoped B11 execution evidence for one C08 optimizer step."""
    if (type(loss_executions) is not tuple
            or len(loss_executions) < _LOGICAL_BATCH_MIN_ROWS):
        _invalid("C08_LOGICAL_BATCH_EXECUTION_REQUIRED")
    validate_group_census(group_eligible, spec, extents)
    executions = tuple(require_bamf_loss_execution(item) for item in loss_executions)
    inputs = StepParticipationInputs(
        visible_identity_rows=tuple(sorted({
            row for execution in executions for row in execution.visible_identity_rows
        })),
        feedback_identity_rows=tuple(sorted({
            row for execution in executions for row in execution.feedback_identity_rows
        })),
        visible_feature_rows=tuple(sorted({
            row for execution in executions for row in execution.feature_rows
        })),
        local_slot_rows=tuple(sorted({
            row for execution in executions for row in execution.local_slot_rows
        })),
        executed_parameter_names=tuple(sorted({
            name for execution in executions for name in execution.dense_parameter_names
        })),
        loss_bearing_target=True,
    )
    denominator = SemanticDenominator(
        identity_rows=tuple(sorted({
            row for execution in executions
            for row in execution.semantic_denominator_identity_rows
        })),
        feature_rows=tuple(sorted({
            row for execution in executions
            for row in execution.semantic_denominator_feature_rows
        })),
    )
    motif_reads = tuple(
        result for execution in executions for result in execution.motif_reads)
    role_reads = RoleReadParticipation(tuple(sorted({
        row for execution in executions for row in execution.role_read_feature_rows
    })))
    active_admitted = ActiveAdmittedRows(
        identity_rows=group_eligible.admitted_identity_rows,
        motif_slots=tuple(sorted({
            slot for result in motif_reads for slot in result.participating_slots
        })),
        feature_rows=inputs.visible_feature_rows,
        local_slot_rows=inputs.local_slot_rows,
    )
    return issue_execution_provenance(
        inputs, denominator, motif_reads, role_reads, group_eligible, active_admitted,
        spec=spec, extents=extents, run_id=run_id, generation=generation,
        parent_manifest_sha256=parent_manifest_sha256,
        parent_candidate_identity_sha256=parent_candidate_identity_sha256,
        parent_optimizer_step=parent_optimizer_step,
        topology_digest=topology_digest,
        candidate_step_ordinal=candidate_step_ordinal)


def bind_distributed_execution_provenance(
        *, evidence: tuple[DistributedB11Evidence, ...], group_eligible,
        spec, extents, run_id: str, generation: int,
        parent_manifest_sha256: str, parent_candidate_identity_sha256: str,
        parent_optimizer_step: int, topology_digest: str,
        candidate_step_ordinal: int) -> StepExecutionProvenance:
    """Bind portable rank evidence into the same B09/B12 provenance owner."""
    if (type(evidence) is not tuple or len(evidence) < _LOGICAL_BATCH_MIN_ROWS
            or any(type(item) is not DistributedB11Evidence for item in evidence)):
        _invalid("C08_DISTRIBUTED_EVIDENCE_REQUIRED")
    validate_group_census(group_eligible, spec, extents)
    participation = StepParticipation(
        tuple(sorted({row for item in evidence for row in
                      item.visible_identity_rows + item.feedback_identity_rows
                      + item.semantic_denominator_identity_rows})),
        tuple(sorted({slot for item in evidence for slot in item.motif_slots})),
        tuple(sorted({row for item in evidence for row in
                      item.feature_rows + item.semantic_denominator_feature_rows
                      + item.role_read_feature_rows})),
        tuple(sorted({row for item in evidence for row in item.local_slot_rows})),
        tuple(sorted({name for item in evidence for name in item.dense_parameter_names})),
        True)
    active_admitted = ActiveAdmittedRows(
        identity_rows=group_eligible.admitted_identity_rows,
        motif_slots=participation.motif_slots,
        feature_rows=tuple(sorted({
            row for item in evidence for row in item.feature_rows
        })),
        local_slot_rows=participation.local_slot_rows)
    return issue_execution_provenance(
        None, None, None, None, group_eligible, active_admitted,
        spec=spec, extents=extents, run_id=run_id, generation=generation,
        parent_manifest_sha256=parent_manifest_sha256,
        parent_candidate_identity_sha256=parent_candidate_identity_sha256,
        parent_optimizer_step=parent_optimizer_step,
        topology_digest=topology_digest,
        candidate_step_ordinal=candidate_step_ordinal,
        precomputed_participation=participation)
