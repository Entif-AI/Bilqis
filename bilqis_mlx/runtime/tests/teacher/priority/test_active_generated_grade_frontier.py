"""#1314 active generated-grade membership is the outer teaching surface."""
from types import SimpleNamespace
import unittest

from bilqis_mlx.runtime.lawful_teaching_frontier import (
    ActiveGeneratedGradeState,
    _active_grade_state,
    _capabilities,
)
from bilqis_mlx.runtime.tests.teacher.priority.test_lawful_teaching_frontier_projection import (
    _closure,
    _plan,
    _release,
    _snapshot,
)


class ActiveGeneratedGradeFrontierTests(unittest.TestCase):
    def test_later_admitted_capability_is_not_teachable_outside_frozen_membership(self):
        capabilities = _capabilities(
            _release(), _snapshot(), _closure(), _plan(), (),
            active_members=(("P", ("sem.p",)),),
        )

        self.assertEqual(
            tuple(item.capability_id for item in capabilities),
            ("P",),
        )

    def test_held_member_does_not_block_independent_same_grade_member(self):
        capabilities = _capabilities(
            _release(), _snapshot(held=True), _closure(), _plan(), ("P",),
            active_members=(("P", ("sem.p",)), ("D", ("sem.d",))),
        )
        by_id = {item.capability_id: item for item in capabilities}

        self.assertEqual(by_id["P"].disposition.value, "EVIDENCE_COMPLETE")
        self.assertEqual(by_id["D"].disposition.value, "HELD_SOURCE_RIGHTS")

    def test_multi_semantic_capability_exposes_only_frozen_grade_members(self):
        release = _release()
        release.curriculum.capability_map["P"].taught_roots = (
            "sem.p", "sem.future")
        capabilities = _capabilities(
            release, _snapshot(), _closure(), _plan(), (),
            active_members=(("P", ("sem.p",)),),
        )

        self.assertEqual(capabilities[0].semantic_ids, ("sem.p",))

    def test_complete_grade_distinguishes_successor_available_from_global_fixed_point(self):
        capabilities = _capabilities(
            _release(), _snapshot(), _closure(), _plan(), ("P", "D"),
            active_members=(("P", ("sem.p",)), ("D", ("sem.d",))),
        )

        self.assertIs(
            _active_grade_state(capabilities, SimpleNamespace(value="PROPOSAL")),
            ActiveGeneratedGradeState.COMPLETE,
        )
        self.assertIs(
            _active_grade_state(capabilities, SimpleNamespace(value="FIXED_POINT")),
            ActiveGeneratedGradeState.GLOBAL_FIXED_POINT,
        )


if __name__ == "__main__":
    unittest.main()
