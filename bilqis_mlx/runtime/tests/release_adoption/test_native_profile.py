"""Native R19 dispatch preserves explicit compiled-profile authority."""
from pathlib import Path
import unittest
from unittest.mock import patch


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

        with patch.object(session, '_operate_impl') as operate:
            session.operate_bamf(Path('/disposable'), profile_release=Path('/successor.json'))
        startup = operate.call_args.kwargs['before_visits']
        with patch('bilqis_mlx.runtime._release_adoption.native_profile.adopt_profile_release',
                   side_effect=lambda *args, **kwargs: events.append('adopt')):
            with lock(None):
                startup(Path('/disposable'))
        self.assertEqual(events, ['lock', 'adopt', 'unlock'])
