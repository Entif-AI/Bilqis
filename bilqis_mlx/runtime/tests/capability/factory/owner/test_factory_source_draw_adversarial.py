"""Independent-source draw regressions for Factory-owned C05 evidence."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bilqis_mlx.errors.model import BilqisError
from bilqis_mlx.runtime.factory_retention_owner import C05_MAX_FRESH_DRAWS, _fresh_rows
from bilqis_mlx.runtime.source_execution import _source_family
from bilqis_mlx.runtime.tests.capability.factory.retention.diagnostics import (
    factory_retention_target_diagnostic as diagnostic,
)
from bilqis_mlx.semantics.cognitive_operators import TypedValue


def _draw_source(batches):
    execution = SimpleNamespace(
        provider_id="provider", provider_implementation_sha256="a" * 64,
        capability_id="A")
    return SimpleNamespace(release=SimpleNamespace(execution_plan=SimpleNamespace(
        capability_map={"A": execution})), draw_rows=Mock(side_effect=batches))


def _rows(prefix):
    return [{"id": f"{prefix}-{index}", "capability": "A"} for index in range(6)]


class FactorySourceDrawAdversarialTests(unittest.TestCase):
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
        self.assertEqual(
            taught[0]["id"],
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
                result = _fresh_rows(
                    source, ("A",), seed=7,
                    training=(("trained-family",), ("trained-episode",)))
                self.assertEqual((result.seed, result.rows), (8, tuple(clean)))

    def test_fresh_draw_rejects_owner_derived_training_family_across_redraws(self):
        source = _draw_source([_rows("draw")] * C05_MAX_FRESH_DRAWS)
        family = _source_family(source.release.execution_plan.capability_map["A"])
        with self.assertRaises(BilqisError) as caught:
            _fresh_rows(source, ("A",), seed=7, training=((family,), ("trained",)))
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
            require_independent=False)
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
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C05_INDEPENDENT_SOURCE_DRAW_EXHAUSTED")
        self.assertEqual(source.draw_rows.call_count, C05_MAX_FRESH_DRAWS)

    def test_fresh_draw_rejects_short_provider_batch(self):
        with self.assertRaises(BilqisError) as caught:
            _fresh_rows(
                _draw_source([_rows("short")[:5]]), ("A",), seed=7,
                training=((), ()))
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C05_FRESH_SOURCE_COVERAGE_INCOMPLETE")

    def test_fresh_draw_never_selects_using_gold_or_scores(self):
        first = _rows("first")
        for row in first:
            row.update(gold="wrong", score=-100)
        result = _fresh_rows(_draw_source([first]), ("A",), seed=7, training=((), ()))
        self.assertEqual((result.seed, result.rows), (7, tuple(first)))

    def test_target_diagnostic_redraws_training_overlap_before_solver(self):
        initial = [{"id": "trained-episode", "capability": "A"}] + [
            {"id": f"initial-{index}", "capability": "A"} for index in range(5)]
        independent = [
            {"id": f"fresh-{index}", "capability": "A"} for index in range(6)]
        execution = SimpleNamespace(
            provider_id="provider", provider_implementation_sha256="a" * 64,
            capability_id="A")
        source = SimpleNamespace(
            __post_init__=lambda: None,
            release=SimpleNamespace(
                release_sha256="b" * 64,
                execution_plan=SimpleNamespace(capability_map={"A": execution})),
            draw_rows=Mock(side_effect=[initial, independent]))
        gold = TypedValue("Number", 1, "c" * 64)

        def instruments(_context, _candidate, _artifact, rows, **_kwargs):
            return tuple(SimpleNamespace(case=SimpleNamespace(
                case_id=row["id"], goal=row, gold=gold)) for row in rows)

        def solver(_context, _candidate, _artifact, cases):
            self.assertNotIn(
                "trained-episode", {item.case.case_id for item in cases},
                "training episode reached fresh-target solver")
            result = SimpleNamespace(
                answer=gold, route=SimpleNamespace(value="NEURAL_COMPOSITION"),
                neural_calls=1, fallback_reason=None)
            return SimpleNamespace(evaluate=lambda *_args: (result, "contract")), "d" * 64

        with patch.multiple(
                diagnostic,
                _training_exclusions=Mock(return_value=(
                    ("trained-family",), ("trained-episode",))),
                _candidate_from_live_parent=Mock(return_value=(
                    object(), object(), object(), object())),
                candidate_identity_digest=Mock(return_value="e" * 64),
                _owner_seed=Mock(return_value=17), _instruments=instruments,
                factory_complete_solver=solver):
            receipt = diagnostic.diagnose_factory_retention_target(
                source, SimpleNamespace(training_authorities=()), "artifact", "A",
                run_dir=Path("unused"))
        self.assertEqual(
            [item["case_id"] for item in receipt["cases"]],
            [f"fresh-{index}" for index in range(6)])
        self.assertEqual(receipt["total"], 6)
        self.assertEqual(receipt["target_seed"], 104747)
        self.assertFalse(receipt["authorizing"])


if __name__ == "__main__":
    unittest.main()
