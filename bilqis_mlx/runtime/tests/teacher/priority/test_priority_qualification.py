"""Portable qualification orchestration checks with substituted owner boundaries."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as N
from unittest.mock import patch
import pytest

from bilqis_mlx.errors import BilqisError


def mod(**attrs):
    value = ModuleType('stub')
    value.__dict__.update(attrs)
    return value

class Progress(N):
    pass

class Closure(N):
    pass

class Selection(N):
    pass

class Projection(N):
    pass

class Offer:
    source_family_id = 'family'
    source_binding_digest = 'binding'
    release_sha256 = 'release'
    accepted_manifest_sha256 = 'manifest'
    generation_binding = 'generation'
    source_seed = 1
    source_each = 1
    def __init__(self, held=False, capability_id='cap'):
        self.held = held
        self.capability_id = capability_id
        self.source_authority = N(
            capability_id=capability_id, source_family_id='family', seed=1, each=1)
    def require_current(self, context, parent):
        if self.held:
            raise ValueError('held')
    require_qualified_current = require_current

@pytest.fixture
def qualification():
    def rank(options, evidence, snapshot):
        if any(item.stable_id == 'forged' for item in options):
            raise ValueError('signature')
        return N(
            ordered=tuple(sorted(
                options, key=lambda item: item.priority, reverse=True)),
            held=())
    action = N(
        TEACHING='teach', EXPLORATION='explore',
        CORRECTION='correction', PROCEDURE_REPAIR='repair')
    owners = {
        'bilqis_mlx.factory.atlas_frontier_selection': mod(FrontierDeltaSelection=Selection, validate_frontier_selection=lambda *a: None),
        'bilqis_mlx.factory.atlas_frontier_selection_validation': mod(TargetDeltaProjection=Projection, validate_closure_structure=lambda *a: None),
        'bilqis_mlx.factory.atlas_frontier_progress_contracts': mod(FrontierProgress=Progress),
        'bilqis_mlx.factory.atlas_frontier_closure': mod(FrontierClosure=Closure),
        'bilqis_mlx.learning.atlas_salience': mod(rank_attention_options=rank, verify_salience_inputs=lambda facts, policy, snapshot, context: facts, derive_salience=lambda evidence: evidence),
        'bilqis_mlx.learning.salience_contracts': mod(ActionKind=action),
        'bilqis_mlx.learning.salience_history': mod(completed_windows=lambda h: None),
        'bilqis_mlx.runtime.bamf_bundle.accepted_runtime': mod(_accepted_correction_registry=lambda r: (N(generation_binding='generation', accepted_manifest_sha256='manifest'), N(digest='registry'))),
        'bilqis_mlx.runtime.lawful_teaching_frontier': mod(
            require_bound_lawful_teaching_frontier=lambda frontier, context, parent: frontier,
            require_current_lawful_teaching_frontier=lambda frontier, context, parent: frontier),
        'bilqis_mlx.semantics.domains': mod(contract_digest=lambda v: 'binding' if v == 'source-binding' else 'epoch'),
        'bilqis_mlx.runtime.priority_source_offer': mod(PreparedPrioritySourceOffer=Offer),
    }
    name = 'bilqis_mlx.runtime.priority_qualification_portable_test'
    spec = spec_from_file_location(name, Path(__file__).resolve().parents[3] / '_teacher/priority_qualification.py')
    loaded = module_from_spec(spec)
    with patch.dict(sys.modules, {**owners, name: loaded}):
        spec.loader.exec_module(loaded)
        loaded.contract_digest = lambda value: 'binding' if value == 'source-binding' else 'epoch'
        yield loaded


def inputs(q, options, offers):
    snapshot = N(snapshot_sha256='snapshot', admitted_factory_release_sha256='release')
    progress = Progress(
        verify=lambda: None, input_snapshot=snapshot,
        input_snapshot_sha256='snapshot', proposal_selection_sha256=None)
    closure = Closure(verify=lambda: None, snapshot_sha256='snapshot')
    planning = q.PriorityPlanningInput(progress, closure, None, None)
    capability_ids = {option.context.capability_id for option in options}
    release = N(
        release_sha256='release',
        execution_plan=N(capability_map={item: 1 for item in capability_ids}),
        curriculum=N(capability_map={item: 1 for item in capability_ids}),
        source_bindings=N(by_capability={
            item: 'source-binding' for item in capability_ids}),
    )
    source = N(release=release, require_accepted_runtime=lambda run: None)
    program = N(digest=lambda: 'course', grades=(N(
        id='grade', capabilities=tuple(N(id=item) for item in sorted(capability_ids))),))
    school = N(course_digest='course', active_grades=('grade',))
    evidence = []
    for o in options:
        item = N()
        item.basis = N(facts=item, policy=None, context=o.context)
        evidence.append((o.stable_id, item))
    frontier = N(snapshot=N(registry=N(digest='registry'), as_of=10), options=options,
                 evidence=tuple(evidence))
    return ('/run', source, object(), frontier, object(), planning, offers, program, school, object())


def option(name, unlocks=0, *, action_kind='teach', capability_id='cap', priority=0):
    return N(stable_id=name, action_kind=action_kind, downstream_unlocks=unlocks,
             priority=priority,
             context=N(capability_id=capability_id, semantic_release='release', generation_digest='generation',
                       teacher_epoch_digest='epoch', source_binding_digest='binding', source_family_id='family'))


def lawful(*capabilities, exclusions=()):
    ready = ('cap',) if not capabilities else tuple(capabilities)
    return N(
        ready_capability_ids=ready, exclusions=tuple(exclusions),
        _planning_generation=None)


def exclusion(capability='cap', code='FUTURE_GENERATED_GRADE'):
    return N(capability_id=capability, code=N(value=code))


def test_hold_only_affected_offer_and_retain_lower_priority(qualification):
    args = inputs(qualification, (option('high'), option('low')), (('high', Offer(True)), ('low', Offer())))
    result = qualification.requalify_priority(
        *args, now=10, lawful_frontier=lawful())
    assert [o.stable_id for o in result.ranked.ordered] == ['low']
    assert result.holds == (('high', 'SOURCE_OFFER_HELD'),)


def test_forged_filtered_option_fails_before_missing_offer_hold(qualification):
    args = inputs(qualification, (option('forged'),), ())
    with pytest.raises(ValueError, match='signature'):
        qualification.requalify_priority(
            *args, now=10, lawful_frontier=lawful())


def test_nonzero_unlock_without_selection_is_held(qualification):
    args = inputs(qualification, (option('one', 3),), (('one', Offer()),))
    with patch.object(qualification.candidate_realizations, 'realized_atlas_semantic_id', return_value='semantic'):
        result = qualification.requalify_priority(
            *args, now=10, lawful_frontier=lawful())
    assert result.holds == (('one', 'A09_PLANNING_UNAVAILABLE'),)


def test_planner_is_required_even_when_no_option_claims_an_unlock(qualification):
    args = list(inputs(qualification, (option('one'),), (('one', Offer()),)))
    args[5] = None
    with pytest.raises(BilqisError) as failure:
        qualification.requalify_priority(
            *args, now=10, lawful_frontier=lawful())
    assert failure.value.context['reason'] == 'BAMF_PRIORITY_PLANNING_INVALID'
    assert failure.value.code == 'SCHOOL.BAMF_CURRICULUM.INVALID'

def test_grade_projection_is_descriptive_not_an_eligibility_gate(qualification):
    program = N(grades=(N(id='renamed', capabilities=(N(id='cap'),)),))
    assert qualification._grade(program, N(active_grades=('renamed',)), 'cap') == 'renamed'
    assert qualification._grade(program, N(active_grades=('old',)), 'cap') == 'renamed'
    assert qualification._grade(program, N(active_grades=()), 'cap') == 'renamed'

def test_matching_selection_unlocks_and_unadmitted_capability(qualification):
    selected = Selection(selected_semantic_id='semantic', downstream_unlocks=3,
                         selection_sha256='selection')
    item = option('one', 3)
    args = list(inputs(qualification, (item,), (('one', Offer()),)))
    args[5].progress.proposal_selection_sha256 = 'selection'
    args[5] = qualification.PriorityPlanningInput(args[5].progress, args[5].closure, selected, Projection())
    with patch.object(qualification.candidate_realizations, 'realized_atlas_semantic_id', return_value='semantic'):
        assert qualification.requalify_priority(
            *args, now=10, lawful_frontier=lawful()).ranked.ordered == (item,)
        args[8].active_grades = ()
        result = qualification.requalify_priority(
            *args, now=10, lawful_frontier=lawful())
    assert result.ranked.ordered == (item,)
    assert result.holds == ()


def test_priority_visit_reports_planning_verification_metrics(qualification):
    args = inputs(qualification, (option('one'),), (('one', Offer()),))
    observed = []
    qualification.requalify_priority(
        *args, now=10, lawful_frontier=lawful(),
        planning_observer=observed.append)
    assert len(observed) == 1
    assert observed[0].snapshots_rehashed == 0
    assert observed[0].historical_bytes_serialized == 0
    assert observed[0].receipt_history_lookups == 0


@pytest.mark.parametrize(('missing', 'expected'), [
    ('execution', 'CAPABILITY_NOT_ADMITTED'),
    ('curriculum', 'CAPABILITY_NOT_ADMITTED'),
    ('binding', 'SOURCE_OFFER_HELD'),
    ('offer', 'SOURCE_OFFER_MISSING'),
])
def test_hold_precedence_before_missing_offer(qualification, missing, expected):
    args = list(inputs(qualification, (option('one'),), ()))
    release = args[1].release
    if missing == 'execution':
        release.execution_plan.capability_map.clear()
        release.source_bindings.by_capability.clear()
    elif missing == 'curriculum':
        release.curriculum.capability_map.clear()
    elif missing == 'binding':
        release.source_bindings.by_capability.clear()
    result = qualification.requalify_priority(
        *args, now=10, lawful_frontier=lawful())
    assert result.holds == (('one', expected),)


@pytest.mark.parametrize('grades', [(), (N(id='a', capabilities=(N(id='cap'),)),) * 2])
def test_schedule_grade_does_not_decide_what_is_lawful(qualification, grades):
    args = list(inputs(
        qualification, (option('one'),), (('one', Offer()),)))
    args[7].grades = grades
    result = qualification.requalify_priority(
        *args, now=10, lawful_frontier=lawful())
    assert result.ranked.ordered == (args[3].options[0],)
    assert result.holds == ()


def test_salience_cannot_revive_option_held_by_lawful_frontier(qualification):
    args = inputs(qualification, (option('one'),), ())
    held = lawful('other', exclusions=(exclusion(),))
    result = qualification.requalify_priority(
        *args, now=10, lawful_frontier=held)
    assert result.ranked.ordered == ()
    assert result.holds == (('one', 'FUTURE_GENERATED_GRADE'),)


def test_higher_priority_future_grade_never_reaches_ranking(qualification):
    future = option('future', capability_id='future', priority=100)
    active = option('active', capability_id='active', priority=1)
    args = inputs(
        qualification, (future, active),
        (('active', Offer(capability_id='active')),),
    )
    result = qualification.requalify_priority(
        *args, now=10,
        lawful_frontier=lawful(
            'active', exclusions=(exclusion('future'),)))
    assert result.ranked.ordered == (active,)
    assert result.holds == (('future', 'FUTURE_GENERATED_GRADE'),)


def test_priority_still_orders_two_lawful_same_frontier_peers(qualification):
    low = option('low', capability_id='low', priority=1)
    high = option('high', capability_id='high', priority=100)
    args = inputs(
        qualification, (low, high),
        (
            ('low', Offer(capability_id='low')),
            ('high', Offer(capability_id='high')),
        ),
    )
    result = qualification.requalify_priority(
        *args, now=10, lawful_frontier=lawful('low', 'high'))
    assert result.ranked.ordered == (high, low)
    assert result.holds == ()


def test_out_of_grade_remediation_is_held_before_ranking(qualification):
    args = inputs(
        qualification, (option('repair', action_kind='repair'),), ())
    held = lawful('other', exclusions=(exclusion(),))
    result = qualification.requalify_priority(
        *args, now=10, lawful_frontier=held)
    assert result.ranked.ordered == ()
    assert result.holds == (('repair', 'FUTURE_GENERATED_GRADE'),)


def test_in_grade_remediation_remains_rankable_without_source_offer(qualification):
    item = option('repair', action_kind='repair')
    args = inputs(qualification, (item,), ())
    result = qualification.requalify_priority(
        *args, now=10, lawful_frontier=lawful())
    assert result.ranked.ordered == (item,)
    assert result.holds == ()


def test_offer_enumeration_outside_lawful_frontier_fails_closed(qualification):
    args = inputs(qualification, (option('one'),), (('one', Offer()),))
    held = lawful('other', exclusions=(exclusion(),))
    with pytest.raises(BilqisError) as failure:
        qualification.requalify_priority(
            *args, now=10, lawful_frontier=held)
    assert failure.value.context['reason'] == 'BAMF_PRIORITY_OFFERS_INVALID'
