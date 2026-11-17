"""R05 generated-cohort soup contracts; fixtures are synthetic and neural-inert."""
from pathlib import Path
import tempfile
import unittest

import numpy as np

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning._championship.cohort_soup import (
    cohort_soup_recipe, cohort_vote_count, partitioned_recipes,
    read_frozen_cohort_soup, save_frozen_cohort_soup, seal_frozen_cohort_soup,
    verify_frozen_cohort_soup, weighted_average,
)


def role(capability, checkpoint="1", *, correct=19, total=20, group="opaque-z"):
    digest = checkpoint * 64
    return {
        "capability": capability,
        "capability_group": group,
        "checkpoint_origin_group": "origin-alpha",
        "championship_qualification_correct": correct,
        "championship_qualification_total": total,
        "checkpoint": {
            "sha256": digest,
            "filename": "bamf-generations/7",
            "optimizer_step": 22,
            "model_and_native_adamw": True,
        },
        "complete_solver_provenance": {
            "schema_version": "bilqis.c05.complete-solver-provenance/v1",
            "generation_digest": "a" * 64,
            "weight_sha256": digest,
            "solver_contracts": ["b" * 64],
        },
    }


def recipe(state, capabilities):
    return cohort_soup_recipe(
        state, "opaque-z", tuple(capabilities),
        championship_epoch_sha256="c" * 64,
        cohort_definition_sha256="d" * 64,
        factory_release_sha256="e" * 64)


class GeneratedCohortSoupTests(unittest.TestCase):
    def test_opaque_cohort_counts_roles_and_deduplicates_shared_checkpoint(self):
        state = {"active_roles": {
            "future:first": role("future:first"),
            "future:second": role("future:second"),
            "future:exact-ninety": role("future:exact-ninety", "2", correct=18),
        }}
        plan = recipe(state, ("future:first", "future:second", "future:exact-ninety"))
        self.assertEqual(plan["cohort_id"], "opaque-z")
        self.assertEqual(plan["vote_count"], 2)
        self.assertEqual(plan["members"], [{
            "checkpoint": role("unused")["checkpoint"], "votes": 2}])
        self.assertEqual(plan["covered_capabilities"], ["future:first", "future:second"])

    def test_partitions_exact_graphs_without_losing_logical_votes(self):
        state = {"active_roles": {
            "future:first": role("future:first", "1"),
            "future:second": role("future:second", "2"),
        }}
        plan = recipe(state, ("future:first", "future:second"))
        shards = partitioned_recipes(
            plan, {
                "1" * 64: {
                    "accepted_manifest_sha256": "c" * 64,
                    "source_graph_sha256": "a" * 64,
                },
                "2" * 64: {
                    "accepted_manifest_sha256": "d" * 64,
                    "source_graph_sha256": "b" * 64,
                },
            })
        self.assertEqual(len(shards), 2)
        self.assertEqual(sum(item["vote_count"] for item in shards), 2)
        self.assertEqual({item["source_graph_sha256"] for item in shards}, {"a" * 64, "b" * 64})
        self.assertEqual(
            {item["members"][0]["accepted_manifest_sha256"] for item in shards},
            {"c" * 64, "d" * 64})

    def test_direct_and_cross_cohort_soup_policy_is_generic(self):
        snap = {"teacher_policy": "bilqis.bamf.generated-cohort-adviser-policy/v1",
                "cohort_id": "opaque-z", "vote_count": 6}
        self.assertEqual(cohort_vote_count(snap, "opaque-z", 3), 6.0)
        self.assertEqual(cohort_vote_count(snap, "another-cohort", 3), 2.0)

    def test_frozen_receipt_cold_reloads_and_tamper_fails_closed(self):
        import mlx.core as mx
        mx.set_default_device(mx.cpu)
        plan = recipe({"active_roles": {"future:first": role("future:first")}},
                      ("future:first",))
        plan = partitioned_recipes(plan, {"1" * 64: {
            "accepted_manifest_sha256": "c" * 64,
            "source_graph_sha256": "a" * 64,
        }})[0]
        weights = {"embedding.weight": mx.array([[1., 3.]], dtype=mx.float32)}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = save_frozen_cohort_soup(root, plan, weights, reserve_gib=0.)
            seal_frozen_cohort_soup(root, snapshot)
            cold = read_frozen_cohort_soup(root, plan)
            self.assertEqual(cold, snapshot)
            np.testing.assert_allclose(
                np.asarray(verify_frozen_cohort_soup(root, cold)["embedding.weight"]),
                [[1., 3.]])
            blob = root / snapshot["filename"]
            blob.write_bytes(blob.read_bytes() + b"corrupt")
            with self.assertRaises(BilqisError) as caught:
                read_frozen_cohort_soup(root, plan)
            self.assertEqual(
                caught.exception.context["reason"],
                "COHORT_SOUP_SAVED_ARTIFACT_CHANGED")

    def test_cold_receipt_cannot_authorize_coordinated_tensor_forgery(self):
        import json
        import mlx.core as mx
        mx.set_default_device(mx.cpu)
        plan = recipe({"active_roles": {"future:first": role("future:first")}},
                      ("future:first",))
        plan = partitioned_recipes(plan, {"1" * 64: {
            "accepted_manifest_sha256": "c" * 64,
            "source_graph_sha256": "a" * 64,
        }})[0]
        trusted = {"embedding.weight": mx.array([[1., 3.]], dtype=mx.float32)}
        forged = {"embedding.weight": mx.array([[9., 8.]], dtype=mx.float32)}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = save_frozen_cohort_soup(
                root, plan, trusted, reserve_gib=0.)
            receipt_path = seal_frozen_cohort_soup(root, snapshot)
            blob = root / snapshot["filename"]
            mx.save_safetensors(str(blob), forged)
            forged_snapshot = dict(snapshot)
            from bilqis_mlx.backup import digest_file
            forged_snapshot["sha256"] = digest_file(blob)
            forged_snapshot["parameter_signature_sha256"] = (
                snapshot["parameter_signature_sha256"])
            receipt_path.write_text(
                json.dumps(forged_snapshot, sort_keys=True, separators=(",", ":")))
            with self.assertRaises(BilqisError) as caught:
                read_frozen_cohort_soup(
                    root, plan, expected_weights=trusted)
            self.assertEqual(
                caught.exception.context["reason"],
                "COHORT_SOUP_TRUSTED_RECONSTRUCTION_DRIFT")

    def test_soup_averages_only_parameter_values(self):
        import mlx.core as mx
        left = {"w": mx.array([1., 3.], dtype=mx.float32)}
        right = {"w": mx.array([7., 9.], dtype=mx.float32)}
        merged = weighted_average(mx, ((2, left), (1, right)))
        np.testing.assert_allclose(np.asarray(merged["w"]), [3., 5.])
        np.testing.assert_allclose(np.asarray(left["w"]), [1., 3.])


if __name__ == "__main__":
    unittest.main()
