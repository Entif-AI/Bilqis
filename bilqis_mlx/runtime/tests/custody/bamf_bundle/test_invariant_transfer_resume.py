"""Independent-authority cold-readback witness for BAMF invariant transfer."""
from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.learning.atlas_candidate import CandidateCustodyIdentity
from bilqis_mlx.runtime.bamf_bundle import publish_initial_generation
from bilqis_mlx.runtime.bamf_bundle.records import CompleteStudent, sidecar_records
from bilqis_mlx.runtime.tests.custody.bamf_bundle.cold_resume_probe import retained_digest
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    genesis_preparation,
    shape_patch,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]


def _in_memory_student(source, pointer) -> CompleteStudent:
    """Bind publication custody without reading the just-written bundle back."""
    records = sidecar_records(source)
    retained = replace(
        source.retained_state,
        custody=CandidateCustodyIdentity(
            source.run_id,
            source.generation,
            pointer["manifest_sha256"],
            source.topology.digest,
            source.extents.digest,
        ),
    )
    return CompleteStudent(
        source.run_id,
        source.generation,
        source.parent_manifest_sha256,
        source.implementation_sha256,
        source.topology,
        source.extents,
        retained,
        source.optimizer_hyperparameters,
        source.provenance,
        source.semantic_abi,
        source.compiler_features,
        source.correction_frontier,
        source.teacher_state,
        source.evaluation_contract,
        source.transition,
        tuple(records["outbox"]),
        source.run_identity,
    )


def _cold_readback(run: Path) -> dict:
    code = (
        "import json,sys; "
        "from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation; "
        "from bilqis_mlx.runtime.tests.custody.bamf_bundle.cold_resume_probe "
        "import retained_digest; "
        "from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch; "
        "ctx=shape_patch(); ctx.__enter__(); "
        "student=load_accepted_generation(sys.argv[1]); "
        "print(json.dumps({'generation':student.generation,"
        "'state_digest':retained_digest(student.retained_state),"
        "'teacher_state':dict(student.teacher_state),"
        "'optimizer_step':student.retained_state.optimizer_step,"
        "'run_seed':student.run_identity.run_seed if student.run_identity else None})); "
        "ctx.__exit__(None,None,None)"
    )
    process = subprocess.run(
        [sys.executable, "-B", "-c", code, str(run)],
        cwd=str(REPOSITORY_ROOT),
        capture_output=True,
        text=True,
        env=dict(os.environ),
        timeout=300,
    )
    if process.returncode:
        raise AssertionError(process.stderr)
    return json.loads(process.stdout.strip().splitlines()[-1])


class InvariantTransferColdResumeTests(unittest.TestCase):
    def test_cold_readback_matches_just_published_in_memory_authority(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / "run"
            with patch.dict(
                    os.environ, {"BILQIS_DATA_PLANE": str(root / "plane.sqlite3")}):
                with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
                    prepared = genesis_preparation()
                    pointer = publish_initial_generation(
                        run, prepared, reserve_gib=0.)
                    authority = _in_memory_student(prepared.candidate, pointer)
                expected = {
                    "generation": authority.generation,
                    "state_digest": retained_digest(authority.retained_state),
                    "teacher_state": dict(authority.teacher_state),
                    "optimizer_step": authority.retained_state.optimizer_step,
                    "run_seed": (
                        authority.run_identity.run_seed
                        if authority.run_identity is not None else None
                    ),
                }
                self.assertEqual(_cold_readback(run), expected)


if __name__ == "__main__":
    unittest.main()
