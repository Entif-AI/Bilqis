"""Owner-bound candidate optimizer-step execution and custody proofs."""
from __future__ import annotations

from bilqis_mlx.runtime.atlas_optimizer import (
    _adamw_update, reconcile_b01_optimizer_manifest,
)
from ..atlas_execution_provenance import (
    StepExecutionProvenance, mask_digest, participation_digest,
)
from ..atlas_participation import optimizer_participation_mask
from .common import (
    LEGACY_STEP_PROOF_SCHEMA,
    OBJECTIVE_CLOSURE_STEP_PROOF_SCHEMA,
    OBJECTIVE_LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA,
    OBJECTIVE_LOGICAL_BATCH_STEP_PROOF_SCHEMA,
    OBJECTIVE_MINIMAL_STEP_PROOF_SCHEMA, OBJECTIVE_STEP_PROOF_SCHEMA,
    invalid,
)
from .proofs import CandidateStepProof
from .transaction import CandidateTransaction, _issue_transaction


def _validated_step_decay(candidate, execution, spec, extents):
    custody = candidate.parent.custody
    if custody is None:
        invalid()
    from bilqis_mlx.runtime.model_topology_v2 import (
        GenerationExtents, ModelTopologySpecV2,
    )
    if (type(spec) is not ModelTopologySpecV2
            or type(extents) is not GenerationExtents
            or spec.digest != custody.topology_digest
            or extents.digest != custody.extents_digest):
        invalid()
    decay = reconcile_b01_optimizer_manifest(candidate.optimizer, spec, extents)
    if (execution.run_id != custody.run_id
            or execution.generation != custody.generation + 1
            or (custody.manifest_sha256 is not None
                and execution.parent_manifest_sha256 != custody.manifest_sha256)
            or execution.topology_digest != custody.topology_digest
            or execution.extents_sha256 != custody.extents_digest
            or execution.parent_candidate_identity_sha256
            != candidate._parent_identity_sha256
            or execution.parent_optimizer_step != candidate.parent.optimizer_step
            or execution.candidate_step != candidate.update_steps + 1):
        invalid()
    return decay


def _candidate_step_proof(candidate, execution, update_mask, loss_bearing,
                          training_authority):
    proof_args = dict(
        step_index=candidate.update_steps + 1,
        provenance_sha256=execution.digest,
        participation_sha256=participation_digest(execution.participation),
        mask_sha256=mask_digest(execution.mask),
        parameter_names=tuple(sorted(update_mask)),
        loss_bearing=bool(loss_bearing))
    if training_authority is None:
        return CandidateStepProof(
            **proof_args,
            training_objective_digest=candidate.training_objective_digest,
            schema_version=OBJECTIVE_MINIMAL_STEP_PROOF_SCHEMA)
    from bilqis_mlx.runtime.atlas_training_authority import (
        BamfLogicalBatchTrainingAuthority, BamfTrainingAuthority,
    )
    if type(training_authority) not in (
            BamfTrainingAuthority, BamfLogicalBatchTrainingAuthority):
        invalid()
    training_authority.__post_init__()
    common = dict(
        source_release_sha256=training_authority.release_sha256,
        training_batch_sha256=training_authority.training_batch_sha256,
        target_capability_id=training_authority.delivery_capability,
        training_authority_sha256=training_authority.digest,
        training_objective_digest=candidate.training_objective_digest,
    )
    if type(training_authority) is BamfTrainingAuthority:
        closure = getattr(training_authority, "artifact_closure_sha256", None)
        if closure is not None:
            from bilqis_mlx.semantics.dependencies.closure import closure_digest
            if closure_digest(training_authority.artifact_nodes) != closure:
                invalid()
        return CandidateStepProof(
            **proof_args, **common,
            source_family_id=training_authority.source_family_id,
            episode_id=training_authority.episode_id,
            artifact_closure_sha256=closure,
            schema_version=(
                OBJECTIVE_CLOSURE_STEP_PROOF_SCHEMA
                if closure else OBJECTIVE_STEP_PROOF_SCHEMA))
    if type(training_authority) is BamfLogicalBatchTrainingAuthority:
        closure = training_authority.artifact_closure_sha256
        if closure is not None:
            from bilqis_mlx.semantics.dependencies.closure import closure_digest
            if closure_digest(training_authority.artifact_nodes) != closure:
                invalid()
        return CandidateStepProof(
            **proof_args, **common,
            training_authority_members=tuple(
                (member.digest, member.source_family_id, member.episode_id)
                for member in training_authority.members),
            artifact_closure_sha256=closure,
            schema_version=(
                OBJECTIVE_LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA
                if closure else OBJECTIVE_LOGICAL_BATCH_STEP_PROOF_SCHEMA))
    invalid()


def candidate_step(candidate: CandidateTransaction, gradients, execution,
                   teacher_hparams, *, spec, extents, loss_bearing: bool,
                   max_norm: float, training_authority=None) -> CandidateTransaction:
    """Bind the step to owner-issued execution provenance, then run native AdamW.

    The mask comes from the B09.2 owner's provenance, never from a caller
    mapping. Counts identify actual participating rows, including
    numerical-zero gradients. No-loss and wholly frozen steps preserve the
    transaction object.
    """
    if type(candidate) is not CandidateTransaction:
        invalid()
    candidate.__post_init__()
    if candidate.motif_transition is not None:
        invalid()
    if type(execution) is not StepExecutionProvenance:
        invalid()
    from ..atlas_execution_provenance import require_execution_training_authority
    require_execution_training_authority(execution, training_authority)
    decay = _validated_step_decay(candidate, execution, spec, extents)
    update_mask = optimizer_participation_mask(
        execution.mask, candidate.optimizer.update_counts)
    participation_authority = {
        item.name: (item.whole_parameter, item.row_indices)
        for item in execution.mask.parameters
    }
    optimizer = _adamw_update(
        candidate.optimizer, gradients, update_mask, teacher_hparams,
        decay=decay, loss_bearing=loss_bearing, max_norm=max_norm,
        participation_authority=participation_authority)
    if optimizer is candidate.optimizer:
        return candidate
    proof = _candidate_step_proof(
        candidate, execution, update_mask, loss_bearing, training_authority)
    return _issue_transaction(
        candidate.parent, optimizer, candidate.teacher_requests_full,
        candidate.update_steps + 1, candidate.step_proofs + (proof,),
        candidate.training_authorities + (training_authority,),
        parent_identity_sha256=candidate._parent_identity_sha256,
        parent_guard=candidate._parent_guard)



__all__ = ("candidate_step",)
