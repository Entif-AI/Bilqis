"""Human root commands must not accidentally begin optimization."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from bilqis_mlx import cli
from bilqis_mlx.cli import main, ORIGINAL_CHECKPOINT


class OperatorTests(unittest.TestCase):
    def test_worktree_preflight_uses_explicit_source_paths_without_global_mutation(self):
        from bilqis_mlx import cli
        original = cli.LEGACY_ROOT, cli.ORIGINAL_CHECKPOINT
        with tempfile.TemporaryDirectory() as tmp, patch(
                "bilqis_mlx.presentation.operator_cli.command.ROOT", Path(tmp)):
            donor = Path(tmp) / "explicit-donor"
            run = Path(tmp) / "runs" / "aspirant"
            out = io.StringIO()
            with patch("bilqis_mlx.grade_a_manifest.verify_manifest", return_value={
                    "verified_items": 216, "exam_rubric_sha256": "a" * 64}) as verify, \
                    patch("bilqis_mlx.presentation.operator_cli.preflight.assert_headroom", return_value={}), redirect_stdout(out):
                self.assertEqual(main(["train", "--dry-run", "--verify-source", "--run-dir", str(run),
                                       "--legacy-code-root", str(donor)]), 0)
            self.assertEqual(verify.call_args.args[1], donor)
            self.assertEqual(verify.call_args.args[2], donor / "runs" / "primitive-consolidation-v16-triplets" /
                             ORIGINAL_CHECKPOINT.name)
            self.assertEqual((cli.LEGACY_ROOT, cli.ORIGINAL_CHECKPOINT), original)
            self.assertFalse(json.loads(out.getvalue())["neural_training_started_by_this_command"])

    def test_legacy_boolean_preflight_facade_keeps_exact_payload(self):
        from bilqis_mlx import cli
        from bilqis_mlx.compatibility.cli_preflight import (
            legacy_boolean_revision_preflight,
        )

        fields = dict(
            resume=True, boolean_composite=True, boolean_idboolops=False,
            checkpoint_sha256="a" * 64)
        expected = legacy_boolean_revision_preflight(**fields)
        self.assertEqual(
            cli._boolean_revision_preflight(
                Path("/not-used"), Path("/not-used"), **fields), expected)
        self.assertEqual(expected["legacy_boolean_revision_flags"], {
            "composite_requested": True,
            "idboolops_requested": False,
            "authority": "CANONICAL_PROFILE_TEACHING_STAGES",
            "separate_release_enrollment": False,
            "source_student_sha256": "a" * 64,
            "neural_updates": 0,
        })

    def test_legacy_cli_compatibility_facades_keep_exact_payloads(self):
        from bilqis_mlx import cli
        from bilqis_mlx.compatibility.cli_preflight import (
            historical_session_stop,
            legacy_qualification_scope,
        )

        self.assertEqual(cli._qualification_scope(), legacy_qualification_scope())
        self.assertTrue(historical_session_stop("GRADE_A_SESSION_STOPPED"))
        self.assertFalse(historical_session_stop("SCHOOL_SESSION_STOPPED"))

    def test_legacy_grade_b_preflight_defers_next_grade_until_v2_migration(self):
        from bilqis_mlx import cli
        from bilqis_mlx.boolean_composite import build_course as admitted_composite
        from bilqis_mlx.boolean_identification import build_course as admitted_idboolops
        from bilqis_mlx.grade_a_release import accepted_grade_a
        from bilqis_mlx.live_grade_a import live_course as admitted_a
        from bilqis_mlx.live_grade_b import live_course as admitted_b
        manifest = json.loads(cli.GRADE_A_MANIFEST.read_text())
        b_course = admitted_b(admitted_a(accepted_grade_a(manifest)), cli.LEGACY_ROOT)
        b_course = admitted_composite(b_course, cli.LEGACY_ROOT)
        b_course = admitted_idboolops(b_course, cli.LEGACY_ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            saved = {
                "schema": "bilqis.mlx.human-grade-a-trainer/v1",
                "generation": 3, "result": "GRADE_B_MASTERED_AWAITING_GRADE_C",
                "curriculum_mode": b_course.version,
                "school": {"active_grades": ["A", "B"], "grade_index": 1,
                           "course_digest": b_course.digest(),
                           "stage": "AWAITING_NEXT_GRADE", "visits": 4,
                           "current_student": {"sha256": "a" * 64,
                                               "optimizer_step": 204072},
                           "champions": {"A": {}, "B": {}}},
                "teacher": {"events": 10, "strategies": {}}, "last_exam": None,
            }
            (run / "state.json").write_text(json.dumps(saved))
            out = io.StringIO()
            with patch("bilqis_mlx.live_grade_c.REGISTRY_PATH", run / "missing.json"), \
                    patch("bilqis_mlx.grade_c_preflight.qualify",
                          side_effect=AssertionError("unverified C must not qualify")), \
                    patch("bilqis_mlx.presentation.operator_cli.preflight.assert_headroom", return_value={}), \
                    redirect_stdout(out):
                self.assertEqual(main(["train", "--dry-run", "--resume",
                                       "--run-dir", tmp]), 0)
            report = json.loads(out.getvalue())
            self.assertNotIn("next_profile_transition", report)
            self.assertNotIn("next_grade", report)
            self.assertEqual(report["blockers"], [])
            self.assertEqual(
                report["legacy_profile"]["profile"], "FULL_DEFAULT")
            self.assertFalse(report["legacy_profile"]["migration_required"])
            self.assertTrue((run / "state.json").is_file())

    def test_old_grade_b_preflight_requires_profile_migration_not_release_ladder(self):
        from bilqis_mlx import cli
        from bilqis_mlx.grade_a_release import accepted_grade_a
        from bilqis_mlx.live_grade_a import live_course as admitted_a
        from bilqis_mlx.live_grade_b import live_course as admitted_b
        manifest = json.loads(cli.GRADE_A_MANIFEST.read_text())
        b_course = admitted_b(admitted_a(accepted_grade_a(manifest)), cli.LEGACY_ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            saved = {
                "schema": "bilqis.mlx.human-grade-a-trainer/v1",
                "generation": 3, "result": "GRADE_B_MASTERED_AWAITING_GRADE_C",
                "curriculum_mode": b_course.version,
                "school": {"active_grades": ["A", "B"], "grade_index": 1,
                           "course_digest": b_course.digest(),
                           "stage": "AWAITING_NEXT_GRADE", "visits": 4,
                           "current_student": {"sha256": "a" * 64,
                                               "optimizer_step": 204072},
                           "champions": {"A": {}, "B": {}}},
                "teacher": {"events": 10, "strategies": {}}, "last_exam": None,
            }
            (run / "state.json").write_text(json.dumps(saved))
            out = io.StringIO()
            with patch("bilqis_mlx.presentation.operator_cli.preflight.assert_headroom", return_value={}), redirect_stdout(out):
                self.assertEqual(main(["train", "--dry-run", "--resume",
                                       "--run-dir", tmp]), 0)
            report = json.loads(out.getvalue())
        self.assertNotIn("next_profile_transition", report)
        self.assertNotIn("next_grade", report)
        self.assertEqual(
            report["legacy_profile"]["profile"], "FULL_DEFAULT")
        self.assertFalse(report["legacy_profile"]["migration_required"])
        self.assertEqual(report["blockers"], [])

    def test_composite_grade_b_preflight_requires_profile_migration_not_release_ladder(self):
        from bilqis_mlx import cli
        from bilqis_mlx.boolean_composite import build_course as admitted_composite
        from bilqis_mlx.grade_a_release import accepted_grade_a
        from bilqis_mlx.live_grade_a import live_course as admitted_a
        from bilqis_mlx.live_grade_b import live_course as admitted_b
        manifest = json.loads(cli.GRADE_A_MANIFEST.read_text())
        b_course = admitted_b(admitted_a(accepted_grade_a(manifest)), cli.LEGACY_ROOT)
        b_course = admitted_composite(b_course, cli.LEGACY_ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            saved = {
                "schema": "bilqis.mlx.human-grade-a-trainer/v1",
                "generation": 3, "result": "GRADE_B_MASTERED_AWAITING_GRADE_C",
                "curriculum_mode": b_course.version,
                "school": {"active_grades": ["A", "B"], "grade_index": 1,
                           "course_digest": b_course.digest(),
                           "stage": "AWAITING_NEXT_GRADE", "visits": 4,
                           "current_student": {"sha256": "a" * 64,
                                               "optimizer_step": 204072},
                           "champions": {"A": {}, "B": {}}},
                "teacher": {"events": 10, "strategies": {}}, "last_exam": None,
            }
            (run / "state.json").write_text(json.dumps(saved))
            out = io.StringIO()
            with patch("bilqis_mlx.presentation.operator_cli.preflight.assert_headroom", return_value={}), redirect_stdout(out):
                self.assertEqual(main(["train", "--dry-run", "--resume",
                                       "--run-dir", tmp]), 0)
            report = json.loads(out.getvalue())
        self.assertNotIn("next_profile_transition", report)
        self.assertNotIn("next_grade", report)
        self.assertEqual(
            report["legacy_profile"]["profile"], "FULL_DEFAULT")
        self.assertFalse(report["legacy_profile"]["migration_required"])
        self.assertEqual(report["blockers"], [])
