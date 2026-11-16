"""Capability-best retention tests use only synthetic checkpoints."""

from pathlib import Path
import tempfile
import unittest

from bilqis_mlx.learning.capability_frontier import (
    candidate_roles, graduation_perfect, historical_frontier, promote, pinned,
    recover_graduation_breadth,
    retirement_plan, retire_bundles,
)

RUBRIC = "a" * 64


def checkpoint(name, step):
    return {"filename": "bundles/" + name, "sha256": f"{step:064x}",
            "optimizer_step": step, "model_and_native_adamw": True}


def scores(*values):
    return {"A." + name: {"correct": value, "total": 12}
            for name, value in zip(("IDENTITY", "LINK", "EDGE"), values)}


class CapabilityFrontierTests(unittest.TestCase):
    def test_simultaneous_perfect_breadth_consolidates_only_eligible_roles(self):
        rubric = "b" * 64
        caps = ("A.3", "A.5", "A.7", "A.11")
        def result(*perfect):
            return {cap: {"correct": 12 if cap in perfect else 9, "total": 12}
                    for cap in caps}
        original, double, triple, successor = (
            checkpoint(name, step) for step, name in enumerate(
                ("one", "two", "three", "four"), 1))
        ranks = {}
        ranks, roles = graduation_perfect(ranks, result("A.3"), rubric,
                                          "e" * 64, original, "exam/1")
        self.assertEqual(roles, ("A.3",))
        ranks, roles = graduation_perfect(ranks, result("A.3", "A.5"), rubric,
                                          "e" * 64, double, "exam/2")
        self.assertEqual(roles, ("A.3", "A.5"))
        self.assertEqual({v["checkpoint"]["filename"] for v in ranks.values()},
                         {double["filename"]})
        ranks, roles = graduation_perfect(ranks, result("A.5", "A.7", "A.11"),
                                          rubric, "e" * 64, triple, "exam/3")
        self.assertEqual(roles, ("A.11", "A.5", "A.7"))
        self.assertEqual(ranks[rubric + ":A.3"]["checkpoint"], double)
        self.assertEqual(ranks[rubric + ":A.5"]["checkpoint"], triple)
        self.assertEqual(ranks[rubric + ":A.5"]["breadth"], 3)
        same, roles = graduation_perfect(ranks, result("A.3", "A.5", "A.11"),
                                         rubric, "e" * 64, successor, "exam/tie")
        self.assertEqual(roles, ("A.3",))
        self.assertEqual(same[rubric + ":A.5"]["checkpoint"], triple)
        self.assertEqual({v["checkpoint"]["filename"] for v in same.values()},
                         {triple["filename"], successor["filename"]})

    def test_perfect_graduation_retained_independent_of_candidate_ranking(self):
        student = checkpoint("perfect", 20)
        old = checkpoint("old", 10)
        frontier = promote({}, scores(7, 5, 4), RUBRIC, old,
                           "candidate-prior", tuple(scores(7, 5, 4)))
        self.assertEqual(candidate_roles(frontier, scores(6, 4, 3), RUBRIC), ())
        perfect, roles = graduation_perfect({}, scores(12, 9, 8), RUBRIC,
                                            "b" * 64, student, "graduation")
        self.assertEqual(roles, ("A.IDENTITY",))
        self.assertEqual(perfect[RUBRIC + ":A.IDENTITY"]["checkpoint"], student)
        self.assertEqual(pinned(frontier, student, {}) | pinned(perfect, student, {}),
                         {"bundles/old", "bundles/perfect"})
        subsequent, new_roles = graduation_perfect(perfect, scores(8, 9, 8),
                            RUBRIC, "b" * 64, checkpoint("next", 30), "retry")
        self.assertEqual(new_roles, ())
        self.assertEqual(subsequent, perfect)

    def test_legacy_perfect_breadth_requires_matching_committed_exam_evidence(self):
        checkpoint_data = checkpoint("legacy", 5)
        rubric = "a" * 64
        cohort = "b" * 64
        old = {rubric + ":A.3": {"rubric": rubric, "capability": "A.3",
            "correct": 12, "total": 12, "checkpoint": checkpoint_data,
            "cohort_sha256": cohort, "evaluation_id": "exam"}}
        event = {"event": "SCHOOL_GRADE_B_LIVE_EXAM_COMMITTED",
            "student_sha256": checkpoint_data["sha256"],
            "rubric": rubric, "cohort_sha256": cohort,
            "scores": {"A.3": {"correct": 12, "total": 12},
                       "A.5": {"correct": 12, "total": 12},
                       "A.7": {"correct": 9, "total": 12}}}
        from copy import deepcopy
        untouched = deepcopy(old)
        upgraded = recover_graduation_breadth(old, (event,))
        self.assertEqual(upgraded[rubric + ":A.3"]["breadth"], 2)
        self.assertEqual(old, untouched)
        with self.assertRaisesRegex(ValueError, "HISTORICAL_EVIDENCE_MISSING"):
            recover_graduation_breadth(old, ())
        wrong = {**event, "student_sha256": "e" * 64}
        with self.assertRaisesRegex(ValueError, "HISTORICAL_EVIDENCE_MISSING"):
            recover_graduation_breadth(old, (wrong,))

    def test_best_can_be_subperfect_and_share_multiple_capabilities(self):
        a = checkpoint("first", 1)
        s = scores(5, 7, 4)
        roles = candidate_roles({}, s, RUBRIC)
        self.assertEqual(set(roles), set(s))
        result = promote({}, s, RUBRIC, a, "exam-1", roles)
        self.assertEqual({v["checkpoint"]["filename"] for v in result.values()},
                         {"bundles/first"})
        self.assertEqual(len(result), 3)

    def test_new_candidate_claims_all_best_slots_and_old_is_only_retired_when_unused(self):
        a, b, c = (checkpoint("a", 1), checkpoint("b", 2), checkpoint("c", 3))
        base = promote({}, scores(5, 7, 4), RUBRIC, a, "exam-1",
                       candidate_roles({}, scores(5, 7, 4), RUBRIC))
        roles = candidate_roles(base, scores(6, 7, 3), RUBRIC)
        self.assertEqual(set(roles), {"A.IDENTITY", "A.LINK"})
        next_best = promote(base, scores(6, 7, 3), RUBRIC, b, "exam-2", roles)
        self.assertEqual(pinned(next_best, b, {}), {"bundles/a", "bundles/b"})
        roles = candidate_roles(next_best, scores(6, 7, 5), RUBRIC)
        self.assertEqual(set(roles), {"A.IDENTITY", "A.LINK", "A.EDGE"})
        final_best = promote(next_best, scores(6, 7, 5), RUBRIC, c,
                             "exam-3", roles)
        self.assertEqual(pinned(final_best, c, {}), {"bundles/c"})

    def test_nonbest_does_not_qualify_for_a_new_champion_binary(self):
        base = promote({}, scores(6, 8, 4), RUBRIC, checkpoint("a", 1),
                       "exam-1", tuple(scores(6, 8, 4)))
        self.assertEqual(candidate_roles(base, scores(4, 6, 3), RUBRIC), ())
        self.assertEqual(candidate_roles(base, scores(6, 8, 4), RUBRIC), ())

    def test_ties_can_consolidate_multiple_independent_champions(self):
        base = promote({}, scores(5, 8, 4), RUBRIC, checkpoint("a", 1),
                       "exam-1", tuple(scores(5, 8, 4)))
        base = promote(base, scores(7, 7, 3), RUBRIC, checkpoint("b", 2),
                       "exam-2", ("A.IDENTITY",))
        self.assertEqual(set(candidate_roles(base, scores(7, 8, 4), RUBRIC)),
                         {"A.IDENTITY", "A.LINK", "A.EDGE"})

    def test_retirement_plan_checks_all_holders_and_unrecognized_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "bundles"
            for name in ("current", "capability", "grade", "old"):
                folder = root / name
                folder.mkdir(parents=True)
                for filename in ("manifest.json", "semantic-catalog.json",
                                 "model-and-own-adamw.safetensors"):
                    (folder / filename).write_bytes(b"fixture")
            front = promote({}, scores(5, 6, 4), RUBRIC,
                            checkpoint("capability", 1), "exam", tuple(scores(5, 6, 4)))
            protected = pinned(front, checkpoint("current", 3),
                               {"A": checkpoint("grade", 2)})
            self.assertEqual(retirement_plan(Path(temp), protected),
                             ("bundles/old",))
            (root / "old" / "extra").write_text("unexpected")
            with self.assertRaisesRegex(ValueError, "CUSTODY"):
                retirement_plan(Path(temp), protected)

    def test_retirement_only_removes_obsolete_synthetic_bundles(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "bundles"
            for name in ("student", "frontier", "obsolete"):
                d = root / name
                d.mkdir(parents=True)
                for f in ("manifest.json", "semantic-catalog.json",
                          "model-and-own-adamw.safetensors"):
                    (d/f).write_bytes(b"fictional")
            keep = {"bundles/student", "bundles/frontier"}
            self.assertEqual(retire_bundles(Path(temp), keep), ("bundles/obsolete",))
            self.assertTrue((root / "frontier/manifest.json").exists())
            self.assertTrue((root / "student/manifest.json").exists())
            self.assertFalse((root / "obsolete").exists())

    def test_historical_exams_rehydrate_best_without_training_or_pruning(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for i in (1, 2):
                d = root / "bundles" / f"visit-{i}"
                d.mkdir(parents=True)
                (d / "manifest.json").write_text(json.dumps({
                    "safetensors_sha256": f"{i:064x}", "optimizer_step": i}))
            with (root / "events.jsonl").open("w") as log:
                for i, vals in ((1, scores(5, 7, 4)), (2, scores(6, 6, 5))):
                    log.write(json.dumps({"event": "GRADE_A_EXAM_COMMITTED",
                        "rubric": RUBRIC, "generation": i,
                        "student_sha256": f"{i:064x}", "scores": vals}) + "\n")
            result = historical_frontier(root)
            self.assertEqual(result[RUBRIC + ":A.IDENTITY"]["checkpoint"]["sha256"],
                             f"{2:064x}")
            self.assertEqual(result[RUBRIC + ":A.LINK"]["checkpoint"]["sha256"],
                             f"{1:064x}")
            self.assertEqual(result[RUBRIC + ":A.EDGE"]["checkpoint"]["sha256"],
                             f"{2:064x}")
            with self.assertRaisesRegex(ValueError, "HISTORIC_RUBRIC_DRIFT"):
                historical_frontier(root, expected_rubric="b" * 64)
            with self.assertRaisesRegex(ValueError, "HISTORIC_INCOMPLETE_EXAM"):
                historical_frontier(root, expected_capabilities={"A.IDENTITY": 12})

    def test_custody_verifies_all_retained_student_and_champion_hashes(self):
        import hashlib
        import json
        from bilqis_mlx.trainer import _verify_best_custody

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            best = {}
            for i, name in enumerate(("working", "leader"), 1):
                path = root / "bundles" / name
                path.mkdir(parents=True)
                payload = ("owned-" + name).encode()
                digest = hashlib.sha256(payload).hexdigest()
                (path / "model-and-own-adamw.safetensors").write_bytes(payload)
                (path / "manifest.json").write_text(json.dumps({
                    "safetensors_sha256": digest, "optimizer_step": i}))
                best[name] = {"filename": "bundles/" + name, "sha256": digest,
                              "optimizer_step": i, "model_and_native_adamw": True}
            receipt = {"school": {"current_student": best["working"],
                                  "champions": {}},
                       "capability_best": {RUBRIC + ":A.IDENTITY": {
                           "checkpoint": best["leader"],
                           "rubric": RUBRIC, "capability": "A.IDENTITY",
                           "correct": 5, "total": 12}}}
            _verify_best_custody(root, receipt)
            (root / "bundles/leader/model-and-own-adamw.safetensors").write_bytes(
                b"same file name, wrong bytes")
            with self.assertRaisesRegex(ValueError, "CUSTODY_SHA_DRIFT"):
                _verify_best_custody(root, receipt)


if __name__ == "__main__":
    unittest.main()
