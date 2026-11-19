from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.swarm_contributions import DurableReplayStore
from bilqis_mlx.runtime.tests.swarm_contributions.fixtures import manifest, receipt


class DurableReplayStoreTests(unittest.TestCase):
    def test_claim_survives_new_store_instance_and_replay_rejects(self):
        work = manifest()
        result = receipt(work)
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "replay"
            first = DurableReplayStore(root)
            ledger = first.claim(work.replay_id, work.digest, result.digest)
            self.assertEqual(ledger.consumed_replay_ids, (work.replay_id,))

            recovered = DurableReplayStore(root)
            self.assertEqual(
                recovered.snapshot().consumed_replay_ids, (work.replay_id,))
            with self.assertRaises(BilqisError):
                recovered.claim(work.replay_id, work.digest, result.digest)

    def test_tampered_claim_fails_closed(self):
        work = manifest()
        result = receipt(work)
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "replay"
            store = DurableReplayStore(root)
            store.claim(work.replay_id, work.digest, result.digest)
            claim = next(root.glob("*.json"))
            claim.write_text('{"schema":"broken"}\n')
            with self.assertRaises(BilqisError):
                DurableReplayStore(root).snapshot()


if __name__ == "__main__":
    unittest.main()
