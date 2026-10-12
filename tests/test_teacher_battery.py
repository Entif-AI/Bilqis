import copy
import json
import unittest

from bilqis_teacher.battery import make_battery, render, select_mode, verify_trace


class TeacherBatteryTests(unittest.TestCase):
    def test_identical_panel_identities_and_no_gold_in_three_renderings(self):
        battery = make_battery()
        self.assertEqual(len(battery), 8)
        for cell in battery:
            panels = []
            for mode in ('english', 'canonical', 'combined'):
                state, question, options = render(cell, mode, 0, [])
                panels.append([c['candidate_id'] for c in options])
                if cell['gold'] != 'REVIEW': self.assertNotIn(cell['gold'], question)
                self.assertNotIn('"gold"', state)
            self.assertEqual(panels[0], panels[1]); self.assertEqual(panels[1], panels[2])
            _, _, permuted = render(cell, 'combined', 1, [])
            self.assertEqual(set(panels[0]), {c['candidate_id'] for c in permuted})
            self.assertNotEqual(panels[0], [c['candidate_id'] for c in permuted])

    def test_combined_needs_meaningful_improvement_and_retains_null(self):
        summary = {m: {'correct': 10, 'review_correct': 2, 'sequential_correct': 4} for m in ('english', 'canonical', 'combined')}
        self.assertEqual(select_mode(summary)['selected'], 'canonical')
        summary['combined']['correct'] = 12
        self.assertEqual(select_mode(summary)['selected'], 'combined')
        summary['combined']['review_correct'] = 0
        self.assertEqual(select_mode(summary)['selected'], 'canonical')

    def test_order_and_actual_request_bytes_are_checked(self):
        state, question, options = render(make_battery()[0], 'combined', 1, [])
        payload = {'state': state, 'questions': {'decision': {'criteria': {c['candidate_id']: c['description'] for c in options}}}}
        raw = json.dumps(payload, separators=(',', ':'))
        import hashlib
        trace = {'payload': payload, 'serialized_request': raw, 'request_sha256': hashlib.sha256(raw.encode()).hexdigest(), 'offered_candidate_ids': [c['candidate_id'] for c in options], 'status': 'ERROR'}
        verify_trace(trace)
        bad = copy.deepcopy(trace); bad['offered_candidate_ids'].reverse()
        with self.assertRaises(ValueError): verify_trace(bad)


if __name__ == '__main__': unittest.main()
