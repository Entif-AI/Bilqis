"""Fail-closed priority-selection boundaries introduced by the CI refactor."""
from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from types import SimpleNamespace
from unittest.mock import patch

import pytest


def _module(**attrs):
    result = ModuleType("stub")
    result.__dict__.update(attrs)
    return result


@dataclass(frozen=True)
class _PriorityStudentIdentity:
    sha256: str


@dataclass(frozen=True)
class _PrioritySchoolContext:
    course_digest: str
    active_grades: tuple[str, ...]
    current_student: _PriorityStudentIdentity
    stage: str = "MAIN"


@pytest.fixture
def priority():
    owners = {
        "bilqis_mlx.factory.teaching": _module(describe_delivered_teaching=None),
        "bilqis_mlx.factory.schedule": _module(ScheduleProgram=object),
        "bilqis_mlx.learning.atlas_acceptance": _module(candidate_identity_digest=None),
        "bilqis_mlx.learning.atlas_salience": _module(salience_priority_features=None),
        "bilqis_mlx.learning.salience_contracts": _module(
            ActionKind=SimpleNamespace(CORRECTION=1, PROCEDURE_REPAIR=2)),
        "bilqis_mlx.learning.salience_teacher": _module(
            _teacher=None, PrioritySchoolContext=_PrioritySchoolContext,
            PriorityStudentIdentity=_PriorityStudentIdentity),
        "bilqis_mlx.learning.learning_experiment": _module(Settings=type(None)),
        "bilqis_mlx.learning.teacher_lineage": _module(restore_teacher_lineage=None),
        "bilqis_mlx.learning.teacher_visit_identity": _module(
            derive_teacher_visit_identity=None,
            record_teacher_visit_authority=lambda projection, identity: projection,
            record_teacher_visit_identity=None),
        "bilqis_mlx.runtime.atlas_optimizer": _module(AdamWHyperparameters=object),
        "bilqis_mlx.runtime.atlas_training_contracts": _module(
            BamfVisitProvenance=SimpleNamespace(from_c03_record=None)),
        "bilqis_mlx.runtime.bamf_bundle.currentness_transaction": _module(
            refresh_accepted_currentness=lambda transaction, parent: transaction,
            require_live_accepted_currentness_step=(
                lambda step, transaction, parent: step)),
        "bilqis_mlx.runtime.factory_candidate_training": _module(
            execute_factory_candidate_step=None),
        "bilqis_mlx.runtime.lawful_teaching_frontier": _module(
            require_bound_lawful_teaching_frontier=(
                lambda frontier, context, parent, **_kwargs: frontier),
            require_current_lawful_teaching_frontier=lambda frontier, context, parent: frontier),
        "bilqis_mlx.runtime.teacher_policy_selection": _module(select_visit_policy=None),
        "bilqis_mlx.runtime.outcomes.replay": _module(
            replay_rejected_outcomes=lambda run, parent, cache, teacher: teacher),
        "bilqis_mlx.runtime.outcomes.issuance": _module(context_for_selection=lambda *args: {}),
        "bilqis_mlx.semantics.domains": _module(contract_digest=None),
        "bilqis_mlx.runtime.accepted_teacher_custody": _module(
            _accepted_parent=None, _c03_projection=None, _issue_bound_visit=None,
                _require_current_visit=None, _selection_projection=None,
                current_teacher_projection=lambda run, parent, cache, projection: projection),
        "bilqis_mlx.runtime.priority_qualification": _module(
            _grade=None, requalify_priority=None),
    }
    name = "bilqis_mlx.runtime.priority_selection_failure_boundary_test"
    path = Path(__file__).resolve().parents[3] / "_teacher/priority/accepted_priority_visit.py"
    spec = spec_from_file_location(name, path)
    loaded = module_from_spec(spec)
    with patch.dict(sys.modules, {**owners, name: loaded}):
        spec.loader.exec_module(loaded)
        yield loaded


class Offer:
    materialized = object()

    def require_current(self, context, parent):
        return self.materialized


def lawful():
    return SimpleNamespace(
        ready_capability_ids=("cap",),
        exclusions=(),
        _planning_generation=SimpleNamespace(
            parent_candidate_identity_sha256="student-id"))


@dataclass(frozen=True)
class _Epoch:
    current_json: str = "{}"


def _selection_context():
    option = SimpleNamespace(
        stable_id="o", action_kind=3, eligible_since=7, downstream_unlocks=2,
        context=SimpleNamespace(capability_id="cap", scope="scope"))
    frontier = SimpleNamespace(evidence=(("o", "evidence"),))
    parent = SimpleNamespace(
        retained_state="student",
        run_identity=SimpleNamespace(digest="run", run_seed=5),
        generation=4)
    cache = SimpleNamespace(accepted_manifest_sha256="manifest")
    school = SimpleNamespace(
        current_student=SimpleNamespace(sha256="student-id"))
    qualified = SimpleNamespace(
        ranked=SimpleNamespace(ordered=(option,), tiers=(("o", 1),)),
        offers=(("o", Offer()),), holds=())
    return option, frontier, parent, cache, school, qualified


def _base_patches(priority, parent, cache, qualified):
    return (
        patch.object(priority, "_accepted_parent", return_value=(parent, cache)),
        patch.object(
            priority, "_c03_projection",
            return_value=SimpleNamespace(teacher_state={})),
        patch.object(priority, "restore_teacher_lineage", return_value=_Epoch()),
        patch.object(
            priority, "candidate_identity_digest", return_value="student-id"),
        patch.object(priority, "_teacher", return_value={}),
        patch.object(priority, "contract_digest", return_value="epoch-digest"),
        patch.object(priority, "requalify_priority", return_value=qualified),
    )


def test_policy_value_error_is_not_reclassified_as_source_hold(priority):
    _option, frontier, parent, cache, school, qualified = _selection_context()
    patches = _base_patches(priority, parent, cache, qualified)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], \
         patch.object(priority, "salience_priority_features", return_value={}), \
         patch.object(priority, "_grade", return_value="g"), \
         patch.object(
             priority, "select_visit_policy",
             side_effect=ValueError("policy invalid")):
        with pytest.raises(ValueError, match="policy invalid"):
            priority.select_accepted_priority_visit(
                "/run", None, frontier, None, None,
                (("o", qualified.offers[0][1]),),
                None, school, None, None, program=None, now=1,
                lawful_frontier=lawful())


def test_salience_validation_precedes_visit_authority(priority):
    _option, frontier, parent, cache, school, qualified = _selection_context()
    patches = _base_patches(priority, parent, cache, qualified)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], \
         patch.object(
             priority, "salience_priority_features",
             side_effect=ValueError("salience invalid")), \
         patch.object(priority, "record_teacher_visit_authority") as authority:
        with pytest.raises(ValueError, match="salience invalid"):
            priority.select_accepted_priority_visit(
                "/run", None, frontier, None, None,
                (("o", qualified.offers[0][1]),),
                None, school, None, None, program=None, now=1,
                lawful_frontier=lawful())
    authority.assert_not_called()
