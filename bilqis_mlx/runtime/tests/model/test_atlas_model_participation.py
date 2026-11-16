"""Exact B11 loss-read participation projected into B09 authority."""
from types import SimpleNamespace
import unittest

from bilqis_mlx.learning.atlas_readout import DecisionKind, RoleCandidate
from bilqis_mlx.semantics.frame_schema import ConceptRef
from bilqis_mlx.runtime.atlas_model_participation import _executed_readout_parameters
from bilqis_mlx.runtime.atlas_model_training import _loss_participation
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2


RELEASE = "a" * 64


def _concept(name, index):
    return ConceptRef(name, RELEASE, index, ("Entity",), f"source:{name}")


class LossParticipationTests(unittest.TestCase):
    def test_never_executed_readout_head_is_not_reported_as_execution(self):
        plan = SimpleNamespace(decisions=(
            SimpleNamespace(decision_id="control", depends_on=()),
            SimpleNamespace(decision_id="role", depends_on=("control",)),
            SimpleNamespace(decision_id="epistemic", depends_on=("role",)),
        ))
        output = SimpleNamespace(decisions=(
            SimpleNamespace(decision_id="control", kind=DecisionKind.CONTROL),
            SimpleNamespace(decision_id="role", kind=DecisionKind.ROLE),
        ))

        names = _executed_readout_parameters(plan, output)

        self.assertIn("readout.control", names)
        self.assertIn("readout.role_query", names)
        self.assertIn("readout.feedback", names)
        self.assertNotIn("readout.epistemic", names)
        self.assertNotIn("readout.epistemic_bias", names)

    def test_loss_owner_records_denominators_feedback_and_role_reads(self):
        parent = _concept("concept:parent", 3)
        bank_rows = ModelTopologySpecV2.semantic_bank_rows
        left = _concept("concept:left", bank_rows + 1)
        right = _concept("concept:right", bank_rows + 2)
        role_candidates = (
            RoleCandidate("frame:test", 1, "agent", 0),
            RoleCandidate("frame:test", 1, "theme", 0),
        )
        specs = (
            SimpleNamespace(
                decision_id="parent", role_id="agent", depends_on=()),
            SimpleNamespace(
                decision_id="role", role_id=None, depends_on=("parent",)),
            SimpleNamespace(
                decision_id="value", role_id="theme", depends_on=("role",)),
        )
        output = SimpleNamespace(
            plan=SimpleNamespace(decisions=specs),
            decisions=(
                SimpleNamespace(
                    decision_id="parent", kind=DecisionKind.VALUE,
                    candidates=(parent,)),
                SimpleNamespace(
                    decision_id="role", kind=DecisionKind.ROLE,
                    candidates=role_candidates),
                SimpleNamespace(
                    decision_id="value", kind=DecisionKind.VALUE,
                    candidates=(left, right)),
            ),
            committed=(
                SimpleNamespace(decision_id="parent", value=parent),
                SimpleNamespace(decision_id="role", value=role_candidates[0]),
                SimpleNamespace(decision_id="value", value=left),
            ),
        )
        record = SimpleNamespace(
            role_map=(("NONE", 0), ("agent", 2), ("theme", 3)))
        result = _loss_participation(
            output,
            (SimpleNamespace(decision_id="role"),
             SimpleNamespace(decision_id="value")),
            {"role": True, "value": True},
            record,
        )

        self.assertEqual(result[0], ((0, 3),))
        self.assertEqual(result[1], ((1, 1), (1, 2)))
        self.assertEqual(result[2], (("role", 2), ("role", 3)))
        self.assertEqual(
            result[3], (("role", 0), ("role", 2), ("role", 3)))


if __name__ == "__main__":
    unittest.main()
