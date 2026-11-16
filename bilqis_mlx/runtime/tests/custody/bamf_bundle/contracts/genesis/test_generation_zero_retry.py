"""Generation-zero retries authenticate exact state and recover durable custody."""
from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.bamf_bundle.publication as publication
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import publish_initial_generation
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    genesis_preparation, shape_patch,
)


class GenerationZeroRetryTests(unittest.TestCase):
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

    def _prepare(self, *, run_seed):
        with shape_patch():
            return genesis_preparation(run_seed=run_seed)

    def _publish(self, prepared):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_initial_generation(
                self.run, prepared, reserve_gib=0.)

    def test_completed_retry_rejects_post_publication_numerical_mutation(self):
        prepared = self._prepare(run_seed=307)
        first = self._publish(prepared)
        before = json.loads((self.run / "bamf-state.json").read_text())
        state = prepared.candidate.retained_state
        optimizer = state.optimizer
        name, parameter = next(iter(optimizer.parameters.items()))
        parameters = dict(optimizer.parameters)
        parameters[name] = parameter + 1
        tampered_state = replace(
            state, optimizer=replace(optimizer, parameters=parameters))
        object.__setattr__(
            prepared, "candidate",
            replace(prepared.candidate, retained_state=tampered_state))

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), \
                self.assertRaises(BilqisError) as failure:
            publish_initial_generation(self.run, prepared, reserve_gib=0.)

        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_BINDING_DRIFT")
        self.assertEqual(
            json.loads((self.run / "bamf-state.json").read_text()), before)
        self.assertEqual(before, first)

    def test_post_pointer_crash_retry_reconciles_pending_delivery_before_success(self):
        prepared = self._prepare(run_seed=312)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), \
                patch.object(
                    publication, "reconcile_bamf_outbox",
                    side_effect=RuntimeError("outbox crash")):
            with self.assertRaisesRegex(RuntimeError, "outbox crash"):
                publish_initial_generation(self.run, prepared, reserve_gib=0.)

        before = json.loads((self.run / "bamf-state.json").read_text())
        self.assertFalse((self.run / "events.jsonl").exists())

        retried = self._publish(prepared)

        self.assertEqual(retried, before)
        events = [
            json.loads(line)
            for line in (self.run / "events.jsonl").read_text().splitlines()
        ]
        self.assertEqual([event["event"] for event in events], ["FIXTURE_GENESIS"])
        self.assertEqual([event["optimizer_step"] for event in events], [0])

    def test_unpointed_conflicting_genesis_cannot_replace_durable_acceptance(self):
        prepared = self._prepare(run_seed=313)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), \
                patch.object(
                    publication, "_atomic_pointer",
                    side_effect=RuntimeError("pointer crash")):
            with self.assertRaisesRegex(RuntimeError, "pointer crash"):
                publish_initial_generation(self.run, prepared, reserve_gib=0.)
        foreign = self._prepare(run_seed=317)

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), \
                self.assertRaises(BilqisError):
            publish_initial_generation(self.run, foreign, reserve_gib=0.)

        self.assertFalse((self.run / "bamf-state.json").exists())
        self.assertEqual(len(tuple((self.run / "bamf-bundles").iterdir())), 1)
        self.assertEqual(len(tuple((self.run / "bamf-acceptance").iterdir())), 1)

if __name__ == "__main__":
    unittest.main()
