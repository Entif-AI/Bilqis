"""Cold semantic validation for C16.3 candidate-horizon evidence."""
from __future__ import annotations

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.teaching import (
    content_digest, describe_delivered_teaching,
)
from bilqis_mlx.runtime import state
from bilqis_mlx.runtime.teacher_observation_capture import read_sidecar

from .evidence import (
    EVIDENCE_SCHEMA, PERSISTENCE_SCHEMA, REFERENCE_SCHEMA, candidate_attempt_id,
)
from .session_parts.distributed_receipt_validation import (
    validate_distributed_step_receipts,
)


_HORIZON_ENVELOPE_RECORDS = 2
_MIN_HORIZON_LOGICAL_RECORDS = 3


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_FIRST_STUDENT.INVALID, reason=reason)


def _persistence(receipt):
    persistence = receipt.get("persistence") if isinstance(receipt, dict) else None
    if (not isinstance(persistence, dict)
            or persistence.get("schema") != PERSISTENCE_SCHEMA
            or type(persistence.get("bytes_written")) is not int
            or persistence["bytes_written"] < 0
            or persistence.get("file_fsyncs") not in (0, 1)
            or persistence.get("directory_fsyncs") not in (0, 1)
            or type(persistence.get("evidence_objects")) is not int
            or persistence["evidence_objects"] not in (0, 1)
            or type(persistence.get("logical_records")) is not int
            or persistence["logical_records"] < _MIN_HORIZON_LOGICAL_RECORDS
            or type(persistence.get("unique_source_objects")) is not int
            or persistence["unique_source_objects"] < 1
            or type(persistence.get("delivery_records")) is not int
            or persistence["delivery_records"] < 1
            or type(persistence.get("persistence_seconds")) not in (int, float)
            or type(persistence["persistence_seconds"]) is bool
            or persistence["persistence_seconds"] < 0):
        _invalid("BAMF_C16_3_EVIDENCE_PERSISTENCE_INVALID")
    return persistence


def _payload_parts(receipt, persistence, payload):
    proposal = payload.get("proposal")
    if (payload.get("schema") != EVIDENCE_SCHEMA
            or not isinstance(proposal, dict)
            or payload.get("attempt_id") != receipt.get("attempt_id")
            or payload.get("proposal_id") != receipt.get("proposal_id")
            or state._fingerprint(proposal) != receipt.get("proposal_id")):
        _invalid("BAMF_C16_3_EVIDENCE_REFERENCE_DRIFT")
    expected_attempt = candidate_attempt_id(
        proposal.get("generation"), proposal.get("accepted_manifest_sha256"),
        proposal.get("visit_id"), proposal.get("candidate_attempt_ordinal"))
    if expected_attempt != payload.get("attempt_id"):
        _invalid("BAMF_C16_3_EVIDENCE_ATTEMPT_DRIFT")
    objects, steps, outcome = (
        payload.get("source_objects"), payload.get("steps"), payload.get("outcome"))
    if (not isinstance(objects, dict) or not objects
            or not isinstance(steps, list) or not steps
            or not isinstance(outcome, dict) or type(outcome.get("accepted")) is not bool
            or not isinstance(outcome.get("decision"), dict)):
        _invalid("BAMF_C16_3_EVIDENCE_PAYLOAD_INVALID")
    if (persistence["logical_records"]
            != len(steps) + _HORIZON_ENVELOPE_RECORDS
            or persistence["unique_source_objects"] != len(objects)
            or persistence["delivery_records"] != len(steps)
            or persistence["evidence_objects"] != int(persistence["bytes_written"] > 0)):
        _invalid("BAMF_C16_3_EVIDENCE_PERSISTENCE_INVALID")
    return proposal, objects, steps, outcome


def _validate_objects(objects):
    for digest, value in objects.items():
        if state._fingerprint(value) != digest:
            _invalid("BAMF_C16_3_EVIDENCE_OBJECT_DRIFT")


def _step_rows(step, objects, proposal, previous):
    ordinal = step.get("step") if isinstance(step, dict) else None
    positions = step.get("positions") if isinstance(step, dict) else None
    if (type(ordinal) is not int or ordinal != previous + 1
            or step.get("capability") != proposal.get("capability")
            or not isinstance(positions, list) or not positions):
        _invalid("BAMF_C16_3_EVIDENCE_STEP_ORDER_INVALID")
    rows, selected = [], []
    for position in positions:
        reference = position.get("row") if isinstance(position, dict) else None
        roles = position.get("roles") if isinstance(position, dict) else None
        if (not isinstance(reference, str) or reference not in objects
                or not isinstance(roles, list) or not roles):
            _invalid("BAMF_C16_3_EVIDENCE_OBJECT_DRIFT")
        row = objects[reference]
        rows.append(row)
        if "selected_option" in roles:
            selected.append((row, position))
    return ordinal, rows, selected


def _validate_step_delivery(step, rows, selected):
    controls = step.get("controls")
    if (not isinstance(controls, dict)
            or controls.get("delivered_content_sha256") != content_digest(rows)):
        _invalid("BAMF_C16_3_EVIDENCE_DELIVERY_DRIFT")
    delivery = step.get("delivered_teaching")
    if not selected:
        if delivery is not None:
            _invalid("BAMF_C16_3_EVIDENCE_DELIVERY_DRIFT")
        return
    selected_rows = [item[0] for item in selected]
    providers = {item[1].get("provider_id") for item in selected}
    implementations = {
        item[1].get("provider_implementation_sha256") for item in selected}
    if (not isinstance(delivery, dict)
            or delivery.get("specimen_content_sha256") != content_digest(selected_rows)
            or delivery.get("specimen_ids") != list(dict.fromkeys(
                row["id"] for row in selected_rows))
            or providers != {delivery.get("provider_id")}
            or implementations != {delivery.get("provider_implementation_sha256")}):
        _invalid("BAMF_C16_3_EVIDENCE_DELIVERY_DRIFT")


def read_candidate_horizon_evidence(run_dir, receipt: dict) -> dict:
    """Cold-read a staged or committed horizon and verify internal semantics."""
    if (not isinstance(receipt, dict) or receipt.get("schema") != REFERENCE_SCHEMA
            or not isinstance(receipt.get("object"), dict)):
        _invalid("BAMF_C16_3_EVIDENCE_REFERENCE_INVALID")
    persistence = _persistence(receipt)
    payload = read_sidecar(run_dir, receipt["object"])
    proposal, objects, steps, _outcome = _payload_parts(receipt, persistence, payload)
    _validate_objects(objects)
    previous = proposal.get("parent_optimizer_step")
    if type(previous) is not int or previous < 0:
        _invalid("BAMF_C16_3_EVIDENCE_STEP_ORDER_INVALID")
    for step in steps:
        previous, rows, selected = _step_rows(step, objects, proposal, previous)
        _validate_step_delivery(step, rows, selected)
    return payload


def _event_selected_rows(step, payload, capability_map):
    selected_rows = []
    for position in step["positions"]:
        row = payload["source_objects"][position["row"]]
        owner = capability_map.get(row.get("capability"))
        if ((owner is None) != (position.get("provider_id") is None)
                or (owner is not None
                    and (position.get("provider_id") != owner.provider_id
                         or position.get("provider_implementation_sha256")
                         != owner.provider_implementation_sha256))):
            _invalid("BAMF_C16_3_EVIDENCE_PROVIDER_DRIFT")
        if "selected_option" in position["roles"]:
            selected_rows.append(row)
    return selected_rows


def _validate_released_delivery(step, selected_rows, release, capability_map):
    capability_owner = capability_map.get(step["capability"])
    teaching_options = getattr(capability_owner, "teaching_option_ids", ())
    if not isinstance(teaching_options, tuple) or not teaching_options:
        _invalid("BAMF_C16_3_EVIDENCE_DELIVERY_DRIFT")
    expected_option = teaching_options[0]
    delivered = step.get("delivered_teaching")
    if selected_rows and not isinstance(delivered, dict):
        _invalid("BAMF_C16_3_EVIDENCE_DELIVERY_DRIFT")
    delivery_option = (
        delivered.get("option_id") if isinstance(delivered, dict) else None)
    if selected_rows and delivery_option != expected_option:
        _invalid("BAMF_C16_3_EVIDENCE_DELIVERY_DRIFT")
    expected = (
        describe_delivered_teaching(
            release, step["capability"], expected_option, selected_rows)
        if selected_rows else None)
    if expected is None:
        matched = delivered is None
    else:
        matched = (
            isinstance(delivered, dict)
            and delivered.get("option_id") == expected.option_id
            and delivered.get("provider_id") == expected.provider_id
            and delivered.get("provider_implementation_sha256")
            == expected.provider_implementation_sha256
            and delivered.get("variation_axes") == list(expected.variation_axes)
            and delivered.get("specimen_ids") == list(expected.specimen_ids)
            and delivered.get("specimen_content_sha256")
            == expected.specimen_content_sha256)
    if not matched:
        _invalid("BAMF_C16_3_EVIDENCE_DELIVERY_DRIFT")


def validate_candidate_horizon_event(run_dir, event: dict, release) -> dict:
    """Bind horizon bytes to an already-authoritative accepted/rejection event."""
    if not isinstance(event, dict):
        _invalid("BAMF_C16_3_EVIDENCE_EVENT_INVALID")
    if event.get("event") == "BAMF_C16_3_ACCEPTED":
        receipt, outer, accepted = event.get("candidate_evidence"), event, True
    elif event.get("event") == "BAMF_CANDIDATE_REJECTED":
        outer, accepted = event.get("evidence"), False
        receipt = outer.get("candidate_evidence") if isinstance(outer, dict) else None
    else:
        _invalid("BAMF_C16_3_EVIDENCE_EVENT_INVALID")
    payload = read_candidate_horizon_evidence(run_dir, receipt)
    proposal, steps, outcome = payload["proposal"], payload["steps"], payload["outcome"]
    if getattr(release, "release_sha256", None) != proposal.get("factory_release_sha256"):
        _invalid("BAMF_C16_3_EVIDENCE_RELEASE_DRIFT")
    plan = getattr(release, "execution_plan", None)
    capability_map = getattr(plan, "capability_map", None)
    if not isinstance(capability_map, dict):
        _invalid("BAMF_C16_3_EVIDENCE_RELEASE_INVALID")
    for step in steps:
        selected_rows = _event_selected_rows(step, payload, capability_map)
        _validate_released_delivery(step, selected_rows, release, capability_map)
    validate_distributed_step_receipts(run_dir, proposal, steps)
    last_step = steps[-1]["step"]
    if (outcome["accepted"] is not accepted
            or outer.get("capability") != proposal.get("capability")
            or outer.get("visit_id") != proposal.get("visit_id")
            or outer.get("selected_policy_key") != proposal.get("selected_policy_key")):
        _invalid("BAMF_C16_3_EVIDENCE_EVENT_DRIFT")
    if accepted:
        resource = outer.get("resource")
        if (outer.get("parent_generation") != proposal.get("generation")
                or outer.get("accepted_manifest_sha256")
                != proposal.get("accepted_manifest_sha256")
                or outer.get("candidate_attempt_ordinal")
                != proposal.get("candidate_attempt_ordinal")
                or outer.get("selected_option_id") != proposal.get("selected_option")
                or outer.get("optimizer_step") != last_step or not isinstance(resource, dict)
                or resource.get("optimizer_steps") != len(steps)
                or resource.get("evidence_bytes_written") != receipt["persistence"]["bytes_written"]
                or resource.get("evidence_file_fsyncs") != receipt["persistence"]["file_fsyncs"]
                or resource.get("evidence_directory_fsyncs") != receipt["persistence"]["directory_fsyncs"]
                or resource.get("evidence_objects") != receipt["persistence"]["evidence_objects"]):
            _invalid("BAMF_C16_3_EVIDENCE_EVENT_DRIFT")
    elif (event.get("generation") != proposal.get("generation")
            or event.get("student_manifest_sha256")
            != proposal.get("accepted_manifest_sha256")
            or outer.get("selected_option_id") != proposal.get("selected_option")
            or outer.get("candidate_optimizer_step") != last_step
            or outer.get("retained_optimizer_step") != proposal.get("parent_optimizer_step")
            or outer.get("rejection_journal_ordinal")
            != proposal.get("candidate_attempt_ordinal")
            or outer.get("decision") != outcome.get("decision")):
        _invalid("BAMF_C16_3_EVIDENCE_EVENT_DRIFT")
    return payload


__all__ = (
    "read_candidate_horizon_evidence", "validate_candidate_horizon_event",
)
