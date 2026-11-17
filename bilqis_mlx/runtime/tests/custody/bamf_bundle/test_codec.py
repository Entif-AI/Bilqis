"""B13.1 exact bundle and historical-v1 codec witnesses."""
from __future__ import annotations

import os
import hashlib
import json
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import mlx.core as mx
import mlx.optimizers as optim
import numpy as np

import bilqis_mlx.runtime.bamf_bundle.codec as codec
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError, ErrorBus
from bilqis_mlx.diagnostics.learning_health import STATE_SCHEMA, project_learning_health
from bilqis_mlx.learning.atlas_engram import MotifKey, MotifManifest, MotifSlot
from bilqis_mlx.learning.atlas_engram_transaction import MotifAllocationSnapshot
from bilqis_mlx.learning.capability_championship_state import (
    active_checkpoint_references, championship_epoch_identity,
    compact_championship_state,
)
from bilqis_mlx.runtime.bamf_bundle import load_bamf_bundle, save_bamf_bundle
from bilqis_mlx.runtime.baseline.lifecycle import (
    BaselineComparisonIdentity, BaselineLedger, BaselineLifecycleState,
    _issue_factory_baseline_transition, apply_factory_baseline_transition,
)
from bilqis_mlx.runtime.plasticity_escape import (
    CertifiedSurfaceDebt, CertifiedSurfaceId, PlasticityActivationReason,
    PlasticityEscapeState,
)

from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    NAME, accepted_state, candidate, next_accepted_step, parent_state,
    rewrite_motif_bundle_fixture, shape_patch,
)


class BamfBundleCodecTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def test_real_b12_retained_state_round_trips_with_100gib_default(self):
        retained = accepted_state(parent_state())
        source = candidate(retained)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom") as reserve:
            manifest = save_bamf_bundle(source, self.root / "bundle")
            loaded = load_bamf_bundle(
                self.root / "bundle", expected_manifest_sha256=manifest["manifest_sha256"])
        self.assertEqual(loaded.retained_state.optimizer_step, retained.optimizer_step)
        self.assertEqual(loaded.retained_state.policy, retained.policy)
        self.assertEqual(loaded.retained_state.allocations, retained.allocations)
        self.assertEqual(loaded.teacher_state["next_seed"], 42)
        self.assertEqual(loaded.correction_frontier["correction_generation"], 4)
        np.testing.assert_array_equal(
            np.asarray(loaded.retained_state.optimizer.parameters[NAME]),
            np.asarray(retained.optimizer.parameters[NAME]))
        np.testing.assert_array_equal(
            np.asarray(loaded.retained_state.optimizer.update_counts[NAME]),
            np.asarray(retained.optimizer.update_counts[NAME]))
        self.assertEqual(reserve.call_args.kwargs["reserve_gib"], 100.0)

        uninterrupted = next_accepted_step(retained)
        resumed = next_accepted_step(loaded.retained_state, loaded.extents)
        self.assertEqual(resumed.optimizer_step, uninterrupted.optimizer_step)
        self.assertEqual(resumed.policy, uninterrupted.policy)
        np.testing.assert_array_equal(
            np.asarray(resumed.optimizer.parameters[NAME]),
            np.asarray(uninterrupted.optimizer.parameters[NAME]))
        np.testing.assert_array_equal(
            np.asarray(resumed.optimizer.update_counts[NAME]),
            np.asarray(uninterrupted.optimizer.update_counts[NAME]))

        expected = {
            "optimizer_step": uninterrupted.optimizer_step,
            "parameters_sha256": hashlib.sha256(
                np.asarray(uninterrupted.optimizer.parameters[NAME]).tobytes()).hexdigest(),
            "counts_sha256": hashlib.sha256(
                np.asarray(uninterrupted.optimizer.update_counts[NAME]).tobytes()).hexdigest(),
            "policy": uninterrupted.policy.to_record(),
        }
        script = "\n".join((
            "import hashlib,json,sys,numpy as np",
            "from bilqis_mlx.runtime.bamf_bundle import load_bamf_bundle",
            "from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import NAME,next_accepted_step,shape_patch",
            "with shape_patch(): student=load_bamf_bundle(sys.argv[1])",
            "state=next_accepted_step(student.retained_state, student.extents)",
            "result={'optimizer_step':state.optimizer_step,'parameters_sha256':hashlib.sha256(np.asarray(state.optimizer.parameters[NAME]).tobytes()).hexdigest(),'counts_sha256':hashlib.sha256(np.asarray(state.optimizer.update_counts[NAME]).tobytes()).hexdigest(),'policy':state.policy.to_record()}",
            "print(json.dumps(result,sort_keys=True))",
        ))
        completed = subprocess.run(
            [sys.executable, "-c", script, str(self.root / "bundle")],
            check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(completed.stdout), expected)

    def test_c05_baseline_evidence_round_trips_exactly_through_cold_custody(self):
        identity = BaselineComparisonIdentity(
            "B.IDBOOLOPS", "1" * 64, "2" * 64, "3" * 64, "4" * 64,
            "5" * 64, "6" * 64, None, "7" * 64, "8" * 64, "9" * 64,
            "FOUNDATION_ACQUISITION")
        empty = BaselineLedger.empty()
        transition = _issue_factory_baseline_transition(
            identity, run_id="fixture-run", accepted_generation=1,
            accepted_parent_manifest_sha256="a" * 64,
            accepted_candidate_sha256="b" * 64,
            decision_evidence_sha256="c" * 64,
            parent_ledger_sha256=empty.digest)
        ledger = apply_factory_baseline_transition(empty, transition)
        source = replace(
            candidate(parent_state(), generation=1, parent="a" * 64),
            baseline_evidence=ledger.to_record())
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest = save_bamf_bundle(
                source, self.root / "baseline-bundle", reserve_gib=0.)
            loaded = load_bamf_bundle(
                self.root / "baseline-bundle",
                expected_manifest_sha256=manifest["manifest_sha256"])
        restored = BaselineLedger.from_optional_record(loaded.baseline_evidence)
        self.assertEqual(restored.digest, ledger.digest)
        self.assertIs(
            restored.state_for(identity), BaselineLifecycleState.BASELINE_ESTABLISHED)

    def test_learning_health_state_round_trips_exactly_through_cold_custody(self):
        health = project_learning_health({
            "capability_id": "future:capability", "grade_id": "future:grade",
            "retention_policy_sha256": "1" * 64,
            "fixed_cohort_sha256": "2" * 64,
            "rubric_sha256": "3" * 64, "source_sha256": "4" * 64,
            "target": {"state": "MEASURED", "before": 2, "after": 4, "total": 5},
        }, accepted=True)
        surface = CertifiedSurfaceId(
            "certification:future-surface", "future:capability",
            "5" * 64, "6" * 64, "3" * 64, "7" * 64, "4" * 64, "2" * 64)
        plasticity = PlasticityEscapeState(
            "7" * 64, "future:capability", True,
            (PlasticityActivationReason.LOCAL_STARVATION,), 32, 24,
            (CertifiedSurfaceDebt(surface, 3, 5, 5),), (), 17)
        state = {
            "schema": STATE_SCHEMA, "coverage_state": "PARTIAL",
            "by_capability": {"future:capability": health},
            "certified_surfaces": [],
            "plasticity_escape": plasticity.to_record(),
        }
        source = replace(
            candidate(parent_state(), generation=1, parent="a" * 64),
            learning_health_state=state)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest = save_bamf_bundle(
                source, self.root / "health-bundle", reserve_gib=0.)
            loaded = load_bamf_bundle(
                self.root / "health-bundle",
                expected_manifest_sha256=manifest["manifest_sha256"])
        self.assertEqual(
            loaded.learning_health_state,
            json.loads(json.dumps(state, sort_keys=True)))

    def test_capability_championship_state_round_trips_with_only_active_title_custody(self):
        identity = championship_epoch_identity(
            factory_release_sha256="1" * 64,
            semantic_catalog_sha256="2" * 64,
            curriculum_sha256="3" * 64,
            capability_groups=(("future:capability", "future:group"),),
            fixed_cohort_sha256="4" * 64,
            rubric_sha256="5" * 64,
            scope_sha256="6" * 64,
            source_sha256="7" * 64,
            policy_sha256="8" * 64,
            topology_sha256="9" * 64,
            extents_sha256="a" * 64,
            semantic_abi={"schema": "fixture"},
        )
        pointer = {
            "sha256": "b" * 64,
            "filename": "bamf-generations/1",
            "optimizer_step": 7,
            "model_and_native_adamw": True,
        }
        state = compact_championship_state({
            "active_roles": {
                "future:capability": {
                    "capability": "future:capability",
                    "capability_group": "future:group",
                    "checkpoint_origin_group": "future:group",
                    "complete_solver_provenance": {
                        "weight_sha256": "b" * 64,
                        "generation_digest": "c" * 64,
                        "solver_contracts": ["d" * 64],
                    },
                    "checkpoint": pointer,
                    "correct": 10,
                    "total": 10,
                    "championship_qualification_correct": 10,
                    "championship_qualification_total": 10,
                    "surviving_battery": [],
                },
            },
            "settled_matchups": {},
        }, identity)
        source = replace(
            candidate(parent_state(), generation=1, parent="a" * 64),
            championship_state=state)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest = save_bamf_bundle(
                source, self.root / "championship-bundle", reserve_gib=0.)
            loaded = load_bamf_bundle(
                self.root / "championship-bundle",
                expected_manifest_sha256=manifest["manifest_sha256"])
        self.assertEqual(
            loaded.championship_state,
            json.loads(json.dumps(state, sort_keys=True)))
        self.assertEqual(
            active_checkpoint_references(loaded.championship_state),
            (pointer,))

    def test_authenticated_non_genesis_motif_state_round_trips_and_resumes(self):
        parent = parent_state()
        key = MotifKey(
            "STRUCTURAL", "b" * 64, "fixture:frame", 1, (), "f" * 64,
            "fixture:scope")
        allocations = MotifAllocationSnapshot(
            MotifManifest("b" * 64, (MotifSlot(0, key),)),
            ((key.digest, 3),),
        )
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest = save_bamf_bundle(candidate(parent), self.root / "motif-bundle")
            manifest = rewrite_motif_bundle_fixture(
                self.root / "motif-bundle", manifest, allocations)
            loaded = load_bamf_bundle(
                self.root / "motif-bundle",
                expected_manifest_sha256=manifest["manifest_sha256"])
        self.assertEqual(loaded.retained_state.allocations, allocations)
        resumed = next_accepted_step(loaded.retained_state, loaded.extents)
        self.assertEqual(resumed.allocations, allocations)
        self.assertEqual(resumed.optimizer_step, parent.optimizer_step + 1)

    def test_corrupt_or_inconsistent_sidecar_fails_before_tensor_load(self):
        source = candidate(parent_state())
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            save_bamf_bundle(source, self.root / "bundle")
        sidecar = self.root / "bundle" / "correction-frontier.json"
        sidecar.write_text(sidecar.read_text().replace(
            '"correction_generation":4', '"correction_generation":5'))
        with patch.object(codec._mlx_checkpoint, "load_bamf_state_payload") as tensor_load:
            with self.assertRaises(BilqisError) as caught:
                load_bamf_bundle(self.root / "bundle")
        tensor_load.assert_not_called()
        self.assertEqual(
            ErrorBus.report(caught.exception).context["reason"],
            "DATA_PLANE_BUNDLE_PAYLOAD_DRIFT")
        wrong = replace(source, correction_frontier={
            **source.correction_frontier, "correction_generation": 5})
        with patch.object(codec._mlx_checkpoint, "save_bamf_state_payload") as tensor_save:
            with self.assertRaises(BilqisError):
                save_bamf_bundle(wrong, self.root / "rejected")
        tensor_save.assert_not_called()

    def test_historical_v1_reads_but_cannot_be_coerced_to_v2(self):
        parameters = {"p": mx.array([1., 2.], dtype=mx.float32)}
        optimizer = optim.AdamW(learning_rate=.001, bias_correction=True)
        optimizer.apply_gradients({"p": mx.ones((2,), dtype=mx.float32)}, parameters)
        legacy = self.root / "legacy"
        mlx_checkpoint.save_new_bundle(
            legacy, parameters, optimizer, source_digest="a" * 64, reserve_gib=0.0)
        before = (legacy / "manifest.json").read_bytes()
        restored, _, manifest = mlx_checkpoint.load_bundle(legacy)
        self.assertEqual(list(restored), ["p"])
        self.assertEqual(manifest["schema"], mlx_checkpoint.SCHEMA)
        with patch.object(codec._mlx_checkpoint, "load_bamf_state_payload") as tensor_load:
            with self.assertRaises(BilqisError):
                load_bamf_bundle(legacy)
        tensor_load.assert_not_called()
        self.assertEqual((legacy / "manifest.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
