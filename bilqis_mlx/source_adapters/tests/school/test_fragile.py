"""Source-owned truth-pattern and structural replay witnesses."""
import unittest
from bilqis_mlx.learning.tests.test_fragile_replay import (
    _direct_u7c_replay_rows, _v2_replay_rows, structural_signature,
)

class FragileSourcePolicyTests(unittest.TestCase):
    def test_source_policy_owns_fragile_truth_and_structure_callbacks(self):
        from bilqis_mlx.source_adapters.school import fragile_source_policy
        from bilqis_mlx.profiles.retention import fragile_preservation_policy
        policy = fragile_source_policy(fragile_preservation_policy().source_selector)
        direct = _direct_u7c_replay_rows()[0]
        historical = _v2_replay_rows()[0]
        self.assertTrue(policy.is_exact(direct))
        self.assertFalse(policy.is_exact(historical))
        self.assertEqual(policy.signature(direct), structural_signature(direct))
        self.assertTrue(policy.verify_row(direct, direct["capability"]))
        self.assertTrue(policy.verify_row(historical, historical["capability"]))
        self.assertFalse(policy.verify_row({**direct, "gold": "wrong"}, direct["capability"]))
        self.assertEqual(policy.pattern_counts("B.OR", _direct_u7c_replay_rows(), each=4),
                         {(False, False): 1, (False, True): 1,
                          (True, False): 1, (True, True): 1})
        with self.assertRaisesRegex(ValueError, "FRAGILE_PRESERVATION_SOURCE_POLICY_UNKNOWN"):
            fragile_source_policy("unadmitted.source")
