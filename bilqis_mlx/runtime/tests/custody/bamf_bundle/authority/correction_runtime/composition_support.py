"""Shared fixtures for accepted operator-composition custody tests."""
from dataclasses import replace
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.atlas_revalidation import (
    SourceAuthorityKey, SourceAuthorityRegistry, SourceAuthorityScope,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, provision_source_authority_registry,
    publish_candidate, shape_patch, with_source_authority_registry,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import (
    AUTHORITY, _SOURCE_OWNER, _TEST_PUBLIC, _event, _result, _sign_event,
)
from bilqis_mlx.runtime.tests.capability.factory.solver_helpers import _fixture
from bilqis_mlx.runtime.cognitive_solver import QualifiedComposition, SolveContext
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind, DependencyRef
from bilqis_mlx.semantics.context_eligibility import C09ContextInvalidation
from bilqis_mlx.semantics.domains import contract_digest


SYNTHETIC_SOURCE_AUTHORITY = SourceAuthorityRegistry((
    SourceAuthorityKey(
        _SOURCE_OWNER,
        _TEST_PUBLIC,
        (SourceAuthorityScope(DependencyKind.SOURCE, "synthetic:"),),
    ),
))


class AcceptedCorrectionCompositionCase(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()
        self._authority_registry = AUTHORITY

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def publish(self, source, registry=AUTHORITY):
        self._authority_registry = registry
        provision_source_authority_registry(self.run, registry)
        source = with_source_authority_registry(source, registry)
        with self._shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_candidate(self.run, source)
            return pointer

    def _shape_patch(self):
        return shape_patch(self._authority_registry)

    def _composition_context(self, count):
        binding, generation, _budget, add, _ambiguous = _fixture()
        first = QualifiedComposition(
            add, generation.source_binding_digest, generation.generation_digest,
            binding.frontier.rights_epoch, binding.frontier.correction_generation,
            "a" * 64)
        compositions = tuple(
            first if index == 0 else replace(
                first, qualification_receipt_sha256=chr(98 + index - 1) * 64)
            for index in range(count))
        return binding, SolveContext(
            binding, qualified_compositions=compositions,
            qualification_verifier=lambda item: True), compositions

    def _concurrent_corrections(self, binding):
        dependency = DependencyRef(
            DependencyKind.SOURCE,
            "source:binding:" + contract_digest(binding),
        )
        first = _event(dependency)
        second = _sign_event(replace(
            first,
            event_id="correction:synthetic:2",
            source_receipt_sha256="e" * 64,
            old_evidence_sha256="b" * 64,
            new_evidence_sha256="c" * 64,
            recorded_at=631,
            source_signature_hex="0" * 128,
        ))
        return first, second

    def _record_equal_revalidation(self, owner, composition, correction):
        node = owner.node_for(composition)
        with self._shape_patch():
            return AcceptedRuntimeHost(self.run).record_revalidation(_result(
                    node, digest=node.content_digest,
                    correction=correction),
            )

    def _context_invalidation(self, case, new_digest):
        return C09ContextInvalidation(
            old_context_digest=case.previous.digest,
            new_context_digest=new_digest,
            reason_codes=("BAMF_CONTEXT_APPROVED_VIEW_CHANGED",),
            principal_id=case.task.principal_id,
            tenant_id=case.task.tenant_id,
            scope=case.task.scope,
            semantic_release=case.task.semantic_release,
            policy_epoch=case.policy.policy_epoch,
            rights_epoch=case.frontier.rights_epoch,
            correction_generation=case.frontier.correction_generation,
            causal_prefix_end=case.task.causal_prefix_end,
            invalidated_handles=tuple(sorted({
                handle
                for frame in case.previous.eligible.frames
                for handle in (frame.frame_handle, *frame.member_handles)
            })),
        )
