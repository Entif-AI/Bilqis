"""Regression coverage for distinct priority and Factory teaching identities."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from bilqis_mlx.factory.teaching import content_digest
from bilqis_mlx.runtime.bamf_operator.evidence import (
    CandidateEvidenceCapture,
    prepare_candidate_evidence_root,
)
from bilqis_mlx.runtime.bamf_operator.evidence_validation import (
    read_candidate_horizon_evidence,
    validate_candidate_horizon_event,
)
from bilqis_mlx.runtime.teacher_observation_capture import store_sidecar


class CandidateEvidenceIdentityTests(unittest.TestCase):
    @staticmethod
    def _selection():
        identity = SimpleNamespace(
            visit_id="visit:edge",
            policy_key="policy:edge",
            to_record=lambda: {
                "visit_id": "visit:edge",
                "policy_key": "policy:edge",
            },
        )
        selection = SimpleNamespace(
            option_id="A.EDGE",
            visit=SimpleNamespace(identity=identity),
            offer=SimpleNamespace(
                capability_id="A.EDGE",
                source_seed=17,
                release_sha256="b" * 64,
            ),
            policy={"lr": 0.001},
        )
        return selection

    @staticmethod
    def _release():
        execution = SimpleNamespace(
            provider_id="provider:edge",
            provider_implementation_sha256="f" * 64,
            variation_axes=("seed",),
            teaching_option_ids=(
                "source.direct/A.EDGE",
                "source.alternate/A.EDGE",
            ),
        )
        release = SimpleNamespace(
            release_sha256="b" * 64,
            execution_plan=SimpleNamespace(
                capability_map={"A.EDGE": execution}),
        )
        return release

    @staticmethod
    def _row():
        return {
            "id": "row:edge",
            "capability": "A.EDGE",
            "tokens": [1, 2, 3],
        }

    @staticmethod
    def _event(receipt):
        return {
            "event": "BAMF_CANDIDATE_REJECTED",
            "generation": 3,
            "student_manifest_sha256": "a" * 64,
            "evidence": {
                "schema": "bilqis.bamf.c16.3-rejection/v2",
                "rejection_journal_ordinal": 1,
                "rejection_attempt_ordinal": 1,
                "visit_id": "visit:edge",
                "selected_policy_key": "policy:edge",
                "selected_option_id": "A.EDGE",
                "capability": "A.EDGE",
                "candidate_optimizer_step": 11,
                "retained_optimizer_step": 10,
                "decision": {"decision": "REJECTED"},
                "candidate_evidence": receipt,
            },
        }

    def _capture(self, root):
        row = self._row()
        release = self._release()
        capture = CandidateEvidenceCapture(
            root,
            self._selection(),
            generation=3,
            accepted_manifest_sha256="a" * 64,
            candidate_attempt_ordinal=1,
            parent_optimizer_step=10,
        )
        capture.delivery(
            release,
            "A.EDGE",
            11,
            (row,),
            option_rows=(row,),
            seed=17,
            controls={"delivered_content_sha256": content_digest((row,))},
        )
        receipt = capture.finalize(
            accepted=False,
            decision={"decision": "REJECTED"},
        )
        return release, receipt

    def _assert_alternate_option_rejected(
            self, root, payload, receipt, event, release):
        forged = {
            **payload,
            "steps": [{
                **payload["steps"][0],
                "delivered_teaching": {
                    **payload["steps"][0]["delivered_teaching"],
                    "option_id": "source.alternate/A.EDGE",
                },
            }],
        }
        forged_receipt = {
            **receipt,
            "object": store_sidecar(root, forged),
        }
        forged_event = {
            **event,
            "evidence": {
                **event["evidence"],
                "candidate_evidence": forged_receipt,
            },
        }
        with self.assertRaises(ValueError):
            validate_candidate_horizon_event(root, forged_event, release)

    def test_priority_option_does_not_replace_factory_teaching_option(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepare_candidate_evidence_root(root)
            release, receipt = self._capture(root)
            payload = read_candidate_horizon_evidence(root, receipt)
            event = self._event(receipt)
            validated = validate_candidate_horizon_event(root, event, release)
            self.assertEqual(payload["proposal"]["selected_option"], "A.EDGE")
            self.assertEqual(
                payload["steps"][0]["delivered_teaching"]["option_id"],
                "source.direct/A.EDGE",
            )
            self.assertEqual(
                validated["steps"][0]["delivered_teaching"]["option_id"],
                "source.direct/A.EDGE",
            )
            self._assert_alternate_option_rejected(
                root, payload, receipt, event, release)


if __name__ == "__main__":
    unittest.main()
