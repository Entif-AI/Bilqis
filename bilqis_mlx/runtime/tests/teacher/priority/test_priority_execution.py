"""Portable mocked-boundary checks; these do not prove source or MLX execution."""
from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
import pytest

from bilqis_mlx.errors import BilqisError

@dataclass(frozen=True)
class HParams:
    learning_rate: float
    betas: tuple
    eps: float
    weight_decay: float

@dataclass(frozen=True)
class Observation:
    option_rows: tuple
    seed: int


class ScheduleProgramStub:
    def __init__(self, grades):
        self.grades = grades
    def digest(self):
        return 'course'


@dataclass(frozen=True)
class PriorityStudentIdentityStub:
    sha256: str


@dataclass(frozen=True)
class PrioritySchoolContextStub:
    course_digest: str
    active_grades: tuple[str, ...]
    current_student: PriorityStudentIdentityStub
    stage: str = 'MAIN'

def module(**attrs):
    result = ModuleType('stub')
    result.__dict__.update(attrs)
    return result

@pytest.fixture
def priority():
    owners = {
        'bilqis_mlx.factory.teaching': module(describe_delivered_teaching=None),
        'bilqis_mlx.factory.schedule': module(ScheduleProgram=ScheduleProgramStub),
        'bilqis_mlx.learning.atlas_acceptance': module(candidate_identity_digest=None),
        'bilqis_mlx.learning.atlas_salience': module(salience_priority_features=None),
        'bilqis_mlx.learning.salience_contracts': module(ActionKind=SimpleNamespace(CORRECTION=1, PROCEDURE_REPAIR=2)),
        'bilqis_mlx.learning.salience_teacher': module(
            _teacher=None,
            PrioritySchoolContext=PrioritySchoolContextStub,
            PriorityStudentIdentity=PriorityStudentIdentityStub,
        ),
        'bilqis_mlx.learning.learning_experiment': module(Settings=type(None)),
        'bilqis_mlx.learning.teacher_lineage': module(restore_teacher_lineage=None),
        'bilqis_mlx.learning.teacher_visit_identity': module(
            derive_teacher_visit_identity=None,
            record_teacher_visit_authority=lambda projection, identity: projection,
            record_teacher_visit_identity=None,
        ),
        'bilqis_mlx.runtime.atlas_optimizer': module(AdamWHyperparameters=HParams),
        'bilqis_mlx.runtime.atlas_training_contracts': module(BamfVisitProvenance=SimpleNamespace(from_c03_record=None)),
        'bilqis_mlx.runtime.bamf_bundle.currentness_transaction': module(
            refresh_accepted_currentness=lambda transaction, parent: transaction,
            require_live_accepted_currentness_step=(
                lambda step, transaction, parent: step)),
        'bilqis_mlx.runtime.factory_candidate_training': module(execute_factory_candidate_step=None),
        'bilqis_mlx.runtime.lawful_teaching_frontier': module(
            require_bound_lawful_teaching_frontier=(
                lambda frontier, context, parent, **_kwargs: frontier),
            require_current_lawful_teaching_frontier=lambda frontier, context, parent: frontier),
        'bilqis_mlx.runtime.teacher_policy_selection': module(select_visit_policy=None),
        'bilqis_mlx.runtime.outcomes.replay': module(
            replay_rejected_outcomes=lambda run, parent, cache, teacher: teacher),
        'bilqis_mlx.runtime.outcomes.issuance': module(context_for_selection=lambda *args: {}),
        'bilqis_mlx.semantics.domains': module(contract_digest=None),
        'bilqis_mlx.runtime.accepted_teacher_custody': module(_accepted_parent=None, _c03_projection=None,
            _issue_bound_visit=None, _require_current_visit=None, _selection_projection=None,
            current_teacher_projection=lambda run, parent, cache, projection: projection),
        'bilqis_mlx.runtime.priority_qualification': module(_grade=None, requalify_priority=None),
    }
    name = 'bilqis_mlx.runtime.priority_execution_portable_test'
    path = Path(__file__).resolve().parents[3] / '_teacher/priority/accepted_priority_visit.py'
    spec = spec_from_file_location(name, path)
    loaded = module_from_spec(spec)
    with patch.dict(sys.modules, {**owners, name: loaded}):
        spec.loader.exec_module(loaded)
        yield loaded

@dataclass(frozen=True)
class Visit:
    identity: object

class Offer:
    capability_id = 'cap'
    source_seed = 7
    source_each = 1
    _planning_generation = SimpleNamespace(
        _accepted_currentness='currentness',
        _parent='planned-parent',
        _authenticated_features='semantic-context',
        parent_candidate_identity_sha256='planned-id',
    )
    materialized = object()
    def require_current_parent(self, context):
        return 'planned-parent', 'planned-cache'
    def rows(self):
        return ({'id': 'one', 'capability': 'cap'},)
    def require_current(self, context, parent):
        return self.materialized


class HeldOffer(Offer):
    def require_current(self, context, parent):
        raise ValueError('held')


def lawful(*capabilities):
    ready = ('cap',) if not capabilities else tuple(capabilities)
    return SimpleNamespace(
        ready_capability_ids=ready,
        exclusions=(),
        _planning_generation=Offer._planning_generation,
    )


def _candidate_owner(priority):
    return sys.modules[priority.execute_accepted_priority_candidate.__module__]


def _contracts_owner(priority):
    return sys.modules[priority.accepted_priority_school.__module__]

def test_execution_owns_rows_policy_and_teacher_rate(priority):
    candidate = _candidate_owner(priority)
    identity = SimpleNamespace(to_record=lambda: {'visit': 1})
    selected = priority._issue_result('TEACHER_SELECTED', 'o', Offer(), Visit(identity),
        {'lr': 0.25, 'nested': {'x': 1}}, {}, 'g', (), '/run', lawful())
    selected.policy['nested']['x'] = 99
    release = SimpleNamespace(execution_plan=SimpleNamespace(capability_map={
        'cap': SimpleNamespace(teaching_option_ids=('instruction',))}))
    with patch.object(candidate, 'AdamWHyperparameters', HParams), \
         patch.object(candidate, '_require_current_visit'), \
         patch.object(candidate.BamfVisitProvenance, 'from_c03_record', return_value='provenance'), \
         patch.object(candidate, 'describe_delivered_teaching', return_value='delivery'), \
         patch.object(candidate, 'execute_factory_candidate_step', return_value='step') as execute:
        assert priority.execute_accepted_priority_candidate(selected, SimpleNamespace(release=release), 'atlas', 'features',
            teacher_hparams=HParams(0.01, (0.8, 0.9), 1e-8, 0.2), observation=Observation(({'id': 'old'},), 0),
            optimizer_step_seed=3, max_norm=1, capture_diagnostics=True) == 'step'
    args, kw = execute.call_args
    assert args[5] == ({'id': 'one', 'capability': 'cap'},)
    assert kw['teacher_strategy'] == {'lr': 0.25, 'nested': {'x': 1}}
    assert kw['teacher_hparams'] == HParams(0.25, (0.8, 0.9), 1e-8, 0.2)
    assert kw['observation'] == Observation(args[5], 7)
    assert kw['capture_diagnostics'] is True
    assert kw['prepared_source'] is selected.offer.materialized


def test_execution_reuses_authenticated_planning_parent(priority):
    candidate = _candidate_owner(priority)
    identity = SimpleNamespace(to_record=lambda: {'visit': 1})
    selected = priority._issue_result('TEACHER_SELECTED', 'o', Offer(), Visit(identity),
        {'lr': 0.25}, {}, 'g', (), '/run', lawful())
    release = SimpleNamespace(execution_plan=SimpleNamespace(capability_map={
        'cap': SimpleNamespace(teaching_option_ids=('instruction',))}))
    with patch.object(candidate, 'AdamWHyperparameters', HParams), \
         patch.object(candidate, '_require_current_visit') as require_visit, \
         patch.object(candidate.BamfVisitProvenance, 'from_c03_record', return_value='provenance'), \
         patch.object(candidate, 'describe_delivered_teaching', return_value='delivery'), \
         patch.object(candidate, 'execute_factory_candidate_step', return_value='step') as execute:
        assert priority.execute_accepted_priority_candidate(
            selected, SimpleNamespace(release=release), 'atlas', 'features',
            teacher_hparams=HParams(0.01, (0.8, 0.9), 1e-8, 0.2),
            observation=Observation(({'id': 'old'},), 0), optimizer_step_seed=3,
            max_norm=1, candidate_step_started_at=123.0,
            source_prepare_wall_seconds=0.75) == 'step'
    require_visit.assert_called_once_with(
        'planned-parent', 'planned-cache', selected.visit,
        candidate_identity_sha256='planned-id',
        currentness_step='currentness',
        currentness_transaction='currentness')
    assert execute.call_args.args[2] == 'planned-parent'
    assert execute.call_args.kwargs['semantic_context'] == 'semantic-context'
    assert execute.call_args.kwargs['currentness_transaction'] == 'currentness'
    assert execute.call_args.kwargs['currentness_binding_wall_seconds'] >= 0.0
    assert execute.call_args.kwargs['candidate_step_started_at'] == 123.0
    assert execute.call_args.kwargs[
        'upstream_pre_neural_source_compile_wall_seconds'] >= 0.75


def test_final_live_currentness_fence_is_immediately_before_candidate_execution(priority):
    candidate = _candidate_owner(priority)
    currentness_owner = sys.modules[
        'bilqis_mlx.runtime.bamf_bundle.currentness_transaction']
    identity = SimpleNamespace(to_record=lambda: {'visit': 1})
    selected = priority._issue_result('TEACHER_SELECTED', 'o', Offer(), Visit(identity),
        {'lr': 0.25}, {}, 'g', (), '/run', lawful())
    release = SimpleNamespace(execution_plan=SimpleNamespace(capability_map={
        'cap': SimpleNamespace(teaching_option_ids=('instruction',))}))
    events = []

    def fence(step, transaction, parent):
        events.append('fence')
        return step

    def execute(*args, **kwargs):
        events.append('execute')
        return 'step'

    def delivery(*args, **kwargs):
        events.append('delivery')
        return 'delivery'

    with patch.object(candidate, 'AdamWHyperparameters', HParams), \
         patch.object(candidate, '_require_current_visit'), \
         patch.object(candidate.BamfVisitProvenance, 'from_c03_record', return_value='provenance'), \
         patch.object(candidate, 'describe_delivered_teaching', side_effect=delivery), \
         patch.object(currentness_owner, 'require_live_accepted_currentness_step', side_effect=fence), \
         patch.object(candidate, 'execute_factory_candidate_step', side_effect=execute):
        assert priority.execute_accepted_priority_candidate(
            selected, SimpleNamespace(release=release), 'atlas', 'features',
            teacher_hparams=HParams(0.01, (0.8, 0.9), 1e-8, 0.2),
            observation=Observation(({'id': 'old'},), 0), optimizer_step_seed=3,
            max_norm=1) == 'step'

    assert events[-2:] == ['fence', 'execute']


def test_accepted_priority_school_derives_all_admitted_grades_and_student(priority):
    contracts = _contracts_owner(priority)
    program = ScheduleProgramStub(
        (SimpleNamespace(id='violet'), SimpleNamespace(id='amber')))
    parent = SimpleNamespace(retained_state='student')
    with patch.object(contracts, 'candidate_identity_digest', return_value='student-id'), \
         patch.object(contracts, 'PrioritySchoolContext', PrioritySchoolContextStub), \
         patch.object(contracts, 'PriorityStudentIdentity', PriorityStudentIdentityStub):
        school = priority.accepted_priority_school(parent, program)
    assert school.course_digest == 'course'
    assert school.active_grades == ('violet', 'amber')
    assert school.current_student.sha256 == 'student-id'
    assert school.stage == 'MAIN'

def test_issuer_and_rate_are_required(priority):
    candidate = _candidate_owner(priority)
    with pytest.raises(ValueError):
        priority.PriorityVisitResult()
    visit = Visit(SimpleNamespace(to_record=lambda: {'visit': 1}))
    selection = priority._issue_result('TEACHER_SELECTED', 'o', Offer(), visit,
        {'lr': True}, {}, 'g', (), '/run', lawful())
    with patch.object(candidate, '_require_current_visit'):
        with pytest.raises(ValueError):
            priority.execute_accepted_priority_candidate(selection, object(), 'a', 'b',
                teacher_hparams=HParams(0.1, (0.9, 0.99), 1e-8, 0),
                observation=object(), optimizer_step_seed=1, max_norm=1)

def test_stale_offer_rejects_candidate_without_call(priority):
    candidate = _candidate_owner(priority)
    class Stale(Offer):
        def require_current(self, context, parent):
            raise ValueError('C09 hold')
    visit = Visit(SimpleNamespace(to_record=lambda: {'visit': 1}))
    selection = priority._issue_result('TEACHER_SELECTED', 'o', Stale(), visit,
        {'lr': 0.1}, {}, 'g', (), '/run', lawful())
    with patch.object(candidate, '_require_current_visit'), \
         patch.object(candidate, 'execute_factory_candidate_step') as execute:
        with pytest.raises(ValueError, match='C09 hold'):
            priority.execute_accepted_priority_candidate(selection, object(), 'a', 'b',
                teacher_hparams=HParams(0.1, (0.9, 0.99), 1e-8, 0),
                observation=object(), optimizer_step_seed=1, max_norm=1)
        execute.assert_not_called()

def test_non_teaching_result_does_not_execute(priority):
    result = priority._issue_result('ACTION_REQUIRED', 'repair', None, None,
                                    None, None, None, (), '/run')
    assert priority.execute_accepted_priority_candidate(result, None, 'a', 'b',
        teacher_hparams=None, observation=None, optimizer_step_seed=0, max_norm=1) is result
