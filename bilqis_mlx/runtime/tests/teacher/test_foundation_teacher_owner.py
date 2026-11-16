"""C16.3 production ownership of the accepted C03 teacher trajectory."""
from __future__ import annotations

import os
import random
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.compatibility import historical_teacher_policy
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.learning_experiment import Settings
from bilqis_mlx.runtime.accepted_teacher_custody import select_accepted_teacher_visit
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.runtime.foundation_teacher_owner import (
    accepted_teacher_trajectory, select_foundation_priority_visit,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import publish_genesis, shape_patch
from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import (
    adaptation, selection_teacher,
)


class FoundationTeacherOwnerTests(unittest.TestCase):
    def test_priority_authority_uses_bootstrapped_teacher_state_not_raw_genesis_sidecar(self):
        owner_module = __import__(
            select_foundation_priority_visit.__module__, fromlist=["*"])
        parent = SimpleNamespace(teacher_state={
            "schema": "bilqis.mlx.bamf-teacher-state/v1",
            "teacher_identity": "1" * 64,
            "teacher_epoch": 0,
            "next_seed": 71,
            "cursor": "GENESIS",
        })
        projected_state = {
            **parent.teacher_state,
            "teacher_identity": "2" * 64,
            "c03_lineage": {"bootstrapped": True},
        }
        projection = SimpleNamespace(teacher_state=projected_state)
        epoch = object()
        authority = SimpleNamespace(
            frontier="frontier", history="history", planning="planning",
            lawful_frontier="lawful-frontier", offers="offers", now=17,
            planning_generation="planning-generation")
        selected = object()
        with patch(
                "bilqis_mlx.runtime.bamf_bundle.admission.load_accepted_generation",
                return_value=parent), patch.object(
                owner_module, "current_foundation_teacher_projection",
                return_value=projection), patch.object(
                owner_module, "restore_teacher_lineage", return_value=epoch), patch.object(
                owner_module, "foundation_teacher_bootstrap",
                return_value=SimpleNamespace(
                    legacy_receipt=None, adaptation=None, prior_region=None)), patch(
                "bilqis_mlx.runtime.priority_authority.issue_foundation_priority_authority",
                return_value=authority) as issue, patch(
                "bilqis_mlx.runtime.accepted_priority_visit.select_accepted_priority_visit",
                return_value=selected):
            result = select_foundation_priority_visit(
                Path("/run"), SimpleNamespace(release=SimpleNamespace(
                    execution_plan=SimpleNamespace(capabilities=()))), "/atlas",
                program="program", school="school")

        self.assertIs(result, selected)
        self.assertIs(issue.call_args.kwargs["teacher_state"], projected_state)
        self.assertNotIn("c03_lineage", parent.teacher_state)

    def test_accepted_visit_owns_next_seed_and_opaque_cursor(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / "run"
            with patch.dict(os.environ, {"BILQIS_DATA_PLANE": str(root / "plane.sqlite3")}), \
                    shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
                publish_genesis(run, run_seed=71)
                parent = load_accepted_generation(run)
                school = SimpleNamespace(
                    stage="MAIN",
                    current_student=SimpleNamespace(
                        sha256=candidate_identity_digest(parent.retained_state)))
                bound, _policy, _metadata = select_accepted_teacher_visit(
                    run, historical_teacher_policy, school, random.Random(71),
                    Settings(), "factory/foundation", {}, "violet",
                    capability_id="C.ADD", total_capabilities=20,
                    legacy_receipt={"teacher": selection_teacher()},
                    adaptation=adaptation(), prior_region="legacy-region")
        trajectory = accepted_teacher_trajectory(bound)
        self.assertEqual(trajectory.next_seed, bound.identity.selection_seed + 1)
        self.assertEqual(trajectory.cursor, bound.identity.visit_id)
        self.assertNotEqual(trajectory.cursor, bound.identity.cursor)


if __name__ == "__main__":
    unittest.main()
