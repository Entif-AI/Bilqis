from bilqis_mlx.factory.autonomy import (
    AutonomyActionKind,
    EvidenceKind,
    ProjectionEvidenceSpec,
    compile_autonomy_plan,
    evidence_complete_capabilities,
    initial_evidence_ledger,
    next_action,
    next_source_coverage_debt,
    next_work,
    obligations_for_capability,
    record_evidence,
)

from .support import AutonomyFixture, sha


class AutonomyProjectionTests(AutonomyFixture):
    def test_projection_proof_is_part_of_evidence_completion(self):
        plan = compile_autonomy_plan(
            self.release,
            projection_evidence=(
                ProjectionEvidenceSpec(
                    "A.BASE", "TRANSFER", 2, ("nonce-symbol-renaming",)),))
        ledger = initial_evidence_ledger(self.release, plan=plan)
        direct = next_work(self.release, ledger, plan=plan)
        self.assertEqual(direct.obligation.kind, EvidenceKind.DIRECT)
        ledger = record_evidence(
            self.release, ledger, self.receipt(direct.obligation), plan=plan)
        self.assertNotIn(
            "A.BASE",
            evidence_complete_capabilities(self.release, ledger, plan=plan))
        projection = next_work(self.release, ledger, plan=plan)
        self.assertEqual(projection.capability_id, "A.BASE")
        self.assertEqual(projection.obligation.kind, EvidenceKind.PROJECTION)
        self.assertEqual(projection.obligation.key, "TRANSFER")
        self.assertEqual(
            projection.obligation.proof_axes, ("nonce-symbol-renaming",))
        ledger = record_evidence(
            self.release, ledger, self.receipt(projection.obligation), plan=plan)
        self.assertIn(
            "A.BASE",
            evidence_complete_capabilities(self.release, ledger, plan=plan))

    def test_unsupported_projection_routes_as_source_coverage_debt(self):
        plan = compile_autonomy_plan(
            self.release,
            projection_coverage_debt=(
                "A.BASE:TRANSFER:SOURCE_PROJECTION_UNSUPPORTED",))
        ledger = initial_evidence_ledger(self.release, plan=plan)
        action = next_action(self.release, ledger, plan=plan)
        self.assertEqual(action.kind, AutonomyActionKind.SOURCE_COVERAGE)
        self.assertEqual(
            action.source_coverage_debt,
            "A.BASE:TRANSFER:SOURCE_PROJECTION_UNSUPPORTED")
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
        import json
        self.assertEqual(
            plan.digest(),
            sha(json.dumps(
                legacy_payload, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False)))


class TypedCompositionAutonomyTests(AutonomyFixture):
    def test_source_covered_discovered_edge_becomes_composition_obligation(self):
        plan = compile_autonomy_plan(self.release, self.coverage_report())
        obligations = obligations_for_capability(self.release, "A.F3", plan=plan)
        typed = [item for item in obligations if item.kind is EvidenceKind.COMPOSITION]
        self.assertEqual(len(typed), 1)
        self.assertEqual(typed[0].requires_capabilities, ("A.BASE",))
        self.assertIn("typed-composition/A.BASE/slot/0", typed[0].obligation_id)
        self.assertEqual(plan.coverage_debt, ())

    def test_unverified_discovered_edge_stays_source_coverage_debt(self):
        report = self.coverage_report(status="AWAITING_SOURCE_WITNESS", debt=True)
        plan = compile_autonomy_plan(self.release, report)
        obligations = obligations_for_capability(self.release, "A.F3", plan=plan)
        self.assertFalse(
            any(item.kind is EvidenceKind.COMPOSITION for item in obligations))
        self.assertIn(
            "A.F3:A.BASE:0:AWAITING_SOURCE_WITNESS",
            next_source_coverage_debt(plan))

    def test_undeclared_unverified_candidate_is_deferred_not_blocking(self):
        report = self.coverage_report(
            status="CROSS_SOURCE_AST_BRIDGE_UNVERIFIED", debt=True)
        report["obligations"][0]["declared_prerequisite"] = False
        plan = compile_autonomy_plan(self.release, report)
        self.assertEqual(plan.coverage_debt, ())
        self.assertEqual(plan.blocked_capabilities, ())
        self.assertEqual(
            plan.deferred_composition_candidates,
            ("A.F3:A.BASE:0:CROSS_SOURCE_AST_BRIDGE_UNVERIFIED",))
        self.assertIsNone(next_source_coverage_debt(plan))

    def test_evidence_ledger_is_bound_to_exact_autonomy_plan(self):
        plan = compile_autonomy_plan(self.release, self.coverage_report())
        ledger = initial_evidence_ledger(self.release, plan=plan)
        changed = compile_autonomy_plan(
            self.release,
            self.coverage_report(status="SOURCE_CONTRAST_PARTIAL", debt=True))
        with self.assertRaisesRegex(ValueError, "AUTONOMY_PLAN_MISMATCH"):
            next_work(self.release, ledger, plan=changed)
