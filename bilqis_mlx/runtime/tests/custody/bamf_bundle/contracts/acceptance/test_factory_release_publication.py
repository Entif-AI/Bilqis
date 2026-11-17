from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.acceptance.factory_release_admission_binding_support import *
import unittest

class FactoryReleasePublicationTests(GenerationAcceptanceFixture, unittest.TestCase):
    def test_profile_publication_rejects_stale_active_grade(self):
        from bilqis_mlx.runtime.bamf_bundle.factory_release_adoption import (
            _issue_profile_expansion_transition,
        )
        parent = self.parent()
        manifest = self._parent_pointer['manifest_sha256']
        transition = _issue_profile_expansion_transition(
            predecessor_factory_release_sha256=parent.run_identity.factory_release_sha256,
            factory_release_sha256='2' * 64, profile_sha256='3' * 64,
            parent_manifest_sha256=manifest, lease_sha256='4' * 64,
            source_approval_sha256='5' * 64, profile_transition_sha256='6' * 64)
        candidate = derive_factory_release_adoption_candidate(
            parent, parent_manifest_sha256=manifest, transition=transition)
        binding = _issue_factory_release_admission_binding(candidate, parent, transition=transition)
        with shape_patch(), patch.object(mlx_checkpoint, 'assert_headroom'):
            with self.assertRaises(BilqisError):
                publish_factory_release_adoption_generation(
                    self.run, candidate, admission=binding, reserve_gib=0.,
                    expected_active_grade_activation_sha256='a' * 64)
            _, digest = load_bamf_generation_authority(self.run / 'bamf-state.json')
        self.assertEqual(digest, manifest)

    def test_profile_child_publishes_and_cold_loads(self):
        from bilqis_mlx.runtime.bamf_bundle.factory_release_adoption import (
            _issue_profile_expansion_transition,
        )
        parent = self.parent()
        manifest = self._parent_pointer['manifest_sha256']
        transition = _issue_profile_expansion_transition(
            predecessor_factory_release_sha256=parent.run_identity.factory_release_sha256,
            factory_release_sha256='2' * 64, profile_sha256='3' * 64,
            parent_manifest_sha256=manifest, lease_sha256='4' * 64,
            source_approval_sha256='5' * 64, profile_transition_sha256='6' * 64)
        candidate = derive_factory_release_adoption_candidate(
            parent, parent_manifest_sha256=manifest, transition=transition)
        binding = _issue_factory_release_admission_binding(
            candidate, parent, transition=transition,
            accepted_obligation_keys=(('obligation', '7' * 64),))
        with shape_patch(), patch.object(mlx_checkpoint, 'assert_headroom'):
            pointer = publish_factory_release_adoption_generation(
                self.run, candidate, admission=binding, reserve_gib=0.0)
            cold, digest = load_bamf_generation_authority(self.run / 'bamf-state.json')
        self.assertEqual(pointer['manifest_sha256'], digest)
        self.assertEqual(cold.transition['kind'], 'PROFILE_EXPANSION')
        self.assertEqual(cold.transition['parent_manifest_sha256'], manifest)
        self.assertEqual(cold.retained_state.optimizer_step, parent.retained_state.optimizer_step)

    def test_real_factory_release_child_publishes_and_cold_loads_exactly(self):
        parent = self.parent()
        transition = _issue_factory_release_adoption_transition(
            predecessor_factory_release_sha256=parent.run_identity.factory_release_sha256,
            factory_release_sha256="2" * 64,
            handoff_sha256="3" * 64,
            proposal_sha256="4" * 64,
            staged_candidate_sha256="5" * 64,
            selection_receipt_sha256="6" * 64,
            lease_sha256="7" * 64,
            source_approval_sha256="8" * 64,
        )
        candidate = derive_factory_release_adoption_candidate(
            parent,
            parent_manifest_sha256=self._parent_pointer["manifest_sha256"],
            transition=transition,
        )
        binding = _issue_factory_release_admission_binding(
            candidate,
            parent,
            transition=transition,
        )

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_factory_release_adoption_generation(
                self.run,
                candidate,
                admission=binding,
                reserve_gib=0.0,
            )
            cold, manifest_sha256 = load_bamf_generation_authority(
                self.run / "bamf-state.json"
            )

        self.assertEqual(pointer["generation"], parent.generation + 1)
        self.assertEqual(pointer["manifest_sha256"], manifest_sha256)
        self.assertEqual(cold.parent_manifest_sha256, self._parent_pointer["manifest_sha256"])
        self.assertEqual(cold.retained_state.optimizer_step, parent.retained_state.optimizer_step)
        self.assertEqual(cold.topology.digest, parent.topology.digest)
        self.assertEqual(cold.extents.digest, parent.extents.digest)
        self.assertEqual(cold.transition["kind"], "FACTORY_RELEASE_ADOPTION")
        self.assertEqual(cold.transition["factory_release_sha256"], "2" * 64)

    def test_generated_grade_semantic_admission_publishes_with_empty_settlement_authority(self):
        from bilqis_mlx.learning.capability_championship_state import (
            championship_epoch_identity, compact_championship_state,
        )
        parent = self.parent()
        identity = championship_epoch_identity(
            factory_release_sha256="1" * 64, semantic_catalog_sha256="2" * 64,
            curriculum_sha256="3" * 64,
            capability_groups=(("future:capability", "future:group"),),
            fixed_cohort_sha256="4" * 64, rubric_sha256="5" * 64,
            scope_sha256="6" * 64, source_sha256="7" * 64,
            policy_sha256="8" * 64, topology_sha256=parent.topology.digest,
            extents_sha256=parent.extents.digest, semantic_abi=parent.semantic_abi)
        parent = replace(parent, championship_state=compact_championship_state({
            "active_roles": {},
            "settled_matchups": {
                "future:capability|" + "9" * 64 + "|" + "a" * 64: {
                    "capability": "future:capability", "winner_sha256": "9" * 64,
                },
            },
        }, identity))
        transition = _issue_factory_release_adoption_transition(
            predecessor_factory_release_sha256=parent.run_identity.factory_release_sha256,
            factory_release_sha256="2" * 64, handoff_sha256="3" * 64,
            proposal_sha256="4" * 64, staged_candidate_sha256="5" * 64,
            selection_receipt_sha256="6" * 64, lease_sha256="7" * 64,
            source_approval_sha256="8" * 64)
        candidate = derive_factory_release_adoption_candidate(
            parent, parent_manifest_sha256=self._parent_pointer["manifest_sha256"],
            transition=transition, new_semantic_admission=True)
        binding = _issue_factory_release_admission_binding(
            candidate, parent, transition=transition,
            accepted_obligation_keys=(("semantic:event", "b" * 64),),
            generated_grade_proposal_sha256="a" * 64)
        from bilqis_mlx.runtime.bamf_bundle.publication.authority import (
            validate_parent_transition,
        )
        validated = validate_parent_transition(
            self.run, self._parent_pointer, candidate,
            load_bundle=lambda *_args, **_kwargs: parent,
            reconcile=lambda *_args, **_kwargs: None,
            parent=parent, factory_release_new_semantic_admission=True)
        self.assertIs(validated, parent)
        self.assertEqual(candidate.championship_state["settled_matchups"], {})
        self.assertEqual(
            candidate.championship_state["epoch_history"][-1]["reason"],
            "NEW_SEMANTIC_ADMISSION")
