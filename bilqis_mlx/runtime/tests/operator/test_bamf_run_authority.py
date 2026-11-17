"""R17 native operator authority ordering witnesses."""
from contextlib import nullcontext
from types import SimpleNamespace
import unittest

from bilqis_mlx.runtime.bamf_operator._session_visit import visit


class BamfRunAuthorityOrderingTests(unittest.TestCase):
    def test_accepted_publication_rechecks_authority_immediately_before_publish(self):
        events = []
        binding = SimpleNamespace(
            assert_current=lambda: events.append("authority"))
        successor = SimpleNamespace(
            extents=SimpleNamespace(factor_map_digest="f" * 64))
        prepared = SimpleNamespace(
            status="READY",
            parent=object(),
            selection=object(),
            step=SimpleNamespace(
                transaction=SimpleNamespace(training_authorities=("training",))),
            decision=SimpleNamespace(accepted=True),
            retained=object(),
            successor=successor,
        )

        def publish(*_args, **_kwargs):
            events.append("publish")

        result = visit(
            "/run", 0.0, steps_per_visit=1, progress=None,
            source_prefetch_workers=0, source_prefetch_executor=None,
            source_prefetch_metrics=None, observer=None,
            run_authority_binding=binding,
            prepare_visit=lambda *_args, **_kwargs: prepared,
            record_rejection=lambda *_args, **_kwargs: None,
            accept_publish=publish, load_generation=lambda *_args: None,
            measure_phase=lambda *_args, **_kwargs: nullcontext(),
            emit_progress=lambda *_args: None,
        )
        self.assertEqual(result, "ACCEPTED")
        self.assertEqual(events, ["authority", "publish"])


if __name__ == "__main__":
    unittest.main()
