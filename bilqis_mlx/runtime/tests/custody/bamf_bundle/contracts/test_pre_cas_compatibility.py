"""Positive cold read of a bundle emitted by the pinned pre-CAS B13 writer."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

import numpy as np

import bilqis_mlx.runtime.bamf_bundle.codec as codec
import bilqis_mlx.runtime.bamf_bundle.publication as publication
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.data_plane import DataPlane, data_plane
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import (
    load_bamf_generation, publish_bamf_generation,
)
from bilqis_mlx.runtime.bamf_bundle.codec import save_bamf_bundle
from bilqis_mlx.runtime.bamf_bundle.records import (
    BAMF_POINTER_SCHEMA, OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
    canonical, validate_sidecars,
)
from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
    parent_acceptance_anchor_from_manifest,
)
from bilqis_mlx.runtime.tests.custody.data_plane.base import DataPlaneCase, historical_module
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    acceptance, accepted_state, candidate, next_accepted_step, parent_state,
    publish_candidate, retention_decision, shape_patch,
)

PRE_CAS = "dfc0c7586c23b6477c08d4db486ade3deeb79fae"
WRITER_SHA256 = "01e66fcbe15802615c3557a2a4b99c0fb75a37d64fe3d61ee30bf56d1301fcdc"
LEGACY_CAS = "deaa8b9dbd277993f884abeea7413f9cb799d945"
HISTORICAL_SIDECARS = MappingProxyType({
    "semantic_abi": "semantic-abi.json",
    "motif_allocation": "motif-allocation.json",
    "plasticity_policy": "plasticity-policy.json",
    "compiler_features": "compiler-features.json",
    "correction_frontier": "correction-frontier.json",
    "teacher_state": "teacher-state.json",
    "evaluation_contract": "evaluation-contract.json",
    "outbox": "outbox.json",
})


def bind_historical_sidecar_contract(writer):
    """Freeze codec dependencies that were module globals at the pinned commit."""
    current_records = writer.sidecar_records

    def historical_records(candidate):
        records = current_records(candidate)
        return {name: records[name] for name in HISTORICAL_SIDECARS}

    def historical_validation(extents, provenance, records):
        modern = dict(records)
        modern["step_proofs"] = {
            "schema": "bilqis.mlx.bamf-step-proofs/v1", "proofs": []}
        return validate_sidecars(extents, provenance, modern)

    writer.SIDECARS = HISTORICAL_SIDECARS
    writer.sidecar_records = historical_records
    writer.validate_sidecars = historical_validation
    return writer



def numerical_observation(student):
    state = student.retained_state
    arrays = {}
    for field in ("parameters", "m", "v", "update_counts"):
        for name, value in getattr(state.optimizer, field).items():
            array = np.asarray(value)
            arrays[field + ":" + name] = [str(array.dtype), list(array.shape),
                                         hashlib.sha256(array.tobytes()).hexdigest()]
    return {"arrays": arrays, "step": state.optimizer_step,
            "policy": state.policy.to_record(), "teacher": dict(student.teacher_state),
            "hyperparameters": json.loads(json.dumps(asdict(student.optimizer_hyperparameters)))}


class PreCasCompatibilityTests(DataPlaneCase):
    def setUp(self):
        super().setUp()
        from bilqis_mlx.learning.atlas_candidate import CandidateState
        from bilqis_mlx.learning._retention._atlas_candidate.identity import LEGACY_IDENTITY_SCHEME
        # Pinned old writers consume historical candidates, not raw-v2 candidates.
        historical_state = lambda *a, **k: CandidateState(
            *a, **k, identity_scheme=LEGACY_IDENTITY_SCHEME)
        for target, options in (
                ('bilqis_mlx.runtime.bamf_bundle.genesis.preparation.CandidateState',
                 {'side_effect': historical_state}),
                ('bilqis_mlx.learning._atlas_candidate.transaction.RAW_IDENTITY_SCHEME',
                 {'new': LEGACY_IDENTITY_SCHEME})):
            control = patch(target, **options)
            control.start()
            self.addCleanup(control.stop)

    def test_legacy_published_cas_cold_read_detaches_surviving_descriptor(self):
        writer = bind_historical_sidecar_contract(historical_module(
            self.root, LEGACY_CAS, "bilqis_mlx/runtime/_custody/bamf_bundle/codec.py",
            "bilqis_mlx.runtime.bamf_bundle.legacy_cas_fixture",
            "d92258e08b398a839ac23f73491abc36c11ee29795021da1e8aba39e040f398b"))
        adopter = historical_module(
            self.root, LEGACY_CAS, "bilqis_mlx/_data_plane/file_objects.py",
            "bilqis_mlx._data_plane.legacy_cas_fixture",
            "bd0ac8d7c8488af69e92a837530c129f9d8df7ee9a525de4627f865c8cb218b1")
        run, descriptors = self.root / "legacy-cas-run", []
        source = candidate(parent_state())
        save = mlx_checkpoint.save_bamf_state_payload

        def retained_descriptor(path, *args, **kwargs):
            record = save(path, *args, **kwargs)
            descriptors.append(Path(path).open("r+b"))
            return record

        try:
            bundle = run / "historical-bundle"
            with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), \
                    patch.object(DataPlane, "adopt_file_object", adopter.DataPlaneFileObjectMixin.adopt_file_object), \
                    patch.object(mlx_checkpoint, "save_bamf_state_payload", side_effect=retained_descriptor):
                manifest = writer.save_bamf_bundle(source, bundle, reserve_gib=0.)
            with shape_patch():
                expected = numerical_observation(writer.load_bamf_bundle(bundle))
            before = {path.name: path.read_bytes() for path in bundle.iterdir()}
            digest = json.loads(before["manifest.json"])["tensors"]["object_sha256"]
            plane = data_plane()
            target = plane.require_file_object(digest)
            original_inode = target.stat().st_ino
            self.assertFalse(plane.owns_file_object(digest))
            with shape_patch():
                with patch.object(codec, "assert_headroom", side_effect=RuntimeError("reserve")):
                    with self.assertRaisesRegex(RuntimeError, "reserve"):
                        codec.load_bamf_bundle(
                            bundle, expected_manifest_sha256=manifest["manifest_sha256"])
                self.assertEqual(target.stat().st_ino, original_inode)
                self.assertFalse(plane.owns_file_object(digest))
                loaded = codec.load_bamf_bundle(
                    bundle, expected_manifest_sha256=manifest["manifest_sha256"])
                self.assertTrue(plane.owns_file_object(digest))
                self.assertNotEqual(target.stat().st_ino, original_inode)
                descriptors[0].seek(0)
                descriptors[0].write(b"old caller mutation")
                descriptors[0].flush()
                self.assertEqual(numerical_observation(loaded), expected)
                self.assertEqual(
                    numerical_observation(codec.load_bamf_bundle(
                        bundle, expected_manifest_sha256=manifest["manifest_sha256"])),
                    expected)
            self.assertEqual({path.name: path.read_bytes() for path in bundle.iterdir()}, before)
        finally:
            for descriptor in descriptors:
                descriptor.close()

    def test_pinned_old_writer_bundle_cold_loads_without_rewriting(self):
        repository = Path(__file__).resolve().parents[5]
        source = subprocess.run(
            ["git", "show", PRE_CAS + ":bilqis_mlx/runtime/_custody/bamf_bundle/codec.py"],
            cwd=repository, check=True, capture_output=True).stdout
        self.assertEqual(hashlib.sha256(source).hexdigest(), WRITER_SHA256)
        writer_path = self.root / "pre_cas_codec.py"
        writer_path.write_bytes(source)
        spec = importlib.util.spec_from_file_location(
            "bilqis_mlx.runtime.bamf_bundle.pre_cas_fixture", writer_path)
        writer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(writer)
        bind_historical_sidecar_contract(writer)
        bundle = self.root / "historical-bundle"
        initial = candidate(parent_state())
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest_record = writer.save_bamf_bundle(initial, bundle, reserve_gib=0.)
        with shape_patch():
            expected = numerical_observation(codec.load_bamf_bundle(
                bundle, expected_manifest_sha256=manifest_record["manifest_sha256"]))
        before = {path.name: path.read_bytes() for path in bundle.iterdir()}
        manifest = json.loads(before["manifest.json"])
        self.assertNotIn("object_sha256", manifest["tensors"])
        self.assertIn(manifest["tensors"]["filename"], before)
        with shape_patch():
            self.assertEqual(numerical_observation(writer.load_bamf_bundle(bundle)), expected)
            self.assertEqual(
                numerical_observation(codec.load_bamf_bundle(
                    bundle, expected_manifest_sha256=manifest_record["manifest_sha256"])),
                expected)
        script = "\n".join((
            "import json,sys",
            "from bilqis_mlx.runtime.bamf_bundle import load_bamf_bundle",
            "from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch",
            "from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.test_pre_cas_compatibility import numerical_observation",
            "with shape_patch(): student=load_bamf_bundle(sys.argv[1])",
            "print(json.dumps(numerical_observation(student),sort_keys=True))",
        ))
        result = subprocess.run([sys.executable, "-c", script, str(bundle)],
                                check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), expected)
        self.assertEqual({path.name: path.read_bytes() for path in bundle.iterdir()}, before)

    def test_pinned_old_writer_cannot_publish_fresh_accepted_successor(self):
        repository = Path(__file__).resolve().parents[5]
        source = subprocess.run(
            ["git", "show", PRE_CAS + ":bilqis_mlx/runtime/_custody/bamf_bundle/codec.py"],
            cwd=repository, check=True, capture_output=True).stdout
        self.assertEqual(hashlib.sha256(source).hexdigest(), WRITER_SHA256)
        writer_path = self.root / "pre_cas_codec.py"
        writer_path.write_bytes(source)
        spec = importlib.util.spec_from_file_location(
            "bilqis_mlx.runtime.bamf_bundle.pre_cas_successor_fixture", writer_path)
        writer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(writer)

        run = self.root / "successor-run"
        parent = candidate(parent_state())
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_candidate(run, parent)
        successor = candidate(
            accepted_state(parent_state()), 1, pointer["manifest_sha256"])

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), \
                patch.object(publication, "save_bamf_bundle",
                             side_effect=writer.save_bamf_bundle), \
                self.assertRaises(BilqisError):
            publish_candidate(run, successor)
        self.assertEqual(json.loads((run / "bamf-state.json").read_text())["generation"], 0)

    def test_live_parent_migrates_to_objective_acceptance_bound_successor(self):
        run = self.root / "v2-upgrade-run"
        genesis = candidate(parent_state())
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            first = publish_candidate(run, genesis)
            published_parent = load_bamf_generation(run / "bamf-state.json")

        generation_one = candidate(
            accepted_state(
                published_parent.retained_state, published_parent.extents),
            1, first["manifest_sha256"])
        stage = run / "legacy-v2-stage"
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest = save_bamf_bundle(generation_one, stage)
        target = run / "bamf-bundles" / manifest["manifest_sha256"]
        stage.rename(target)
        accepted_one = acceptance(
            generation_one, parent=published_parent.retained_state)
        acceptance_dir = run / "bamf-acceptance"
        acceptance_dir.mkdir(exist_ok=True)
        (acceptance_dir / f"{manifest['manifest_sha256']}.json").write_bytes(
            canonical(accepted_one.to_record()))
        pointer = {
            "schema": BAMF_POINTER_SCHEMA,
            "run_id": generation_one.run_id,
            "generation": generation_one.generation,
            "parent_manifest_sha256": generation_one.parent_manifest_sha256,
            "bundle": f"bamf-bundles/{manifest['manifest_sha256']}",
            "manifest_sha256": manifest["manifest_sha256"],
            "acceptance_sha256": accepted_one.digest,
        }
        (run / "bamf-state.json").write_bytes(canonical(pointer))
        with shape_patch():
            historical_parent = load_bamf_generation(run / "bamf-state.json")

        generation_two = candidate(
            next_accepted_step(
                historical_parent.retained_state, historical_parent.extents),
            2,
            manifest["manifest_sha256"])
        accepted_two = acceptance(
            generation_two, parent=historical_parent.retained_state)

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            successor = publish_bamf_generation(
                run, generation_two, acceptance=accepted_two)

        self.assertEqual(successor["generation"], 2)
        child_manifest = json.loads(
            (run / successor["bundle"] / "manifest.json").read_text())
        self.assertEqual(
            child_manifest["schema"],
            OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA)
        self.assertEqual(
            child_manifest["parent_acceptance_sha256"], accepted_one.digest)
        self.assertEqual(
            parent_acceptance_anchor_from_manifest(
                run, successor["manifest_sha256"]),
            accepted_one.digest,
        )
        with shape_patch():
            reloaded = load_bamf_generation(run / "bamf-state.json")
        self.assertEqual(reloaded.generation, 2)
