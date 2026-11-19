"""Accepted-generation teacher-state identity and bootstrap helpers."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_candidate import CandidateState
from bilqis_mlx.learning.teacher_lineage import (
    TeacherCustodyProjection, advance_teacher_lineage, bind_next_teacher_epoch,
    initialize_teacher_lineage, restore_teacher_lineage,
)
from bilqis_mlx.learning._teaching.teacher_lineage_records import invalid
from bilqis_mlx.runtime.bamf_bundle import CompleteStudent
from bilqis_mlx.runtime.bamf_bundle.factory_release_adoption import (
    is_factory_release_adoption_transition,
    validate_factory_release_adoption_transition,
)
from bilqis_mlx.runtime.bamf_bundle.package_import_transition import (
    is_package_import_transition, validate_package_import_transition,
)
from bilqis_mlx.runtime.bamf_bundle.records import validate_transition
from bilqis_mlx.semantics.domains import contract_digest

_STUDENT_SCHEMA = "bilqis.bamf.student-reference/v1"


def _bank_identity(student: CompleteStudent) -> str:
    banks = student.semantic_abi.get("bank_identities")
    if not isinstance(banks, (tuple, list)) or not banks:
        invalid("TEACHER_STUDENT_BANK_IDENTITY_INVALID")
    return contract_digest(("bilqis.bamf.c03-bank-identity/v1", tuple(banks)))


def _plasticity_identity(state: CandidateState) -> str:
    if type(state) is not CandidateState:
        invalid("TEACHER_STUDENT_PLASTICITY_IDENTITY_INVALID")
    return contract_digest(("bilqis.bamf.c03-plasticity-identity/v1",
                            state.policy.to_record()))


def _student_region(student_sha256: str, bank_identity: str,
                    plasticity_identity: str) -> str:
    binding = {
        "student_sha256": student_sha256,
        "bank_identity": bank_identity,
        "plasticity_identity": plasticity_identity,
    }
    return hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()


def _student_reference(student: CompleteStudent, state: CandidateState | None = None) -> dict:
    retained = student.retained_state if state is None else state
    student_sha = candidate_identity_digest(retained)
    bank_identity = _bank_identity(student)
    plasticity_identity = _plasticity_identity(retained)
    return {
        "schema": _STUDENT_SCHEMA,
        "student_sha256": student_sha,
        "region": _student_region(student_sha, bank_identity, plasticity_identity),
    }


def _prebootstrap_transition_eligible(parent: CompleteStudent, state: Mapping) -> bool:
    if (parent.generation <= 0
            or parent.retained_state.optimizer_step != 0
            or state.get("teacher_identity") != parent.provenance.teacher_identity
            or state.get("teacher_epoch") != parent.provenance.teacher_epoch):
        return False
    transition = parent.transition
    if is_package_import_transition(transition):
        validate_package_import_transition(transition)
        return True
    if is_factory_release_adoption_transition(transition):
        validate_factory_release_adoption_transition(transition)
        return True
    if (isinstance(transition, Mapping)
            and transition.get("kind") == "PARAMETER_EXTENSION"):
        validate_transition(parent.generation, transition)
        return True
    return False


def _require_current_c03_lineage(parent: CompleteStudent, state: Mapping):
    epoch = restore_teacher_lineage(state)
    student = _student_reference(parent)
    if (epoch.student_sha256 != student["student_sha256"]
            or state.get("teacher_identity") != parent.provenance.teacher_identity
            or state.get("teacher_epoch") != parent.provenance.teacher_epoch):
        invalid("TEACHER_ACCEPTED_GENERATION_DRIFT")
    return epoch


def _c03_projection(parent: CompleteStudent, *, legacy_receipt, adaptation,
                    prior_region) -> TeacherCustodyProjection:
    state = dict(parent.teacher_state)
    student = _student_reference(parent)
    if "c03_lineage" in state:
        if any(value is not None for value in (legacy_receipt, adaptation, prior_region)):
            invalid("TEACHER_BOOTSTRAP_ALREADY_COMPLETE")
        _require_current_c03_lineage(parent, state)
        return TeacherCustodyProjection(
            state, state["teacher_identity"], state["teacher_epoch"])
    can_bootstrap = (
        parent.generation == 0 or _prebootstrap_transition_eligible(parent, state))
    if (not can_bootstrap or not isinstance(legacy_receipt, Mapping)
            or not isinstance(adaptation, Mapping)
            or not isinstance(prior_region, str) or not prior_region):
        invalid("TEACHER_BOOTSTRAP_REQUIRED")
    return initialize_teacher_lineage(
        legacy_receipt, student, adaptation, prior_region=prior_region,
        next_seed=state["next_seed"], cursor=state["cursor"])


def rebind_package_import_teacher_custody(
        parent: CompleteStudent, retained_state: CandidateState,
) -> TeacherCustodyProjection | None:
    """Rebind mature recipient teacher custody after an accepted package import."""
    if type(parent) is not CompleteStudent or type(retained_state) is not CandidateState:
        invalid("TEACHER_STUDENT_BINDING_INVALID")
    state = dict(parent.teacher_state)
    if "c03_lineage" not in state:
        return None
    _require_current_c03_lineage(parent, state)
    student = _student_reference(parent, retained_state)
    next_epoch = bind_next_teacher_epoch(
        state, student, bank_identity=_bank_identity(parent),
        plasticity_identity=_plasticity_identity(retained_state))
    return advance_teacher_lineage(
        state, next_epoch, next_seed=state["next_seed"], cursor=state["cursor"])


__all__ = (
    "_bank_identity", "_c03_projection", "_plasticity_identity",
    "rebind_package_import_teacher_custody",
)
