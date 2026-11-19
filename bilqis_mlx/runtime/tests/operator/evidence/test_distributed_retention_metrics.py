"""Post-C05 distributed telemetry belongs to the retention owner."""
import hashlib
import json
from types import SimpleNamespace
import unittest

from bilqis_mlx.runtime.bamf_operator.session_parts.retention import (
    _distributed_retention_metrics,
)


class DistributedRetentionMetricsTests(unittest.TestCase):
    @staticmethod
    def _digest(payload):
        wire = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(wire.encode()).hexdigest()

    def _step(self):
        return SimpleNamespace(realized_cost={
            "c08_distributed_manifest_digest": "a" * 64,
            "c08_distributed_retained_generation": 7,
            "c08_distributed_retained_manifest_sha256": "d" * 64,
            "c08_distributed_logical_batch_digest": "e" * 64,
            "c08_distributed_source_release": "b" * 64,
            "c08_distributed_curriculum_release": "f" * 64,
            "candidate_step_wall_seconds": 4.0,
        })

    def test_accepted_visit_records_retained_gain_and_accepted_rate(self):
        evaluation = SimpleNamespace(decision=SimpleNamespace(
            outcome_scores=(("cap", 1, 2, 4),), policy_sha256="c" * 64))
        observer = SimpleNamespace(record={"retention_wall_seconds": 1.0})
        resource = {"wall_seconds": 2.0, "optimizer_steps": 1}
        decision = SimpleNamespace(
            accepted=True, retention_protection_plan_sha256="1" * 64,
            evaluated_capability_ids=("cap",), broad_certification_trigger=False)
        _distributed_retention_metrics(
            (self._step(),), evaluation, decision,
            observer, resource)
        self.assertEqual(resource["c08_distributed_evaluation_seconds"], 1.0)
        self.assertEqual(
            resource["c08_distributed_accepted_steps_per_hour"], 720.0)
        self.assertEqual(
            resource["c08_distributed_retained_capability_gain"], 0.25)
        self.assertEqual(
            resource["c08_distributed_source_contract_digest"],
            self._digest([{
                "retained_generation": 7,
                "retained_manifest_sha256": "d" * 64,
                "logical_batch_digest": "e" * 64,
                "source_release": "b" * 64,
                "curriculum_release": "f" * 64,
            }]))
        self.assertEqual(
            resource["c08_distributed_evaluation_contract_digest"],
            self._digest({
                "policy_sha256": "c" * 64,
                "retention_protection_plan_sha256": "1" * 64,
                "evaluated_capability_ids": ("cap",),
                "broad_certification_trigger": False,
            }))

    def test_rejected_visit_records_zero_retained_gain_and_accepted_rate(self):
        evaluation = SimpleNamespace(decision=SimpleNamespace(
            outcome_scores=(("cap", 2, 1, 4),), policy_sha256="c" * 64))
        observer = SimpleNamespace(record={"retention_wall_seconds": 1.0})
        resource = {"wall_seconds": 2.0, "optimizer_steps": 1}
        _distributed_retention_metrics(
            (self._step(),), evaluation, SimpleNamespace(
                accepted=False, evaluated_capability_ids=()),
            observer, resource)
        self.assertEqual(resource["c08_distributed_accepted_steps_per_hour"], 0.0)
        self.assertEqual(
            resource["c08_distributed_retained_capability_gain"], 0.0)


if __name__ == "__main__":
    unittest.main()
