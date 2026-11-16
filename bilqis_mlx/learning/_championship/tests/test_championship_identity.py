from unittest import TestCase

from bilqis_mlx.learning.championship_identity import (
    build_school_identity, enforce_school_identity)
from bilqis_mlx.learning.mentor_epoch import begin_initial_epoch, reference_checkpoints
from bilqis_mlx.semantics.abi import HISTORICAL_PREFIX_SIZE


def _identity(course="a", graph="b", release="c", width=8):
    return build_school_identity(
        course_sha256=course * 64,
        semantic_graph_sha256=graph * 64,
        parameter_shapes={"embedding.weight": [HISTORICAL_PREFIX_SIZE, width],
                          "head.weight": [width, 4]},
        factory_release_sha256=release * 64)


class ChampionshipIdentityTests(TestCase):
    def test_identity_is_deterministic_and_shape_sensitive(self):
        self.assertEqual(_identity(), _identity())
        self.assertNotEqual(_identity()["sha256"], _identity(width=9)["sha256"])
        self.assertNotEqual(_identity()["sha256"], _identity(course="d")["sha256"])
        self.assertNotEqual(_identity()["sha256"], _identity(graph="d")["sha256"])
        self.assertNotEqual(_identity()["sha256"], _identity(release="d")["sha256"])

    def test_identity_drift_archives_and_clears_all_live_authority(self):
        epoch = {
            "active_roles": {
                "A.X": {"capability": "A.X"},
                "B.Y": {"capability": "B.Y"},
            },
            "active_grade_soups": {
                "A": {"vote_count": 1},
                "B": {"vote_count": 2},
            },
            "settled_matchups": {"A.X|1|2": {"winner_sha256": "1" * 64}},
            "championship_school_identity": _identity(),
            "championship_eligibility_after_step": 3,
        }
        student = {"filename": "bundles/current", "sha256": "d" * 64,
                   "optimizer_step": 11, "model_and_native_adamw": True}
        successor_identity = _identity(course="e")
        result, changed = enforce_school_identity(
            epoch, successor_identity, generation=20, student=student)
        self.assertTrue(changed)
        self.assertEqual(result["active_roles"], {})
        self.assertEqual(result["active_grade_soups"], {})
        self.assertEqual(result["settled_matchups"], epoch["settled_matchups"])
        self.assertEqual(result["championship_eligibility_after_step"], 3)
        historic = result["school_identity_history"][-1]
        self.assertEqual(historic["active_roles"], epoch["active_roles"])
        self.assertEqual(historic["active_grade_soups"], epoch["active_grade_soups"])
        self.assertEqual(historic["starting_student"], student)
        self.assertEqual(result["superseded_active_championships"][-1], historic)
        repeated, changed = enforce_school_identity(
            result, successor_identity, generation=21, student=student)
        self.assertFalse(changed)
        self.assertEqual(repeated, result)
        self.assertEqual(len(repeated["school_identity_history"]), 1)

    def test_each_identity_component_drift_clears_live_authority(self):
        base = _identity()
        variants = {
            "course": _identity(course="d"),
            "graph": _identity(graph="d"),
            "parameter_shapes": _identity(width=9),
            "factory_release": _identity(release="d"),
        }
        for name, identity in variants.items():
            with self.subTest(name=name):
                epoch = {
                    "active_roles": {"A.X": {"capability": "A.X"}},
                    "active_grade_soups": {"A": {"vote_count": 1}},
                    "settled_matchups": {"A.X|1|2": {"winner_sha256": "1" * 64}},
                    "championship_school_identity": base,
                    "championship_eligibility_after_step": 3,
                }
                result, changed = enforce_school_identity(
                    epoch, identity, generation=20,
                    student={"sha256": "d" * 64, "optimizer_step": 11})
                self.assertTrue(changed)
                self.assertEqual(result["active_roles"], {})
                self.assertEqual(result["active_grade_soups"], {})
                self.assertEqual(result["settled_matchups"], epoch["settled_matchups"])
                self.assertEqual(result["championship_eligibility_after_step"], 3)

    def test_same_identity_is_idempotent(self):
        identity = _identity()
        epoch = {"active_roles": {}, "active_grade_soups": {},
                 "settled_matchups": {}, "championship_school_identity": identity}
        student = {"sha256": "d" * 64, "optimizer_step": 11}
        first, changed = enforce_school_identity(
            epoch, identity, generation=20, student=student)
        self.assertFalse(changed)
        self.assertEqual(first, epoch)

    def test_identity_can_reset_repeatedly_without_losing_permanent_history(self):
        epoch = {
            "active_roles": {"A.X": {"capability": "A.X"}},
            "active_grade_soups": {"A": {"vote_count": 1}},
            "settled_matchups": {"A.X|1|2": {"winner_sha256": "1" * 64}},
            "championship_school_identity": _identity(),
        }
        student = {"sha256": "d" * 64, "optimizer_step": 11}
        first, changed = enforce_school_identity(
            epoch, _identity(course="e"), generation=20, student=student)
        self.assertTrue(changed)
        first["active_roles"] = {"A.Y": {"capability": "A.Y"}}
        first["active_grade_soups"] = {"A": {"vote_count": 1}}

        second, changed = enforce_school_identity(
            first, _identity(course="e", graph="f"), generation=21,
            student={"sha256": "e" * 64, "optimizer_step": 12})
        self.assertTrue(changed)
        self.assertEqual(second["active_roles"], {})
        self.assertEqual(second["active_grade_soups"], {})
        self.assertEqual(second["settled_matchups"], epoch["settled_matchups"])
        self.assertEqual(len(second["school_identity_history"]), 2)
        self.assertEqual(second["school_identity_history"][-1]["active_roles"],
                         {"A.Y": {"capability": "A.Y"}})

    def test_repeated_identity_resets_preserve_all_same_sha_bundle_aliases(self):
        baseline = {"filename": "bundles/base", "sha256": "b" * 64,
                    "optimizer_step": 9, "model_and_native_adamw": True}
        student = {"filename": "bundles/current", "sha256": "c" * 64,
                   "optimizer_step": 10, "model_and_native_adamw": True}
        alias_one = {"filename": "bundles/alias-one", "sha256": "a" * 64,
                     "optimizer_step": 8, "model_and_native_adamw": True}
        alias_two = {"filename": "bundles/alias-two", "sha256": "a" * 64,
                     "optimizer_step": 8, "model_and_native_adamw": True}
        epoch = begin_initial_epoch(
            student=baseline, introduced_grade="A",
            source_graph_sha256="f" * 64, frontier={}, soups={})
        epoch["championship_school_identity"] = _identity()
        epoch["active_roles"] = {"A.X": {"capability": "A.X",
                                              "origin_grade": "A",
                                              "checkpoint": alias_one}}
        epoch["settled_matchups"] = {}
        first, _ = enforce_school_identity(
            epoch, _identity(course="d"), generation=20, student=student)
        first["active_roles"] = {"A.Y": {"capability": "A.Y",
                                               "origin_grade": "A",
                                               "checkpoint": alias_two}}
        second, _ = enforce_school_identity(
            first, _identity(course="d", graph="e"), generation=21, student=student)
        filenames = {pointer["filename"] for pointer in reference_checkpoints(second)}
        self.assertIn("bundles/alias-one", filenames)
        self.assertIn("bundles/alias-two", filenames)
