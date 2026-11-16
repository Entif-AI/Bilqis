"""Shared deterministic fixtures for A09.2 frontier-closure tests."""
from dataclasses import replace
import hashlib

from bilqis_mlx.factory.autonomy import (
    EvidenceReceipt,
    compile_autonomy_plan,
    initial_evidence_ledger,
    obligations_for_capability,
    record_evidence,
)
from bilqis_mlx.factory.atlas_frontier_closure import resolve_frontier_closure
from bilqis_mlx.factory.atlas_frontier_contracts import PrerequisiteEdge
from bilqis_mlx.factory.skos_curriculum import (
    IMPLEMENTATION_UNCOVERED,
    PROGRAM_BOUND,
    ConceptFamilyCoverage,
    FamilyInventoryCounts,
    FamilyObligation,
    SemanticFamilyInventory,
)
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_events import (
    _snapshot,
)


def rehash(snapshot, **changes):
    draft = replace(snapshot, snapshot_sha256="0" * 64, **changes)
    return replace(draft, snapshot_sha256=draft.expected_digest())


def row(semantic_id, family="positive_identity", *, implemented=True):
    return FamilyObligation(
        semantic_id,
        family,
        hashlib.sha256(f"{semantic_id}:{family}".encode()).hexdigest(),
        PROGRAM_BOUND if implemented else IMPLEMENTATION_UNCOVERED,
        "FACTORY_PROGRAM_BOUND" if implemented
        else "FAMILY_CONSTRUCTOR_CHECKER_NOT_BOUND",
    )


def current_evidence(*capability_ids):
    from bilqis_mlx.factory.tests.autonomy.autonomy_support import AutonomyFixture

    fixture = AutonomyFixture()
    fixture.setUp()
    release = fixture.release
    plan = compile_autonomy_plan(release)
    ledger = initial_evidence_ledger(release, plan=plan)
    checkpoint = "8" * 64
    step = 11
    index = 0
    for capability_id in capability_ids:
        for obligation in obligations_for_capability(release, capability_id):
            index += 1
            ledger = record_evidence(
                release,
                ledger,
                EvidenceReceipt(
                    obligation.obligation_id,
                    f"closure-evidence-{index}",
                    checkpoint,
                    step,
                    hashlib.sha256(f"cohort:{index}".encode()).hexdigest(),
                    obligation.minimum_specimens,
                    True,
                ),
                plan=plan,
                current_checkpoint_sha256=checkpoint,
                current_optimizer_step=step,
            )
    return release, ledger, plan, checkpoint, step


def three_node_snapshot():
    base = _snapshot()
    rows = (
        row("urn:one", implemented=False),
        row("urn:two"),
        row("urn:three"),
    )
    return rehash(
        base,
        source_eligible_concept_ids=("urn:one", "urn:three", "urn:two"),
        coverage_rows=tuple(sorted(
            rows, key=lambda item: (item.semantic_id, item.family_id))),
        prerequisite_edges=(PrerequisiteEdge("urn:two", "urn:one", "a" * 64),),
    )


def census_for(snapshot, *, obligations=None):
    rows = tuple(snapshot.coverage_rows if obligations is None else obligations)
    families_by_semantic = {}
    for item in rows:
        families_by_semantic.setdefault(item.semantic_id, []).append(item.family_id)
    concepts = tuple(ConceptFamilyCoverage(
        semantic_id,
        index,
        True,
        "SOURCE_ELIGIBLE",
        IMPLEMENTATION_UNCOVERED,
        tuple(sorted(families_by_semantic.get(semantic_id, ()))),
        (f"source:{semantic_id}",),
    ) for index, semantic_id in enumerate(snapshot.source_eligible_concept_ids))
    source_obligations = tuple(sorted((FamilyObligation(
        item.semantic_id,
        item.family_id,
        item.source_evidence_sha256,
        IMPLEMENTATION_UNCOVERED,
        "FAMILY_CONSTRUCTOR_CHECKER_NOT_BOUND",
    ) for item in rows), key=lambda item: (item.semantic_id, item.family_id)))
    return SemanticFamilyInventory(
        snapshot.semantic_release,
        snapshot.atlas_bundle_id,
        snapshot.source_bundle_id,
        snapshot.source_coverage_sha256,
        snapshot.source_eligible_concept_ids,
        snapshot.required_source_family_ids,
        (),
        concepts,
        source_obligations,
        snapshot.source_held_rows,
        snapshot.source_ir_only_rows,
        (),
        FamilyInventoryCounts(
            len(snapshot.source_eligible_concept_ids),
            0,
            len(snapshot.source_eligible_concept_ids),
            len(snapshot.source_held_rows),
            len(snapshot.source_ir_only_rows),
            0,
            len(snapshot.required_source_family_ids),
            0,
            len(source_obligations),
            len(source_obligations),
        ),
    )


def resolve(snapshot, *, census=None, **kwargs):
    frozen = census or census_for(snapshot)
    if snapshot.frozen_census_sha256 != frozen.digest:
        snapshot = rehash(snapshot, frozen_census_sha256=frozen.digest)
    return resolve_frontier_closure(snapshot, frozen, **kwargs)
