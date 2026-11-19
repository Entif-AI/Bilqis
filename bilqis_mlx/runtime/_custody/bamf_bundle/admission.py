"""Production candidate admission: derive, step, accept, publish.

This is the production path from executed-step evidence to a published accepted
generation. The B09.2 binder derives the participation and the mask, the
retention owner mints the acceptance binding, and B13 custody publishes the
generation only with that binding. No test helper is involved.

The generation identity used to bind a step comes from the published custody,
never from caller parameters, so a provenance record cannot be replayed onto
another candidate, generation, step, topology or extents state.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from bilqis_mlx.learning.atlas_acceptance import (
    ParsedAcceptedCandidateBinding, candidate_identity_digest,
    mint_acceptance_binding,
)
from bilqis_mlx.learning.atlas_retention_decision import (
    CandidateRetentionDecision,
)
from bilqis_mlx.learning.atlas_candidate import (
    CandidateState, CandidateTransaction, _begin_candidate_with_parent_identity,
    resolve_candidate,
)
from bilqis_mlx.learning.atlas_plasticity import group_eligibility, next_update_mode
from bilqis_mlx.learning.atlas_participation import ActiveAdmittedRows
from bilqis_mlx.runtime.atlas_candidate_step import production_candidate_step
from bilqis_mlx.runtime.model_topology_v2 import ParameterCensus

from .accepted_runtime import (
    AcceptedGenerationIdentity, _identity_from_pointer,
    _published_in_memory_identity, _read_accepted, _read_accepted_locked,
    bind_accepted_execution_cache,
    load_accepted_generation,
)
from .codec import load_bamf_bundle
from .publication import (
    _pointer_read_lock, _read_pointer, _require_published_acceptance,
    publish_bamf_generation,
)
from .publication.authority import authenticate_current_successor_retry
from .records import (
    BamfBundleCandidate, CompleteStudent, canonical, invalid, sha,
)
from .motif.transition import derive_motif_allocation_transition


def derive_successor_bundle(parent: CompleteStudent, retained_state: CandidateState,
                            *, parent_manifest_sha256: str,
                            delivery_events: tuple) -> BamfBundleCandidate:
    """Build the successor generation bundle from the accepted parent custody.

    The successor inherits the parent's topology, extents, provenance and
    sidecars. Only the retained optimizer state, the generation identity, the
    transition kind and the delivery intent change. The delivery events are
    unbound intent records for the new lineage; the parent's bound outbox is
    never replayed under a new generation.
    """
    if type(parent) is not CompleteStudent or type(retained_state) is not CandidateState:
        invalid("BAMF_GENERATION_PARENT_INVALID")
    if retained_state.allocations.digest != parent.retained_state.allocations.digest:
        invalid("BAMF_MOTIF_ALLOCATION_TRANSITION_REQUIRED")
    kind = "RETAINED_CANDIDATE"
    transition = {
        "schema": "bilqis.mlx.bamf-generation-transition/v1",
        "kind": kind,
        "invalidate_derived_caches": kind in {"PARAMETER_EXTENSION", "MODEL_SWAP"},
    }
    return BamfBundleCandidate(
        parent.run_id, parent.generation + 1, parent_manifest_sha256,
        parent.implementation_sha256, parent.topology, parent.extents,
        retained_state, parent.optimizer_hyperparameters, parent.provenance,
        dict(parent.semantic_abi), dict(parent.compiler_features),
        dict(parent.correction_frontier), dict(parent.teacher_state),
        dict(parent.evaluation_contract), transition, tuple(delivery_events),
        parent.run_identity, parent.baseline_evidence, parent.learning_health_state,
        parent.championship_state)


def derive_motif_successor_bundle(
        parent: CompleteStudent, transaction: CandidateTransaction, *, retained_state=None,
        parent_manifest_sha256: str, delivery_events: tuple) -> BamfBundleCandidate:
    """Build the exact successor C05 must screen for a staged B07 transition."""
    from bilqis_mlx.learning._atlas_candidate.motif_transition import (
        _require_candidate_motif_allocation_transition,
    )
    from bilqis_mlx.runtime.atlas_optimizer import reconcile_b01_optimizer_manifest

    if (type(parent) is not CompleteStudent
            or type(transaction) is not CandidateTransaction
            or transaction.motif_transition is None
            or transaction.parent.custody is None
            or transaction.parent.custody.manifest_sha256 != parent_manifest_sha256
            or candidate_identity_digest(transaction.parent)
            != candidate_identity_digest(parent.retained_state)):
        invalid("BAMF_MOTIF_ALLOCATION_TRANSITION_INVALID")
    b12 = transaction.motif_transition
    _require_candidate_motif_allocation_transition(b12)
    retained_state = (
        resolve_candidate(transaction, accepted=True)
        if retained_state is None else retained_state)
    if type(retained_state) is not CandidateState:
        invalid("BAMF_MOTIF_ALLOCATION_TRANSITION_INVALID")
    extents = b12.candidate_extents
    reconcile_b01_optimizer_manifest(retained_state.optimizer, parent.topology, extents)
    from bilqis_mlx.learning._atlas_candidate.identity_binding import (
        bind_candidate_identity_or_fallback,
    )
    bind_candidate_identity_or_fallback(
        retained_state, parent.topology.digest, extents.digest)
    transition = derive_motif_allocation_transition(b12, retained_state)
    return BamfBundleCandidate(
        parent.run_id, parent.generation + 1, parent_manifest_sha256,
        parent.implementation_sha256, parent.topology, extents,
        retained_state, parent.optimizer_hyperparameters, parent.provenance,
        dict(parent.semantic_abi), dict(parent.compiler_features),
        dict(parent.correction_frontier), dict(parent.teacher_state),
        dict(parent.evaluation_contract), transition, tuple(delivery_events),
        parent.run_identity, parent.baseline_evidence, parent.learning_health_state,
        parent.championship_state)


def _parameter_census(parent: CompleteStudent) -> ParameterCensus:
    """The B01 parameter census owner for the accepted generation.

    The declared parameter set is read through the census owner module that the
    participation owner validates against, so both see exactly the same ledger.
    """
    owner = sys.modules["bilqis_mlx.learning.atlas_participation_census"]
    return ParameterCensus(
        parent.topology.digest, parent.extents.digest,
        owner.expected_bamf_shapes(parent.topology, parent.extents))


def derive_participation_inputs(parent: CompleteStudent):
    """Derive structural eligibility from B01 and the retained policy.

    The group eligibility comes from the B01 parameter census owner and the
    retained policy owner, and the admitted rows from published custody.
    Neither the census nor these eligibility facts prove actual execution.
    """
    census = _parameter_census(parent)
    mode = next_update_mode(parent.retained_state.policy,
                             teacher_requests_full=False)
    eligibility = group_eligibility(
        mode, census, parent.retained_state.policy.row_ages)
    return eligibility, ActiveAdmittedRows(
        identity_rows=eligibility.admitted_identity_rows)


def _admit_loaded_candidate_step(
        parent: CompleteStudent, identity: AcceptedGenerationIdentity, gradients=None, *,
        loss_bearing_target, gradient_execution=None, logical_batch_execution=None,
        training_batch=None, logical_batch_plan=None, teacher_hparams,
        max_norm: float, candidate: CandidateTransaction | None = None,
        execution_cache=None) -> CandidateTransaction:
    """Pass custody-verified state plus B11 execution truth to B09/B12.

    Raw gradients remain usable only for the no-loss no-op path. A loss-bearing
    update must carry the unforgeable ``BamfGradientExecution`` issued by the
    real B11 forward/backward owner; B09 then derives participation and the
    final update mask from that same execution record.
    """
    if (type(parent) is not CompleteStudent
            or type(identity) is not AcceptedGenerationIdentity
            or identity.run_id != parent.run_id
            or identity.generation != parent.generation
            or identity.topology_digest != parent.topology.digest
            or identity.extents_digest != parent.extents.digest
            or identity.optimizer_step != parent.retained_state.optimizer_step):
        invalid("BAMF_GENERATION_POINTER_DRIFT")
    if candidate is None:
        candidate = _begin_candidate_with_parent_identity(
            parent.retained_state, identity.candidate_identity_sha256)
    elif (type(candidate) is not CandidateTransaction
            or candidate.parent is not parent.retained_state
            or candidate._parent_identity_sha256 != identity.candidate_identity_sha256):
        invalid("BAMF_CANDIDATE_CONTINUATION_PARENT_DRIFT")
    candidate.__post_init__()
    eligibility, _active_admitted = derive_participation_inputs(parent)
    return production_candidate_step(
        candidate, gradients,
        loss_bearing_target=loss_bearing_target,
        gradient_execution=gradient_execution,
        logical_batch_execution=logical_batch_execution,
        training_batch=training_batch,
        logical_batch_plan=logical_batch_plan,
        group_eligible=eligibility,
        spec=parent.topology, extents=parent.extents,
        run_id=identity.run_id, generation=identity.generation + 1,
        parent_manifest_sha256=identity.manifest_sha256,
        parent_candidate_identity_sha256=identity.candidate_identity_sha256,
        parent_optimizer_step=identity.optimizer_step,
        topology_digest=identity.topology_digest,
        candidate_step_ordinal=candidate.update_steps + 1,
        teacher_hparams=teacher_hparams, max_norm=max_norm,
        execution_cache=execution_cache)


def admit_uninterrupted_candidate_step(
        run_dir: Path, parent: CompleteStudent, gradients=None, *,
        loss_bearing_target, gradient_execution=None, logical_batch_execution=None,
        training_batch=None, logical_batch_plan=None, teacher_hparams,
        max_norm: float, candidate: CandidateTransaction | None = None,
        execution_cache=None, currentness_transaction=None) -> CandidateTransaction:
    """Continue held state only after full current B13 custody authentication."""
    if currentness_transaction is None:
        identity = _published_in_memory_identity(run_dir, parent)
    else:
        from .currentness_transaction import accepted_currentness_identity
        identity = accepted_currentness_identity(currentness_transaction, parent)
    return _admit_loaded_candidate_step(
        parent, identity, gradients,
        loss_bearing_target=loss_bearing_target,
        gradient_execution=gradient_execution,
        logical_batch_execution=logical_batch_execution,
        training_batch=training_batch,
        logical_batch_plan=logical_batch_plan,
        teacher_hparams=teacher_hparams, max_norm=max_norm, candidate=candidate,
        execution_cache=execution_cache)


def admit_candidate_step(run_dir: Path, gradients=None, *,
                         loss_bearing_target, gradient_execution=None,
                         logical_batch_execution=None, training_batch=None,
                         logical_batch_plan=None, teacher_hparams,
                         max_norm: float) -> CandidateTransaction:
    """Cold-load the accepted state and enter the production execution guard."""
    pointer, parent = _read_accepted(run_dir)
    identity = _identity_from_pointer(parent, pointer)
    return _admit_loaded_candidate_step(
        parent, identity, gradients,
        loss_bearing_target=loss_bearing_target,
        gradient_execution=gradient_execution,
        logical_batch_execution=logical_batch_execution,
        training_batch=training_batch,
        logical_batch_plan=logical_batch_plan,
        teacher_hparams=teacher_hparams, max_norm=max_norm)


def _require_source_authority_for_acceptance(
        run_dir: Path, candidate: BamfBundleCandidate, *, parent_witness=None):
    """Authenticate current custody and derive the ordinary successor C09 root."""
    from .source_authority_custody import (
        require_source_authority_successor_inheritance,
    )

    run_dir = Path(run_dir)
    with _pointer_read_lock(run_dir):
        current = _read_pointer(run_dir / "bamf-state.json")
        if current is None:
            invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
        if current["generation"] == candidate.generation - 1:
            if parent_witness is not None:
                from .accepted_execution_cache import (
                    _require_accepted_publication_parent_locked,
                )
                current_child = _require_accepted_publication_parent_locked(
                    run_dir, current, parent_witness).student
            else:
                current, current_child = _read_accepted_locked(run_dir)
            if (candidate.run_id != current_child.run_id
                    or candidate.generation != current_child.generation + 1
                    or candidate.parent_manifest_sha256
                    != current["manifest_sha256"]
                    or candidate.run_identity != current_child.run_identity):
                invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
            return require_source_authority_successor_inheritance(
                run_dir,
                current_child.correction_frontier,
                candidate.correction_frontier,
                allow_historical_anchor=(
                    candidate.transition.get("kind") == "RETAINED_CANDIDATE"),
            )
        if current["generation"] == candidate.generation:
            current, current_child = _read_accepted_locked(run_dir)
            parent, persisted = authenticate_current_successor_retry(
                run_dir, current, candidate, current_child,
                load_bundle=load_bamf_bundle,
                require_published_acceptance=_require_published_acceptance,
            )
            if not isinstance(persisted, ParsedAcceptedCandidateBinding):
                invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
            registry = require_source_authority_successor_inheritance(
                run_dir,
                parent.correction_frontier,
                current_child.correction_frontier,
                allow_historical_anchor=(
                    current_child.transition.get("kind") == "RETAINED_CANDIDATE"),
            )
            digest = registry.digest if registry is not None else None
            if digest != persisted.source_authority_registry_sha256:
                invalid("BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_MISMATCH")
            return registry
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")


def _publication_parent_witness(
        run_dir: Path, candidate: BamfBundleCandidate):
    if candidate.generation == 0:
        return None
    from .accepted_execution_cache import _bind_accepted_publication_parent_locked

    run_dir = Path(run_dir)
    with _pointer_read_lock(run_dir):
        current = _read_pointer(run_dir / "bamf-state.json")
        if current is None:
            invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
        if current["generation"] == candidate.generation:
            return None
        if (current["generation"] != candidate.generation - 1
                or current["manifest_sha256"] != candidate.parent_manifest_sha256):
            invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
        return _bind_accepted_publication_parent_locked(run_dir, current)


def accept_and_publish(run_dir: Path, bundle: BamfBundleCandidate,
                       retained_state: CandidateState, *,
                       decision: CandidateRetentionDecision,
                       feature_sha256: str,
                       reserve_gib: float = 100.0,
                       training_authorities=None,
                       publication_observer=None) -> dict:
    """Publish a candidate that the retention decision owner has accepted.

    Publication does not decide that the candidate was accepted. The retention
    decision owner issues the decision, the retention owner mints the acceptance
    binding from that decision, and B13 custody publishes the generation only
    when the binding matches the candidate it publishes.
    """
    from .genesis.records import successor_candidate_identity_digest
    from bilqis_mlx.learning.atlas_retention_decision import (
        _issued_decision_generation_authority,
        _require_issued_decision_generation_authority,
    )

    from .publication.instrumentation import publication_measurement
    with publication_measurement(publication_observer):
        parent_witness = _publication_parent_witness(run_dir, bundle)
        trusted_registry = _require_source_authority_for_acceptance(
            run_dir, bundle, parent_witness=parent_witness)
        exact_generation_authority = successor_candidate_identity_digest(bundle)
        if _issued_decision_generation_authority(decision) is not None:
            _require_issued_decision_generation_authority(
                decision, exact_generation_authority)
        binding = mint_acceptance_binding(
            decision, retained_state, run_id=bundle.run_id,
            generation=bundle.generation, feature_sha256=feature_sha256,
            training_authorities=training_authorities,
            source_authority_registry_sha256=(
                trusted_registry.digest if trusted_registry is not None else None),
            teacher_state_sha256=sha(canonical(dict(bundle.teacher_state))),
            generation_authority_sha256=exact_generation_authority)
        return publish_bamf_generation(
            run_dir, bundle, acceptance=binding, reserve_gib=reserve_gib,
            parent_witness=parent_witness)
