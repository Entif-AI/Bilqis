"""A smaller lookup slice retains query identity and independent source gold."""
import unittest
from dataclasses import replace
from unittest.mock import patch

from bilqis_mlx.source_adapters import event_frames, event_pairs
from bilqis_mlx.live_grade_c import registry_graph


class EventPairTests(unittest.TestCase):
    def test_balanced_fresh_pairs_preserve_the_queried_transition(self):
        graph = event_frames.expanded_graph(registry_graph())
        for cap in event_frames.SPECS:
            rows = event_pairs.draw(None, graph, seed=349, each=64, capability=cap)
            self.assertEqual(len({r['id'] for r in rows}), 64)
            self.assertEqual(sum(r['gold'] == 'TRUE' for r in rows), 32)
            self.assertTrue(all(len(r['record']['events']) == 2 for r in rows))
            self.assertTrue(all(event_pairs.check(r, graph=graph) for r in rows))
            for row in rows:
                record = row['record']
                event = next(e for e in record['events'] if e[0] == record['query'])
                value = event_frames.evaluate(event_frames.expression(graph, cap, *event[1:]))
                self.assertEqual(row['gold'], 'TRUE' if value else 'FALSE')
            wrong = {**rows[0], 'gold': 'FALSE' if rows[0]['gold'] == 'TRUE' else 'TRUE'}
            self.assertFalse(event_pairs.check(wrong, graph=graph))
            self.assertNotEqual([r['id'] for r in rows], [r['id'] for r in
                event_pairs.draw(None, graph, seed=350, each=64, capability=cap)])

    def test_supplemental_lessons_pair_opposite_queries_in_the_same_world(self):
        graph = event_frames.expanded_graph(registry_graph())
        for cap in event_frames.SPECS:
            rows = event_pairs.enrich(source_root=None, graph=graph, capability=cap,
                                      seed=349, option_id=event_pairs.OPTION, prerequisites=())
            self.assertEqual(len(rows), 16)
            for left, right in zip(rows[::2], rows[1::2]):
                self.assertEqual(len(left['record']['events']), 2)
                self.assertEqual(left['record']['events'], right['record']['events'])
                self.assertNotEqual(left['record']['query'], right['record']['query'])
                self.assertNotEqual(left['gold'], right['gold'])
                self.assertTrue(event_pairs.check(left, graph=graph))
                self.assertTrue(event_pairs.check(right, graph=graph))

    def test_each_assessment_contains_an_opposite_query_pair(self):
        graph = event_frames.expanded_graph(registry_graph())
        for cap in event_frames.SPECS:
            for seed in (349, 350, 351, 352):
                rows = event_pairs.draw(None, graph, seed=seed, each=12, capability=cap)
                worlds = {}
                for row in rows:
                    key = repr(row['record']['events'])
                    worlds.setdefault(key, set()).add(row['gold'])
                self.assertTrue(any(labels == {'TRUE', 'FALSE'} for labels in worlds.values()))
                self.assertEqual(len({r['id'] for r in rows}), 12)
                self.assertEqual(sum(r['gold'] == 'TRUE' for r in rows), 6)

    def test_joint_option_preserves_declared_event_prerequisites(self):
        graph = event_frames.expanded_graph(registry_graph())
        rows = event_pairs.enrich(graph=graph, capability='D.TERMINATION', seed=349,
            option_id=event_pairs.OPTION,
            prerequisites=('D.EVENT_OCCURRENCE', 'D.COMMENCEMENT', 'A.IDENTITY'))
        self.assertEqual({cap: sum(r['capability'] == cap for r in rows)
                          for cap in event_frames.SPECS},
                         {'D.EVENT_OCCURRENCE': 16, 'D.COMMENCEMENT': 16,
                          'D.TERMINATION': 16})
        self.assertTrue(all(event_pairs.check(row, graph=graph) for row in rows))
        contexts = {cap: {(repr(r['record']['events']), r['record']['query'])
                          for r in rows if r['capability'] == cap}
                    for cap in event_frames.SPECS}
        self.assertEqual(contexts['D.TERMINATION'], contexts['D.EVENT_OCCURRENCE'])
        self.assertEqual(contexts['D.TERMINATION'], contexts['D.COMMENCEMENT'])

    def test_single_event_option_teaches_all_before_after_cases_for_each_root(self):
        graph = event_frames.expanded_graph(registry_graph())
        rows = event_pairs.enrich(graph=graph, capability='D.TERMINATION', seed=349,
                                 option_id=event_pairs.SIMPLE_OPTION)
        self.assertEqual(len(rows), 48)
        for cap in event_frames.SPECS:
            own = [row for row in rows if row['capability'] == cap]
            self.assertEqual(len(own), 16)
            self.assertEqual({tuple(row['record']['events'][0][1:]) for row in own},
                             {(False, False), (False, True), (True, False), (True, True)})
            self.assertTrue(all(len(row['record']['events']) == 1 and
                                event_pairs.check(row, graph=graph) for row in own))

    def test_introductory_provider_changes_are_bound_to_the_pair_fingerprint(self):
        before = event_pairs.registered_adapter().descriptor.implementation_sha256
        original = event_pairs.intro.registered_adapter()
        changed = replace(original, descriptor=replace(
            original.descriptor, implementation_sha256='f' * 64))
        with patch.object(event_pairs.intro, 'registered_adapter', return_value=changed):
            self.assertNotEqual(before,
                event_pairs.registered_adapter().descriptor.implementation_sha256)
