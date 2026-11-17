"""R05 proof that an opaque disposable Grade Z can form and cold-consume a soup."""
from pathlib import Path
import tempfile

import mlx.core as mx

from bilqis_mlx.learning._championship.cohort_soup import (
    cohort_soup_recipe,
    partitioned_recipes,
    read_frozen_cohort_soup,
    save_frozen_cohort_soup,
    seal_frozen_cohort_soup,
    verify_frozen_cohort_soup,
)
from bilqis_mlx.runtime.state import _fingerprint
from tests.system.factory_grade_z.fixture import CAPABILITIES, fixture


def test_grade_z_forms_and_cold_consumes_generic_frozen_cohort_soup():
    mx.set_default_device(mx.cpu)
    _registry, graph, release = fixture()
    capability = CAPABILITIES[0]
    checkpoint_sha = "1" * 64
    state = {"active_roles": {capability: {
        "capability": capability,
        "capability_group": "Z",
        "checkpoint_origin_group": "Z",
        "championship_qualification_correct": 19,
        "championship_qualification_total": 20,
        "checkpoint": {
            "sha256": checkpoint_sha,
            "filename": "bamf-generations/7",
            "optimizer_step": 7,
            "model_and_native_adamw": True,
        },
        "complete_solver_provenance": {
            "schema_version": "bilqis.c05.complete-solver-provenance/v1",
            "generation_digest": "2" * 64,
            "weight_sha256": checkpoint_sha,
            "solver_contracts": ["3" * 64],
        },
    }}}
    recipe = cohort_soup_recipe(
        state, "Z", CAPABILITIES,
        championship_epoch_sha256="4" * 64,
        cohort_definition_sha256="5" * 64,
        factory_release_sha256=release.release_sha256)
    shard = partitioned_recipes(recipe, {
        checkpoint_sha: {
            "accepted_manifest_sha256": "6" * 64,
            "source_graph_sha256": _fingerprint(graph),
        },
    })[0]
    assert shard["cohort_id"] == "Z"
    assert shard["covered_capabilities"] == [capability]
    assert shard["members"][0]["accepted_manifest_sha256"] == "6" * 64
    weights = {"z.weight": mx.array([[1., 2.]], dtype=mx.float32)}
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        snapshot = save_frozen_cohort_soup(root, shard, weights, reserve_gib=0.0)
        seal_frozen_cohort_soup(root, snapshot)
        cold = read_frozen_cohort_soup(root, shard, expected_weights=weights)
        assert cold["recipe_sha256"] == shard["recipe_sha256"]
        restored = verify_frozen_cohort_soup(root, cold, expected_weights=weights)
        assert tuple(restored) == ("z.weight",)
