"""v2 source -> exact checkpoint evidence -> durable autonomous work."""
from dataclasses import asdict, replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.execution import CurriculumProfile
from bilqis_mlx.factory.tests.test_executable_release import ExecutableFactoryReleaseTests
from bilqis_mlx.factory.autonomy import (
    AutonomyActionKind, initial_evidence_ledger, compile_autonomy_plan,
    next_action, record_evidence, reconcile_successor_evidence,
)
from bilqis_mlx.factory.evidence import measure_evidence
from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.runtime.autonomy_state import persist_autonomy_state, read_autonomy_state
from bilqis_mlx.runtime.admission import _persist_executable_factory_release
from bilqis_mlx.runtime.autonomy_live import (
    LiveAutonomySession, reconcile_live_autonomy_state)
from bilqis_mlx.learning.champions import Checkpoint


class ExecutableAutonomyTests(TestCase):
    def setUp(self):
        fixture = ExecutableFactoryReleaseTests()
        fixture.setUp()
        self.release, self.registry, self.graph = fixture.compile(), fixture.registry, fixture.graph
        self.plan = compile_autonomy_plan(self.release)
        self.student = {"sha256": "a" * 64, "optimizer_step": 10, "model_and_native_adamw": True}

    def test_v2_evidence_executes_and_current_checkpoint_stays_exact(self):
        ledger = initial_evidence_ledger(self.release, plan=self.plan)
        args = dict(current_checkpoint_sha256="a" * 64, current_optimizer_step=10)
        action = next_action(self.release, ledger, plan=self.plan, **args)
        self.assertEqual(action.kind, AutonomyActionKind.LEARNING_EVIDENCE)
        proof = measure_evidence(None, self.graph, self.release, self.registry,
            action.evidence_work.obligation, checkpoint=self.student, seed=11,
            predictor=lambda rows: {row["id"]: row["gold"] for row in rows})
        ledger = record_evidence(self.release, ledger, proof, plan=self.plan, **args)
        self.assertNotEqual(next_action(self.release, ledger, plan=self.plan, **args).evidence_work.obligation, action.evidence_work.obligation)
        changed = next_action(self.release, ledger, plan=self.plan,
            current_checkpoint_sha256="b" * 64, current_optimizer_step=11)
        self.assertEqual(changed.evidence_work.obligation, action.evidence_work.obligation)
        with TemporaryDirectory() as directory:
            persist_autonomy_state(Path(directory), self.release, plan=self.plan, ledger=ledger)
            self.assertEqual(read_autonomy_state(Path(directory), self.release), (self.plan, ledger))

    def test_v2_evidence_can_bind_predictor_to_exact_source_draw(self):
        ledger = initial_evidence_ledger(self.release, plan=self.plan)
        action = next_action(
            self.release, ledger, plan=self.plan,
            current_checkpoint_sha256="a" * 64, current_optimizer_step=10)
        observed = []

        def source_bound_predictor(rows, source_draws):
            observed.extend(source_draws)
            return {row["id"]: row["gold"] for row in rows}

        proof = measure_evidence(
            None, self.graph, self.release, self.registry,
            action.evidence_work.obligation, checkpoint=self.student, seed=11,
            predictor=None, source_bound_predictor=source_bound_predictor)

        self.assertTrue(proof.passed)
        self.assertEqual(len(observed), proof.specimen_count)
        self.assertEqual(
            {item.row_id for item in observed},
            {item.row_id for item in observed if item.source_each >= 1})
        self.assertTrue(all(item.source_seed >= 11 for item in observed))

    def test_championship_identity_uses_admitted_curriculum_projection(self):
        from types import SimpleNamespace
        from bilqis_mlx import trainer
        fixture = ExecutableFactoryReleaseTests()
        fixture.setUp()
        receipt = {"factory_release_sha256": self.release.release_sha256,
                   "factory_admission_v2": {"curriculum_sha256": self.release.curriculum.digest()},
                   "semantic_graph_sha256": trainer._fingerprint(self.graph),
                   "parameter_shapes": {"embedding.weight": [3, 2]}}
        expected = trainer.build_school_identity(
            course_sha256=self.release.curriculum.digest(),
            semantic_graph_sha256=receipt["semantic_graph_sha256"],
            parameter_shapes=receipt["parameter_shapes"],
            factory_release_sha256=self.release.release_sha256)
        self.assertEqual(trainer._live_championship_identity(receipt, fixture.course,
            self.graph, {"embedding.weight": SimpleNamespace(shape=(3, 2))}), expected)

    def test_append_only_successor_carries_only_projection_stable_evidence(self):
        ledger = initial_evidence_ledger(self.release, plan=self.plan)
        args = dict(current_checkpoint_sha256="a" * 64, current_optimizer_step=10)
        action = next_action(self.release, ledger, plan=self.plan, **args)
        proof = measure_evidence(
            None, self.graph, self.release, self.registry,
            action.evidence_work.obligation, checkpoint=self.student, seed=23,
            predictor=lambda rows: {row["id"]: row["gold"] for row in rows})
        ledger = record_evidence(
            self.release, ledger, proof, plan=self.plan, **args)

        fixture = ExecutableFactoryReleaseTests()
        fixture.setUp()
        grade = fixture.course.grades[0]
        new_capability = replace(
            grade.capabilities[-1], id="Z.C6",
            taught_roots=("fixture.op.6",), examined_roots=("fixture.op.6",))
        expanded_course = replace(
            fixture.course, grades=(replace(
                grade,
                capabilities=(*grade.capabilities, new_capability),
                exam_item_counts=(*grade.exam_item_counts, ("Z.C6", 4))),))
        curriculum, bindings = from_legacy_course(expanded_course)
        expanded_graph = {
            "tokens": [*fixture.graph["tokens"], "fixture.appended.identity"]}
        successor = compile_executable_factory_release(
            curriculum, bindings, CurriculumProfile.full(),
            fixture.registry_with_revised_roots({"Z.C6": "fixture.op.6"}),
            fixture.answers, source_root=None,
            graph=expanded_graph, verification_seed=20261019,
            predecessor=self.release)
        successor_plan = compile_autonomy_plan(successor)
        reconciled = reconcile_successor_evidence(
            self.release, successor, ledger,
            previous_plan=self.plan, current_plan=successor_plan)
        self.assertEqual(reconciled.receipts, ledger.receipts)
        self.assertEqual(reconciled.interventions, ())
        self.assertEqual(
            reconciled.factory_release_sha256, successor.release_sha256)

    def test_cold_restart_successor_recovers_projection_stable_evidence(self):
        ledger = initial_evidence_ledger(self.release, plan=self.plan)
        args = dict(
            current_checkpoint_sha256="a" * 64, current_optimizer_step=10)
        action = next_action(self.release, ledger, plan=self.plan, **args)
        proof = measure_evidence(
            None, self.graph, self.release, self.registry,
            action.evidence_work.obligation, checkpoint=self.student, seed=29,
            predictor=lambda rows: {row["id"]: row["gold"] for row in rows})
        ledger = record_evidence(
            self.release, ledger, proof, plan=self.plan, **args)

        fixture = ExecutableFactoryReleaseTests()
        fixture.setUp()
        grade = fixture.course.grades[0]
        new_capability = replace(
            grade.capabilities[-1], id="Z.C6",
            taught_roots=("fixture.op.6",), examined_roots=("fixture.op.6",))
        expanded_course = replace(
            fixture.course, grades=(replace(
                grade,
                capabilities=(*grade.capabilities, new_capability),
                exam_item_counts=(*grade.exam_item_counts, ("Z.C6", 4))),))
        curriculum, bindings = from_legacy_course(expanded_course)
        expanded_graph = {
            "tokens": [*fixture.graph["tokens"], "fixture.appended.identity"]}
        successor = compile_executable_factory_release(
            curriculum, bindings, CurriculumProfile.full(),
            fixture.registry_with_revised_roots({"Z.C6": "fixture.op.6"}),
            fixture.answers, source_root=None,
            graph=expanded_graph, verification_seed=20261019,
            predecessor=self.release)
        successor_plan = compile_autonomy_plan(successor)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _persist_executable_factory_release(root, self.release)
            _persist_executable_factory_release(root, successor)
            persist_autonomy_state(
                root, self.release, plan=self.plan, ledger=ledger)
            recovered = reconcile_live_autonomy_state(
                root, successor, successor_plan)
            self.assertEqual(recovered.receipts, ledger.receipts)
            self.assertEqual(
                read_autonomy_state(root, successor),
                (successor_plan, recovered))

    def test_committed_teaching_outbox_recovers_missing_intervention(self):
        parent = Checkpoint("a" * 64, "bundles/parent", 10, True)
        child = Checkpoint("b" * 64, "bundles/child", 11, True)
        ledger = initial_evidence_ledger(self.release, plan=self.plan)
        action = next_action(
            self.release, ledger, plan=self.plan,
            current_checkpoint_sha256=parent.sha256,
            current_optimizer_step=parent.optimizer_step)
        obligation = action.evidence_work.obligation
        from bilqis_mlx.factory.autonomy import EvidenceReceipt
        failed = EvidenceReceipt(
            obligation.obligation_id, "failed-before-teaching",
            parent.sha256, parent.optimizer_step, "c" * 64,
            obligation.minimum_specimens, False)
        ledger = record_evidence(
            self.release, ledger, failed, plan=self.plan,
            current_checkpoint_sha256=parent.sha256,
            current_optimizer_step=parent.optimizer_step)
        capability = action.evidence_work.capability_id
        option = action.evidence_work.teaching_option_ids[0]
        rows = [{
            "id": "teaching-row-1", "capability": capability,
            "gold": "TRUE", "answer_kind": "binary"}]
        delivery = describe_delivered_teaching(
            self.release, capability, option, rows)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            persist_autonomy_state(
                root, self.release, plan=self.plan, ledger=ledger)
            teaching_file = (
                root / "autonomy/teaching" /
                (delivery.specimen_content_sha256 + ".json"))
            teaching_file.parent.mkdir(parents=True, exist_ok=True)
            teaching_file.write_text(
                json.dumps({"rows": rows}), encoding="utf-8")
            school_receipt = {
                "run_id": "issue-349-test",
                "generation": 7,
                "delivery_outbox": [{
                    "event": "SCHOOL_TEACHER_VISIT_COMMITTED",
                    "capability": capability,
                    "optimizer_step": child.optimizer_step,
                    "retained_optimizer_updates": 1,
                    "recovered_at_student_sha256": child.sha256,
                    "autonomy_teaching": {
                        **asdict(delivery),
                        "specimen_file": (
                            "autonomy/teaching/" +
                            delivery.specimen_content_sha256 + ".json"),
                    },
                }],
            }
            session = LiveAutonomySession(
                root, Path("."), self.release, self.plan, ledger)
            recovered = session.recover_teaching(school_receipt, child)
            self.assertIsNotNone(recovered)
            self.assertEqual(
                recovered.specimen_content_sha256,
                delivery.specimen_content_sha256)
            self.assertEqual(recovered.parent_checkpoint_sha256, parent.sha256)
            self.assertEqual(recovered.checkpoint_sha256, child.sha256)
            self.assertEqual(len(session.ledger.interventions), 1)
            self.assertEqual(
                session.recover_teaching(school_receipt, child), recovered)
            self.assertEqual(len(session.ledger.interventions), 1)
            self.assertEqual(
                read_autonomy_state(root, self.release),
                (self.plan, session.ledger))

    def test_rejected_teaching_outbox_is_not_recovered_as_intervention(self):
        parent = Checkpoint("a" * 64, "bundles/parent", 10, True)
        child = Checkpoint("b" * 64, "bundles/child", 11, True)
        ledger = initial_evidence_ledger(self.release, plan=self.plan)
        action = next_action(
            self.release, ledger, plan=self.plan,
            current_checkpoint_sha256=parent.sha256,
            current_optimizer_step=parent.optimizer_step)
        obligation = action.evidence_work.obligation
        from bilqis_mlx.factory.autonomy import EvidenceReceipt
        failed = EvidenceReceipt(
            obligation.obligation_id, "failed-before-rejected-teaching",
            parent.sha256, parent.optimizer_step, "c" * 64,
            obligation.minimum_specimens, False)
        ledger = record_evidence(
            self.release, ledger, failed, plan=self.plan,
            current_checkpoint_sha256=parent.sha256,
            current_optimizer_step=parent.optimizer_step)
        failed_child = EvidenceReceipt(
            obligation.obligation_id, "failed-after-retained-teaching",
            child.sha256, child.optimizer_step, "d" * 64,
            obligation.minimum_specimens, False)
        ledger = record_evidence(
            self.release, ledger, failed_child, plan=self.plan,
            current_checkpoint_sha256=child.sha256,
            current_optimizer_step=child.optimizer_step)
        capability = action.evidence_work.capability_id
        option = action.evidence_work.teaching_option_ids[0]
        rows = [{
            "id": "rejected-teaching-row-1", "capability": capability,
            "gold": "TRUE", "answer_kind": "binary"}]
        delivery = describe_delivered_teaching(
            self.release, capability, option, rows)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            teaching_file = (
                root / "autonomy/teaching" /
                (delivery.specimen_content_sha256 + ".json"))
            teaching_file.parent.mkdir(parents=True, exist_ok=True)
            teaching_file.write_text(
                json.dumps({"rows": rows}), encoding="utf-8")
            school_receipt = {
                "run_id": "issue-349-test",
                "generation": 8,
                "delivery_outbox": [{
                    "event": "SCHOOL_TEACHER_VISIT_COMMITTED",
                    "capability": capability,
                    "optimizer_step": child.optimizer_step,
                    "candidate_attempt_optimizer_step":
                        child.optimizer_step + 4,
                    "retained_optimizer_updates": 0,
                    "recovered_at_student_sha256": child.sha256,
                    "autonomy_teaching": {
                        **asdict(delivery),
                        "specimen_file": (
                            "autonomy/teaching/" +
                            delivery.specimen_content_sha256 + ".json"),
                    },
                }],
            }
            session = LiveAutonomySession(
                root, Path("."), self.release, self.plan, ledger)
            self.assertIsNone(
                session.recover_teaching(school_receipt, child))
            self.assertEqual(session.ledger, ledger)
