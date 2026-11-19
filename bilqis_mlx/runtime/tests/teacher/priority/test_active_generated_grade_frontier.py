"""#1314 active generated-grade membership is the outer teaching surface."""
from types import SimpleNamespace
import unittest

from bilqis_mlx.runtime.lawful_teaching_frontier import (
    ActiveGeneratedGradeState,
    _active_grade_state,
    _active_member_projection,
    _capabilities,
    _exclusions,
    _recovery_yield_capabilities,
)
from bilqis_mlx.runtime.lawful_teaching_frontier_contracts import (
    LawfulTeachingExclusion,
    LawfulTeachingExclusionCode,
    _issue_frontier,
)
from bilqis_mlx.runtime.tests.teacher.priority.authority.test_lawful_teaching_frontier_projection import (
    _closure,
    _plan,
    _release,
    _snapshot,
)


class ActiveGeneratedGradeFrontierTests(unittest.TestCase):
    def test_recovery_yield_opens_next_already_admitted_grade_without_relabeling_active_grade(self):
        release = _release(relabeled=True)
        release.execution_plan.grades = (
            SimpleNamespace(id="first", capabilities=("P",)),
            SimpleNamespace(id="next", capabilities=("D",)),
        )

        yielded = _recovery_yield_capabilities(
            release, _snapshot(), _closure(), _plan(), ("P",),
            active_capability_ids=("P",),
        )

        self.assertEqual(tuple(item.capability_id for item in yielded), ("D",))
        self.assertEqual(yielded[0].disposition.value, "READY")

    def test_recovery_yield_never_reopens_current_or_earlier_declared_grade(self):
        release = _release(relabeled=True)
        release.execution_plan.grades = (
            SimpleNamespace(id="first", capabilities=("P",)),
            SimpleNamespace(id="next", capabilities=("D",)),
        )

        yielded = _recovery_yield_capabilities(
            release, _snapshot(), _closure(), _plan(), ("P", "D"),
            active_capability_ids=("D",),
        )

        self.assertEqual(yielded, ())

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

    def test_multi_semantic_capability_cannot_teach_non_member_semantics(self):
        release = _release()
        release.curriculum.capability_map["P"].taught_roots = (
            "sem.p", "sem.future")
        capabilities = _capabilities(
            release, _snapshot(), _closure(), _plan(), (),
            active_members=(("P", ("sem.p",)),),
        )

        self.assertEqual(capabilities[0].semantic_ids, ("sem.p",))
        self.assertEqual(
            capabilities[0].disposition.value,
            "IMPLEMENTATION_UNCOVERED",
        )
        self.assertIn(
            "ACTIVE_GRADE_SEMANTIC_SCOPE_UNCOVERED",
            {item.code for item in capabilities[0].holds},
        )
        exclusion = _exclusions(release, capabilities)[0]
        self.assertIs(
            exclusion.code,
            LawfulTeachingExclusionCode.IMPLEMENTATION_UNCOVERED,
        )

    def test_successor_membership_reissue_unlocks_future_without_grade_logic(self):
        release = _release(relabeled=True)
        first = _capabilities(
            release, _snapshot(), _closure(), _plan(), ("P",),
            active_members=(("P", ("sem.p",)),),
        )
        first_exclusions = _exclusions(release, first)
        self.assertIn(
            ("D", LawfulTeachingExclusionCode.FUTURE_GENERATED_GRADE),
            tuple((item.capability_id, item.code) for item in first_exclusions),
        )

        successor = _capabilities(
            release, _snapshot(), _closure(), _plan(), ("P",),
            active_members=(("P", ("sem.p",)), ("D", ("sem.d",))),
        )
        by_id = {item.capability_id: item for item in successor}
        self.assertEqual(by_id["D"].disposition.value, "READY")
        self.assertNotIn(
            "D", {item.capability_id for item in _exclusions(release, successor)})

    def test_a09_credit_cannot_rewrite_active_member_projection(self):
        release = _release()
        binding = release.source_bindings.by_capability["P"]
        member = SimpleNamespace(
            capability_id="P", semantic_id="sem.p",
            source_anchor=binding.source_anchor)
        definition = SimpleNamespace(members=(member,))
        first = SimpleNamespace(definition=definition, accepted_credit=None)
        changed_credit = SimpleNamespace(
            definition=definition, accepted_credit=object())
        self.assertEqual(
            _active_member_projection(release, first),
            _active_member_projection(release, changed_credit),
        )

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

    def test_frontier_contract_preserves_exact_ordered_member_pairs(self):
        values = dict(
            run_id="run", accepted_generation=1,
            accepted_manifest_sha256="1" * 64,
            accepted_correction_frontier_sha256="2" * 64,
            accepted_checkpoint_sha256="3" * 64,
            accepted_optimizer_step=4,
            candidate_identity_sha256="4" * 64,
            admitted_release_sha256="5" * 64,
            admission_receipt_sha256="6" * 64,
            a09_snapshot_sha256="7" * 64,
            a09_closure_sha256="8" * 64,
            prerequisite_evidence_sha256="9" * 64,
            autonomy_plan_sha256="a" * 64,
            autonomy_evidence_sha256="b" * 64,
            rights_epoch=1, correction_generation=2, policy_epoch=3,
            source_authority_registry_sha256="c" * 64,
            active_grade_activation_sha256="d" * 64,
            active_grade_definition_sha256="e" * 64,
            active_grade_members=(("A", "s1"), ("B", "s2"), ("A", "s3")),
            active_grade_state=ActiveGeneratedGradeState.INCOMPLETE_HELD,
            capabilities=(), exclusions=(), _source_context=object(), _parent=object(),
            _planning_generation=object(),
        )
        frontier = _issue_frontier(**values)

        self.assertEqual(
            frontier.active_grade_members,
            (("A", "s1"), ("B", "s2"), ("A", "s3")),
        )
        self.assertEqual(
            frontier.to_record()["active_grade_members"],
            [["A", "s1"], ["B", "s2"], ["A", "s3"]],
        )
        exclusion = LawfulTeachingExclusion(
            "B", ("s2",),
            LawfulTeachingExclusionCode.FUTURE_GENERATED_GRADE, ())
        excluded = _issue_frontier(**{**values, "exclusions": (exclusion,)})
        self.assertEqual(
            excluded.to_record()["exclusions"], [exclusion.to_record()])
        self.assertNotEqual(frontier.frontier_sha256, excluded.frontier_sha256)


if __name__ == "__main__":
    unittest.main()
