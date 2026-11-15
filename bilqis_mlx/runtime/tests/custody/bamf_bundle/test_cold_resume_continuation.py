"""Disposable B13.2 cold-resume and uninterrupted numerical diagnostics.

The synthetic objective verifies B12/AdamW persistence and B13 pointer/lock
behavior. It is not source-qualified Factory or live B11 trainer acceptance.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

import numpy as np
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import (
    load_bamf_generation, publish_bamf_generation, save_bamf_bundle,
)
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    require_accepted_execution_cache,
)
from bilqis_mlx.runtime.bamf_bundle.records import SIDECARS
from bilqis_mlx.runtime.atlas_model_forward import _source_producer

from bilqis_mlx.runtime.tests.custody.bamf_bundle.cold_resume_probe import (
    continue_generation, retained_digest,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, publish_candidate, shape_patch,
)

PROBE = ("bilqis_mlx.runtime.tests.custody.bamf_bundle.cold_resume_probe")
REPOSITORY_ROOT = Path(__file__).resolve().parents[5]


class BamfColdResumeContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def publish(self, source):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_candidate(self.run, source)

    @staticmethod
    def in_memory_student(source, pointer):
        """Keep the just-published fixture in memory without loading it back."""
        from dataclasses import replace
        from bilqis_mlx.learning.atlas_candidate import CandidateCustodyIdentity
        from bilqis_mlx.runtime.bamf_bundle.records import (
            CompleteStudent, sidecar_records,
        )

        records = sidecar_records(source)
        retained = replace(
            source.retained_state,
            custody=CandidateCustodyIdentity(
                source.run_id, source.generation, pointer["manifest_sha256"],
                source.topology.digest, source.extents.digest))
        return CompleteStudent(
            source.run_id, source.generation, source.parent_manifest_sha256,
            source.implementation_sha256, source.topology, source.extents,
            retained, source.optimizer_hyperparameters, source.provenance,
            source.semantic_abi, source.compiler_features, source.correction_frontier,
            source.teacher_state, source.evaluation_contract, source.transition,
            tuple(records["outbox"]), source.run_identity)

    def probe(self, run=None):
        """Cold resume in a clean process and return its receipt."""
        target = Path(run or self.run)
        process = subprocess.run(
            [sys.executable, "-m", PROBE, str(target)],
            cwd=str(REPOSITORY_ROOT), capture_output=True, text=True,
            env=dict(os.environ), timeout=300)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout.strip().splitlines()[-1])

    def test_cold_resume_continues_the_next_controlled_optimizer_step(self):
        first = self.publish(candidate(parent_state()))
        with shape_patch():
            student = load_bamf_generation(self.run / "bamf-state.json")
            initial = student.retained_state
        receipt = self.probe()
        self.assertEqual(receipt["generation"], 0)
        self.assertEqual(receipt["manifest_sha256"], first["manifest_sha256"])
        self.assertEqual(receipt["state_digest"], retained_digest(initial))
        self.assertEqual(receipt["teacher_state"]["teacher_identity"],
                         student.provenance.teacher_identity)
        self.assertEqual(receipt["optimizer_step"], initial.optimizer_step)
        self.assertEqual(receipt["successor_optimizer_step"],
                         initial.optimizer_step + 1)
        counts = receipt["successor_update_counts"]["identity.bank.0"]
        # The disposable execution fixture reports row 0 only. Row 1 must
        # not advance merely because B01 declares it in the same tensor.
        self.assertEqual(counts, [1, 0])
        self.assertEqual(receipt["published"]["generation"], 1)
        self.assertEqual(
            receipt["published"]["parent_manifest_sha256"], first["manifest_sha256"])

    def test_cold_resumed_generation_is_the_published_generation(self):
        first = self.publish(candidate(parent_state()))
        self.probe()
        pointer = json.loads((self.run / "bamf-state.json").read_text())
        self.assertEqual(pointer["generation"], 1)
        self.assertEqual(pointer["parent_manifest_sha256"], first["manifest_sha256"])
        with shape_patch():
            student = load_bamf_generation(self.run / "bamf-state.json")
        self.assertEqual(student.generation, 1)
        self.assertEqual(student.retained_state.optimizer_step, 1)
        self.assertEqual(
            [int(value) for value in
             np.asarray(student.retained_state.optimizer.update_counts["identity.bank.0"])],
            [1, 0])

    def test_synthetic_direct_save_load_cannot_satisfy_acceptance(self):
        initial = parent_state()
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            save_bamf_bundle(candidate(initial), self.root / "unpublished")
        self.assertFalse((self.root / "unpublished" / "bamf-state.json").exists())
        with self.assertRaises(BilqisError):
            load_bamf_generation(self.root / "unpublished" / "bamf-state.json")
        process = subprocess.run(
            [sys.executable, "-m", PROBE, str(self.root / "unpublished")],
            cwd=str(REPOSITORY_ROOT), capture_output=True, text=True,
            env=dict(os.environ), timeout=300)
        self.assertNotEqual(process.returncode, 0)

    def test_uninterrupted_and_cold_continuation_publish_the_same_successor(self):
        self.publish(candidate(parent_state()))
        second = self.root / "uninterrupted"
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            from bilqis_mlx.runtime.bamf_bundle import publish_initial_generation
            from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
                genesis_preparation,
            )
            prepared = genesis_preparation()
            held_pointer = publish_initial_generation(
                second, prepared, reserve_gib=0.)
            held = self.in_memory_student(prepared.candidate, held_pointer)
        with patch(
                "bilqis_mlx.runtime.tests.custody.bamf_bundle.cold_resume_probe."
                "load_accepted_generation",
                side_effect=AssertionError("uninterrupted arm reloaded")), \
                patch(
                    "bilqis_mlx.runtime.bamf_bundle.admission.load_accepted_generation",
                    side_effect=AssertionError("uninterrupted arm reloaded")), \
                patch(
                    "bilqis_mlx.runtime.bamf_bundle.load_bamf_generation",
                    side_effect=AssertionError("uninterrupted arm reloaded")):
            with shape_patch():
                admission._published_in_memory_identity(second, held)
            uninterrupted = continue_generation(
                second, student=held, pointer=held_pointer)
        cold = self.probe()
        self.assertEqual(
            cold["run_seed"], prepared.candidate.run_identity.run_seed)
        self.assertEqual(cold["published"]["manifest_sha256"],
                         uninterrupted["published"]["manifest_sha256"])
        self.assertEqual(cold["successor_digest"], uninterrupted["successor_digest"])
        self.assertEqual(cold["successor_update_counts"],
                         uninterrupted["successor_update_counts"])
        self.assertEqual(cold["successor_proof_digests"],
                         uninterrupted["successor_proof_digests"])
        self.assertEqual(cold["decision"]["decision"],
                         uninterrupted["decision"]["decision"])
        self.assertEqual(cold["decision"]["decision_sha256"],
                         uninterrupted["decision"]["decision_sha256"])

    def test_live_loss_bearing_path_requires_gradient_execution_owner(self):
        self.publish(candidate(parent_state()))
        with shape_patch():
            with self.assertRaises(BilqisError) as failure:
                admission.admit_candidate_step(
                    self.run, {}, loss_bearing_target=True,
                    teacher_hparams=None, max_norm=1.)
        self.assertEqual(failure.exception.context["reason"],
                         "B11_GRADIENT_EXECUTION_REQUIRED")

    def test_factory_teacher_source_next_visit_survives_cold_owner_readback(self):
        """Check persisted next-visit identity with disposable source evidence."""
        import copy
        import random
        from dataclasses import asdict

        from bilqis_mlx.compatibility import historical_teacher_policy as engine
        from bilqis_mlx.curriculum.scheduler import next_capability, start_new
        from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
        from bilqis_mlx.factory.tests.test_teaching import closed_source_fixture
        from bilqis_mlx.learning.champions import Checkpoint
        from bilqis_mlx.learning.teacher_strategy_population import BAMF_SUCCESSOR_SELECTION
        from bilqis_mlx.learning.tests.test_teacher_vnext_replay import _teacher
        from bilqis_mlx.runtime import admission as factory_admission, state
        from bilqis_mlx.runtime.source_execution import SourceExecutionContext
        from bilqis_mlx.runtime.teacher_policy_selection import select_visit_policy

        _, graph, sources, answers, release = closed_source_fixture()
        release_file = factory_admission._persist_executable_factory_release(
            self.root, release)
        program = schedule_program_from_executable_release(release)
        school = start_new(
            program, Checkpoint("a" * 64, "bundles/fixture", 0, True))
        teacher, _, _ = _teacher()
        teacher["selection_contract"] = BAMF_SUCCESSOR_SELECTION
        teacher["events"] = 100
        teacher["global_stats"] = {
            key: {"trials": 10, "reward_sum": index, "reward_ema": index}
            for index, key in enumerate(teacher["strategies"])
        }
        teacher["grade_stats"] = {}
        receipt = {
            "run_id": "next-visit-fixture",
            "generation": 7,
            "school": asdict(school),
            "teacher": teacher,
            "factory_release_sha256": release.release_sha256,
            "factory_release_file": release_file,
            "curriculum_mode": "fixture",
            "numeric_maximum": 7,
        }

        def evidence(active_release, active_receipt, active_teacher):
            active_program = schedule_program_from_executable_release(active_release)
            active_school = state._state_from_json(
                active_receipt["school"], active_program)
            capability = next_capability(active_school)
            self.assertIsNotNone(capability)
            seed = state._seed(active_receipt, capability=capability)
            context = SourceExecutionContext(
                active_release, graph, None, sources, answers)
            rows = context.draw_rows(seed=seed, capability=capability, each=2)
            policy_key, policy, metadata = select_visit_policy(
                engine, active_teacher, capability, active_school,
                random.Random(seed), None,
                f"{active_receipt['curriculum_mode']}/{active_receipt['numeric_maximum']}",
                None, capability.split(".", 1)[0],
                len(active_program.grades[0].capabilities))
            return {
                "release": active_release.release_sha256,
                "capability": capability,
                "seed": seed,
                "rows": tuple(row["id"] for row in rows),
                "policy_key": policy_key,
                "policy": policy,
                "selection_reason": metadata["selection_reason"],
            }

        uninterrupted = evidence(release, copy.deepcopy(receipt), copy.deepcopy(teacher))
        cold_receipt = json.loads(json.dumps(receipt))
        cold_release = factory_admission._read_executable_factory_release_artifact(
            self.root, cold_receipt)
        self.assertIsNot(cold_release, release)
        cold = evidence(cold_release, cold_receipt, json.loads(json.dumps(teacher)))
        self.assertEqual(cold, uninterrupted)

    def test_cold_continuation_reissues_cache_and_rejects_stale_or_corrupt_cache(self):
        initial = parent_state()
        absent_run = self.root / "cache-absent"
        stale_run = self.root / "cache-stale"
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_candidate(absent_run, candidate(initial))
            pointer = publish_candidate(stale_run, candidate(initial))
            stale_cache = admission.bind_accepted_execution_cache(stale_run)

        bundle = stale_run / pointer["bundle"]
        manifest = json.loads((bundle / "manifest.json").read_text())
        self.assertEqual(set(manifest["sidecars"]), set(SIDECARS))
        self.assertFalse(any(
            "cache" in binding["filename"]
            for binding in manifest["sidecars"].values()))

        absent = self.probe(absent_run)
        stale = self.probe(stale_run)
        with shape_patch():
            fresh_cache = admission.bind_accepted_execution_cache(stale_run)

        self.assertEqual(stale["successor_digest"], absent["successor_digest"])
        self.assertEqual(stale["successor_optimizer_step"],
                         absent["successor_optimizer_step"])
        self.assertEqual(stale["successor_update_counts"],
                         absent["successor_update_counts"])
        self.assertEqual(stale["decision"]["decision_sha256"],
                         absent["decision"]["decision_sha256"])
        self.assertEqual(stale_cache.generation, 0)
        self.assertEqual(fresh_cache.generation, 1)
        self.assertNotEqual(stale_cache.accepted_manifest_sha256,
                            fresh_cache.accepted_manifest_sha256)
        self.assertNotEqual(stale_cache.generation_binding,
                            fresh_cache.generation_binding)
        with shape_patch(), self.assertRaises(BilqisError) as mismatch:
            _source_producer(
                None, None, fresh_cache.generation_binding, stale_cache)
        self.assertEqual(mismatch.exception.context["reason"],
                         "B13_EXECUTION_CACHE_STALE")

        object.__setattr__(stale_cache, "generation_binding", "corrupt")
        with shape_patch(), self.assertRaises(BilqisError):
            require_accepted_execution_cache(stale_cache)

    def test_cold_resume_refuses_a_generation_without_published_custody(self):
        process = subprocess.run(
            [sys.executable, "-m", PROBE, str(self.root / "absent")],
            cwd=str(REPOSITORY_ROOT), capture_output=True, text=True,
            env=dict(os.environ), timeout=300)
        self.assertNotEqual(process.returncode, 0)


if __name__ == "__main__":
    unittest.main()
