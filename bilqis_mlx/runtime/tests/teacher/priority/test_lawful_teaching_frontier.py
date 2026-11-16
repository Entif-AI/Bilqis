"""#1291 learner-relative lawful teaching frontier runtime ownership."""
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.autonomy import (
    EvidenceReceipt,
    obligations_for_capability,
    record_evidence,
)
from bilqis_mlx.paths import LEGACY_SOURCE
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.autonomy_state import (
    persist_autonomy_state,
    read_autonomy_state,
)
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
from bilqis_mlx.runtime.lawful_teaching_frontier import (
    issue_lawful_teaching_frontier,
    require_current_lawful_teaching_frontier,
)
from bilqis_mlx.runtime.tests.admission.atlas.v2.mixed_witness_support import (
    MixedWitnessSupport,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.domains import contract_digest


def _historical_active_grade_reader():
    active_cache = {}

    def active_grade(run_dir):
        if "grade" not in active_cache:
            from bilqis_mlx.runtime.atlas_admission import (
                read_accepted_atlas_factory_release,
            )
            release = read_accepted_atlas_factory_release(run_dir)
            members = []
            for capability_id in sorted(release.execution_plan.capability_map):
                capability = release.curriculum.capability_map[capability_id]
                semantic_ids = tuple(dict.fromkeys((
                    *capability.taught_roots, *capability.examined_roots,
                )))
                members.append(SimpleNamespace(
                    capability_id=capability_id,
                    semantic_id=semantic_ids[0],
                    source_anchor=(release.source_bindings.by_capability[
                        capability_id].source_anchor),
                ))
            active_cache["grade"] = SimpleNamespace(
                activation_sha256="e" * 64,
                definition=SimpleNamespace(
                    definition_sha256="d" * 64,
                    members=tuple(members),
                ),
            )
        return active_cache["grade"]

    return active_grade


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
        active_grade = _historical_active_grade_reader()
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
        stack.enter_context(patch(
            "bilqis_mlx.runtime.active_generated_grade."
            "ensure_active_generated_grade",
            side_effect=active_grade))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.active_generated_grade."
            "read_active_generated_grade",
            side_effect=active_grade))
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
