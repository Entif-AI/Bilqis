"""#1165: one accepted N-step candidate publishes one successor generation."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.learning.atlas_candidate import resolve_candidate
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, derive_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.tests.correction.capability_support_owner_support import (
    source_qualified_state,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    parent_state, publish_genesis, retention_decision, shape_patch,
)


def test_four_step_rejection_returns_exact_parent_optimizer_and_identity():
    original = parent_state()
    parent, transaction, _retained, _authority = source_qualified_state(
        original, steps=4)
    before_identity = candidate_identity_digest(parent)
    rejected = resolve_candidate(transaction, accepted=False)
    assert rejected is parent
    assert candidate_identity_digest(rejected) == before_identity
    assert rejected.optimizer is parent.optimizer
    assert rejected.optimizer_step == 11


def test_four_step_candidate_publishes_exactly_one_successor_with_four_updates():
    with TemporaryDirectory() as temporary, TemporaryDirectory() as data_plane:
        run = Path(temporary) / "run"
        with patch.dict(
                os.environ,
                {"BILQIS_DATA_PLANE": str(Path(data_plane) / "plane.sqlite3")}), \
                shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_genesis(run)
            accepted_parent = load_accepted_generation(run)
            parent, transaction, retained, _authority = source_qualified_state(
                accepted_parent.retained_state,
                extents=accepted_parent.extents,
                spec=accepted_parent.topology,
                steps=4,
            )
            assert transaction.update_steps == 4
            assert len(transaction.step_proofs) == 4
            assert len(transaction.training_authorities) == 4
            assert retained.optimizer_step == parent.optimizer_step + 4
            successor = derive_successor_bundle(
                accepted_parent, retained,
                parent_manifest_sha256=pointer["manifest_sha256"],
                delivery_events=({"event": "CANDIDATE_HORIZON_ACCEPTED"},),
            )
            decision = retention_decision(parent=parent, retained=retained)
            published = accept_and_publish(
                run, successor, retained, decision=decision,
                feature_sha256=successor.extents.factor_map_digest,
                training_authorities=transaction.training_authorities,
                reserve_gib=0.0,
            )
            cold = load_accepted_generation(run)
    assert published["generation"] == accepted_parent.generation + 1
    assert cold.generation == accepted_parent.generation + 1
    assert cold.retained_state.optimizer_step == parent.optimizer_step + 4
