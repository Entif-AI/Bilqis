"""A09.4 regressions for exact A09.3 projection custody (ADR-122)."""
from dataclasses import replace
import hashlib
import unittest
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.atlas_frontier_contracts import _bytes
from bilqis_mlx.factory.atlas_frontier_progress import plan_frontier_progress
from bilqis_mlx.factory.atlas_frontier_progress_audit import (
    rehydrate_frontier_progress,
)
from bilqis_mlx.factory.atlas_frontier_selection import (
    DeferredClosure,
    _candidate_signature,
    _ranked_ready_targets,
    select_frontier_delta,
)
from bilqis_mlx.factory.atlas_frontier_selection_validation import (
    TargetDeltaProjection,
    catalog_digest,
    obligation_signature,
)
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_progress import (
    ProjectionAuthorityFixture,
    _ready,
    _stage,
    _staged_ready,
)
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection import (
    _candidate,
    _closure,
    _options,
    _snapshot,
)
from bilqis_mlx.factory.tests.curriculum.frontier.test_candidate_staging import (
    CandidateStagingFixture,
)
def _forge_selection(selection, *, capabilities=None, identities=None):
    capabilities = capabilities or selection.introduced_capability_ids
    identities = identities if identities is not None else selection.introduced_semantic_ids
    obligations = tuple(
        (row.family_id, row.source_evidence_sha256, row.prerequisites)
        for row in selection.selected_obligations)
    signature = hashlib.sha256(_bytes({
        "semantic_id": selection.selected_semantic_id,
        "obligations": obligations,
        "introduced_capability_ids": capabilities,
        "introduced_semantic_ids": identities,
    })).hexdigest()
    return _rehash(replace(
        selection,
        introduced_capability_ids=capabilities,
        introduced_semantic_ids=identities,
        candidate_signature=signature,
    ), "selection_sha256")
def _rehash(value, field):
    draft = replace(value, **{field: "0" * 64})
    return replace(draft, **{field: draft.expected_digest()})
class AtlasFrontierProjectionCustodyTests(ProjectionAuthorityFixture, unittest.TestCase):
    def test_direct_proposal_requires_release_and_projection_evidence(self):
        _, snapshot, closure, selection = _ready()
        with self.assertRaises(BilqisError):
            plan_frontier_progress(snapshot, closure, selection)

    def test_same_semantic_capability_forgery_fails_closed(self):
        release, snapshot, closure, selection = _ready()
        projection = next(
            item for item in _options(snapshot, release, closure)
            if item.semantic_id == selection.selected_semantic_id)
        forged = _forge_selection(selection, capabilities=("Z.FORGED",))
        with self.assertRaises(BilqisError):
            plan_frontier_progress(
                snapshot, closure, forged,
                current_release=release,
                selected_projection=projection,
            )

    def test_same_semantic_identity_forgery_fails_closed(self):
        release, snapshot, closure, selection = _ready()
        projection = next(
            item for item in _options(snapshot, release, closure)
            if item.semantic_id == selection.selected_semantic_id)
        forged = _forge_selection(
            selection, identities=("fixture.forged.semantic",))
        with self.assertRaises(BilqisError):
            plan_frontier_progress(
                snapshot, closure, forged,
                current_release=release,
                selected_projection=projection,
            )

    def test_mutually_forged_selection_and_projection_fail_closed(self):
        release, snapshot, closure, selection = _ready()
        projection = next(
            item for item in _options(snapshot, release, closure)
            if item.semantic_id == selection.selected_semantic_id)
        capabilities = ("Z.FORGED",)
        identities = ("fixture.forged.semantic",)
        forged_projection = _rehash(replace(
            projection,
            added_capability_ids=capabilities,
            introduced_semantic_ids=identities,
            projected_semantic_catalog_sha256=catalog_digest(
                release.semantic_catalog + identities),
        ), "projection_sha256")
        forged_selection = _forge_selection(
            selection, capabilities=capabilities, identities=identities)
        forged_projection.verify()
        forged_selection.verify()
        with self.assertRaises(BilqisError):
            plan_frontier_progress(
                snapshot, closure, forged_selection,
                current_release=release,
                selected_projection=forged_projection,
            )

    def test_cold_resume_rejects_self_rehashed_forged_projection_custody(self):
        release, snapshot, closure, selection, receipt = _staged_ready()
        prior = plan_frontier_progress(
            snapshot, closure, selection,
            current_release=release,
            selected_projection=receipt.projection,
            staged_receipt=receipt,
        )
        forged_projection = _rehash(replace(
            receipt.projection,
            added_capability_ids=("Z.FORGED",),
        ), "projection_sha256")
        forged_receipt = _rehash(replace(
            receipt,
            projection=forged_projection,
        ), "receipt_sha256")
        with self.assertRaises(BilqisError):
            rehydrate_frontier_progress(
                replace(prior), (snapshot,), (forged_receipt,))

    def test_historical_receipt_requires_authenticated_staging_membership(self):
        _, snapshot, _, _, receipt = _staged_ready()
        unstaged_snapshot = _rehash(replace(
            snapshot, staged_factory_release_sha256s=()), "snapshot_sha256")
        unstaged_selection = _rehash(replace(
            receipt.selection,
            snapshot_sha256=unstaged_snapshot.snapshot_sha256,
        ), "selection_sha256")
        forged_receipt = _rehash(replace(
            receipt,
            selection=unstaged_selection,
            selection_snapshot=unstaged_snapshot,
        ), "receipt_sha256")
        with self.assertRaises(BilqisError):
            forged_receipt.verify()

    def test_cold_resume_rejects_self_consistent_alternate_ready_selection(self):
        release, snapshot, closure, selection, receipt = _staged_ready()
        prior = plan_frontier_progress(
            snapshot, closure, selection, staged_receipt=receipt)
        _, ranked = _ranked_ready_targets(snapshot, closure)
        slope, neg_unlocks, _, alternate_id, rows = next(
            item for item in ranked if item[3] == "z.op.1")
        capabilities = receipt.staged_successor.transition.added_capabilities
        identities = tuple(
            receipt.staged_successor.semantic_catalog[
                len(release.semantic_catalog):
            ]
        )
        projection = TargetDeltaProjection(
            semantic_id=alternate_id,
            obligation_signature=obligation_signature(rows),
            current_release_sha256=release.release_sha256,
            current_semantic_catalog_sha256=release.semantic_catalog_sha256,
            added_capability_ids=capabilities,
            introduced_semantic_ids=identities,
            projected_semantic_catalog_sha256=catalog_digest(
                release.semantic_catalog + identities),
            projection_sha256="0" * 64,
        )
        projection = _rehash(projection, "projection_sha256")
        selected_keys = {
            (item.semantic_id, item.family_id) for item in rows
        }
        deferred = tuple(sorted(DeferredClosure(
            item.semantic_id,
            item.family_id,
            item.status,
            item.reasons,
        ) for item in closure.candidates
            if (item.semantic_id, item.family_id) not in selected_keys))
        forged_selection = _rehash(replace(
            selection,
            selected_semantic_id=alternate_id,
            selected_obligations=rows,
            introduced_capability_ids=capabilities,
            introduced_semantic_ids=identities,
            prerequisite_slope=slope,
            downstream_unlocks=-neg_unlocks,
            deferred=deferred,
            candidate_signature=_candidate_signature(
                alternate_id, rows, capabilities, identities),
        ), "selection_sha256")
        forged_receipt = _rehash(replace(
            receipt,
            selection=forged_selection,
            projection=projection,
        ), "receipt_sha256")
        forged_receipt.verify()
        with self.assertRaises(BilqisError):
            rehydrate_frontier_progress(
                replace(prior), (snapshot,), (forged_receipt,))

    def test_cold_resume_rejects_alternate_ready_cursor_laundering(self):
        fixture = CandidateStagingFixture()
        fixture.setUp()
        staged = fixture.stage()
        release = fixture.current
        snapshot = _snapshot(release, cursor=0, prerequisite_edges=())
        snapshot = _rehash(replace(
            snapshot,
            staged_factory_release_sha256s=(staged.successor.release_sha256,),
        ), "snapshot_sha256")
        closure = _closure(snapshot, tuple(
            _candidate(snapshot, identity)
            for identity in snapshot.source_eligible_concept_ids))
        capabilities = {
            identity: staged.successor.transition.added_capabilities
            for identity in snapshot.source_eligible_concept_ids
        }
        identities = {identity: () for identity in snapshot.source_eligible_concept_ids}
        projections = _options(
            snapshot, release, closure,
            capabilities=capabilities, identities=identities)
        selection = select_frontier_delta(
            snapshot, closure, release, projections)
        projection = next(
            item for item in projections
            if item.semantic_id == selection.selected_semantic_id)
        receipt = _stage(selection, projection, release, staged.successor, snapshot)
        prior = plan_frontier_progress(
            snapshot, closure, selection, staged_receipt=receipt)
        forged_snapshot = _rehash(replace(snapshot, cursor=1), "snapshot_sha256")
        forged_closure = _closure(forged_snapshot, tuple(
            _candidate(forged_snapshot, identity)
            for identity in forged_snapshot.source_eligible_concept_ids))
        forged_projections = _options(
            forged_snapshot, release, forged_closure,
            capabilities=capabilities, identities=identities)
        forged_selection = select_frontier_delta(
            forged_snapshot, forged_closure, release, forged_projections)
        self.assertEqual(forged_selection.selected_semantic_id, "z.op.1")
        forged_selection = _rehash(replace(
            forged_selection,
            snapshot_sha256=snapshot.snapshot_sha256,
            closure_sha256=closure.closure_sha256,
        ), "selection_sha256")
        forged_projection = next(
            item for item in forged_projections
            if item.semantic_id == "z.op.1")
        forged_receipt = _stage(
            forged_selection, forged_projection, release, staged.successor,
            forged_snapshot)
        with self.assertRaises(BilqisError):
            forged_receipt.verify()
