"""Ephemeral CP03 bounded query catalog over authoritative CP02 records."""
from __future__ import annotations

from collections.abc import Iterable

from .contracts.envelopes import (
    PartialEnvelope, StaleEnvelope, UnavailableEnvelope,
)
from .contracts.events import LearningEpisode
from .contracts.model import WireRecord, require
from .contracts.observability import GenerationManifest
from .query_contracts import (
    QueryFamily, QueryLink, QueryMode, QueryPage, QueryRequest,
)
from .contracts.snapshots import (
    CapabilitySnapshot, OperatorView,
)
from .semantic import (
    SemanticConceptSnapshot, SemanticGenerationState, SemanticHeldMappingSnapshot,
    SemanticSimilaritySnapshot,
)
from .query_support import (
    FAMILY_TYPES, build_page, encode_query_page, matches_identity,
    record_sort_key, select_current,
)


class MissionControlQueryCatalog:
    """Read-only catalog; input records remain truth and CP06 owns persistence."""

    def __init__(self, records: Iterable[WireRecord], *, available: bool = True):
        copied = tuple(records)
        require(all(isinstance(item, WireRecord) for item in copied), "QUERY_RECORD")
        require(type(available) is bool, "QUERY_AVAILABILITY")
        ids = tuple(item.meta.record_id for item in copied)
        require(len(ids) == len(set(ids)), "QUERY_RECORD_ID_DUPLICATE")
        self._records = tuple(sorted(copied, key=record_sort_key))
        self.available = available
        self._by_id = {item.meta.record_id: item for item in self._records}

    @classmethod
    def unavailable(cls) -> "MissionControlQueryCatalog":
        return cls((), available=False)

    def _base_records(self, request: QueryRequest) -> tuple[WireRecord, ...]:
        record_types = FAMILY_TYPES.get(request.family)
        require(record_types is not None, "QUERY_FAMILY_RECORDS")
        rows = [
            item for item in self._records
            if type(item) in record_types and matches_identity(item, request)
        ]
        if request.mode is QueryMode.CURRENT and request.record_id is None:
            rows = select_current(rows)
        return tuple(sorted(rows, key=record_sort_key))

    def _markers(self, records, request: QueryRequest) -> tuple[WireRecord, ...]:
        record_ids = {item.meta.record_id for item in records}
        resources = {
            request.family.value,
            request.record_id,
            request.reference,
            None if request.run_id is None else f"{request.family.value}:{request.run_id}",
        }
        markers = [
            item for item in self._records
            if ((type(item) is PartialEnvelope and item.partial_record_id in record_ids)
                or (type(item) is StaleEnvelope and item.stale_record_id in record_ids))
                or (type(item) is UnavailableEnvelope and item.resource in resources
                    and (item.meta.run is None
                         or matches_identity(item, request, match_record_id=False)))
        ]
        if not records and request.as_of is not None:
            markers.extend(
                item for item in self._records
                if type(item) is StaleEnvelope
                and item.requested_as_of == request.as_of
                and item.stale_record_id in self._by_id
                and type(self._by_id[item.stale_record_id])
                in FAMILY_TYPES.get(request.family, ())
            )
        return tuple(sorted(markers, key=record_sort_key))

    def _links_for(self, record: WireRecord) -> tuple[QueryLink, ...]:
        links = []
        meta = record.meta
        for relation, refs in (
            ("SOURCE", meta.source_refs),
            ("EVIDENCE", meta.evidence_refs),
            ("RECEIPT", meta.receipt_refs),
        ):
            links.extend(QueryLink(
                relation, meta.record_id, ref,
                ref if ref in self._by_id else None,
            ) for ref in refs)
        if type(record) is OperatorView:
            links.extend(QueryLink(
                "RELATED_RECORD", meta.record_id, ref,
                ref if ref in self._by_id else None,
            ) for ref in record.related_record_ids)
        if type(record) is SemanticConceptSnapshot:
            links.append(QueryLink(
                "SEMANTIC_IDENTITY", meta.record_id, record.semantic_id,
                meta.record_id,
            ))
            links.extend(QueryLink(
                "CANONICAL_RELATION", meta.record_id, relation.target_semantic_id,
                None,
            ) for relation in record.relations)
            links.extend(QueryLink(
                "FRAME_SCHEMA", meta.record_id, ref, None,
            ) for ref in record.frame_schema_refs)
            links.extend(QueryLink(
                "CAPABILITY", meta.record_id, ref, None,
            ) for ref in record.capability_ids)
        if type(record) is SemanticGenerationState:
            links.append(QueryLink(
                "SEMANTIC_IDENTITY", meta.record_id, record.semantic_id,
                record.concept_record_id,
            ))
            if record.concept_record_id is not None:
                links.append(QueryLink(
                    "CANONICAL_CONCEPT", meta.record_id, record.concept_record_id,
                    record.concept_record_id if record.concept_record_id in self._by_id else None,
                ))
        if type(record) is SemanticHeldMappingSnapshot and record.semantic_id is not None:
            links.append(QueryLink(
                "HELD_SEMANTIC_IDENTITY", meta.record_id, record.semantic_id,
                meta.record_id,
            ))
        if type(record) is SemanticSimilaritySnapshot:
            links.extend((
                QueryLink("LEARNED_SIMILARITY_SOURCE", meta.record_id,
                          record.source_semantic_id, meta.record_id),
                QueryLink("LEARNED_SIMILARITY_TARGET", meta.record_id,
                          record.target_semantic_id, meta.record_id),
            ))
        if type(record) is CapabilitySnapshot and meta.run is not None:
            for item in self._records:
                if (type(item) is LearningEpisode and item.meta.run == meta.run
                        and item.capability_id == record.capability_id):
                    links.append(QueryLink(
                        "EPISODE", meta.record_id, item.meta.record_id,
                        item.meta.record_id))
        if type(record) is GenerationManifest:
            checkpoint_ref = f"checkpoint:{record.checkpoint_sha256}"
            links.append(QueryLink(
                "CHECKPOINT", meta.record_id,
                checkpoint_ref, checkpoint_ref))
            links.extend(QueryLink(
                "RECEIPT", checkpoint_ref, ref,
                ref if ref in self._by_id else None,
            ) for ref in meta.receipt_refs)
        return tuple(sorted(
            links, key=lambda item: (
                item.relation, item.target_ref, item.source_record_id)))

    def _query_links(self, request: QueryRequest) -> QueryPage:
        record = self._by_id.get(request.record_id)
        if record is not None:
            if not matches_identity(record, request):
                links = ()
            else:
                links = tuple(
                    link for link in self._links_for(record)
                    if link.source_record_id == request.record_id)
        else:
            source_records = [
                item for item in self._records
                if matches_identity(item, request, match_record_id=False)
            ]
            exact_checkpoint = request.record_id.startswith("checkpoint:")
            if exact_checkpoint:
                source_records = [
                    item for item in source_records
                    if type(item) is GenerationManifest
                    and f"checkpoint:{item.checkpoint_sha256}" == request.record_id
                ]
            elif request.mode is QueryMode.CURRENT:
                source_records = select_current(source_records)
            links = tuple(
                link
                for source in source_records
                for link in self._links_for(source)
                if link.source_record_id == request.record_id
            )
        return self._page(request, (), (), links, exact_missing=not links)

    def _query_reference(self, request: QueryRequest) -> QueryPage:
        source_records = [
            item for item in self._records
            if matches_identity(item, request)
        ]
        if request.mode is QueryMode.CURRENT and request.record_id is None:
            source_records = select_current(source_records)
        links = tuple(
            link for record in source_records for link in self._links_for(record)
            if link.target_ref == request.reference
        )
        linked_source_ids = {link.source_record_id for link in links}
        relevant_record_ids = linked_source_ids | {request.reference}
        marker_records = [
            item for item in source_records
            if (
                item.meta.record_id in linked_source_ids
                or (type(item) is PartialEnvelope
                    and item.partial_record_id in relevant_record_ids)
                or (type(item) is StaleEnvelope
                    and item.stale_record_id in relevant_record_ids)
                or (type(item) is UnavailableEnvelope
                    and item.resource in relevant_record_ids)
            )
        ]
        target = self._by_id.get(request.reference)
        if target is not None and target not in marker_records:
            marker_records.append(target)
        markers = self._markers(marker_records, request)
        return self._page(
            request, (), markers, links, exact_missing=not links and not markers)

    def _page(self, request, records, markers, links=(), *, exact_missing=False):
        return build_page(
            available=self.available, request=request, records=records,
            markers=markers, links=links, exact_missing=exact_missing,
        )

    def query(self, request: QueryRequest) -> QueryPage:
        if request.family is QueryFamily.LINKS:
            return self._query_links(request)
        if request.family is QueryFamily.REFERENCE:
            return self._query_reference(request)
        if not self.available:
            return self._page(request, (), (), exact_missing=False)
        records = self._base_records(request)
        markers = self._markers(records, request)
        exact_missing = bool(
            request.record_id is not None
            or request.generation is not None
            or request.frontier_id is not None
            or request.as_of is not None
        ) and not records and not markers
        return self._page(
            request, records, markers, exact_missing=exact_missing)

    @staticmethod
    def encode_page(page: QueryPage) -> dict:
        return encode_query_page(page)
