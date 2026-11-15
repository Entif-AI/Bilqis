"""Literal CP03 queries cover every required Admin Main Frame read family."""
from dataclasses import replace
import unittest

from bilqis_mlx.mission_control.codec import canonical_json, encode_record
from bilqis_mlx.mission_control.envelopes import PartialEnvelope
from bilqis_mlx.mission_control.model import CoverageState
from bilqis_mlx.mission_control.query_contracts import (
    QueryFamily, QueryRequest, QueryState,
)
from bilqis_mlx.mission_control.query_catalog import MissionControlQueryCatalog
from bilqis_mlx.mission_control.operator import OperatorActionReceipt
from bilqis_mlx.mission_control.observability import MemorySnapshot
from bilqis_mlx.mission_control.tests.samples import SAMPLES
from bilqis_mlx.presentation.atlas_metrics import bamf_status


_FAMILIES = (
    QueryFamily.RECORD,
    QueryFamily.RUN,
    QueryFamily.SCHOOL,
    QueryFamily.CAPABILITY,
    QueryFamily.EPISODE,
    QueryFamily.GENERATION,
    QueryFamily.SEMANTIC,
    QueryFamily.FRAME,
    QueryFamily.NEURAL,
    QueryFamily.MEMORY,
    QueryFamily.TEACHER,
    QueryFamily.SALIENCE,
    QueryFamily.CORRECTION,
    QueryFamily.RESOURCE,
)


class MissionControlQueryFamilyTests(unittest.TestCase):
    def setUp(self):
        self.domain_records = SAMPLES[:16]
        self.index = MissionControlQueryCatalog(self.domain_records)

    def test_literal_fixture_queries_cover_every_required_family(self):
        for family in _FAMILIES:
            with self.subTest(family=family.value):
                page = self.index.query(QueryRequest(family))
                self.assertEqual(page.state, QueryState.PRESENT)
                self.assertGreaterEqual(page.total_matches, 1)
                self.assertTrue(page.records)

        self.assertEqual(
            {type(item).__name__ for item in self.index.query(
                QueryRequest(QueryFamily.SCHOOL)).records},
            {"SchoolSnapshot", "CurriculumFrontier"},
        )
        self.assertEqual(
            {type(item).__name__ for item in self.index.query(
                QueryRequest(QueryFamily.EPISODE)).records},
            {"LearningEpisode", "CandidateDecision"},
        )

    def test_current_operator_view_is_the_same_cp02_truth_used_by_status(self):
        page = self.index.query(QueryRequest(QueryFamily.RUN))
        operator = next(
            item for item in page.records
            if item.schema_version.endswith("operator-view/v1"))
        self.assertEqual(bamf_status(encode_record(operator)), operator)

    def test_querying_records_is_byte_stable_and_non_mutating(self):
        before = tuple(canonical_json(item) for item in self.domain_records)
        for family in _FAMILIES:
            self.index.query(QueryRequest(family))
        after = tuple(canonical_json(item) for item in self.domain_records)
        self.assertEqual(after, before)

    def test_capability_episode_evidence_and_generation_receipt_links_resolve(self):
        capability = self.index.query(QueryRequest(
            QueryFamily.LINKS, record_id="capability"))
        episode = next(link for link in capability.links if link.relation == "EPISODE")
        self.assertEqual(episode.target_record_id, "episode")

        episode_links = self.index.query(QueryRequest(
            QueryFamily.LINKS, record_id=episode.target_record_id))
        self.assertIn(
            "evidence:a",
            {link.target_ref for link in episode_links.links
             if link.relation == "EVIDENCE"},
        )

        generation = self.index.query(QueryRequest(
            QueryFamily.LINKS, record_id="generation"))
        checkpoint = next(
            link for link in generation.links if link.relation == "CHECKPOINT")
        expected_checkpoint = "checkpoint:" + SAMPLES[14].checkpoint_sha256
        self.assertEqual(checkpoint.target_ref, expected_checkpoint)
        self.assertEqual(checkpoint.target_record_id, expected_checkpoint)
        checkpoint_links = self.index.query(QueryRequest(
            QueryFamily.LINKS, record_id=checkpoint.target_record_id))
        self.assertIn(
            "receipt:a",
            {link.target_ref for link in checkpoint_links.links
             if link.relation == "RECEIPT"},
        )

    def test_reference_lookup_returns_exact_stable_link_sources(self):
        page = self.index.query(QueryRequest(
            QueryFamily.REFERENCE, reference="evidence:a", limit=32))
        self.assertEqual(page.state, QueryState.PRESENT)
        self.assertGreater(page.total_matches, 1)
        self.assertTrue(all(link.target_ref == "evidence:a" for link in page.links))
        receipt_page = self.index.query(QueryRequest(
            QueryFamily.REFERENCE, reference="receipt:a", limit=32))
        self.assertEqual(receipt_page.state, QueryState.PRESENT)
        self.assertTrue(all(
            link.target_ref == "receipt:a" for link in receipt_page.links))

    def test_forensic_record_family_finds_command_receipt_by_operation_identity(self):
        receipt = next(item for item in SAMPLES if type(item) is OperatorActionReceipt)
        page = MissionControlQueryCatalog(SAMPLES).query(QueryRequest(
            QueryFamily.RECORD, reference=receipt.operation_id, limit=32))
        self.assertEqual(page.state, QueryState.PRESENT)
        self.assertEqual(page.records, (receipt,))

    def test_forensic_record_family_preserves_conflicting_evidence_rows(self):
        candidate = SAMPLES[6]
        conflicting = replace(
            candidate,
            meta=replace(candidate.meta, record_id="decision:conflicting"),
            candidate_id="candidate-conflicting",
        )
        page = MissionControlQueryCatalog((*SAMPLES, conflicting)).query(QueryRequest(
            QueryFamily.RECORD, reference=candidate.capability_id, limit=32))
        candidate_ids = {
            item.candidate_id for item in page.records if hasattr(item, "candidate_id")
        }
        self.assertEqual(candidate_ids, {candidate.candidate_id, "candidate-conflicting"})

    def test_forensic_memory_identity_search_uses_admitted_provenance_refs(self):
        memory = next(item for item in SAMPLES if type(item) is MemorySnapshot)
        bound = replace(
            memory,
            meta=replace(
                memory.meta,
                evidence_refs=("motif:bool-composition", "allocation-slot:42"),
            ),
        )
        catalog = MissionControlQueryCatalog((bound,))
        motif = catalog.query(QueryRequest(
            QueryFamily.RECORD, reference="motif:bool-composition"))
        slot = catalog.query(QueryRequest(
            QueryFamily.RECORD, reference="allocation-slot:42"))
        self.assertEqual(motif.records, (bound,))
        self.assertEqual(slot.records, (bound,))

    def test_reference_query_keeps_degradation_on_its_actual_source_chain(self):
        source = replace(
            SAMPLES[1],
            meta=replace(
                SAMPLES[1].meta,
                record_id="operator:reference-partial",
                receipt_refs=("receipt:wanted",),
            ),
        )
        partial = PartialEnvelope(
            replace(
                source.meta, record_id="partial:reference-source",
                coverage=CoverageState.PARTIAL,
            ),
            source.meta.record_id,
            ("stage",),
        )
        page = MissionControlQueryCatalog((source, partial)).query(QueryRequest(
            QueryFamily.REFERENCE, reference="receipt:wanted"))
        self.assertEqual(page.state, QueryState.PARTIAL)
        self.assertEqual(page.markers, (partial,))

    def test_index_rejects_duplicate_record_identity(self):
        with self.assertRaises(ValueError):
            MissionControlQueryCatalog((*self.domain_records, replace(
                self.domain_records[0], meta=self.domain_records[0].meta)))


if __name__ == "__main__":
    unittest.main()
