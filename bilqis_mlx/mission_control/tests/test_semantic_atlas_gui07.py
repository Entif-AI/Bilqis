"""GUI07 semantic authority, ABI address, and historical-state acceptance."""
from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace
import unittest

from bilqis_mlx.mission_control.model import (
    AuthorityClass, RunRef, ValueOrigin,
)
from bilqis_mlx.mission_control.query_catalog import MissionControlQueryCatalog
from bilqis_mlx.mission_control.query_contracts import (
    QueryFamily, QueryMode, QueryRequest, QueryState,
)
from bilqis_mlx.mission_control.semantic import (
    SemanticAdmissionState, SemanticConceptSnapshot, SemanticGenerationState,
    SemanticHeldMappingSnapshot, SemanticSimilaritySnapshot,
)
from bilqis_mlx.mission_control.semantic.projection import (
    SimilarityInput, concept_record_id, project_semantic_atlas_records,
    state_record_id,
)


ROOT = Path(__file__).resolve().parents[3]
RELEASE = "1" * 64
BUNDLE = "2" * 64
SOURCE_BUNDLE = "3" * 64
ROOT_ID = (
    "https://github.com/Entif-AI/Bilqis-MLX/id/root/"
    "NI-LEXICON-CURRICULUM/LEXROOT-007a2c39cfe74c"
)
SENSE_1 = ROOT_ID.replace("/id/root/", "/id/sense/") + "/STEM%201/BSC"
SENSE_2 = ROOT_ID.replace("/id/root/", "/id/sense/") + "/STEM%202/BSC"


def _label(value):
    return SimpleNamespace(role="definition", value=value, language="en")


def _source_row(key):
    return SimpleNamespace(domain="lexicon", table="lexicon_root_senses", key=key)


def _concept(semantic_id, kind, definition, index, *, relation_target=None):
    relation = (() if relation_target is None else
                (SimpleNamespace(predicate="skos:broader", target=relation_target),))
    source = _source_row("LEXROOT-007a2c39cfe74c" if kind == "root"
                         else "LEXSENSE-fixture")
    body = SimpleNamespace(
        semantic_id=semantic_id, kind=kind, types=("skos:Concept",),
        labels=(_label(definition),), realizations=(),
        source_loci=(SimpleNamespace(canonical="New Ithkuil Lexicon §4.3 p.179"),),
        relations=relation, source_rows=(source,),
    )
    return SimpleNamespace(
        concept=body, abi_index=index, abi_bank=0, abi_row=index,
        active=index < 2, implementation_status="ADMITTED",
        teaching_candidate=True, teaching_reason="SOURCE_ELIGIBLE",
    )


def _snapshot():
    concepts = (
        _concept(ROOT_ID, "root", "arrogance / haughtiness / insolence", 0),
        _concept(SENSE_1, "sense", "arrogant behavior", 1, relation_target=ROOT_ID),
        _concept(SENSE_2, "sense", "haughty behavior", 2, relation_target=ROOT_ID),
    )
    entries = tuple(SimpleNamespace(
        index=index, bank=0, row=index, semantic_id=item.concept.semantic_id,
        symbol=None, source="fixture", active=index < 2,
        teaching_candidate=True, reason="SOURCE_ELIGIBLE",
    ) for index, item in enumerate(concepts))
    held = (SimpleNamespace(
        domain="mapping", table="lexicon_mapping", key="ambiguous-1",
        semantic_id="semantic:held:ambiguous-1", source_disposition="SOURCE_HELD",
        implementation_status="IMPLEMENTATION_UNCOVERED", teaching_candidate=False,
        reason_code="AMBIGUOUS_MAPPING", teaching_reason="HOLD_FOR_REVIEW", owner="#55",
    ),)
    binding = SimpleNamespace(
        semantic_ids=(SENSE_1,), capability_ids=("D.COPULAR_IDENTITY",),
    )
    counts = SimpleNamespace(semantic_concepts=3, source_held=1)
    return SimpleNamespace(
        bundle_id=BUNDLE, release_sha256=RELEASE, source_bundle_id=SOURCE_BUNDLE,
        counts=counts, formal_domain_bindings=(binding,), concepts=concepts,
        abi_entries=entries, withheld_rows=held,
    )


def _run(generation: int) -> RunRef:
    return RunRef(
        "run-semantic", "4" * 64, generation, "5" * 64, "6" * 64,
        "7" * 64, RELEASE, "8" * 64,
    )


class Gui07SemanticAtlasTests(unittest.TestCase):
    def test_source_backed_root_and_two_senses_keep_exact_distinct_identity(self):
        path = ROOT / "lib/ithkuil/_data/csv/lexicon_root_senses.csv"
        with path.open(newline="", encoding="utf-8") as stream:
            rows = [row for row in csv.DictReader(stream)
                    if row["lexicon_root_id"] == "LEXROOT-007a2c39cfe74c"]
        self.assertTrue(any(row["stem"] == "STEM 1" for row in rows))
        self.assertTrue(any(row["stem"] == "STEM 2" for row in rows))
        self.assertNotEqual(ROOT_ID, SENSE_1)
        self.assertNotEqual(SENSE_1, SENSE_2)

        records = project_semantic_atlas_records(
            _snapshot(), _run(7), (0, 1), materialized_at=100,
            similarities=(SimilarityInput(
                SENSE_1, SENSE_2, "embedding:fixture", 0.97,
                ValueOrigin.DERIVED),),
            frame_schema_refs={SENSE_1: ("frame:copular/v1",)},
        )
        concepts = {item.semantic_id: item for item in records
                    if type(item) is SemanticConceptSnapshot}
        self.assertEqual(concepts[ROOT_ID].kind, "root")
        self.assertEqual(concepts[SENSE_1].kind, "sense")
        self.assertEqual(concepts[SENSE_2].kind, "sense")
        self.assertEqual(concepts[SENSE_1].relations[0].target_semantic_id, ROOT_ID)
        self.assertFalse(any(
            relation.target_semantic_id == SENSE_2
            for relation in concepts[SENSE_1].relations
        ))
        similarity = next(item for item in records
                          if type(item) is SemanticSimilaritySnapshot)
        self.assertEqual(similarity.target_semantic_id, SENSE_2)
        self.assertFalse(similarity.canonical_equivalence)
        self.assertIs(similarity.meta.authority, AuthorityClass.DERIVED)

    def test_exact_identity_and_bank_row_queries_resolve_same_semantic(self):
        run = _run(7)
        records = project_semantic_atlas_records(
            _snapshot(), run, (0, 1), materialized_at=100)
        catalog = MissionControlQueryCatalog(records)
        exact = catalog.query(QueryRequest(
            QueryFamily.SEMANTIC,
            record_id=concept_record_id(RELEASE, SENSE_1),
        ))
        self.assertEqual(exact.state, QueryState.PRESENT)
        concept = exact.records[0]
        self.assertEqual(concept.semantic_id, SENSE_1)
        self.assertEqual((concept.abi_bank, concept.abi_row), (0, 1))
        self.assertEqual(concept.source_loci, ("New Ithkuil Lexicon §4.3 p.179",))

        state = catalog.query(QueryRequest(
            QueryFamily.SEMANTIC,
            record_id=state_record_id(run, 0, 1),
        )).records[0]
        self.assertEqual(state.semantic_id, SENSE_1)
        self.assertEqual((state.abi_bank, state.abi_row), (0, 1))
        self.assertIs(state.admission_state, SemanticAdmissionState.ACTIVE)

        identity_links = catalog.query(QueryRequest(
            QueryFamily.REFERENCE, reference=SENSE_1, limit=32))
        self.assertIn(concept.meta.record_id, {
            link.target_record_id for link in identity_links.links
            if link.relation == "SEMANTIC_IDENTITY"
        })

    def test_held_reason_is_source_authoritative_and_has_no_fabricated_abi_row(self):
        records = project_semantic_atlas_records(
            _snapshot(), _run(7), (0, 1), materialized_at=100)
        held = next(item for item in records if type(item) is SemanticHeldMappingSnapshot)
        self.assertEqual(held.reason_code, "AMBIGUOUS_MAPPING")
        self.assertEqual(held.teaching_reason, "HOLD_FOR_REVIEW")
        self.assertIs(held.meta.authority, AuthorityClass.SOURCE_AUTHORITATIVE)
        self.assertFalse(hasattr(held, "abi_row"))

    def test_historical_generation_uses_its_active_set_not_current_state(self):
        source = _snapshot()
        current = project_semantic_atlas_records(
            source, _run(7), (0, 1), materialized_at=100,
            newly_admitted_indices=(1,), recently_exercised_indices=(1,))
        historical = project_semantic_atlas_records(
            source, _run(6), (0,), materialized_at=90, as_of=80)
        records = tuple(item for item in current if item.meta.run is None) + tuple(
            item for item in (*historical, *current) if item.meta.run is not None)
        catalog = MissionControlQueryCatalog(records)

        current_page = catalog.query(QueryRequest(
            QueryFamily.SEMANTIC,
            schema_version=SemanticGenerationState.SCHEMA,
            limit=32,
        ))
        current_states = {item.semantic_id: item for item in current_page.records}
        self.assertIs(current_states[SENSE_1].admission_state,
                      SemanticAdmissionState.ACTIVE)
        self.assertTrue(current_states[SENSE_1].recently_exercised)

        old_page = catalog.query(QueryRequest(
            QueryFamily.SEMANTIC, mode=QueryMode.HISTORICAL,
            run_id="run-semantic", generation=6,
            schema_version=SemanticGenerationState.SCHEMA, limit=32,
        ))
        old_states = {item.semantic_id: item for item in old_page.records}
        self.assertIs(old_states[SENSE_1].admission_state,
                      SemanticAdmissionState.RESERVED_MASKED)
        self.assertFalse(old_states[SENSE_1].recently_exercised)

    def test_similarity_contract_cannot_be_promoted_to_canonical_equivalence(self):
        item = next(item for item in project_semantic_atlas_records(
            _snapshot(), _run(7), (0, 1), materialized_at=100,
            similarities=(SimilarityInput(SENSE_1, SENSE_2, "embedding:x", 0.9),),
        ) if type(item) is SemanticSimilaritySnapshot)
        with self.assertRaises(ValueError):
            SemanticSimilaritySnapshot(
                item.meta, item.source_semantic_id, item.target_semantic_id,
                item.basis_ref, item.similarity, True,
            )

    def test_similarity_contract_rejects_source_authority_and_out_of_range_score(self):
        item = next(item for item in project_semantic_atlas_records(
            _snapshot(), _run(7), (0, 1), materialized_at=100,
            similarities=(SimilarityInput(SENSE_1, SENSE_2, "embedding:x", 0.9),),
        ) if type(item) is SemanticSimilaritySnapshot)
        with self.assertRaises(ValueError):
            SemanticSimilaritySnapshot(
                item.meta.__class__(
                    **{**item.meta.__dict__, "authority": AuthorityClass.SOURCE_AUTHORITATIVE}
                ),
                item.source_semantic_id, item.target_semantic_id,
                item.basis_ref, item.similarity, False,
            )
        with self.assertRaises(ValueError):
            SemanticSimilaritySnapshot(
                item.meta, item.source_semantic_id, item.target_semantic_id,
                item.basis_ref,
                item.similarity.__class__(
                    item.similarity.state, item.similarity.origin, 1.01,
                    item.similarity.units,
                ),
                False,
            )


if __name__ == "__main__":
    unittest.main()
