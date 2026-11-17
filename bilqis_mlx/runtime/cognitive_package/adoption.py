"""C12 bridge from authoritative screening into B12/B13 package-import custody."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from bilqis_mlx.runtime.bamf_bundle import BamfBundleCandidate
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, bind_accepted_execution_cache,
)
from bilqis_mlx.runtime.bamf_bundle.package_import_transition import (
    _issue_package_import_transition,
)
from bilqis_mlx.runtime.accepted_teacher_custody import (
    rebind_package_import_teacher_custody,
)
from bilqis_mlx.semantics.atlas_release_audit import ExportClearanceReceipt

from .contracts import SourceRights, require
from .delta import ScreenedDeltaCandidate
from .receiver import _load_current_generation, _receiver_tensors


def _artifact_digests(package):
    return tuple(sorted(artifact.digest for artifact in package.artifacts))


def _verify_export_clearance(
        package, parent, receipt, atlas_selection, source_frontier,
        source_context, run_dir):
    from bilqis_mlx.runtime.source_execution import SourceExecutionContext
    from bilqis_mlx.runtime.atlas_source_authority import (
        require_source_authority_runtime,
    )
    require(type(receipt) is ExportClearanceReceipt, "A12 export clearance required")
    require(type(source_context) is SourceExecutionContext,
            "accepted source execution context required")
    run_dir = Path(run_dir)
    source_context.require_accepted_runtime(run_dir)
    cache = bind_accepted_execution_cache(run_dir)
    authority = require_source_authority_runtime(
        source_context.source_authority(), cache)
    digests = _artifact_digests(package)
    clearance = authority._validate_export_clearance_context(
        cache, receipt, atlas_selection, source_frontier, digests)
    expected = SourceRights(
        receipt.source_owner, clearance, receipt.export_artifact_digests,
        receipt.revoked_artifact_digests, receipt.revocation_lineage)
    require(package.rights == expected, "package source rights do not match current A12 clearance")
    require(package.binding.semantic_release == receipt.semantic_release,
            "package semantic release differs from A12 clearance")
    correction = parent.correction_frontier
    require(correction.get("rights_epoch") == receipt.rights_epoch
            and correction.get("correction_generation") == receipt.correction_generation,
            "receiver rights frontier differs from A12 clearance")
    require(cache.source_authority_registry_sha256 is not None,
            "accepted source authority registry required")
    return (
        clearance,
        cache.accepted_manifest_sha256,
        cache.source_authority_registry_sha256,
    )


def _require_exact_parent(screened, pointer, parent):
    candidate = screened.candidate
    require(candidate.parent_generation == pointer["manifest_sha256"],
            "screened import parent is stale")
    require(candidate.parent_tensors == _receiver_tensors(parent),
            "screened import parent tensors drifted")


def _successor(parent, pointer, screened, transaction, clearance):
    decision = screened.decision
    package = screened.candidate.package
    transition = _issue_package_import_transition(
        package_sha256=package.digest,
        screened_candidate_sha256=screened.candidate.generation_digest,
        reset_policy_sha256=transaction.reset_policy_sha256,
        c05_evidence_sha256=decision.evidence_sha256,
        c05_policy_sha256=decision.policy_sha256,
        source_clearance_sha256=clearance)
    event = {
        "event": "BAMF_PACKAGE_IMPORT_ACCEPTED",
        "origin": "PACKAGE_IMPORT",
        "receiver_generation": parent.generation,
        "receiver_manifest_sha256": pointer["manifest_sha256"],
        "package_sha256": package.digest,
        "screened_candidate_sha256": screened.candidate.generation_digest,
        "reset_policy_sha256": transaction.reset_policy_sha256,
        "c05_evidence_sha256": decision.evidence_sha256,
        "c05_policy_sha256": decision.policy_sha256,
        "source_clearance_sha256": clearance,
        "optimizer_step": transaction.candidate.optimizer_step,
    }
    teacher = rebind_package_import_teacher_custody(
        parent, transaction.candidate)
    provenance = parent.provenance
    teacher_state = parent.teacher_state
    if teacher is not None:
        provenance = replace(
            provenance, teacher_identity=teacher.teacher_identity,
            teacher_epoch=teacher.teacher_epoch)
        teacher_state = dict(teacher.teacher_state)
    return BamfBundleCandidate(
        parent.run_id, parent.generation + 1, pointer["manifest_sha256"],
        parent.implementation_sha256, parent.topology, parent.extents,
        transaction.candidate, parent.optimizer_hyperparameters, provenance,
        parent.semantic_abi, parent.compiler_features, parent.correction_frontier,
        teacher_state, parent.evaluation_contract, transition, (event,),
        parent.run_identity, screened.baseline_ledger.to_record(),
        parent.learning_health_state, parent.championship_state)


def publish_screened_delta_import(
        screened, run_dir, *, export_clearance, atlas_selection, source_frontier,
        source_context, reserve_gib: float = 100.0,
):
    """Publish only an owner-issued, C05-eligible, A12-cleared exact-parent import."""
    require(type(screened) is ScreenedDeltaCandidate, "issued screened delta candidate required")
    screened.__post_init__()
    require(screened.decision.accepted, "C05 rejected package import")
    pointer, parent = _load_current_generation(Path(run_dir))
    _require_exact_parent(screened, pointer, parent)
    clearance, _manifest_sha256, _registry_sha256 = _verify_export_clearance(
        screened.candidate.package, parent, export_clearance, atlas_selection,
        source_frontier, source_context, run_dir)
    transaction = screened.transaction
    successor = _successor(parent, pointer, screened, transaction, clearance)
    return accept_and_publish(
        Path(run_dir), successor, transaction.candidate,
        decision=screened.decision,
        feature_sha256=successor.extents.factor_map_digest,
        reserve_gib=reserve_gib)
