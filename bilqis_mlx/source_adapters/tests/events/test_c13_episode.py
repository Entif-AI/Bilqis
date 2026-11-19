"""Production source and TaskGoal authority for the C13 episode-binding family."""
from __future__ import annotations

from types import SimpleNamespace
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.live_answers import live_answer_registry
from bilqis_mlx.live_grade_c import registry_graph
from bilqis_mlx.source_adapters.c13_episode import (
    CAPABILITY, GENERATOR_ID, ORACLE_ID, PROVIDER_ID, check_episode_row,
    draw_episode, encode_case, provider_implementation_digest,
)
from bilqis_mlx.source_adapters.c13_episode_cases import (
    EpisodeBindingCase, EpisodeEvent,
)
from bilqis_mlx.source_adapters.c13_episode_release import compile_episode_release
from bilqis_mlx.source_adapters.school import live_source_registry
from bilqis_mlx.source_adapters.task_goal_registry import require_task_goal_lowerer


class C13EpisodeSourceTests(unittest.TestCase):
    def setUp(self):
        self.graph = registry_graph()
        self.registry = live_source_registry()
        self.owner = self.registry.require(GENERATOR_ID, ORACLE_ID)
        self.capability = SimpleNamespace(capability_id=CAPABILITY)

    def test_live_registry_and_factory_release_bind_exact_provider(self):
        self.assertEqual(self.owner.descriptor.adapter_id, PROVIDER_ID)
        self.assertEqual(
            self.owner.descriptor.implementation_sha256,
            provider_implementation_digest(),
        )
        release = compile_episode_release(
            None, self.graph, self.registry, live_answer_registry())
        execution = release.execution_plan.capability_map[CAPABILITY]
        self.assertEqual(execution.provider_id, PROVIDER_ID)
        self.assertEqual(
            execution.provider_implementation_sha256,
            provider_implementation_digest(),
        )
        self.assertEqual(execution.teaching_option_ids, ("source.direct/" + CAPABILITY,))

    def test_draw_is_reproducible_checked_and_exposes_no_target_actor(self):
        first = draw_episode(None, self.graph, seed=23, each=4)
        second = draw_episode(None, self.graph, seed=23, each=4)
        self.assertEqual(first, second)
        for row in first:
            self.assertTrue(check_episode_row(row, graph=self.graph))
            self.assertNotIn("target_actor", row)
            self.assertNotIn("target_actor", row["record"])
            self.assertEqual(
                row["native_output"]["identity"],
                self.graph["tokens"][row["native_output"]["token_id"]],
            )
        forged = dict(first[0])
        forged["native_output"] = dict(forged["native_output"], token_id=0)
        self.assertFalse(check_episode_row(forged, graph=self.graph))
        forged_record = dict(first[0])
        forged_record["record"] = dict(
            forged_record["record"],
            relation_cue={
                **forged_record["record"]["relation_cue"],
                "kind": "CALLER_INVENTED_RELATION",
            },
        )
        self.assertFalse(check_episode_row(forged_record, graph=self.graph))

    def test_missing_canonical_atom_rejects_before_source_row_issuance(self):
        graph = dict(self.graph)
        graph["tokens"] = [
            token for token in self.graph["tokens"]
            if token != "development.Event.E1"
        ]
        with self.assertRaises(BilqisError) as caught:
            draw_episode(None, graph, seed=23, each=1)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C13_EPISODE_GRAPH_SYMBOL_MISSING",
        )

    def test_lowerer_is_gold_blind_and_equal_values_do_not_choose_binding(self):
        events = tuple(
            EpisodeEvent(actor, ordinal, base + ordinal * 5, 5)
            for actor, base in (("A", 0), ("B", 10), ("C", 20))
            for ordinal in (0, 1)
        )
        case = EpisodeBindingCase(99, 1, events, "A", "LATER_DURATION")
        record = case.source_view()
        row = {
            "id": "equal-duration-row",
            "source_id": "equal-duration-row",
            "capability": CAPABILITY,
            "record": record,
            "tokens": encode_case(case, self.graph),
        }
        lowerer = require_task_goal_lowerer(
            PROVIDER_ID, provider_implementation_digest())
        goal, _binding = lowerer.lower(
            row, semantic_release="a" * 64, capability=self.capability)
        resolved = lowerer.resolve(
            {**row, "gold": "5"},
            semantic_release="a" * 64,
            capability=self.capability,
        )
        self.assertEqual(len(goal.expression_or_holes.nodes[0].candidate_operand_refs[0]), 3)
        self.assertEqual(
            resolved.expression_or_holes.nodes[0].operands[0].source_handle,
            "source:c13:99:duration:B:1",
        )
        with self.assertRaises(BilqisError):
            lowerer.lower(
                {**row, "gold": "5"},
                semantic_release="a" * 64,
                capability=self.capability,
            )

    def test_wrong_provider_digest_cannot_select_lowerer(self):
        with self.assertRaises(BilqisError):
            require_task_goal_lowerer(PROVIDER_ID, "0" * 64)


if __name__ == "__main__":
    unittest.main()
