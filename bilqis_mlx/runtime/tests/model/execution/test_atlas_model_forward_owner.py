"""B11 source-producer owner threading across cache modes."""
from types import SimpleNamespace
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
import bilqis_mlx.runtime.atlas_model_forward as forward_impl


class AtlasModelOwnerThreadingTests(TestCase):
    def _batch(self, owner):
        compiled = SimpleNamespace(
            extents=SimpleNamespace(motif_key_map_digest="motif-digest"),
            features=SimpleNamespace(semantic_release="semantic-release"))
        return SimpleNamespace(
            compiled=compiled,
            sources=("source",),
            feature_schema=object(),
            active_semantic_rows=SimpleNamespace(
                active_indices=(0,), run_id="test-run", generation=0),
            atlas_feature_artifact_owner=owner,
        )

    def test_source_producer_threads_owner_without_cache(self):
        owner = object()
        batch = self._batch(owner)
        params = object()
        producer = object()
        with patch.object(
                forward_impl, "semantic_bank_views", return_value=("banks",)), patch.object(
                forward_impl, "start_source_backbone_producer",
                return_value=producer) as start:
            actual, accepted, capture = forward_impl._source_producer(
                params, batch, "generation", None)
        self.assertIs(actual, producer)
        self.assertIsNone(accepted)
        self.assertTrue(capture)
        self.assertIs(start.call_args.args[-1], owner)

    def test_source_producer_threads_owner_for_accepted_cache(self):
        owner = object()
        batch = self._batch(owner)
        params = object()
        producer = object()
        empty_cache = SimpleNamespace(
            run_id="test-run", generation=0,
            generation_binding="generation",
            motif_manifest=SimpleNamespace(digest="motif-digest", slots=()),
        )
        with patch.object(
                forward_impl, "semantic_bank_views", return_value=("banks",)), patch.object(
                forward_impl, "require_accepted_execution_cache",
                return_value=empty_cache), patch.object(
                forward_impl, "bind_motif_artifact_owner") as bind, patch.object(
                forward_impl, "start_retained_source_backbone_producer",
                return_value=producer) as start:
            actual, accepted, capture = forward_impl._source_producer(
                params, batch, "generation", object())
        self.assertIs(actual, producer)
        self.assertIs(accepted, empty_cache)
        self.assertTrue(capture)
        bind.assert_called_once_with(empty_cache, batch.compiled)
        self.assertIs(start.call_args.args[-1], owner)

    def test_source_producer_rejects_foreign_accepted_cache(self):
        batch = self._batch(object())
        params = object()
        foreign_cache = SimpleNamespace(
            run_id="foreign-run", generation=0,
            generation_binding="generation",
            motif_manifest=SimpleNamespace(digest="motif-digest", slots=()),
        )
        with patch.object(
                forward_impl, "semantic_bank_views", return_value=("banks",)), patch.object(
                forward_impl, "require_accepted_execution_cache",
                return_value=foreign_cache):
            with self.assertRaises(BilqisError):
                forward_impl._source_producer(
                    params, batch, "generation", object())

    def test_source_producer_threads_owner_for_retained_and_candidate_cache(self):
        owner = object()
        batch = self._batch(owner)
        params = object()
        producer = object()
        retained_cache = SimpleNamespace(
            run_id="test-run", generation=0,
            generation_binding="generation",
            motif_manifest=SimpleNamespace(
                digest="motif-digest", slots=(object(),)),
        )
        with patch.object(
                forward_impl, "semantic_bank_views", return_value=("banks",)), patch.object(
                forward_impl, "require_accepted_execution_cache",
                return_value=retained_cache), patch.object(
                forward_impl, "bind_motif_artifact_owner") as bind, patch.object(
                forward_impl, "start_retained_source_backbone_producer",
                return_value=producer) as start:
            actual, accepted, capture = forward_impl._source_producer(
                params, batch, "generation", object())
        self.assertIs(actual, producer)
        self.assertIs(accepted, retained_cache)
        self.assertTrue(capture)
        bind.assert_called_once_with(retained_cache, batch.compiled)
        self.assertIs(start.call_args.args[-1], owner)

        candidate_cache = object.__new__(forward_impl.CandidateExecutionCache)
        speculative = SimpleNamespace(
            generation_binding="candidate-generation",
            _accepted_cache=retained_cache,
        )
        with patch.object(
                forward_impl, "semantic_bank_views", return_value=("banks",)), patch.object(
                forward_impl, "require_candidate_execution_cache",
                return_value=speculative), patch.object(
                forward_impl, "bind_motif_artifact_owner") as bind, patch.object(
                forward_impl, "start_retained_source_backbone_producer",
                return_value=producer) as start:
            actual, accepted, capture = forward_impl._source_producer(
                params, batch, "candidate-generation", candidate_cache)
        self.assertIs(actual, producer)
        self.assertIs(accepted, retained_cache)
        self.assertFalse(capture)
        bind.assert_called_once_with(retained_cache, batch.compiled)
        self.assertIs(start.call_args.args[-1], owner)

    def test_durable_b13_forward_captures_b14_only_after_source_completion(self):
        producer = object()
        batch = object()
        accepted = SimpleNamespace(_run_dir=Path("/tmp/accepted-b13"))
        hidden = object()
        with patch.object(
            forward_impl, "finalize_source_backbone_hidden", return_value=hidden
        ), patch(
            "bilqis_mlx.runtime.atlas_cache_runtime._capture_forward_attention_caches"
        ) as capture:
            actual = forward_impl._finalize_source_hidden(
                producer, accepted, batch, capture_derived_cache=True)
        self.assertIs(actual, hidden)
        capture.assert_called_once_with(accepted, batch, producer)

    def test_loss_bearing_forward_never_captures_b14_cache(self):
        producer = object()
        batch = object()
        accepted = SimpleNamespace(_run_dir=Path("/tmp/accepted-b13"))
        hidden = object()
        with patch.object(
            forward_impl, "finalize_source_backbone_hidden", return_value=hidden
        ), patch(
            "bilqis_mlx.runtime.atlas_cache_runtime._capture_forward_attention_caches"
        ) as capture:
            actual = forward_impl._finalize_source_hidden(
                producer, accepted, batch, capture_derived_cache=False)
        self.assertIs(actual, hidden)
        capture.assert_not_called()
