"""C09 learned-support identity for multi-context packed-frame execution."""
from dataclasses import replace
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.learning.tests.frames.nested_fixtures import _case as _nested_case
from bilqis_mlx.runtime.atlas_model_participation import _execution_dependencies
from bilqis_mlx.runtime.atlas_training_authority import (
    extend_training_dependencies,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import _new_execution_cache
from bilqis_mlx.runtime.tests.correction.capability_support_owner_support import (
    training_authority,
)
from bilqis_mlx.semantics.cognitive_dependencies import (
    ArtifactKind, ArtifactNode, DependencyKind, DependencyRef,
)


class AtlasModelMultiContextDependencyTests(TestCase):
    def test_learned_support_keeps_context_time_but_not_internal_view_ids(self):
        _ast, _config, compiled, _vectors, _params = _nested_case()
        manifest = MotifManifest(compiled.features.semantic_release)
        compiled = replace(
            compiled,
            extents=replace(
                compiled.extents,
                motif_key_map_digest=manifest.digest,
            ),
        )
        cache = _new_execution_cache(
            run_id="test-c09-multi-context-learned",
            generation=7,
            accepted_manifest_sha256="8" * 64,
            generation_binding="7" * 64,
            motif_manifest=manifest,
        )
        feature = ArtifactNode(
            "feature:test-multi-context",
            ArtifactKind.ATLAS_FEATURE,
            "a" * 64,
            True,
            (DependencyRef(DependencyKind.SOURCE, "source:feature"),),
            impact=1,
            exigency=1,
        )
        batch = SimpleNamespace(
            compiled=compiled,
            atlas_feature_artifact_owner=SimpleNamespace(current_node=feature),
        )
        producer = SimpleNamespace(
            _motif_read=SimpleNamespace(participating_slots=(0,)),
        )

        with patch(
            "bilqis_mlx.runtime.bamf_bundle.execution_cache.require_accepted_execution_cache",
            side_effect=lambda value: value,
        ):
            observed = _execution_dependencies(batch, producer, cache)
        learned = extend_training_dependencies(
            training_authority(), observed).immediate_dependencies
        learned_keys = {ref.key for ref in learned}
        packed = compiled.packed_frame_artifact_owner

        for dependency in packed.current_context_dependencies:
            self.assertIn(dependency, learned)
        for view_id in packed.origin_context_keys:
            self.assertNotIn(view_id, learned_keys)
