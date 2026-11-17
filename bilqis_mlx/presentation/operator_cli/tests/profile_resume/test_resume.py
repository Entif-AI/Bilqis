"""R19 exact compiled-profile requests reach the native resume owner."""
from contextlib import redirect_stdout, redirect_stderr
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.cli import main
from bilqis_mlx.runtime.bamf_operator import BamfOperatorResult


class ProfileResumeTests(unittest.TestCase):
    def invoke(self, *arguments):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(['train', *arguments])
        return code, output.getvalue(), errors.getvalue()

    def test_human_resume_forwards_exact_profile_artifact(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'bamf-state.json').write_text('{}')
            artifact = root / 'successor.json'
            artifact.write_text('{}')
            with patch('bilqis_mlx.runtime.run_authority.bind_native_run_authority'), patch('bilqis_mlx.presentation.operator_cli.bamf_lifecycle._resume_runtime_context',
                       return_value=({'result': 'READY_TO_RESUME'}, None)), patch(
                    'bilqis_mlx.runtime._release_adoption.native_profile.preview_profile_release',
                    return_value={'profile_id': 'fixture/Z/v2'}) as preview, patch(
                    'bilqis_mlx.runtime.bamf_operator.operate_bamf',
                    return_value=BamfOperatorResult('VISIT_LIMIT', 1, 1, 0, 1, 0)) as operate:
                code, _, errors = self.invoke('--human-run', '--resume', '--run-dir', str(root),
                                             '--factory-profile-release', str(artifact))
            self.assertEqual((code, errors), (0, ''))
            self.assertEqual(operate.call_args.kwargs['profile_release'], artifact)
            preview.assert_called_once_with(root, artifact)

    def test_dry_run_previews_without_native_operator_or_publication(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'bamf-state.json').write_text('{}')
            artifact = root / 'successor.json'
            with patch('bilqis_mlx.runtime.run_authority.bind_native_run_authority'), patch('bilqis_mlx.presentation.operator_cli.bamf_lifecycle._resume_runtime_context',
                       return_value=({'result': 'READY_TO_RESUME'}, None)), patch(
                    'bilqis_mlx.runtime._release_adoption.native_profile.preview_profile_release',
                    return_value={'profile_id': 'fixture/Z/v2'}) as preview, patch(
                    'bilqis_mlx.runtime.bamf_operator.operate_bamf') as operate:
                code, output, errors = self.invoke('--dry-run', '--resume', '--run-dir', str(root),
                                                  '--factory-profile-release', str(artifact))
            self.assertEqual((code, errors), (0, ''))
            self.assertIn('fixture/Z/v2', output)
            preview.assert_called_once_with(root, artifact)
            operate.assert_not_called()

    def test_profile_option_rejects_fresh_and_legacy_fallthrough(self):
        for resume in ([], ['--resume']):
            with self.subTest(resume=resume), TemporaryDirectory() as directory:
                code, output, errors = self.invoke(*resume, '--dry-run', '--run-dir', directory,
                                                  '--factory-profile-release', '/successor.json')
                self.assertEqual((code, output), (2, ''))
                self.assertIn('BAMF_PROFILE_NATIVE_RESUME_REQUIRED', errors)
