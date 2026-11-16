from dataclasses import replace
import hashlib
import unittest

from bilqis_mlx.curriculum import AnswerFamily, BINARY, Capability, Course, Grade
from bilqis_mlx.factory.adapters import RegisteredSourceAdapter, SourceAdapterRegistry
from bilqis_mlx.factory.autonomy import (
    AutonomyActionKind,
    EvidenceKind,
    EvidenceReceipt,
    RejectedTeachingAttemptReceipt,
    ProjectionEvidenceSpec,
    compile_autonomy_plan,
    initial_evidence_ledger,
    evidence_complete_capabilities,
    next_action,
    next_work,
    obligations_for_capability,
    record_evidence,
    record_rejected_teaching_attempt,
)
from bilqis_mlx.factory.model import SourceAdapter
from bilqis_mlx.factory.release import compile_factory_release

from bilqis_mlx.factory.tests.autonomy_support import AutonomyFixture, _sha

class AutonomousCurriculumPlannerExtensionTests(AutonomyFixture, unittest.TestCase):
    def test_passing_receipt_must_meet_obligation_specimen_floor(self):
        ledger = initial_evidence_ledger(self.release)
        obligation = next_work(self.release, ledger).obligation
        with self.assertRaisesRegex(ValueError, "INSUFFICIENT_EVIDENCE_SPECIMENS"):
            record_evidence(self.release, ledger,
                            self.receipt(obligation, specimen_count=obligation.minimum_specimens - 1))

    def test_evidence_is_bound_to_exact_factory_release(self):
        ledger = initial_evidence_ledger(self.release)
        changed = replace(self.release, release_sha256="f" * 64)
        with self.assertRaisesRegex(ValueError, "AUTONOMY_RELEASE_MISMATCH"):
            next_work(changed, ledger)

    def test_autonomous_loop_finishes_without_grade_specific_dispatch(self):
        ledger = initial_evidence_ledger(self.release)
        seen = []
        for _ in range(40):
            work = next_work(self.release, ledger)
            if work is None:
                break
            seen.append((work.capability_id, work.obligation.kind))
            ledger = record_evidence(self.release, ledger, self.receipt(work.obligation))
        else:
            self.fail("autonomous evidence loop did not converge")

        self.assertLess(seen.index(("A.BASE", EvidenceKind.DIRECT)),
                        seen.index(("A.COMPOSITE", EvidenceKind.DIRECT)))
        self.assertLess(seen.index(("A.OTHER", EvidenceKind.DIRECT)),
                        seen.index(("A.COMPOSITE", EvidenceKind.DIRECT)))
        self.assertEqual(evidence_complete_capabilities(self.release, ledger),
                         tuple(item.capability_id for item in self.release.capabilities))
        self.assertIsNone(next_work(self.release, ledger))

    def test_projection_proof_is_part_of_evidence_completion(self):
        plan = compile_autonomy_plan(
            self.release,
            projection_evidence=(
                ProjectionEvidenceSpec(
                    "A.BASE", "TRANSFER", 2,
                    ("nonce-symbol-renaming",)),
            ),
        )
        ledger = initial_evidence_ledger(self.release, plan=plan)
        direct = next_work(self.release, ledger, plan=plan)
        self.assertEqual(direct.obligation.kind, EvidenceKind.DIRECT)
        ledger = record_evidence(
            self.release, ledger, self.receipt(direct.obligation), plan=plan)
        self.assertNotIn(
            "A.BASE",
            evidence_complete_capabilities(self.release, ledger, plan=plan),
        )
        projection = next_work(self.release, ledger, plan=plan)
        self.assertEqual(projection.capability_id, "A.BASE")
        self.assertEqual(projection.obligation.kind, EvidenceKind.PROJECTION)
        self.assertEqual(projection.obligation.key, "TRANSFER")
        self.assertEqual(
            projection.obligation.proof_axes,
            ("nonce-symbol-renaming",),
        )
        ledger = record_evidence(
            self.release, ledger, self.receipt(projection.obligation), plan=plan)
        self.assertIn(
            "A.BASE",
            evidence_complete_capabilities(self.release, ledger, plan=plan),
        )

    def test_unsupported_projection_routes_as_source_coverage_debt(self):
        plan = compile_autonomy_plan(
            self.release,
            projection_coverage_debt=(
                "A.BASE:TRANSFER:SOURCE_PROJECTION_UNSUPPORTED",
            ),
        )
        ledger = initial_evidence_ledger(self.release, plan=plan)
        action = next_action(self.release, ledger, plan=plan)
        self.assertEqual(action.kind, AutonomyActionKind.SOURCE_COVERAGE)
        self.assertEqual(
            action.source_coverage_debt,
            "A.BASE:TRANSFER:SOURCE_PROJECTION_UNSUPPORTED",
        )
        self.assertIn("A.BASE", plan.blocked_capabilities)

    def test_empty_projection_extension_preserves_legacy_plan_digest(self):
        plan = compile_autonomy_plan(self.release)
        legacy_payload = {
            "factory_release_sha256": self.release.release_sha256,
            "source_composition_audited": False,
            "source_composition_edges": (),
            "coverage_debt": (),
            "blocked_capabilities": (),
            "deferred_composition_candidates": (),
        }
        self.assertEqual(plan.digest(), _sha(
            __import__("json").dumps(
                legacy_payload, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False)))
