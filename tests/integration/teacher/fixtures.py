"""Teacher integration contracts; original evidence and boundaries preserved."""
from contextlib import redirect_stdout
import io
from pathlib import Path
from bilqis_mlx import trainer as storage
from bilqis_mlx.compatibility.live_releases import initial_course
from bilqis_mlx.grade_a_release import accepted_grade_a
from bilqis_mlx.learning.learning_experiment import Settings
from tests.system import test_grade_c_trainer as fixtures
from tests.integration import test_numeric_staircase as staircase_fixtures


class TeacherFixture:
    @classmethod
    def setUpClass(cls):
        if not fixtures.PARENT.is_file():
            raise FileNotFoundError(
                "CAUSAL_TEACHER_PINNED_PARENT_FIXTURE_MISSING:"
                + str(fixtures.PARENT))
        staircase_fixtures.NumericStaircaseTests.setUpClass()
        cls.source_root = fixtures.SOURCE
        cls.grade_a_course = initial_course(
            accepted_grade_a(staircase_fixtures.NumericStaircaseTests.manifest))

    def setUp(self):
        self.fixture=staircase_fixtures.NumericStaircaseTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.mx = self.fixture.mx
        self.course, self.receipt = self.fixture.start()
        with redirect_stdout(io.StringIO()):
            self.receipt, self.executable_release, self.schedule_program = (
                storage._ensure_executable_release(
                    self.fixture.root, self.receipt, self.course,
                    self.grade_a_course, self.source_root, self.fixture.graph))
            school = storage._state_from_json(
                self.receipt["school"], self.schedule_program)
            current_rubric = self.schedule_program.grades[-1].assessment_sha256
            if self.receipt.get("live_rubric_sha256") != current_rubric:
                self.receipt = storage._advance(
                    self.fixture.root,
                    {**self.receipt, "live_rubric_sha256": current_rubric},
                    school)
            self.receipt = storage._migrate_championship_governance(
                self.fixture.root, self.receipt, self.course)

    def visit(self):
        return storage._take_visit(
            self.mx,self.fixture.root,self.receipt,self.fixture.fixture.manifest,
            self.course,self.fixture.fixture.engine,
            self.fixture.params,self.fixture.optimizer,self.fixture.graph,
            steps_per_visit=1,batch_size=6,reserve_gib=0.,
            source_root=self.source_root,
            learning_settings=Settings(probe_each=6,mature_max_loss=2,
                                       introduction_extra_loss=2))

    def resume(self):
        return storage._resume(
            self.fixture.root, self.fixture.fixture.manifest, self.course,
            self.fixture.fixture.policy_sha,
            grade_a_course=self.grade_a_course, source_root=self.source_root,
            admitted_courses={self.course.version: self.course})
