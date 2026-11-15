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
    capability_id = 'cap'
    source_family_id = 'family'
    source_binding_digest = 'binding'
    release_sha256 = 'release'
    accepted_manifest_sha256 = 'manifest'
    generation_binding = 'generation'
    source_seed = 1
    source_each = 1
    source_authority = N(capability_id='cap', source_family_id='family', seed=1, each=1)
    def __init__(self, held=False):
        self.held = held
    def require_current(self, context, parent):
        if self.held:
            raise ValueError('held')

@pytest.fixture
def qualification():
    def rank(options, evidence, snapshot):
        if any(item.stable_id == 'forged' for item in options):
            raise ValueError('signature')
        return N(ordered=options, held=())
    action = N(TEACHING='teach', EXPLORATION='explore')
    owners = {
        'bilqis_mlx.factory.atlas_frontier_selection': mod(FrontierDeltaSelection=Selection, validate_frontier_selection=lambda *a: None),
        'bilqis_mlx.factory.atlas_frontier_selection_validation': mod(TargetDeltaProjection=Projection, validate_closure_structure=lambda *a: None),
        'bilqis_mlx.factory.atlas_frontier_progress_contracts': mod(FrontierProgress=Progress),
        'bilqis_mlx.factory.atlas_frontier_closure': mod(FrontierClosure=Closure),
        'bilqis_mlx.learning.atlas_salience': mod(rank_attention_options=rank, verify_salience_inputs=lambda facts, policy, snapshot, context: facts, derive_salience=lambda evidence: evidence),
        'bilqis_mlx.learning.salience_contracts': mod(ActionKind=action),
        'bilqis_mlx.learning.salience_history': mod(completed_windows=lambda h: None),
        'bilqis_mlx.runtime.bamf_bundle.accepted_runtime': mod(_accepted_correction_registry=lambda r: (N(generation_binding='generation', accepted_manifest_sha256='manifest'), N(digest='registry'))),
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
    release = N(release_sha256='release', execution_plan=N(capability_map={'cap': 1}),
                curriculum=N(capability_map={'cap': 1}), source_bindings=N(by_capability={'cap': 'source-binding'}))
    source = N(release=release, require_accepted_runtime=lambda run: None)
    program = N(digest=lambda: 'course', grades=(N(id='grade', capabilities=(N(id='cap'),)),))
    school = N(course_digest='course', active_grades=('grade',))
    evidence = []
    for o in options:
        item = N()
        item.basis = N(facts=item, policy=None, context=o.context)
        evidence.append((o.stable_id, item))
    frontier = N(snapshot=N(registry=N(digest='registry'), as_of=10), options=options,
                 evidence=tuple(evidence))
    return ('/run', source, object(), frontier, object(), planning, offers, program, school, object())


def option(name, unlocks=0):
    return N(stable_id=name, action_kind='teach', downstream_unlocks=unlocks,
             context=N(capability_id='cap', semantic_release='release', generation_digest='generation',
                       teacher_epoch_digest='epoch', source_binding_digest='binding', source_family_id='family'))


def test_hold_only_affected_offer_and_retain_lower_priority(qualification):
    args = inputs(qualification, (option('high'), option('low')), (('high', Offer(True)), ('low', Offer())))
    result = qualification.requalify_priority(*args, now=10)
    assert [o.stable_id for o in result.ranked.ordered] == ['low']
    assert result.holds == (('high', 'SOURCE_OFFER_HELD'),)


def test_forged_filtered_option_fails_before_missing_offer_hold(qualification):
    args = inputs(qualification, (option('forged'),), ())
    with pytest.raises(ValueError, match='signature'):
        qualification.requalify_priority(*args, now=10)


def test_nonzero_unlock_without_selection_is_held(qualification):
    args = inputs(qualification, (option('one', 3),), (('one', Offer()),))
    with patch.object(qualification.candidate_realizations, 'realized_atlas_semantic_id', return_value='semantic'):
        result = qualification.requalify_priority(*args, now=10)
    assert result.holds == (('one', 'A09_PLANNING_UNAVAILABLE'),)


def test_planner_is_required_even_when_no_option_claims_an_unlock(qualification):
    args = list(inputs(qualification, (option('one'),), (('one', Offer()),)))
    args[5] = None
    with pytest.raises(BilqisError) as failure:
        qualification.requalify_priority(*args, now=10)
    assert failure.value.context['reason'] == 'BAMF_PRIORITY_PLANNING_INVALID'

def test_grade_renaming_keeps_capability_admission(qualification):
    program = N(grades=(N(id='renamed', capabilities=(N(id='cap'),)),))
    assert qualification._grade(program, N(active_grades=('renamed',)), 'cap') == 'renamed'
    assert qualification._grade(program, N(active_grades=('old',)), 'cap') is None

def test_matching_selection_unlocks_and_unadmitted_capability(qualification):
    selected = Selection(selected_semantic_id='semantic', downstream_unlocks=3,
                         selection_sha256='selection')
    item = option('one', 3)
    args = list(inputs(qualification, (item,), (('one', Offer()),)))
    args[5].progress.proposal_selection_sha256 = 'selection'
    args[5] = qualification.PriorityPlanningInput(args[5].progress, args[5].closure, selected, Projection())
    with patch.object(qualification.candidate_realizations, 'realized_atlas_semantic_id', return_value='semantic'):
        assert qualification.requalify_priority(*args, now=10).ranked.ordered == (item,)
        args[8].active_grades = ()
        result = qualification.requalify_priority(*args, now=10)
    assert result.holds == (('one', 'CAPABILITY_NOT_ADMITTED'),)


def test_priority_visit_reports_planning_verification_metrics(qualification):
    args = inputs(qualification, (option('one'),), (('one', Offer()),))
    observed = []
    qualification.requalify_priority(
        *args, now=10, planning_observer=observed.append)
    assert len(observed) == 1
    assert observed[0].snapshots_rehashed == 0
    assert observed[0].historical_bytes_serialized == 0
    assert observed[0].receipt_history_lookups == 0
