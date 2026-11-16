"""Real A01/A05/C02/B13 inputs carry signed fixture labels into B11."""
from contextlib import contextmanager
from dataclasses import replace
import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_salience import derive_salience, verify_salience_inputs
from bilqis_mlx.learning.salience_contracts import AuthoritySnapshot, Metric
from bilqis_mlx.learning.tests.test_atlas_salience import _CONTEXT, _policy, _fact, _signed
from bilqis_mlx.runtime.atlas_revalidation import SourceAuthorityRegistry
from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.bamf_bundle import (
    issue_initial_foundation_feature_authority, prepare_initial_generation,
    publish_initial_generation,
)
from bilqis_mlx.runtime.bamf_bundle.genesis.foundation import initial_foundation_sidecars
from bilqis_mlx.runtime.bamf_bundle.genesis.preparation_authority import _factory_generation_provenance
from bilqis_mlx.runtime.model_topology_v2 import b01_generation_authority, b01_generation_extents
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.runtime.factory_candidate_training import (
    FactoryDeliveryObservation,
)
from bilqis_mlx.runtime.salience_auxiliaries import RowSalienceBinding
from bilqis_mlx.runtime.salience_training import SalienceLabelRequest
from bilqis_mlx.runtime.teacher_observation_capture import ObservationCapture, store_sidecar
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.tests.capability.factory.retention.factory_retention_live_support import (
    HP, live_factory_context,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    provision_source_authority_registry,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import issue_factory_authority
from bilqis_mlx.runtime.tests.model.test_salience_auxiliaries import _REGISTRY as SALIENCE_REGISTRY
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY
from bilqis_mlx.semantics.atlas.feature_io import persist_feature_manifest
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.runtime.priority_source_offer import prepare_priority_source_offer
from bilqis_mlx.runtime.accepted_priority_visit import execute_accepted_priority_candidate
from bilqis_mlx.runtime.tests.model.salience.priority_witness_support import planning, select
from bilqis_mlx.runtime.tests.model.salience.retained_closure_witness import assert_non_authorizing_closure_witness

BILQIS_LEAF_GATE_POLICY = 'DETACHED_ONLY'


REGISTRY = SourceAuthorityRegistry(tuple(sorted((*AUTHORITY.keys, *SALIENCE_REGISTRY.keys),
                                              key=lambda key: key.owner_id)))


@contextmanager
def stage(name):
    started = time.monotonic()
    print(f'C06_STAGE {name} started', flush=True)
    try:
        yield
    finally:
        print(f'C06_STAGE {name} elapsed_seconds={time.monotonic() - started:.3f}', flush=True)


class FactorySalienceExecutionTests(unittest.TestCase):
    def setUp(self):
        artifact = os.environ.get('BILQIS_A01_ATLAS_BUNDLE')
        if not artifact or not Path(artifact).is_dir():
            self.skipTest('BILQIS_A01_ATLAS_BUNDLE fixture is not mounted')
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        environment = patch.dict(os.environ, {'BILQIS_DATA_PLANE': str(self.root / 'plane.sqlite3')})
        environment.start()
        self.addCleanup(environment.stop)
        with stage('source_setup'):
            self.artifact = Path(artifact)
            selection = AtlasArtifactSelection(
                str(self.artifact),
                '5f8fba20ecc0adebf39c3b663fdffa4f766e780915197f09d116713042a479e7',
                '58e0c281b5da18b9b7e6c803709b29eeeb0a88f16b06f48de692808e2fb88306',
                'f1c89c1d1bcd72695c81f8e777d0fbbdf446e92cb27132bebf1cd6873ec689ec')
            self.context, _ = live_factory_context(
                Path.cwd(), (Path.cwd() / 'vendor/legacy-v16').resolve())
            self.features = issue_initial_foundation_feature_authority(selection)
            self.feature_receipt = persist_feature_manifest(self.features.features, self.root / 'features')

    def accepted_source_context(self, run_dir):
        from bilqis_mlx.runtime import admission as factory_admission
        release_file = factory_admission._persist_executable_factory_release(
            run_dir, self.context.release)
        receipt = {'factory_release_sha256': self.context.release.release_sha256,
                   'factory_release_file': release_file}
        return AcceptedRuntimeHost(run_dir).source_context(
            receipt, graph=self.context.graph, source_root=self.context.source_root)

    def _provider(self, prepared):
        batch = prepared.training_batch
        row = batch.rows[0]
        context = replace(_CONTEXT, semantic_release=batch.release_sha256,
            generation_digest=batch.generation_binding,
            capability_id=row.provenance.capability_id,
            source_family_id=row.provenance.source_family_id,
            source_binding_digest=contract_digest(self.context.release.source_bindings.by_capability[
                row.provenance.capability_id]))
        snapshot = AuthoritySnapshot((context,), 100, REGISTRY)
        policy = _signed(replace(_policy(), semantic_release=batch.release_sha256,
                                 source_family_ids=(context.source_family_id,)))
        evidence = derive_salience(verify_salience_inputs((
            _fact(Metric.DECLARED_IMPACT, 2, policy, context=context),
            _fact(Metric.BLOCKED_COUNT, 0, policy, context=context),
        ), policy, snapshot, context))
        binding = _signed(RowSalienceBinding.for_row(batch, row, evidence,
            source_owner='fixture:salience-owner', signature_hex='0' * 128))
        return SalienceLabelRequest(((binding, evidence),), snapshot, lambda *args: False)

    def _bootstrap(self, run_dir):
        provision_source_authority_registry(run_dir, REGISTRY)
        with stage('bootstrap_prepare'):
            origin = Checkpoint('7' * 64, 'bundles/foundation-origin', 0, True)
            factory = issue_factory_authority(self.context.release, self.context.graph, origin)
            features = self.features
            semantic, compiler, *_ = initial_foundation_sidecars(
                factory.release, factory.admission, self.context.graph, run_seed=379,
                feature_authority=features)
            provenance = _factory_generation_provenance(factory.release, features)
            motif = MotifManifest(provenance.release_digest)
            extents = b01_generation_extents(
                semantic_abi=semantic, compiler_features=compiler, motif_page_count=1,
                motif_key_map_digest=motif.digest)
            prepared = prepare_initial_generation(
                run_id='c06-salience-disposable', run_seed=379, graph=self.context.graph,
                factory_authority=factory, foundation_features=features,
                model_authority=b01_generation_authority(extents),
                optimizer_hyperparameters=HP, provenance=provenance,
                delivery_events=({'event': 'FIXTURE_GENESIS', 'optimizer_step': 0},))
        with stage('bootstrap_publish'):
            publish_initial_generation(run_dir, prepared, reserve_gib=0.)
        return factory, self.accepted_source_context(run_dir), load_accepted_generation(run_dir)

    def _select_priority(self, run_dir, context, parent, factory, capability, seed):
        with stage('priority_offer'):
            offer = prepare_priority_source_offer(
                context, parent, str(self.artifact),
                capability=capability, source_seed=seed, source_each=1)
        with stage('a09_planning'):
            plan = planning(self.features.selection, factory, run_dir)
        from bilqis_mlx.runtime import accepted_priority_visit as priority_owner
        with stage('priority_selection'), patch.object(
                priority_owner, 'select_visit_policy',
                wraps=priority_owner.select_visit_policy) as policy_call:
            selection = select(run_dir, context, parent, offer, plan, REGISTRY)
        self.assertEqual(selection.status, 'TEACHER_SELECTED')
        self.assertEqual(selection.option_id, 'c06-teaching')
        self.assertIs(selection.offer, offer)
        self.assertEqual(selection.visit.identity.capability_id, capability)
        self.assertEqual(
            selection.visit.identity.accepted_manifest_sha256,
            offer.accepted_manifest_sha256)
        self.assertEqual(policy_call.call_count, 1)
        policy = selection.policy
        self.assertGreater(policy['lr'], 0)
        selection.policy['lr'] = 99
        self.assertEqual(selection.policy, policy)
        return priority_owner, selection, policy, offer.rows()

    def _execute_candidate(
            self, priority_owner, run_dir, context, parent, selection, policy, rows, seed):
        capture = ObservationCapture(run_dir, {})
        capture.attempt_id = 'c06-salience-disposable'
        capture.proposal_id = store_sidecar(
            run_dir, {'attempt_id': capture.attempt_id})['sha256']
        capture.select_option(selection.visit.identity.capability_id, None)
        with stage('candidate_step'), patch.object(
                priority_owner, 'execute_factory_candidate_step',
                wraps=priority_owner.execute_factory_candidate_step) as step_call, patch(
                    'bilqis_mlx.runtime.lawful_teaching_frontier.'
                    'require_bound_lawful_teaching_frontier',
                    return_value=selection._lawful_frontier):
            result = execute_accepted_priority_candidate(
                selection, context, str(self.artifact), self.feature_receipt.path,
                teacher_hparams=HP, optimizer_step_seed=379, max_norm=1.0,
                observation=FactoryDeliveryObservation(capture, 1, rows, seed),
                salience_provider=self._provider, capture_diagnostics=True)
        self._assert_candidate_result(
            step_call, result, selection, policy, rows, seed, parent, run_dir)
        return result

    def _assert_candidate_result(
            self, step_call, result, selection, policy, rows, seed, parent, run_dir):
        self.assertEqual(step_call.call_count, 1)
        arguments, keywords = step_call.call_args
        self.assertEqual(arguments[5], rows)
        self.assertEqual(keywords['teacher_strategy'], policy)
        self.assertEqual(keywords['source_seed'], seed)
        self.assertEqual(
            keywords['teacher_hparams'], replace(HP, learning_rate=float(policy['lr'])))
        self.assertEqual(
            keywords['visit_provenance'].visit_id, selection.visit.identity.visit_id)
        self.assertEqual(
            result.prepared.training_batch.rows[0].provenance.visit.visit_id,
            selection.visit.identity.visit_id)
        self.assertIsNotNone(result.diagnostics)
        gradient = result.diagnostics.gradient_execution
        loss = gradient.execution.loss
        self.assertGreater(float(loss.impact), 0.)
        self.assertGreater(float(loss.exigency), 0.)
        self.assertEqual(float(loss.novelty), 0.)
        for name in ('impact', 'exigency'):
            value = gradient.gradients['readout.salience_bias.' + name]
            self.assertGreater(float(mx.abs(value).sum()), 0.)
        novelty = gradient.gradients['readout.salience_bias.novelty']
        self.assertEqual(float(mx.abs(novelty).sum()), 0.)
        census = gradient.execution.dense_parameter_names
        self.assertIn('readout.salience.impact', census)
        self.assertNotIn('readout.salience.novelty', census)
        self.assertEqual(result.transaction.update_steps, 1)
        self.assertEqual(parent.retained_state.optimizer_step, 0)
        self.assertEqual(load_accepted_generation(run_dir).generation, parent.generation)

    def test_real_factory_step_uses_present_heads_and_preserves_missing_head(self):
        capability, seed = 'B.IDBOOLOPS', 37901
        with TemporaryDirectory() as run_value, patch(
                'bilqis_mlx.runtime.bamf_bundle.source_authority_custody.'
                'read_host_system_source_authority_registry', return_value=REGISTRY):
            run_dir = Path(run_value)
            factory, context, parent = self._bootstrap(run_dir)
            priority_owner, selection, policy, rows = self._select_priority(
                run_dir, context, parent, factory, capability, seed)
            result = self._execute_candidate(
                priority_owner, run_dir, context, parent, selection, policy, rows, seed)
            with stage('retained_closure'):
                assert_non_authorizing_closure_witness(self, run_dir, parent, result)
