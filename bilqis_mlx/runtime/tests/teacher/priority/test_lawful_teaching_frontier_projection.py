"""Pure #1291/#1314 lawful-teaching projection tests."""
from types import SimpleNamespace
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.atlas_frontier_closure import ClosureReason, ClosureStatus
from bilqis_mlx.factory.curriculum_definition import CapabilitySourceBinding
from bilqis_mlx.runtime.lawful_teaching_frontier_contracts import (
    LawfulTeachingDisposition,
    LawfulTeachingFrontier,
)
from bilqis_mlx.runtime.lawful_teaching_frontier_projection import _capabilities
from bilqis_mlx.semantics.atlas_projection import CorpusCoverageRow


_SHA = "a" * 64


def _release(*, reversed_order=False, relabeled=False):
    prerequisite = SimpleNamespace(
        capability_id="P", grade_id="X" if relabeled else "A",
        prerequisites=(), composed_of=())
    dependent = SimpleNamespace(
        capability_id="D", grade_id="Y" if relabeled else "B",
        prerequisites=("P",), composed_of=("P",))
    rows = (dependent, prerequisite) if reversed_order else (prerequisite, dependent)
    specs = {
        "P": SimpleNamespace(taught_roots=("sem.p",), examined_roots=("sem.p",)),
        "D": SimpleNamespace(taught_roots=("sem.d",), examined_roots=("sem.d",)),
    }
    bindings = {
        item: CapabilitySourceBinding(
            item, f"source:{item}", f"generator:{item}", f"oracle:{item}")
        for item in ("P", "D")
    }
    return SimpleNamespace(
        release_sha256=_SHA,
        execution_plan=SimpleNamespace(
            capability_map={item.capability_id: item for item in rows}),
        curriculum=SimpleNamespace(capability_map=specs),
        source_bindings=SimpleNamespace(by_capability=bindings),
    )


def _snapshot(*, held=False):
    source_held = ()
    if held:
        source_held = (CorpusCoverageRow(
            "fixture", "concepts", "D", "sem.d", "SOURCE_HELD",
            "PROGRAM_BOUND", False, "SOURCE_RIGHTS_HELD",
            "rights hold", "source:rights"),)
    return SimpleNamespace(source_held_rows=source_held)


def _closure(*, waiting=False, uncovered=False):
    status = (
        ClosureStatus.IMPLEMENTATION_UNCOVERED if uncovered
        else ClosureStatus.WAITING_FOR_EVIDENCE if waiting
        else ClosureStatus.READY)
    reason = ()
    if status is not ClosureStatus.READY:
        reason = (ClosureReason(
            "A09_" + status.value, "factory:a09", "sem.p"),)
    return SimpleNamespace(candidates=(
        SimpleNamespace(
            semantic_id="sem.d", status=status,
            prerequisites=("sem.p",), reasons=reason),
    ))


def _plan(*blocked):
    return SimpleNamespace(blocked_capabilities=tuple(blocked))


class LawfulTeachingProjectionTests(unittest.TestCase):
    def test_real_prerequisite_evidence_unlocks_dependent_without_grade_logic(self):
        before = _capabilities(_release(), _snapshot(), _closure(), _plan(), ())
        after = _capabilities(_release(), _snapshot(), _closure(), _plan(), ("P",))
        by_id_before = {item.capability_id: item for item in before}
        by_id_after = {item.capability_id: item for item in after}
        self.assertIs(
            by_id_before["D"].disposition,
            LawfulTeachingDisposition.HELD_PREREQUISITE_EVIDENCE)
        self.assertEqual(by_id_before["D"].evidence_complete_prerequisites, ())
        self.assertIs(by_id_after["D"].disposition, LawfulTeachingDisposition.READY)
        self.assertEqual(by_id_after["D"].evidence_complete_prerequisites, ("P",))
        self.assertEqual(by_id_after["D"].semantic_prerequisites, ("sem.p",))

    def test_evidence_complete_target_is_not_ready_for_teaching_again(self):
        by_id = {item.capability_id: item for item in _capabilities(
            _release(), _snapshot(), _closure(), _plan(), ("P",))}
        self.assertTrue(by_id["P"].target_evidence_complete)
        self.assertIs(
            by_id["P"].disposition, LawfulTeachingDisposition.EVIDENCE_COMPLETE)
        self.assertIs(by_id["D"].disposition, LawfulTeachingDisposition.READY)

    def test_grade_labels_and_release_iteration_order_cannot_mint_readiness(self):
        canonical = _capabilities(_release(), _snapshot(), _closure(), _plan(), ())
        adversarial = _capabilities(
            _release(reversed_order=True, relabeled=True),
            _snapshot(), _closure(), _plan(), ())
        self.assertEqual(
            tuple(item.to_record() for item in canonical),
            tuple(item.to_record() for item in adversarial))
        self.assertIs(
            adversarial[0].disposition,
            LawfulTeachingDisposition.HELD_PREREQUISITE_EVIDENCE)

    def test_source_rights_and_implementation_holds_outrank_prerequisite_readiness(self):
        source_held = {item.capability_id: item for item in _capabilities(
            _release(), _snapshot(held=True), _closure(), _plan(), ("P",))}
        uncovered = {item.capability_id: item for item in _capabilities(
            _release(), _snapshot(), _closure(uncovered=True), _plan("D"), ("P",))}
        self.assertIs(
            source_held["D"].disposition,
            LawfulTeachingDisposition.HELD_SOURCE_RIGHTS)
        self.assertIs(
            uncovered["D"].disposition,
            LawfulTeachingDisposition.IMPLEMENTATION_UNCOVERED)

    def test_a09_waiting_evidence_cannot_be_overridden_by_capability_prerequisites(self):
        by_id = {item.capability_id: item for item in _capabilities(
            _release(), _snapshot(), _closure(waiting=True), _plan(), ("P",))}
        self.assertIs(
            by_id["D"].disposition,
            LawfulTeachingDisposition.HELD_PREREQUISITE_EVIDENCE)
        self.assertIn(
            "A09_WAITING_FOR_EVIDENCE", {item.code for item in by_id["D"].holds})

    def test_frontier_cannot_be_constructed_by_a_caller(self):
        with self.assertRaises(BilqisError) as forbidden:
            LawfulTeachingFrontier()
        self.assertEqual(
            forbidden.exception.context.get("reason"),
            "BAMF_LEARNER_FRONTIER_CALLER_CONSTRUCTION_FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
