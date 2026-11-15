"""Production authority adversaries for the consolidated EGM-Mitigation candidate.

These witnesses cover the authority seams end to end: owner-derived participation
inputs, provenance that cannot be replayed, retention acceptance that only the
retention decision owner can grant, and step proofs that survive immutable B13
publication and cold readback.
"""
from __future__ import annotations

import inspect
import json
from dataclasses import replace
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_acceptance import (
    AcceptedCandidateBinding, mint_acceptance_binding,
)
from bilqis_mlx.learning.atlas_plasticity import next_update_mode
from bilqis_mlx.learning.atlas_retention_decision import (
    CandidateRetentionDecision, decide_candidate_retention,
)
from bilqis_mlx.runtime.bamf_bundle import (
    load_bamf_generation, publish_bamf_generation,
)
from bilqis_mlx.learning.atlas_participation import (
    ActiveAdmittedRows, parameter_update_mask, step_participation,
)
from bilqis_mlx.learning.atlas_participation import (
    RoleReadParticipation, SemanticDenominator, StepParticipationInputs,
)
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _reset_execution_cache_owner_for_tests
from bilqis_mlx.runtime.bamf_bundle.admission import (
    admit_candidate_step, bind_accepted_execution_cache,
    derive_participation_inputs,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    AcceptedExecutionCache, bind_motif_artifact_owner,
    require_accepted_execution_cache,
)
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost,
    _reset_accepted_correction_runtime_for_tests, record_accepted_correction, record_accepted_revalidation,
)
from bilqis_mlx.runtime.atlas_revalidation import SourceAuthorityRegistry
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY, _event, _result
from bilqis_mlx.learning.tests.test_frame_encoder import FrameEncoderTests

from bilqis_mlx.learning._retention.tests.execution_fixtures import (
    execution_provenance,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    acceptance, accepted_state, candidate, parent_state, publish_candidate,
    retention_decision,
    provision_source_authority_registry, shape_patch, with_source_authority_registry,
)


def _participation():
    return step_participation(
        StepParticipationInputs(executed_parameter_names=("identity.bank.0",)),
        SemanticDenominator(), (), RoleReadParticipation())


def _active():
    return ActiveAdmittedRows(identity_rows=((0, 0),))


class ProductionAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()
        self._authority_registry = None

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def publish(self, source, registry=None):
        self._authority_registry = registry
        if registry is not None:
            provision_source_authority_registry(self.run, registry)
            source = with_source_authority_registry(source, registry)
        with self._shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_candidate(self.run, source)

    def _shape_patch(self):
        return (
            shape_patch()
            if self._authority_registry is None
            else shape_patch(self._authority_registry)
        )

    def test_production_step_accepts_no_caller_participation_facts(self):
        """The production API takes no caller-authored participation facts."""
        parameters = set(inspect.signature(
            admit_candidate_step).parameters)
        for forbidden in ("motif_reads", "executed_parameter_names", "visible_identity_rows",
                          "feedback_identity_rows", "local_slot_rows",
                          "group_eligible", "active_admitted", "spec", "extents",
                          "update_mask", "decay"):
            self.assertNotIn(forbidden, parameters)

    def test_group_eligibility_comes_from_the_ledger_and_policy_owners(self):
        self.publish(candidate(parent_state()))
        with self._shape_patch():
            student = admission.load_accepted_generation(self.run)
            eligibility, active = derive_participation_inputs(student)
        derived = set(eligibility.eligible_parameter_names) | set(
            eligibility.frozen_parameter_names)
        self.assertTrue(derived)
        self.assertFalse(set(eligibility.eligible_parameter_names)
                         & set(eligibility.frozen_parameter_names))
        self.assertEqual(eligibility.mode, next_update_mode(
            student.retained_state.policy, teacher_requests_full=False))
        self.assertEqual(active.identity_rows, eligibility.admitted_identity_rows)

    def test_only_accepted_b13_custody_mints_live_execution_cache(self):
        self.publish(candidate(parent_state()))
        with self._shape_patch():
            accepted = admission.load_accepted_generation(self.run)
            cache = bind_accepted_execution_cache(self.run)
            rebound = bind_accepted_execution_cache(self.run)
            self.assertIs(require_accepted_execution_cache(cache), cache)
        self.assertIs(rebound, cache)
        self.assertEqual(cache.run_id, "fixture-run")
        self.assertEqual(
            cache.motif_manifest.digest,
            accepted.retained_state.allocations.manifest.digest,
        )
        with self.assertRaises(BilqisError):
            AcceptedExecutionCache()

    def test_signed_accepted_correction_replays_into_motif_owner_after_cold_restart(self):
        self.publish(candidate(parent_state()), AUTHORITY)
        with self._shape_patch():
            cache = bind_accepted_execution_cache(self.run)
        fixture = FrameEncoderTests()
        fixture.setUp()
        compiled, _vectors, _ast = fixture.compiled_inputs()
        compiled = replace(
            compiled,
            extents=replace(
                compiled.extents,
                motif_key_map_digest=cache.motif_manifest.digest,
            ),
        )
        with self._shape_patch():
            owner = bind_motif_artifact_owner(cache, compiled)
        correction = _event(owner.source_dependencies[0])
        with self._shape_patch():
            AcceptedRuntimeHost(self.run).record_correction(correction)
        self.assertTrue(owner.queue.held_artifact_ids)
        with self.assertRaises(BilqisError):
            owner.require(cache, compiled)

        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        with self._shape_patch():
            cold_cache = bind_accepted_execution_cache(self.run)
        self.assertIsNot(cold_cache, cache)
        with self._shape_patch(), self.assertRaises(BilqisError):
            bind_motif_artifact_owner(cold_cache, compiled)

    def test_provenance_cannot_replay_onto_another_candidate_or_step(self):
        self.publish(candidate(parent_state()))
        with self._shape_patch():
            student = admission.load_accepted_generation(self.run)
        issued = execution_provenance(student.retained_state, rows=(0,))
        with self.assertRaises(BilqisError):
            replace(issued, run_id="other-run")
        with self.assertRaises(BilqisError):
            replace(issued, generation=99)
        with self.assertRaises(BilqisError):
            replace(issued, parent_manifest_sha256="9" * 64)
        with self.assertRaises(BilqisError):
            replace(issued, topology_digest="9" * 64)
        with self.assertRaises(BilqisError):
            replace(issued, extents_sha256="9" * 64)
        with self.assertRaises(BilqisError):
            replace(issued, parent_candidate_identity_sha256="9" * 64)
        with self.assertRaises(BilqisError):
            replace(issued, parent_optimizer_step=999)
        with self.assertRaises(BilqisError):
            replace(issued, candidate_step=2)

    def test_caller_created_candidate_cannot_publish_without_the_decision_owner(self):
        source = candidate(parent_state())
        with self._shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            with self.assertRaises(BilqisError):
                publish_bamf_generation(self.run, source)
        self.assertFalse((self.run / "bamf-state.json").exists())

    def test_caller_cannot_mint_a_retention_decision(self):
        decision = retention_decision()
        with self.assertRaises(BilqisError):
            CandidateRetentionDecision(
                decision.decision, decision.reason, decision.parent_generation,
                decision.candidate_generation, decision.evidence_sha256,
                decision.policy_sha256)

    def test_primitive_retention_claims_cannot_issue_authority(self):
        with self.assertRaises(TypeError):
            decide_candidate_retention(
                no_target_gain=False, same_grade_net_gain=1,
                fixed_grade_regression=False, active_grade_regression=False,
                whole_school_regression=False, frontier_measured=True,
                fragile_losses=0, exceeded=False)

    def test_caller_selected_c05_screen_cannot_issue_live_authority(self):
        from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
            _screen_inputs,
        )
        screen = _screen_inputs()
        with self.assertRaises(BilqisError) as failure:
            decide_candidate_retention(
                parent_solver=screen[0], candidate_solver=screen[1],
                target_capability=screen[2], policy=screen[3], cohorts=screen[4],
                parent_state=parent_state(),
                candidate_state=accepted_state(parent_state()))
        self.assertEqual(failure.exception.context["reason"],
                         "BAMF_C05_SOURCE_OWNER_REQUIRED")

    def test_acceptance_requires_an_accepted_decision(self):
        source = candidate(parent_state())
        rejected = retention_decision(
            accepted=False, retained=source.retained_state)
        with self.assertRaises(BilqisError):
            mint_acceptance_binding(
                rejected, source.retained_state, run_id=source.run_id,
                generation=source.generation,
                feature_sha256=source.extents.factor_map_digest)

    def test_step_proofs_survive_publication_and_cold_readback(self):
        initial = parent_state()
        first = self.publish(candidate(initial))
        retained = accepted_state(initial)
        second = self.publish(candidate(retained, 1, first["manifest_sha256"]))
        with self._shape_patch():
            student = load_bamf_generation(self.run / "bamf-state.json")
        proofs = student.retained_state.step_proofs
        self.assertEqual(len(proofs), 1)
        binding = AcceptedCandidateBinding.from_record(json.loads(
            (self.run / "bamf-acceptance" / f"{second['manifest_sha256']}.json")
            .read_text()))
        self.assertEqual(list(binding.step_proof_sha256),
                         [proof.digest for proof in proofs])

    def test_tampered_step_proof_fails_custody_validation(self):
        initial = parent_state()
        first = self.publish(candidate(initial))
        retained = accepted_state(initial)
        second = self.publish(candidate(retained, 1, first["manifest_sha256"]))
        proofs = (self.run / "bamf-bundles" / second["manifest_sha256"]
                  / "step-proofs.json")
        record = json.loads(proofs.read_text())
        record["proofs"][0]["mask_sha256"] = "0" * 64
        proofs.write_text(json.dumps(record))
        with self._shape_patch():
            with self.assertRaises(BilqisError):
                load_bamf_generation(self.run / "bamf-state.json")


if __name__ == "__main__":
    unittest.main()
