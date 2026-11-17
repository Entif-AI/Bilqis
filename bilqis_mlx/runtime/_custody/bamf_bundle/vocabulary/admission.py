"""A02 production-quality vocabulary staging through accepted B13 custody."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import shutil

import mlx.core as mx
import numpy as np

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_candidate import issue_parameter_extension_state
from bilqis_mlx.learning.atlas_plasticity import IdentityRowAge, PlasticityPolicy
from bilqis_mlx.learning.capability_championship_state import clear_championship_epoch
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.semantics.atlas.snapshot import (
    AtlasArtifactSelection, load_pinned_atlas_snapshot,
)
from bilqis_mlx.semantics.atlas_projection import (
    _canonical_bytes as _atlas_bytes, _digest as _atlas_sha256,
    resolve_atlas_source_bundle,
)
from bilqis_mlx.semantics.atlas_features import FeatureSchema
from bilqis_mlx.semantics.atlas.vocabulary import VocabularyBankParent, VocabularyPrior
from bilqis_mlx.semantics.atlas.vocabulary_planning import (
    _plan_authenticated_vocabulary_extension,
)
from bilqis_mlx.semantics.atlas.vocabulary_resources import (
    RESOURCE_SCHEMA, _build_authenticated_registry_mirror_delta,
)
from bilqis_mlx.semantics.atlas.vocabulary_transaction import (
    FullVocabularyParent, _stage_authenticated_full_vocabulary_extension,
)
from .admission_records import (
    A02StagedVocabularyExtension, A02VocabularyStagingReceipt, STAGED_EVENT,
    _issue_a02_staged_vocabulary_extension,
    require_issued_a02_staged_vocabulary_extension,
)
from ..feature_authority import (
    feature_schema_from_compiler_features, read_accepted_generation_feature_context,
)
from ..publication import load_bamf_generation_authority
from ..records import BamfBundleCandidate, canonical, invalid, sha


def _accepted_active_ids(parent, snapshot) -> tuple[str, ...]:
    """Recover the active semantic ABI from accepted B12/B13 custody."""
    indices = tuple(sorted(
        row.bank_index * ModelTopologySpecV2.semantic_bank_rows + row.row_index
        for row in parent.retained_state.policy.row_ages))
    if (indices != tuple(sorted(set(indices)))
            or any(index >= parent.extents.semantic_bank_count
                   * ModelTopologySpecV2.semantic_bank_rows for index in indices)
            or _atlas_sha256(_atlas_bytes(list(indices)))
            != parent.extents.active_semantic_digest
            or parent.semantic_abi.get("active_set_sha256")
            != parent.extents.active_semantic_digest):
        invalid("BAMF_A02_PARENT_ACTIVE_SET_DRIFT")
    by_index = {entry.index: entry.semantic_id for entry in snapshot.abi_entries}
    if len(by_index) != len(snapshot.abi_entries):
        invalid("BAMF_A02_PARENT_ACTIVE_SET_DRIFT")
    try:
        return tuple(by_index[index] for index in indices)
    except KeyError:
        invalid("BAMF_A02_PARENT_ACTIVE_SET_DRIFT")


def _bank_parent(parent, prior, available: int) -> VocabularyBankParent:
    optimizer = parent.retained_state.optimizer
    if parent.run_identity is None:
        invalid("BAMF_RUN_IDENTITY_DRIFT")
    banks = range(parent.extents.semantic_bank_count)
    weights = tuple(optimizer.parameters[f"identity.bank.{bank}"] for bank in banks)
    moments_m = tuple(optimizer.m[f"identity.bank.{bank}"] for bank in banks)
    moments_v = tuple(optimizer.v[f"identity.bank.{bank}"] for bank in banks)
    counts = []
    snapshot = load_pinned_atlas_snapshot(prior.source_selection)
    for semantic_id in prior.active_semantic_ids:
        entry = snapshot.abi_for_semantic(semantic_id)
        name = f"identity.bank.{entry.index // ModelTopologySpecV2.semantic_bank_rows}"
        count = optimizer.update_counts[name][entry.index % ModelTopologySpecV2.semantic_bank_rows]
        counts.append((entry.index, int(np.asarray(count))))
    feature_names = (
        "features.type", "features.project_type",
        "features.project_graph", "features.gates",
    )
    return VocabularyBankParent(
        prior, weights, moments_m, moments_v, tuple(counts),
        {name: optimizer.parameters[name] for name in feature_names},
        parent.run_identity.run_seed, available)


def _full_parent(parent, prior, available: int) -> FullVocabularyParent:
    optimizer = parent.retained_state.optimizer
    state = {
        "step": mx.array(parent.retained_state.optimizer_step, dtype=mx.uint64),
        "learning_rate": mx.array(
            parent.optimizer_hyperparameters.learning_rate, dtype=mx.float32),
        **{name: {"m": optimizer.m[name], "v": optimizer.v[name]}
           for name in optimizer.parameters},
    }
    return FullVocabularyParent(
        _bank_parent(parent, prior, available), parent.topology,
        optimizer.parameters, state, observed_available_bytes=available)


def _successor_state(parent, prepared):
    prior = parent.retained_state.optimizer
    counts = {}
    for name, parameter in prepared.parameters.items():
        if name in prior.update_counts:
            counts[name] = prior.update_counts[name]
        elif name.startswith("identity.bank."):
            counts[name] = mx.zeros((parameter.shape[0],), dtype=mx.uint64)
        else:
            invalid("BAMF_A02_UNEXPECTED_PARAMETER_EXTENSION")
    optimizer = AdamWStateTree(
        prepared.parameters,
        {name: prepared.optimizer_state[name]["m"] for name in prepared.parameters},
        {name: prepared.optimizer_state[name]["v"] for name in prepared.parameters},
        counts)
    ages = {row.identity: row for row in parent.retained_state.policy.row_ages}
    for item in prepared.bank_candidate.registry_mirror_delta:
        ages.setdefault((item.bank, item.row), IdentityRowAge(item.bank, item.row, 0))
    old_policy = parent.retained_state.policy
    policy = PlasticityPolicy(
        mode=old_policy.mode,
        accepted_fast_since_full=old_policy.accepted_fast_since_full,
        row_ages=tuple(ages[key] for key in sorted(ages)),
        policy_version=old_policy.policy_version,
        schema_version=old_policy.schema_version,
        mode_transition=old_policy.mode_transition)
    return issue_parameter_extension_state(
        parent.retained_state, optimizer, policy)


def _digest_record(value) -> str:
    return sha(canonical(value))


def _resource_requirement(resource) -> dict:
    """Stable admission requirement; live free bytes are checked, not identity."""
    record = asdict(resource)
    record.pop("observed_available_bytes")
    record.pop("fits")
    return record


def _sealed_resource_requirement(staged: A02StagedVocabularyExtension) -> int:
    staged = require_issued_a02_staged_vocabulary_extension(staged)
    events = tuple(
        event for event in staged.candidate.outbox
        if isinstance(event, dict) and event.get("event") == STAGED_EVENT)
    if len(events) != 1:
        invalid("BAMF_A02_STAGED_RESOURCE_REQUIREMENT_INVALID")
    record = events[0].get("resource_estimate")
    integer_fields = (
        "previous_bank_count", "next_bank_count", "added_bank_bytes",
        "complete_checkpoint_bytes_lower_bound", "disk_reserve_bytes",
        "extra_planning_bytes", "required_available_bytes_lower_bound",
    )
    if (not isinstance(record, dict)
            or record.get("schema_version") != RESOURCE_SCHEMA
            or set(record) != set(integer_fields) | {"schema_version"}
            or any(type(record.get(name)) is not int or record[name] < 0
                   for name in integer_fields)
            or record["previous_bank_count"] > record["next_bank_count"]
            or record["next_bank_count"] != staged.receipt.semantic_bank_count
            or record["required_available_bytes_lower_bound"]
            != record["complete_checkpoint_bytes_lower_bound"]
            + record["disk_reserve_bytes"] + record["extra_planning_bytes"]
            or _digest_record(record) != staged.receipt.resource_estimate_sha256):
        invalid("BAMF_A02_STAGED_RESOURCE_REQUIREMENT_INVALID")
    return record["required_available_bytes_lower_bound"]


def require_staged_vocabulary_admission_headroom(
        run_dir: Path,
        staged: A02StagedVocabularyExtension) -> int:
    """Recheck the A02-sealed disk requirement immediately before first commit."""
    run_dir = Path(run_dir)
    required = _sealed_resource_requirement(staged)
    available = int(shutil.disk_usage(run_dir).free)
    if available < required:
        invalid("BAMF_VOCABULARY_ADMISSION_DISK_BUDGET_EXCEEDED")
    return available


def _accepted_vocabulary_parent(run_dir: Path, artifact_path: str):
    pointer_path = run_dir / "bamf-state.json"
    feature_context = read_accepted_generation_feature_context(pointer_path)
    parent_receipt = feature_context.receipt
    features = feature_context.features
    predecessor = feature_context.construction_predecessor
    parent, parent_manifest = load_bamf_generation_authority(pointer_path)
    if parent_manifest != parent_receipt.generation_manifest_sha256:
        invalid("BAMF_A02_PARENT_AUTHORITY_DRIFT")
    selection = AtlasArtifactSelection(
        str(artifact_path), features.atlas_bundle_id,
        features.semantic_release, features.source_bundle_id)
    snapshot = load_pinned_atlas_snapshot(selection)
    recorded = feature_schema_from_compiler_features(parent.compiler_features)
    schema = FeatureSchema(
        recorded.role_ids, recorded.schema_ids, predecessor,
        recorded.source_bindings)
    prior = VocabularyPrior(
        selection, parent.extents, features, schema,
        _accepted_active_ids(parent, snapshot), parent_manifest)
    return parent, parent_manifest, parent_receipt, features, predecessor, prior


def _prepare_vocabulary_extension(
        run_dir: Path, source_bundle_path: Path, admissions: tuple[str, ...],
        parent, features, predecessor, prior):
    full_parent = _full_parent(parent, prior, int(shutil.disk_usage(run_dir).free))
    plan = _plan_authenticated_vocabulary_extension(
        prior, admissions, parent.topology, features, predecessor)
    prepared = _stage_authenticated_full_vocabulary_extension(
        full_parent, plan, accepted_features=features, predecessor=predecessor)
    mirror = _build_authenticated_registry_mirror_delta(
        prior, plan, source_bundle_path=source_bundle_path,
        accepted_features=features, predecessor=predecessor)
    return plan, prepared, mirror


def _stage_vocabulary_extension_from_accepted(
        run_dir: Path, source_bundle_path: Path, admissions: tuple[str, ...],
        accepted_parent) -> A02StagedVocabularyExtension:
    run_dir = Path(run_dir)
    parent, parent_manifest, parent_receipt, features, predecessor, prior = (
        accepted_parent)
    plan, prepared, mirror = _prepare_vocabulary_extension(
        run_dir, Path(source_bundle_path), admissions, parent, features,
        predecessor, prior)
    successor_state = _successor_state(parent, prepared)
    resource_record = _resource_requirement(prepared.resource_estimate)
    receipt = A02VocabularyStagingReceipt(
        run_id=parent.run_id, generation=parent.generation + 1,
        parent_manifest_sha256=parent_manifest,
        parent_feature_receipt_sha256=parent_receipt.digest,
        candidate_identity_sha256=candidate_identity_digest(successor_state),
        source_allocation_sha256=plan.source_allocation_digest,
        plan_sha256=sha(canonical(asdict(plan))),
        prepared_extents_sha256=prepared.extents_digest,
        active_mask_sha256=prepared.active_mask_sha256,
        registry_mirror_sha256=mirror.digest,
        resource_estimate_sha256=_digest_record(resource_record),
        active_set_sha256=prepared.bank_candidate.extents.active_semantic_digest,
        feature_sha256=features.digest,
        semantic_bank_count=prepared.bank_candidate.extents.semantic_bank_count,
    )
    event = {
        "event": STAGED_EVENT,
        "staging_receipt": receipt.to_record(),
        "plan": asdict(plan), "registry_mirror": asdict(mirror),
        "resource_estimate": resource_record,
    }
    semantic = dict(parent.semantic_abi)
    semantic.update({
        "active_set_sha256": prepared.bank_candidate.extents.active_semantic_digest,
        "semantic_bank_count": prepared.bank_candidate.extents.semantic_bank_count,
        "bank_identities": [
            f"bank:{index}" for index in range(
                prepared.bank_candidate.extents.semantic_bank_count)],
    })
    championship_state = parent.championship_state
    if championship_state is not None:
        championship_state = clear_championship_epoch(
            dict(championship_state),
            source_manifest_sha256=parent_manifest,
            source_generation=parent.generation,
        )
    candidate = BamfBundleCandidate(
        parent.run_id, parent.generation + 1, parent_manifest,
        parent.implementation_sha256, parent.topology,
        prepared.bank_candidate.extents, successor_state,
        parent.optimizer_hyperparameters, parent.provenance,
        semantic, dict(parent.compiler_features),
        dict(parent.correction_frontier), dict(parent.teacher_state),
        dict(parent.evaluation_contract),
        {"schema": "bilqis.mlx.bamf-generation-transition/v1",
         "kind": "PARAMETER_EXTENSION", "invalidate_derived_caches": True},
        (event,), parent.run_identity, parent.baseline_evidence,
        parent.learning_health_state, championship_state)
    return _issue_a02_staged_vocabulary_extension(candidate, receipt)


def stage_vocabulary_extension(
        run_dir: Path, artifact_path: str, source_bundle_path: Path,
        admissions: tuple[str, ...]) -> A02StagedVocabularyExtension:
    """Prepare one exact A02 successor without granting C07 admission authority."""
    run_dir = Path(run_dir)
    accepted_parent = _accepted_vocabulary_parent(run_dir, artifact_path)
    return _stage_vocabulary_extension_from_accepted(
        run_dir, Path(source_bundle_path), admissions, accepted_parent)


def stage_vocabulary_extension_from_source_id(
        run_dir: Path, artifact_path: str, source_bundle_id: str,
        admissions: tuple[str, ...]) -> A02StagedVocabularyExtension:
    """Stage through host storage without accepting a caller-owned source path."""
    run_dir = Path(run_dir)
    source_bundle_path = resolve_atlas_source_bundle(source_bundle_id)
    accepted_parent = _accepted_vocabulary_parent(run_dir, artifact_path)
    prior = accepted_parent[-1]
    if source_bundle_id != prior.source_selection.source_bundle_id:
        invalid("BAMF_A02_SOURCE_BUNDLE_ID_MISMATCH")
    return _stage_vocabulary_extension_from_accepted(
        run_dir, source_bundle_path, admissions, accepted_parent)
