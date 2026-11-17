"""Fresh defense, tie transfer, and bounded same-group fan-out coverage."""
import json
from dataclasses import asdict, replace

from bilqis_mlx.learning.capability_championship import assessment_exam
from bilqis_mlx.learning.capability_championship_state import (
    SCHEMA_V1 as CHAMPIONSHIP_SCHEMA_V1, active_checkpoint_references,
)
from bilqis_mlx.learning._epoch_championships.receipts import _role_receipt
from bilqis_mlx.semantics.domains import contract_digest

from bilqis_mlx.runtime.tests.operator.observed.capability_championship_support import (
    ADJUDICATION, CAPABILITY, GROUP, SIBLING, NativeChampionshipCase,
    bind_accepted_championship_successor, capability_cohort, evaluation,
    measurement, source_context, patch, Path,
)


class ChampionshipCompetitionTests(NativeChampionshipCase):
    def test_same_identity_v1_cold_state_upgrades_before_new_settlement(self):
        first = self.successor()
        first_assessment, incumbent = measurement(
            first, self.cohort, self.contexts, 20, "8" * 64)
        titled = self.bind(self.parent, first, first_assessment, incumbent)
        legacy = json.loads(json.dumps(titled.championship_state, sort_keys=True))
        legacy["schema"] = CHAMPIONSHIP_SCHEMA_V1
        legacy.pop("settlement_epoch_sha256")
        legacy.pop("comparison_context_sha256")
        legacy.pop("epoch_history")
        resumed = replace(titled, championship_state=legacy)
        challenger = self.successor(resumed, generation=2, manifest="b")
        challenge_assessment, challenger_binding = measurement(
            challenger, self.cohort, self.contexts, 20, "9" * 64)
        transferred = self.bind(
            resumed, challenger, challenge_assessment, challenger_binding,
            incumbent=incumbent)
        self.assertNotEqual(
            transferred.championship_state["schema"], CHAMPIONSHIP_SCHEMA_V1)
        self.assertTrue(transferred.championship_state["settled_matchups"])
        settlement = next(iter(transferred.championship_state["settled_matchups"].values()))
        self.assertEqual(
            settlement["comparison_context_sha256"],
            transferred.championship_state["comparison_context_sha256"])

    def test_native_takeover_runs_one_capability_local_same_group_fanout(self):
        self.context = source_context(include_sibling=True)
        first = self.successor()
        first_assessment, target_incumbent = measurement(
            first, self.cohort, self.contexts, 19, "8" * 64)
        titled = self.bind(self.parent, first, first_assessment, target_incumbent)
        sibling_cohort, sibling_contexts = capability_cohort(SIBLING)
        sibling_assessment, sibling_incumbent = measurement(
            first, sibling_cohort, sibling_contexts, 19, "8" * 64)
        sibling_exam = assessment_exam(
            sibling_assessment, sibling_incumbent, challenge_group=GROUP)
        sibling_role = _role_receipt(
            sibling_exam, SIBLING, (), scope=(SIBLING,), capability_group=GROUP)
        state = json.loads(json.dumps(titled.championship_state, sort_keys=True))
        state["active_roles"][SIBLING] = sibling_role
        parent = replace(titled, championship_state=state)
        challenger = self.successor(parent, generation=2, manifest="b")
        challenge_assessment, target_challenger = measurement(
            challenger, self.cohort, self.contexts, 20, "9" * 64)
        sibling_challenge_assessment, sibling_challenger = measurement(
            challenger, sibling_cohort, sibling_contexts, 19, "9" * 64)
        target_challenger = replace(target_challenger, checkpoint_origin_group="opaque-origin")
        sibling_challenger = replace(sibling_challenger, checkpoint_origin_group="opaque-origin")

        def current_binding(*args, **_kwargs):
            cohort = args[7]
            return sibling_challenger if cohort.capability_groups[0][0] == SIBLING else target_challenger

        def incumbent_binding(*args, **_kwargs):
            role = args[-1]
            return sibling_incumbent if role["capability"] == SIBLING else target_incumbent

        with patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "_require_factory_evaluation", side_effect=lambda value: value), patch(
                ADJUDICATION + "_current_binding", side_effect=current_binding), patch(
                ADJUDICATION + "_incumbent_binding", side_effect=incumbent_binding), patch(
                ADJUDICATION + "capability_championship_evidence",
                return_value=(sibling_cohort, sibling_challenge_assessment)):
            result = bind_accepted_championship_successor(
                Path("unused"), parent, self.cache, challenger, self.context,
                "artifact", CAPABILITY, evaluation(self.cohort, challenge_assessment),
                checkpoint_origin_group="opaque-origin")
        roles = result.championship_state["active_roles"]
        self.assertEqual(roles[CAPABILITY]["checkpoint"]["sha256"],
                         target_challenger.checkpoint.sha256)
        self.assertEqual(roles[SIBLING]["checkpoint"]["sha256"],
                         sibling_challenger.checkpoint.sha256)
        self.assertTrue(any(key.startswith(SIBLING + "|")
                            for key in result.championship_state["settled_matchups"]))

    def test_title_survives_failed_challenge_then_tie_transfers(self):
        first = self.successor()
        first_assessment, incumbent = measurement(
            first, self.cohort, self.contexts, 20, "8" * 64)
        titled = self.bind(self.parent, first, first_assessment, incumbent)
        role = titled.championship_state["active_roles"][CAPABILITY]
        cold_state = json.loads(json.dumps(titled.championship_state, sort_keys=True))
        resumed = replace(titled, championship_state=cold_state)
        failed = self.successor(resumed, generation=2, manifest="b")
        failed_assessment, failed_binding = measurement(
            failed, self.cohort, self.contexts, 19, "9" * 64)
        defended = self.bind(resumed, failed, failed_assessment, failed_binding,
                             incumbent=incumbent)
        self.assertEqual(active_checkpoint_references(defended.championship_state),
                         (role["checkpoint"],))
        tied = self.successor(defended, generation=3, manifest="c")
        tied_assessment, challenger = measurement(
            tied, self.cohort, self.contexts, 20, "a" * 64)
        transferred = self.bind(defended, tied, tied_assessment, challenger,
                                incumbent=incumbent)
        winner = transferred.championship_state["active_roles"][CAPABILITY]
        self.assertEqual(winner["checkpoint"], asdict(challenger.checkpoint))
        self.assertNotEqual(winner["checkpoint"], role["checkpoint"])
        self.assertTrue(transferred.championship_state["settled_matchups"])
        settlement = next(iter(transferred.championship_state["settled_matchups"].values()))
        self.assertEqual(
            settlement["settlement_epoch_sha256"],
            transferred.championship_state["settlement_epoch_sha256"])
        self.assertEqual(len(settlement["comparison_identity_sha256"]), 64)

    def test_same_pair_is_suppressed_before_native_incumbent_replay(self):
        first = self.successor()
        first_assessment, incumbent = measurement(
            first, self.cohort, self.contexts, 20, "8" * 64)
        titled = self.bind(self.parent, first, first_assessment, incumbent)
        challenger = self.successor(titled, generation=2, manifest="b")
        challenge_assessment, challenger_binding = measurement(
            challenger, self.cohort, self.contexts, 19, "9" * 64)
        state = json.loads(json.dumps(titled.championship_state, sort_keys=True))
        pair = sorted((incumbent.checkpoint.sha256, challenger_binding.checkpoint.sha256))
        context = state["comparison_context_sha256"]
        state["settled_matchups"][CAPABILITY + "|" + context + "|" + "|".join(pair)] = {
            "capability": CAPABILITY,
            "winner_sha256": incumbent.checkpoint.sha256,
            "comparison_identity_sha256": contract_digest(state["identity"]),
            "comparison_context_sha256": context,
            "settlement_epoch_sha256": state["settlement_epoch_sha256"],
        }
        settled = replace(titled, championship_state=state)
        before = json.loads(json.dumps(state, sort_keys=True))
        with patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "_require_factory_evaluation", side_effect=lambda value: value), patch(
                ADJUDICATION + "_current_binding", return_value=challenger_binding), patch(
                ADJUDICATION + "_incumbent_binding",
                side_effect=AssertionError("settled pair must suppress incumbent replay")):
            replay = bind_accepted_championship_successor(
                Path("unused"), settled, self.cache, challenger, self.context,
                "artifact", CAPABILITY, evaluation(self.cohort, challenge_assessment),
                checkpoint_origin_group=GROUP)
        self.assertEqual(replay.championship_state, before)
