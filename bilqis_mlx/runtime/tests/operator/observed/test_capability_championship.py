"""Native BAMF title admission and origin-provenance coverage."""
from dataclasses import replace

from bilqis_mlx.learning.capability_championship_state import active_checkpoint_references

from bilqis_mlx.runtime.tests.operator.observed.capability_championship_support import (
    ADJUDICATION, CAPABILITY, GROUP, OTHER_GROUP, SIBLING,
    NativeChampionshipCase, bind_accepted_championship_successor,
    capability_cohort, evaluation, measurement, source_context, patch, Path,
)


class NativeCapabilityChampionshipTests(NativeChampionshipCase):
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

        def current_binding(*args, **_kwargs):
            measured = args[7]
            return other_binding if measured.capability_groups[0][0] == SIBLING else target_binding

        with patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "_require_factory_evaluation", side_effect=lambda value: value), patch(
                ADJUDICATION + "_current_binding", side_effect=current_binding), patch(
                ADJUDICATION + "_incumbent_binding",
                side_effect=AssertionError("empty titles must not replay incumbents")), patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "capability_championship_evidence",
                return_value=(other_cohort, other_assessment)):
            result = bind_accepted_championship_successor(
                Path("unused"), self.parent, self.cache, successor,
                self.context, "artifact", CAPABILITY,
                evaluation(self.cohort, target_assessment,
                           evaluated_capability_ids=(CAPABILITY, SIBLING)),
                checkpoint_origin_group=GROUP)
        role = result.championship_state["active_roles"][SIBLING]
        self.assertEqual(role["capability_group"], OTHER_GROUP)
        self.assertEqual(role["checkpoint_origin_group"], GROUP)
        self.assertEqual(role["checkpoint"]["sha256"], other_binding.checkpoint.sha256)
