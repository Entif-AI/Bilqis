"""R05 native championship adviser composition; all execution is neural-inert."""
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from bilqis_mlx.learning.capability_championship import assessment_exam
from bilqis_mlx.learning._epoch_championships.receipts import _role_receipt
from bilqis_mlx.runtime.championship_advisers import (
    championship_mentor_supervision, prepare_championship_adviser_pool,
)
from bilqis_mlx.runtime.tests.operator.observed.capability_championship_support import (
    CAPABILITY, NativeChampionshipCase, capability_cohort, evaluation, measurement,
    source_context,
)


def _answer(value):
    return SimpleNamespace(
        type_name="boolean", state="VALUE", semantic_release="test-release",
        value=value)


def _accepted_ancestor_fixture(student):
    return replace(student, compiler_features={
        **student.compiler_features,
        "factory_semantic_graph_sha256": "4" * 64,
    })


def _runtime_context(case, *, group):
    context = source_context(include_sibling=True)
    capability_map = {
        item.capability_id: SimpleNamespace(
            capability_id=item.capability_id, grade_id=group)
        for item in context.release.execution_plan.capabilities
    }
    context.release.execution_plan.capabilities = tuple(capability_map.values())
    context.release.execution_plan.capability_map = capability_map
    context.release.execution_plan.grades = (
        SimpleNamespace(grade_id=group, capabilities=tuple(capability_map)),)
    context.release.execution_plan.curriculum_sha256 = "3" * 64
    return context


class NativeChampionshipMentorAdviceTests(NativeChampionshipCase):
    def test_zero_distill_skips_adviser_inference_entirely(self):
        with patch(
                "bilqis_mlx.runtime.championship_advisers."
                "factory_evaluation_instruments",
                side_effect=AssertionError("zero influence must not evaluate advisers")):
            supervision = championship_mentor_supervision(
                object(), ({"id": "row:zero"},), source_seed=17,
                teacher_strategy={"distill": 0.0})

        self.assertIsNone(supervision)

    def test_zero_distill_native_horizon_preserves_unmentored_observation(self):
        from bilqis_mlx.runtime.bamf_operator.session_parts.candidate_execution import (
            _mentor_observation,
        )

        selection = SimpleNamespace(
            policy={"distill": 0.0},
            offer=SimpleNamespace(source_seed=17, capability_id="future:cap"),
            visit=SimpleNamespace(identity=SimpleNamespace(visit_id="visit:r05-zero")),
        )
        lesson = SimpleNamespace(
            enrichment=(), prior=(), preservation=(), retention_support=())
        observation = unittest.mock.Mock(return_value="observation")
        observer = SimpleNamespace(record={})
        observer.update = lambda **fields: observer.record.update(fields)
        with patch(
                "bilqis_mlx.runtime.championship_advisers."
                "championship_mentor_supervision", return_value=None):
            result, supervision = _mentor_observation(
                object(), ({"id": "row:r05-zero"},), lesson, selection,
                object(), 8, observation, observer)

        self.assertEqual(result, "observation")
        self.assertIsNone(supervision)
        self.assertNotIn("mentors", observation.call_args.kwargs)
        self.assertNotIn("guidance", observation.call_args.kwargs)
        self.assertNotIn("_mentor_supervision", observation.call_args.kwargs)
        self.assertGreaterEqual(observer.record["adviser_wall_seconds"], 0.0)

    def test_native_horizon_materializes_mentor_supervision_before_candidate_step(self):
        from bilqis_mlx.runtime.bamf_operator.session_parts.native_session import (
            execute_horizon,
        )

        mentor_record = {
            "schema": "bilqis.mlx.championship-mentor-supervision/v1",
            "rows": [{"row_id": "row:r05", "influence": 0.04}],
        }
        guidance_record = {
            "schema": "bilqis.mlx.championship-guidance/v1",
            "rows": [{"row_id": "row:r05", "influence": 0.04}],
        }
        mentor = SimpleNamespace(
            to_record=lambda: mentor_record,
            guidance_record=lambda: guidance_record)
        adviser_pool = object()
        transaction = SimpleNamespace(update_steps=1, motif_transition=None)
        step = SimpleNamespace(transaction=transaction, realized_cost={})
        selection = SimpleNamespace(
            policy={"distill": 0.5},
            offer=SimpleNamespace(source_seed=17, capability_id="future:cap"),
            visit=SimpleNamespace(identity=SimpleNamespace(visit_id="visit:r05")),
        )
        parent = SimpleNamespace(
            retained_state=SimpleNamespace(optimizer_step=7),
            optimizer_hyperparameters="hparams",
        )
        cache = SimpleNamespace(
            generation=1, accepted_manifest_sha256="a" * 64)
        prefix = "bilqis_mlx.runtime.bamf_operator.session_parts.native_session."
        with patch(prefix + "prepare_candidate_evidence_root"), patch(
                prefix + "_Capture") as capture, patch(
                prefix + "FactoryDeliveryObservation", return_value="observation") as observation, patch(
                prefix + "execute_accepted_priority_candidate",
                return_value=step) as execute, patch(
                "bilqis_mlx.runtime.championship_advisers."
                "championship_mentor_supervision",
                return_value=mentor) as supervise:
            steps, returned_capture = execute_horizon(
                Path("/tmp"), selection, SimpleNamespace(), parent,
                "atlas", "feature", ({"id": "row:r05"},), 1, cache, 1,
                None, 0, None, None, None, adviser_pool,
                emit_progress=lambda *_args: None,
                invalid=lambda reason: self.fail(reason))

        self.assertEqual(steps, [step])
        self.assertIs(returned_capture, capture.return_value)
        supervise.assert_called_once_with(
            adviser_pool, ({"id": "row:r05"},), source_seed=17,
            teacher_strategy={"distill": 0.5})
        self.assertEqual(observation.call_args.kwargs["mentors"], mentor_record)
        self.assertEqual(
            observation.call_args.kwargs["guidance"],
            guidance_record)
        self.assertIs(
            observation.call_args.kwargs["_mentor_supervision"], mentor)
        self.assertNotIn("mentor_supervision", execute.call_args.kwargs)

    def _shared_checkpoint_parent(self):
        self.context = _runtime_context(self, group=self.GROUP if hasattr(self, "GROUP") else "factory-group-zeta")
        group = next(iter(self.context.release.execution_plan.grades)).grade_id
        cohort, contexts = capability_cohort(CAPABILITY, group)
        first = self.successor()
        assessment, binding = measurement(first, cohort, contexts, 19, "8" * 64)
        titled = self.bind(self.parent, first, assessment, binding)
        sibling_id = next(
            cap for cap in self.context.release.execution_plan.capability_map
            if cap != CAPABILITY)
        sibling_cohort, sibling_contexts = capability_cohort(sibling_id, group)
        sibling_assessment, sibling_binding = measurement(
            first, sibling_cohort, sibling_contexts, 19, "8" * 64)
        sibling_exam = assessment_exam(
            sibling_assessment, sibling_binding, challenge_group=group)
        sibling_role = _role_receipt(
            sibling_exam, sibling_id, (), scope=(sibling_id,), capability_group=group)
        state = json.loads(json.dumps(titled.championship_state, sort_keys=True))
        state["active_roles"][sibling_id] = sibling_role
        return replace(titled, championship_state=state), group

    def test_shared_checkpoint_load_is_deduped_but_logical_role_votes_survive(self):
        parent, _group = self._shared_checkpoint_parent()
        optimizer = parent.retained_state.optimizer
        moments = (optimizer.m, optimizer.v, optimizer.update_counts)
        with tempfile.TemporaryDirectory() as temp, patch(
                "bilqis_mlx.runtime.championship_advisers._accepted_ancestor",
                return_value=(_accepted_ancestor_fixture(parent), "f" * 64)) as load:
            pool = prepare_championship_adviser_pool(
                Path(temp), parent, self.context, "atlas", self.cache,
                reserve_gib=0.0)
            self.assertEqual(load.call_count, 1)
            self.assertEqual(len(pool.direct), 1)
            self.assertEqual(pool.direct[0].breadth, 2)
            self.assertEqual(pool.eligible_roles, 2)
            self.assertEqual(len(pool.soups), 1)
            self.assertEqual(pool.soups[0].soup_snapshot["vote_count"], 2)
            self.assertEqual(
                tuple(parent.retained_state.optimizer.parameters),
                tuple(pool.direct[0].weights))
            self.assertIs(parent.retained_state.optimizer, optimizer)
            self.assertIs(optimizer.m, moments[0])
            self.assertIs(optimizer.v, moments[1])
            self.assertIs(optimizer.update_counts, moments[2])

    def test_shared_checkpoint_only_votes_for_the_rows_its_logical_roles_own(self):
        parent, group = self._shared_checkpoint_parent()
        with tempfile.TemporaryDirectory() as temp, patch(
                "bilqis_mlx.runtime.championship_advisers._accepted_ancestor",
                return_value=(_accepted_ancestor_fixture(parent), "f" * 64)):
            pool = prepare_championship_adviser_pool(
                Path(temp), parent, self.context, "atlas", self.cache,
                reserve_gib=0.0)
            owned = pool.direct[0].capabilities[0]
            unrelated = "future:not-owned"
            capability_map = self.context.release.execution_plan.capability_map
            capability_map[unrelated] = SimpleNamespace(
                capability_id=unrelated, grade_id=group)
            gold = _answer(True)
            instruments = (
                SimpleNamespace(case=SimpleNamespace(
                    goal="owned", gold=gold, capability_id=owned)),
                SimpleNamespace(case=SimpleNamespace(
                    goal="unrelated", gold=gold, capability_id=unrelated)),
            )
            solver = SimpleNamespace(
                evaluate_cases=lambda goals, generation: tuple(
                    (SimpleNamespace(answer=gold), ()) for _ in goals),
                telemetry_for=lambda: {},
            )
            with patch(
                    "bilqis_mlx.runtime.championship_advisers.factory_evaluation_instruments",
                    return_value=instruments), patch(
                    "bilqis_mlx.runtime.championship_advisers.factory_complete_solver",
                    return_value=(solver, "generation")):
                supervision = championship_mentor_supervision(
                    pool,
                    ({"id": "owned"}, {"id": "unrelated"}),
                    source_seed=1, teacher_strategy={"distill": 1.0})
            self.assertEqual(supervision.rows[0].direct_votes, 1)
            self.assertEqual(supervision.rows[1].direct_votes, 0)
            self.assertTrue(supervision.rows[0].direct_advisers[0]["accepted"])
            self.assertFalse(supervision.rows[1].direct_advisers[0]["accepted"])

    def test_grade_z_forms_and_consumes_verified_soup_without_prefix_dispatch(self):
        group = "Z"
        self.context = _runtime_context(self, group=group)
        cohort, contexts = capability_cohort(CAPABILITY, group)
        self.cohort, self.contexts = cohort, contexts
        first = self.successor()
        assessment, binding = measurement(first, cohort, contexts, 19, "8" * 64)
        titled = self.bind(self.parent, first, assessment, binding)
        role = titled.championship_state["active_roles"][CAPABILITY]
        self.assertEqual(role["capability_group"], "Z")
        with tempfile.TemporaryDirectory() as temp, patch(
                "bilqis_mlx.runtime.championship_advisers._accepted_ancestor",
                return_value=(_accepted_ancestor_fixture(titled), "f" * 64)):
            pool = prepare_championship_adviser_pool(
                Path(temp), titled, self.context, "atlas", self.cache,
                reserve_gib=0.0)
            self.assertEqual(pool.soups[0].soup_snapshot["cohort_id"], "Z")
            row = {"id": "future-row", "capability": CAPABILITY}
            gold = _answer(True)
            instrument = SimpleNamespace(case=SimpleNamespace(
                goal="goal", gold=gold, capability_id=CAPABILITY))
            solver = SimpleNamespace(
                evaluate_cases=lambda goals, generation: (
                    (SimpleNamespace(answer=gold), ()),),
                telemetry_for=lambda: {
                    "shared_backbone_launches": 1, "scalar_neural_launches": 0},
            )
            with patch(
                    "bilqis_mlx.runtime.championship_advisers.factory_evaluation_instruments",
                    return_value=(instrument,)), patch(
                    "bilqis_mlx.runtime.championship_advisers.factory_complete_solver",
                    return_value=(solver, "generation")) as factory_solver:
                supervision = championship_mentor_supervision(
                    pool, (row,), source_seed=1,
                    teacher_strategy={"distill": 1.0})
            record = supervision.rows[0]
            self.assertEqual(factory_solver.call_count, 2)
            self.assertEqual(record.direct_votes, 1)
            self.assertEqual(record.soup_votes, 1.0)
            self.assertEqual(record.influence, 0.08)
            self.assertTrue(record.direct_advisers[0]["accepted"])
            self.assertTrue(record.soup_advisers[0]["accepted"])

    def test_wrong_direct_adviser_contributes_zero_while_separate_soup_survives(self):
        group = "Z"
        self.context = _runtime_context(self, group=group)
        cohort, contexts = capability_cohort(CAPABILITY, group)
        self.cohort, self.contexts = cohort, contexts
        first = self.successor()
        assessment, binding = measurement(first, cohort, contexts, 19, "8" * 64)
        titled = self.bind(self.parent, first, assessment, binding)
        with tempfile.TemporaryDirectory() as temp, patch(
                "bilqis_mlx.runtime.championship_advisers._accepted_ancestor",
                return_value=(_accepted_ancestor_fixture(titled), "f" * 64)):
            pool = prepare_championship_adviser_pool(
                Path(temp), titled, self.context, "atlas", self.cache,
                reserve_gib=0.0)
            row = {"id": "future-row", "capability": CAPABILITY}
            gold, wrong = _answer(True), _answer(False)
            instrument = SimpleNamespace(case=SimpleNamespace(
                goal="goal", gold=gold, capability_id=CAPABILITY))
            wrong_solver = SimpleNamespace(
                evaluate_cases=lambda goals, generation: (
                    (SimpleNamespace(answer=wrong), ()),), telemetry_for=lambda: {})
            correct_solver = SimpleNamespace(
                evaluate_cases=lambda goals, generation: (
                    (SimpleNamespace(answer=gold), ()),), telemetry_for=lambda: {})
            with patch(
                    "bilqis_mlx.runtime.championship_advisers.factory_evaluation_instruments",
                    return_value=(instrument,)), patch(
                    "bilqis_mlx.runtime.championship_advisers.factory_complete_solver",
                    side_effect=((wrong_solver, "direct"), (correct_solver, "soup"))):
                supervision = championship_mentor_supervision(
                    pool, (row,), source_seed=1,
                    teacher_strategy={"distill": 1.0})
            record = supervision.rows[0]
            self.assertEqual(record.direct_votes, 0)
            self.assertEqual(record.soup_votes, 1.0)
            self.assertFalse(record.direct_advisers[0]["accepted"])
            self.assertTrue(record.soup_advisers[0]["accepted"])
            self.assertEqual(record.influence, 0.08)


if __name__ == "__main__":
    unittest.main()
