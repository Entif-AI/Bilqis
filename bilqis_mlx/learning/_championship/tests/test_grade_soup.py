"""Whole-student grade-soup contract; all fixtures are synthetic."""
import unittest
import numpy as np
from pathlib import Path
import tempfile
from bilqis_mlx.factory.schedule import (
    ScheduleCapability, ScheduleGrade, ScheduleProgram,
)

from bilqis_mlx.learning.grade_soup import (
    grade_soup_recipe, needs_refresh, soup_vote_count, weighted_average,
    save_frozen_soup, verify_frozen_soup, retire_stale_soups,
    PARTITIONED_SCHEMA, partitioned_recipe, soup_shards,
)


def perfect(cap, sha, breadth=1, *, rubric="a" * 64):
    return {"rubric": rubric, "capability": cap, "correct": 12, "total": 12,
            "breadth": breadth, "perfect_capabilities": [cap, *(
                "A.OTHER" + str(i) for i in range(breadth-1))],
            "checkpoint": {"filename": "bundles/" + sha,
                           "sha256": sha * 64, "optimizer_step": 5,
                           "model_and_native_adamw": True}}


class GradeSoupTests(unittest.TestCase):
    def test_best_below_max_capability_champion_can_contribute_one_vote(self):
        entry = perfect("A.3", "1")
        entry["correct"] = 10
        entry["breadth"] = 0
        entry["perfect_capabilities"] = []
        plan = grade_soup_recipe({"A.3": entry}, "A", ("A.3",))
        self.assertEqual(plan["vote_count"], 1)
        self.assertEqual(plan["members"][0]["votes"], 1)
        self.assertEqual(plan["roles"][0]["capability"], "A.3")

    def test_partitioned_mixed_source_catalogs_are_separate_frozen_teachers(self):
        import mlx.core as mx
        from types import SimpleNamespace
        from unittest.mock import patch
        from bilqis_mlx import trainer as trainer
        mx.set_default_device(mx.cpu)
        old_graph={"tokens":[0,1],"nodes":[{"id":0},{"id":1}],
                   "row_contract_sha256":{"a":"f"*64}}
        new_graph={"tokens":[0,1,2],"nodes":[{"id":0},{"id":1},{"id":2}],
                   "row_contract_sha256":{"a":"f"*64,"b":"e"*64}}
        self.assertTrue(trainer._compatible_graphs(old_graph,new_graph))
        old=perfect("A.OLD","1")
        new=perfect("A.NEW","2")
        roles={"old":old,"new":new}
        course=ScheduleProgram(
            program_digest="a"*64,
            grades=(ScheduleGrade(
                "A",
                (ScheduleCapability("A.OLD", 12),
                 ScheduleCapability("A.NEW", 12)),
                (), "b"*64),),
            program_complete=False)
        weights_by_sha={
            old["checkpoint"]["sha256"]:(
                {"embedding.weight":mx.ones((2,3)), "norm.weight":mx.ones((3,))},
                old_graph),
            new["checkpoint"]["sha256"]:(
                {"embedding.weight":2*mx.ones((3,3)), "norm.weight":2*mx.ones((3,))},
                new_graph),
        }
        def load_bundle(path):
            sha = ("1" if path.name=="older" else "2")*64
            weights,graph=weights_by_sha[sha]
            return (weights,None,{"source_digest":trainer.AUDITED_PARENT.sha256,
                    "safetensors_sha256":sha,"optimizer_step":5},graph)
        roles["old"]["checkpoint"]["filename"]="bundles/older"
        roles["new"]["checkpoint"]["filename"]="bundles/newer"
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"bundles/older").mkdir(parents=True)
            (root/"bundles/newer").mkdir(parents=True)
            with patch('bilqis_mlx.runtime.mlx_checkpoint.load_semantically_bound_bundle',
                              side_effect=load_bundle):
                frozen,refreshed=trainer._cook_new_grade_soups(
                    mx,root,{"grade_soups":{}},roles,course,new_graph,
                    reserve_gib=0.)
            self.assertEqual(refreshed,("A",))
            aggregate=frozen["A"]
            self.assertEqual(aggregate["schema"],PARTITIONED_SCHEMA)
            self.assertEqual(aggregate["vote_count"],2)
            self.assertEqual([sh["token_count"] for sh in soup_shards(aggregate)],[2,3])
            self.assertEqual(aggregate["partition_policy"],
                             "EXACT_SOURCE_GRAPH_NO_MIXED_PARAMETER_AVERAGE")
            for shard in soup_shards(aggregate):
                self.assertTrue(verify_frozen_soup(root,shard).is_file())
            mentors,receipts=trainer._frozen_grade_soup_votes(
                root,{"grade_soups":frozen},"B",3)
            self.assertEqual(len(mentors),2)
            self.assertAlmostEqual(sum(item["breadth"] for item in mentors),2/3)
            self.assertEqual({entry["frozen_base_votes"] for entry in receipts},{1})
            self.assertEqual(retire_stale_soups(root,frozen),())
            self.assertFalse(needs_refresh(aggregate,grade_soup_recipe(
                roles,"A",("A.OLD","A.NEW"))))
            with self.assertRaisesRegex(ValueError,"PARAMETER_GEOMETRY_DRIFT"):
                weighted_average(mx,((1,weights_by_sha["1"*64][0]),
                                     (1,weights_by_sha["2"*64][0])))

    def test_partitioned_recipe_counts_roles_not_pretend_shared_vocab(self):
        rows={"a":perfect("A.ONE","1"),"b":perfect("A.TWO","2")}
        plan=grade_soup_recipe(rows,"A",("A.ONE","A.TWO"))
        result=partitioned_recipe(plan,{"1"*64:"a"*64,"2"*64:"b"*64})
        self.assertEqual(len(result),2)
        self.assertEqual(sum(shard["vote_count"] for shard in result),2)
        self.assertEqual({shard["source_graph_sha256"] for shard in result},
                         {"a"*64,"b"*64})
        with self.assertRaisesRegex(ValueError,"GRAPH_UNVERIFIED"):
            partitioned_recipe(plan,{"1"*64:"a"*64})

    def test_recipe_counts_capabilities_not_distinct_checkpoints(self):
        rows = {"k1": perfect("A.3", "1", 2),
                "k2": perfect("A.5", "1", 2),
                "k3": perfect("A.7", "2", 1),
                "k4": perfect("B.1", "3", 1)}
        plan = grade_soup_recipe(rows, "A", ("A.3", "A.5", "A.7", "A.11"))
        self.assertEqual(plan["vote_count"], 3)
        self.assertEqual(plan["coverage_peak"], 3)
        self.assertEqual({i["checkpoint"]["sha256"]: i["votes"] for i in plan["members"]},
                         {"1" * 64: 2, "2" * 64: 1})
        self.assertEqual(plan["perfect_capabilities"], ["A.3", "A.5", "A.7"])
        self.assertTrue(needs_refresh(None, plan))
        self.assertFalse(needs_refresh({**plan, "filename": "soups/old.safetensors"}, plan))

    def test_new_coverage_or_champion_displacement_refreshes_but_worse_ties_do_not(self):
        before = {"k1": perfect("A.3", "1", 2), "k2": perfect("A.5", "1", 2)}
        old = grade_soup_recipe(before, "A", ("A.3", "A.5", "A.7"))
        self.assertFalse(needs_refresh(old, grade_soup_recipe(dict(before), "A",
                                             ("A.3", "A.5", "A.7"))))
        after = {**before, "k3": perfect("A.7", "2")}
        self.assertTrue(needs_refresh(old, grade_soup_recipe(after, "A",
                                             ("A.3", "A.5", "A.7"))))
        replaced = {**before, "k2": perfect("A.5", "3", 3)}
        self.assertTrue(needs_refresh(old, grade_soup_recipe(replaced, "A",
                                             ("A.3", "A.5", "A.7"))))

    def test_vote_count_is_frozen_and_foreign_grade_dilution_uses_live_grade_count(self):
        snap = {"grade": "A", "vote_count": 7}
        self.assertEqual(soup_vote_count(snap, "A", 3), 7)
        self.assertAlmostEqual(soup_vote_count(snap, "B", 3), 7/3)
        self.assertAlmostEqual(soup_vote_count(snap, "C", 3), 7/3)
        self.assertEqual(soup_vote_count(snap, "B", 1), 7)
        self.assertEqual(soup_vote_count(snap, "B", 2), 3.5)
        self.assertEqual(snap["vote_count"], 7)

    def test_weight_soup_averages_per_role_and_cannot_mutate_ingredients(self):
        import mlx.core as mx
        left = {"embedding.weight": mx.array([[1., 3.]], dtype=mx.float32)}
        right = {"embedding.weight": mx.array([[7., 9.]], dtype=mx.float32)}
        fused = weighted_average(mx, ((2, left), (1, right)))
        np.testing.assert_allclose(np.asarray(fused["embedding.weight"]), [[3., 5.]])
        np.testing.assert_allclose(np.asarray(left["embedding.weight"]), [[1., 3.]])
        np.testing.assert_allclose(np.asarray(right["embedding.weight"]), [[7., 9.]])

    def test_frozen_file_is_exclusive_hash_verified_and_idempotent(self):
        import mlx.core as mx
        recipe = grade_soup_recipe({"a": perfect("A.3", "1")}, "A", ("A.3",))
        arrays = {"embedding.weight": mx.array([[3., 5.]], dtype=mx.float32)}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = save_frozen_soup(root, recipe, arrays, reserve_gib=0., token_count=1)
            self.assertEqual(verify_frozen_soup(root, first), root / first["filename"])
            second = save_frozen_soup(root, recipe, arrays, reserve_gib=0., token_count=1)
            self.assertEqual(first, second)
            self.assertEqual(len(list((root / "soups").iterdir())), 1)
            blob = root / first["filename"]
            blob.write_bytes(blob.read_bytes() + b"corrupt")
            with self.assertRaisesRegex(ValueError, "ARTIFACT_CHANGED"):
                verify_frozen_soup(root, first)

    def test_superseded_older_snapshots_retire_only_after_new_one_is_pinned(self):
        import mlx.core as mx
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshots = []
            for index in range(3):
                recipe = grade_soup_recipe({"cap": perfect("A.3", str(index+1))},
                                          "A", ("A.3",))
                snapshots.append(save_frozen_soup(
                    root, recipe,
                    {"embedding.weight": mx.array([[float(index)]], dtype=mx.float32)},
                    reserve_gib=0., token_count=1))
            latest = {**snapshots[2], "previous": {
                "filename": snapshots[1]["filename"],
                "sha256": snapshots[1]["sha256"]}}
            unknown = root / "soups" / "manual-custody.txt"
            unknown.write_text("do not touch")
            self.assertEqual(retire_stale_soups(root, {"A": latest}),
                             (snapshots[0]["filename"],))
            self.assertFalse((root / snapshots[0]["filename"]).exists())
            self.assertTrue((root / snapshots[1]["filename"]).exists())
            self.assertTrue((root / snapshots[2]["filename"]).exists())
            self.assertEqual(unknown.read_text(), "do not touch")
