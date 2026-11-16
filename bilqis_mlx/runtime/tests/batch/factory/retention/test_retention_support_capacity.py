"""Retention support capacity."""
import unittest

from bilqis_mlx.learning.tests.test_learning_experiment import (
    CausalTeacherExperimentTests, select_source_lesson,
)


class RetentionSupportCapacityTests(CausalTeacherExperimentTests):
    def test_fresh_support_yields_capacity_to_reserved_retention_rows(self):
        from bilqis_mlx.runtime.candidate_evidence import _inject_preservation_rows

        target = {
            "id": "miss", "capability": "C.MUL", "gold": "3",
            "source_id": "historic", "tokens": [1, 9],
            "answer_kind": "numeric_active",
        }
        current = [target]
        current.extend([
            {"id": f"long-{index}", "capability": "C.MUL", "gold": str(index),
             "source_id": "long", "tokens": [1, 2, 3, 4, index],
             "answer_kind": "numeric_active"}
            for index in range(3)
        ])
        current.extend([
            {"id": f"short-{index}", "capability": "C.MUL", "gold": str(index),
             "source_id": "short", "tokens": [1, index],
             "answer_kind": "numeric_active"}
            for index in range(2)
        ])
        preservation = [
            {"id": f"preserve-{index}", "capability": "B.XOR",
             "gold": "TRUE" if index else "FALSE", "tokens": [7, index]}
            for index in range(2)
        ]

        picked, control = select_source_lesson(
            current, [], {"old": 0, "depth": 3, "contrast": 0.},
            targets=[target], target_exposures={target["id"]: 0},
            reserved_support_slots=len(preservation), seed=17, batch_size=4)
        injected, delivered = _inject_preservation_rows(
            picked, preservation,
            reserved_ids=set(control["fresh_support_ids"]) |
                         set(control["weakness_target_ids"]))

        self.assertEqual(control["fresh_support_delivered"], 2)
        self.assertEqual(len(injected), 4)
        self.assertEqual({row["id"] for row in delivered},
                         {"preserve-0", "preserve-1"})
