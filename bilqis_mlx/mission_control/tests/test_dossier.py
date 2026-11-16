"""Exact, bounded capability dossier facts remain portable and historical."""
from dataclasses import replace
import importlib
import unittest

from bilqis_mlx.mission_control import (
    MissionControlQueryCatalog, QueryFamily, QueryMode, QueryRequest,
    canonical_json, decode_json,
)
from bilqis_mlx.mission_control.contracts.dossier import (
    CapabilityDossier, DossierEntry, DossierValue,
)
from bilqis_mlx.mission_control.tests.samples import meta, value


def dossier(generation=7):
    metadata = meta(f"dossier:{generation}")
    metadata = replace(metadata, run=replace(metadata.run, generation=generation))
    entry = DossierEntry("fresh", "performance", "fresh", "Fresh cohort", generation,
                         118, (DossierValue("correct", value(generation)),),
                         ("evidence:a",), None, None)
    return CapabilityDossier(metadata, "B.EXAMPLE", "Example", value(generation),
                             value(8), value(12), value(1), value("stable"),
                             value("eligible"), value("qualified"), value("held"),
                             (entry,))


class DossierTests(unittest.TestCase):
    def test_old_deep_import_is_same_module_and_class(self):
        for name in ("model", "codec", "snapshots", "events", "schema"):
            self.assertIs(importlib.import_module(f"bilqis_mlx.mission_control.{name}"),
                          importlib.import_module(f"bilqis_mlx.mission_control.contracts.{name}"))

    def test_roundtrip_and_exact_historical_queries(self):
        item = dossier()
        self.assertEqual(decode_json(canonical_json(item)), item)
        catalog = MissionControlQueryCatalog((dossier(6), item))
        page = catalog.query(QueryRequest(QueryFamily.CAPABILITY, QueryMode.HISTORICAL,
                                         run_id="run-7", generation=6,
                                         schema_version=CapabilityDossier.SCHEMA))
        self.assertEqual([row.now.value for row in page.records], [6])
        self.assertEqual(catalog.query(QueryRequest(QueryFamily.CAPABILITY,
                         QueryMode.HISTORICAL, generation=99)).state.value, "MISSING")
        refs = catalog.query(QueryRequest(QueryFamily.REFERENCE, run_id="run-7",
                                         generation=7, reference="evidence:a"))
        self.assertEqual(refs.links[0].source_record_id, "dossier:7")

    def test_invalid_entry_identity_and_unindexed_evidence_fail(self):
        item = dossier()
        entry = item.entries[0]
        for entries in ((entry, entry), (replace(entry, generation=8),),
                        (replace(entry, refs=("not-indexed",)),),
                        ):
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                replace(item, entries=entries)

        for changes in (dict(related_kind="capability"), dict(values=entry.values * 2)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(entry, **changes)

    def test_unicode_row_size_uses_cp03_ascii_escaping(self):
        item = dossier()
        entry = item.entries[0]
        values = tuple(DossierValue(f"v{i}", value("漢" * 500)) for i in range(16))
        with self.assertRaisesRegex(ValueError, "DOSSIER_ROW_TOO_LARGE"):
            replace(item, entries=(replace(entry, values=values),))
