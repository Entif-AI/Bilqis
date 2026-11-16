"""Literal serialization coverage for every registered CP02 record."""
import json
import unittest

from bilqis_mlx.mission_control.codec import (
    canonical_json, decode_json, decode_record, encode_record,
)
from bilqis_mlx.mission_control.contracts.registry import ALL_RECORD_TYPES
from bilqis_mlx.mission_control.tests.samples import SAMPLES


class MissionControlRoundTripTests(unittest.TestCase):
    def test_every_registered_record_has_one_literal_round_trip_sample(self):
        self.assertEqual(
            {type(sample) for sample in SAMPLES}, set(ALL_RECORD_TYPES))
        self.assertEqual(len(SAMPLES), len(ALL_RECORD_TYPES))
        for sample in SAMPLES:
            with self.subTest(schema=sample.schema_version):
                encoded = encode_record(sample)
                self.assertEqual(encoded["schema_version"], sample.schema_version)
                self.assertEqual(decode_record(encoded), sample)
                wire = canonical_json(sample)
                self.assertTrue(wire.endswith(b"\n"))
                self.assertEqual(json.loads(wire), encoded)
                self.assertEqual(decode_json(wire), sample)

    def test_literal_operator_values_do_not_disappear_into_shape_only_assertions(self):
        operator = next(sample for sample in SAMPLES if type(sample).__name__ == "OperatorView")
        encoded = encode_record(operator)
        self.assertEqual(encoded["meta"]["run"]["run_id"], "run-7")
        self.assertEqual(encoded["meta"]["run"]["generation"], 7)
        self.assertEqual(encoded["learner_state"], "READY")
        self.assertEqual(encoded["stage"], "ASSESS_MAIN")
        self.assertEqual(encoded["active_capability_id"], "B.EXAMPLE")


if __name__ == "__main__":
    unittest.main()
