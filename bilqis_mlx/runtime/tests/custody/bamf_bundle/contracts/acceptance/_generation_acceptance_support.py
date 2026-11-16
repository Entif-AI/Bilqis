"""B13.5 accepted-generation acceptance-provenance witnesses.

Publication is not acceptance. A generation may only be published, and may only
mint accepted-generation authority, when the retention owner has accepted the
exact candidate state.
"""
from __future__ import annotations

import os
import hashlib
import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_acceptance import (
    LEGACY_ACCEPTANCE_SCHEMA, PREVIOUS_SOURCE_ACCEPTANCE_SCHEMA,
    EXACT_MOTIF_ACCEPTANCE_SCHEMA, AcceptedCandidateBinding,
    mint_acceptance_binding,
)
from bilqis_mlx.learning.atlas_retention_decision import (
    LEGACY_DECISION_SCHEMA, CandidateRetentionDecision, decide_candidate_retention,
)
from bilqis_mlx.runtime.bamf_bundle import (
    publish_bamf_generation, load_bamf_generation, load_bamf_generation_authority,
    read_accepted_generation_feature_receipt,
)
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle.records import (
    LEGACY_BAMF_POINTER_SCHEMA,
)

from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    acceptance, accepted_state, candidate, next_accepted_step, parent_state,
    publish_genesis, retention_decision, shape_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.test_feature_authority import (
    RELEASE, source_features, feature_bound,
)
from bilqis_mlx.runtime.bamf_bundle.records import canonical




def json_manifest_sha(run_dir: Path) -> str:
    return json.loads((run_dir / "bamf-state.json").read_text())["manifest_sha256"]


class GenerationAcceptanceFixture:
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

    def publish(self, source, **kwargs):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_bamf_generation(self.run, source, **kwargs)

    def parent(self):
        if not hasattr(self, "_parent"):
            with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
                self._parent_pointer = publish_genesis(
                    self.run,
                )
                self._parent = load_bamf_generation(self.run / "bamf-state.json")
        return self._parent

    def source(self, *, alternate=False):
        parent = self.parent()
        retained = (
            next_accepted_step(parent.retained_state, parent.extents)
            if alternate else accepted_state(parent.retained_state, parent.extents)
        )
        return replace(
            candidate(retained, 1, self._parent_pointer["manifest_sha256"]),
            run_identity=parent.run_identity,
            implementation_sha256=parent.implementation_sha256,
            topology=parent.topology,
            extents=parent.extents,
            provenance=parent.provenance,
            semantic_abi=dict(parent.semantic_abi),
            compiler_features=dict(parent.compiler_features),
            correction_frontier=dict(parent.correction_frontier),
            teacher_state=dict(parent.teacher_state),
            evaluation_contract=dict(parent.evaluation_contract),
        )

    def binding(self, source):
        return acceptance(source, parent=self.parent().retained_state)

    def feature_source(self, features):
        source = feature_bound(self.source(), features)
        return replace(
            source,
            transition={
                **source.transition,
                "kind": "PARAMETER_EXTENSION",
            },
        )
