"""Generation acceptance and lineage checks used by B13 publication."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.data_plane import DataPlaneError
from bilqis_mlx.learning.atlas_acceptance import (
    ACCEPTANCE_SCHEMA, MOTIF_ACCEPTANCE_SCHEMA, CLOSURE_ACCEPTANCE_SCHEMA,
    MOTIF_CLOSURE_ACCEPTANCE_SCHEMA, EXACT_ACCEPTANCE_SCHEMA,
    EXACT_CLOSURE_ACCEPTANCE_SCHEMA, EXACT_MOTIF_ACCEPTANCE_SCHEMA,
    EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA, AcceptedCandidateBinding,
    _issued_acceptance_baseline_ledger_sha256, _require_issued_binding,
)
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_for_canonical_consumer,
)

from ..factory_release.admission import (
    require_factory_release_inert_state,
)
from ..factory_release_adoption import (
    is_factory_release_adoption_transition,
    require_issued_factory_release_adoption_transition,
)
from ..package_import_transition import (
    is_package_import_transition, require_issued_package_import_transition,
)
from ..motif.transition import (
    is_motif_allocation_transition, require_issued_motif_allocation_transition,
)
from ..records import (
    ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA, BamfBundleCandidate, CompleteStudent,
    OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA, canonical, invalid, sha,
)
from .acceptance import (
    load_generation_locked, require_accepted_parent, require_published_acceptance,
)


_UNBOUND_RETRY = object()


def _require_c03_visit_authority(candidate: BamfBundleCandidate) -> None:
    """Authenticate any portable C03 visit marker before B13 seals custody."""
    state = candidate.teacher_state
    receipt = state.get("last_visit_receipt")
    visit = state.get("last_visit")
    if receipt is None and visit is None:
        return
    if receipt is None or visit is None:
        invalid("TEACHER_VISIT_CUSTODY_INVALID")
    from bilqis_mlx.learning.teacher_visit_identity import (
        TeacherVisitIdentity, require_teacher_visit_receipt,
        validate_teacher_visit_receipt_record,
    )

    identity = TeacherVisitIdentity.from_record(visit)
    validate_teacher_visit_receipt_record(identity, receipt)
    require_teacher_visit_receipt(identity)


def require_acceptance(
        candidate: BamfBundleCandidate,
        acceptance: AcceptedCandidateBinding | None) -> AcceptedCandidateBinding:
    """Publication is not acceptance: the retention owner must have accepted it."""
    if candidate.generation == 0:
        invalid("BAMF_INITIAL_GENERATION_BOOTSTRAP_REQUIRED")
    if type(acceptance) is not AcceptedCandidateBinding:
        invalid("BAMF_GENERATION_ACCEPTANCE_REQUIRED")
    _require_c03_visit_authority(candidate)
    _require_issued_binding(acceptance)
    acceptance.__post_init__()
    expected_baseline = _issued_acceptance_baseline_ledger_sha256(acceptance)
    if expected_baseline is not None:
        from bilqis_mlx.runtime.baseline.lifecycle import BaselineLedger
        if BaselineLedger.from_optional_record(candidate.baseline_evidence).digest != expected_baseline:
            invalid("BAMF_C05_BASELINE_PUBLICATION_DRIFT")
    motif_transition = is_motif_allocation_transition(candidate.transition)
    expected_schema = ((EXACT_MOTIF_ACCEPTANCE_SCHEMA,
                        EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA)
                       if motif_transition
                       else (EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA))
    if (acceptance.schema_version not in expected_schema
            or acceptance.run_id != candidate.run_id
            or acceptance.generation != candidate.generation
            or acceptance.feature_sha256 != candidate.extents.factor_map_digest
            or acceptance.optimizer_step != candidate.retained_state.optimizer_step
            or acceptance.candidate_identity_sha256
            != candidate_identity_for_canonical_consumer(candidate.retained_state)
            or acceptance.step_proof_sha256 != tuple(
                proof.digest for proof in candidate.retained_state.step_proofs)
            or acceptance.source_authority_registry_sha256
            != candidate.correction_frontier.get(
                "source_authority_registry_sha256")):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    from ..genesis.records import successor_candidate_identity_digest
    if (acceptance.generation_authority_sha256
            != successor_candidate_identity_digest(candidate)):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    if (acceptance.teacher_state_sha256
            != sha(canonical(dict(candidate.teacher_state)))):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    from bilqis_mlx.learning._retention._atlas_acceptance_records import require_closure_proofs
    require_closure_proofs(acceptance, candidate.retained_state.step_proofs)
    return acceptance


def validate_parent_transition(
        run_dir: Path, pointer: dict | None, candidate: BamfBundleCandidate, *,
        load_bundle, reconcile, parent: CompleteStudent | None = None,
        factory_release_new_semantic_admission=False) -> CompleteStudent | None:
    if pointer is None:
        if candidate.generation != 0 or candidate.parent_manifest_sha256 is not None:
            invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
        return None
    if (pointer["run_id"] != candidate.run_id
            or pointer["generation"] != candidate.generation - 1
            or pointer["manifest_sha256"] != candidate.parent_manifest_sha256):
        invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
    if parent is None:
        parent = load_bundle(
            run_dir / pointer["bundle"], expected_manifest_sha256=pointer["manifest_sha256"])
    elif type(parent) is not CompleteStudent:
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    if (parent.run_id != pointer["run_id"]
            or parent.generation != pointer["generation"]
            or parent.parent_manifest_sha256 != pointer["parent_manifest_sha256"]):
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    parent_step = parent.retained_state.optimizer_step
    candidate_step = candidate.retained_state.optimizer_step
    if is_motif_allocation_transition(candidate.transition):
        require_issued_motif_allocation_transition(candidate.transition)
        transition = candidate.transition
        if (parent.topology.digest != candidate.topology.digest
                or candidate_step <= parent_step
                or parent.extents.digest != transition["parent_extents_sha256"]
                or candidate.extents.digest != transition["candidate_extents_sha256"]
                or parent.retained_state.allocations.digest
                != transition["parent_allocation_sha256"]
                or candidate.retained_state.allocations.digest
                != transition["candidate_allocation_sha256"]
                or candidate_identity_for_canonical_consumer(candidate.retained_state)
                != transition["candidate_identity_sha256"]
                or parent.extents.semantic_bank_count != candidate.extents.semantic_bank_count
                or parent.extents.active_semantic_digest != candidate.extents.active_semantic_digest
                or parent.extents.factor_map_digest != candidate.extents.factor_map_digest
                or candidate.extents.motif_page_count - parent.extents.motif_page_count
                != transition["added_pages"]
                or candidate.extents.motif_key_map_digest
                != candidate.retained_state.allocations.manifest.digest):
            invalid("BAMF_GENERATION_TRANSITION_INVALID")
    elif is_package_import_transition(candidate.transition):
        require_issued_package_import_transition(candidate.transition)
        if (parent.topology.digest != candidate.topology.digest
                or parent.extents.digest != candidate.extents.digest
                or candidate_step != parent_step):
            invalid("BAMF_GENERATION_TRANSITION_INVALID")
    elif is_factory_release_adoption_transition(candidate.transition):
        require_issued_factory_release_adoption_transition(candidate.transition)
        require_factory_release_inert_state(
            parent, candidate,
            new_semantic_admission=factory_release_new_semantic_admission)
        if candidate_step != parent_step:
            invalid("BAMF_GENERATION_TRANSITION_INVALID")
    else:
        if (parent.extents.motif_page_count != candidate.extents.motif_page_count
                or parent.extents.motif_key_map_digest
                != candidate.extents.motif_key_map_digest
                or parent.retained_state.allocations.digest
                != candidate.retained_state.allocations.digest):
            invalid("BAMF_GENERATION_TRANSITION_INVALID")
        kind = ("MODEL_SWAP" if parent.topology.digest != candidate.topology.digest else
                "PARAMETER_EXTENSION" if parent.extents.digest != candidate.extents.digest else
                "RETAINED_CANDIDATE")
        if (candidate_step < parent_step or
                (kind == "RETAINED_CANDIDATE" and candidate_step <= parent_step)):
            invalid("BAMF_REJECTED_CANDIDATE_NOT_GENERATION")
        if candidate.transition.get("kind") != kind:
            invalid("BAMF_GENERATION_TRANSITION_INVALID")
    reconcile(run_dir, parent)
    return parent


def authenticate_current_successor_retry(
        run_dir: Path,
        current: dict,
        candidate: BamfBundleCandidate,
        current_child: CompleteStudent,
        *,
        load_bundle,
        require_published_acceptance,
):
    """Authenticate one already-pointed exact successor retry from accepted custody."""
    from ..genesis.records import successor_candidate_identity_digest

    if (not isinstance(current, dict)
            or type(candidate) is not BamfBundleCandidate
            or type(current_child) is not CompleteStudent
            or current.get("run_id") != current_child.run_id
            or current.get("generation") != current_child.generation
            or current.get("parent_manifest_sha256")
            != current_child.parent_manifest_sha256
            or candidate.run_id != current_child.run_id
            or candidate.generation != current_child.generation
            or candidate.parent_manifest_sha256
            != current_child.parent_manifest_sha256
            or successor_candidate_identity_digest(current_child)
            != successor_candidate_identity_digest(candidate)):
        invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
    persisted = require_published_acceptance(run_dir, current, current_child)
    parent_sha = current_child.parent_manifest_sha256
    if parent_sha is None:
        invalid("BAMF_RUN_IDENTITY_DRIFT")
    parent = load_bundle(
        Path(run_dir) / "bamf-bundles" / parent_sha,
        expected_manifest_sha256=parent_sha)
    if (parent.run_id != current_child.run_id
            or parent.generation + 1 != current_child.generation
            or parent.run_identity != current_child.run_identity
            or persisted.parent_candidate_identity_sha256
            != candidate_identity_for_canonical_consumer(parent.retained_state)):
        invalid("BAMF_RUN_IDENTITY_DRIFT")
    return parent, persisted


def parent_acceptance_for_publication(
        run_dir: Path, candidate: BamfBundleCandidate,
        accepted: AcceptedCandidateBinding, *, pointer_lock, read_pointer,
        live_manifest, load_bundle, require_published_acceptance,
        parent_witness=None, bind_parent_witness_locked=None,
        require_parent_witness_locked=None):
    """Read the exact parent acceptance that the new immutable manifest must bind."""
    pointer_path = Path(run_dir) / "bamf-state.json"
    with pointer_lock(run_dir):
        current = read_pointer(pointer_path)
        if current is None:
            if candidate.generation != 0 or candidate.parent_manifest_sha256 is not None:
                invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
            return None, None
        if current["generation"] == candidate.generation:
            if (current["run_id"] != candidate.run_id
                    or current["parent_manifest_sha256"] != candidate.parent_manifest_sha256
                    or current.get("acceptance_sha256") != accepted.digest):
                invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
            manifest = live_manifest(run_dir, current)
            if manifest.get("schema") not in {
                    ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
                    OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
                }:
                return _UNBOUND_RETRY, None
            return manifest.get("parent_acceptance_sha256"), None
        if (current["run_id"] != candidate.run_id
                or current["generation"] != candidate.generation - 1
                or current["manifest_sha256"] != candidate.parent_manifest_sha256):
            invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
        if parent_witness is None and bind_parent_witness_locked is not None:
            parent_witness = bind_parent_witness_locked(run_dir, current)
        if parent_witness is not None:
            if require_parent_witness_locked is None:
                invalid("B13_PUBLICATION_PARENT_REQUIRED")
            witness = require_parent_witness_locked(run_dir, current, parent_witness)
            if (witness.student.run_id != current["run_id"]
                    or witness.student.generation != current["generation"]
                    or witness.manifest_sha256 != current["manifest_sha256"]):
                invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
            return witness.acceptance_sha256, witness
        parent = load_bundle(
            run_dir / current["bundle"],
            expected_manifest_sha256=current["manifest_sha256"])
        require_published_acceptance(run_dir, current, parent)
        return current["acceptance_sha256"], None
