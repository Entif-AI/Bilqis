"""Every residual operator error gets a safe resolution posture."""
from unittest import TestCase

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.runtime.operator_recovery import error_code, recovery_advice


class OperatorRecoveryTests(TestCase):
    def test_rejection_order_failure_has_rejection_specific_recovery(self):
        try:
            ErrorBus.Raise(
                SCHOOL.MODEL_TOPOLOGY.INVALID,
                reason="BAMF_PRIORITY_REJECTION_ORDER_INVALID")
        except ValueError as error:
            advice = recovery_advice(error)
        self.assertEqual(advice.disposition, "PRESERVE_AND_DIAGNOSE")
        self.assertIn("rejection journal", advice.next_action.lower())

    def test_known_operator_configuration_error_has_exact_action(self):
        advice = recovery_advice(ValueError(
            "HUMAN_TRAINER_NEW_RUN_HAS_EXISTING_CONTENT"))
        self.assertEqual(advice.disposition, "OPERATOR_ACTION")
        self.assertIn("--resume", advice.next_action)

    def test_internal_empty_cohort_is_not_presented_as_human_data_debt(self):
        advice = recovery_advice(ValueError("COHORT_EMPTY"))
        self.assertEqual(advice.disposition, "INTERNAL_RECOVERY_REQUIRED")
        self.assertIn("empty assessment cohort", advice.next_action)

    def test_custody_drift_stays_fail_closed_with_a_repair_direction(self):
        advice = recovery_advice(ValueError("FACTORY_RELEASE_RUNTIME_SOURCE_ADAPTER_DRIFT"))
        self.assertEqual(advice.disposition, "PRESERVE_AND_REPAIR")
        self.assertIn("durable checkpoint", advice.next_action)

    def test_lesson_capacity_drift_is_not_reported_as_custody_mismatch(self):
        advice = recovery_advice(ValueError(
            "LEARNING_EXPERIMENT_WEAKNESS_TARGET_CAPACITY_DRIFT"))
        self.assertEqual(advice.disposition, "INTERNAL_RECOVERY_REQUIRED")
        self.assertIn("lesson capacity", advice.next_action)
        self.assertNotIn(
            "identity or custody evidence disagrees",
            advice.next_action.lower())

    def test_school_state_drift_has_specific_operator_diagnostics(self):
        advice = recovery_advice(ValueError(
            "INVALID_OR_DRIFTED_SCHOOL_STATE: course_digest saved=abc expected=def"))
        self.assertEqual(advice.disposition, "PRESERVE_AND_DIAGNOSE")
        self.assertIn("--dry-run --resume --verify-source", advice.next_action)
        self.assertIn("Do not hand-edit state.json", advice.next_action)
        self.assertIn("OPERATOR_FIELD_MANUAL", advice.next_action)

    def test_exhaustion_and_missing_artifact_have_distinct_recovery_postures(self):
        self.assertEqual(
            recovery_advice("HUMAN_TRAINER_FRESH_GENERALIZATION_COHORT_EXHAUSTED").disposition,
            "RETRY_OR_REGENERATE")
        self.assertEqual(
            recovery_advice("HUMAN_TRAINER_SAVED_COHORT_MISSING").disposition,
            "RECONSTRUCT_OR_RESTORE")

    def test_unknown_errors_still_preserve_state_and_request_diagnosis(self):
        advice = recovery_advice(RuntimeError("SOMETHING_NEW:details"))
        self.assertEqual(error_code("SOMETHING_NEW:details"), "SOMETHING_NEW")
        self.assertEqual(advice.disposition, "PRESERVE_AND_REPORT")
        self.assertTrue(advice.next_action)

    def test_policy_and_contract_failures_are_not_mistaken_for_retryable_noise(self):
        self.assertEqual(
            recovery_advice("HUMAN_TRAINER_EXTERNAL_SOURCE_ROOT_FORBIDDEN").disposition,
            "AUTHORITY_OR_POLICY_BLOCK")
        self.assertEqual(
            recovery_advice("ASSESSMENT_NOT_COMPLETE_ACTIVE_POOL").disposition,
            "CORRECT_INPUT_OR_STATE")
