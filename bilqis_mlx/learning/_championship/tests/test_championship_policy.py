"""The retired whole-grade takeover policy must not regain title authority."""
from unittest import TestCase

import bilqis_mlx.learning.championship_policy as championship_policy


class ChampionshipPolicyRetirementTests(TestCase):
    def test_whole_grade_cross_origin_takeover_api_is_retired(self):
        self.assertFalse(hasattr(championship_policy, "cross_origin_takeover"))
