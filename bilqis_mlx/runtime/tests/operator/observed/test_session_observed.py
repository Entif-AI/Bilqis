from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from bilqis_mlx.runtime.bamf_operator.session import _visit


def _first_baseline_operator_case():
    from bilqis_mlx.runtime.tests.capability.factory.owner.test_factory_retention_owner_adversarial import (
        _evaluate_foundation_owner,
        _foundation_owner_fixture,
    )
    from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
        accepted_state,
        candidate,
        parent_state,
    )

    evaluation = _evaluate_foundation_owner(*_foundation_owner_fixture())
    identity = evaluation.baseline_transition.measurement.comparison
    fixture_parent_state = parent_state()
    fixture_candidate_state = accepted_state(fixture_parent_state)
    object.__setattr__(evaluation, "parent_state", fixture_parent_state)
    object.__setattr__(evaluation, "candidate_state", fixture_candidate_state)
    successor = candidate(
        fixture_candidate_state,
        generation=1,
        parent="0" * 64,
    )
    parent = NS(
        generation=0,
        retained_state=NS(optimizer_step=0),
        optimizer_hyperparameters=None,
    )
    selection = NS(
        option_id="fixture-option",
        visit=NS(identity=NS(visit_id="fixture-visit", policy_key="fixture-policy")),
    )
    step = NS(transaction=NS(training_authorities=()))
    capture = NS(finalize=lambda **_kwargs: {
        "schema": "bilqis.bamf.c16.3-candidate-evidence-reference/v1",
        "persistence": {
            "bytes_written": 0,
            "file_fsyncs": 0,
            "directory_fsyncs": 0,
            "evidence_objects": 0,
            "persistence_seconds": 0.0,
        },
    })
    cache = NS(generation=0, accepted_manifest_sha256="0" * 64)
    return evaluation, identity, successor, parent, selection, step, capture, cache


def _operate_first_baseline_case(case):
    from contextlib import ExitStack
    from tempfile import TemporaryDirectory
    from bilqis_mlx.runtime.bamf_operator.session import _retention_result, operate_bamf

    evaluation, identity, successor, parent, selection, step, capture, cache = case
    published = []

    def prepare(run_dir, *, observer=None, **_kwargs):
        if observer is not None:
            observer.bind_parent(parent)
        return _retention_result(
            run_dir, parent, NS(), "artifact", selection, identity.capability_id,
            cache, (step,), capture, 1, 1, {}, None, observer)

    def publish(_run_dir, bound_successor, *_args, **_kwargs):
        published.append(bound_successor)

    prefix = "bilqis_mlx.runtime.bamf_operator.session."
    patches = (
        (prefix + "prepare_bamf_visit", {"side_effect": prepare}),
        (prefix + "evaluate_factory_retention_candidate", {"return_value": evaluation}),
        (prefix + "derive_accepted_teacher_successor", {"return_value": successor}),
        (prefix + "_resource_observation", {"return_value": {}}),
        (prefix + "candidate_identity_metrics_delta", {"return_value": {}}),
        ("bilqis_mlx.runtime.retention.screen.candidate_identity_for_canonical_consumer",
         {"return_value": "d" * 64}),
        (prefix + "accept_and_publish", {"side_effect": publish}),
        (prefix + "load_accepted_generation", {"return_value": NS(
            generation=1, retained_state=NS(optimizer_step=1))}),
    )
    with TemporaryDirectory() as tmp, ExitStack() as stack:
        for target, kwargs in patches:
            stack.enter_context(patch(target, **kwargs))
        result = operate_bamf(
            Path(tmp), minutes=1, max_visits=1, reserve_gib=0,
            source_prefetch_workers=0)
    return result, published


class SessionObservationTests(unittest.TestCase):
    def test_publication_before_accepted_and_failure_propagates(self):
        events = []
        observer = NS(update=lambda **v: events.append(v))
        decision = NS(accepted=True)
        prepared = NS(status='ACCEPTED', parent=object(), selection=object(),
                      step=NS(transaction=NS(training_authorities=())), decision=decision,
                      retained=object(), capability='cap', successor=NS(extents=NS(factor_map_digest='x')))
        with patch('bilqis_mlx.runtime.bamf_operator.session.prepare_bamf_visit', return_value=prepared), patch(
                'bilqis_mlx.runtime.bamf_operator.session.accept_and_publish', side_effect=RuntimeError('publish')):
            with self.assertRaises(RuntimeError):
                _visit(Path('/tmp'), 0, observer=observer)
        self.assertEqual(events[0], {'phase': 'PUBLISHING'})
        self.assertGreaterEqual(events[1]['publishing_wall_seconds'], 0.0)

    def test_preparation_emits_observed_training_and_retention(self):
        from bilqis_mlx.runtime.bamf_operator.session import prepare_bamf_visit
        events = []
        observer = NS(bind_parent=lambda parent: events.append({'bound': parent}),
                      update=lambda **fields: events.append(fields))
        parent = NS(retained_state=NS(optimizer_step=4), optimizer_hyperparameters='hp')
        selection = NS(status='TEACHER_SELECTED', offer=NS(
            capability_id='cap', source_seed=1, rows=lambda: ({'id': 'row'},),
            _planning_generation=NS(_accepted_currentness='currentness')),
            visit=NS(identity=NS(visit_id='visit')))
        steps = [NS(
            transaction=NS(parent=NS(optimizer_step=4), update_steps=i),
            realized_cost={
                'wall_seconds': 1.0, 'optimizer_steps': 1,
                'candidate_optimizer_steps': i, 'c08_memory_budget_bytes': 1,
            }) for i in (1, 2, 3)]
        def assess(*args, observer, **kwargs):
            observer({'retention_completed': 1, 'retention_total': 2,
                      'retention_subject': 'cap', 'retention_role': 'parent'})
            return NS(candidate_state=object(), parent_state=parent.retained_state)
        prefix = 'bilqis_mlx.runtime.bamf_operator.session.'
        patches = {
            '_execution_context': (parent, NS(release='release'), 'atlas', 'feature'),
            'schedule_program_from_executable_release': 'program',
            'accepted_priority_school': 'school', 'select_foundation_priority_visit': selection,
            '_Capture': NS(finalize=lambda **_kwargs: {
                'schema': 'bilqis.bamf.c16.3-candidate-evidence-reference/v1',
                'persistence': {'bytes_written': 1, 'file_fsyncs': 1,
                                'directory_fsyncs': 1, 'evidence_objects': 1,
                                'persistence_seconds': 0.0}}),
            'FactoryDeliveryObservation': 'delivery',
            'bind_accepted_execution_cache': NS(
                generation=1, accepted_manifest_sha256='a' * 64),
            'candidate_step_horizon': 3,
            'rejection_attempt_ordinals': (1, 1),
            'prepare_candidate_evidence_root': Path('/tmp/teacher-observations/objects'),
            'currentness_metrics': {
                'deep_authentication_count': 1,
                'accepted_cache_currentness_count': 3,
                'full_candidate_identity_hashes': 1,
                'bundle_tree_scans': 2,
            },
            'issue_factory_retention_decision': NS(
                accepted=False,
                reason='PROTECTED_CAPABILITY_REGRESSION',
                evaluated_capability_ids=('cap', 'protected-cap'),
                retention_protection_plan_sha256='f' * 64,
                broad_certification_trigger=None,
                to_record=lambda: {'decision': 'REJECTED'}),
        }
        from contextlib import ExitStack
        with ExitStack() as stack:
            for name, value in patches.items():
                stack.enter_context(patch(prefix + name, return_value=value))
            stack.enter_context(patch(prefix + 'execute_accepted_priority_candidate', side_effect=steps))
            stack.enter_context(patch(prefix + 'evaluate_factory_retention_candidate', side_effect=assess))
            stack.enter_context(patch(
                'bilqis_mlx.runtime.bamf_operator.evidence_projection.complete_visit_evidence',
                side_effect=RuntimeError('observation readback failed')))
            result = prepare_bamf_visit(Path('/tmp'), observer=observer)
        self.assertEqual(result.status, 'REJECTED')
        self.assertEqual([e.get('phase') for e in events if 'phase' in e],
                         ['SELECTING', 'TRAINING', 'RETENTION'])
        self.assertIn({'phase': 'TRAINING', 'capability_id': 'cap', 'candidate_step': 0,
                       'candidate_horizon': 3, 'candidate_optimizer_step': 4}, events)
        for i in (1, 2, 3):
            self.assertIn({'candidate_step': i, 'candidate_optimizer_step': 4 + i}, events)
        self.assertIn({'retention_completed': 1, 'retention_total': 2,
                       'retention_subject': 'cap', 'retention_role': 'parent'}, events)
        self.assertIn({
            'retention_evaluated_capability_count': 2,
            'retention_protection_plan_sha256': 'f' * 64,
            'retention_broad_certification_trigger': None,
        }, events)

    def test_operator_publishes_terminal_only_after_publication(self):
        import json
        from tempfile import TemporaryDirectory
        from bilqis_mlx.runtime.bamf_bundle.publication.instrumentation import PublicationMetrics
        from bilqis_mlx.runtime.bamf_operator.session import operate_bamf
        with TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / 'bamf-state.json').write_text(json.dumps({'run_id': 'run', 'manifest_sha256': 'a' * 64}))
            prepared = NS(status='ACCEPTED', parent=object(), selection=object(),
                          step=NS(transaction=NS(training_authorities=())), decision=NS(accepted=True),
                          retained=object(), capability='cap', successor=NS(extents=NS(factor_map_digest='x')))
            snapshots = []
            def publish(*args, **kwargs):
                snapshots.append(json.loads((path / 'trainer-observed.json').read_text())['visits'][-1])
                kwargs['publication_observer'](PublicationMetrics(1, 2, 3, 4, 5))
            prefix = 'bilqis_mlx.runtime.bamf_operator.session.'
            with patch(prefix + 'prepare_bamf_visit', return_value=prepared), patch(
                    prefix + 'accept_and_publish', side_effect=publish), patch(
                    prefix + 'load_accepted_generation', return_value=NS(generation=1, retained_state=NS(optimizer_step=1))):
                operate_bamf(path, minutes=1, max_visits=1, reserve_gib=0)
            final = json.loads((path / 'trainer-observed.json').read_text())['visits'][-1]
            self.assertEqual((snapshots[0]['phase'], snapshots[0]['outcome']), ('PUBLISHING', 'RUNNING'))
            self.assertEqual((final['phase'], final['outcome']), ('COMPLETED', 'ACCEPTED'))
            self.assertEqual(final['publication_parent_bundle_loads'], 1)
            self.assertEqual(final['publication_child_bundle_loads'], 2)
            self.assertEqual(final['publication_tensor_bytes_read'], 3)
            self.assertEqual(final['publication_write_bytes'], 4)
            self.assertEqual(final['publication_fsync_bytes'], 5)

    def test_operate_bamf_carries_first_accepted_baseline_to_publication(self):
        from bilqis_mlx.runtime.baseline.lifecycle import (
            BaselineLedger,
            BaselineLifecycleState,
        )

        case = _first_baseline_operator_case()
        evaluation, identity = case[:2]
        identity = evaluation.baseline_transition.measurement.comparison
        self.assertIs(
            evaluation.baseline_ledger.state_for(identity),
            BaselineLifecycleState.BASELINE_ESTABLISHED,
        )
        result, published = _operate_first_baseline_case(case)

        self.assertEqual((result.accepted, result.rejected), (1, 0))
        self.assertEqual(len(published), 1)
        ledger = BaselineLedger.from_optional_record(published[0].baseline_evidence)
        self.assertIs(
            ledger.state_for(identity),
            BaselineLifecycleState.BASELINE_ESTABLISHED,
        )

    def test_horizon_stops_after_real_motif_transition(self):
        from bilqis_mlx.runtime.bamf_operator.session import _execute_horizon
        events = []
        observer = NS(update=lambda **fields: events.append(fields))
        parent = NS(retained_state=NS(optimizer_step=7), optimizer_hyperparameters='hp')
        selection = NS(offer=NS(source_seed=1), visit=NS(identity=NS(visit_id='v')))
        transactions = [NS(parent=NS(optimizer_step=7), update_steps=1),
                        NS(parent=NS(optimizer_step=7), update_steps=2, motif_transition='stop')]
        prefix = 'bilqis_mlx.runtime.bamf_operator.session.'
        cache = NS(generation=1, accepted_manifest_sha256='a' * 64)
        with patch(prefix + 'prepare_candidate_evidence_root'), patch(prefix + '_Capture'), patch(
                prefix + 'FactoryDeliveryObservation'), patch(
                prefix + 'execute_accepted_priority_candidate', side_effect=[NS(transaction=x) for x in transactions]) as execute:
            steps, _capture = _execute_horizon(
                Path('/tmp'), selection, NS(), parent, 'atlas', 'feature',
                ({'id': 'row'},), 4, cache, 1, None, 0, None, None, observer)
        self.assertEqual(len(steps), 2)
        self.assertEqual(execute.call_count, 2)
        self.assertEqual(events, [{'candidate_step': 1, 'candidate_optimizer_step': 8},
                                  {'candidate_step': 2, 'candidate_optimizer_step': 9}])

    def test_completed_step_projects_every_performance_field_without_authority_change(self):
        from bilqis_mlx.runtime.bamf_operator.performance import STEP_COST_FIELDS
        from bilqis_mlx.runtime.bamf_operator.session import _execute_horizon
        transaction = NS(parent=NS(optimizer_step=7), update_steps=1)
        cost = {
            'candidate_step_wall_seconds': 1.2,
            'pre_neural_source_compile_wall_seconds': 0.1,
            'currentness_binding_wall_seconds': 0.2,
            'b11_preflight_wall_seconds': 0.3,
            'b11_autodiff_wall_seconds': 0.4,
            'optimizer_admission_wall_seconds': 0.1,
            'motif_staging_wall_seconds': 0.0,
            'evidence_capture_wall_seconds': 0.01,
            'candidate_terminal_step': False,
            'c08_gradient_launches': 1,
            'c08_vectorized_microbatches': 1,
            'c08_materialization_barriers': 1,
            'c08_scalar_fallback_rows': 0,
            'c08_logical_batch_wall_seconds': 0.7,
            'c08_rows_per_gradient_launch': 4.0,
            'b11_provider_draw_count': 16,
            'b11_atlas_reload_count': 4,
            'logical_rows': 4,
            'compiled_positions': 32,
        }
        events = []
        observer = NS(update=lambda **fields: events.append(fields))
        parent = NS(retained_state=NS(optimizer_step=7), optimizer_hyperparameters='hp')
        selection = NS(offer=NS(source_seed=1), visit=NS(identity=NS(visit_id='v')))
        cache = NS(generation=1, accepted_manifest_sha256='a' * 64)
        step = NS(transaction=transaction, realized_cost=cost)
        prefix = 'bilqis_mlx.runtime.bamf_operator.session.'
        with patch(prefix + 'prepare_candidate_evidence_root'), patch(prefix + '_Capture'), patch(
                prefix + 'FactoryDeliveryObservation'), patch(
                prefix + 'execute_accepted_priority_candidate', return_value=step):
            steps, _capture = _execute_horizon(
                Path('/tmp'), selection, NS(), parent, 'atlas', 'feature',
                ({'id': 'row'},), 1, cache, 1, None, 0, None, None, observer)
        self.assertIs(steps[0].transaction, transaction)
        self.assertEqual(events[0]['candidate_step'], 1)
        self.assertEqual(events[0]['candidate_optimizer_step'], 8)
        self.assertEqual(
            {name: events[0][name] for name in STEP_COST_FIELDS}, cost)
