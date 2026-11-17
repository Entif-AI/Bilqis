"""Championship epoch reset authority coverage."""
import json
from dataclasses import replace

from bilqis_mlx.learning.capability_championship_state import (
    SCHEMA_V1, active_checkpoint_references, reset_championship_state,
    settlement_epoch_sha256,
)
from bilqis_mlx.learning._epoch_championships.state import _settled_match
from bilqis_mlx.semantics.domains import contract_digest

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
        context = state["comparison_context_sha256"]
        state["settled_matchups"] = {
            CAPABILITY + "|" + context + "|" + "1" * 64 + "|" + "2" * 64: {
                "capability": CAPABILITY, "winner_sha256": "1" * 64,
                "comparison_identity_sha256": contract_digest(state["identity"]),
                "comparison_context_sha256": context,
                "settlement_epoch_sha256": state["settlement_epoch_sha256"],
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

    def test_source_and_rubric_drift_preserve_receipt_without_suppressing_new_context(self):
        resumed = self.titled_with_settlement()
        before_epoch = settlement_epoch_sha256(resumed.championship_state["identity"])
        context = source_context()
        context.release.execution_plan.projection_digests.source = "d" * 64
        context.release.execution_plan.projection_digests.assessment = "c" * 64
        result = self.reset_result(resumed, context)
        self.assertEqual(result.championship_state["active_roles"], {})
        self.assertEqual(
            result.championship_state["settled_matchups"],
            resumed.championship_state["settled_matchups"])
        self.assertEqual(
            result.championship_state["settlement_epoch_sha256"], before_epoch)
        self.assertEqual(len(result.championship_state["epoch_history"]), 1)
        self.assertEqual(
            result.championship_state["epoch_history"][0]["source_manifest_sha256"],
            self.cache.accepted_manifest_sha256)
        self.assertIsNone(_settled_match(
            result.championship_state, CAPABILITY, "1" * 64, "2" * 64))

    def test_policy_change_starts_fresh_settlement_epoch(self):
        resumed = self.titled_with_settlement()
        prior_epoch = settlement_epoch_sha256(resumed.championship_state["identity"])
        context = source_context()
        successor = self.successor(resumed, generation=2, manifest="b")
        assessment, binding = measurement(
            successor, self.cohort, self.contexts, 18, "9" * 64)
        with patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "_require_factory_evaluation", side_effect=lambda value: value), patch(
                "bilqis_mlx.runtime.bamf_operator.championship.contract_digest",
                side_effect=lambda value: "f" * 64 if value.get("schema") ==
                "bilqis.bamf.championship-policy/v1" else __import__(
                    "bilqis_mlx.semantics.domains", fromlist=["contract_digest"]
                ).contract_digest(value)), patch(
                ADJUDICATION + "_current_binding", return_value=binding), patch(
                ADJUDICATION + "_incumbent_binding",
                side_effect=AssertionError("fresh epoch must have no incumbent")):
            result = bind_accepted_championship_successor(
                Path("unused"), resumed, self.cache, successor, context,
                "artifact", CAPABILITY, evaluation(self.cohort, assessment),
                checkpoint_origin_group=GROUP)
        self.assertEqual(result.championship_state["active_roles"], {})
        self.assertEqual(result.championship_state["settled_matchups"], {})
        self.assertNotEqual(
            result.championship_state["settlement_epoch_sha256"], prior_epoch)
        self.assertEqual(len(result.championship_state["epoch_history"]), 1)

    def test_capability_roster_admission_clears_roles_and_pair_suppression(self):
        resumed = self.titled_with_settlement()
        context = source_context()
        context.release.execution_plan.projection_digests.roster = "f" * 64
        result = self.reset_result(resumed, context)
        self.assertEqual(result.championship_state["active_roles"], {})
        self.assertEqual(result.championship_state["settled_matchups"], {})

    def test_v1_identity_reset_archives_exact_cold_record_and_normalizes_live_keys(self):
        resumed = self.titled_with_settlement()
        v2 = resumed.championship_state
        old_receipt = next(iter(v2["settled_matchups"].values()))
        legacy = {
            "schema": SCHEMA_V1,
            "identity": v2["identity"],
            "active_roles": {},
            "settled_matchups": {
                CAPABILITY + "|" + "1" * 64 + "|" + "2" * 64: {
                    "capability": CAPABILITY,
                    "winner_sha256": old_receipt["winner_sha256"],
                },
            },
        }
        identity = {**v2["identity"], "factory_release_sha256": "f" * 64}
        reset = reset_championship_state(
            legacy, identity, source_manifest_sha256="e" * 64,
            source_generation=7)
        self.assertTrue(all(len(key.split("|")) == 4 for key in reset["settled_matchups"]))
        self.assertEqual(
            reset["epoch_history"][-1]["championship_state_sha256"],
            contract_digest(legacy))
