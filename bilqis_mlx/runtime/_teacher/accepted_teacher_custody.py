"""C03 teacher-visit custody bound to the currently accepted B13 generation."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field, replace
import json
from pathlib import Path

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_candidate import CandidateState, CandidateTransaction
from bilqis_mlx.learning.teacher_lineage import (
    TeacherCustodyProjection, advance_teacher_lineage, bind_next_teacher_epoch,
    restore_teacher_lineage,
)
from bilqis_mlx.learning.teacher_visit_identity import (
    TeacherVisitIdentity, derive_teacher_visit_identity,
    record_teacher_visit_authority, record_teacher_visit_identity,
)
from bilqis_mlx.learning._teaching.teacher_lineage_records import (
    SHA256_HEX_LENGTH,
    digest,
    invalid,
)
from bilqis_mlx.runtime.bamf_bundle import CompleteStudent
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache, derive_motif_successor_bundle, derive_successor_bundle,
    load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle.records import (
    BamfBundleCandidate, sidecar_records,
)
from bilqis_mlx.runtime.teacher_policy_selection import select_visit_policy

from .accepted_teacher_state import (
    _bank_identity, _c03_projection, _plasticity_identity,
    _student_region, rebind_package_import_teacher_custody,
)

_BOUND_VISIT_ISSUER = object()
_STUDENT_SCHEMA = "bilqis.bamf.student-reference/v1"


@dataclass(frozen=True, init=False)
class BoundTeacherVisit:
    """C03-owned visit identity tied to one authenticated accepted generation."""

    projection: TeacherCustodyProjection
    identity: TeacherVisitIdentity
    _teacher_state_sha256: str = field(init=False, repr=False, compare=False)
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        invalid("TEACHER_VISIT_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self) -> None:
        if (getattr(self, "_issuance", None) is not _BOUND_VISIT_ISSUER
                or type(self.projection) is not TeacherCustodyProjection
                or type(self.identity) is not TeacherVisitIdentity
                or not isinstance(getattr(self, "_teacher_state_sha256", None), str)
                or len(self._teacher_state_sha256) != SHA256_HEX_LENGTH
                or self.projection.teacher_state.get("last_visit")
                != self.identity.to_record()):
            invalid("TEACHER_VISIT_CUSTODY_INVALID")
        restore_teacher_lineage(self.projection.teacher_state)


def _issue_bound_visit(projection, identity) -> BoundTeacherVisit:
    value = object.__new__(BoundTeacherVisit)
    for name, item in (
            ("projection", projection), ("identity", identity),
            ("_teacher_state_sha256", digest(projection.teacher_state)),
            ("_issuance", _BOUND_VISIT_ISSUER)):
        object.__setattr__(value, name, item)
    value.__post_init__()
    return value


def _accepted_parent(run_dir: Path):
    run_dir = Path(run_dir)
    parent = load_accepted_generation(run_dir)
    cache = bind_accepted_execution_cache(run_dir)
    identity = parent.run_identity
    if (type(parent) is not CompleteStudent or identity is None
            or cache.run_id != parent.run_id
            or cache.generation != parent.generation):
        invalid("TEACHER_ACCEPTED_GENERATION_DRIFT")
    return parent, cache


def _selection_projection(
        projection: TeacherCustodyProjection, selected_epoch) -> TeacherCustodyProjection:
    before = restore_teacher_lineage(projection.teacher_state)
    if (selected_epoch.prior_region != before.prior_region
            or selected_epoch.current_region != before.current_region
            or selected_epoch.student_sha256 != before.student_sha256
            or selected_epoch.replay_head != before.replay_head
            or selected_epoch.prior_teacher() != before.prior_teacher()):
        invalid("TEACHER_SELECTION_EPOCH_DRIFT")
    state = deepcopy(dict(projection.teacher_state))
    teacher = selected_epoch.teacher()
    lineage = state["c03_lineage"]
    lineage["current_teacher"] = teacher
    lineage["current_teacher_sha256"] = digest(teacher)
    selected = TeacherCustodyProjection(
        state, state["teacher_identity"], state["teacher_epoch"])
    restore_teacher_lineage(selected.teacher_state)
    return selected


def current_teacher_projection(
        run_dir: Path, parent: CompleteStudent, cache,
        projection: TeacherCustodyProjection) -> TeacherCustodyProjection:
    """Reduce durable current-generation observations over the immutable teacher base."""
    if type(projection) is not TeacherCustodyProjection:
        invalid("TEACHER_CUSTODY_PROJECTION_INVALID")
    epoch = restore_teacher_lineage(projection.teacher_state)
    from bilqis_mlx.runtime.outcomes.replay import replay_rejected_outcomes
    teacher = replay_rejected_outcomes(
        Path(run_dir), parent, cache, epoch.teacher())
    if teacher == epoch.teacher():
        return projection
    return _selection_projection(
        projection,
        replace(epoch, current_json=json.dumps(teacher, sort_keys=True, allow_nan=False)))


def select_accepted_teacher_visit(
        run_dir: Path, engine, school, rng, learning_settings,
        teacher_curriculum_scope, previsit_diagnostics, lesson_grade, *,
        capability_id: str, total_capabilities=None, plasticity_escape=None,
        legacy_receipt: Mapping | None = None,
        adaptation: Mapping | None = None,
        prior_region: str | None = None):
    """Lower-level custody witness; production selection uses lawful priority."""
    parent, cache = _accepted_parent(Path(run_dir))
    projection = _c03_projection(
        parent, legacy_receipt=legacy_receipt,
        adaptation=adaptation, prior_region=prior_region)
    projection = current_teacher_projection(run_dir, parent, cache, projection)
    epoch = restore_teacher_lineage(projection.teacher_state)
    school_student = getattr(getattr(school, "current_student", None), "sha256", None)
    if school_student != candidate_identity_digest(parent.retained_state):
        invalid("TEACHER_SELECTION_STUDENT_DRIFT")
    teacher = epoch.teacher()
    key, policy, metadata = select_visit_policy(
        engine, teacher, capability_id, school, rng, learning_settings,
        teacher_curriculum_scope, previsit_diagnostics, lesson_grade,
        total_capabilities=total_capabilities, plasticity_escape=plasticity_escape)
    selected_epoch = replace(
        epoch, current_json=json.dumps(teacher, sort_keys=True, allow_nan=False))
    selected = _selection_projection(projection, selected_epoch)
    identity = derive_teacher_visit_identity(
        selected.teacher_state,
        run_identity_sha256=parent.run_identity.digest,
        run_seed=parent.run_identity.run_seed,
        generation=parent.generation,
        accepted_manifest_sha256=cache.accepted_manifest_sha256,
        capability_id=capability_id, policy_key=key)
    recorded = record_teacher_visit_identity(selected.teacher_state, identity)
    recorded = record_teacher_visit_authority(recorded, identity)
    return _issue_bound_visit(recorded, identity), policy, metadata


def _require_current_visit(
        parent, cache, visit: BoundTeacherVisit, *,
        candidate_identity_sha256: str | None = None,
        currentness_step=None, currentness_transaction=None) -> None:
    if type(visit) is not BoundTeacherVisit:
        invalid("TEACHER_VISIT_CUSTODY_REQUIRED")
    if currentness_step is not None:
        from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
            require_accepted_currentness_step,
        )
        require_accepted_currentness_step(
            currentness_step, currentness_transaction, parent)
        identity = visit.identity
        projection = visit.projection
        state = projection.teacher_state
        if (getattr(visit, "_issuance", None) is not _BOUND_VISIT_ISSUER
                or type(projection) is not TeacherCustodyProjection
                or type(identity) is not TeacherVisitIdentity
                or digest(state) != visit._teacher_state_sha256
                or state.get("last_visit") != identity.to_record()):
            invalid("TEACHER_VISIT_CUSTODY_INVALID")
        projection.__post_init__()
        identity.__post_init__()
        if candidate_identity_sha256 is None:
            candidate_identity_sha256 = candidate_identity_digest(
                parent.retained_state)
        if (parent.run_identity is None
                or identity.run_identity_sha256 != parent.run_identity.digest
                or identity.run_seed != parent.run_identity.run_seed
                or identity.generation != parent.generation
                or identity.accepted_manifest_sha256
                   != cache.accepted_manifest_sha256
                or identity.teacher_identity != projection.teacher_identity
                or identity.teacher_epoch != projection.teacher_epoch
                or identity.student_sha256 != candidate_identity_sha256
                or identity.selection_seed != state.get("next_seed")
                or identity.cursor != state.get("cursor")):
            invalid("TEACHER_VISIT_ACCEPTED_GENERATION_DRIFT")
        return
    visit.__post_init__()
    identity = visit.identity
    expected = derive_teacher_visit_identity(
        visit.projection.teacher_state,
        run_identity_sha256=parent.run_identity.digest,
        run_seed=parent.run_identity.run_seed,
        generation=parent.generation,
        accepted_manifest_sha256=cache.accepted_manifest_sha256,
        capability_id=identity.capability_id, policy_key=identity.policy_key)
    if candidate_identity_sha256 is None:
        candidate_identity_sha256 = candidate_identity_digest(parent.retained_state)
    if (identity != expected
            or identity.student_sha256 != candidate_identity_sha256):
        invalid("TEACHER_VISIT_ACCEPTED_GENERATION_DRIFT")


def derive_c03_successor_bundle(
        run_dir: Path, retained_state: CandidateState, visit: BoundTeacherVisit, *,
        next_seed: int, cursor: str, delivery_events: tuple,
        candidate_transaction: CandidateTransaction | None = None) -> BamfBundleCandidate:
    """Build one B13 successor whose C03 teacher state advances atomically.

    C03 owns only the teacher projection. B13 remains the bundle/state-machine
    owner, so this function first uses B13's canonical successor constructor and
    then replaces teacher provenance + sidecar as one validated pair.
    """
    if (type(next_seed) is not int or next_seed < 0
            or not isinstance(cursor, str) or not cursor
            or type(delivery_events) is not tuple):
        invalid("TEACHER_SUCCESSOR_SELECTION_STATE_INVALID")
    parent, cache = _accepted_parent(Path(run_dir))
    _require_current_visit(parent, cache, visit)
    if candidate_transaction is not None and type(candidate_transaction) is not CandidateTransaction:
        invalid("TEACHER_SUCCESSOR_SELECTION_STATE_INVALID")
    if (candidate_transaction is not None
            and candidate_transaction.motif_transition is not None):
        successor = derive_motif_successor_bundle(
            parent, candidate_transaction, retained_state=retained_state,
            parent_manifest_sha256=cache.accepted_manifest_sha256,
            delivery_events=delivery_events)
    else:
        successor = derive_successor_bundle(
            parent, retained_state,
            parent_manifest_sha256=cache.accepted_manifest_sha256,
            delivery_events=delivery_events)
    bank_identity = _bank_identity(successor)
    plasticity_identity = _plasticity_identity(retained_state)
    student_sha = candidate_identity_digest(retained_state)
    student = {
        "schema": _STUDENT_SCHEMA,
        "student_sha256": student_sha,
        "region": _student_region(student_sha, bank_identity, plasticity_identity),
    }
    next_epoch = bind_next_teacher_epoch(
        visit.projection.teacher_state, student,
        bank_identity=bank_identity, plasticity_identity=plasticity_identity)
    advanced = advance_teacher_lineage(
        visit.projection.teacher_state, next_epoch,
        next_seed=next_seed, cursor=cursor)
    successor = replace(
        successor,
        provenance=replace(
            successor.provenance,
            teacher_identity=advanced.teacher_identity,
            teacher_epoch=advanced.teacher_epoch),
        teacher_state=dict(advanced.teacher_state))
    sidecar_records(successor)
    return successor


__all__ = (
    "BoundTeacherVisit",
    "current_teacher_projection", "derive_c03_successor_bundle",
    "rebind_package_import_teacher_custody",
)
