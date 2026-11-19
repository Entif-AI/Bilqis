"""Single-event teaching keeps the four-event assessment and original provider."""
import unittest

from bilqis_mlx.source_adapters import event_frames, event_intro
from bilqis_mlx.live_grade_c import registry_graph
from bilqis_mlx.verification.event_frames import independent_answer


class EventIntroductionTests(unittest.TestCase):
    def test_optional_intro_covers_truth_patterns_without_distractors(self):
        graph = event_frames.expanded_graph(registry_graph())
        for capability in event_frames.SPECS:
            rows = event_intro.enrich(
                source_root=None, graph=graph, capability=capability,
                seed=349, option_id=event_intro.OPTION)
            self.assertEqual(len(rows), 16)
            self.assertEqual(len({row['id'] for row in rows}), 16)
            self.assertEqual({tuple(row['record']['events'][0][1:]) for row in rows},
                             {(False, False), (False, True), (True, False), (True, True)})
            self.assertTrue(all(len(row['record']['events']) == 1 for row in rows))
            self.assertTrue(all(event_intro.check(row, graph=graph) for row in rows))
            self.assertTrue(all(row['gold'] == independent_answer(row['record']) for row in rows))
            fresh = event_intro.enrich(
                source_root=None, graph=graph, capability=capability,
                seed=350, option_id=event_intro.OPTION)
            self.assertNotEqual([r['id'] for r in rows], [r['id'] for r in fresh])

    def test_ordinary_assessment_still_has_four_events(self):
        graph = event_frames.expanded_graph(registry_graph())
        rows = event_intro.draw(None, graph, seed=349, each=32,
                                capability='D.EVENT_OCCURRENCE')
        self.assertTrue(all(len(r['record']['events']) == 4 for r in rows))
        self.assertTrue(all(event_intro.check(r, graph=graph) for r in rows))
        original = event_frames.draw(None, graph, seed=349, each=32,
                                     capability='D.EVENT_OCCURRENCE')
        self.assertEqual([(r['id'], r['gold']) for r in rows],
                         [(r['id'], r['gold']) for r in original])
        self.assertTrue(all(event_frames.check(r, graph=graph) for r in original))
