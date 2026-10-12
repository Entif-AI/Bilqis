import hashlib
import json
import unittest

from tools.u7b_archive import restore_request_order, gate_prediction


class ArchiveTests(unittest.TestCase):
    def test_exact_request_bytes_restore_order_after_canonical_archive(self):
        payload = {'state': 'fixture', 'questions': {'decision': {'criteria': {'Z': 'first', 'A': 'second'}}}}
        raw = json.dumps(payload, separators=(',', ':'))
        trace = {'payload': json.loads(json.dumps(payload, sort_keys=True)), 'serialized_request': raw,
                 'request_sha256': hashlib.sha256(raw.encode()).hexdigest(), 'offered_candidate_ids': ['Z', 'A'], 'status': 'ERROR'}
        fixed = restore_request_order(trace)
        self.assertEqual(list(fixed['payload']['questions']['decision']['criteria']), ['Z', 'A'])
        self.assertEqual(fixed['serialized_request'], raw)
        self.assertEqual(list(trace['payload']['questions']['decision']['criteria']), ['A', 'Z'])
        trace['payload']['state'] = 'changed'
        with self.assertRaises(ValueError): restore_request_order(trace)

    def test_gate_only_baseline_ignores_world_and_operands(self):
        for op, expected in (('AND', 'TRUE'), ('OR', 'FALSE')):
            row = {'input': {'query': {'op': op}, 'world': 'deliberately unread'}}
            self.assertEqual(gate_prediction(row), expected)


if __name__ == '__main__': unittest.main()
