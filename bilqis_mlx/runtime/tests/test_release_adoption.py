"""A source/teaching revision need not change the scheduler projection."""
from dataclasses import replace
from types import SimpleNamespace
import unittest

from bilqis_mlx.curriculum.scheduler import DebtCadencePolicy, start_new
from bilqis_mlx.factory.schedule import ScheduleCapability, ScheduleGrade, ScheduleProgram
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.release_adoption import (
    _grade_a_member_context_revision_required,
    _profile_transition,
    _source_presentation_revision_required,
)
from bilqis_mlx.source_adapters.grade_a_presentation import (
    IRRELEVANT_CONTEXT_VARIATION, MEMBER_CONTEXT_VARIATION,
)
from bilqis_mlx.source_adapters.school import live_source_registry


class TeachingOnlyTransitionTests(unittest.TestCase):
    def setUp(self):
        self.program = ScheduleProgram('a' * 64, (
            ScheduleGrade('D', (ScheduleCapability('D.EVENT_OCCURRENCE', 12),),
                          (('D.EVENT_OCCURRENCE',),), 'b' * 64),), False)
        self.school = start_new(self.program, Checkpoint('c' * 64, 'bundles/fixture', 10, True))

    def test_identical_scheduler_projection_preserves_current_work(self):
        state, revised_grade, appended = _profile_transition(
            self.program, self.program, self.school)
        self.assertIs(state, self.school)
        self.assertIsNone(revised_grade)
        self.assertFalse(appended)

    def test_changed_program_identity_still_requires_a_supported_revision(self):
        changed = replace(self.program, program_digest='d' * 64)
        with self.assertRaisesRegex(ValueError, 'FACTORY_SCHEDULE_REVISION_INVALID'):
            _profile_transition(self.program, changed, self.school)

    def test_grade_a_member_context_requires_one_explicit_source_revision(self):
        registry = live_source_registry()
        generator = "bilqis_mlx.grade_a_probe.make_record"
        oracle = "bilqis.mlx.grade-a-record-oracle/v2"
        current = registry.require(generator, oracle).descriptor
        historical = replace(
            current,
            variation_axes=tuple(
                axis for axis in current.variation_axes
                if axis != MEMBER_CONTEXT_VARIATION),
        )
        binding = SimpleNamespace(generator_id=generator, oracle_id=oracle)

        def release(provider):
            return SimpleNamespace(
                execution_plan=SimpleNamespace(capability_map={
                    "A.MEMBER": SimpleNamespace(provider_id=provider.adapter_id),
                }),
                source_bindings=SimpleNamespace(by_capability={
                    "A.MEMBER": binding,
                }),
                source_adapters=(provider,),
            )

        self.assertTrue(_grade_a_member_context_revision_required(
            release(historical), registry))
        self.assertFalse(_grade_a_member_context_revision_required(
            release(current), registry))
        self.assertTrue(_source_presentation_revision_required(
            release(historical), registry))

    def test_grade_a_context_revision_detects_member_fixed_predecessor(self):
        registry = live_source_registry()
        generator = "bilqis_mlx.grade_a_probe.make_record"
        oracle = "bilqis.mlx.grade-a-record-oracle/v2"
        current = registry.require(generator, oracle).descriptor
        member_only = replace(
            current,
            variation_axes=tuple(
                axis for axis in current.variation_axes
                if axis != IRRELEVANT_CONTEXT_VARIATION),
        )
        self.assertIn(MEMBER_CONTEXT_VARIATION, member_only.variation_axes)
        binding = SimpleNamespace(generator_id=generator, oracle_id=oracle)

        def release(provider):
            return SimpleNamespace(
                execution_plan=SimpleNamespace(capability_map={
                    "A.MEMBER": SimpleNamespace(provider_id=provider.adapter_id),
                }),
                source_bindings=SimpleNamespace(by_capability={
                    "A.MEMBER": binding,
                }),
                source_adapters=(provider,),
            )

        self.assertTrue(_grade_a_member_context_revision_required(
            release(member_only), registry))
        self.assertFalse(_grade_a_member_context_revision_required(
            release(current), registry))

    def test_source_revision_history_keeps_valid_epoch_custody_records(self):
        from dataclasses import asdict
        from types import SimpleNamespace
        from bilqis_mlx.learning.mentor_epoch import begin_initial_epoch, reference_checkpoints
        from bilqis_mlx.runtime.release_adoption import _profile_championship_state

        epoch = begin_initial_epoch(student=asdict(self.school.current_student),
            introduced_grade='D', source_graph_sha256='e' * 64, frontier={}, soups={})
        receipt = dict(generation=1, semantic_graph_sha256='e' * 64,
            parameter_shapes={'weight': [3, 4]}, mentor_epoch=epoch)
        successor = SimpleNamespace(release_sha256='f' * 64,
            execution_plan=SimpleNamespace(curriculum_sha256='a' * 64))
        identity, updated, history = _profile_championship_state(
            receipt, None, successor, self.school, self.school, appended=False)
        self.assertEqual(history, [epoch])
        self.assertEqual(updated['active_roles'], {})
        self.assertEqual(updated['active_grade_soups'], {})
        for item in (*history, updated):
            self.assertTrue(reference_checkpoints(item))
        unchanged = {**receipt, 'mentor_epoch': updated, 'championship_epoch_history': history}
        _, _, repeated_history = _profile_championship_state(
            unchanged, None, successor, self.school, self.school, appended=False)
        self.assertEqual(repeated_history, history)


class ExplicitProfileDebtTests(unittest.TestCase):
    def setUp(self):
        self.previous = ScheduleProgram('a' * 64, (
            ScheduleGrade('A', (ScheduleCapability('A.IDENTITY', 12),), (), 'b' * 64),), False)
        self.successor = ScheduleProgram('c' * 64, (*self.previous.grades,
            ScheduleGrade('B', (ScheduleCapability('B.NOT', 12),), (), 'd' * 64)), False)
        self.school = start_new(self.previous, Checkpoint('e' * 64, 'bundles/student', 10, True))

    def test_explicit_debt_admits_a_same_abi_next_grade_without_fabricating_mastery(self):
        state, revised, appended = _profile_transition(
            self.previous, self.successor, self.school, mastery_debt=('A.IDENTITY',))
        self.assertTrue(appended)
        self.assertIsNone(revised)
        self.assertEqual(state.grade, 'B')
        self.assertEqual(state.carried_mastery_debt, ('A.IDENTITY',))
        self.assertEqual(state.current_student, self.school.current_student)
        self.assertEqual(state.champions, {})
        self.assertEqual(
            state.debt_cadence_policy,
            DebtCadencePolicy('A', 'B', 4),
        )

    def test_ordinary_append_still_requires_the_graduated_boundary(self):
        with self.assertRaises(ValueError):
            _profile_transition(self.previous, self.successor, self.school)

    def test_factory_append_retargets_debt_roles_without_grade_letters(self):
        student = Checkpoint('9' * 64, 'bundles/generic-student', 25, True)
        previous = ScheduleProgram('1' * 64, (
            ScheduleGrade('FOUNDATION', (
                ScheduleCapability('foundation.identity', 12),), (), '2' * 64),
            ScheduleGrade('RELATIONS', (
                ScheduleCapability('relations.compose', 12),), (), '3' * 64),
        ), False)
        successor = ScheduleProgram('4' * 64, (*previous.grades,
            ScheduleGrade('WORLD_MODEL', (
                ScheduleCapability('world_model.predict', 12),), (), '5' * 64)),
            False)
        school = replace(
            start_new(previous, student),
            active_grades=('FOUNDATION', 'RELATIONS'), grade_index=1,
            stage='MAIN', queue=('relations.compose',),
            champions={'FOUNDATION': student},
            carried_mastery_debt=('relations.compose',),
            debt_cadence_policy=DebtCadencePolicy(
                'FOUNDATION', 'RELATIONS', 6),
        )

        state, revised, appended = _profile_transition(
            previous, successor, school,
            mastery_debt=('relations.compose',))

        self.assertTrue(appended)
        self.assertIsNone(revised)
        self.assertEqual(state.grade, 'WORLD_MODEL')
        self.assertEqual(
            state.debt_cadence_policy,
            DebtCadencePolicy('RELATIONS', 'WORLD_MODEL', 6),
        )
        self.assertEqual(state.bounded_debt_visits, 0)
        self.assertEqual(state.priority_visits_since_bounded_debt, 0)

    def test_factory_clean_append_clears_stale_debt_roles_without_grade_letters(self):
        student = Checkpoint('8' * 64, 'bundles/generic-graduate', 30, True)
        previous = ScheduleProgram('6' * 64, (
            ScheduleGrade('FOUNDATION', (
                ScheduleCapability('foundation.identity', 12),), (), '7' * 64),
            ScheduleGrade('RELATIONS', (
                ScheduleCapability('relations.compose', 12),), (), '8' * 64),
        ), False)
        successor = ScheduleProgram('9' * 64, (*previous.grades,
            ScheduleGrade('WORLD_MODEL', (
                ScheduleCapability('world_model.predict', 12),), (), 'a' * 64)),
            False)
        school = replace(
            start_new(previous, student),
            active_grades=('FOUNDATION', 'RELATIONS'), grade_index=1,
            stage='AWAITING_NEXT_GRADE', queue=(),
            champions={'FOUNDATION': student, 'RELATIONS': student},
            carried_mastery_debt=(),
            debt_cadence_policy=DebtCadencePolicy(
                'FOUNDATION', 'RELATIONS', 4),
            bounded_debt_visits=7,
            priority_visits_since_bounded_debt=3,
        )

        state, revised, appended = _profile_transition(
            previous, successor, school)

        self.assertTrue(appended)
        self.assertIsNone(revised)
        self.assertEqual(state.grade, 'WORLD_MODEL')
        self.assertIsNone(state.debt_cadence_policy)
        self.assertEqual(state.bounded_debt_visits, 0)
        self.assertEqual(state.priority_visits_since_bounded_debt, 0)


class EarlierGradeExpansionTests(unittest.TestCase):
    def setUp(self):
        student = Checkpoint('f' * 64, 'bundles/student', 42, True)
        self.previous = ScheduleProgram('1' * 64, (
            ScheduleGrade('A', (ScheduleCapability('A.IDENTITY', 12),), (), '2' * 64),
            ScheduleGrade('B', (ScheduleCapability('B.AND', 12), ScheduleCapability('B.IFF', 12)), (), '3' * 64),
            ScheduleGrade('C', (ScheduleCapability('C.COUNT', 12), ScheduleCapability('C.NUMBER', 12)), (), '4' * 64),
        ), False)
        self.successor = ScheduleProgram('5' * 64, (
            self.previous.grades[0],
            ScheduleGrade('B', tuple(ScheduleCapability(cap, 12) for cap in (
                'B.NOT', 'B.AND', 'B.OR', 'B.XOR', 'B.IMPLIES', 'B.IFF', 'B.COMPOSITE', 'B.IDBOOLOPS')), (), '6' * 64),
            self.previous.grades[2],
        ), False)
        base = start_new(self.previous, student)
        self.school = replace(base, active_grades=('A', 'B', 'C'), grade_index=2,
            stage='RECOVERY_1', queue=('C.NUMBER', 'B.AND'), visits=123,
            carried_mastery_debt=('B.AND', 'C.COUNT'),
            frontier_priority_visits=17, bounded_debt_visits=4)

    def test_additive_prior_grade_revision_reenters_frontier_and_adds_debt(self):
        state, revised, appended = _profile_transition(self.previous, self.successor, self.school)
        self.assertFalse(appended)
        self.assertEqual(revised, 'B')
        self.assertEqual((state.grade, state.stage, state.queue),
                         ('C', 'MAIN', ('C.COUNT', 'C.NUMBER')))
        self.assertEqual(state.current_student, self.school.current_student)
        self.assertEqual((state.visits, state.frontier_priority_visits, state.bounded_debt_visits), (123, 17, 4))
        self.assertEqual(state.carried_mastery_debt, ('B.AND', 'C.COUNT', 'B.NOT', 'B.OR', 'B.XOR', 'B.IMPLIES', 'B.COMPOSITE', 'B.IDBOOLOPS'))
        self.assertEqual(state.course_digest, self.successor.digest())
