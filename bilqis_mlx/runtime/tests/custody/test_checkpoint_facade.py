"""The checkpoint facade remains the interception point for boundary hooks."""
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from bilqis_mlx.runtime import checkpoints


class CheckpointFacadeTests(TestCase):
    def test_boundary_hooks_are_resolved_from_facade_at_call_time(self):
        root = Path('/disposable')
        record = {'generation': 1, 'school': {
            'active_grades': ['A'], 'grade_index': 0,
            'current_student': {'optimizer_step': 7}, 'champions': {},
        }}
        with patch.object(checkpoints, '_boundary_delivery_events', return_value=()) as events, \
             patch.object(checkpoints, '_quarantine_newer_uncommitted_bundles') as quarantine, \
             patch.object(checkpoints._checkpoint_publication._learning_capability_frontier, 'pinned', return_value=set()), \
             patch.object(checkpoints._checkpoint_publication._learning_capability_frontier, 'retire_bundles', return_value=()), \
             patch.object(checkpoints._checkpoint_publication._learning_grade_soup, 'retire_stale_soups', return_value=()), \
             patch.object(checkpoints._checkpoint_publication._data_plane, 'live_grade_soups', return_value=()):
            checkpoints._publish_boundary(root, record, (), ())
        events.assert_called_once_with(record, (), (), None)
        quarantine.assert_called_once_with(root, set(), 7)
