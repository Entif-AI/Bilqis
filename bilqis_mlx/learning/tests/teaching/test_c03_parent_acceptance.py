"""Parent C03 grade-neutrality and Factory-authority acceptance witnesses."""
from dataclasses import replace
import json
import random
from types import SimpleNamespace
import unittest

from bilqis_mlx.compatibility import historical_teacher_policy
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.execution import CurriculumProfile
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.learning.learning_experiment import (
    Settings, VERSION, earlier_grade_capabilities,
)
from bilqis_mlx.learning.teacher_observations import student_region
from bilqis_mlx.learning.teacher_strategy_population import BAMF_SUCCESSOR_SELECTION
from bilqis_mlx.learning.tests.teacher_strategy.support import teacher_fixture
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.runtime.teacher_policy_selection import select_visit_policy
from bilqis_mlx.runtime.tests.batch.test_atlas_training_adapter import (
    AtlasTrainingAdapterTest,
)
from bilqis_mlx.runtime.tests.capability.test_capability_authority import (
    CapabilityAuthorityTests, PrerequisiteThreshold, _release,
)


def _teacher():
    teacher, _strong, _weak = teacher_fixture()
    channel = teacher["causal_experiment"]
    channel["version"] = VERSION
    channel["contexts"]["Z.C0|RECOVERY_1|factory/7"] = channel["contexts"].pop(
        "C.ADD|RECOVERY_1|factory/7")
    teacher["selection_contract"] = BAMF_SUCCESSOR_SELECTION
    teacher["events"] = 100
    teacher["global_stats"] = {
        key: {"trials": 10, "reward_sum": index, "reward_ema": index}
        for index, key in enumerate(teacher["strategies"])
    }
    teacher["grade_stats"] = {
        "A": {"p-strong": {"trials": 1, "reward_sum": 1000., "reward_ema": 1000.}},
        "Z": {"p-weak": {"trials": 1, "reward_sum": 1000., "reward_ema": 1000.}},
    }
    return teacher


class C03ParentAcceptanceTests(AtlasTrainingAdapterTest):
    def _permuted_context(self, grade_id):
        release = self.context.release
        curriculum = replace(
            release.curriculum,
            grades=tuple(replace(grade, grade_id=grade_id)
                         for grade in release.curriculum.grades))
        changed = compile_executable_factory_release(
            curriculum, release.source_bindings, CurriculumProfile.full(),
            self.context.source_registry, self.context.answer_registry,
            source_root=None, graph=self.context.graph, verification_seed=17)
        return SourceExecutionContext(
            changed, self.context.graph, None,
            self.context.source_registry, self.context.answer_registry)

    def _grade_result(self, grade_id):
        context = self._permuted_context(grade_id)
        rows = context.draw_rows(seed=17, capability="Z.C0", each=1)
        actual_grade = context.release.execution_plan.capability_map["Z.C0"].grade_id
        school = SimpleNamespace(
            stage="RECOVERY_1",
            current_student=SimpleNamespace(sha256="b" * 64))
        teacher = json.loads(json.dumps(_teacher()))
        selected = select_visit_policy(
            historical_teacher_policy, teacher, "Z.C0", school,
            random.Random(17), Settings(), "factory/7", {}, actual_grade,
            total_capabilities=20)
        compiled = self.compile(rows, source_context=context)
        delivered = describe_delivered_teaching(
            context.release, "Z.C0", "source.direct/Z.C0", rows)
        program = schedule_program_from_executable_release(context.release)
        region = student_region(
            {"school": {"carried_mastery_debt": ["Z.C1"]}, "last_exam": None},
            program, "Z.C0", "RECOVERY_1", teacher,
            curriculum_scope="factory/7")
        semantic_region = {
            key: value for key, value in region.items()
            if key not in {"lesson_grade", "mastery_debt_shape", "key"}
        }
        item = compiled.rows[0]
        return {
            "selection": selected,
            "teacher": teacher,
            "row_ids": tuple(row["id"] for row in rows),
            "delivery": delivered,
            "model_input": item.model_input,
            "target": item.target,
            "provenance": item.provenance,
            "semantic_region": semantic_region,
            "diagnostic_grade": region["lesson_grade"],
            "diagnostic_debt": region["mastery_debt_shape"],
        }

    def test_actual_grade_id_permutation_preserves_teacher_and_delivered_semantics(self):
        labels = ("A", "B", "C", "Z")
        results = [self._grade_result(label) for label in labels]
        baseline = {
            key: results[0][key] for key in results[0]
            if not key.startswith("diagnostic_")
        }
        for label, result in zip(labels, results):
            self.assertEqual({
                key: result[key] for key in result
                if not key.startswith("diagnostic_")
            }, baseline)
            self.assertEqual(result["diagnostic_grade"], label)
            self.assertEqual(result["diagnostic_debt"], f"{label}:1")
        self.assertEqual(results[0]["row_ids"], ("Z.C0:17:0",))
        self.assertEqual(results[0]["semantic_region"]["mastery_debt_band"], "D01_03")

    def test_prerequisite_and_mastery_debt_follow_capabilities_not_grade_names(self):
        authority = CapabilityAuthorityTests(methodName="runTest")
        outcomes = []
        for labels in (("A", "B"), ("C", "A"), ("Z", "B")):
            release, checkpoint, admission = _release(edge=True, labels=labels)
            threshold = (PrerequisiteThreshold("foundation", 1, 1),)
            blocked = authority.gate(
                release, checkpoint, admission,
                thresholds=threshold, proof=False).reason
            missing = authority.gate(
                release, checkpoint, admission,
                thresholds=threshold, omit=True).reason
            permitted = authority.gate(
                release, checkpoint, admission,
                thresholds=threshold).status
            program = schedule_program_from_executable_release(release)
            debt = earlier_grade_capabilities(
                program, (), "target", carried_mastery_debt=("foundation",))
            no_edge, no_edge_checkpoint, no_edge_admission = _release(
                edge=False, labels=labels)
            no_implied_order_edge = authority.gate(
                no_edge, no_edge_checkpoint, no_edge_admission,
                proof=False).status
            outcomes.append((blocked, missing, permitted, debt, no_implied_order_edge))
        self.assertTrue(all(outcome == outcomes[0] for outcome in outcomes))
        self.assertEqual(outcomes[0], (
            "PREREQUISITE_EVIDENCE_INSUFFICIENT",
            "PREREQUISITE_EVIDENCE_INSUFFICIENT",
            "ELIGIBLE", ("foundation",), "ELIGIBLE"))


if __name__ == "__main__":
    unittest.main()
