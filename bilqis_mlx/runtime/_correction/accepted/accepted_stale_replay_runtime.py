"""Accepted-run stale-replay detection over the actual registered owner graph."""
from __future__ import annotations

from dataclasses import replace

from .accepted_correction_ledger import (
    _accepted_corrections_from_records, _manifest_lineage, append_record, read_records,
)
from .accepted_stale_replay_ledger import (
    DERIVED_CLAIM_EVENT, PROCESS_FAULT_EVENT, REMEDIATION_EVENT,
    derived_claim_from_record, process_fault_from_record, process_fault_record,
    process_fault_requalification_from_record,
    remediation_from_record,
)
from .atlas_requalification import RequalificationLedger
from .atlas_requalification_contracts import RequalificationStatus
from .atlas_revalidation_common import _invalid
from .atlas_stale_replay import escalate_stale_replay
from bilqis_mlx.semantics.cognitive_dependencies import (
    ArtifactKind, DependencyIndex, DependencyKind,
)


def _registered_index(targets, census_nodes=()) -> DependencyIndex | None:
    nodes = {node.artifact_id: node for node in census_nodes}
    census_ids = frozenset(nodes)
    for target in targets:
        owner = target.owner
        index = getattr(owner, "index", None)
        if not isinstance(index, DependencyIndex):
            continue
        for node in index.nodes:
            prior = nodes.get(node.artifact_id)
            if prior is not None and prior != node:
                if (node.artifact_id not in census_ids
                        or prior.kind is not ArtifactKind.CAPABILITY_SUPPORT
                        or node.kind is not ArtifactKind.CAPABILITY_SUPPORT):
                    _invalid("BAMF_C09_REGISTERED_OWNER_INDEX_CONFLICT")
            nodes[node.artifact_id] = node
    if not nodes:
        return None
    identifiers = set(nodes)
    if any(
        dependency.kind is DependencyKind.ARTIFACT
        and dependency.key not in identifiers
        for node in nodes.values()
        for dependency in node.immediate_dependencies
    ):
        return None
    return DependencyIndex.build(tuple(nodes.values()))


def _registered_requalification(
    targets, census: RequalificationLedger,
) -> RequalificationLedger:
    supports = {item.capability_id: item for item in census.capabilities}
    historical = {item: item for item in census.historical}
    tasks = {item.task_id: item for item in census.pending_source_tasks}
    intents = {item.event_id: item for item in census.pending_c10_intents}
    for target in targets:
        ledger = getattr(target.owner, "ledger", None)
        if not isinstance(ledger, RequalificationLedger):
            continue
        for support in ledger.capabilities:
            prior = supports.get(support.capability_id)
            if (prior is not None
                    and replace(prior, status=RequalificationStatus.QUALIFIED)
                    != replace(support, status=RequalificationStatus.QUALIFIED)):
                _invalid("BAMF_C09_REGISTERED_SUPPORT_CONFLICT")
            if (prior is None
                    or support.status is RequalificationStatus.REQUALIFICATION_REQUIRED):
                supports[support.capability_id] = support
        for item in ledger.historical:
            historical[item] = item
        for item in ledger.pending_source_tasks:
            prior = tasks.get(item.task_id)
            if prior is not None and prior != item:
                _invalid("BAMF_C09_REGISTERED_SUPPORT_CONFLICT")
            tasks[item.task_id] = item
        for item in ledger.pending_c10_intents:
            prior = intents.get(item.event_id)
            if prior is not None and prior != item:
                _invalid("BAMF_C09_REGISTERED_SUPPORT_CONFLICT")
            intents[item.event_id] = item
    return RequalificationLedger(
        capabilities=tuple(sorted(
            supports.values(), key=lambda item: item.capability_id)),
        historical=tuple(sorted(
            historical.values(),
            key=lambda item: (item.capability_id, item.retained_generation_sha256,
                              item.status.value, item.observation_ids))),
        pending_source_tasks=tuple(sorted(
            tasks.values(), key=lambda item: item.task_id)),
        pending_c10_intents=tuple(sorted(
            intents.values(), key=lambda item: item.event_id)),
    )


def _current_support_supersedes_fault(
    owner, requalification, lineage: tuple[str, ...],
) -> bool:
    capability_id = getattr(owner, "capability_id", None)
    if capability_id is None or requalification is None:
        return False
    if capability_id not in requalification.affected_capability_ids:
        return False
    current_support = getattr(owner, "support", None)
    if current_support is None:
        return False
    fault_support = requalification.ledger.capability(capability_id)
    current_generation = current_support.retained_generation_sha256
    fault_generation = fault_support.retained_generation_sha256
    if current_generation == fault_generation:
        return False
    order = {manifest: index for index, manifest in enumerate(lineage)}
    if current_generation not in order or fault_generation not in order:
        _invalid("BAMF_C09_PROCESS_FAULT_REQUALIFICATION_DRIFT")
    if order[current_generation] > order[fault_generation]:
        return True
    _invalid("BAMF_C09_PROCESS_FAULT_REQUALIFICATION_DRIFT")


def _install_fault(
    targets, fault, requalification=None, *, lineage: tuple[str, ...] = (),
) -> None:
    held = set(fault.held_artifact_ids)
    for target in targets:
        owner = target.owner
        if owner is None:
            continue
        support_superseded = _current_support_supersedes_fault(
            owner, requalification, lineage)
        owned = {
            node.artifact_id for node in getattr(owner, "index").nodes
        }.intersection(held)
        if owned and not support_superseded:
            target.process_fault_holds.update(owned)
            setattr(
                owner, "_accepted_process_fault_holds",
                frozenset(target.process_fault_holds),
            )
        capability_id = getattr(owner, "capability_id", None)
        if (requalification is not None
                and capability_id in requalification.affected_capability_ids
                and not support_superseded):
            installer = getattr(owner, "install_requalification", None)
            if not callable(installer):
                _invalid("BAMF_C09_PROCESS_FAULT_REQUALIFICATION_DRIFT")
            installer(requalification)


def replay_persisted_faults(retained, records=None) -> tuple[object, ...]:
    """Install already-committed process faults without reclassifying claims."""
    records = (read_records(retained.run_dir, retained.manifest_sha256)
               if records is None else records)
    targets = tuple(retained.targets.values())
    lineage = _manifest_lineage(retained.run_dir, retained.manifest_sha256)
    faults = []
    for record in records:
        if record["event"] != PROCESS_FAULT_EVENT:
            continue
        fault = process_fault_from_record(record)
        _install_fault(
            targets, fault,
            process_fault_requalification_from_record(record),
            lineage=lineage,
        )
        faults.append(fault)
    return tuple(faults)


def _support_census(retained):
    cached = getattr(retained, "_accepted_support_census", None)
    if cached is not None:
        return cached
    from bilqis_mlx.runtime.capability_support_loading import accepted_support_census
    cached = accepted_support_census(retained.run_dir, retained.manifest_sha256)
    retained._accepted_support_census = cached
    return cached


def _flush_c10_intents(retained, ledger, corrections) -> None:
    if not ledger.pending_c10_intents:
        return
    from bilqis_mlx.runtime.akasha_outbox import append_c09_intent
    outbox = retained.run_dir / "akasha-outbox.sqlite3"
    for intent in ledger.pending_c10_intents:
        correction = corrections.get(intent.correction_event_id)
        if correction is None:
            continue
        append_c09_intent(
            outbox, intent, correction, ledger, retained.registry)


def _flush_context_requalifications(retained, ledger, records) -> None:
    """Project only context tasks with durable source-owned v2 temporal custody."""
    tasks = tuple(
        task for task in ledger.pending_source_tasks
        if task.context_event_id is not None
    )
    if not tasks:
        return
    context_records = {
        record["context_invalidation"]["context_event_id"]: record
        for record in records
        if record["event"] == "BAMF_C09_CONTEXT_INVALIDATION"
    }
    from bilqis_mlx.runtime.akasha_outbox import append_context_requalification
    outbox = retained.run_dir / "akasha-outbox.sqlite3"
    for task in tasks:
        record = context_records.get(task.context_event_id)
        if record is None:
            _invalid("BAMF_C10_CONTEXT_RECEIPT_REQUIRED")
        # Historical v1 invalidations remain replayable C09 evidence, but they
        # cannot be projected into C10 because no source-owned four-time tuple
        # existed. Never fabricate or alias one during replay.
        if (record["context_invalidation"].get("schema_version")
                != "bilqis.c09-context-invalidation/v2"):
            continue
        append_context_requalification(
            outbox, retained.run_dir, retained.manifest_sha256, task, ledger)


def replay_stale_evidence(retained) -> tuple[object, ...]:
    """Rebuild durable stale-replay faults from accepted evidence and live owners."""
    if retained.registry is None:
        return ()
    records = read_records(retained.run_dir, retained.manifest_sha256)
    targets = tuple(retained.targets.values())
    replay_persisted_faults(retained, records)
    lineage = _manifest_lineage(retained.run_dir, retained.manifest_sha256)

    census, census_nodes = _support_census(retained)
    index = _registered_index(targets, census_nodes)
    ledger = _registered_requalification(targets, census)
    if index is None:
        return ()
    corrections = {
        event.event_id: event
        for _event_id, event in _accepted_corrections_from_records(
            records, retained.registry)
    }
    _flush_c10_intents(retained, ledger, corrections)
    _flush_context_requalifications(retained, ledger, records)
    remediations = tuple(
        remediation_from_record(record)
        for record in records if record["event"] == REMEDIATION_EVENT)
    claims = tuple(
        derived_claim_from_record(record)
        for record in records if record["event"] == DERIVED_CLAIM_EVENT)
    existing = {
        process_fault_from_record(record).offending_claim_id
        for record in records if record["event"] == PROCESS_FAULT_EVENT
    }
    results = []
    known_ids = {node.artifact_id for node in index.nodes}
    for remediation in remediations:
        correction = corrections.get(remediation.correction_event_id)
        if correction is None:
            continue
        for claim in claims:
            if claim.claim_id in existing or not set(claim.derived_path) <= known_ids:
                continue
            result = escalate_stale_replay(
                remediation, claim, correction, index, ledger, retained.registry)
            if result is None:
                continue
            record = process_fault_record(
                retained.manifest_sha256, result.fault, result.requalification)
            append_record(retained.run_dir, retained.manifest_sha256, record)
            _install_fault(
                targets, result.fault, result.requalification, lineage=lineage)
            _flush_c10_intents(retained, result.requalification.ledger, corrections)
            existing.add(claim.claim_id)
            results.append(result)
    return tuple(results)


__all__ = ("replay_persisted_faults", "replay_stale_evidence")
