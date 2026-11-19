"""Native R19 dispatch preserves explicit compiled-profile authority."""
from contextlib import nullcontext
from pathlib import Path
import unittest
from unittest.mock import patch


@patch("bilqis_mlx.runtime.bamf_operator.session._training_memory_context", nullcontext)
class NativeProfileOperatorTests(unittest.TestCase):
    def test_operator_adopts_explicit_profile_inside_lock_before_first_visit(self):
        from bilqis_mlx.runtime.bamf_operator import session
        from contextlib import contextmanager
        events = []

        @contextmanager
        def lock(_root):
            events.append('lock')
            yield
            events.append('unlock')

        from types import SimpleNamespace
        from unittest.mock import MagicMock
        observer = MagicMock()
        with patch('bilqis_mlx.runtime.run_authority.bind_native_run_authority', return_value=None), patch.object(
                session, 'bamf_operator_lock', lock), patch.object(
                session, 'TrainerObservation', return_value=observer), patch.object(
                session, '_visit', side_effect=lambda *a, **kw: events.append('visit') or 'HELD'), patch.object(
                session, 'load_accepted_generation', return_value=SimpleNamespace(
                    generation=1, retained_state=SimpleNamespace(optimizer_step=0))), patch(
                'bilqis_mlx.runtime._release_adoption.native_profile.adopt_profile_release',
                side_effect=lambda *a, **kw: events.append('adopt')):
            result = session.operate_bamf(Path('/disposable'), max_visits=1,
                                          reserve_gib=0.0, source_prefetch_workers=0,
                                          profile_release=Path('/successor.json'))
        self.assertEqual(events, ['lock', 'adopt', 'visit', 'unlock'])
        self.assertEqual(result.status, 'PRIORITY_HOLD')

    def test_stale_run_authority_blocks_profile_before_any_visit(self):
        from contextlib import nullcontext
        from types import SimpleNamespace
        from unittest.mock import Mock
        from bilqis_mlx.runtime.bamf_operator._session_execution import operate
        events = []
        binding = SimpleNamespace(assert_current=Mock())
        binding.assert_current.side_effect = RuntimeError('stale authority')
        with self.assertRaisesRegex(RuntimeError, 'stale authority'):
            operate(Path('/disposable'), minutes=1, max_visits=1,
                    steps_per_visit=1, reserve_gib=0, source_prefetch_workers=0,
                    progress=None, max_horizon=16, worker_counts=(0,),
                    invalid=self.fail, metrics_type=Mock,
                    source_pool_factory=Mock(), null_context=nullcontext,
                    operator_lock=lambda _: nullcontext(), visit_fn=Mock(),
                    observer_type=Mock(), emit_progress=Mock(), monotonic=lambda: 0,
                    load_generation=Mock(), result_type=Mock(),
                    bind_run_authority=lambda _: binding,
                    before_visits=lambda _: events.append('adopt'))
        self.assertEqual(events, [])
