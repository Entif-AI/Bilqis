"""Championship epoch reset authority coverage."""
import json
from dataclasses import replace

from bilqis_mlx.learning.capability_championship_state import active_checkpoint_references

from bilqis_mlx.runtime.tests.operator.observed.capability_championship_support import (
    ADJUDICATION, CAPABILITY, GROUP, NativeChampionshipCase,
    bind_accepted_championship_successor, evaluation, measurement,
    source_context, patch, Path,
)


class ChampionshipResetTests(NativeChampionshipCase):
    def titled_with_settlement(self):
        first = self.successor()
        assessment, binding = measurement(first, self.cohort, self.contexts, 20, "8" * 64)
        titled = self.bind(self.parent, first, assessment, binding)
        state = json.loads(json.dumps(titled.championship_state, sort_keys=True))
        state["settled_matchups"] = {
            CAPABILITY + "|" + "1" * 64 + "|" + "2" * 64: {
                "capability": CAPABILITY, "winner_sha256": "1" * 64,
            }}
        return replace(titled, championship_state=state)

    def reset_result(self, resumed, changed_context):
        successor = self.successor(resumed, generation=2, manifest="b")
        assessment, binding = measurement(
            successor, self.cohort, self.contexts, 18, "9" * 64)
        with patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "_require_factory_evaluation", side_effect=lambda value: value), patch(
                ADJUDICATION + "_current_binding", return_value=binding), patch(
                ADJUDICATION + "_incumbent_binding",
                side_effect=AssertionError("reset title must not replay")):
            return bind_accepted_championship_successor(
                Path("unused"), resumed, self.cache, successor, changed_context,
                "artifact", CAPABILITY, evaluation(self.cohort, assessment),
                checkpoint_origin_group=GROUP)

    def test_semantic_epoch_change_clears_roles_and_pair_suppression(self):
        resumed = self.titled_with_settlement()
        context = source_context()
        context.release.semantic_catalog_sha256 = "f" * 64
        result = self.reset_result(resumed, context)
        self.assertEqual(result.championship_state["active_roles"], {})
        self.assertEqual(result.championship_state["settled_matchups"], {})
        self.assertEqual(active_checkpoint_references(result.championship_state), ())

    def test_nonsemantic_identity_reset_preserves_pair_suppression(self):
        resumed = self.titled_with_settlement()
        context = source_context()
        context.release.release_sha256 = "f" * 64
        context.release.execution_plan.curriculum_sha256 = "e" * 64
        result = self.reset_result(resumed, context)
        self.assertEqual(result.championship_state["active_roles"], {})
        self.assertEqual(result.championship_state["settled_matchups"],
                         resumed.championship_state["settled_matchups"])

    def test_capability_roster_admission_clears_roles_and_pair_suppression(self):
        resumed = self.titled_with_settlement()
        context = source_context()
        context.release.execution_plan.projection_digests.roster = "f" * 64
        result = self.reset_result(resumed, context)
        self.assertEqual(result.championship_state["active_roles"], {})
        self.assertEqual(result.championship_state["settled_matchups"], {})
