"""The checkpoint facade remains the interception point for boundary hooks."""
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from bilqis_mlx.runtime import checkpoints


class CheckpointFacadeTests(TestCase):
    def test_historical_championship_epoch_does_not_pin_old_champion(self):
        from bilqis_mlx.learning.mentor_epoch import begin_initial_epoch
        from bilqis_mlx.runtime.checkpoint_retention import mentor_epoch_references

        def pointer(name, sha, step):
            return {"filename": "bundles/" + name, "sha256": sha * 64,
                    "optimizer_step": step, "model_and_native_adamw": True}

        old_baseline = pointer("old-baseline", "a", 1)
        old_champion = pointer("old-champion", "b", 2)
        new_baseline = pointer("new-baseline", "c", 3)
        old = begin_initial_epoch(
            student=old_baseline, introduced_grade="A",
            source_graph_sha256="d" * 64, frontier={}, soups={})
        old["active_roles"] = {"A.X": {
            "rubric": "e" * 64, "capability": "A.X",
            "correct": 11, "total": 12,
            "championship_qualification_correct": 11,
            "championship_qualification_total": 12,
            "checkpoint": old_champion,
        }}
        current = begin_initial_epoch(
            student=new_baseline, introduced_grade="B",
            source_graph_sha256="f" * 64, frontier={}, soups={})
        refs = mentor_epoch_references({
            "championship_epoch_history": [old], "mentor_epoch": current})
        self.assertEqual(refs, (new_baseline,))

    def test_new_semantic_epoch_does_not_pin_scheduler_grade_champion_bundle(self):
        root = Path('/disposable')
        student = {
            'filename': 'bundles/current', 'sha256': 'c' * 64,
            'optimizer_step': 7, 'model_and_native_adamw': True,
        }
        stale = {
            'filename': 'bundles/stale-grade-champion', 'sha256': 'a' * 64,
            'optimizer_step': 5, 'model_and_native_adamw': True,
        }
        record = {
            'generation': 2,
            'mentor_epoch': {'new_semantics': True},
            'school': {
                'active_grades': ['A', 'B'], 'grade_index': 1,
                'current_student': student, 'champions': {'A': stale},
            },
        }
        pinned = checkpoints._checkpoint_publication._learning_capability_frontier.pinned
        with patch.object(checkpoints, '_boundary_delivery_events', return_value=()), \
             patch.object(checkpoints, '_quarantine_newer_uncommitted_bundles'), \
             patch.object(checkpoints, '_mentor_epoch_references', return_value=()), \
             patch.object(
                 checkpoints._checkpoint_publication._learning_capability_frontier,
                 'pinned', wraps=pinned) as observed, \
             patch.object(
                 checkpoints._checkpoint_publication._learning_capability_frontier,
                 'retire_bundles', return_value=()), \
             patch.object(
                 checkpoints._checkpoint_publication._learning_grade_soup,
                 'retire_stale_soups', return_value=()), \
             patch.object(
                 checkpoints._checkpoint_publication._data_plane,
                 'live_grade_soups', return_value=()):
            checkpoints._publish_boundary(root, record, (), ())
        self.assertTrue(observed.call_args_list)
        self.assertTrue(all(call.args[2] == {} for call in observed.call_args_list))

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
