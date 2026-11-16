"""#1298 exact comparable-baseline currentness and partial denominators."""
import unittest

from bilqis_mlx.runtime.baseline.currentness import (
    BaselineComparisonEpoch,
    baseline_coverage,
)
from bilqis_mlx.runtime.baseline.lifecycle import (
    LEGACY_COMPARISON_SCHEMA,
    BaselineLedger,
    _issue_factory_baseline_transition,
    apply_factory_baseline_transition,
)


GROUPS = (("A.OLD", "A"), ("A.NEW", "A"), ("B.NEW", "B"))


def _epoch(**changes):
    values = dict(
        factory_release_sha256="1" * 64,
        semantic_catalog_sha256="2" * 64,
        rubric_sha256="3" * 64,
        scope_sha256="4" * 64,
        policy_sha256="5" * 64,
        source_sha256="6" * 64,
        source_authority_registry_sha256="7" * 64,
        correction_frontier_sha256="8" * 64,
        evaluation_contract_sha256="9" * 64,
        fixed_cohort_sha256="a" * 64,
        evidence_stage="FOUNDATION_ACQUISITION",
    )
    values.update(changes)
    return BaselineComparisonEpoch(**values)


def _measure(ledger, epoch, capability, *, generation=1):
    transition = _issue_factory_baseline_transition(
        epoch.identity(capability),
        run_id="fixture-run",
        accepted_generation=generation,
        accepted_parent_manifest_sha256="b" * 64,
        accepted_candidate_sha256=(f"{generation:x}"[-1] * 64),
        decision_evidence_sha256=(f"{generation + 1:x}"[-1] * 64),
        parent_ledger_sha256=ledger.digest,
    )
    return apply_factory_baseline_transition(ledger, transition)


class FactoryBaselineCurrentnessTests(unittest.TestCase):
    def test_unmeasured_members_are_explicit_and_excluded_from_denominators(self):
        epoch = _epoch()
        ledger = _measure(BaselineLedger.empty(), epoch, "A.OLD")

        coverage = baseline_coverage(ledger, epoch, GROUPS)

        self.assertEqual(coverage.measured_capabilities, ("A.OLD",))
        self.assertEqual(coverage.unmeasured_capabilities, ("A.NEW", "B.NEW"))
        self.assertEqual(coverage.measured_denominator, 1)
        self.assertEqual(coverage.total_capabilities, 3)
        self.assertEqual(coverage.group_denominators, (("A", 1, 2), ("B", 0, 1)))

    def test_incompatible_epoch_cannot_borrow_an_established_baseline(self):
        original = _epoch()
        ledger = _measure(BaselineLedger.empty(), original, "A.OLD")

        for incompatible in (
            _epoch(factory_release_sha256="c" * 64),
            _epoch(rubric_sha256="d" * 64),
            _epoch(policy_sha256="e" * 64),
        ):
            with self.subTest(epoch=incompatible.digest):
                coverage = baseline_coverage(ledger, incompatible, GROUPS)
                self.assertEqual(coverage.measured_capabilities, ())
                self.assertEqual(coverage.measured_denominator, 0)

    def test_legacy_v1_baseline_is_readable_but_requires_requalification(self):
        epoch = _epoch()
        legacy = epoch.identity("A.OLD").to_record()
        legacy["schema"] = LEGACY_COMPARISON_SCHEMA
        record = {
            "schema": "bilqis.mlx.c05-baseline-ledger/v1",
            "measurements": [{
                "schema": "bilqis.mlx.c05-baseline-measurement/v1",
                "comparison": legacy,
                "run_id": "fixture-run",
                "accepted_generation": 1,
                "accepted_parent_manifest_sha256": "b" * 64,
                "accepted_candidate_sha256": "c" * 64,
                "decision_evidence_sha256": "d" * 64,
            }],
        }

        ledger = BaselineLedger.from_record(record)
        self.assertEqual(len(ledger.measurements), 1)
        self.assertEqual(
            baseline_coverage(ledger, epoch, GROUPS).measured_capabilities, ())

    def test_cold_read_restores_exact_currentness(self):
        epoch = _epoch()
        ledger = _measure(BaselineLedger.empty(), epoch, "A.OLD")
        cold = BaselineLedger.from_record(ledger.to_record())

        self.assertEqual(cold.digest, ledger.digest)
        self.assertEqual(
            baseline_coverage(cold, epoch, GROUPS).to_record(),
            baseline_coverage(ledger, epoch, GROUPS).to_record(),
        )


if __name__ == "__main__":
    unittest.main()
