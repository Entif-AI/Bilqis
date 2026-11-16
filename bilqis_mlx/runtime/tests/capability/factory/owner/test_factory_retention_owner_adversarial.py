"""Caller-substitution regressions for the Factory-owned C05 admission seam."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bilqis_mlx.learning.atlas_retention_decision import (
    decide_candidate_retention, issue_factory_retention_decision,
)
import bilqis_mlx.learning.atlas_acceptance as acceptance_owner
from bilqis_mlx.learning.atlas_acceptance import mint_acceptance_binding
from bilqis_mlx.learning.atlas_candidate import CandidateTransaction
import bilqis_mlx.runtime.factory_retention_owner as owner
from bilqis_mlx.runtime.factory_retention_owner import (
    C05_MAX_FRESH_DRAWS, FactoryRetentionEvaluation, _cohort, _fresh_rows,
    evaluate_factory_retention_candidate,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import _screen_inputs
from bilqis_mlx.runtime.capability_retention import Decision, DecisionStatus
from bilqis_mlx.runtime.tests.capability.factory.retention import factory_retention_target_diagnostic as diagnostic
from bilqis_mlx.runtime.tests.capability.factory.retention.factory_retention_fixed_diagnostic import (
    _optimizer_delta_summary,
)
import mlx.core as mx
from bilqis_mlx.semantics.cognitive_operators import TypedValue
from bilqis_mlx.runtime.source_execution import _source_family
from bilqis_mlx.errors.model import BilqisError


def _draw_source(batches):
    execution = SimpleNamespace(provider_id="provider",
        provider_implementation_sha256="a" * 64, capability_id="A")
    return SimpleNamespace(release=SimpleNamespace(execution_plan=SimpleNamespace(
        capability_map={"A": execution})), draw_rows=Mock(side_effect=batches))


def _rows(prefix):
    return [{"id": f"{prefix}-{index}", "capability": "A"}
            for index in range(6)]


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
        release_sha = "a" * 64
        target = "B.IDBOOLOPS"
        capabilities = (
            SimpleNamespace(capability_id="B.AND", grade_id="B"),
            SimpleNamespace(capability_id=target, grade_id="B"),
        )
        release = SimpleNamespace(
            release_sha256=release_sha,
            execution_plan=SimpleNamespace(
                capabilities=capabilities,
                capability_map={item.capability_id: item for item in capabilities},
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
        decision = Decision(
            DecisionStatus.ELIGIBLE, "PAIRED_SCREEN_WITHIN_BUDGET",
            "a" * 64, "b" * 64, "c" * 64, "d" * 64)

        with patch(
                "bilqis_mlx.runtime.bamf_bundle.genesis.records."
                "successor_candidate_identity_digest", return_value="f" * 64), \
                patch.multiple(
                    owner,
                    create=True,
                    _training_exclusions=Mock(return_value=(("trained-family",), ("trained-episode",))),
                    _candidate_from_live_parent=Mock(return_value=(
                        SimpleNamespace(retained_state=object(), run_identity=None),
                    SimpleNamespace(
                        retained_state=object(),
                        transition={
                            "schema": "bilqis.mlx.bamf-generation-transition/v3",
                            "kind": "MOTIF_ALLOCATION",
                        }),
                    object(), object())),
                    candidate_identity_digest=Mock(return_value="d" * 64),
                    _owner_seed=Mock(return_value=11),
                    read_current=Mock(return_value={"factory_release_sha256": release_sha}),
                    frontier_exam=Mock(return_value={"factory_release_sha256": release_sha}),
                    load_frontier_cohort=Mock(return_value=fixed),
                    _fresh_rows=fresh,
                    _instruments=Mock(return_value=(SimpleNamespace(case=SimpleNamespace()),)),
                    case_census_digest=Mock(return_value="e" * 64),
                    _cohort=Mock(return_value=object()),
                    FoundationRetentionPolicy=Mock(return_value=object()),
                    factory_complete_solver=Mock(side_effect=((object(), "b" * 64),
                                                              (object(), "c" * 64))),
                    evaluate_foundation_fixed_school_candidate=Mock(return_value=decision),
                ):
            result = evaluate_factory_retention_candidate(
                source, candidate, "artifact", target, run_dir=Path("unused"))

        self.assertIsInstance(result, FactoryRetentionEvaluation)
        result.__post_init__()
        issued = issue_factory_retention_decision(result)
        self.assertTrue(issued.accepted)
        self.assertEqual(issued.parent_generation, "d" * 64)
        self.assertEqual(issued.candidate_generation, "d" * 64)
        self.assertEqual(result.candidate_generation_authority_sha256, "f" * 64)
        retained = SimpleNamespace(optimizer_step=1, step_proofs=())
        with patch.object(acceptance_owner, "candidate_identity_digest",
                          return_value="d" * 64), self.assertRaises(BilqisError):
            mint_acceptance_binding(
                issued, retained, run_id="fixture-run", generation=1,
                feature_sha256="a" * 64)
        fresh.assert_not_called()

    def test_real_source_family_overlap_fails_closed_across_redraws(self):
        from bilqis_mlx.runtime.tests.capability.factory.retention.factory_retention_live_support import (
            live_factory_context,
        )
        root = Path(__file__).resolve().parents[5]
        source_root = (root / "vendor/legacy-v16").resolve()
        if not source_root.is_dir():
            self.skipTest("pinned legacy source fixture is not mounted")
        source, _ = live_factory_context(root, source_root)
        taught = source.draw_rows(seed=46117, capability="B.IDBOOLOPS", each=1)
        self.assertEqual(taught[0]["id"],
            "e1560e78ae0824a8fe0f37efc4d42a18a841c933bac8894e70b607472199e1f7")
        authority = source.bind_rows(taught, seed=46117, capability="B.IDBOOLOPS", each=1)
        seed = 3080565765513679913
        original = source.draw_rows(seed=seed, capability="B.IDBOOLOPS", each=6)
        self.assertIn(taught[0]["id"], {row["id"] for row in original})
        with self.assertRaises(BilqisError) as caught:
            _fresh_rows(
                source, ("B.IDBOOLOPS",), seed=seed,
                training=((authority.source_family_id,), authority.episode_ids))
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C05_INDEPENDENT_SOURCE_DRAW_EXHAUSTED")

    def test_fresh_draw_rejects_explicit_family_episode_and_identity_aliases(self):
        for field, value in (("source_family_id", "trained-family"),
                             ("episode_id", "trained-episode"),
                             ("id", "trained-episode")):
            with self.subTest(field=field):
                bad, clean = _rows("bad"), _rows("clean")
                bad[0].update({field: value})
                if field == "id":
                    bad[0]["episode_id"] = "renamed-episode"
                source = _draw_source([bad, clean])
                result = _fresh_rows(source, ("A",), seed=7,
                    training=(("trained-family",), ("trained-episode",)))
                self.assertEqual((result.seed, result.rows), (8, tuple(clean)))

    def test_fresh_draw_rejects_owner_derived_training_family_across_redraws(self):
        source = _draw_source([_rows("draw")] * C05_MAX_FRESH_DRAWS)
        family = _source_family(source.release.execution_plan.capability_map["A"])
        with self.assertRaises(BilqisError) as caught:
            _fresh_rows(
                source, ("A",), seed=7,
                training=((family,), ("trained",)))
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C05_INDEPENDENT_SOURCE_DRAW_EXHAUSTED")
        self.assertEqual(source.draw_rows.call_count, C05_MAX_FRESH_DRAWS)

    def test_foundation_draw_allows_training_overlap(self):
        rows = _rows("taught")
        rows[0]["episode_id"] = "trained-episode"
        source = _draw_source([rows])
        result = _fresh_rows(
            source, ("A",), seed=7,
            training=(("trained-family",), ("trained-episode",)),
            require_independent=False,
        )
        self.assertEqual(result.seed, 7)
        self.assertEqual(result.rows, tuple(rows))

    def test_fresh_draw_redraws_duplicates_without_shrinking_coverage(self):
        for field in ("id", "episode_id"):
            with self.subTest(field=field):
                bad, clean = _rows("bad"), _rows("clean")
                bad[0][field] = bad[1][field] = "duplicate"
                source = _draw_source([bad, clean])
                result = _fresh_rows(source, ("A",), seed=7, training=((), ()))
                self.assertEqual(result.rows, tuple(clean))
                self.assertEqual(result.seed, 8)

    def test_fresh_draw_fails_closed_when_independent_source_is_exhausted(self):
        bad = _rows("bad")
        bad[0]["id"] = "trained"
        source = _draw_source([bad] * C05_MAX_FRESH_DRAWS)
        with self.assertRaises(BilqisError) as caught:
            _fresh_rows(source, ("A",), seed=7, training=((), ("trained",)))
        self.assertEqual(caught.exception.context["reason"],
                         "BAMF_C05_INDEPENDENT_SOURCE_DRAW_EXHAUSTED")
        self.assertEqual(source.draw_rows.call_count, C05_MAX_FRESH_DRAWS)

    def test_fresh_draw_rejects_short_provider_batch(self):
        with self.assertRaises(BilqisError) as caught:
            _fresh_rows(_draw_source([_rows("short")[:5]]), ("A",), seed=7,
                        training=((), ()))
        self.assertEqual(caught.exception.context["reason"],
                         "BAMF_C05_FRESH_SOURCE_COVERAGE_INCOMPLETE")

    def test_fresh_draw_never_selects_using_gold_or_scores(self):
        first = _rows("first")
        for row in first:
            row.update(gold="wrong", score=-100)
        result = _fresh_rows(_draw_source([first]), ("A",), seed=7,
                             training=((), ()))
        self.assertEqual((result.seed, result.rows), (7, tuple(first)))

    def test_target_diagnostic_redraws_training_overlap_before_solver(self):
        initial = [{"id": "trained-episode", "capability": "A"}] + [
            {"id": f"initial-{index}", "capability": "A"} for index in range(5)]
        independent = [{"id": f"fresh-{index}", "capability": "A"}
                       for index in range(6)]
        execution = SimpleNamespace(
            provider_id="provider", provider_implementation_sha256="a" * 64,
            capability_id="A")
        source = SimpleNamespace(
            __post_init__=lambda: None,
            release=SimpleNamespace(release_sha256="b" * 64,
                execution_plan=SimpleNamespace(capability_map={"A": execution})),
            draw_rows=Mock(side_effect=[initial, independent]))
        gold = TypedValue("Number", 1, "c" * 64)

        def instruments(_context, _candidate, _artifact, rows, **_kwargs):
            return tuple(SimpleNamespace(case=SimpleNamespace(
                case_id=row["id"], goal=row, gold=gold)) for row in rows)

        def solver(_context, _candidate, _artifact, cases):
            self.assertNotIn("trained-episode", {item.case.case_id for item in cases},
                             "training episode reached fresh-target solver")
            result = SimpleNamespace(answer=gold, route=SimpleNamespace(value="NEURAL_COMPOSITION"),
                                     neural_calls=1, fallback_reason=None)
            return SimpleNamespace(evaluate=lambda *_args: (result, "contract")), "d" * 64

        with patch.multiple(diagnostic,
                _training_exclusions=Mock(return_value=(("trained-family",), ("trained-episode",))),
                _candidate_from_live_parent=Mock(return_value=(object(), object(), object(), object())),
                candidate_identity_digest=Mock(return_value="e" * 64),
                _owner_seed=Mock(return_value=17),
                _instruments=instruments,
                factory_complete_solver=solver):
            receipt = diagnostic.diagnose_factory_retention_target(
                source, SimpleNamespace(training_authorities=()), "artifact", "A",
                run_dir=Path("unused"))
        self.assertEqual([item["case_id"] for item in receipt["cases"]],
                         [f"fresh-{index}" for index in range(6)])
        self.assertEqual(receipt["total"], 6)
        self.assertEqual(receipt["target_seed"], 104747)
        self.assertFalse(receipt["authorizing"])

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
