"""Production developmental coverage metrics stay distinct and authority-derived."""
import unittest

from bilqis_mlx.factory.generated_grade.development_inputs import (
    _minimal_contrast_value,
    _reusable_constituent_value,
)


class GeneratedGradeDevelopmentInputTests(unittest.TestCase):
    def test_reusable_constituent_value_counts_transitive_compiled_dependents(self):
        graph = {
            "root": set(),
            "middle": {"root"},
            "leaf": {"middle"},
            "peer": set(),
        }

        self.assertEqual(_reusable_constituent_value("root", graph), 2)
        self.assertEqual(_reusable_constituent_value("middle", graph), 1)
        self.assertEqual(_reusable_constituent_value("leaf", graph), 0)
        self.assertEqual(_reusable_constituent_value("peer", graph), 0)

    def test_minimal_contrast_value_counts_mastered_family_overlap(self):
        families = {
            "mastered-a": {"identity", "relation"},
            "mastered-b": {"quantity"},
            "candidate": {"identity", "quantity", "new-factor"},
        }

        self.assertEqual(
            _minimal_contrast_value(
                "candidate", families, {"mastered-a", "mastered-b"}),
            2,
        )
        self.assertEqual(
            _minimal_contrast_value("candidate", families, set()),
            0,
        )


if __name__ == "__main__":
    unittest.main()
