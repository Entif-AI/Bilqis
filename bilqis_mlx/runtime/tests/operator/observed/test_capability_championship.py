"""Native BAMF title admission and origin-provenance coverage."""
from dataclasses import replace

from bilqis_mlx.learning.capability_championship_state import active_checkpoint_references
from bilqis_mlx.runtime.capability_retention import EvidenceStage

from bilqis_mlx.runtime.tests.operator.observed.capability_championship_support import (
    ADJUDICATION, CAPABILITY, GROUP, OTHER_GROUP, SIBLING,
    NativeChampionshipCase, bind_accepted_championship_successor,
    capability_cohort, evaluation, measurement, source_context, patch, Path,
)


class NativeCapabilityChampionshipTests(NativeChampionshipCase):
    def test_explicit_accepted_boundary_computes_target_evidence_when_c05_did_not(self):
        successor = self.successor()
        assessment, binding = measurement(
            successor, self.cohort, self.contexts, 19, "8" * 64)
        c05 = evaluation(None, None, evaluated_capability_ids=(CAPABILITY,))
        observed = []

        with patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "_require_factory_evaluation", side_effect=lambda value: value), patch(
                ADJUDICATION + "_current_binding", return_value=binding), patch(
                ADJUDICATION + "_incumbent_binding",
                side_effect=AssertionError("empty titles must not replay incumbents")), patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "capability_championship_evidence",
                return_value=(self.cohort, assessment)) as championship:
            result = bind_accepted_championship_successor(
                Path("unused"), self.parent, self.cache, successor,
                self.context, "artifact", CAPABILITY, c05,
                training=(("family:train",), ("episode:train",)),
                evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
                checkpoint_origin_group=GROUP,
                observer=observed.append)

        championship.assert_called_once()
        self.assertEqual(
            championship.call_args.args,
            (self.context, successor, "artifact", self.cache, CAPABILITY,
             (("family:train",), ("episode:train",)),
             EvidenceStage.FOUNDATION_ACQUISITION))
        self.assertTrue(callable(championship.call_args.kwargs["observer"]))
        self.assertIn(CAPABILITY, result.championship_state["active_roles"])

    def test_exact_ninety_percent_keeps_no_active_title_or_checkpoint_custody(self):
        successor = self.successor()
        assessment, binding = measurement(
            successor, self.cohort, self.contexts, 18, "8" * 64)
        result = self.bind(self.parent, successor, assessment, binding)
        self.assertEqual(result.championship_state["active_roles"], {})
        self.assertEqual(active_checkpoint_references(result.championship_state), ())

    def test_nineteen_of_twenty_earns_first_title_without_grade_ontology(self):
        successor = self.successor()
        assessment, binding = measurement(
            successor, self.cohort, self.contexts, 19, "8" * 64)
        result = self.bind(self.parent, successor, assessment, binding)
        role = result.championship_state["active_roles"][CAPABILITY]
        self.assertEqual((role["correct"], role["total"]), (19, 20))
        self.assertEqual(role["capability_group"], GROUP)
        self.assertEqual(active_checkpoint_references(result.championship_state),
                         (role["checkpoint"],))

    def test_checkpoint_origin_is_provenance_not_title_jurisdiction(self):
        successor = self.successor()
        origin = "opaque-origin-alpha"
        assessment, binding = measurement(
            successor, self.cohort, self.contexts, 19, "8" * 64)
        binding = replace(binding, checkpoint_origin_group=origin)
        result = self.bind(
            self.parent, successor, assessment, binding,
            checkpoint_origin_group=origin)
        role = result.championship_state["active_roles"][CAPABILITY]
        self.assertEqual(role["capability_group"], GROUP)
        self.assertEqual(role["checkpoint_origin_group"], origin)

    def test_native_measured_cross_group_capability_keeps_update_origin(self):
        self.context = source_context(include_sibling=True, sibling_group=OTHER_GROUP)
        successor = self.successor()
        target_assessment, target_binding = measurement(
            successor, self.cohort, self.contexts, 19, "8" * 64)
        other_cohort, other_contexts = capability_cohort(SIBLING, OTHER_GROUP)
        other_assessment, other_binding = measurement(
            successor, other_cohort, other_contexts, 19, "9" * 64)
        target_binding = replace(target_binding, checkpoint_origin_group=GROUP)
        other_binding = replace(other_binding, checkpoint_origin_group=GROUP)
        observed = []

        def current_binding(*args, **_kwargs):
            measured = args[7]
            return other_binding if measured.capability_groups[0][0] == SIBLING else target_binding

        def championship_evidence(
                _context, _successor, _artifact, _cache, capability,
                _training, _stage, *, observer=None):
            if observer is not None:
                observer({
                    "championship_prepare_wall_seconds": (
                        1.0 if capability == CAPABILITY else 2.0),
                    "championship_case_count": 20,
                    "championship_shared_backbone_launches": 1,
                    "championship_scalar_neural_launches": 0,
                })
            return (
                (self.cohort, target_assessment)
                if capability == CAPABILITY
                else (other_cohort, other_assessment)
            )

        with patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "_require_factory_evaluation", side_effect=lambda value: value), patch(
                ADJUDICATION + "_current_binding", side_effect=current_binding), patch(
                ADJUDICATION + "_incumbent_binding",
                side_effect=AssertionError("empty titles must not replay incumbents")), patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "capability_championship_evidence",
                side_effect=championship_evidence):
            result = bind_accepted_championship_successor(
                Path("unused"), self.parent, self.cache, successor,
                self.context, "artifact", CAPABILITY,
                evaluation(None, None, evaluated_capability_ids=(CAPABILITY, SIBLING)),
                checkpoint_origin_group=GROUP,
                training=((), ()),
                evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
                observer=observed.append,
                boundary_capabilities=(CAPABILITY, SIBLING))
        role = result.championship_state["active_roles"][SIBLING]
        self.assertEqual(role["capability_group"], OTHER_GROUP)
        self.assertEqual(role["checkpoint_origin_group"], GROUP)
        self.assertEqual(role["checkpoint"]["sha256"], other_binding.checkpoint.sha256)
        profile = {}
        for event in observed:
            profile.update(event)
        self.assertEqual(profile["championship_prepare_wall_seconds"], 3.0)
        self.assertEqual(profile["championship_case_count"], 40)
        self.assertEqual(profile["championship_shared_backbone_launches"], 2)
        self.assertEqual(profile["championship_scalar_neural_launches"], 0)
