import json
from contextlib import nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch


@patch("bilqis_mlx.runtime.bamf_operator.session._training_memory_context", nullcontext)
class SessionPublicationObservationTests(unittest.TestCase):
    def test_operator_publishes_terminal_only_after_publication(self):
        from bilqis_mlx.runtime.bamf_bundle.publication.instrumentation import PublicationMetrics
        from bilqis_mlx.runtime.bamf_operator.session import operate_bamf
        with TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / 'bamf-state.json').write_text(json.dumps({'run_id': 'run', 'manifest_sha256': 'a' * 64}))
            prepared = NS(status='ACCEPTED', parent=object(), selection=object(),
                          step=NS(transaction=NS(training_authorities=())), decision=NS(accepted=True),
                          retained=object(), capability='cap', successor=NS(extents=NS(factor_map_digest='x')))
            snapshots = []
            def publish(*args, **kwargs):
                snapshots.append(json.loads((path / 'trainer-observed.json').read_text())['visits'][-1])
                kwargs['publication_observer'](PublicationMetrics(1, 2, 3, 4, 5))
            prefix = 'bilqis_mlx.runtime.bamf_operator.session.'
            with patch(
                    prefix + 'prepare_bamf_visit', return_value=prepared), patch(
                    prefix + 'accept_and_publish', side_effect=publish), patch(
                    prefix + 'load_accepted_generation', return_value=NS(generation=1, retained_state=NS(optimizer_step=1))):
                operate_bamf(path, minutes=1, max_visits=1, reserve_gib=0)
            final = json.loads((path / 'trainer-observed.json').read_text())['visits'][-1]
            self.assertEqual((snapshots[0]['phase'], snapshots[0]['outcome']), ('PUBLISHING', 'RUNNING'))
            self.assertEqual((final['phase'], final['outcome']), ('COMPLETED', 'ACCEPTED'))
            self.assertEqual(final['publication_parent_bundle_loads'], 1)
            self.assertEqual(final['publication_child_bundle_loads'], 2)
            self.assertEqual(final['publication_tensor_bytes_read'], 3)
            self.assertEqual(final['publication_write_bytes'], 4)
            self.assertEqual(final['publication_fsync_bytes'], 5)


if __name__ == '__main__':
    unittest.main()
