"""C05-owned immutable fixed-school custody for accepted BAMF lineages."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from bilqis_mlx.generated_assessment import EXECUTABLE_COHORT_SCHEMA
from bilqis_mlx.runtime.assessment import _draw_executable_scope_cohort
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache,
    load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle.publication import inspect_accepted_generation
from bilqis_mlx.runtime.capability_evaluation import _invalid

from ._factory_fixed_school_contract import (
    SCHEMA, load_trusted_complete_school, pointer, require_receipt, school_seed, scope,
)
from ._factory_fixed_school_custody import fixed_school_lock
from ._factory_fixed_school_io import fixed_school_root, require_projection_json
from ._factory_fixed_school_trust import (
    load_fixed_school_trust, publish_fixed_school_trust,
)


def _accepted_parent(source_context, run_dir: Path, expected_parent_manifest_sha256: str):
    source_context.require_accepted_runtime(run_dir)
    parent = load_accepted_generation(run_dir)
    cache = bind_accepted_execution_cache(run_dir)
    custody = parent.retained_state.custody
    inspection = inspect_accepted_generation(run_dir / "bamf-state.json")
    if (inspection.factory_release_sha256 != source_context.release.release_sha256
            or inspection.generation_manifest_sha256 != cache.accepted_manifest_sha256
            or parent.run_identity is None
            or inspection.run_identity_sha256 != parent.run_identity.digest
            or custody is None or parent.run_id != cache.run_id
            or parent.generation != cache.generation
            or custody.manifest_sha256 != cache.accepted_manifest_sha256
            or cache.accepted_manifest_sha256 != expected_parent_manifest_sha256):
        _invalid("BAMF_C05_FIXED_SCHOOL_ACCEPTED_PARENT_DRIFT")
    return parent, cache


def _founding_scope_context(source_context, run_dir, parent):
    """Bind fixed-school custody to the founding release, through verified edges."""
    identity = parent.run_identity
    if identity is None:
        _invalid("BAMF_C05_BAMF_RUN_IDENTITY_REQUIRED")
    founding_sha = identity.factory_release_sha256
    current = source_context.release
    if current.release_sha256 == founding_sha:
        return source_context

    from bilqis_mlx.factory.profile_expansion import verify_profile_expansion
    from bilqis_mlx.runtime.admission import _read_executable_factory_release_artifact

    seen = {current.release_sha256}
    try:
        while current.release_sha256 != founding_sha:
            predecessor_sha = current.predecessor_release_sha256
            if not predecessor_sha or predecessor_sha in seen:
                raise ValueError("missing or cyclic release ancestry")
            predecessor = _read_executable_factory_release_artifact(run_dir, {
                "factory_release_sha256": predecessor_sha,
                "factory_release_file": f"factory-releases/{predecessor_sha}.json",
            })
            verify_profile_expansion(predecessor, current)
            seen.add(predecessor_sha)
            current = predecessor
    except (OSError, ValueError, TypeError, KeyError) as exc:
        _invalid("BAMF_C05_FIXED_SCHOOL_FOUNDING_RELEASE_INVALID")
        raise AssertionError from exc
    return replace(source_context, release=current)


def _trusted_school(
        root_fd, receipt_raw, cohort_raw, source_manifest, source_context, parent,
        capabilities, contract, source_identity):
    try:
        receipt = json.loads(receipt_raw)
        cohort_payload = json.loads(cohort_raw)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
        _invalid("BAMF_C05_FIXED_SCHOOL_TRUST_DRIFT")
        raise AssertionError
    receipt = require_receipt(
        receipt, source_context=source_context, parent=parent,
        capabilities=capabilities, contract=contract, source_identity=source_identity)
    school = load_trusted_complete_school(
        cohort_payload, source_manifest, source_context.release, capabilities,
        pointer(receipt))
    require_projection_json(
        root_fd, "c05-fixed-school", f"{parent.run_identity.digest}.json", receipt_raw)
    require_projection_json(
        root_fd, "cohorts", f"{receipt['cohort_sha256']}.json", cohort_raw)
    return school


def _materialize_school(
        root_fd, source_manifest, source_context, parent, cache,
        capabilities, contract, source_identity):
    identity = parent.run_identity
    seed = school_seed(
        identity, source_context.release, source_identity, capabilities, contract)
    cohort, actual_contract = _draw_executable_scope_cohort(
        source_context.source_root, source_context.graph, source_context.release,
        source_context.source_registry, capabilities=capabilities, seed=seed)
    if actual_contract != contract:
        _invalid("BAMF_C05_FIXED_SCHOOL_SCOPE_DRIFT")
    cohort_payload = {
        "schema": EXECUTABLE_COHORT_SCHEMA,
        "factory_release_sha256": contract.factory_release_sha256,
        "semantic_catalog_sha256": contract.semantic_catalog_sha256,
        "source_manifest_sha256": source_manifest["manifest_sha256"],
        "capabilities": list(contract.capabilities),
        "rubric_sha256": contract.rubric_sha256,
        "source_sha256": contract.source_sha256,
        "generator_version": contract.generator_version,
        "seed": cohort.seed,
        "cohort_sha256": cohort.digest,
        "rows": list(cohort.rows),
    }
    receipt = {
        "schema": SCHEMA,
        "run_id": parent.run_id,
        "run_identity_sha256": identity.digest,
        "foundation_parent_manifest_sha256": cache.accepted_manifest_sha256,
        "factory_release_sha256": source_context.release.release_sha256,
        "source_identity_sha256": source_identity,
        "semantic_catalog_sha256": source_context.release.semantic_catalog_sha256,
        "capabilities": list(capabilities),
        "rubric_sha256": contract.rubric_sha256,
        "source_sha256": contract.source_sha256,
        "generator_version": contract.generator_version,
        "seed": seed,
        "cohort_sha256": cohort.digest,
        "cohort_file": f"cohorts/{cohort.digest}.json",
        "cohort_seed": cohort.seed,
    }
    require_receipt(
        receipt, source_context=source_context, parent=parent,
        capabilities=capabilities, contract=contract, source_identity=source_identity)
    trusted = publish_fixed_school_trust(receipt, cohort_payload)
    return _trusted_school(
        root_fd, trusted.receipt_raw, trusted.cohort_raw,
        source_manifest, source_context, parent,
        capabilities, contract, source_identity)


def _bamf_fixed_school_cohort(
        source_context, run_dir: Path, *, expected_parent_manifest_sha256: str):
    """Create once, then cold-verify one whole-release fixed school per BAMF run."""
    run_dir = Path(run_dir)
    with fixed_school_root(run_dir) as (root_fd, _root_identity):
        with fixed_school_lock(root_fd):
            parent, cache = _accepted_parent(
                source_context, run_dir, expected_parent_manifest_sha256)
            founding_context = _founding_scope_context(source_context, run_dir, parent)
            capabilities, contract, source_identity = scope(founding_context, parent)
            source_manifest = {"manifest_sha256": source_identity}
            trusted = load_fixed_school_trust(parent.run_identity.digest)
            if trusted is None:
                school = _materialize_school(
                    root_fd, source_manifest, founding_context, parent, cache,
                    capabilities, contract, source_identity)
            else:
                school = _trusted_school(
                    root_fd, trusted.receipt_raw, trusted.cohort_raw,
                    source_manifest, founding_context, parent, capabilities,
                    contract, source_identity)
            _accepted_parent(source_context, run_dir, expected_parent_manifest_sha256)
            return school


__all__ = ()
