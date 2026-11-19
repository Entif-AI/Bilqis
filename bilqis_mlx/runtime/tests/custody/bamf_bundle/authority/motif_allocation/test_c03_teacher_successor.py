"""C03 teacher advancement preserves an accepted B13 motif transition."""
from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
import random
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
import bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers as bamf_helpers
from bilqis_mlx.compatibility import historical_teacher_policy
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning._atlas_candidate.transaction import (
    _stage_candidate_motif_allocation,
)
from bilqis_mlx.learning._engram.tests.motif_fixtures import source as motif_source
from bilqis_mlx.learning._retention.tests.motif_allocation_support import (
    CandidateMotifAllocationFixture,
)
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_candidate import resolve_candidate
from bilqis_mlx.learning.atlas_engram import MotifBudget
from bilqis_mlx.learning.atlas_engram_transaction import _prepare_candidate_motif_snapshot
from bilqis_mlx.learning.atlas_retention_decision import (
    _issued_decision_generation_authority, issue_factory_retention_decision,
)
from bilqis_mlx.learning.learning_experiment import Settings
from bilqis_mlx.runtime._factory_identity_evaluation import (
    _finalize_factory_generation_authority, _raw_issue_owner_evaluation,
)
from bilqis_mlx.runtime.accepted_teacher_custody import select_accepted_teacher_visit
from bilqis_mlx.runtime.baseline.lifecycle import BaselineLedger
from bilqis_mlx.runtime.bamf_bundle.admission import (
    derive_motif_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle.genesis.records import (
    successor_candidate_identity_digest,
)
from bilqis_mlx.runtime.bamf_operator.session_parts import retention as retention_session
from bilqis_mlx.runtime.capability_retention import Decision, DecisionStatus
from bilqis_mlx.runtime.factory_retention_owner import (
    bind_factory_baseline_successor,
)
from bilqis_mlx.runtime.foundation_teacher_owner import derive_accepted_teacher_successor
from bilqis_mlx.runtime.model_topology_v2 import GenerationExtents
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    publish_genesis, shape_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import (
    adaptation, selection_teacher,
)


class C03MotifSuccessorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def _bound_visit(self, parent):
        student = candidate_identity_digest(parent.retained_state)
        school = SimpleNamespace(
            stage="RECOVERY_1", current_student=SimpleNamespace(sha256=student))
        return select_accepted_teacher_visit(
            self.run, historical_teacher_policy, school, random.Random(17),
            Settings(), "factory/7", {}, "A", capability_id="A.EDGE",
            total_capabilities=20, legacy_receipt={"teacher": selection_teacher()},
            adaptation=adaptation(), prior_region="legacy-region")[0]

    def _staged_candidate(self, fixture, parent, pointer):
        source = motif_source()
        release = parent.retained_state.allocations.manifest.semantic_release
        source = replace(source, frame=replace(
            source.frame,
            bindings=tuple(
                replace(
                    binding,
                    concept=(replace(binding.concept, semantic_release=release)
                             if binding.concept is not None else None))
                for binding in source.frame.bindings)))
        proposal = _prepare_candidate_motif_snapshot(
            (source,), parent.retained_state.allocations, MotifBudget(2))
        candidate_extents = GenerationExtents(
            parent.extents.semantic_bank_count, parent.extents.motif_page_count,
            parent.extents.active_semantic_digest,
            proposal.proposed.manifest.digest, parent.extents.factor_map_digest)
        continuation = fixture._continuation(proposal)
        with fixture._continuation_patch(continuation):
            staged = _stage_candidate_motif_allocation(
                fixture._step(), continuation, spec=parent.topology,
                parent_extents=parent.extents, candidate_extents=candidate_extents,
                run_seed=parent.run_identity.run_seed)
            retained = resolve_candidate(staged, accepted=True)
            screened = derive_motif_successor_bundle(
                parent, staged, retained_state=retained,
                parent_manifest_sha256=pointer["manifest_sha256"], delivery_events=())
        return staged, retained, screened, continuation

    def _issued_evaluation(self, parent, retained, screened):
        screen_decision = Decision(
            DecisionStatus.ELIGIBLE, "PAIRED_SCREEN_WITHIN_BUDGET",
            "a" * 64, "b" * 64, "c" * 64, "d" * 64,
            evaluated_capability_ids=("A.EDGE",))
        evaluation = _raw_issue_owner_evaluation(
            screen_decision,
            candidate_identity_digest(parent.retained_state),
            candidate_identity_digest(retained),
            successor_candidate_identity_digest(screened),
            None, parent_state=parent.retained_state, candidate_state=retained,
            parent_binding=None, candidate_binding=None, baseline_transition=None,
            baseline_ledger=BaselineLedger.from_optional_record(parent.baseline_evidence),
            championship_cohort=None, championship_assessment=None)
        return evaluation, issue_factory_retention_decision(evaluation)

    def _accepted_successor(
            self, fixture, continuation, parent, pointer, bound, retained, staged,
            evaluation, decision):
        selection = SimpleNamespace(
            visit=bound, option_id="A.EDGE", metadata={},
            offer=SimpleNamespace(capability_id="A.EDGE"))
        cache = SimpleNamespace(
            generation=parent.generation,
            accepted_manifest_sha256=pointer["manifest_sha256"])
        with (fixture._continuation_patch(continuation),
              patch.object(retention_session, "_instruction_event", return_value={
                "event": "BAMF_INSTRUCTION_HISTORY",
                "schema": "bilqis.bamf.instruction-history/v1",
                "state": "COMPLETE", "capability_ids": ["A.EDGE"],
              }),
              patch(
                "bilqis_mlx.runtime.bamf_operator.learning_health_runtime."
                "accepted_learning_health_state", return_value=(None, None)),
              patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "championship_boundary_capabilities", return_value=())):
            return retention_session._accepted_successor(
                decision, self.run, parent, SimpleNamespace(), None, selection,
                "A.EDGE", cache, retained, staged, None, 1, {}, {}, object(),
                {"outcome_sha256": "f" * 64}, derive_accepted_teacher_successor,
                bind_factory_baseline_successor, evaluation,
                lambda visit, _outcome: visit,
                lambda _visit, candidate, _parent: candidate, None,
                _finalize_factory_generation_authority)[0]

    def test_accepted_motif_transition_survives_c03_teacher_advancement(self):
        fixture = CandidateMotifAllocationFixture()
        fixture.setUp()
        with (patch.object(bamf_helpers, "DECLARED", fixture.declared),
              shape_patch(), patch.object(mlx_checkpoint, "assert_headroom")):
            pointer = publish_genesis(self.run, run_seed=71)
            parent = load_accepted_generation(self.run)
            fixture.parent, fixture.extents = parent.retained_state, parent.extents
            bound = self._bound_visit(parent)
            staged, retained, screened, continuation = self._staged_candidate(
                fixture, parent, pointer)
            evaluation, decision = self._issued_evaluation(parent, retained, screened)
            screened_authority = successor_candidate_identity_digest(screened)
            self.assertEqual(
                _issued_decision_generation_authority(decision), screened_authority)
            successor = self._accepted_successor(
                fixture, continuation, parent, pointer, bound, retained, staged,
                evaluation, decision)
            with fixture._continuation_patch(continuation), self.assertRaises(BilqisError):
                _finalize_factory_generation_authority(
                    evaluation, decision, parent, staged, successor)

        self.assertEqual(successor.transition["kind"], "MOTIF_ALLOCATION")
        self.assertEqual(
            successor.transition["candidate_allocation_sha256"],
            staged.motif_transition.candidate_allocation_sha256)
        self.assertEqual(successor.teacher_state["last_visit"], bound.identity.to_record())
        final_authority = successor_candidate_identity_digest(successor)
        self.assertNotEqual(screened_authority, final_authority)
        self.assertEqual(_issued_decision_generation_authority(decision), final_authority)


if __name__ == "__main__":
    unittest.main()
