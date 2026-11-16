"""Accepted-run C09 operator-composition replay and branch custody."""

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost,
    record_accepted_correction, record_accepted_revalidation, register_solve_context,
)
from bilqis_mlx.runtime.atlas_revalidation import RevalidationFrontier
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, shape_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.correction_runtime.composition_support import (
    AUTHORITY, AcceptedCorrectionCompositionCase, _event, _result,
)
from bilqis_mlx.runtime.tests.capability.factory.solver_helpers import _fixture
from bilqis_mlx.runtime.cognitive_solver import QualifiedComposition, SolveContext
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind, DependencyRef
from bilqis_mlx.semantics.domains import contract_digest


class AcceptedCorrectionCompositionReplayTests(AcceptedCorrectionCompositionCase):
    def test_operator_composition_declares_direct_policy_and_time_premises(self):
            binding, context, compositions = self._composition_context(1)
            node = context.operator_composition_artifact_owner.node_for(compositions[0])
            refs = set(node.immediate_dependencies)
            self.assertIn(DependencyRef(
                DependencyKind.POLICY,
                "policy:" + contract_digest((
                    binding.task.scope,
                    binding.policy.policy_id,
                    binding.policy.policy_epoch,
                )),
            ), refs)
            self.assertIn(DependencyRef(
                DependencyKind.TIME,
                "time:observed-frontier:" + str(binding.task.observed_frontier),
            ), refs)
            self.assertIn(DependencyRef(
                DependencyKind.TIME,
                "time:effective:" + str(binding.task.effective_time),
            ), refs)
            self.assertIn(DependencyRef(
                DependencyKind.TIME,
                "time:causal-prefix-end:" + str(binding.task.causal_prefix_end),
            ), refs)

    def test_multi_result_frontier_consumes_every_applicable_held_artifact(self):
            self.publish(candidate(parent_state()))
            binding, context, compositions = self._composition_context(2)
            with self._shape_patch():
                register_solve_context(self.run, context)
            correction = _event(DependencyRef(
                DependencyKind.SOURCE, "source:binding:" + contract_digest(binding)))
            with self._shape_patch():
                AcceptedRuntimeHost(self.run).record_correction(correction)
            owner = context.operator_composition_artifact_owner
            results = tuple(sorted((
                _result(owner.node_for(item), digest=owner.node_for(item).content_digest,
                        correction=correction).results[0]
                for item in compositions), key=lambda item: item.artifact_id))
            with self._shape_patch():
                AcceptedRuntimeHost(self.run).record_revalidation(RevalidationFrontier(results))
            self.assertEqual(owner.queue.held_artifact_ids, ())

    def test_deferred_frontier_remembers_partial_consumption_across_retry(self):
            self.publish(candidate(parent_state()))
            binding, context, _compositions = self._composition_context(3)
            with self._shape_patch():
                register_solve_context(self.run, context)
            correction = _event(DependencyRef(
                DependencyKind.SOURCE, "source:binding:" + contract_digest(binding)))
            with self._shape_patch():
                AcceptedRuntimeHost(self.run).record_correction(correction)
            owner = context.operator_composition_artifact_owner
            task_ids = tuple(task.artifact_id for task in owner.queue.pending)
            by_id = {
                item.artifact_id: _result(
                    item, digest=item.content_digest, correction=correction).results[0]
                for item in owner.index.nodes
            }
            with self._shape_patch():
                first_event = AcceptedRuntimeHost(self.run).record_revalidation(RevalidationFrontier((by_id[task_ids[0]], by_id[task_ids[2]])))
            with self._shape_patch():
                AcceptedRuntimeHost(self.run).record_revalidation(RevalidationFrontier((by_id[task_ids[1]],)))
            self.assertEqual(owner.queue.held_artifact_ids, ())

    def test_same_logical_artifact_owners_all_remain_live_for_later_correction(self):
            self.publish(candidate(parent_state()))
            binding, first_context, compositions = self._composition_context(1)
            second_context = SolveContext(
                binding, qualified_compositions=compositions,
                qualification_verifier=lambda item: True)
            with self._shape_patch():
                register_solve_context(self.run, first_context)
                register_solve_context(self.run, second_context)
            dependency = DependencyRef(
                DependencyKind.SOURCE,
                "source:binding:" + contract_digest(binding),
            )
            correction = _event(dependency)

            with self._shape_patch():
                AcceptedRuntimeHost(self.run).record_correction(correction)

            for context in (first_context, second_context):
                owner = context.operator_composition_artifact_owner
                self.assertIsNotNone(owner.queue)
                self.assertEqual(owner.queue.event.event_id, correction.event_id)
                with self.assertRaises(BilqisError):
                    owner.require(compositions[0], binding)

    def test_late_materialization_rechecks_all_active_concurrent_branches(self):
            self.publish(candidate(parent_state()))
            binding, context, compositions = self._composition_context(1)
            with self._shape_patch():
                register_solve_context(self.run, context)
            correction_a, correction_b = self._concurrent_corrections(binding)
            owner = context.operator_composition_artifact_owner

            with self._shape_patch():
                AcceptedRuntimeHost(self.run).record_correction(correction_a)
            self._record_equal_revalidation(
                owner, compositions[0], correction_a)
            with self._shape_patch():
                AcceptedRuntimeHost(self.run).record_correction(correction_b)
            self._record_equal_revalidation(
                owner, compositions[0], correction_b)
            self.assertEqual(owner.queue.held_artifact_ids, ())

            _binding, generation, _budget, add, _ambiguous = _fixture()
            learned = QualifiedComposition(
                add, generation.source_binding_digest, generation.generation_digest,
                binding.frontier.rights_epoch, binding.frontier.correction_generation,
                "f" * 64)
            self.assertTrue(owner.remember(learned, binding))
            with self.assertRaises(BilqisError) as held:
                owner.require(learned, binding)
            self.assertEqual(
                held.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")
            for correction in (correction_a, correction_b):
                if (owner.queue is None
                        or owner.queue.event.event_id != correction.event_id):
                    continue
                self._record_equal_revalidation(owner, learned, correction)
            if owner.queue is not None and owner.queue.pending:
                self._record_equal_revalidation(
                    owner, learned, owner.queue.event)
            self.assertIsNotNone(owner.require(learned, binding))
