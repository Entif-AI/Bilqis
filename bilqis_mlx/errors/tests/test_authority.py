"""Authority failures retain owner-specific recovery instead of topology advice."""
import unittest

from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL
from bilqis_mlx.errors.catalog import BY_CODE


class AuthorityCatalogTests(unittest.TestCase):
    def test_authority_contracts_are_registered_and_preserve_state(self):
        for namespace, members in (
            ('BAMF_CURRICULUM', ('INVALID', 'NOT_ADMITTED', 'NOT_TEACHABLE',
                                 'PREREQUISITE_HELD', 'SOURCE_HELD')),
            ('BAMF_RETENTION', ('BASELINE_ABSENT', 'COMPARABLE_REGRESSION')),
            ('BAMF_B11', ('SOURCE_EXECUTION_AUTHORITY_INVALID',)),
            ('BAMF_ADMISSION', ('LEASE_REQUIRED', 'WAITING_FOR_EVIDENCE',
                                'HELD', 'IMPLEMENTATION_UNCOVERED', 'FIXED_POINT')),
        ):
            for member in members:
                with self.subTest(namespace=namespace, member=member):
                    spec = getattr(getattr(SCHOOL, namespace), member)
                    self.assertIs(BY_CODE[spec.code], spec)
                    report = ErrorBus.report(BilqisError(spec, {'reason': 'exact owner reason'}))
                    self.assertIn('exact owner reason', report.summary)
                    self.assertTrue(report.preserve_state)
                    self.assertNotIn('head count', report.next_action)
                    self.assertFalse(report.legacy_untyped)

    def test_true_topology_keeps_structural_recovery(self):
        report = ErrorBus.report(BilqisError(SCHOOL.MODEL_TOPOLOGY.INVALID))
        self.assertIn('width divisible by head count', report.next_action)
