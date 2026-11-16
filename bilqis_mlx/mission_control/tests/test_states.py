"""Explicit degraded-state and compatibility semantics for CP02."""
from dataclasses import FrozenInstanceError, replace
import math
import unittest

from bilqis_mlx.mission_control.codec import (
    canonical_json, decode_json, decode_record, encode_record,
)
from bilqis_mlx.mission_control.envelopes import (
    EventEnvelope, PartialEnvelope, StaleEnvelope, StreamPosition,
    UnavailableEnvelope, UnavailableReason,
)
from bilqis_mlx.mission_control.model import (
    AuthorityClass, ContractErrorCode, CoverageState, DataValue,
    MAX_WIRE_INTEGER, MissionControlContractError, RecordMeta,
    ValueOrigin, ValueState,
)
from bilqis_mlx.mission_control.operator import (
    ActionParameter, ActionReceiptState, OperatorActionReceipt,
    OperatorActionReceiptV2, OperatorActionRequest, OperatorActionRequestV2,
)
from bilqis_mlx.mission_control.snapshots import SchoolSnapshot
from bilqis_mlx.mission_control.snapshots import RunContext
from bilqis_mlx.mission_control.tests.samples import RUN, SAMPLES, meta


class MissionControlStateTests(unittest.TestCase):
    def test_absent_values_are_explicit_states_not_zero_sentinels(self):
        for state in (
            ValueState.MISSING, ValueState.UNKNOWN,
            ValueState.DENIED, ValueState.UNAVAILABLE,
        ):
            with self.subTest(state=state):
                value = DataValue(state, None, None)
                self.assertIsNone(value.value)
                self.assertIsNone(value.origin)
        measured = DataValue(ValueState.PRESENT, ValueOrigin.MEASURED, 0, "count")
        derived = DataValue(ValueState.PRESENT, ValueOrigin.DERIVED, 0, "count")
        self.assertNotEqual(measured.origin, derived.origin)

    def test_record_authority_variants_round_trip_literally(self):
        for authority in AuthorityClass:
            with self.subTest(authority=authority):
                record = RunContext(
                    replace(meta("authority-record"), authority=authority),
                    "READY",
                    42,
                    "ASSESS_MAIN",
                )
                decoded = decode_json(canonical_json(record))
                self.assertEqual(decoded.meta.authority, authority)
                self.assertEqual(decoded, record)

    def test_lone_surrogates_are_outside_the_wire_domain(self):
        surrogate = chr(0xD800)
        with self.assertRaises(MissionControlContractError):
            RunContext(meta("surrogate-record"), surrogate, 42, "ASSESS_MAIN")
        with self.assertRaises(MissionControlContractError):
            DataValue(ValueState.PRESENT, ValueOrigin.MEASURED, surrogate)
        with self.assertRaises(MissionControlContractError):
            ActionParameter("value", surrogate)

        sample = next(sample for sample in SAMPLES if type(sample) is RunContext)
        wire = canonical_json(sample).decode("utf-8")
        forged = wire.replace(
            '"run_state":"READY"',
            '"run_state":"\\ud800"',
            1,
        )
        with self.assertRaises(MissionControlContractError):
            decode_json(forged)

    def test_absent_values_round_trip_through_a_real_snapshot(self):
        school = next(sample for sample in SAMPLES if type(sample) is SchoolSnapshot)
        for state in (
            ValueState.MISSING, ValueState.UNKNOWN,
            ValueState.DENIED, ValueState.UNAVAILABLE,
        ):
            with self.subTest(state=state):
                candidate = replace(
                    school,
                    capability_count=DataValue(state, None, None),
                )
                self.assertEqual(decode_json(canonical_json(candidate)), candidate)

    def test_degraded_envelopes_are_first_class_records(self):
        envelope_types = {type(sample) for sample in SAMPLES if type(sample) in (
            UnavailableEnvelope, StaleEnvelope, PartialEnvelope,
        )}
        self.assertEqual(envelope_types, {UnavailableEnvelope, StaleEnvelope, PartialEnvelope})

    def test_every_unavailable_reason_round_trips_literally(self):
        for reason in UnavailableReason:
            with self.subTest(reason=reason):
                refs = {} if reason is UnavailableReason.DENIED else {
                    "source_refs": ("source:a",),
                    "evidence_refs": ("evidence:a",),
                    "receipt_refs": ("receipt:a",),
                }
                unavailable_meta = RecordMeta(
                    record_id=f"unavailable:{reason.value}",
                    run=None,
                    materialized_at=120,
                    observed_at=None,
                    as_of=118,
                    coverage=CoverageState.UNKNOWN,
                    authority=AuthorityClass.DERIVED,
                    **refs,
                )
                envelope = UnavailableEnvelope(
                    unavailable_meta, "resource:a", reason, None,
                )
                self.assertEqual(decode_json(canonical_json(envelope)), envelope)

    def test_denied_envelope_carries_no_source_or_evidence_leakage(self):
        meta = RecordMeta(
            record_id="denied", run=None, materialized_at=120,
            observed_at=None, as_of=118, coverage=CoverageState.UNKNOWN,
            authority=AuthorityClass.DERIVED,
        )
        denied = UnavailableEnvelope(meta, "private-view", UnavailableReason.DENIED,
                                     "policy:mission-control")
        self.assertEqual(denied.meta.source_refs, ())
        self.assertEqual(denied.meta.evidence_refs, ())

        leaking_meta = replace(meta, run=RUN)
        with self.assertRaises(MissionControlContractError):
            UnavailableEnvelope(
                leaking_meta, "private-view", UnavailableReason.DENIED, None,
            )

    def test_degraded_envelope_metadata_cannot_contradict_the_envelope(self):
        with self.assertRaises(MissionControlContractError):
            UnavailableEnvelope(
                meta("unavailable-complete", run=None),
                "resource:a", UnavailableReason.MISSING, None,
            )
        with self.assertRaises(MissionControlContractError):
            PartialEnvelope(meta("partial-complete"), "school", ("field",))
        with self.assertRaises(MissionControlContractError):
            StaleEnvelope(
                meta("stale-mismatch", coverage=CoverageState.PARTIAL),
                "school", 100, 118,
            )
        with self.assertRaises(MissionControlContractError):
            StaleEnvelope(
                meta("stale-future", coverage=CoverageState.PARTIAL, as_of=100),
                "school", 100, 121,
            )

    def test_action_acknowledgement_cannot_masquerade_as_completion(self):
        complete = next(sample for sample in SAMPLES if type(sample) is OperatorActionReceipt)
        self.assertEqual(complete.state, ActionReceiptState.COMPLETED)
        self.assertIsNotNone(complete.postcondition_ref)
        pending = OperatorActionReceipt(
            complete.meta, "request-2", "operation-2", ActionReceiptState.ACCEPTED,
            120, None, None,
        )
        self.assertIsNone(pending.postcondition_ref)
        with self.assertRaises(MissionControlContractError):
            OperatorActionReceipt(
                complete.meta, "request-3", "operation-3", ActionReceiptState.ACCEPTED,
                120, "postcondition:forbidden", None,
            )

    def test_cp05_action_v2_is_pre_run_without_changing_v1_run_binding(self):
        v1 = next(
            sample for sample in SAMPLES if type(sample) is OperatorActionRequest)
        with self.assertRaises(MissionControlContractError):
            replace(v1, meta=replace(v1.meta, run=None))

        v2 = next(
            sample for sample in SAMPLES if type(sample) is OperatorActionRequestV2)
        self.assertIsNone(v2.meta.run)
        self.assertFalse(v2.human_authorized)
        decoded = decode_json(canonical_json(v2))
        self.assertEqual(decoded, v2)
        self.assertIsNone(decoded.meta.run)

        receipt = next(
            sample for sample in SAMPLES if type(sample) is OperatorActionReceiptV2)
        self.assertIsNone(receipt.meta.run)
        self.assertEqual(receipt.request_sha256, "1" * 64)
        self.assertTrue(receipt.target_ref.startswith("command-target:"))

    def test_event_cursor_is_order_metadata_not_event_identity(self):
        event = next(sample for sample in SAMPLES if type(sample) is EventEnvelope)
        self.assertEqual(event.event_id, "event-9")
        self.assertEqual(event.position.stream_id, "run-7:candidate")
        self.assertEqual(event.position.epoch_id, "epoch-1")
        self.assertEqual(event.position.ordinal, 9)
        self.assertEqual(event.position.previous_cursor_sha256, "4" * 64)
        self.assertNotEqual(event.event_id, event.position.cursor_sha256)

    def test_event_cursor_cannot_be_reused_for_a_different_position(self):
        event = next(sample for sample in SAMPLES if type(sample) is EventEnvelope)
        forged_position = type(event.position)(
            event.position.stream_id,
            event.position.epoch_id,
            event.position.ordinal + 1,
            event.position.cursor_sha256,
            event.position.previous_cursor_sha256,
        )
        with self.assertRaises(MissionControlContractError):
            EventEnvelope(
                event.meta,
                event.event_id,
                forged_position,
                event.event_family,
                event.payload_schema_version,
                event.payload_record_id,
                event.payload_sha256,
                event.payload_ref,
            )

    def test_stream_predecessor_shape_is_total_and_cursor_binds_it(self):
        event = next(sample for sample in SAMPLES if type(sample) is EventEnvelope)
        with self.assertRaises(MissionControlContractError):
            StreamPosition("stream", "epoch", 0, "1" * 64, "2" * 64)
        with self.assertRaises(MissionControlContractError):
            StreamPosition("stream", "epoch", 1, "1" * 64, None)
        forged = replace(event.position, previous_cursor_sha256="2" * 64)
        with self.assertRaises(MissionControlContractError):
            replace(event, position=forged)

    def test_action_parameters_reject_non_finite_float_values(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(MissionControlContractError):
                    ActionParameter("weight", value)

    def test_action_parameter_duplicate_keys_fail_with_contract_error(self):
        request = next(sample for sample in SAMPLES if type(sample) is OperatorActionRequest)
        with self.assertRaises(MissionControlContractError):
            replace(
                request,
                parameters=(ActionParameter("x", 1), ActionParameter("x", "one")),
            )

    def test_unknown_and_missing_schema_errors_are_deterministic(self):
        for payload, code in (
            ({}, ContractErrorCode.SCHEMA_MISSING),
            ({"schema_version": "bilqis.bamf.mission-control.operator-view/v999"},
             ContractErrorCode.SCHEMA_UNSUPPORTED),
        ):
            with self.subTest(code=code):
                with self.assertRaises(MissionControlContractError) as raised:
                    decode_record(payload)
                self.assertEqual(raised.exception.code, code)
                self.assertTrue(str(raised.exception).startswith(code.value))

    def test_duplicate_json_keys_and_non_json_constants_fail_closed(self):
        sample = SAMPLES[0]
        wire = canonical_json(sample).decode("utf-8")
        needle = f'"schema_version":"{sample.schema_version}"'
        forged = wire.replace(
            needle,
            f'"schema_version":"{sample.schema_version}/forged",{needle}',
            1,
        )
        for payload in (forged, '{"schema_version":NaN}'):
            with self.subTest(payload=payload[:40]):
                with self.assertRaises(MissionControlContractError) as raised:
                    decode_json(payload)
                self.assertEqual(raised.exception.code, ContractErrorCode.PAYLOAD_INVALID)

    def test_integer_wire_domain_matches_javascript_safe_integer_semantics(self):
        sample = next(sample for sample in SAMPLES if type(sample) is RunContext)
        wire = canonical_json(sample).decode("utf-8")
        decimal_integral = wire.replace(
            f'"generation":{sample.meta.run.generation}',
            f'"generation":{sample.meta.run.generation}.0',
            1,
        )
        self.assertEqual(
            decode_json(decimal_integral).meta.run.generation,
            sample.meta.run.generation,
        )

        unsafe = wire.replace(
            f'"generation":{sample.meta.run.generation}',
            f'"generation":{MAX_WIRE_INTEGER + 1}',
            1,
        )
        with self.assertRaises(MissionControlContractError):
            decode_json(unsafe)

        with self.assertRaises(MissionControlContractError):
            replace(sample.meta.run, generation=MAX_WIRE_INTEGER + 1)
        with self.assertRaises(MissionControlContractError):
            DataValue(
                ValueState.PRESENT,
                ValueOrigin.MEASURED,
                MAX_WIRE_INTEGER + 1,
            )

    def test_scalar_union_preserves_literal_float_identity(self):
        scalar = DataValue(
            ValueState.PRESENT,
            ValueOrigin.MEASURED,
            7.0,
            "count",
        )
        school = next(sample for sample in SAMPLES if type(sample) is SchoolSnapshot)
        school = replace(school, mastered_count=scalar)
        decoded = decode_json(canonical_json(school))
        self.assertIs(type(decoded.mastered_count.value), float)
        self.assertEqual(decoded.mastered_count.value, 7.0)
        self.assertEqual(canonical_json(decoded), canonical_json(school))

        action = next(
            sample for sample in SAMPLES if type(sample) is OperatorActionRequest
        )
        action = replace(action, parameters=(ActionParameter("ratio", 7.0),))
        decoded_action = decode_json(canonical_json(action))
        self.assertIs(type(decoded_action.parameters[0].value), float)
        self.assertEqual(decoded_action.parameters[0].value, 7.0)
        self.assertEqual(canonical_json(decoded_action), canonical_json(action))

    def test_extra_wire_field_fails_closed_and_records_are_frozen(self):
        sample = SAMPLES[0]
        payload = encode_record(sample)
        payload["surprise"] = True
        with self.assertRaises(MissionControlContractError) as raised:
            decode_record(payload)
        self.assertEqual(raised.exception.code, ContractErrorCode.PAYLOAD_INVALID)
        with self.assertRaises(FrozenInstanceError):
            sample.stage = "MUTATED"


if __name__ == "__main__":
    unittest.main()
