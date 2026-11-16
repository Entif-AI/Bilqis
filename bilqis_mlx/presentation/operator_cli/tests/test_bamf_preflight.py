"""BAMF CLI preflight failures remain read-only and neural-inert."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from bilqis_mlx.cli import main, parse_args
from bilqis_mlx.presentation.operator_cli.command import _bamf_or_topology
from bilqis_mlx.runtime.model_topology import ModelTopologySpec
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactIdentity
from bilqis_mlx.semantics.atlas_projection import ATLAS_MANIFEST_SCHEMA, _canonical_bytes

ROOT = Path(__file__).resolve().parents[4]
TOPOLOGY = ROOT / 'configs/models/bamf-0.2.json'


class BamfPreflightTests(unittest.TestCase):
    def invoke(self, extra):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(['train', '--dry-run', '--model-topology', str(TOPOLOGY), *extra])
        return code, output.getvalue(), errors.getvalue()

    def test_actual_v2_dry_run_requires_explicit_foundation_inputs_without_creating_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / 'new'
            code, output, errors = self.invoke([
                '--run-dir', str(run), '--source-prefetch-workers', '0'])
            self.assertEqual((code, output), (2, ''))
            self.assertIn('BAMF_OPERATOR_FOUNDATION_IDENTITY_REQUIRED', errors)
            self.assertFalse(run.exists())

    def test_historical_v1_topology_does_not_claim_bamf_v2_ownership(self):
        with tempfile.TemporaryDirectory() as tmp:
            topology = ModelTopologySpec(1, 2, 12, 24, 96)
            topology_path = Path(tmp) / 'historical-v1-topology.json'
            topology_path.write_text(json.dumps(topology.to_record()), encoding='utf-8')
            for resume in (False, True):
                argv = [
                    'train', '--dry-run', '--model-topology', str(topology_path),
                    '--run-dir', str(Path(tmp) / 'historical-run'),
                ]
                if resume:
                    argv.append('--resume')
                with self.subTest(resume=resume):
                    handled, result, loaded = _bamf_or_topology(parse_args(argv))
                    self.assertFalse(handled)
                    self.assertIsNone(result)
                    self.assertEqual(loaded, topology)

    def test_fresh_v2_conflicting_topology_rejects_before_source_or_run_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / 'manifest.json'
            manifest.write_text('{}')
            forged = ModelTopologySpecV2()
            object.__setattr__(forged, 'layers', forged.layers + 1)
            with patch('bilqis_mlx.runtime.topology_lifecycle.topology_from_file',
                       return_value=forged):
                code, output, errors = self.invoke([
                    '--run-dir', str(root / 'new'), '--atlas-release-manifest', str(manifest),
                    '--run-id', 'new-run', '--run-seed', '5', '--learning-rate', '0.001',
                    '--adam-beta1', '0.9', '--adam-beta2', '0.95', '--adam-eps', '1e-8',
                    '--weight-decay', '0.1'])
            self.assertEqual((code, output), (2, ''))
            self.assertIn('BAMF_OPERATOR_CREATE_TOPOLOGY_CONFLICT', errors)
            self.assertEqual(sorted(path.name for path in root.iterdir()), ['manifest.json'])

    def test_unqualified_manifest_is_rejected_without_becoming_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / 'manifest.json'
            raw = b'{"unqualified-source-reference":true}\n'
            manifest.write_bytes(raw)
            before = manifest.stat()
            code, output, errors = self.invoke([
                '--run-dir', str(root / 'new'), '--atlas-release-manifest', str(manifest),
                '--run-id', 'dry-run', '--run-seed', '7',
                '--learning-rate', '0.001', '--adam-beta1', '0.9',
                '--adam-beta2', '0.95', '--adam-eps', '1e-8', '--weight-decay', '0.1'])
            self.assertEqual((code, output), (2, ''))
            self.assertIn('BAMF_OPERATOR_ATLAS_MANIFEST_INVALID', errors)
            self.assertEqual(manifest.read_bytes(), raw)
            self.assertEqual(manifest.stat().st_mtime_ns, before.st_mtime_ns)
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['manifest.json'])

    def test_canonical_but_unpinned_manifest_cannot_mint_source_qualification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / 'manifest.json'
            manifest.write_bytes(_canonical_bytes({
                'schema': ATLAS_MANIFEST_SCHEMA,
                'release_sha256': '0' * 64,
            }))
            code, output, errors = self.invoke([
                '--run-dir', str(root / 'new'), '--atlas-release-manifest', str(manifest),
                '--run-id', 'source-pin-test', '--run-seed', '7',
                '--learning-rate', '0.001', '--adam-beta1', '0.9',
                '--adam-beta2', '0.95', '--adam-eps', '1e-8', '--weight-decay', '0.1'])
            self.assertEqual((code, output), (2, ''))
            self.assertIn('BAMF_OPERATOR_ATLAS_MANIFEST_NOT_SOURCE_PINNED', errors)
            self.assertFalse((root / 'new').exists())

    def test_missing_or_policy_conflicting_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for extra in (['--admission-policy', 'atlas-release'],
                          ['--atlas-release-manifest', str(Path(tmp) / 'missing')]):
                with self.subTest(extra=extra):
                    code, output, errors = self.invoke(['--run-dir', tmp, *extra])
                    self.assertEqual(code, 2)
                    self.assertEqual(output, '')
                    self.assertIn('BLOCKED', errors)

    def test_saved_v1_is_never_coerced_to_v2_or_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state.json'
            state.write_bytes(b'protected-v1-lineage-not-for-this-reader')
            before = state.stat()
            with patch('bilqis_mlx.presentation.operator_cli.command._invoke_learner',
                       side_effect=AssertionError('no optimizer')):
                code, _, errors = self.invoke(['--run-dir', tmp, '--resume'])
            self.assertEqual(code, 2)
            self.assertIn('BLOCKED', errors)
            self.assertEqual(state.read_bytes(), b'protected-v1-lineage-not-for-this-reader')
            self.assertEqual(state.stat().st_mtime_ns, before.st_mtime_ns)
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['state.json'])

    def test_symlink_manifest_is_rejected_without_reading_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / 'target.json'
            target.write_bytes(b'private-reference')
            manifest = root / 'manifest.json'
            manifest.symlink_to(target)
            before = target.stat()
            code, output, errors = self.invoke(['--run-dir', str(root / 'new'),
                '--admission-policy', 'atlas-release', '--atlas-release-manifest', str(manifest)])
            self.assertEqual((code, output), (2, ''))
            self.assertIn('BLOCKED', errors)
            self.assertEqual(target.stat().st_mtime_ns, before.st_mtime_ns)
            self.assertFalse((root / 'new').exists())

    def test_resume_pointer_is_not_read_or_changed_by_held_inspection(self):
        with tempfile.TemporaryDirectory() as tmp:
            pointer = Path(tmp) / 'bamf-state.json'
            pointer.write_bytes(b'not-yet-qualified-by-B13')
            before = pointer.stat()
            code, output, errors = self.invoke(['--run-dir', tmp, '--resume'])
            self.assertEqual((code, output), (2, ''))
            self.assertIn('BLOCKED', errors)
            self.assertEqual(pointer.read_bytes(), b'not-yet-qualified-by-B13')
            self.assertEqual(pointer.stat().st_mtime_ns, before.st_mtime_ns)
            code, output, errors = self.invoke(['--run-dir', tmp])
            self.assertEqual((code, output), (2, ''))
            self.assertIn('BLOCKED', errors)

    def test_parser_keeps_human_and_prefetch_controls(self):
        args = parse_args(['train', '--dry-run', '--human-run', '--source-prefetch-workers', '1',
                          '--atlas-release-manifest', '/manifest.json'])
        self.assertTrue(args.human_run)
        self.assertEqual(args.source_prefetch_workers, 1)
        self.assertEqual(args.atlas_release_manifest, Path('/manifest.json'))
        explicit = parse_args(['train', '--admission-policy', 'staged'])
        equals = parse_args(['train', '--admission-policy=staged'])
        omitted = parse_args(['train'])
        self.assertEqual((explicit.admission_policy, equals.admission_policy,
                          omitted.admission_policy), ('staged', 'staged', 'staged'))
        self.assertTrue(explicit.admission_policy_explicit)
        self.assertTrue(equals.admission_policy_explicit)
        self.assertFalse(omitted.admission_policy_explicit)

    def test_parser_tracks_v2_foundation_presence_across_argparse_spellings(self):
        cases = (
            ['--run-id', 'x'], ['--run-id=x'], ['--run-i', 'x'],
            ['--run-seed', '0'], ['--run-seed=0'], ['--run-s', '0'],
            ['--learning-rate', '0.1'], ['--learning-rate=0.1'], ['--learning-r', '0.1'],
            ['--adam-beta1', '0.8'], ['--adam-beta1=0.8'],
            ['--adam-beta2', '0.9'], ['--adam-beta2=0.9'],
            ['--adam-eps', '1e-8'], ['--adam-eps=1e-8'], ['--adam-e', '1e-8'],
            ['--weight-decay', '0.01'], ['--weight-decay=0.01'], ['--weight-d', '0.01'],
        )
        for spelling in cases:
            with self.subTest(spelling=spelling):
                self.assertTrue(parse_args(['train', *spelling]).bamf_v2_foundation_explicit)
        self.assertFalse(parse_args(['train']).bamf_v2_foundation_explicit)

    def test_parser_accepts_explicit_source_run_for_fresh_bamf(self):
        args = parse_args(['train', '--source-run-dir', '/accepted/source-run'])
        self.assertEqual(args.source_run_dir, Path('/accepted/source-run'))

    def test_fresh_external_target_does_not_fall_through_to_legacy_trainer(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / 'aspirant'
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                code = main(['train', '--human-run', '--run-dir', str(run)])
            self.assertEqual((code, output.getvalue()), (2, ''))
            self.assertIn('BAMF_OPERATOR_FRESH_EXTERNAL_RUN_REQUIRES_FOUNDATION_INPUTS',
                          errors.getvalue())
            self.assertNotIn('LEARNING_EXPERIMENT_REQUIRES_ISOLATED_WORKTREE_RUN',
                             errors.getvalue())
            self.assertFalse(run.exists())

    def test_fresh_v2_optimizer_completeness_precedes_missing_topology(self):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(['train', '--dry-run', '--run-id', 'x', '--run-seed', '0',
                         '--learning-rate', '0.001'])
        self.assertEqual((code, output.getvalue()), (2, ''))
        self.assertIn('BAMF_OPERATOR_FOUNDATION_OPTIMIZER_INCOMPLETE', errors.getvalue())
        self.assertNotIn('BAMF_OPERATOR_V2_TOPOLOGY_REQUIRED', errors.getvalue())

    def test_mutating_atlas_release_requires_human_before_request_compatibility(self):
        request = SimpleNamespace(
            requested_run_id='wrong-run', requested_run_seed=999,
            requested_topology_digest='0' * 64,
            source_approval=SimpleNamespace(atlas_release_sha256='1' * 64),
        )
        identity = AtlasArtifactIdentity('2' * 64, '3' * 64, '4' * 64)
        output, errors = io.StringIO(), io.StringIO()
        with patch(
                'bilqis_mlx.presentation.operator_cli.bamf_lifecycle.atlas_manifest_identity',
                return_value=identity), patch(
                'bilqis_mlx.runtime.atlas_admission.read_atlas_enrollment_request_v2',
                return_value=request), redirect_stdout(output), redirect_stderr(errors):
            code = main([
                'train', '--model-topology', str(TOPOLOGY), '--run-id', 'x',
                '--run-seed', '0', '--learning-rate', '0.001', '--adam-beta1', '0.9',
                '--adam-beta2', '0.95', '--adam-eps', '1e-8', '--weight-decay', '0.1',
                '--atlas-release-manifest', '/synthetic-manifest.json',
                '--admission-policy', 'atlas-release', '--atlas-admission-scope',
                '/synthetic-request.json',
            ])
        self.assertEqual((code, output.getvalue()), (2, ''))
        self.assertIn('BAMF_ATLAS_V2_EXPLICIT_HUMAN_REQUEST_REQUIRED', errors.getvalue())
        self.assertNotIn('BAMF_OPERATOR_ATLAS_REQUEST_RUN_ID_CONFLICT', errors.getvalue())

    def test_train_help_preserves_operator_descriptions_after_parser_factoring(self):
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as stopped:
            parse_args(['train', '--help'])
        self.assertEqual(stopped.exception.code, 0)
        help_text = ' '.join(output.getvalue().split()).replace('- ', '-')
        for text in (
            'PROVISIONAL max new wrong answers on any protected capability',
            ('Explicit operator confirmation for mutating CLI actions; this is not '
             'authentication. BAMF create and enrollment remain neural-inert, while '
             'an accepted BAMF --resume may enter the persistent BAMF-native learner.'),
            'Accepted source learner used to derive a fresh BAMF foundation.',
            'autonomously measure, teach, and remeasure factory evidence',
            'Optional complete visit cap',
            'low-overhead nanosecond timing markers',
            'Pure host-side lesson prep workers',
            'Defer expensive assessments while training',
            'stagnation quarantine actuator',
            'one-time next-grade admission',
            'Global weakest-three recovery',
        ):
            self.assertIn(text, help_text)

    def test_lease_scope_or_missing_resume_pointer_stays_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            scope = Path(tmp) / 'scope.json'
            scope.write_bytes(b'not-authority-for-configuration-inspection')
            for extra in (['--atlas-admission-scope', str(scope)], ['--resume']):
                with self.subTest(extra=extra):
                    code, output, errors = self.invoke(['--run-dir', str(Path(tmp) / 'new'), *extra])
                    self.assertEqual((code, output), (2, ''))
                    self.assertIn('BLOCKED', errors)
                    self.assertFalse((Path(tmp) / 'new').exists())
            self.assertEqual(scope.read_bytes(), b'not-authority-for-configuration-inspection')

    def test_atlas_release_requires_an_existing_regular_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            for manifest in (Path(tmp), Path(tmp) / 'absent.json'):
                with self.subTest(manifest=manifest):
                    code, output, errors = self.invoke(['--run-dir', str(Path(tmp) / 'new'),
                        '--admission-policy', 'atlas-release', '--atlas-release-manifest', str(manifest)])
                    self.assertEqual((code, output), (2, ''))
                    self.assertIn('BLOCKED', errors)
                    self.assertFalse((Path(tmp) / 'new').exists())

    def test_manifest_is_not_accepted_by_legacy_or_live_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'manifest.json'
            manifest.write_bytes(b'opaque reference')
            for selection in (['--dry-run'], [], ['--model-topology', str(TOPOLOGY), '--human-run']):
                with self.subTest(selection=selection), \
                        patch('bilqis_mlx.presentation.operator_cli.command._invoke_learner',
                              side_effect=AssertionError('no learner for held manifest')):
                    output, errors = io.StringIO(), io.StringIO()
                    with redirect_stdout(output), redirect_stderr(errors):
                        code = main(['train', '--run-dir', str(Path(tmp) / 'new'),
                            '--atlas-release-manifest', str(manifest), *selection])
                    self.assertEqual((code, output.getvalue()), (2, ''))
                    self.assertIn('BLOCKED', errors.getvalue())
                    self.assertFalse((Path(tmp) / 'new').exists())

    def test_fresh_process_can_inspect_without_mlx_or_run_writes(self):
        script = '''
import importlib.abc,sys
class NoMlx(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'mlx' or fullname.startswith('mlx.'):
            raise ModuleNotFoundError('no MLX during configuration inspection')
        return None
sys.meta_path.insert(0,NoMlx())
sys.path.insert(0,sys.argv[1])
from bilqis_mlx.cli import main
raise SystemExit(main(['train','--dry-run','--model-topology',sys.argv[2],'--run-dir',sys.argv[3]]))
'''
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipts = root / 'existing-receipts'
            receipts.mkdir()
            (receipts / 'receipt.json').write_bytes(b'preserved receipt\x00\xff')
            (root / 'lineage.bin').write_bytes(b'protected unrelated lineage')
            def snapshot():
                return tuple((str(p.relative_to(root)), p.is_dir(), p.stat().st_mtime_ns,
                              None if p.is_dir() else p.read_bytes())
                             for p in (root, *sorted(root.rglob('*'))))
            before = snapshot()
            result = subprocess.run([sys.executable, '-I', '-B', '-c', script,
                str(ROOT), str(TOPOLOGY), str(Path(tmp) / 'new')],
                text=True, capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertIn('BAMF_OPERATOR_FOUNDATION_IDENTITY_REQUIRED', result.stderr)
            self.assertEqual(snapshot(), before)
            self.assertFalse((root / 'new').exists())
