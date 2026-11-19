"""Crash-idempotent, serialized B13.1 pointer publication and outbox recovery."""
from __future__ import annotations

import os
from pathlib import Path

from bilqis_mlx.data_plane import DataPlaneError
from bilqis_mlx.learning.atlas_acceptance import AcceptedCandidateBinding

from ..atlas_admission import (
    AtlasAdmissionBinding, require_atlas_admission_binding,
)
from ..factory_release.admission import (
    FactoryReleaseAdmissionBinding,
    require_factory_release_admission_binding,
)
from ..codec import load_bamf_bundle, save_bamf_bundle
from ..records import (
    BAMF_POINTER_SCHEMA, BamfBundleCandidate, CompleteStudent,
    complete_student_from_candidate, invalid,
)
from .authority import (
    _UNBOUND_RETRY,
    load_generation_locked as _load_generation_locked_impl,
    parent_acceptance_for_publication as _parent_acceptance_for_publication_impl,
    require_acceptance as _require_acceptance,
    require_accepted_parent as _require_accepted_parent_impl,
    require_published_acceptance as _require_published_acceptance_impl,
    validate_parent_transition as _validate_parent_transition_impl,
)
from .events import reconcile_bamf_outbox, record_bamf_rejection
from .factory_release import persist_prepared_initial_factory_release
from .genesis_trust import publish_initial_generation_trust_root
from .inspection import AcceptedGenerationInspection, inspect_accepted_generation
from .retry import (
    _existing_initial_generation_retry, recover_prepared_initial_generation,
    recover_sealed_initial_generation,
    reconcile_already_pointed_retry as _reconcile_already_pointed_retry,
)
from .storage import (
    ACCEPTANCE_DIR, _acceptance_path, _atomic_pointer, _live_bundle_manifest,
    _fsync_directory, _initial_generation_pointer_lock, _pointer_lock,
    _pointer_read_lock, _publication_pointer_lock, _read_pointer,
    _remove_stage, _require_bundle_root, _require_run_root, _stage, _write_acceptance,
)


def _require_published_acceptance(
        run_dir: Path, pointer: dict, student: CompleteStudent, *,
        accepted_parent: tuple[str, CompleteStudent] | None = None):
    return _require_published_acceptance_impl(
        run_dir, pointer, student,
        load_bundle=load_bamf_bundle, live_manifest=_live_bundle_manifest,
        accepted_parent=accepted_parent)


def _load_generation_locked(pointer_path: Path) -> tuple[CompleteStudent, dict]:
    return _load_generation_locked_impl(
        pointer_path, read_pointer=_read_pointer,
        live_manifest=_live_bundle_manifest, load_bundle=load_bamf_bundle)


def _parent_acceptance_for_publication(
        run_dir: Path, candidate: BamfBundleCandidate,
        accepted, *, parent_witness=None):
    from ..accepted_execution_cache import (
        _bind_accepted_publication_parent_locked,
        _require_accepted_publication_parent_locked,
    )
    pointer_lock = (
        _initial_generation_pointer_lock
        if candidate.generation == 0 else _publication_pointer_lock)
    return _parent_acceptance_for_publication_impl(
        run_dir, candidate, accepted,
        pointer_lock=pointer_lock, read_pointer=_read_pointer,
        live_manifest=_live_bundle_manifest, load_bundle=load_bamf_bundle,
        require_published_acceptance=_require_published_acceptance,
        parent_witness=parent_witness,
        bind_parent_witness_locked=_bind_accepted_publication_parent_locked,
        require_parent_witness_locked=_require_accepted_publication_parent_locked)


def _save_publication_bundle(candidate: BamfBundleCandidate, stage: Path,
                             parent_acceptance, *, reserve_gib: float):
    """Use the acceptance-bound writer when available; preserve pinned old-writer replay."""
    if parent_acceptance is _UNBOUND_RETRY:
        return save_bamf_bundle(candidate, stage, reserve_gib=reserve_gib)
    try:
        return save_bamf_bundle(
            candidate, stage, reserve_gib=reserve_gib,
            parent_acceptance_sha256=parent_acceptance)
    except TypeError as exc:
        if "unexpected keyword argument 'parent_acceptance_sha256'" not in str(exc):
            raise
        if candidate.generation > 0:
            invalid("BAMF_GENERATION_ACCEPTANCE_MISSING")
        return save_bamf_bundle(candidate, stage, reserve_gib=reserve_gib)


def publish_bamf_generation(
        run_dir: Path, candidate: BamfBundleCandidate, *,
        acceptance: AcceptedCandidateBinding | None = None,
        reserve_gib: float = 100.0, parent_witness=None,
        publication_observer=None) -> dict:
    """Publish one retained successor; generation zero has a separate B13 gate."""
    accepted = _require_acceptance(candidate, acceptance)
    from .instrumentation import publication_measurement
    with publication_measurement(publication_observer):
        return _publish_authorized_generation(
            run_dir, candidate, accepted, reserve_gib=reserve_gib,
            parent_witness=parent_witness)


def publish_atlas_admission_generation(
        run_dir: Path, candidate: BamfBundleCandidate, *,
        admission: AtlasAdmissionBinding, reserve_gib: float = 100.0) -> dict:
    """Publish one C07-authorized parameter extension through B13 custody."""
    admitted = require_atlas_admission_binding(candidate, admission)
    return _publish_authorized_generation(
        run_dir, candidate, admitted, reserve_gib=reserve_gib)


def publish_factory_release_adoption_generation(
        run_dir: Path, candidate: BamfBundleCandidate, *,
        admission: FactoryReleaseAdmissionBinding,
        reserve_gib: float = 100.0,
        expected_active_grade_activation_sha256: str | None = None) -> dict:
    """Publish one neural-inert Factory-release successor through B13 custody."""
    admitted = require_factory_release_admission_binding(candidate, admission)
    return _publish_authorized_generation(
        run_dir, candidate, admitted, reserve_gib=reserve_gib,
        expected_active_grade_activation_sha256=expected_active_grade_activation_sha256)
def _authorize_publication_candidate(
        run_dir: Path, candidate: BamfBundleCandidate, authority):
    """Validate generation-specific authority before entering shared publication."""
    if candidate.generation > 0:
        if type(authority) is AtlasAdmissionBinding:
            return require_atlas_admission_binding(candidate, authority), None, None
        if type(authority) is FactoryReleaseAdmissionBinding:
            return require_factory_release_admission_binding(
                candidate, authority), None, None
        accepted = _require_acceptance(candidate, authority)
        return accepted, None, None
    from ..genesis import (
        PreparedInitialGeneration, validate_initial_generation_binding,
        validate_initial_generation_preparation,
        validate_initial_generation_source_authority,
    )
    if (type(authority) is not PreparedInitialGeneration
            or authority.candidate is not candidate):
        invalid("BAMF_INITIAL_GENERATION_PREPARATION_REQUIRED")
    authority.__post_init__()
    validate_initial_generation_binding(candidate, authority.binding)
    validate_initial_generation_source_authority(candidate)
    existing = _existing_initial_generation_retry(run_dir, candidate, authority)
    if existing is not None:
        return None, authority, existing
    validate_initial_generation_preparation(authority)
    return authority.binding, authority, None


def _require_successor_source_authority(run_dir, parent, child, authority):
    from ..source_authority_custody import require_source_authority_successor_inheritance

    trusted = require_source_authority_successor_inheritance(
        run_dir,
        parent.correction_frontier,
        child.correction_frontier,
        allow_historical_anchor=(
            type(authority) is AcceptedCandidateBinding
            and child.transition.get("kind") == "RETAINED_CANDIDATE"),
    )
    trusted_digest = trusted.digest if trusted is not None else None
    if trusted_digest != child.correction_frontier.get(
            "source_authority_registry_sha256"):
        invalid("BAMF_C09_SOURCE_AUTHORITY_TRUST_ROOT_MISMATCH")
    return trusted


def _witnessed_parent_locked(run_dir, current, parent_witness):
    if parent_witness is None:
        return None, None
    from ..accepted_execution_cache import (
        _require_accepted_publication_parent_locked,
    )
    witness = _require_accepted_publication_parent_locked(
        run_dir, current, parent_witness)
    return witness.student, witness


def _install_publication_target(stage, target, digest, published_student):
    if target.exists() or target.is_symlink():
        if target.is_symlink() or not target.is_dir():
            invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
        from .instrumentation import publication_bundle_load
        with publication_bundle_load("child"):
            published_student = load_bamf_bundle(
                target, expected_manifest_sha256=digest)
        _remove_stage(stage)
        return published_student
    stage.rename(target)
    _fsync_directory(stage.parent)
    _fsync_directory(target.parent)
    return published_student


def _publish_authorized_generation(
        run_dir: Path, candidate: BamfBundleCandidate, authority, *,
        reserve_gib: float, parent_witness=None,
        expected_active_grade_activation_sha256=None) -> dict:
    """Shared crash-safe transaction after generation-specific authority validates."""
    authority, prepared, existing = _authorize_publication_candidate(
        run_dir, candidate, authority)
    if existing is not None:
        return existing
    run_dir = Path(run_dir)
    parent_acceptance, parent_witness = _parent_acceptance_for_publication(
        run_dir, candidate, authority, parent_witness=parent_witness)
    stage = _stage(run_dir)
    try:
        manifest = _save_publication_bundle(
            candidate, stage, parent_acceptance, reserve_gib=reserve_gib)
        digest = manifest["manifest_sha256"]
        published_student = complete_student_from_candidate(candidate)
        target = _require_bundle_root(run_dir, create=True) / digest
        pointer_path = run_dir / "bamf-state.json"
        pointer_lock = (
            _initial_generation_pointer_lock
            if candidate.generation == 0 else _publication_pointer_lock)
        with pointer_lock(run_dir):
            current = _read_pointer(pointer_path)
            if expected_active_grade_activation_sha256 is not None:
                from bilqis_mlx.runtime.active_generated_grade_custody import (
                    _read_stored_active,
                )
                active = _read_stored_active(run_dir)
                if (active is None or active.activation_sha256 !=
                        expected_active_grade_activation_sha256):
                    invalid("BAMF_PROFILE_ACTIVE_GRADE_MEMBERSHIP_DRIFT")
            if current is not None and current["generation"] == candidate.generation:
                return _reconcile_already_pointed_retry(
                    run_dir, current, candidate, authority, prepared, digest, stage,
                    require_successor_source_authority=_require_successor_source_authority)
            if prepared is not None:
                from ..genesis import validate_initial_generation_preparation
                validate_initial_generation_preparation(prepared)
            witnessed_parent, parent_witness = _witnessed_parent_locked(
                run_dir, current, parent_witness)
            parent = _validate_parent_transition_impl(
                run_dir, current, candidate,
                load_bundle=load_bamf_bundle, reconcile=reconcile_bamf_outbox,
                parent=witnessed_parent,
                factory_release_new_semantic_admission=(
                    type(authority) is FactoryReleaseAdmissionBinding
                    and authority.generated_grade_proposal_sha256 is not None))
            if candidate.generation > 0:
                if parent is None:
                    invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
                _require_successor_source_authority(
                    run_dir, parent, candidate, authority)
                _require_accepted_parent_impl(
                    run_dir, candidate, authority, load_bundle=load_bamf_bundle,
                    parent=parent)
                live_parent_acceptance = (
                    parent_witness.acceptance_sha256
                    if parent_witness is not None else
                    _require_published_acceptance(run_dir, current, parent).digest)
                if live_parent_acceptance != parent_acceptance:
                    invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
            published_student = _install_publication_target(
                stage, target, digest, published_student)
            if prepared is not None:
                persist_prepared_initial_factory_release(run_dir, prepared)
                publish_initial_generation_trust_root(run_dir, prepared, digest)
            _write_acceptance(run_dir, digest, authority)
            pointer = {
                "schema": BAMF_POINTER_SCHEMA, "run_id": candidate.run_id,
                "generation": candidate.generation,
                "parent_manifest_sha256": candidate.parent_manifest_sha256,
                "bundle": str(target.relative_to(run_dir)),
                "manifest_sha256": digest, "acceptance_sha256": authority.digest,
            }
            _atomic_pointer(pointer_path, pointer)
            reconcile_bamf_outbox(run_dir, published_student)
            return pointer
    except BaseException:
        if stage.exists() and stage.is_dir() and not stage.is_symlink():
            _remove_stage(stage)
        raise


def load_bamf_generation_authority(
        pointer_path: Path) -> tuple[CompleteStudent, str]:
    """Read current accepted B13 authority without mutating delivery state."""
    pointer_path = Path(pointer_path)
    with _pointer_read_lock(pointer_path.parent):
        student, pointer = _load_generation_locked(pointer_path)
        _require_published_acceptance(pointer_path.parent, pointer, student)
        return student, pointer["manifest_sha256"]


def load_bamf_generation(
        pointer_path: Path, *, publish_missing_outbox: bool = True) -> CompleteStudent:
    pointer_path = Path(pointer_path)
    with _pointer_lock(pointer_path.parent):
        student, _ = _load_generation_locked(pointer_path)
        reconcile_bamf_outbox(
            pointer_path.parent, student, publish_missing=publish_missing_outbox)
        return student
