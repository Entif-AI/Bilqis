from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch


class SessionCandidateExecutionTests(unittest.TestCase):
    def test_horizon_stops_after_real_motif_transition(self):
        from bilqis_mlx.runtime.bamf_operator.session_parts.native_session import execute_horizon
        from bilqis_mlx.runtime.bamf_operator.session import _emit_progress, _invalid
        events = []
        observer = NS(update=lambda **fields: events.append(fields))
        parent = NS(retained_state=NS(optimizer_step=7), optimizer_hyperparameters='hp')
        selection = NS(offer=NS(source_seed=1), visit=NS(identity=NS(visit_id='v')))
        transactions = [NS(parent=NS(optimizer_step=7), update_steps=1),
                        NS(parent=NS(optimizer_step=7), update_steps=2, motif_transition='stop')]
        prefix = 'bilqis_mlx.runtime.bamf_operator.session_parts.native_session.'
        cache = NS(generation=1, accepted_manifest_sha256='a' * 64)
        with patch(prefix + 'prepare_candidate_evidence_root'), patch(prefix + '_Capture'), patch(
                prefix + 'FactoryDeliveryObservation'), patch(
                prefix + 'execute_accepted_priority_candidate', side_effect=[NS(transaction=x) for x in transactions]) as execute:
            steps, _capture = execute_horizon(
                Path('/tmp'), selection, NS(), parent, 'atlas', 'feature',
                ({'id': 'row'},), 4, cache, 1, None, 0, None, None, observer, None,
                emit_progress=_emit_progress, invalid=_invalid)
        self.assertEqual(len(steps), 2)
        self.assertEqual(execute.call_count, 2)
        self.assertEqual(events, [{'candidate_step': 1, 'candidate_optimizer_step': 8},
                                  {'candidate_step': 2, 'candidate_optimizer_step': 9}])

    def test_horizon_uses_selected_teacher_projection_for_first_instruction(self):
        from bilqis_mlx.runtime.bamf_operator.session_parts.native_session import execute_horizon
        from bilqis_mlx.runtime.bamf_operator.session import _emit_progress, _invalid
        observer = NS(update=lambda **fields: None)
        parent = NS(
            teacher_state={"schema": "raw-genesis"},
            retained_state=NS(optimizer_step=0),
            optimizer_hyperparameters='hp',
        )
        selection = NS(
            offer=NS(source_seed=1, capability_id='cap:first'),
            visit=NS(
                identity=NS(visit_id='v'),
                projection=NS(teacher_state={"schema": "projected-c03"}),
            ),
        )
        cache = NS(generation=0, accepted_manifest_sha256='a' * 64)
        transaction = NS(parent=NS(optimizer_step=0), update_steps=1)
        step = NS(transaction=transaction, realized_cost={})
        prefix = 'bilqis_mlx.runtime.bamf_operator.session_parts.native_session.'
        with patch(prefix + 'prepare_candidate_evidence_root'), patch(
                prefix + '_Capture') as capture, patch(
                prefix + 'FactoryDeliveryObservation'), patch(
                prefix + 'execute_accepted_priority_candidate', return_value=step), patch(
                'bilqis_mlx.learning.teacher_lineage.instruction_history',
                return_value=('COMPLETE', ())) as history, patch(
                'bilqis_mlx.runtime.priority_rejection_replay.rejection_recency',
                return_value=(None, ())):
            execute_horizon(
                Path('/tmp'), selection, NS(), parent, 'atlas', 'feature',
                ({'id': 'row'},), 1, cache, 1, None, 0, None, None, observer, None,
                emit_progress=_emit_progress, invalid=_invalid)
        history.assert_called_once_with(selection.visit.projection.teacher_state)
        self.assertTrue(capture.call_args.kwargs['introductory'])

    def test_completed_step_projects_every_performance_field_without_authority_change(self):
        from bilqis_mlx.runtime.bamf_operator.performance import STEP_COST_FIELDS
        from bilqis_mlx.runtime.bamf_operator.session_parts.native_session import execute_horizon
        from bilqis_mlx.runtime.bamf_operator.session import _emit_progress, _invalid
        transaction = NS(parent=NS(optimizer_step=7), update_steps=1)
        cost = {
            'candidate_step_wall_seconds': 1.2,
            'pre_neural_source_compile_wall_seconds': 0.1,
            'currentness_binding_wall_seconds': 0.2,
            'accepted_currentness_refresh_wall_seconds': 0.0,
            'accepted_currentness_live_fence_wall_seconds': 0.0,
            'accepted_parent_currentness_wall_seconds': 0.0,
            'lawful_frontier_currentness_wall_seconds': 0.0,
            'teacher_visit_currentness_wall_seconds': 0.0,
            'source_currentness_wall_seconds': 0.0,
            'candidate_binding_wall_seconds': 0.0,
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
        prefix = 'bilqis_mlx.runtime.bamf_operator.session_parts.native_session.'
        with patch(prefix + 'prepare_candidate_evidence_root'), patch(prefix + '_Capture'), patch(
                prefix + 'FactoryDeliveryObservation'), patch(
                prefix + 'execute_accepted_priority_candidate', return_value=step):
            steps, _capture = execute_horizon(
                Path('/tmp'), selection, NS(), parent, 'atlas', 'feature',
                ({'id': 'row'},), 1, cache, 1, None, 0, None, None, observer, None,
                emit_progress=_emit_progress, invalid=_invalid)
        self.assertIs(steps[0].transaction, transaction)
        self.assertEqual(events[0]['candidate_step'], 1)
        self.assertEqual(events[0]['candidate_optimizer_step'], 8)
        self.assertEqual(
            {name: events[0][name] for name in STEP_COST_FIELDS}, cost)


if __name__ == '__main__':
    unittest.main()
