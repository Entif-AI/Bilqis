"""Production candidate-step boundary for B09.2/B12.2 execution authority."""
from __future__ import annotations

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.atlas_candidate import candidate_step
from bilqis_mlx.runtime.atlas_model import BamfGradientExecution
from bilqis_mlx.runtime.atlas_execution_binder import (
    bind_execution_provenance, bind_execution_provenance_many,
)
from bilqis_mlx.runtime.atlas_training_authority import (
    bind_logical_batch_training_authority,
)
from bilqis_mlx.runtime.atlas_resources import BatchPlan
from bilqis_mlx.runtime.atlas_training_contracts import BamfTrainingBatch
from .c08_gradient_accumulation import require_logical_batch_gradient_execution
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.bamf_bundle.execution_cache import bind_execution_generation


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def _logical_batch_inputs(logical_batch_execution, training_batch,
                          logical_batch_plan, spec):
    logical = require_logical_batch_gradient_execution(logical_batch_execution)
    if (type(logical_batch_plan) is not BatchPlan
            or type(training_batch) is not BamfTrainingBatch):
        _invalid("C08_LOGICAL_BATCH_PLAN_REQUIRED")
    logical_batch_plan.__post_init__()
    training_batch.__post_init__()
    row_ids = tuple(row.provenance.row_id for row in training_batch.rows)
    seeds = {row.provenance.optimizer_step_seed for row in training_batch.rows}
    if (logical.plan_digest != logical_batch_plan.digest
            or logical.source_digest != logical_batch_plan.source_digest
            or logical.generation_binding != logical_batch_plan.generation_binding
            or logical_batch_plan.logical_row_ids != row_ids
            or seeds != {logical_batch_plan.optimizer_step_seed}
            or logical_batch_plan.generation_binding != training_batch.generation_binding
            or logical_batch_plan.topology_digest != spec.digest):
        _invalid("C08_LOGICAL_BATCH_PLAN_DRIFT")
    return logical.loss_executions, logical.gradients


def _require_execution_custody(
        candidate, observed, *, spec, extents, execution_cache=None):
    expected_generation = (
        execution_generation_digest(
            candidate.optimizer.parameters, spec=spec, extents=extents)
        if execution_cache is None else bind_execution_generation(
            execution_cache, candidate.optimizer.parameters,
            spec=spec, extents=extents).generation_digest)
    custody = candidate.parent.custody
    for execution in observed:
        if execution.output.generation_binding != expected_generation:
            _invalid("B11_GRADIENT_EXECUTION_CANDIDATE_MISMATCH")
        if (custody is None
                or execution.custody_run_id != custody.run_id
                or execution.custody_generation != custody.generation
                or execution.custody_manifest_sha256 != custody.manifest_sha256):
            _invalid("B11_GRADIENT_EXECUTION_CUSTODY_MISMATCH")


def production_candidate_step(
        candidate, gradients=None, *, loss_bearing_target,
        gradient_execution=None, logical_batch_execution=None, training_batch=None,
        logical_batch_plan=None,
        group_eligible, spec, extents,
        run_id, generation, parent_manifest_sha256,
        parent_candidate_identity_sha256, parent_optimizer_step, topology_digest,
        candidate_step_ordinal, teacher_hparams, max_norm: float,
        execution_cache=None):
    """Run only when the binder can issue truthful execution provenance."""
    loss_execution = None
    loss_executions = None
    training_authority = None
    actual_gradients = gradients
    if loss_bearing_target:
        if logical_batch_execution is not None:
            if gradient_execution is not None or gradients is not None:
                _invalid("C08_LOGICAL_BATCH_EXECUTION_REQUIRED")
            loss_executions, actual_gradients = _logical_batch_inputs(
                logical_batch_execution, training_batch, logical_batch_plan, spec)
        else:
            if logical_batch_plan is not None:
                _invalid("C08_LOGICAL_BATCH_PLAN_UNEXPECTED")
            if type(gradient_execution) is not BamfGradientExecution:
                _invalid("B11_GRADIENT_EXECUTION_REQUIRED")
            gradient_execution.__post_init__()
        observed = (loss_executions if loss_executions is not None
                    else (gradient_execution.execution,))
        _require_execution_custody(
            candidate, observed, spec=spec, extents=extents,
            execution_cache=execution_cache)
        if loss_executions is None:
            loss_execution = gradient_execution.execution
            actual_gradients = gradient_execution.gradients
            training_authority = getattr(loss_execution, "training_authority", None)
        else:
            provenance = bind_execution_provenance_many(
                loss_executions=loss_executions, group_eligible=group_eligible,
                spec=spec, extents=extents, run_id=run_id, generation=generation,
                parent_manifest_sha256=parent_manifest_sha256,
                parent_candidate_identity_sha256=parent_candidate_identity_sha256,
                parent_optimizer_step=parent_optimizer_step,
                topology_digest=topology_digest,
                candidate_step_ordinal=candidate_step_ordinal)
            training_authority = bind_logical_batch_training_authority(
                training_batch,
                tuple(execution.training_authority for execution in loss_executions))
            return candidate_step(
                candidate, actual_gradients, provenance, teacher_hparams,
                spec=spec, extents=extents, loss_bearing=True, max_norm=max_norm,
                training_authority=training_authority)
    elif (gradient_execution is not None or logical_batch_execution is not None
          or logical_batch_plan is not None):
        _invalid("B11_GRADIENT_EXECUTION_UNEXPECTED")
    provenance = bind_execution_provenance(
        loss_bearing_target=loss_bearing_target,
        loss_execution=loss_execution,
        group_eligible=group_eligible,
        spec=spec, extents=extents,
        run_id=run_id, generation=generation,
        parent_manifest_sha256=parent_manifest_sha256,
        parent_candidate_identity_sha256=parent_candidate_identity_sha256,
        parent_optimizer_step=parent_optimizer_step,
        topology_digest=topology_digest,
        candidate_step_ordinal=candidate_step_ordinal)
    return candidate_step(
        candidate, actual_gradients, provenance, teacher_hparams,
        spec=spec, extents=extents,
        loss_bearing=loss_bearing_target, max_norm=max_norm,
        training_authority=training_authority)
