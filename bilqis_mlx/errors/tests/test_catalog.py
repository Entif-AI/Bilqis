"""The public error catalog preserves exact wire and recovery contracts."""
from dataclasses import asdict
import hashlib
import json
import pickle
import unittest

from bilqis_mlx.errors import CATALOG, ErrorBus, SCHOOL, SOURCE
from bilqis_mlx.errors.catalog import BY_CODE, BY_LEGACY_CODE


class CatalogTests(unittest.TestCase):
    def test_frozen_catalog_order_and_complete_contracts(self):
        payload = json.dumps([asdict(spec) for spec in CATALOG[:123]],
                             sort_keys=True, separators=(",", ":"))
        self.assertEqual(len(CATALOG), 146)
        self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(),
                         "753528902fed2b4d2ddd844ad07e8494b2dc7746f2dcc61f8cd4fd39a0b704cc")
        self.assertEqual(len(BY_CODE), 146)
        self.assertIs(BY_CODE["SCHOOL.STATE.COURSE_DIGEST_MISMATCH"],
                      SCHOOL.STATE.COURSE_DIGEST_MISMATCH)
        self.assertIs(CATALOG[132], SCHOOL.BAMF_PACKAGE.INVALID)
        self.assertEqual(
            BY_CODE["SCHOOL.BAMF_FIRST_STUDENT.INVALID"].owner,
            "runtime.bamf_first_student")
        self.assertEqual(
            BY_CODE["SCHOOL.BAMF_DELIVERY.INVALID"].owner,
            "runtime.delivery")
        for spec in CATALOG:
            for alias in spec.legacy_codes:
                self.assertIn(spec, BY_LEGACY_CODE[alias])

    def test_nested_namespaces_keep_historical_pickle_paths(self):
        for namespace in (SCHOOL, SCHOOL.STATE, SCHOOL.BAMF_AKASHA,
                          SOURCE, SOURCE.BOOLEAN):
            with self.subTest(namespace=namespace):
                self.assertEqual(namespace.__module__, "bilqis_mlx.errors.catalog")
                self.assertIs(pickle.loads(pickle.dumps(namespace)), namespace)

    def test_source_failure_still_has_recoverable_operator_contract(self):
        report = ErrorBus.explain("SOURCE.BOOLEAN.UNKNOWN_OPERATOR")[0]
        self.assertEqual(report.owner, "live_grade_b")
        self.assertTrue(report.preserve_state)
        self.assertFalse(report.legacy_untyped)
