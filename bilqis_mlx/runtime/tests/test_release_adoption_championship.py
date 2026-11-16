"""Championship state at executable-release admission boundaries."""
from dataclasses import asdict, replace
from types import SimpleNamespace
import unittest

from bilqis_mlx.curriculum.scheduler import start_new
from bilqis_mlx.factory.schedule import ScheduleCapability, ScheduleGrade, ScheduleProgram
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.release_adoption import _profile_championship_state


class SemanticAdmissionChampionshipTests(unittest.TestCase):
    def test_new_semantic_epoch_archives_but_does_not_inherit_settled_matchups(self):
        graduate = Checkpoint('c' * 64, 'bundles/graduate', 10, True)
        previous = ScheduleProgram(
            'a' * 64,
            (ScheduleGrade(
                'D', (ScheduleCapability('D.EVENT_OCCURRENCE', 12),), (),
                'b' * 64),),
            False,
        )
        successor_program = ScheduleProgram(
            'd' * 64,
            (*previous.grades, ScheduleGrade(
                'E', (ScheduleCapability('E.NEW', 12),), (), 'e' * 64)),
            False,
        )
        school = start_new(previous, graduate)
        next_state = replace(
            school,
            course_digest=successor_program.digest(),
            active_grades=('D', 'E'),
            grade_index=1,
            stage='MAIN',
            queue=('E.NEW',),
        )
        old_epoch = {
            'settled_matchups': {
                'D.EVENT_OCCURRENCE|a|c': {
                    'capability': 'D.EVENT_OCCURRENCE',
                },
            },
        }
        receipt = {
            'generation': 4,
            'semantic_graph_sha256': '1' * 64,
            'parameter_shapes': {'weight': [3, 4]},
            'mentor_epoch': old_epoch,
            'last_exam': {
                'student_sha256': graduate.sha256,
                'exam_rubric_sha256': '2' * 64,
                'cohort_sha256': '3' * 64,
                'scores': {
                    'D.EVENT_OCCURRENCE': {'correct': 12, 'total': 12},
                },
            },
        }
        predecessor = SimpleNamespace(
            execution_plan=SimpleNamespace(capabilities=(
                SimpleNamespace(capability_id='D.EVENT_OCCURRENCE'),)),
        )
        successor = SimpleNamespace(
            release_sha256='4' * 64,
            execution_plan=SimpleNamespace(
                curriculum_sha256=successor_program.digest()),
        )

        _, epoch, history = _profile_championship_state(
            receipt, predecessor, successor, school, next_state, appended=True)

        self.assertEqual(epoch['settled_matchups'], {})
        self.assertEqual(history[-1]['settled_matchups'], old_epoch['settled_matchups'])
        self.assertEqual(epoch['active_roles'], {})
        self.assertEqual(epoch['active_grade_soups'], {})
        self.assertEqual(epoch['baseline'], asdict(graduate))


if __name__ == '__main__':
    unittest.main()
