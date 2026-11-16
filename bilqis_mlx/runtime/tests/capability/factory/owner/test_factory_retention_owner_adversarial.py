"""Caller-substitution regressions for the Factory-owned C05 admission seam."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bilqis_mlx.learning.atlas_retention_decision import (
    _issued_decision_baseline_ledger_sha256, decide_candidate_retention,
    issue_factory_retention_decision,
)
import bilqis_mlx.learning.atlas_acceptance as acceptance_owner
from bilqis_mlx.learning.atlas_acceptance import mint_acceptance_binding
from bilqis_mlx.learning.atlas_candidate import CandidateTransaction
import bilqis_mlx.runtime.factory_retention_owner as owner
import bilqis_mlx.runtime.retention.screen as owner_screen
from bilqis_mlx.runtime.factory_retention_owner import (
    FactoryRetentionEvaluation, _cohort, evaluate_factory_retention_candidate,
)
from bilqis_mlx.runtime._factory_parent_assessment_cache import ParentAssessmentCacheReceipt
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import _screen_inputs
from bilqis_mlx.runtime.capability_retention import Decision, DecisionStatus
from bilqis_mlx.runtime.baseline.lifecycle import BaselineLifecycleState
from bilqis_mlx.runtime.tests.capability.factory.retention.diagnostics.factory_retention_fixed_diagnostic import (
    _optimizer_delta_summary,
)
import mlx.core as mx
from bilqis_mlx.errors.model import BilqisError


def _foundation_owner_fixture():
    release_sha = "a" * 64
    target = "B.IDBOOLOPS"
    capabilities = (
        SimpleNamespace(capability_id="B.AND", grade_id="B"),
        SimpleNamespace(capability_id=target, grade_id="B"),
    )
    release = SimpleNamespace(
        release_sha256=release_sha,
        semantic_catalog_sha256="b" * 64,
        execution_plan=SimpleNamespace(
            capabilities=capabilities,
            capability_map={item.capability_id: item for item in capabilities},
            grades=(SimpleNamespace(
                grade_id="B", assessment_blueprint_sha256="c" * 64),),
            curriculum_sha256="d" * 64,
            profile_id="factory-c05-adversarial",
            projection_digests=SimpleNamespace(source="e" * 64),
        ),
    )
    source = SimpleNamespace(
        __post_init__=lambda: None,
        release=release,
        require_accepted_runtime=Mock(),
    )
    candidate = object.__new__(CandidateTransaction)
    object.__setattr__(candidate, "training_authorities", (
        SimpleNamespace(delivery_capability=target, release_sha256=release_sha),
    ))
    fixed = SimpleNamespace(rows=({"id": "fixed"},), seed=7)
    fresh = Mock(side_effect=AssertionError(
        "foundation acceptance constructed measure-only fresh rows"))
    policy_factory = Mock(return_value=object())
    decision = Decision(
        DecisionStatus.ELIGIBLE, "PAIRED_SCREEN_WITHIN_BUDGET",
        "a" * 64, "b" * 64, "c" * 64, "d" * 64)
    return source, candidate, target, fixed, fresh, policy_factory, decision


def _evaluate_foundation_owner(source, candidate, target, fixed, fresh,
                               policy_factory, decision):
    release_sha = source.release.release_sha256
    with patch(
            "bilqis_mlx.runtime.bamf_bundle.genesis.records."
            "successor_candidate_identity_digest", return_value="f" * 64), \
            patch.multiple(
                owner,
                create=True,
                _training_exclusions=Mock(
                    return_value=(("trained-family",), ("trained-episode",))),
                _candidate_from_live_parent=Mock(return_value=(
                    SimpleNamespace(
                        retained_state=object(), run_identity=None,
                        run_id="fixture-run", generation=0, baseline_evidence=None,
                        correction_frontier={}, evaluation_contract={}),
                    SimpleNamespace(
                        retained_state=object(),
                        parent_manifest_sha256="0" * 64,
                        transition={
                            "schema": "bilqis.mlx.bamf-generation-transition/v3",
                            "kind": "MOTIF_ALLOCATION",
                        }),
                    object(), SimpleNamespace(
                        accepted_manifest_sha256="0" * 64,
                        source_authority_registry_sha256=None))),
                candidate_identity_digest=Mock(return_value="d" * 64),
                _owner_seed=Mock(return_value=11),
                read_current=Mock(return_value={"factory_release_sha256": release_sha}),
                frontier_exam=Mock(return_value={"factory_release_sha256": release_sha}),
                load_frontier_cohort=Mock(return_value=fixed),
                _fresh_rows=fresh,
                _instruments=Mock(return_value=(SimpleNamespace(case=SimpleNamespace()),)),
            ), patch.multiple(
                owner_screen,
                case_census_digest=Mock(return_value="e" * 64),
                _cohort=Mock(return_value=SimpleNamespace(
                    rubric_sha256="1" * 64, scope_sha256="2" * 64,
                    policy_sha256="3" * 64, source_sha256="4" * 64,
                    evidence_stage=owner.CURRENT_EVIDENCE_STAGE)),
                FoundationRetentionPolicy=policy_factory,
                factory_complete_solver=Mock(side_effect=(
                    (object(), "b" * 64), (object(), "c" * 64))),
                factory_parent_assessment_identity=Mock(return_value=SimpleNamespace(
                    factory_release_sha256="5" * 64,
                    semantic_catalog_sha256="6" * 64,
                    source_authority_registry_sha256=None,
                    correction_frontier_sha256="7" * 64,
                    evaluation_contract_sha256="8" * 64,
                    fixed_cohort_sha256="9" * 64)),
                use_parent_assessment=Mock(return_value=(
                    object(),
                    ParentAssessmentCacheReceipt("1" * 64, "2" * 64, "3" * 64, False))),
                evaluate_foundation_fixed_school_candidate=Mock(return_value=decision),
                candidate_identity_for_canonical_consumer=Mock(return_value="d" * 64),
                candidate_identity_binding_for_state=Mock(return_value=None)):
        return evaluate_factory_retention_candidate(
            source, candidate, "artifact", target, run_dir=Path("unused"))


class FactoryRetentionOwnerAdversarialTests(unittest.TestCase):
    def test_optimizer_delta_summary_distinguishes_decay_only_from_gradient_driven_change(self):
        parent = SimpleNamespace(retained_state=SimpleNamespace(
            optimizer=SimpleNamespace(parameters={
                "blocks.0.query": mx.array([1.0], dtype=mx.float32),
                "readout.query": mx.array([2.0], dtype=mx.float32),
            })))
        candidate = SimpleNamespace(optimizer=SimpleNamespace(parameters={
            "blocks.0.query": mx.array([0.99], dtype=mx.float32),
            "readout.query": mx.array([2.1], dtype=mx.float32),
        }))
        gradient = SimpleNamespace(gradients={
            "blocks.0.query": mx.array([0.0], dtype=mx.float32),
            "readout.query": mx.array([3.0], dtype=mx.float32),
        })

        summary = _optimizer_delta_summary(parent, candidate, gradient)

        self.assertEqual(summary["blocks"]["nonzero_gradient_parameters"], 0)
        self.assertEqual(summary["blocks"]["changed_parameters"], 1)
        self.assertEqual(summary["blocks"]["zero_gradient_changed_parameters"], 1)
        self.assertEqual(summary["readout"]["nonzero_gradient_parameters"], 1)
        self.assertEqual(summary["readout"]["changed_parameters"], 1)
        self.assertEqual(summary["readout"]["zero_gradient_changed_parameters"], 0)

    def test_foundation_owner_does_not_construct_measure_only_fresh_cohorts(self):
        fixture = _foundation_owner_fixture()
        source, candidate, target, _, fresh, policy_factory, _ = fixture
        result = _evaluate_foundation_owner(*fixture)

        self.assertIsInstance(result, FactoryRetentionEvaluation)
        result.__post_init__()
        issued = issue_factory_retention_decision(result)
        self.assertTrue(issued.accepted)
        self.assertEqual(issued.parent_generation, "d" * 64)
        self.assertEqual(issued.candidate_generation, "d" * 64)
        self.assertEqual(result.parent_assessment_cache.assessment_sha256, "2" * 64)
        self.assertEqual(result.candidate_generation_authority_sha256, "f" * 64)
        self.assertEqual(
            _issued_decision_baseline_ledger_sha256(issued),
            result.baseline_ledger.digest)
        self.assertIsNotNone(result.baseline_transition)
        self.assertIs(
            result.baseline_ledger.state_for(result.baseline_transition.measurement.comparison),
            BaselineLifecycleState.BASELINE_ESTABLISHED,
        )
        self.assertEqual(
            policy_factory.call_args.args[2], (),
            "a virgin accepted parent must not fabricate protected capability baselines")
        retained = SimpleNamespace(optimizer_step=1, step_proofs=())
        with patch.object(acceptance_owner, "candidate_identity_digest",
                          return_value="d" * 64):
            bound = mint_acceptance_binding(
                issued, retained, run_id="fixture-run", generation=1,
                feature_sha256="a" * 64, generation_authority_sha256="f" * 64)
        self.assertEqual(
            acceptance_owner._issued_acceptance_baseline_ledger_sha256(bound),
            result.baseline_ledger.digest)
        fresh.assert_not_called()

    def test_caller_cannot_construct_evaluation_authority(self):
        with self.assertRaises(Exception):
            FactoryRetentionEvaluation(
                decision=object(),
                parent_candidate_sha256="a" * 64,
                candidate_candidate_sha256="b" * 64,
            )

    def test_issuer_rejects_foreign_evidence(self):
        with self.assertRaises(Exception):
            issue_factory_retention_decision(object())

    def test_reachable_factory_issuer_token_cannot_mint_live_c05_authority(self):
        forged = object.__new__(FactoryRetentionEvaluation)
        for name, value in (
            ("decision", Decision(
                DecisionStatus.ELIGIBLE, "PAIRED_SCREEN_WITHIN_BUDGET",
                "a" * 64, "b" * 64, "c" * 64, "d" * 64)),
            ("parent_candidate_sha256", "a" * 64),
            ("candidate_candidate_sha256", "b" * 64),
        ):
            object.__setattr__(forged, name, value)

        self.assertFalse(hasattr(owner, "_OWNER_ISSUER"))
        self.assertFalse(hasattr(owner, "_raw_issue_owner_evaluation"))
        self.assertFalse(hasattr(owner, "_issue_owner_evaluation"))
        with self.assertRaises(Exception):
            issue_factory_retention_decision(forged)

    def test_caller_selected_solver_and_policy_remain_fail_closed(self):
        with self.assertRaises(Exception):
            decide_candidate_retention(
                parent_solver=object(), candidate_solver=object(),
                target_capability="B.IDBOOLOPS", policy=object(),
                cohorts=(), parent_state=object(), candidate_state=object(),
            )

    def test_factory_entry_rejects_caller_cohorts_and_policy(self):
        with self.assertRaises(TypeError):
            evaluate_factory_retention_candidate(
                object(), object(), "artifact", "B.IDBOOLOPS",
                run_dir=Path("unused"), cohorts=(), policy=object(),
            )

    def test_owner_cohorts_share_one_factory_evaluation_scope(self):
        _, _, _, policy, cohorts = _screen_inputs()
        release = SimpleNamespace(execution_plan=SimpleNamespace(
            curriculum_sha256="1" * 64,
            profile_id="factory-c05-test",
            grades=(SimpleNamespace(
                grade_id="A", assessment_blueprint_sha256="2" * 64),),
            projection_digests=SimpleNamespace(source="3" * 64),
        ))
        training = (("trained-family",), ("trained-episode",))
        rebuilt = tuple(_cohort(
            cohort.kind,
            tuple(SimpleNamespace(case=case) for case in cohort.cases),
            cohort.capability_groups,
            release,
            policy,
            training,
        ) for cohort in cohorts)
        self.assertEqual(len({cohort.scope_sha256 for cohort in rebuilt}), 1)


if __name__ == "__main__":
    unittest.main()
