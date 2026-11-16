"""ADR-142 baseline lifecycle contract for accepted C05 evidence."""
import unittest

from bilqis_mlx.errors.model import BilqisError
from bilqis_mlx.runtime.baseline.lifecycle import (
    BaselineComparisonIdentity,
    BaselineLifecycleState,
    BaselineLedger,
    _issue_factory_baseline_transition,
    apply_factory_baseline_transition,
)


def _identity(*, policy="7" * 64):
    return BaselineComparisonIdentity(
        capability_id="B.IDBOOLOPS",
        factory_release_sha256="1" * 64,
        semantic_catalog_sha256="2" * 64,
        rubric_sha256="3" * 64,
        scope_sha256="4" * 64,
        policy_sha256=policy,
        source_sha256="5" * 64,
        source_authority_registry_sha256="6" * 64,
        correction_frontier_sha256="8" * 64,
        evaluation_contract_sha256="9" * 64,
        fixed_cohort_sha256="a" * 64,
        evidence_stage="FOUNDATION_ACQUISITION",
    )


def _transition(identity, *, generation=1, evidence="b" * 64,
                candidate="c" * 64, parent_ledger_sha256=None):
    return _issue_factory_baseline_transition(
        identity,
        run_id="fixture-run",
        accepted_generation=generation,
        accepted_parent_manifest_sha256="d" * 64,
        accepted_candidate_sha256=candidate,
        decision_evidence_sha256=evidence,
        parent_ledger_sha256=(parent_ledger_sha256 or BaselineLedger.empty().digest),
    )


class FactoryBaselineLifecycleTest(unittest.TestCase):
    def test_unmeasured_first_measurement_and_cold_resume(self):
        identity = _identity()
        ledger = BaselineLedger.empty()
        self.assertIs(ledger.state_for(identity), BaselineLifecycleState.UNMEASURED)

        established = apply_factory_baseline_transition(
            ledger, _transition(identity))
        self.assertIs(
            established.state_for(identity),
            BaselineLifecycleState.BASELINE_ESTABLISHED,
        )

        cold = BaselineLedger.from_record(established.to_record())
        self.assertEqual(cold.digest, established.digest)
        self.assertIs(
            cold.state_for(identity), BaselineLifecycleState.BASELINE_ESTABLISHED)

    def test_identical_replay_is_idempotent_and_divergent_duplicate_fails_closed(self):
        identity = _identity()
        first = _transition(identity)
        established = apply_factory_baseline_transition(BaselineLedger.empty(), first)
        replay = _transition(
            identity, parent_ledger_sha256=BaselineLedger.empty().digest)
        self.assertEqual(
            apply_factory_baseline_transition(BaselineLedger.empty(), replay),
            established,
        )

        with self.assertRaises(BilqisError):
            apply_factory_baseline_transition(
                established,
                _transition(
                    identity,
                    evidence="e" * 64,
                    parent_ledger_sha256=established.digest,
                ),
            )
        with self.assertRaises(BilqisError):
            BaselineLedger((first.measurement, first.measurement))

    def test_compatible_history_advances_but_incompatible_epoch_is_unmeasured(self):
        identity = _identity()
        first = apply_factory_baseline_transition(
            BaselineLedger.empty(), _transition(identity))
        second = apply_factory_baseline_transition(
            first,
            _transition(
                identity,
                generation=2,
                evidence="f" * 64,
                candidate="0" * 64,
                parent_ledger_sha256=first.digest,
            ),
        )
        self.assertIs(
            second.state_for(identity), BaselineLifecycleState.COMPARABLE_HISTORY)
        self.assertIs(
            second.state_for(_identity(policy="1" * 64)),
            BaselineLifecycleState.UNMEASURED,
        )
        self.assertEqual(len(second.measurements), 2)

    def test_caller_cannot_construct_authorizing_transition(self):
        from bilqis_mlx.runtime.baseline.lifecycle import (
            FactoryBaselineTransition,
        )

        with self.assertRaises(BilqisError):
            FactoryBaselineTransition()


if __name__ == "__main__":
    unittest.main()
