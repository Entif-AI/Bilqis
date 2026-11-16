"""Disposable champion confidence tests; no real student updates."""
import unittest
import numpy as np
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from bilqis_mlx.learning.champion_confidence import (
    vote_targets, vote_targets_typed, champion_roster,
)


def record(cap, sha, perfect):
    return {"capability": cap, "rubric": "a" * 64,
            "checkpoint": {"sha256": sha * 64,
                           "filename": "bundles/" + sha,
                           "optimizer_step": 1,
                           "model_and_native_adamw": True},
            "correct": 12, "total": 12,
            "perfect_capabilities": list(perfect), "breadth": len(perfect)}


class ChampionConfidenceTests(unittest.TestCase):
    def test_foreign_maxed_capability_champion_is_silent_but_diluted_soup_advises_grade_b(self):
        from bilqis_mlx.trainer import (
            _frozen_confidence_champions, _frozen_grade_soup_votes,
        )
        a_champ = record("A.3", "1", ("A.3", "A.5"))
        with TemporaryDirectory() as temp:
            root = Path(temp)
            soup_role = {"capability": "A.3", "rubric": "a" * 64,
                         "correct": 12, "total": 12,
                         "checkpoint_sha256": "1" * 64}
            a_only = {"graduation_perfect": {"a" * 64 + ":A.3": a_champ},
                      "grade_soups": {"A": {"grade": "A", "vote_count": 1,
                                               "roles": [soup_role]}}}
            graph = {"tokens": ["PAD", "TRUE", "FALSE"], "nodes": [],
                     "row_contract_sha256": {}}
            with (patch("pathlib.Path.stat") as stat,
                  patch('bilqis_mlx.learning.lesson_guidance._cached_frozen_champion',
                        return_value=({"embedding.weight": "synthetic"}, graph))):
                stat.return_value.st_size = 1
                stat.return_value.st_mtime_ns = 1
                direct = _frozen_confidence_champions(root, a_only, "B", graph)
            self.assertEqual(direct, ())
            path = root / "soups" / "A-frozen.safetensors"
            path.parent.mkdir()
            path.write_bytes(b"synthetic immutable path")
            soup = {"schema": "bilqis.mlx.frozen-grade-soup/v1",
                    "grade": "A", "filename": str(path.relative_to(root)),
                    "sha256": "c" * 64, "token_count": 12,
                    "recipe_sha256": "d" * 64, "vote_count": 7}
            with patch('bilqis_mlx.learning.lesson_guidance._cached_grade_soup',
                       return_value={"embedding.weight": "synthetic"}):
                mentors, receipts = _frozen_grade_soup_votes(
                    root, {"grade_soups": {"A": soup}}, "B", 3)
            self.assertEqual(len(mentors), 1)
            self.assertAlmostEqual(mentors[0]["breadth"], 7 / 3)
            self.assertEqual(receipts[0]["frozen_base_votes"], 7)
            self.assertAlmostEqual(receipts[0]["effective_votes"], 7 / 3)

    def test_six_maxed_a_roles_vote_directly_only_in_a_while_soup_crosses_to_b(self):
        from bilqis_mlx.trainer import _frozen_confidence_champions
        from bilqis_mlx.learning.grade_soup import soup_vote_count
        grade = "A"
        caps = tuple(f"A.{n}" for n in range(6))
        frontier = {}
        roles = []
        for index, cap in enumerate(caps):
            item = record(cap, str(index + 1), caps)
            frontier[item["rubric"] + ":" + cap] = item
            roles.append({"capability": cap, "rubric": item["rubric"],
                          "correct": 12, "total": 12,
                          "checkpoint_sha256": item["checkpoint"]["sha256"]})
        snapshot = {"grade": grade, "vote_count": 6, "roles": roles}
        graph = {"tokens": ["PAD", "TRUE", "FALSE"], "nodes": [],
                 "row_contract_sha256": {}}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            receipt = {"graduation_perfect": frontier,
                       "grade_soups": {grade: snapshot}}
            with (patch("pathlib.Path.stat") as stat,
                  patch('bilqis_mlx.learning.lesson_guidance._cached_frozen_champion',
                        return_value=({"embedding.weight": "synthetic"}, graph))):
                stat.return_value.st_size = 1
                stat.return_value.st_mtime_ns = 1
                direct = _frozen_confidence_champions(root, receipt, "A", graph)
        self.assertEqual(sum(mentor["breadth"] for mentor in direct), 6)
        self.assertEqual(sum(mentor["source_grade_votes"]["A"] for mentor in direct), 6)
        self.assertEqual(soup_vote_count(snapshot, "B", 3), 2.0)

    def test_subperfect_roles_stay_soup_only_while_five_maxed_c_roles_vote_directly(self):
        from bilqis_mlx.learning.champion_confidence import perfect_role_roster
        from bilqis_mlx.learning.grade_soup import soup_vote_count
        frontier, roles = {}, []
        for index in range(7):
            cap = f"C.{index}"
            perfect = index < 5
            item = record(cap, str(index + 1), (cap,) if perfect else ())
            item["correct"], item["total"] = ((21, 21) if perfect else (20, 21))
            item["breadth"] = 1 if perfect else 0
            item["perfect_capabilities"] = [cap] if perfect else []
            frontier[item["rubric"] + ":" + cap] = item
            roles.append({"capability": cap, "rubric": item["rubric"],
                          "correct": item["correct"], "total": item["total"],
                          "checkpoint_sha256": item["checkpoint"]["sha256"]})
        snapshot = {"grade": "C", "vote_count": 7, "roles": roles}
        direct = perfect_role_roster(frontier, {"C": snapshot})
        self.assertEqual(sum(mentor["breadth"] for mentor in direct), 5)
        self.assertEqual(sum(mentor["source_grade_votes"]["C"] for mentor in direct), 5)
        self.assertAlmostEqual(soup_vote_count(snapshot, "B", 3), 7 / 3)

    def test_mlx_supervised_step_absorbs_advice_without_modifying_exam_inference(self):
        import mlx.core as mx
        import mlx.optimizers as optim
        from bilqis_mlx.trainer import (
            _confidence_guidance, _predictions, _train_step,
        )
        mx.set_default_device(mx.cpu)
        rng = np.random.default_rng(41)
        width = 12
        shapes = {"embedding.weight": (32, width),
                  "position.weight": (12, width),
                  "norm.weight": (width,),
                  "blocks.0.n1.weight": (width,),
                  "blocks.0.n2.weight": (width,),
                  "blocks.0.qkv.weight": (3 * width, width),
                  "blocks.0.proj.weight": (width, width),
                  "blocks.0.up.weight": (2 * width, width),
                  "blocks.0.down.weight": (width, 2 * width)}
        original = {key: (rng.normal(0, .1, size=shape).astype(np.float32)
                          if len(shape) > 1 else np.ones(shape, dtype=np.float32))
                    for key, shape in shapes.items()}
        def student():
            weights = {key: mx.array(value) for key, value in original.items()}
            optimizer = optim.AdamW(learning_rate=.00013, bias_correction=True)
            optimizer.update(weights, {key: mx.zeros_like(value)
                                       for key, value in weights.items()})
            mx.eval(weights, optimizer.state)
            return weights, optimizer
        base, first = student()
        guided, second = student()
        rows = [{"id": "yes", "gold": "TRUE", "tokens": [1, 2, 3, 6]},
                {"id": "no", "gold": "FALSE", "tokens": [4, 5, 6, 7]}]
        config = {"heads": 3, "layers": 1}
        self.assertEqual(_predictions(mx, base, rows, config, [6, 7]),
                         _predictions(mx, guided, rows, config, [6, 7]))
        agreed = _predictions(mx, guided, rows, config, [6, 7])
        coaching_rows = [{**row, "gold": agreed[row["id"]]} for row in rows]
        prepared = _confidence_guidance(
            mx, ({"weights": guided, "graph": {"tokens": list(range(32))},
                  "breadth": 3},), coaching_rows, config, [6, 7],
            scope_size=6, teacher_distill=0.5)
        self.assertIsNotNone(prepared)
        np.testing.assert_allclose(prepared[1], [.02, .02], atol=1e-6)
        unassisted, _ = _train_step(mx, base, first, rows, config, [6, 7])
        advice = (np.array([[.1, .9], [.9, .1]], dtype=np.float32),
                  np.array([.06, .06], dtype=np.float32))
        assisted, _ = _train_step(mx, guided, second, rows, config, [6, 7],
                                  champion_guidance=advice)
        self.assertGreater(assisted, unassisted)
        self.assertEqual(int(first.state["step"].item()),
                         int(second.state["step"].item()))
        self.assertTrue(any(not np.array_equal(np.asarray(base[key]),
                                              np.asarray(guided[key]))
                            for key in original))

    def test_unique_checkpoint_receives_one_vote_at_its_true_breadth(self):
        roster = {"a" * 64 + ":A.3": record("A.3", "1", ("A.3", "A.5")),
                  "a" * 64 + ":A.5": record("A.5", "1", ("A.3", "A.5")),
                  "a" * 64 + ":B.IFF": record("B.IFF", "2", ("B.IFF",))}
        chosen = champion_roster(roster, "A")
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0]["breadth"], 2)
        self.assertEqual(len(champion_roster(roster, "B")), 1)
        self.assertEqual(champion_roster(roster, "B")[0]["breadth"], 1)
        self.assertEqual(champion_roster(roster, "C"), ())

    def test_nonperfect_best_score_role_with_zero_perfect_breadth_is_valid_but_silent(self):
        item = record("B.NOT", "3", ())
        item["correct"] = 11
        item["breadth"] = 0
        item["perfect_capabilities"] = []
        frontier = {"a" * 64 + ":B.NOT": item}
        snapshot = {"grade": "B", "vote_count": 1,
                    "roles": [{"capability": "B.NOT",
                               "rubric": "a" * 64,
                               "checkpoint_sha256": "3" * 64}]}
        self.assertEqual(champion_roster(frontier, "B", snapshot=snapshot), ())

    def test_nonperfect_role_does_not_invalidate_same_checkpoint_perfect_grade_role(self):
        perfect = record("B.AND", "4", ("A.EDGE", "B.AND"))
        nonperfect = record("B.NOT", "4", ("A.EDGE", "B.AND"))
        nonperfect["correct"] = 10
        nonperfect["breadth"] = 2
        nonperfect["perfect_capabilities"] = ["A.EDGE", "B.AND"]
        frontier = {
            "a" * 64 + ":B.AND": perfect,
            "a" * 64 + ":B.NOT": nonperfect,
        }
        snapshot = {"grade": "B", "vote_count": 2,
                    "roles": [
                        {"capability": "B.AND", "rubric": "a" * 64,
                         "checkpoint_sha256": "4" * 64},
                        {"capability": "B.NOT", "rubric": "a" * 64,
                         "checkpoint_sha256": "4" * 64},
                    ]}
        self.assertEqual(
            champion_roster(frontier, "B", snapshot=snapshot),
            ({"checkpoint": perfect["checkpoint"], "breadth": 2},))

    def test_gold_agreeing_logits_vote_proportional_to_breadth(self):
        labels = np.array([1, 0], dtype=np.int64)
        correct_logits = np.array([[0., 2.], [2., 0.]], dtype=np.float32)
        one = vote_targets([(1, correct_logits)], labels, eligible_capabilities=12,
                           teacher_distill=0.5)
        three = vote_targets([(3, correct_logits)], labels, eligible_capabilities=12,
                             teacher_distill=0.5)
        self.assertAlmostEqual(float(three[1][0] / one[1][0]), 3., places=5)
        self.assertLess(three[1][0], 0.08)
        np.testing.assert_allclose(three[0].sum(axis=1), [1., 1.])
        wrong_logits = -correct_logits
        mixed = vote_targets([(1, wrong_logits), (3, correct_logits)], labels,
                             eligible_capabilities=12, teacher_distill=0.5)
        np.testing.assert_allclose(mixed[1], three[1])
        zero = vote_targets([(3, correct_logits)], labels, eligible_capabilities=12,
                            teacher_distill=0.)
        self.assertEqual(float(zero[1].sum()), 0.)

    def test_vote_mask_limits_direct_advice_to_owned_rows(self):
        labels = np.array([1, 1], dtype=np.int64)
        correct_logits = np.array([[0., 2.], [0., 2.]], dtype=np.float32)
        target, weight = vote_targets_typed(
            [(1, correct_logits, np.array([True, False]))],
            labels, classes=2, eligible_capabilities=4, teacher_distill=.5)
        self.assertGreater(float(weight[0]), 0.)
        self.assertEqual(float(weight[1]), 0.)
        np.testing.assert_allclose(target[1], [.5, .5], atol=1e-6)

    def test_role_owner_votes_are_capability_routed_and_same_grade_soup_falls_back(self):
        from bilqis_mlx.learning.lesson_guidance import _mentor_vote_specs

        row_capabilities = ("C.ADD", "C.SUB", "B.AND")
        direct = _mentor_vote_specs(
            {"capabilities": ("C.ADD", "C.SUCCESSOR"), "breadth": 2},
            row_capabilities, lesson_grade="C",
            direct_capabilities={"C.ADD", "C.SUCCESSOR"})
        self.assertEqual(len(direct), 2)
        self.assertEqual(direct[0][0], 1)
        np.testing.assert_array_equal(direct[0][1], [True, False, False])

        same_grade_soup = _mentor_vote_specs(
            {"soup_grade": "C", "breadth": 5},
            row_capabilities, lesson_grade="C",
            direct_capabilities={"C.ADD", "C.SUCCESSOR"})
        self.assertEqual(same_grade_soup[0][0], 5)
        np.testing.assert_array_equal(
            same_grade_soup[0][1], [False, True, True])

        foreign_soup = _mentor_vote_specs(
            {"soup_grade": "A", "breadth": 2},
            row_capabilities, lesson_grade="C",
            direct_capabilities={"C.ADD", "C.SUCCESSOR"})
        np.testing.assert_array_equal(
            foreign_soup[0][1], [True, True, True])

    def test_champion_directed_rows_require_student_miss_and_source_correct_owner(self):
        from bilqis_mlx.learning.lesson_guidance import _champion_directed_rows

        rows = [
            {"id": "miss", "capability": "C.ADD", "gold": "3",
             "tokens": [1, 2], "answer_kind": "numeric_active"},
            {"id": "known", "capability": "C.ADD", "gold": "4",
             "tokens": [1, 3], "answer_kind": "numeric_active"},
            {"id": "other", "capability": "C.SUB", "gold": "2",
             "tokens": [1, 4], "answer_kind": "numeric_active"},
        ]
        mentors = ({
            "weights": {"synthetic": True},
            "graph": {"tokens": list(range(16)), "nodes": [],
                      "row_contract_sha256": {}},
            "capabilities": ("C.ADD",),
            "breadth": 1,
        },)
        with patch(
            "bilqis_mlx.learning.lesson_guidance._learning_student_ops._predictions",
            side_effect=[
                {"miss": "2", "known": "4", "other": "1"},
                {"miss": "3", "known": "4"},
            ],
        ):
            directed = _champion_directed_rows(
                None, mentors, {"student": True}, rows,
                {"heads": 1, "layers": 1}, [1, 2])
        self.assertEqual([row["id"] for row in directed], ["miss"])

    def test_champion_directed_rows_collapse_repeated_source_specimens(self):
        from bilqis_mlx.learning.lesson_guidance import _champion_directed_rows

        repeated = {"id": "same", "capability": "C.COUNT", "gold": "3",
                    "tokens": [1, 2], "answer_kind": "numeric_active"}
        rows = [repeated, dict(repeated)]
        mentors = ({
            "weights": {"synthetic": True},
            "graph": {"tokens": list(range(16)), "nodes": [],
                      "row_contract_sha256": {}},
            "capabilities": ("C.COUNT",),
            "breadth": 1,
        },)
        with patch(
            "bilqis_mlx.learning.lesson_guidance._learning_student_ops._predictions",
            side_effect=[{"same": "2"}, {"same": "3"}],
        ):
            directed = _champion_directed_rows(
                None, mentors, {"student": True}, rows,
                {"heads": 1, "layers": 1}, [1, 2])

        self.assertEqual([row["id"] for row in directed], ["same"])
