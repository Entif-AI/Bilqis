"""#1333 cadence terminal replay composes authenticated B13/rejection custody."""
import json
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.runtime.active_grade_cadence_replay import (
    authenticated_cadence_attempts,
)


def _cadence(capability="cap"):
    return {
        "schema": "bilqis.bamf.active-grade-cadence-authorization/v1",
        "phase": "MAIN", "phase_round": 0,
        "phase_sha256": "1" * 64, "cadence_sha256": "2" * 64,
        "active_grade_activation_sha256": "3" * 64,
        "active_grade_definition_sha256": "4" * 64,
        "member_census_sha256": "5" * 64,
        "deficit_evidence_sha256": "6" * 64,
        "policy_epoch": 1, "authorized_capability_ids": [capability],
        "disposition": "TEACHING",
    }


def test_accepted_outbox_attempt_is_recovered_even_before_event_delivery(tmp_path):
    (tmp_path / "bamf-state.json").write_text("{}", encoding="utf-8")
    cadence = _cadence()
    event = {
        "event": "BAMF_C16_3_ACCEPTED", "parent_generation": 0,
        "accepted_manifest_sha256": "a" * 64, "capability": "cap",
        "cadence": cadence,
    }
    chain = {
        0: (SimpleNamespace(outbox=()), "a" * 64),
        1: (SimpleNamespace(outbox=(event,)), "b" * 64),
    }
    with patch(
            "bilqis_mlx.runtime.active_grade_cadence_replay._accepted_chain",
            return_value=chain):
        attempts = authenticated_cadence_attempts(tmp_path)
    assert attempts == ((cadence, "cap"),)


def test_rejected_attempt_requires_existing_authenticated_rejection_owner(tmp_path):
    (tmp_path / "bamf-state.json").write_text("{}", encoding="utf-8")
    cadence = _cadence()
    event = {
        "event": "BAMF_CANDIDATE_REJECTED", "generation": 0,
        "evidence": {"schema": "bilqis.bamf.c16.3-rejection/v2",
                     "capability": "cap", "cadence": cadence},
    }
    (tmp_path / "events.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
    parent = SimpleNamespace(outbox=())
    chain = {0: (parent, "a" * 64)}
    with patch(
            "bilqis_mlx.runtime.active_grade_cadence_replay._accepted_chain",
            return_value=chain), patch(
                "bilqis_mlx.runtime.priority_rejection_replay."
                "authenticated_rejection_event", return_value=True) as authenticate:
        attempts = authenticated_cadence_attempts(tmp_path)
    assert attempts == ((cadence, "cap"),)
    authenticate.assert_called_once_with(event, parent, "a" * 64)
