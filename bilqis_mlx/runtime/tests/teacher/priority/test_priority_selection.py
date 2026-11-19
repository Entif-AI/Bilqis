"""Accepted priority selection remains bounded by the lawful frontier."""
from dataclasses import dataclass
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.priority_qualification import _grade as project_grade
from bilqis_mlx.runtime.tests.teacher.priority.test_priority_execution import (
    HParams,
    HeldOffer,
    Offer,
    Visit,
    lawful,
    priority,
)


def test_preselection_hold_never_calls_policy(priority):
    stale = HeldOffer()
    option = SimpleNamespace(stable_id='o', action_kind=3, eligible_since=7,
        downstream_unlocks=2, context=SimpleNamespace(capability_id='cap', scope='scope'))
    frontier = SimpleNamespace(evidence=(('o', 'evidence'),))
    parent = SimpleNamespace(retained_state='student')
    cache = object()
    school = SimpleNamespace(stage='MAIN', current_student=SimpleNamespace(sha256='student-id'))
    qualified = SimpleNamespace(ranked=SimpleNamespace(ordered=(option,)),
                                offers=(('o', stale),), holds=())
    with patch.object(priority, '_accepted_parent', return_value=(parent, cache)), \
         patch.object(priority, '_c03_projection', return_value=SimpleNamespace(teacher_state={})) as base_projection, \
         patch.object(priority, 'current_teacher_projection', side_effect=lambda run, parent, cache, projection: projection) as current_projection, \
         patch.object(priority, 'restore_teacher_lineage', return_value='epoch'), \
         patch.object(priority, 'candidate_identity_digest', return_value='student-id'), \
         patch.object(priority, '_teacher', return_value={'causal_experiment': {'diagnostic_contexts': {'selected': {'salience': 'verified'}}}}), \
         patch.object(priority, 'contract_digest', return_value='epoch-digest'), \
         patch.object(priority, 'salience_priority_features'), \
         patch.object(priority, 'requalify_priority', return_value=qualified), \
         patch.object(priority, 'select_visit_policy') as policy:
        result = priority.select_accepted_priority_visit('/run', SimpleNamespace(release=None), frontier, None, None,
            (('o', qualified.offers[0][1]),), None, school, None, None,
            program=None, now=1, lawful_frontier=lawful())
    assert result.status == 'NO_ADMISSIBLE_TEACHING'
    assert result.holds == (('o', 'SOURCE_OFFER_HELD'),)
    current_projection.assert_called_once_with('/run', parent, cache, base_projection.return_value)
    policy.assert_not_called()


def test_accepted_selection_calls_policy_once(priority):
    @dataclass(frozen=True)
    class Epoch:
        current_json: str
    epoch = Epoch('{}')
    option = SimpleNamespace(stable_id='o', action_kind=3, eligible_since=7,
        downstream_unlocks=2, context=SimpleNamespace(capability_id='cap', scope='scope'))
    frontier = SimpleNamespace(evidence=(('o', 'evidence'),))
    parent = SimpleNamespace(retained_state='student', run_identity=SimpleNamespace(digest='run', run_seed=5), generation=4)
    cache = SimpleNamespace(accepted_manifest_sha256='manifest')
    school = SimpleNamespace(stage='MAIN', current_student=SimpleNamespace(sha256='student-id'))
    qualified = SimpleNamespace(ranked=SimpleNamespace(ordered=(option,), tiers=(('o', 1),)),
                                offers=(('o', Offer()),), holds=())
    identity = SimpleNamespace(to_record=lambda: {'visit': 1})
    with patch.object(priority, '_accepted_parent', return_value=(parent, cache)), \
         patch.object(priority, '_c03_projection', return_value=SimpleNamespace(teacher_state={})) as base_projection, \
         patch.object(priority, 'current_teacher_projection', side_effect=lambda run, parent, cache, projection: projection) as current_projection, \
         patch.object(priority, 'restore_teacher_lineage', return_value=epoch), \
         patch.object(priority, 'candidate_identity_digest', return_value='student-id'), \
         patch.object(priority, '_teacher', return_value={'causal_experiment': {'diagnostic_contexts': {'selected': {'salience': 'verified'}}}}), \
         patch.object(priority, 'contract_digest', return_value='epoch-digest'), \
         patch.object(priority, 'salience_priority_features'), \
         patch.object(priority, 'requalify_priority', return_value=qualified), \
         patch.object(priority, '_grade', return_value='g'), \
         patch.object(priority, 'context_for_selection', return_value={'diagnostic_context_key': 'selected'}) as context, \
         patch.object(priority, 'select_visit_policy', return_value=('k', {'lr': 0.5}, {'diagnostic_context_key': 'selected'})) as policy, \
         patch.object(priority, '_selection_projection', return_value=SimpleNamespace(teacher_state={})), \
         patch.object(priority, 'derive_teacher_visit_identity', return_value=identity), \
         patch.object(priority, 'record_teacher_visit_identity', return_value='recorded'), \
         patch.object(priority, '_issue_bound_visit', return_value=Visit(identity)), \
         patch.object(priority.time, 'perf_counter', side_effect=(10.0, 10.25)):
        result = priority.select_accepted_priority_visit('/run', SimpleNamespace(release=None), frontier, None, None,
            (('o', qualified.offers[0][1]),), None, school, None, None,
            program=None, now=1, lawful_frontier=lawful())
    assert result.status == 'TEACHER_SELECTED'
    assert result.policy == {'lr': 0.5}
    assert result.source_materialization_wall_seconds == 0.25
    assert result.ranking_evidence['dispatch_tier'] == 1
    policy.assert_called_once()
    assert policy.call_args.args[2] == 'cap'
    current_projection.assert_called_once_with('/run', parent, cache, base_projection.return_value)
    assert result.metadata['how_context'] == {'diagnostic_context_key': 'selected'}


@pytest.mark.parametrize('grades', [
    (),
    (SimpleNamespace(id='g1', capabilities=(SimpleNamespace(id='cap'),)),
     SimpleNamespace(id='g2', capabilities=(SimpleNamespace(id='cap'),))),
])
def test_lawful_selection_fails_closed_when_how_grade_projection_is_invalid(priority, grades):
    option = SimpleNamespace(stable_id='o', action_kind=3, eligible_since=7,
        downstream_unlocks=2, context=SimpleNamespace(capability_id='cap', scope='scope'))
    frontier = SimpleNamespace(evidence=(('o', 'evidence'),))
    parent = SimpleNamespace(retained_state='student')
    school = SimpleNamespace(stage='MAIN', current_student=SimpleNamespace(sha256='student-id'))
    program = SimpleNamespace(grades=grades)
    assert project_grade(program, school, 'cap') is None
    offer = Offer()
    qualified = SimpleNamespace(
        ranked=SimpleNamespace(ordered=(option,), tiers=(('o', 1),)),
        offers=(('o', offer),), holds=())
    with patch.object(priority, '_accepted_parent', return_value=(parent, object())), \
         patch.object(priority, '_c03_projection', return_value=SimpleNamespace(teacher_state={})), \
         patch.object(priority, 'current_teacher_projection', side_effect=lambda run, parent, cache, projection: projection), \
         patch.object(priority, 'restore_teacher_lineage', return_value='epoch'), \
         patch.object(priority, 'candidate_identity_digest', return_value='student-id'), \
         patch.object(priority, '_teacher', return_value={}), \
         patch.object(priority, 'contract_digest', return_value='epoch-digest'), \
         patch.object(priority, 'salience_priority_features', return_value={}), \
         patch.object(priority, 'requalify_priority', return_value=qualified), \
         patch.object(priority, '_grade', side_effect=project_grade), \
         patch.object(priority, 'select_visit_policy') as policy:
        with pytest.raises(BilqisError) as failure:
            priority.select_accepted_priority_visit(
                '/run', SimpleNamespace(release=None), frontier, None, None,
                (('o', qualified.offers[0][1]),), None, school, None, None,
                program=program, now=1, lawful_frontier=lawful())
    assert failure.value.context.get('reason') == 'BAMF_PRIORITY_PROGRAM_INVALID'
    policy.assert_not_called()


def test_stale_lawful_frontier_rejects_before_visit_or_source_execution(priority):
    candidate = sys.modules[priority.execute_accepted_priority_candidate.__module__]
    identity = SimpleNamespace(to_record=lambda: {'visit': 1})
    selected = priority._issue_result(
        'TEACHER_SELECTED', 'o', Offer(), Visit(identity),
        {'lr': 0.1}, {}, 'g', (), '/run', lawful())
    frontier_owner = sys.modules['bilqis_mlx.runtime.lawful_teaching_frontier']
    with patch.object(
            frontier_owner, 'require_bound_lawful_teaching_frontier',
            side_effect=ValueError('frontier stale')), patch.object(
                candidate, '_require_current_visit') as require_visit, patch.object(
                candidate, 'execute_factory_candidate_step') as execute:
        with pytest.raises(ValueError, match='frontier stale'):
            priority.execute_accepted_priority_candidate(
                selected, object(), 'a', 'b',
                teacher_hparams=HParams(0.1, (0.9, 0.99), 1e-8, 0),
                observation=object(), optimizer_step_seed=1, max_norm=1)
    require_visit.assert_not_called()
    execute.assert_not_called()


def test_held_capability_cannot_reach_visit_or_candidate_execution(priority):
    candidate = sys.modules[priority.execute_accepted_priority_candidate.__module__]
    identity = SimpleNamespace(to_record=lambda: {'visit': 1})
    held = SimpleNamespace(
        ready_capability_ids=(), exclusions=(),
        _planning_generation=Offer._planning_generation)
    selected = priority._issue_result(
        'TEACHER_SELECTED', 'o', Offer(), Visit(identity),
        {'lr': 0.1}, {}, 'g', (), '/run', held)
    with patch.object(candidate, '_require_current_visit') as require_visit, \
         patch.object(candidate, 'execute_factory_candidate_step') as execute:
        with pytest.raises(BilqisError) as failure:
            priority.execute_accepted_priority_candidate(
                selected, object(), 'a', 'b',
                teacher_hparams=HParams(0.1, (0.9, 0.99), 1e-8, 0),
                observation=object(), optimizer_step_seed=1, max_norm=1)
    assert getattr(failure.value, 'context', {}).get('reason') == (
        'BAMF_PRIORITY_SELECTION_OUTSIDE_LAWFUL_FRONTIER')
    require_visit.assert_not_called()
    execute.assert_not_called()


def test_empty_lawful_frontier_returns_no_admissible_without_teacher_policy(priority):
    planning = SimpleNamespace(parent_candidate_identity_sha256='student-id')
    exclusion = SimpleNamespace(
        capability_id='future',
        code=SimpleNamespace(value='FUTURE_GENERATED_GRADE'))
    empty = SimpleNamespace(
        ready_capability_ids=(), exclusions=(exclusion,),
        _planning_generation=planning)
    school = SimpleNamespace(stage='MAIN', current_student=SimpleNamespace(sha256='student-id'))
    parent = SimpleNamespace(retained_state='student')
    with patch.object(
            priority, '_accepted_parent', return_value=(parent, object())), patch.object(
                priority, 'candidate_identity_digest', return_value='student-id'), patch.object(
                priority, '_c03_projection') as projection, patch.object(
                priority, 'select_visit_policy') as policy:
        result = priority.select_accepted_priority_visit(
            '/run', object(), None, None, None, (), None, school, None, None,
            program=None, now=1, lawful_frontier=empty)
    assert result.status == 'NO_ADMISSIBLE_TEACHING'
    assert result.holds == (('future', 'FUTURE_GENERATED_GRADE'),)
    assert result.exclusions == (exclusion,)
    projection.assert_not_called()
    policy.assert_not_called()
