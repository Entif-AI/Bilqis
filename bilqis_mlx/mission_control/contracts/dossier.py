"""Evidence-bound capability dossier facts; producers own all interpretations."""
from __future__ import annotations

from dataclasses import dataclass
import json

from .model import DataValue, RecordMeta, ValueState, WireRecord, is_name, is_names, is_time, require


SECTIONS = ("performance", "teaching", "sources", "dependencies", "history")
RELATED_KINDS = ("capability", "episode", "semantic", "checkpoint", "source", "evidence")


def _name(value):
    return is_name(value) and len(value) <= 512


def _metric(value):
    return type(value) is DataValue and (
        not isinstance(value.value, str) or len(value.value) <= 512)


@dataclass(frozen=True)
class DossierValue:
    name: str
    value: DataValue

    def __post_init__(self):
        require(_name(self.name) and _metric(self.value), "DOSSIER_VALUE")


@dataclass(frozen=True)
class DossierEntry:
    entry_id: str
    section: str
    kind: str
    label: str
    generation: int
    observed_at: int
    values: tuple[DossierValue, ...]
    refs: tuple[str, ...]
    related_kind: str | None
    related_id: str | None

    def __post_init__(self):
        require(all(_name(item) for item in (self.entry_id, self.kind, self.label)),
                "DOSSIER_ENTRY_ID")
        require(self.section in SECTIONS, "DOSSIER_SECTION")
        require(is_time(self.generation) and is_time(self.observed_at), "DOSSIER_TIME")
        require(type(self.values) is tuple and len(self.values) <= 16
                and all(type(item) is DossierValue for item in self.values), "DOSSIER_VALUES")
        require(len({item.name for item in self.values}) == len(self.values), "DOSSIER_VALUE_DUPLICATE")
        require(is_names(self.refs) and len(self.refs) <= 16
                and all(_name(ref) for ref in self.refs), "DOSSIER_REFS")
        require(bool(self.refs) or not any(item.value.state is ValueState.PRESENT
                                          for item in self.values), "DOSSIER_EVIDENCE_REQUIRED")
        require((self.related_kind is None and self.related_id is None)
                or (self.related_kind in RELATED_KINDS and _name(self.related_id)), "DOSSIER_RELATED")


@dataclass(frozen=True)
class CapabilityDossier(WireRecord):
    SCHEMA = "bilqis.bamf.mission-control.capability-dossier/v1"
    meta: RecordMeta
    capability_id: str
    name: str
    now: DataValue
    top: DataValue
    total: DataValue
    debt: DataValue
    retention: DataValue
    eligibility: DataValue
    qualification: DataValue
    source_state: DataValue
    entries: tuple[DossierEntry, ...]

    def __post_init__(self):
        super().__post_init__()
        require(_name(self.capability_id) and _name(self.name), "DOSSIER_ID")
        require(all(_metric(item) for item in (
            self.now, self.top, self.total, self.debt, self.retention,
            self.eligibility, self.qualification, self.source_state)), "DOSSIER_METRICS")
        require(type(self.entries) is tuple and len(self.entries) <= 128
                and all(type(item) is DossierEntry for item in self.entries), "DOSSIER_ENTRIES")
        require(len({item.entry_id for item in self.entries}) == len(self.entries), "DOSSIER_ENTRY_DUPLICATE")
        refs = set((*self.meta.source_refs, *self.meta.evidence_refs, *self.meta.receipt_refs))
        require(all(set(item.refs) <= refs for item in self.entries), "DOSSIER_REFS_UNINDEXED")
        require(all(item.generation <= self.meta.run.generation
                    and item.observed_at <= self.meta.materialized_at
                    for item in self.entries), "DOSSIER_ENTRY_FUTURE")
        from .codec import encode_record
        size = len(json.dumps(encode_record(self), sort_keys=True,
                              separators=(",", ":")).encode("utf-8"))
        require(size <= 48 * 1024, "DOSSIER_ROW_TOO_LARGE")
