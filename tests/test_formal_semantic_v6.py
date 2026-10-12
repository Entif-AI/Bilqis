"""Behavioral controls for a new source-frozen semantic teacher experiment."""
from __future__ import annotations

from collections import Counter
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import torch

from bilqis_formal import controller_v6 as c
from bilqis_formal import curriculum_v6 as v
from bilqis_formal import pilot_v6 as p
from bilqis_formal.student_v3 import initialize


class SemanticCurriculumTests(unittest.TestCase):
    def test_complete_oracle_with_independent_splits(self):
        self.assertTrue(v.validate())
        self.assertEqual(v.STAGES, ("V00.BOOLEAN", "V01.NOT", "V02.AND"))
        self.assertEqual(v.DEPENDENCIES["V02.AND"], ("V00.BOOLEAN",))
        for stage in v.STAGES:
            pools = v.split(stage)
            self.assertFalse({r["id"] for r in pools["train"]} &
                             {r["id"] for r in pools["dev"]})
            self.assertFalse({r["id"] for r in pools["train"]} &
                             {r["id"] for r in pools["gate"]})
            self.assertFalse({r["id"] for r in pools["dev"]} &
                             {r["id"] for r in pools["gate"]})
            if stage != "V00.BOOLEAN":
                self.assertTrue(any(v.depth(r["input"]["expression"]) >= 2
                                    for r in pools["gate"]))

    def test_semantic_equivalence_is_not_answer_label(self):
        self.assertEqual(v.signature("P"), v.signature(v.AND("P", "TRUE")))
        self.assertEqual(v.concept_key("P"), v.concept_key(v.NOT("P")))
        self.assertNotEqual(v.signature("P"), v.signature(v.NOT("P")))
        self.assertNotEqual(v.concept_key("P"), v.concept_key("FALSE"))
        self.assertEqual(len(v.signature("P")), 8)
        for a, b in v.RELATIONS:
            self.assertEqual(v.concept_key(a), v.concept_key(b))

    def test_heldout_not_evaluated_when_building_training_batches(self):
        original = c.rows

        def allow_training_only(stage, role):
            if role != "train":
                raise AssertionError("SEALED_OR_DEV_CROSSED_TEACHER_BOUNDARY")
            return original(stage, role)

        with patch.object(c, "rows", side_effect=allow_training_only):
            batches = c.training_batches(seed=503, stage="V02.AND", block=1,
                                         arm="semantic8", prior=("V00.BOOLEAN", "V01.NOT"))
        self.assertEqual(len(batches), 64)

    def test_exact_block_multisets_and_label_balance(self):
        for stage, prior in (("V00.BOOLEAN", ()),
                             ("V01.NOT", ("V00.BOOLEAN",)),
                             ("V02.AND", ("V00.BOOLEAN", "V01.NOT"))):
            for seed in (503, 509):
                for block in (0, 4):
                    ledgers = {}
                    for arm in c.ARMS:
                        batches = c.training_batches(seed=seed, stage=stage,
                            block=block, arm=arm, prior=prior)
                        receipt = c.ledger(batches, stage=stage)
                        self.assertEqual(receipt["examples"], 64 * 32)
                        self.assertEqual(receipt["by_gold"],
                                         {"ATOM.FALSE": 1024, "ATOM.TRUE": 1024})
                        self.assertEqual(len(batches), 64)
                        for batch in batches:
                            self.assertEqual(Counter(row["gold"] for row in batch),
                                             {"ATOM.FALSE": 16, "ATOM.TRUE": 16})
                        ledgers[arm] = receipt
                    self.assertEqual(ledgers["uniform8"]["row_multiset_sha256"],
                                     ledgers["semantic8"]["row_multiset_sha256"])
                    self.assertEqual(ledgers["uniform8"]["row_multiset_sha256"],
                                     ledgers["sham8"]["row_multiset_sha256"])
                    self.assertEqual(ledgers["uniform16"]["row_multiset_sha256"],
                                     ledgers["semantic16"]["row_multiset_sha256"])
                    self.assertEqual(ledgers["uniform8"]["by_stage"][stage],
                                     2048 if not prior else 1536)
                    self.assertEqual(ledgers["uniform16"]["by_stage"][stage],
                                     2048 if not prior else 1024)

    def test_semantic_schedule_materially_changes_cohort_composition(self):
        args = dict(seed=503, stage="V02.AND", block=0,
                    prior=("V00.BOOLEAN", "V01.NOT"))
        uniform = c.ledger(c.training_batches(arm="uniform8", **args), stage=args["stage"])
        grouped = c.ledger(c.training_batches(arm="semantic8", **args), stage=args["stage"])
        sham = c.ledger(c.training_batches(arm="sham8", **args), stage=args["stage"])
        self.assertEqual(uniform["row_multiset_sha256"], grouped["row_multiset_sha256"])
        self.assertNotEqual(uniform["row_order_sha256"], grouped["row_order_sha256"])
        self.assertNotEqual(grouped["row_order_sha256"], sham["row_order_sha256"])
        self.assertGreater(grouped["semantic_pair_count"], uniform["semantic_pair_count"])
        self.assertGreater(grouped["semantic_pair_count"], sham["semantic_pair_count"])
        self.assertGreater(grouped["cross_skill_equivalence_pairs"],
                           uniform["cross_skill_equivalence_pairs"])
        self.assertGreater(grouped["cross_skill_same_valuation_equivalent"],
                           uniform["cross_skill_same_valuation_equivalent"])
        self.assertGreater(grouped["relation_coexposures_same_valuation"]["relation_01"],
                           uniform["relation_coexposures_same_valuation"]["relation_01"])

    def test_same_arm_schedule_is_replayable(self):
        arguments = dict(seed=521, stage="V01.NOT", block=2, arm="semantic8",
                         prior=("V00.BOOLEAN",))
        a = c.ledger(c.training_batches(**arguments), stage=arguments["stage"])
        b = c.ledger(c.training_batches(**arguments), stage=arguments["stage"])
        self.assertEqual(a, b)

    def test_wrong_seeds_and_stage_rejected(self):
        for config in (dict(seed=999, stage="V01.NOT", block=0, arm="semantic8"),
                       dict(seed=503, stage="V04.FUTURE", block=0, arm="semantic8"),
                       dict(seed=503, stage="V01.NOT", block=5, arm="semantic8")):
            with self.assertRaises(ValueError):
                c.training_batches(**config)

    def test_e9_runner_rejects_dirty_or_unfrozen_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                p.run(Path(tmp) / "wrong-output")

    def test_frozen_manifest_closes_transitive_runtime_imports(self):
        required = {"bilqis_ref/model.py", "bilqis_ref/codec.py",
                    "bilqis_ref/semantics.py", "bilqis_formal/semantics.py",
                    "bilqis_formal/dialogue.py", "bilqis_formal/dialogue_v3.py",
                    "bilqis_formal/course_v3.py", "bilqis_formal/student_v3.py",
                    "bilqis_formal/curriculum_v6.py", "bilqis_formal/controller_v6.py",
                    "bilqis_formal/pilot_v6.py", "tests/test_formal_semantic_v6.py",
                    "docs/formal/SEMANTIC_V06_PROTOCOL.md"}
        self.assertEqual(set(p.SOURCE_FILES), required)

    def test_final_gate_not_consulted_until_full_stage_budget(self):
        trained = []

        def synthetic_block(_model, _optimizer, *, stage, block, **kwargs):
            trained.append((stage, block))
            return {"optimizer_sha256": "unit-fixture"}

        def guarded_gate(_model, stage):
            self.assertEqual(stage, "V00.BOOLEAN")
            self.assertEqual(trained, [(stage, i) for i in range(5)])
            # Failed current exam prevents advancing its dependents.
            return {"accuracy": {"correct": 0, "n": 1}}

        with tempfile.TemporaryDirectory() as tmp:
            with (patch.object(p, "train_block", side_effect=synthetic_block),
                  patch.object(p, "optimizer_steps", side_effect=lambda opt:
                               {len(trained) * c.BLOCK_UPDATES}),
                  patch.object(p, "_gate_score", side_effect=guarded_gate),
                  patch.object(p, "save_checkpoint"),
                  patch.object(p, "_formative", return_value={})):
                report = p._arm_one(Path(tmp) / "unit-arm", seed=503,
                                    arm="semantic8", source_sha=p.locked_source_sha())
        self.assertEqual(report["exposed"], ["V00.BOOLEAN"])
        self.assertEqual(report["accepted"], [])
        self.assertEqual([x["stage"] for x in report["skipped"]],
                         ["V01.NOT", "V02.AND"])

    def test_actual_optimizer_block_and_no_conversational_feedback(self):
        model, _ = initialize(seed=503)
        optimizer = torch.optim.AdamW(model.parameters(), lr=.002, betas=(.9, .95),
                                     eps=1e-8, weight_decay=.01)
        before = sum(float(w.detach().abs().sum()) for w in model.parameters())
        original_input = c.inputs_for
        modes = []
        def observed_input(model, rows, *, mode):
            modes.append(mode)
            return original_input(model, rows, mode=mode)
        with patch.object(c, "inputs_for", side_effect=observed_input):
            result = c.train_block(model, optimizer, seed=503, stage="V00.BOOLEAN",
                                   block=0, arm="semantic8", prior=())
        after = sum(float(w.detach().abs().sum()) for w in model.parameters())
        self.assertNotEqual(before, after)
        self.assertEqual(result["examples"], 64 * 32)
        self.assertGreaterEqual(result["pre_update_errors"], 0)
        self.assertEqual(modes, ["none"] * c.BLOCK_UPDATES)
        self.assertTrue(result["optimizer_sha256"])


if __name__ == "__main__":
    unittest.main()
