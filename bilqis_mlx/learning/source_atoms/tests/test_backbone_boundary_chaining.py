"""B11 producer consumes only the immediate selected-state boundary."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
import bilqis_mlx.learning.source_atoms.backbone as backbone
import bilqis_mlx.learning.source_atoms.backbone_producer_session as producer_session


class _Session:
    def __init__(self, completed):
        self.results = [object() for _ in range(completed)]
        self.next_inputs = []

    def advance(self, *, next_input=None):
        self.next_inputs.append(next_input)
        result = SimpleNamespace(execution_digest="fixture-execution", hidden=object())
        self.results.append(result)
        return result


class BoundaryChainingTests(unittest.TestCase):
    def producer(self, completed=2):
        producer = object.__new__(backbone._SourceBackboneProducerSession)
        producer._session = _Session(completed)
        producer._depth_inputs = ()
        producer._receipts = ()
        producer._receipt_refs = ()
        producer._receipt_seals = ()
        producer._result_refs = ()
        producer._result_seals = ()
        producer._parameters = {"fixture": object()}
        producer._topology = object()
        producer._compiled = SimpleNamespace(extents=object())
        return producer

    def test_stale_boundary_fails_before_depth_selection_or_execution(self):
        producer = self.producer(completed=2)
        stale_features = SimpleNamespace(boundary_group=1)
        stale_view = SimpleNamespace(boundary_group=1)
        with patch.object(producer_session, "depth_select") as select:
            with self.assertRaises(BilqisError):
                producer.advance(stale_features, stale_view)
        select.assert_not_called()
        self.assertEqual(producer._session.next_inputs, [])
        self.assertEqual(producer._depth_inputs, ())

    def test_exact_next_boundary_preserves_selected_input_and_receipt_order(self):
        producer = self.producer(completed=2)
        features = SimpleNamespace(boundary_group=2)
        view = SimpleNamespace(boundary_group=2)
        selected = object()
        adapter_parameters = object()
        adapted = object()
        receipt = SimpleNamespace(
            receipt_digest="fixture-receipt", output_digest="fixture-output")
        with (patch.object(producer_session, "depth_select", return_value=selected) as select,
              patch.object(producer_session, "adapter_parameter_view",
                           return_value=adapter_parameters) as parameter_view,
              patch.object(producer_session, "adapter_forward", return_value=adapted) as adapt,
              patch.object(producer_session, "_content_digest", return_value="fixture-hidden"),
              patch.object(producer_session, "_issue_from_producer", return_value=receipt)):
            actual = producer.advance(features, view)
        select.assert_called_once_with(producer, features, view)
        parameter_view.assert_called_once_with(
            producer._parameters, spec=producer._topology,
            extents=producer._compiled.extents, group_index=1)
        adapt.assert_called_once_with(selected, adapter_parameters)
        self.assertIs(actual, receipt)
        self.assertEqual(producer._session.next_inputs, [adapted])
        self.assertEqual(producer._depth_inputs, ((features, view),))
        self.assertEqual(producer._receipts, (receipt,))

    def test_trace_three_group_horizon_never_mints_forensic_receipts(self):
        producer = self.producer(completed=0)
        producer._trace = True
        producer._trace_boundaries = (object(),)
        producer._motif_manifest = None
        producer._execution_binding = object()
        producer._generation = "generation"
        first_view = SimpleNamespace(boundary_group=1)
        second_view = SimpleNamespace(boundary_group=2)
        selected = object()
        adapted = object()
        with (patch.object(producer_session, "source_depth_select", return_value=selected),
              patch.object(producer_session, "adapter_parameter_view", return_value=object()),
              patch.object(producer_session, "adapter_forward", return_value=adapted),
              patch.object(producer_session, "_content_digest",
                           side_effect=AssertionError("content digest entered trace")),
              patch.object(producer_session, "_issue_from_producer",
                           side_effect=AssertionError("receipt replay entered trace"))):
            producer.advance()
            producer.advance(depth_parameters=first_view)
            producer.advance(depth_parameters=second_view)
        self.assertEqual(len(producer._session.results), 3)
        self.assertEqual(len(producer._session.next_inputs), 3)
        self.assertEqual(producer._session.next_inputs, [None, adapted, adapted])
        self.assertEqual(len(producer._trace_boundaries), 4)
        self.assertEqual(producer._receipts, ())


if __name__ == "__main__":
    unittest.main()
