from dataclasses import replace
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bilqis_mlx.factory.autonomy import compile_autonomy_plan, initial_evidence_ledger
from bilqis_mlx.factory.jit_curriculum import propose_curriculum_delta
from bilqis_mlx.factory.tests.curriculum.frontier.test_candidate_staging import CandidateStagingFixture
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.jit_adoption import (
    resolve_ready_candidate, verify_current_implementations,
)


class JitAdoptionTests(CandidateStagingFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.staged = self.stage()
        self.plan = compile_autonomy_plan(self.current)
        self.ledger = initial_evidence_ledger(self.current, plan=self.plan)
        self.checkpoint = Checkpoint("e" * 64, "bundles/fixture", 0, True)
        self.proposal = propose_curriculum_delta(self.frontier, self.current,
            self.ledger, self.plan, self.checkpoint.sha256, self.checkpoint.optimizer_step,
            candidate_bindings=(self.staged.binding,))

    def resolve(self, **overrides):
        arguments = dict(frontier=self.frontier, current=self.current,
            ledger=self.ledger, plan=self.plan, checkpoint=self.checkpoint,
            proposal=self.proposal, staged=(self.staged,))
        arguments.update(overrides)
        return resolve_ready_candidate(**arguments)

    def test_exact_current_proposal_resolves_without_mutating_learner(self):
        self.assertEqual(self.resolve(), self.staged)
        self.assertEqual(self.checkpoint.optimizer_step, 0)
        self.assertEqual(self.ledger.receipts, ())

    def test_checkpoint_or_optimizer_drift_prevents_adoption(self):
        for checkpoint in (replace(self.checkpoint, sha256="f" * 64),
                           replace(self.checkpoint, optimizer_step=1)):
            with self.assertRaisesRegex(ValueError, "PROPOSAL_CONTEXT_CHANGED"):
                self.resolve(checkpoint=checkpoint)

    def test_new_evidence_and_missing_package_require_a_new_proposal(self):
        with self.assertRaisesRegex(ValueError, "PROPOSAL_CONTEXT_CHANGED"):
            self.resolve(staged=())
        from bilqis_mlx.factory.autonomy import EvidenceReceipt, record_evidence, obligations_for_capability
        obligation = obligations_for_capability(self.current, "Z.C0", plan=self.plan)[0]
        ledger = record_evidence(self.current, self.ledger, EvidenceReceipt(
            obligation.obligation_id, "new-evidence", "e" * 64, 0,
            "d" * 64, obligation.minimum_specimens, True), plan=self.plan)
        with self.assertRaisesRegex(ValueError, "PROPOSAL_CONTEXT_CHANGED"):
            self.resolve(ledger=ledger)


    def test_changed_frontier_predecessor_and_package_invalidate_prepared_work(self):
        from bilqis_mlx.factory.executable_release import compile_executable_factory_release

        changed = replace(self.frontier, senses=(replace(
            self.frontier.senses[0], source_text_sha256="f" * 64),))
        frontier = replace(changed, release_sha256=changed.expected_digest())
        with self.assertRaisesRegex(ValueError, "CANDIDATE_STAGING_FRONTIER_MISMATCH"):
            self.resolve(frontier=frontier)
        fixture = self.fixture.fixture
        predecessor = compile_executable_factory_release(
            self.current.curriculum, self.current.source_bindings, self.current.profile,
            fixture.registry, fixture.answers, source_root=None, graph=fixture.graph,
            verification_seed=37)
        with self.assertRaisesRegex(ValueError, "FACTORY_EXECUTABLE_RELEASE_PREDECESSOR_DRIFT"):
            self.resolve(current=predecessor)
        replacement = self.stage(verification_seed=38)
        with self.assertRaisesRegex(ValueError, "JIT_ADOPTION_PROPOSAL_CONTEXT_CHANGED"):
            self.resolve(staged=(replacement,))
        # Rejections do not invalidate the original immutable, current context.
        self.assertEqual(self.resolve(), self.staged)
        self.assertEqual(self.ledger.receipts, ())
        self.assertEqual(self.checkpoint.optimizer_step, 0)

    def test_unchanged_implementation_descriptors_pass_without_mutation(self):
        fixture = self.fixture.fixture
        before = self.staged.successor.manifest()
        verify_current_implementations(self.staged.successor,
                                       fixture.registry, fixture.answers)
        self.assertEqual(self.staged.successor.manifest(), before)

    def test_explicit_historical_source_provider_chains_pass_jit_verification(self):
        from bilqis_mlx.factory.live_answers import live_answer_registry
        from bilqis_mlx.runtime.tests.operator.pre_neural_journey_support import (
            historical_school_release,
        )
        from bilqis_mlx.source_adapters.school import live_source_registry

        release, _graph = historical_school_release()
        verify_current_implementations(
            release, live_source_registry(), live_answer_registry())

    def test_source_and_answer_drift_block_before_admission_transactions(self):
        from bilqis_mlx.runtime import release_adoption

        fixture = self.fixture.fixture
        successor = self.staged.successor
        binding = successor.source_bindings.bindings[0]
        source = fixture.registry.require(binding.generator_id, binding.oracle_id)
        answer = fixture.answers.require(successor.answer_modalities[0].kind)
        sources = SimpleNamespace(require=Mock(return_value=replace(
            source, descriptor=replace(source.descriptor, implementation_sha256="f" * 64))))
        answers = SimpleNamespace(require=Mock(return_value=replace(
            answer, descriptor=replace(answer.descriptor, implementation_sha256="f" * 64))))
        session = SimpleNamespace(resolve_ready_proposal=Mock(return_value=self.staged))
        receipt = {"school": {"fixture": "unchanged"}}
        before = deepcopy(receipt)
        for registry, modalities, expected in (
                (sources, fixture.answers, "JIT_ADOPTION_SOURCE_IMPLEMENTATION_DRIFT"),
                (fixture.registry, answers, "JIT_ADOPTION_ANSWER_IMPLEMENTATION_DRIFT")):
            with self.subTest(drift=expected), \
                    patch.object(release_adoption._runtime_admission,
                                 "_require_executable_factory_admission", return_value=self.current), \
                    patch.object(release_adoption._runtime_state, "_state_from_json",
                                 return_value=SimpleNamespace(current_student=self.checkpoint)), \
                    patch.object(release_adoption._source_adapters_school,
                                 "live_source_registry", return_value=registry), \
                    patch.object(release_adoption._factory_live_answers,
                                 "live_answer_registry", return_value=modalities), \
                    patch.object(release_adoption, "_adopt_catalog_profile") as catalog, \
                    patch.object(release_adoption, "_adopt_executable_profile") as profile:
                with self.assertRaisesRegex(ValueError, "^" + expected + "$" ):
                    release_adoption._adopt_jit_proposal(
                        None, Path("/unused"), receipt, None, None, fixture.graph,
                        None, None, session, self.proposal, reserve_gib=100.)
                catalog.assert_not_called()
                profile.assert_not_called()
                self.assertEqual(receipt, before)
