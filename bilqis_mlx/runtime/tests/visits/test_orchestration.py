"""Visit orchestration preserves behavior while emitting observation evidence."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

class VisitObservationTests(unittest.TestCase):
    def _install_seams(self, patches, visits, release, program, fixture, draw, evidence, predictions, train):
        patches.enter_context(patch.object(visits._runtime_admission, "_read_executable_factory_release_artifact", return_value=release))
        patches.enter_context(patch.object(visits._runtime_release_adoption, "_schedule_for_receipt", return_value=program))
        patches.enter_context(patch.object(visits._runtime_assessment, "_draw_live_rows", side_effect=draw))
        patches.enter_context(patch.object(visits._source_adapters_school, "live_source_registry", return_value=fixture.registry))
        patches.enter_context(patch.object(visits._runtime_candidate_evidence, "_candidate_grade_evidence", side_effect=evidence))
        patches.enter_context(patch.object(visits._learning_student_ops, "_predictions", side_effect=predictions))
        patches.enter_context(patch.object(visits._learning_student_ops, "_train_step", side_effect=train))
        patches.enter_context(patch.object(visits, "_visit_retention_scope", return_value=(("Z.C1",), ("Z.C1",))))
        patches.enter_context(patch("bilqis_mlx.learning.matrix_strain.observe", return_value={"status": "NOT_MEASURED"}))

    def _fixture(self, previous):
        import mlx.core as mx
        from copy import deepcopy
        from dataclasses import asdict, replace
        from bilqis_mlx.factory.tests.test_executable_release import ExecutableFactoryReleaseTests
        from bilqis_mlx.factory.adapters import SourceAdapterRegistry
        from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
        from bilqis_mlx.curriculum.scheduler import start_new
        from bilqis_mlx.learning.champions import Checkpoint
        from bilqis_mlx.runtime import state
        from bilqis_mlx.runtime.model_topology import ModelTopologySpec, create_student
        fixture = ExecutableFactoryReleaseTests()
        fixture.setUp()
        adapter = next(iter(fixture.registry.adapters.values())) if hasattr(fixture.registry, "adapters") else fixture.registry.require("fixture.z-generator/v1", "fixture.z-oracle/v1")
        def source_rows(**kwargs):
            return tuple({**row, "tokens": [1 if row["gold"] == "FALSE" else 2],
                          "record": {"source": row["id"]}}
                         for row in adapter.draw(**kwargs))
        fixture.registry = SourceAdapterRegistry((replace(adapter, draw=source_rows),))
        from bilqis_mlx.vocabulary_growth import digest
        nodes = [dict(id=token, meaning=token, semantic_id="fixture:" + token, family="logic",
                      subtype="atomic", signature="SemanticSymbol", arity=0,
                      source="fixture:observations", admission_receipt="a" * 64)
                 for token in fixture.graph["tokens"]]
        fixture.graph.update(nodes=nodes, row_contract_sha256={node["id"]: digest(node) for node in nodes})
        release = fixture.compile()
        program = schedule_program_from_executable_release(release)
        pointer = Checkpoint("a" * 64, "bundles/fixture", 0, True)
        topology = ModelTopologySpec(1, 2, 12, 24, 96)
        parameters, optimizer = create_student(topology, len(fixture.graph["tokens"]), seed=5)
        receipt = previous or dict(generation=1, run_id="same-disposable-run", teacher={"strategies": {}},
            school=asdict(start_new(program, pointer)), config=dict(layers=1, heads=2, width=12,
                ffn_dimension=24, context=96, precision="fp32", vocab_size=3),
            model_topology=topology.to_record(), model_initialization={"origin": "fresh-model", "seed": 5},
            model_implementation={"provider": "mlx"}, source_manifest_sha256="b" * 64,
            teacher_source_sha256="c" * 64, semantic_graph_sha256=state._fingerprint(fixture.graph),
            factory_release_sha256=release.release_sha256, answer_ids=[1, 2], curriculum_mode="fixture")
        receipt = deepcopy(receipt)
        policy = dict(old=1, preview=0, depth=1, contrast=1., lr=.00013, distill=0.)
        receipt["teacher"]["strategies"] = {"fixture-policy": policy}
        return fixture, release, program, parameters, optimizer, receipt, policy

    def _qualify_retention_canary(self, receipt):
        from bilqis_mlx.learning._retention import canary
        receipt["teacher"]["retention_canary_projection"] = {
            "schema": canary.HISTORY_SCHEMA,
            "reviews": [{
                "schema": canary.SCHEMA,
                "channel": "RETENTION_TARGET_CANARY",
                "mode": "SHADOW",
                "policy_version": canary.DEFAULT_POLICY.version,
                "first_would_stop_step": 8,
                "final_retained": False,
                "false_kill": False,
                "false_continue": False,
                "actual_steps_spent": 16,
                "shadow_steps_if_active": 8,
                "shadow_steps_saved": 8,
            } for _ in range(64)],
        }

    def run_visit(self, *, enabled=True, outcome_kind="retained", autonomy=False,
                  previous=None, use_schedule_program=False, steps_per_visit=2,
                  qualified_retention_canary=False, canary_target_gain=False):
        try:
            import mlx.core as mx
            import numpy as np
        except ImportError:
            self.skipTest("native MLX unavailable")
        from contextlib import ExitStack
        from types import SimpleNamespace
        from bilqis_mlx.factory.generation import draw_executable_release_rows
        from bilqis_mlx.learning.learning_experiment import Settings
        from bilqis_mlx.runtime import visits, state
        from bilqis_mlx.runtime.teacher_observation_capture import read_observation
        fixture, release, program, parameters, optimizer, receipt, policy = self._fixture(previous)
        if qualified_retention_canary:
            self._qualify_retention_canary(receipt)
        trace = {"pick": [], "observe": [], "draw": [], "train": []}
        def pick(teacher, grade, rng):
            trace["pick"].append((grade, rng.getstate(), rng.random(), rng.getstate()))
            return "fixture-policy", policy
        def observe(teacher, grade, key, reward):
            trace["observe"].append((grade, key, reward))
            teacher["events"] = teacher.get("events", 0) + 1
        engine = SimpleNamespace(pick=pick, observe=observe)
        def draw(root, graph, *, seed, capability, each, **kwargs):
            result = list(draw_executable_release_rows(root, graph, release, fixture.registry,
                seed=seed, capability=capability, each=each))
            trace["draw"].append((seed, capability, each, [row["id"] for row in result]))
            return result
        def predictions(_mx, weights, selected, *_):
            if (canary_target_gain and weights is not parameters
                    and selected and all(row.get("capability") == target for row in selected)):
                return {row["id"]: row["gold"] for row in selected}
            return {row["id"]: (row["gold"] if outcome_kind == "skip" else "FALSE") for row in selected}
        target = "Z.C0"
        def evidence(*args):
            pair = {cap.id: {"before": 1, "after": 1, "total": 6} for cap in program.grades[0].capabilities}
            pair[target]["after"] = 2 if outcome_kind != "target-only" else 1
            if outcome_kind == "rejected":
                pair["Z.C1"]["before"], pair["Z.C1"]["after"] = 6, 0
            if outcome_kind == "target-only":
                pair = {target: pair[target]}
                protected, required, stage = set(), (target,), "TARGET_ONLY_REJECTED"
            else:
                protected, required, stage = set(pair) - {target}, tuple(pair), "COMPLETE_SAME_GRADE"
            missing = {"status": "NOT_MEASURED", "reason": "FIXTURE_NO_FRONTIER"}
            return pair, protected, required, missing, missing, missing, stage
        original_train = visits._learning_student_ops._train_step
        def train(mx, weights, own_adamw, rows, *args, **kwargs):
            trace["train"].append(([row["id"] for row in rows], int(own_adamw.state["step"].item())))
            return original_train(mx, weights, own_adamw, rows, *args, **kwargs)
        with TemporaryDirectory() as tmp, ExitStack() as patches:
            root = Path(tmp)
            self._install_seams(patches, visits, release, program, fixture, draw, evidence, predictions, train)
            mx.set_default_device(mx.cpu)
            result = visits._take_visit(mx, root, receipt, {"manifest_sha256": "b" * 64},
                program if use_schedule_program else fixture.course,
                engine, parameters, optimizer, fixture.graph, steps_per_visit=steps_per_visit,
                batch_size=6, reserve_gib=0., source_root=root, learning_settings=Settings(),
                autonomy_teaching_option="source.direct/Z.C0" if autonomy else None,
                capture_teacher_observations=enabled)
            from bilqis_mlx.runtime.checkpoints import _bundle_pointer
            from bilqis_mlx.runtime.model_topology import ModelTopologySpec
            published = _bundle_pointer(root, "observed-result", parameters, optimizer, fixture.graph,
                reserve_gib=0., model_topology=ModelTopologySpec.from_record(receipt["model_topology"]))
            event = result["_pending_visit_events"][-1]
            observation = read_observation(root, event) if enabled else None
            if enabled:
                self._assert_cold_publication(root, result, published, outcome_kind, observation)
            learner = {key: np.asarray(value).tolist() for key, value in parameters.items()}
            adamw = {key: ({name: np.asarray(value).tolist() for name, value in cell.items()}
                           if isinstance(cell, dict) else np.asarray(cell).tolist())
                     for key, cell in optimizer.state.items()}
            return dict(trace=trace, result=result, learner=learner, adamw=adamw,
                        observation=observation, event=event, release=release.release_sha256, published=published)

    def test_schedule_projection_visit_uses_release_curriculum_for_methodology(self):
        try:
            import mlx.core  # noqa: F401
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest("native MLX unavailable")
        from bilqis_mlx.factory.curriculum_definition import CurriculumDefinition
        from bilqis_mlx.runtime import visits
        seen = []
        summarize = visits._diagnostics_teaching.summarize_teaching_visit

        def capture_authority(course, *args, **kwargs):
            seen.append(course)
            return summarize(course, *args, **kwargs)

        with patch.object(visits._diagnostics_teaching, "summarize_teaching_visit",
                          side_effect=capture_authority):
            result = self.run_visit(use_schedule_program=True)
        methodology = result["event"]["lesson_methodology"]
        self.assertEqual(len(seen), 1)
        self.assertIsInstance(seen[0], CurriculumDefinition)
        self.assertEqual(methodology["capability"], "Z.C0")
        self.assertTrue(methodology["course_sha256"])

    def _assert_cold_publication(self, root, result, published, outcome_kind, observation):
        from contextlib import redirect_stdout
        from dataclasses import asdict
        import io
        from bilqis_mlx.runtime import checkpoints
        from bilqis_mlx.runtime.teacher_observation_replay import read_committed_observations
        from bilqis_mlx.learning.teacher_observations import summarize_observations
        committed = {**result, "school": {**result["school"], "current_student": asdict(published)}}
        pending = committed.pop("_pending_visit_events")
        boundary = checkpoints._boundary_delivery_events(committed, pending, (), None)
        committed = checkpoints._persist(root, checkpoints._with_delivery_outbox(committed, boundary))
        cold = read_committed_observations(root)
        self.assertEqual(len(cold), 1)
        self.assertEqual(cold[0]["ledger_delivery"], "OUTBOX_COMMITTED_NOT_EMITTED")
        with redirect_stdout(io.StringIO()):
            checkpoints._reconcile_delivery_outbox(root, committed)
            journal = (root / "events.jsonl").read_bytes()
            checkpoints._reconcile_delivery_outbox(root, committed)
        self.assertEqual((root / "events.jsonl").read_bytes(), journal)
        emitted = read_committed_observations(root)
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0]["event_id"], cold[0]["event_id"])
        self.assertEqual(emitted[0]["publication"]["checkpoint"], asdict(published))
        summary = summarize_observations(emitted)
        expected_attempted = (
            0 if outcome_kind == "skip"
            else pending[-1]["attempted_optimizer_updates"])
        self.assertEqual(summary["attempted_steps"]["value"], expected_attempted)
        expected = ("NOT_MEASURED" if outcome_kind == "skip" else "MEASURED")
        self.assertEqual(observation["outcome"]["retention"]["status"], expected)
        if outcome_kind == "skip":
            self.assertEqual(observation["outcome"]["target"]["before"]["status"], "MEASURED")
            self.assertFalse(observation["steps"])
        else:
            self.assertEqual(observation["outcome"]["retention"]["value"],
                             "RETAINED" if outcome_kind == "retained" else "REJECTED")
        if outcome_kind == "target-only":
            self.assertEqual(observation["outcome"]["protected"]["net_correct_delta"]["status"], "NOT_MEASURED")

    def test_enabled_disabled_orchestration_is_behaviorally_identical(self):
        from copy import deepcopy
        for kind, autonomy in ((kind, autonomy) for kind in ("retained", "rejected", "target-only", "skip") for autonomy in (False, True)):
            with self.subTest(kind=kind, autonomy=autonomy):
                enabled = self.run_visit(enabled=True, outcome_kind=kind, autonomy=autonomy)
                disabled = self.run_visit(enabled=False, outcome_kind=kind, autonomy=autonomy)
                self.assertEqual(enabled["trace"], disabled["trace"])
                self.assertEqual(enabled["learner"], disabled["learner"])
                self.assertEqual(enabled["adamw"], disabled["adamw"])
                self.assertEqual(enabled["release"], disabled["release"])
                self.assertEqual(enabled["published"], disabled["published"])
                without_evidence = deepcopy(enabled["result"])
                for event in without_evidence["_pending_visit_events"]:
                    event.pop("teacher_observation", None)
                self.assertEqual(without_evidence, disabled["result"])

    def test_ordinary_and_autonomy_capture_actual_support_and_order(self):
        for autonomy in (False, True):
            with self.subTest(autonomy=autonomy):
                result = self.run_visit(autonomy=autonomy)
                observation = result["observation"]
                self.assertEqual(len(observation["steps"]), 2)
                for step, trained in zip(observation["steps"], result["trace"]["train"]):
                    self.assertEqual([position["row"]["id"] for position in step["positions"]], trained[0])
                    self.assertTrue(any("retention_support" in position["roles"] for position in step["positions"]))
                    self.assertIsNotNone(step["delivered_teaching"])
                    self.assertTrue(step["realization_changed"])

    def test_qualified_retention_canary_stops_at_eight_and_confirms_target_rejection(self):
        result = self.run_visit(
            outcome_kind="target-only", steps_per_visit=16,
            qualified_retention_canary=True)
        event = result["event"]
        self.assertEqual(len(result["trace"]["train"]), 8)
        self.assertEqual(event["candidate_step_control"]["effective_steps"], 16)
        self.assertEqual(event["candidate_step_control"]["spent_steps"], 8)
        self.assertTrue(event["candidate_step_control"]["retention_canary_stopped"])
        self.assertEqual(event["candidate_retention"]["reason"], "NO_MEASURABLE_TARGET_GAIN")
        self.assertEqual(event["retention_canary"]["mode"], "ACTIVE")
        self.assertTrue(event["retention_canary"]["stop"])
        self.assertEqual(event["retention_canary"]["steps_saved"], 8)

    def test_canary_pass_still_requires_full_protected_retention_proof(self):
        result = self.run_visit(
            outcome_kind="rejected", steps_per_visit=16,
            qualified_retention_canary=True, canary_target_gain=True)
        event = result["event"]
        self.assertEqual(len(result["trace"]["train"]), 16)
        self.assertFalse(event["candidate_step_control"]["retention_canary_stopped"])
        self.assertEqual(event["candidate_step_control"]["spent_steps"], 16)
        self.assertEqual(event["retention_canary"]["mode"], "ACTIVE")
        self.assertFalse(event["retention_canary"]["stop"])
        self.assertEqual(event["candidate_retention"]["decision"], "REJECT")
        self.assertEqual(
            event["candidate_retention"]["reason"],
            "PROTECTED_CAPABILITY_REGRESSION")

    def test_retention_canary_is_deterministic_for_same_visit(self):
        first = self.run_visit(
            outcome_kind="target-only", steps_per_visit=16,
            qualified_retention_canary=True)
        second = self.run_visit(
            outcome_kind="target-only", steps_per_visit=16,
            qualified_retention_canary=True)
        self.assertEqual(
            first["event"]["retention_canary"],
            second["event"]["retention_canary"])
        self.assertEqual(
            first["event"]["candidate_step_control"],
            second["event"]["candidate_step_control"])
