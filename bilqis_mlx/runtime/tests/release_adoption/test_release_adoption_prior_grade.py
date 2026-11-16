"""Earlier-grade executable-profile revision behavior."""
from dataclasses import replace
import unittest

from bilqis_mlx.curriculum.scheduler import start_new
from bilqis_mlx.factory.schedule import ScheduleCapability, ScheduleGrade, ScheduleProgram
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.release_adoption import _profile_transition


class EarlierGradeExpansionTests(unittest.TestCase):
    def setUp(self):
        student = Checkpoint('f' * 64, 'bundles/student', 42, True)
        self.previous = ScheduleProgram('1' * 64, (
            ScheduleGrade('A', (ScheduleCapability('A.IDENTITY', 12),), (), '2' * 64),
            ScheduleGrade('B', (
                ScheduleCapability('B.AND', 12),
                ScheduleCapability('B.IFF', 12),
            ), (), '3' * 64),
            ScheduleGrade('C', (
                ScheduleCapability('C.COUNT', 12),
                ScheduleCapability('C.NUMBER', 12),
            ), (), '4' * 64),
        ), False)
        self.successor = ScheduleProgram('5' * 64, (
            self.previous.grades[0],
            ScheduleGrade('B', tuple(ScheduleCapability(cap, 12) for cap in (
                'B.NOT', 'B.AND', 'B.OR', 'B.XOR', 'B.IMPLIES', 'B.IFF',
                'B.COMPOSITE', 'B.IDBOOLOPS')), (), '6' * 64),
            self.previous.grades[2],
        ), False)
        base = start_new(self.previous, student)
        self.school = replace(
            base, active_grades=('A', 'B', 'C'), grade_index=2,
            stage='RECOVERY_1', queue=('C.NUMBER', 'B.AND'), visits=123,
            carried_mastery_debt=('B.AND', 'C.COUNT'),
            frontier_priority_visits=17, bounded_debt_visits=4)

    def test_additive_prior_grade_revision_reenters_frontier_and_adds_debt(self):
        state, revised, appended = _profile_transition(
            self.previous, self.successor, self.school)
        self.assertFalse(appended)
        self.assertEqual(revised, 'B')
        self.assertEqual((state.grade, state.stage, state.queue),
                         ('C', 'MAIN', ('C.COUNT', 'C.NUMBER')))
        self.assertEqual(state.current_student, self.school.current_student)
        self.assertEqual(
            (state.visits, state.frontier_priority_visits,
             state.bounded_debt_visits), (123, 17, 4))
        self.assertEqual(
            state.carried_mastery_debt,
            ('B.AND', 'C.COUNT', 'B.NOT', 'B.OR', 'B.XOR', 'B.IMPLIES',
             'B.COMPOSITE', 'B.IDBOOLOPS'))
        self.assertEqual(state.course_digest, self.successor.digest())
