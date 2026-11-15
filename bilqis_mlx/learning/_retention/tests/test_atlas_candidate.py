"""B12.2 disposable candidate rollback and accepted-clock witnesses."""
import hashlib
import inspect
import json
from dataclasses import replace
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import mlx.core as mx
import numpy as np

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning._engram.tests.motif_fixtures import RELEASE, source
from bilqis_mlx.learning.atlas_engram import MotifBudget, MotifManifest
from bilqis_mlx.learning.atlas_engram_transaction import (
    MotifAllocationSnapshot, _prepare_candidate_motif_snapshot,
)
from bilqis_mlx.learning.atlas_plasticity import IdentityRowAge, PlasticityPolicy
from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters, AdamWStateTree
from bilqis_mlx.learning.atlas_candidate import (
    CandidateCustodyIdentity, CandidateState, CandidateStepProof,
    CandidateTransaction, begin_candidate, candidate_step, resolve_candidate,
)
from bilqis_mlx.learning._retention._atlas_candidate.common import (
    LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA, LOGICAL_BATCH_STEP_PROOF_SCHEMA,
    PREVIOUS_STEP_PROOF_SCHEMA,
)
from bilqis_mlx.learning._retention.tests.execution_fixtures import execution_provenance
from bilqis_mlx.learning.source_atoms import SourceAtomRow
from bilqis_mlx.factory.teaching import content_digest
from bilqis_mlx.runtime.atlas_training_contracts import (
    BamfDeliveryProvenance, BamfTrainingRow, _issue_training_batch,
)
from bilqis_mlx.runtime.atlas_visit_provenance import BamfVisitProvenance
from bilqis_mlx.runtime.atlas_training_authority import _issue as issue_training_authority
from bilqis_mlx.runtime.source_execution import source_content_digest
from bilqis_mlx.semantics.cognitive_dependencies import (
    DependencyKind, DependencyRef,
)


def _visit_provenance(capability_id: str) -> BamfVisitProvenance:
    payload = {
        "run_identity_sha256": "1" * 64,
        "run_seed": 17,
        "generation": 0,
        "accepted_manifest_sha256": "2" * 64,
        "teacher_identity": "3" * 64,
        "teacher_epoch": 0,
        "student_sha256": "4" * 64,
        "selection_seed": 42,
        "cursor": "lesson:7",
        "capability_id": capability_id,
        "policy_key": "p-strong",
        "schema": "bilqis.bamf.c03-teacher-visit-identity/v1",
    }
    wire = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return BamfVisitProvenance.from_c03_record({
        **payload, "visit_id": hashlib.sha256(wire.encode()).hexdigest()})


class CandidateTransactionTests(TestCase):
    def setUp(self):
        name = 'identity.bank.0'
        values = mx.array([[.5, -.25], [1., 2.]], dtype=mx.float32)
        state = AdamWStateTree({name: values}, {name: mx.ones_like(values) * .1},
                              {name: mx.ones_like(values) * .01},
                              {name: mx.array([2, 3], dtype=mx.uint64)})
        from bilqis_mlx.runtime.model_topology_v2 import (
            GenerationExtents, Initializer, ModelTopologySpecV2,
            ParameterGroup, ParameterSpec,
        )
        allocations = MotifAllocationSnapshot(MotifManifest(RELEASE))
        extents = GenerationExtents(
            1, 1, "a" * 64, allocations.manifest.digest, "c" * 64)
        spec = ModelTopologySpecV2()
        self.parent = CandidateState(
            state, PlasticityPolicy('ADAPTIVE', 7, (IdentityRowAge(0, 0, 7), IdentityRowAge(0, 1, 2))),
            allocations, 11,
            CandidateCustodyIdentity(
                "fixture-run", 0, "6" * 64, spec.digest,
                extents.digest))
        self.hp = AdamWHyperparameters(.001, (.9, .95), 1e-8, .01)
        self.name = name
        self.spec = spec
        self.extents = extents
        self.declared = (ParameterSpec(
            name, (2, 2), Initializer.EMBEDDING,
            ParameterGroup.IDENTITY_ROW_AGE, True),)
        self.no_decay_declared = (ParameterSpec(
            name, (2, 2), Initializer.EMBEDDING,
            ParameterGroup.IDENTITY_ROW_AGE, False),)

    def test_public_candidate_step_accepts_no_caller_decay(self):
        self.assertNotIn("decay", inspect.signature(candidate_step).parameters)

    def test_public_candidate_step_derives_no_decay_from_custody_bound_b01(self):
        optimizer = self.parent.optimizer
        zero_moments = AdamWStateTree(
            optimizer.parameters,
            {self.name: mx.zeros_like(optimizer.m[self.name])},
            {self.name: mx.zeros_like(optimizer.v[self.name])},
            optimizer.update_counts,
        )
        parent = replace(self.parent, optimizer=zero_moments)
        candidate = begin_candidate(parent)
        before = np.asarray(parent.optimizer.parameters[self.name]).copy()
        with patch(
                "bilqis_mlx.runtime.model_topology_v2.expected_bamf_shapes",
                return_value=self.no_decay_declared), patch(
                "bilqis_mlx.runtime.topology_v2.validation.expected_bamf_shapes",
                return_value=self.no_decay_declared):
            stepped = candidate_step(
                candidate, {self.name: mx.zeros((2, 2), dtype=mx.float32)},
                execution_provenance(parent, rows=(0,), candidate_step=1),
                self.hp, spec=self.spec, extents=self.extents,
                loss_bearing=True, max_norm=1.)
        np.testing.assert_array_equal(
            np.asarray(stepped.optimizer.parameters[self.name]), before)
        np.testing.assert_array_equal(
            np.asarray(stepped.optimizer.update_counts[self.name]), [3, 3])

    def test_direct_public_step_with_real_b11_authority_still_uses_b01_decay(self):
        source_row = {"id": "row-1", "capability": "A.TEST", "payload": "fixture"}
        delivery = BamfDeliveryProvenance(
            "row-1", source_content_digest((source_row,)), "source-1", "A.TEST", "op-1", (), 1, 1, None, 0,
            _visit_provenance("A.TEST"), "family-1", "episode-1", tuple(sorted((
                DependencyRef(DependencyKind.SOURCE, "row-1"),
                DependencyRef(DependencyKind.OPERATOR, "operator:op-1"),
                DependencyRef(DependencyKind.RELEASE, "source-release:" + "4" * 64),
                DependencyRef(DependencyKind.POLICY, "policy:fixture"),
                DependencyRef(DependencyKind.RIGHTS, "rights:fixture"),
            ))))
        batch = _issue_training_batch(
            "4" * 64, "5" * 64, content_digest((source_row,)), "A.TEST",
            (BamfTrainingRow(None, None, None, delivery),))
        source = SourceAtomRow(None, source_row, {}, Path("."), 0, 1)
        authority = issue_training_authority(batch, source, delivery)
        optimizer = self.parent.optimizer
        zero_moments = AdamWStateTree(
            optimizer.parameters,
            {self.name: mx.zeros_like(optimizer.m[self.name])},
            {self.name: mx.zeros_like(optimizer.v[self.name])},
            optimizer.update_counts,
        )
        parent = replace(self.parent, optimizer=zero_moments)
        before = np.asarray(parent.optimizer.parameters[self.name]).copy()
        with patch(
                "bilqis_mlx.runtime.model_topology_v2.expected_bamf_shapes",
                return_value=self.no_decay_declared), patch(
                "bilqis_mlx.runtime.topology_v2.validation.expected_bamf_shapes",
                return_value=self.no_decay_declared):
            stepped = candidate_step(
                begin_candidate(parent),
                {self.name: mx.zeros((2, 2), dtype=mx.float32)},
                execution_provenance(parent, rows=(0,), candidate_step=1),
                self.hp, spec=self.spec, extents=self.extents,
                loss_bearing=True, max_norm=1., training_authority=authority)
        np.testing.assert_array_equal(
            np.asarray(stepped.optimizer.parameters[self.name]), before)
        self.assertIs(stepped.training_authorities[0], authority)
        self.assertEqual(stepped.step_proofs[0].training_authority_sha256,
                         authority.digest)

    def step(self, candidate, rows=(0,), *, loss_bearing=True):
        with patch(
                "bilqis_mlx.runtime.model_topology_v2.expected_bamf_shapes",
                return_value=self.declared), patch(
                "bilqis_mlx.runtime.topology_v2.validation.expected_bamf_shapes",
                return_value=self.declared):
            return candidate_step(
                candidate,
                {self.name: mx.array([[3., 4.], [3e38, -3e38]], dtype=mx.float32)},
                execution_provenance(
                    candidate.parent, rows=rows, loss_bearing=loss_bearing,
                    candidate_step=candidate.update_steps + 1), self.hp,
                spec=self.spec, extents=self.extents,
                loss_bearing=loss_bearing, max_norm=1.)

    def snapshot(self, state):
        return tuple(np.asarray(getattr(state.optimizer, field)[self.name]).tobytes()
                     for field in ('parameters', 'm', 'v', 'update_counts'))

    def test_rejection_returns_exact_parent_with_all_custody(self):
        before = self.snapshot(self.parent)
        candidate = begin_candidate(self.parent, budget=MotifBudget(0))
        candidate = self.step(self.step(candidate))
        self.assertIs(resolve_candidate(candidate, accepted=False), self.parent)
        self.assertEqual(self.snapshot(self.parent), before)
        self.assertEqual(self.parent.policy.accepted_fast_since_full, 7)
        self.assertEqual(self.parent.optimizer_step, 11)
        self.assertEqual(self.parent.allocations.observed_uses, ())

    def test_acceptance_moves_entire_state_and_ages_once_for_two_steps(self):
        candidate = self.step(self.step(begin_candidate(self.parent)))
        accepted = resolve_candidate(candidate, accepted=True)
        np.testing.assert_array_equal(np.asarray(accepted.optimizer.update_counts[self.name]), [4, 3])
        self.assertEqual(accepted.optimizer_step, 13)
        self.assertEqual(tuple(r.accepted_age for r in accepted.policy.row_ages), (8, 2))
        self.assertEqual(accepted.policy.accepted_fast_since_full, 8)
        self.assertEqual(candidate.update_mode, 'FAST')
        self.assertEqual(begin_candidate(accepted).update_mode, 'FULL')
        self.assertNotEqual(self.snapshot(accepted), self.snapshot(self.parent))
        for field in ('parameters', 'm', 'v', 'update_counts'):
            np.testing.assert_array_equal(np.asarray(getattr(accepted.optimizer, field)[self.name][1]),
                                          np.asarray(getattr(self.parent.optimizer, field)[self.name][1]))

    def test_changing_step_masks_ages_union_once(self):
        first = self.step(begin_candidate(self.parent))
        with patch(
                "bilqis_mlx.runtime.model_topology_v2.expected_bamf_shapes",
                return_value=self.declared), patch(
                "bilqis_mlx.runtime.topology_v2.validation.expected_bamf_shapes",
                return_value=self.declared):
            second = candidate_step(
                first, {self.name: mx.zeros((2, 2), dtype=mx.float32)},
                execution_provenance(
                    first.parent, rows=(1,), candidate_step=first.update_steps + 1),
                self.hp, spec=self.spec, extents=self.extents,
                loss_bearing=True, max_norm=1.)
        accepted = resolve_candidate(second, accepted=True)
        self.assertEqual(tuple(r.accepted_age for r in accepted.policy.row_ages), (8, 3))
        np.testing.assert_array_equal(np.asarray(accepted.optimizer.update_counts[self.name]), [3, 4])

    def test_no_loss_or_wholly_frozen_candidate_cannot_advance_clocks_or_allocations(self):
        for kwargs in ({'loss_bearing': False}, {'rows': ()}):
            candidate = begin_candidate(self.parent, budget=MotifBudget(0))
            result = self.step(candidate, **kwargs)
            self.assertIs(result, candidate)
            self.assertIs(resolve_candidate(result, accepted=True), self.parent)

    def test_full_acceptance_resets_cadence_rejection_keeps_full_due(self):
        due = replace(self.parent, policy=replace(self.parent.policy, accepted_fast_since_full=8))
        candidate = self.step(begin_candidate(due))
        self.assertEqual(candidate.update_mode, 'FULL')
        self.assertIs(resolve_candidate(candidate, accepted=False), due)
        self.assertEqual(resolve_candidate(candidate, accepted=True).policy.accepted_fast_since_full, 0)
        self.assertEqual(begin_candidate(resolve_candidate(candidate, accepted=False)).update_mode, 'FULL')

    def test_teacher_full_and_foundation_use_existing_policy(self):
        for parent, request in ((self.parent, True),
                                (replace(self.parent, policy=PlasticityPolicy(row_ages=self.parent.policy.row_ages)), False)):
            candidate = self.step(begin_candidate(parent, teacher_requests_full=request))
            self.assertEqual(candidate.update_mode, 'FULL')
            self.assertEqual(resolve_candidate(candidate, accepted=True).policy.accepted_fast_since_full, 0)

    def test_invalid_state_and_decision_fail_before_parent_mutation(self):
        before = self.snapshot(self.parent)
        with self.assertRaises(BilqisError):
            replace(self.parent, optimizer_step=True)
        with self.assertRaises(BilqisError):
            replace(self.parent, policy=replace(self.parent.policy, row_ages=(IdentityRowAge(0, 3, 0),)))
        with self.assertRaises(BilqisError):
            resolve_candidate(begin_candidate(self.parent), accepted=1)
        self.assertEqual(self.snapshot(self.parent), before)

    def test_raw_caller_motif_frames_are_not_a_candidate_api(self):
        with self.assertRaises(TypeError):
            begin_candidate(self.parent, frames=(source(),), budget=MotifBudget(2))

        proposal = _prepare_candidate_motif_snapshot(
            (source(),), self.parent.allocations, MotifBudget(0))
        with self.assertRaises(BilqisError):
            replace(self.parent, allocations=proposal.proposed)

    def test_non_genesis_allocations_cannot_become_candidate_state(self):
        proposal = _prepare_candidate_motif_snapshot(
            (source(),), self.parent.allocations, MotifBudget(2))
        self.assertTrue(proposal.proposed.manifest.slots)
        with self.assertRaises(BilqisError):
            CandidateState(
                self.parent.optimizer, self.parent.policy,
                proposal.proposed, self.parent.optimizer_step)

    def test_caller_cannot_issue_transaction_with_arbitrary_optimizer_or_allocation(self):
        changed = AdamWStateTree(
            {self.name: self.parent.optimizer.parameters[self.name] + 100},
            self.parent.optimizer.m, self.parent.optimizer.v,
            {self.name: self.parent.optimizer.update_counts[self.name] + 1})
        with self.assertRaises(BilqisError):
            CandidateTransaction(self.parent, changed, self.parent.allocations, False, 1)
        legitimate = self.step(begin_candidate(self.parent, budget=MotifBudget(0)))
        with self.assertRaises(BilqisError):
            replace(legitimate, optimizer=changed)
        forged = replace(legitimate.allocations, observed_uses=(("a" * 64, 999),))
        with self.assertRaises(BilqisError):
            replace(legitimate, allocations=forged)
        self.assertEqual(resolve_candidate(legitimate, accepted=True).optimizer_step, 12)

    def test_v2_step_proof_roundtrips_source_training_authority(self):
        proof = CandidateStepProof(
            1, "1" * 64, "2" * 64, "3" * 64, (self.name,), True,
            source_release_sha256="4" * 64,
            training_batch_sha256="5" * 64,
            target_capability_id="A.TEST",
            training_authority_sha256="6" * 64,
            schema_version=PREVIOUS_STEP_PROOF_SCHEMA,
        )
        record = proof.to_record()
        self.assertEqual(record["schema_version"], "bilqis.mlx.candidate-step-proof/v2")
        self.assertEqual(record["target_capability_id"], "A.TEST")
        self.assertEqual(CandidateStepProof.from_record(record), proof)

    def test_v4_step_proof_roundtrips_logical_batch_member_authorities(self):
        members = (
            ("7" * 64, "family:a", "episode:a"),
            ("8" * 64, "family:a", "episode:b"),
        )
        proof = CandidateStepProof(
            1, "1" * 64, "2" * 64, "3" * 64, (self.name,), True,
            source_release_sha256="4" * 64,
            training_batch_sha256="5" * 64,
            target_capability_id="A.TEST",
            training_authority_sha256="6" * 64,
            training_authority_members=members,
            schema_version=LOGICAL_BATCH_STEP_PROOF_SCHEMA,
        )
        record = proof.to_record()
        self.assertEqual(
            record["schema_version"], "bilqis.mlx.candidate-step-proof/v4")
        self.assertEqual(record["training_authority_members"], members)
        self.assertEqual(CandidateStepProof.from_record(record), proof)

    def test_v6_step_proof_roundtrips_logical_batch_artifact_closure(self):
        members = (
            ("7" * 64, "family:a", "episode:a"),
            ("8" * 64, "family:a", "episode:b"),
        )
        proof = CandidateStepProof(
            1, "1" * 64, "2" * 64, "3" * 64, (self.name,), True,
            source_release_sha256="4" * 64,
            training_batch_sha256="5" * 64,
            target_capability_id="A.TEST",
            training_authority_sha256="6" * 64,
            training_authority_members=members,
            artifact_closure_sha256="9" * 64,
            schema_version=LOGICAL_BATCH_CLOSURE_STEP_PROOF_SCHEMA,
        )
        record = proof.to_record()
        self.assertEqual(
            record["schema_version"], "bilqis.mlx.candidate-step-proof/v6")
        self.assertEqual(record["training_authority_members"], members)
        self.assertEqual(record["artifact_closure_sha256"], "9" * 64)
        self.assertEqual(CandidateStepProof.from_record(record), proof)
