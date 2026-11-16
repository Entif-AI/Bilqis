"""#1291 learner-relative lawful teaching frontier ownership."""
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.atlas_frontier_closure import (
    ClosureReason,
    ClosureStatus,
)
from bilqis_mlx.factory.autonomy import (
    EvidenceReceipt,
    obligations_for_capability,
    record_evidence,
)
from bilqis_mlx.factory.curriculum_definition import CapabilitySourceBinding
from bilqis_mlx.paths import LEGACY_SOURCE
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.autonomy_state import (
    persist_autonomy_state,
    read_autonomy_state,
)
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
from bilqis_mlx.runtime.lawful_teaching_frontier import (
    LawfulTeachingDisposition,
    LawfulTeachingFrontier,
    issue_lawful_teaching_frontier,
    require_current_lawful_teaching_frontier,
)
from bilqis_mlx.runtime.lawful_teaching_frontier import (
    _capabilities,
)
from bilqis_mlx.runtime.tests.admission.atlas.v2.mixed_witness_support import (
    MixedWitnessSupport,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.atlas_projection import CorpusCoverageRow
from bilqis_mlx.semantics.domains import contract_digest


_SHA = "a" * 64


def _release(*, reversed_order=False, relabeled=False):
    prerequisite = SimpleNamespace(
        capability_id="P", grade_id="X" if relabeled else "A",
        prerequisites=(), composed_of=())
    dependent = SimpleNamespace(
        capability_id="D", grade_id="Y" if relabeled else "B",
        prerequisites=("P",), composed_of=("P",))
    rows = (dependent, prerequisite) if reversed_order else (
        prerequisite, dependent)
    specs = {
        "P": SimpleNamespace(
            taught_roots=("sem.p",), examined_roots=("sem.p",)),
        "D": SimpleNamespace(
            taught_roots=("sem.d",), examined_roots=("sem.d",)),
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
        before = _capabilities(
            _release(), _snapshot(), _closure(), _plan(), ())
        after = _capabilities(
            _release(), _snapshot(), _closure(), _plan(), ("P",))
        by_id_before = {item.capability_id: item for item in before}
        by_id_after = {item.capability_id: item for item in after}
        self.assertIs(
            by_id_before["D"].disposition,
            LawfulTeachingDisposition.HELD_PREREQUISITE_EVIDENCE)
        self.assertEqual(
            by_id_before["D"].evidence_complete_prerequisites, ())
        self.assertIs(
            by_id_after["D"].disposition,
            LawfulTeachingDisposition.READY)
        self.assertEqual(
            by_id_after["D"].evidence_complete_prerequisites, ("P",))
        self.assertEqual(by_id_after["D"].semantic_prerequisites, ("sem.p",))

    def test_evidence_complete_target_is_not_ready_for_teaching_again(self):
        by_id = {item.capability_id: item for item in _capabilities(
            _release(), _snapshot(), _closure(), _plan(), ("P",))}

        self.assertTrue(by_id["P"].target_evidence_complete)
        self.assertIs(
            by_id["P"].disposition,
            LawfulTeachingDisposition.EVIDENCE_COMPLETE,
        )
        self.assertIs(
            by_id["D"].disposition,
            LawfulTeachingDisposition.READY,
        )

    def test_grade_labels_and_release_iteration_order_cannot_mint_readiness(self):
        canonical = _capabilities(
            _release(), _snapshot(), _closure(), _plan(), ())
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
            _release(), _snapshot(), _closure(uncovered=True),
            _plan("D"), ("P",))}
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
            "A09_WAITING_FOR_EVIDENCE",
            {item.code for item in by_id["D"].holds})

    def test_frontier_cannot_be_constructed_by_a_caller(self):
        with self.assertRaises(BilqisError) as forbidden:
            LawfulTeachingFrontier()
        self.assertEqual(
            forbidden.exception.context.get("reason"),
            "BAMF_LEARNER_FRONTIER_CALLER_CONSTRUCTION_FORBIDDEN")


class LawfulTeachingFrontierRuntimeTests(MixedWitnessSupport, unittest.TestCase):
    def _runtime_patches(self, snapshot, schema, features, candidate):
        from contextlib import ExitStack
        from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier import (
            _rights,
        )
        source_frontier, policy = _rights()
        source_authority = SimpleNamespace(
            frontier=source_frontier,
            policy=policy,
            authority_registry_sha256="f" * 64,
        )
        selection = AtlasArtifactSelection(
            "/artifact", snapshot.bundle_id, snapshot.release_sha256,
            snapshot.source_bundle_id)
        combined = self.combined_source_registry()
        stack = ExitStack()
        stack.enter_context(self.source_replay(snapshot, schema, features))
        stack.enter_context(self.host_registry())
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_bundle.source_authority_custody."
            "currentness._trust_root_snapshot",
            return_value=("FIXTURE", 1, 2, 3, 4, 5)))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.atlas_flywheel_runtime."
            "resolve_atlas_artifact_selection", return_value=selection))
        stack.enter_context(patch(
            "bilqis_mlx.factory.skos_curriculum.compile_semantic_curriculum",
            return_value=candidate))
        stack.enter_context(patch(
            "bilqis_mlx.factory.skos_curriculum."
            "issue_source_context_transition_authority",
            return_value=source_authority))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.atlas_flywheel_runtime._candidate_frontier",
            return_value=self.frontier))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.atlas_flywheel_runtime.live_source_registry",
            return_value=combined))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.atlas_flywheel_runtime.live_answer_registry",
            return_value=self.answer_registry))
        stack.enter_context(patch(
            "bilqis_mlx.source_adapters.school.live_source_registry",
            return_value=combined))
        stack.enter_context(patch(
            "bilqis_mlx.factory.live_answers.live_answer_registry",
            return_value=self.answer_registry))
        return stack, selection

    def test_exact_accepted_frontier_reissues_after_cold_read_and_stales_on_new_evidence(self):
        with shape_patch():
            snapshot, candidate, schema, features = self.common_atlas()
            self.publish_matching_genesis(snapshot, schema, features)
            stack, selection = self._runtime_patches(
                snapshot, schema, features, candidate)
            with stack:
                parent, _ = load_bamf_generation_authority(
                    self.run / "bamf-state.json")
                context = AcceptedRuntimeHost(self.run).source_context(
                    source_root=LEGACY_SOURCE.resolve())
                frontier = issue_lawful_teaching_frontier(
                    self.run, context, parent, selection.path)
                require_current_lawful_teaching_frontier(
                    frontier, context, parent)
                self.assertEqual(
                    frontier.accepted_checkpoint_sha256,
                    frontier.candidate_identity_sha256)
                self.assertEqual(
                    frontier.admitted_release_sha256,
                    context.release.release_sha256)
                self.assertEqual(
                    frontier.accepted_correction_frontier_sha256,
                    contract_digest(parent.correction_frontier))

                plan, ledger = read_autonomy_state(self.run, context.release)
                target_id = next(
                    item.capability_id for item in frontier.capabilities
                    if not item.target_evidence_complete)
                for obligation in obligations_for_capability(
                        context.release, target_id, plan=plan):
                    ledger = record_evidence(
                        context.release, ledger, EvidenceReceipt(
                            obligation_id=obligation.obligation_id,
                            evidence_id="frontier:" + obligation.obligation_id,
                            checkpoint_sha256=frontier.accepted_checkpoint_sha256,
                            optimizer_step=frontier.accepted_optimizer_step,
                            cohort_sha256="d" * 64,
                            specimen_count=obligation.minimum_specimens,
                            passed=True,
                        ),
                        plan=plan,
                        current_checkpoint_sha256=(
                            frontier.accepted_checkpoint_sha256),
                        current_optimizer_step=frontier.accepted_optimizer_step,
                    )
                persist_autonomy_state(
                    self.run, context.release, plan=plan, ledger=ledger)
                with self.assertRaises(BilqisError) as stale:
                    require_current_lawful_teaching_frontier(
                        frontier, context, parent)
                self.assertEqual(
                    stale.exception.context.get("reason"),
                    "BAMF_LEARNER_FRONTIER_STALE")

            cold_stack, selection = self._runtime_patches(
                snapshot, schema, features, candidate)
            with cold_stack:
                cold_parent, _ = load_bamf_generation_authority(
                    self.run / "bamf-state.json")
                cold_context = AcceptedRuntimeHost(self.run).source_context(
                    source_root=LEGACY_SOURCE.resolve())
                cold = issue_lawful_teaching_frontier(
                    self.run, cold_context, cold_parent, selection.path)
                require_current_lawful_teaching_frontier(
                    cold, cold_context, cold_parent)
                self.assertNotEqual(
                    cold.autonomy_evidence_sha256,
                    frontier.autonomy_evidence_sha256)
                target = next(
                    item for item in cold.capabilities
                    if item.capability_id == target_id)
                self.assertTrue(target.target_evidence_complete)


if __name__ == "__main__":
    unittest.main()
