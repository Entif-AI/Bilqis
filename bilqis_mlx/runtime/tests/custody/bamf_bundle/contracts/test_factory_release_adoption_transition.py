"""B13 owns the neural-inert Factory-release adoption transition."""
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.runtime.bamf_bundle.factory_release_adoption import (
    FACTORY_RELEASE_ADOPTION_EVENT,
    FACTORY_RELEASE_ADOPTION_EVENT_SCHEMA,
    FACTORY_RELEASE_ADOPTION_KIND,
    FactoryReleaseAdoptionTransition,
    _issue_factory_release_adoption_transition,
    derive_factory_release_adoption_candidate,
)
from bilqis_mlx.runtime.tests.admission.atlas.adoption.atlas_adoption_executor_support import (
    AtlasAdoptionExecutorFixture,
)


class FactoryReleaseAdoptionTransitionTests(unittest.TestCase):
    def test_profile_transition_binds_parent_and_round_trips_without_a09(self):
        from bilqis_mlx.runtime.bamf_bundle.factory_release_adoption import (
            _issue_profile_expansion_transition,
        )
        from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
            _issue_factory_release_admission_binding,
            FactoryReleaseAdmissionBinding,
        )
        helper = object.__new__(AtlasAdoptionExecutorFixture)
        parent, _ = AtlasAdoptionExecutorFixture._native_parent_and_candidate(helper)
        transition = _issue_profile_expansion_transition(
            predecessor_factory_release_sha256='1' * 64,
            factory_release_sha256='2' * 64, profile_sha256='3' * 64,
            parent_manifest_sha256='a' * 64, lease_sha256='4' * 64,
            source_approval_sha256='5' * 64, profile_transition_sha256='6' * 64)
        candidate = derive_factory_release_adoption_candidate(
            parent, parent_manifest_sha256='a' * 64, transition=transition)
        binding = _issue_factory_release_admission_binding(
            candidate, parent, transition=transition)
        parsed = FactoryReleaseAdmissionBinding.from_record(binding.to_record())
        from dataclasses import asdict
        self.assertEqual(asdict(binding)['handoff_sha256'], None)
        self.assertEqual(asdict(transition)['profile_sha256'], '3' * 64)
        self.assertIn('PROFILE_EXPANSION', repr(transition))
        self.assertIn('FactoryReleaseAdmissionBinding', repr(binding))
        other = _issue_profile_expansion_transition(
            predecessor_factory_release_sha256='1' * 64,
            factory_release_sha256='2' * 64, profile_sha256='f' * 64,
            parent_manifest_sha256='a' * 64, lease_sha256='4' * 64,
            source_approval_sha256='5' * 64, profile_transition_sha256='6' * 64)
        self.assertNotEqual(transition, other)
        self.assertEqual(parsed.digest, binding.digest)
        self.assertEqual(parsed.accepted_obligation_keys, ())
        self.assertNotIn('handoff_sha256', binding.to_record())
        self.assertNotIn('proposal_sha256', candidate.outbox[0])
        self.assertIs(candidate.retained_state, parent.retained_state)
        for field in ('profile_sha256', 'parent_manifest_sha256', 'lease_sha256'):
            record = binding.to_record()
            record.pop(field)
            with self.assertRaises(BilqisError):
                FactoryReleaseAdmissionBinding.from_record(record)
        record = binding.to_record()
        record['handoff_sha256'] = 'f' * 64
        with self.assertRaises(BilqisError):
            FactoryReleaseAdmissionBinding.from_record(record)
        with self.assertRaises(BilqisError):
            derive_factory_release_adoption_candidate(
                parent, parent_manifest_sha256='b' * 64, transition=transition)

    @staticmethod
    def _transition():
        return _issue_factory_release_adoption_transition(
            predecessor_factory_release_sha256="1" * 64,
            factory_release_sha256="2" * 64,
            handoff_sha256="3" * 64,
            proposal_sha256="4" * 64,
            staged_candidate_sha256="5" * 64,
            selection_receipt_sha256="6" * 64,
            lease_sha256="7" * 64,
            source_approval_sha256="8" * 64,
        )

    def test_transition_is_not_caller_constructible(self):
        with self.assertRaises(BilqisError):
            FactoryReleaseAdoptionTransition()

    def test_successor_is_generation_only_and_neural_state_identical(self):
        helper = object.__new__(AtlasAdoptionExecutorFixture)
        parent, _unused = AtlasAdoptionExecutorFixture._native_parent_and_candidate(helper)
        transition = self._transition()
        successor = derive_factory_release_adoption_candidate(
            parent,
            parent_manifest_sha256="a" * 64,
            transition=transition,
        )

        self.assertEqual(successor.generation, parent.generation + 1)
        self.assertEqual(successor.parent_manifest_sha256, "a" * 64)
        self.assertIs(successor.retained_state, parent.retained_state)
        self.assertEqual(
            candidate_identity_digest(successor.retained_state),
            candidate_identity_digest(parent.retained_state),
        )
        self.assertEqual(successor.topology, parent.topology)
        self.assertEqual(successor.extents, parent.extents)
        self.assertEqual(successor.semantic_abi, parent.semantic_abi)
        self.assertEqual(successor.optimizer_hyperparameters, parent.optimizer_hyperparameters)
        self.assertEqual(successor.provenance, parent.provenance)
        self.assertEqual(successor.compiler_features, parent.compiler_features)
        self.assertEqual(successor.correction_frontier, parent.correction_frontier)
        self.assertEqual(successor.teacher_state, parent.teacher_state)
        self.assertEqual(successor.evaluation_contract, parent.evaluation_contract)
        self.assertIs(successor.transition, transition)
        self.assertEqual(successor.transition["kind"], FACTORY_RELEASE_ADOPTION_KIND)
        self.assertFalse(successor.transition["invalidate_derived_caches"])
        self.assertEqual(len(successor.outbox), 1)
        event = successor.outbox[0]
        self.assertEqual(event["event"], FACTORY_RELEASE_ADOPTION_EVENT)
        self.assertEqual(event["schema"], FACTORY_RELEASE_ADOPTION_EVENT_SCHEMA)
        self.assertNotIn("event_id", event)
        self.assertEqual(event["transition_sha256"], transition.digest)


if __name__ == "__main__":
    unittest.main()
