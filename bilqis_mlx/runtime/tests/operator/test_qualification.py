"""Qualification preparation owns identity and authority, not teacher decisions."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch, Mock
from types import SimpleNamespace

from bilqis_mlx.runtime import qualification_manifest as contract
from bilqis_mlx.runtime.model_topology import ModelTopologySpec
from bilqis_mlx.runtime.state import _fingerprint, _seed
from bilqis_mlx.runtime.tests.operator.session.qualification_runtime_mixin import (
    QualificationRuntimeMixin,
)


class QualificationTests(QualificationRuntimeMixin, unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        from bilqis_mlx.factory.tests.test_executable_release import ExecutableFactoryReleaseTests
        fixture = ExecutableFactoryReleaseTests()
        fixture.setUp()
        self.release = fixture.compile()
        self.graph = fixture.graph
        self.manifest = {
            'schema': contract.SCHEMA, 'implementation': {'head': 'head', 'files': {}, 'components': {}},
            'release': self.write_object('release.json', self.release.manifest()),
            'graph': self.write_object('graph.json', self.graph),
            'workload': contract.workload(self.release, self.graph),
            'arms': [{'id': name, 'topology': ModelTopologySpec(layers, 2, 12, 24, 96).to_record(),
                'initialization_origin': 'fresh-model', 'initialization_seed': 42,
                'run_dir': str(self.root/name)} for name, layers in (('base', 1), ('larger', 2))],
            'initialization_seed': 42, 'training_seed': 73, 'numeric_maximum': 7,
            'optimizer': {}, 'policy': {'value': {'retention': True}},
            'budget': {'minutes': 1, 'max_visits': 2, 'steps_per_visit': 2,
                       'batch_size': 6, 'attempted_step_ceiling': 4},
            'observation_capture': True, 'neural_authority': False,
            'evaluation': {'post_acquisition_seeds': [11, 13, 17]}, 'external_files': []}
        self.manifest['policy']['sha256'] = _fingerprint(self.manifest['policy']['value'])
        self.manifest['budget_sha256'] = _fingerprint(self.manifest['budget'])
        self.manifest['numeric_scope_sha256'] = _fingerprint(7)
        self.save(self.manifest)

    def write_object(self, name, value):
        (self.root/name).write_text(json.dumps(value))
        return {'file': name, 'sha256': _fingerprint(value)}

    def save(self, value):
        value['digest'] = _fingerprint({k: v for k, v in value.items() if k != 'digest'})
        (self.root/'manifest.json').write_text(json.dumps(value))

    def validate(self, expected=None):
        with patch.object(contract.subprocess, 'check_output', return_value='head'), \
                patch.object(contract, 'implementation_files', return_value={}), \
                patch('bilqis_mlx.runtime.jit_adoption.verify_current_implementations'):
            return contract.validate(self.root/'manifest.json', 'base', implementation_root=self.root,
                                     expected_digest=expected or self.manifest['digest'])

    def test_preflight_parses_without_neural_import_or_filesystem_mutation(self):
        before = {str(p): p.read_bytes() for p in self.root.iterdir()}
        prepared = self.validate()
        self.assertEqual(prepared.arm['topology'], self.manifest['arms'][0]['topology'])
        self.assertEqual({str(p): p.read_bytes() for p in self.root.iterdir()}, before)
        self.assertFalse((self.root/'base').exists())

    def test_portable_runtime_import_does_not_require_mlx(self):
        code = r'''
import importlib.abc
import sys

class BlockMlx(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "mlx" or fullname.startswith("mlx."):
            raise ModuleNotFoundError("blocked portable MLX import", name=fullname)
        return None

sys.meta_path.insert(0, BlockMlx())
from bilqis_mlx.runtime import checkpoints
from bilqis_mlx.runtime.atlas_resources import inspect_distributed_backends
assert checkpoints is not None
assert all(not item.available for item in inspect_distributed_backends())
'''
        result = subprocess.run(
            [sys.executable, '-c', code],
            cwd=Path(__file__).resolve().parents[4],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_each_identity_mutation_fails_before_initialization(self):
        for name, change in (
            ('head', lambda m: m['implementation'].update(head='other')),
            ('topology', lambda m: m['arms'][0]['topology'].update(width=24)),
            ('workload', lambda m: m['workload'].update(curriculum_sha256='other')),
            ('numeric', lambda m: m.update(numeric_maximum=8)),
            ('policy', lambda m: m['policy']['value'].update(retention=False)),
            ('budget', lambda m: m['budget'].update(max_visits=3)),
            ('authority', lambda m: m.update(neural_authority=True)),
            ('capture', lambda m: m.update(observation_capture=False)),
        ):
            with self.subTest(name=name):
                altered = deepcopy(self.manifest)
                change(altered)
                self.save(altered)
                with patch.object(contract.QualificationPreparation, 'initial_model', side_effect=AssertionError('NEURAL_ALLOCATION_FORBIDDEN')):
                    with self.assertRaises(ValueError):
                        self.validate()
                    with self.assertRaises(ValueError):
                        self.validate(expected=altered["digest"])
        self.save(self.manifest)

    def test_existing_run_and_corrupt_sidecar_fail_closed(self):
        (self.root/'base').mkdir()
        with self.assertRaises(ValueError) as caught:
            self.validate()
        self.assertEqual(caught.exception.context['detail'], 'FRESH_RUN_REQUIRED')
        (self.root/'base').rmdir()
        (self.root/'graph.json').write_text('{}')
        with self.assertRaises(ValueError) as caught:
            self.validate()

        self.assertEqual(caught.exception.context['detail'], 'ARTIFACT_DIGEST')

    def test_training_seed_is_shared_without_reusing_run_identity(self):
        left = {'run_id': 'base', 'generation': 4, 'qualification_training_seed': 73}
        right = {**left, 'run_id': 'larger'}
        self.assertEqual(_seed(left, capability='Z.C0'), _seed(right, capability='Z.C0'))
        self.assertNotEqual(_seed({'run_id': 'base', 'generation': 4}, capability='Z.C0'),
                            _seed({'run_id': 'larger', 'generation': 4}, capability='Z.C0'))

    def test_qualified_initialization_never_uses_historical_weights(self):
        prepared = self.validate()
        try:
            import mlx.core as mx
        except ImportError:
            self.skipTest('MLX unavailable')
        with patch('bilqis_mlx.learning.student_ops._initial_model', side_effect=AssertionError('HISTORICAL_MODEL_FORBIDDEN')):
            parameters, optimizer, _, graph, _, topology, origin = prepared.initial_model()
        self.assertEqual(topology.to_record(), prepared.arm['topology'])
        self.assertEqual(int(optimizer.state['step'].item()), 0)
        self.assertEqual(graph, self.graph)
        self.assertEqual(origin, {'origin': 'fresh-model', 'seed': 42})

    def test_launch_defaults_to_no_neural_authority_and_dry_run_wins(self):
        from bilqis_mlx.runtime.qualification import execute
        prepared = self.validate()
        for human, dry in ((False, False), (False, True), (True, True)):
            with self.subTest(human=human, dry=dry), \
                    patch('bilqis_mlx.runtime.qualification.preflight', return_value=prepared), \
                    patch.dict('sys.modules', {'bilqis_mlx.runtime.operating_loop':
                        SimpleNamespace(operate=Mock(side_effect=AssertionError('NEURAL_RUN_FORBIDDEN')))}):
                report = execute(None, 'base', prepared.manifest['digest'], root=self.root,
                                 human_run=human, dry_run=dry)
                self.assertEqual(report['actual_optimizer_updates'], 0)
                self.assertFalse(report['neural_authority'])

    def test_current_proficiency_and_post_sweeps_keep_exact_threshold(self):
        from bilqis_mlx.runtime.qualification_results import meets_criterion, specimen_key
        criterion = {'numerator': 9, 'denominator': 10}
        score = {'Z.C0': {'correct': 9, 'total': 10}}
        self.assertFalse(meets_criterion(score, ['Z.C0'], criterion, acquisition=True))
        self.assertTrue(meets_criterion(score, ['Z.C0'], criterion))
        self.assertFalse(meets_criterion(score, ['Z.C0', 'Z.C1'], criterion))
        one = {'id': 'seed-one', 'capability': 'Z.C0', 'tokens': [1, 2], 'gold': 'TRUE'}
        self.assertEqual(specimen_key(one), specimen_key({**one, 'id': 'seed-two'}))

    def test_frozen_release_does_not_advance_numeric_scope(self):
        from bilqis_mlx.runtime.release_adoption import _advance_numeric_profile
        args = (None, {'qualification': {'release_sha256': self.release.release_sha256},
                       'numeric_scope_final_maximum': 10}, None, None, self.graph,
                None, self.release, None)
        with patch('bilqis_mlx.profiles.catalog.next_numeric_scope_profile', side_effect=AssertionError('GROWTH_FORBIDDEN')):
            result = _advance_numeric_profile(*args, numeric_staircase=True)
        self.assertEqual(result[2], self.release)

    def test_numeric_scope_bounds_are_four_through_ten(self):
        from bilqis_mlx.profiles.catalog import numeric_scope_bounds
        self.assertEqual(numeric_scope_bounds(), (4, 10))

    def test_wide_unscoped_c_entry_is_migration_signature_but_completed_ten_is_not(self):
        from types import SimpleNamespace
        from bilqis_mlx.runtime.release_adoption import _wide_numeric_entry_rebind_due
        release = SimpleNamespace(
            profile=SimpleNamespace(profile_id="school/example/numeric-0-10"))
        broken = {"numeric_maximum": 10, "numeric_scope_final_maximum": None}
        completed = {"numeric_maximum": 10, "numeric_scope_final_maximum": 10}

        self.assertTrue(_wide_numeric_entry_rebind_due(
            broken, release, final_maximum=10))
        self.assertFalse(_wide_numeric_entry_rebind_due(
            completed, release, final_maximum=10))
