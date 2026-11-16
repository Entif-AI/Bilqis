"""Cheap unit checks for B13.2 cross-process numeric parity helpers."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import mlx.core as mx

from bilqis_mlx import state_dag

from ..retention.factory_retention_live_support import live_factory_context
from ..retention.next_step.factory_retention_next_step_evidence import (
    _compare_numeric_reference, _write_numeric_reference,
)
from ..retention.next_step.factory_retention_next_step_state import (
    _persist_controlled_visit, _persist_unforced_visit,
    _require_sealed_execution, _require_sealed_visit, _seal_execution,
    _verified_visit, natural_next_selection,
)
from ..retention.next_step.factory_retention_next_step_witness import _spawn_cpu_natural


class FactoryRetentionNextStepWitnessTests(unittest.TestCase):
    def test_full_elementwise_reference_detects_unsampled_middle_delta(self):
        original = {
            "gradient/example": mx.array([0.0, 1.0, 2.0, 3.0, 4.0], dtype=mx.float32),
            "delta/m/example": mx.array([0.0, 0.0, 0.0], dtype=mx.float32),
            "loss/total": mx.array(0.5, dtype=mx.float32),
        }
        changed = dict(original)
        changed["gradient/example"] = mx.array(
            [0.0, 1.0, 2.25, 3.0, 4.0], dtype=mx.float32)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.safetensors"
            _write_numeric_reference(path, original)
            exact = _compare_numeric_reference(path, original)
            drift = _compare_numeric_reference(path, changed)
        self.assertEqual(exact["overall"], 0.0)
        self.assertEqual(drift["gradient"], 0.25)
        self.assertEqual(drift["overall"], 0.25)

    def test_numeric_reference_rejects_nonfinite_values(self):
        finite = {"gradient/example": mx.array([0.0], dtype=mx.float32)}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.safetensors"
            _write_numeric_reference(path, finite)
            with self.assertRaisesRegex(AssertionError, "non-finite"):
                _compare_numeric_reference(
                    path,
                    {"gradient/example": mx.array([float("nan")], dtype=mx.float32)},
                )

            path.unlink()
            mx.save_safetensors(
                str(path),
                {"t00000": mx.array([float("nan")], dtype=mx.float32)},
            )
            with self.assertRaisesRegex(AssertionError, "non-finite"):
                _compare_numeric_reference(path, finite)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.safetensors"
            with self.assertRaisesRegex(AssertionError, "non-finite"):
                _write_numeric_reference(
                    path,
                    {"gradient/example": mx.array([float("inf")], dtype=mx.float32)},
                )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reference.safetensors"
            _write_numeric_reference(
                path,
                {"gradient/example": mx.array([-3.0e38], dtype=mx.float32)},
            )
            with self.assertRaisesRegex(AssertionError, "numeric delta non-finite"):
                _compare_numeric_reference(
                    path,
                    {"gradient/example": mx.array([3.0e38], dtype=mx.float32)},
                )

    def test_natural_selection_and_controlled_fixture_reconstruct_without_model(self):
        root = Path.cwd()
        source = (root / "vendor/legacy-v16").resolve()
        if not source.is_dir():
            self.skipTest("pinned legacy source fixture is not mounted")
        context, _ = live_factory_context(root, source)
        student = SimpleNamespace(
            run_id="factory-c05-live", generation=1,
            retained_state=SimpleNamespace(optimizer_step=1))
        published = {
            "manifest_sha256": "a" * 64,
            "bundle": "bamf-bundles/" + "a" * 64,
        }
        with tempfile.TemporaryDirectory() as directory:
            root_dir = Path(directory)
            run_dir = root_dir / "controlled"
            natural_run = root_dir / "natural"
            for state_root in (run_dir, natural_run):
                state_dag.persist(state_root, {
                    "generation": 0,
                    "factory_release_sha256": context.release.release_sha256,
                    "last_exam": None,
                })
            _persist_unforced_visit(
                natural_run, context, published, student)
            natural = natural_next_selection(natural_run, context)
            cold_natural = _spawn_cpu_natural(natural_run, root, source)
            self.assertEqual(natural, cold_natural)
            self.assertEqual(natural["capability"], "A.IDENTITY")
            _persist_controlled_visit(
                run_dir, context, published, student, "B.IDBOOLOPS")
            selected = _verified_visit(run_dir, context)
            fixture = selected[1]["continuation_fixture"]
            for key in (
                    "seed", "row_id", "row_sha256", "policy_key",
                    "policy_sha256", "selection_reason"):
                self.assertIn(key, fixture)
            drifted = list(selected)
            drifted[4] = {**selected[4], "id": selected[4]["id"] + ":drift"}
            with self.assertRaisesRegex(AssertionError, "sealed visit drift"):
                _require_sealed_visit(tuple(drifted))
            plan = SimpleNamespace(
                modality_id="fixture", input_prefix_end=1, decisions=("decision",),
                generation_binding="generation", maximum_decisions=1)
            execution_receipt = {
                **selected[1], "continuation_fixture": dict(fixture)}
            _seal_execution(execution_receipt, plan, ("target",), {"decision": True})
            _require_sealed_execution(
                execution_receipt, plan, ("target",), {"decision": True})
            with self.assertRaisesRegex(AssertionError, "sealed execution drift"):
                _require_sealed_execution(
                    execution_receipt, plan, ("changed",), {"decision": True})
        self.assertEqual(selected[2], "B.IDBOOLOPS")
        self.assertFalse(selected[1]["continuation_fixture"]["scheduler_selected"])
        self.assertTrue(
            selected[1]["continuation_fixture"]["controlled_optimizer_fixture"])


if __name__ == "__main__":
    unittest.main()
