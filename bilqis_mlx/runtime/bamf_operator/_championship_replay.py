"""B13-authenticated checkpoint replay for native championship adjudication."""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_for_canonical_consumer,
)
from bilqis_mlx.learning.capability_championship import ReplayBinding
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.bamf_bundle import BamfBundleCandidate
from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
from bilqis_mlx.runtime.capability_retention import Assessment
from bilqis_mlx.runtime.factory_complete_solver import factory_complete_solver
from bilqis_mlx.runtime.retention.championship_evidence import (
    capability_championship_instruments,
)


GENERATION_LOCATOR_ARITY = 2


def _invalid(reason):
    ErrorBus.raise_(SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID, reason=reason)


def _native_checkpoint(candidate: BamfBundleCandidate) -> Checkpoint:
    return Checkpoint(
        candidate_identity_for_canonical_consumer(candidate.retained_state),
        f"bamf-generations/{candidate.generation}",
        candidate.retained_state.optimizer_step,
        True,
    )


def _as_candidate(student) -> BamfBundleCandidate:
    """Adapt an ancestry-proven immutable generation for source replay only."""
    return BamfBundleCandidate(**{
        field.name: getattr(student, field.name)
        for field in fields(BamfBundleCandidate)
    })


def _accepted_ancestor(run_dir, parent, cache, checkpoint):
    parts = checkpoint.filename.split("/")
    if (len(parts) != GENERATION_LOCATOR_ARITY
            or parts[0] != "bamf-generations" or not parts[1].isdigit()):
        _invalid("BAMF_CHAMPIONSHIP_NATIVE_CHECKPOINT_LOCATOR_INVALID")
    target_generation = int(parts[1])
    if target_generation > parent.generation:
        _invalid("BAMF_CHAMPIONSHIP_CHECKPOINT_NOT_ACCEPTED_ANCESTOR")
    current = parent
    manifest_sha256 = cache.accepted_manifest_sha256
    while current.generation > target_generation:
        parent_sha256 = current.parent_manifest_sha256
        if parent_sha256 is None:
            _invalid("BAMF_CHAMPIONSHIP_ACCEPTED_ANCESTRY_INCOMPLETE")
        prior = load_bamf_bundle(
            Path(run_dir) / "bamf-bundles" / parent_sha256,
            expected_manifest_sha256=parent_sha256,
        )
        if (prior.run_id != current.run_id
                or prior.generation + 1 != current.generation
                or current.parent_manifest_sha256 != parent_sha256):
            _invalid("BAMF_CHAMPIONSHIP_ACCEPTED_ANCESTRY_DRIFT")
        current, manifest_sha256 = prior, parent_sha256
    if (current.generation != target_generation
            or candidate_identity_for_canonical_consumer(current.retained_state)
            != checkpoint.sha256
            or current.retained_state.optimizer_step != checkpoint.optimizer_step):
        _invalid("BAMF_CHAMPIONSHIP_CHECKPOINT_IDENTITY_DRIFT")
    return current, manifest_sha256


def _solver_binding(
        source_context, artifact_path, run_dir, release, parent, cache,
        candidate, cohort, checkpoint_origin_group, *,
        expected_checkpoint=None, expected_generation=None, solver_contracts=None):
    if len(cohort.capability_groups) != 1:
        _invalid("BAMF_CHAMPIONSHIP_CAPABILITY_PANEL_REQUIRED")
    capability = cohort.capability_groups[0][0]
    instruments, _contract = capability_championship_instruments(
        source_context, candidate, artifact_path, cache, capability)
    if tuple(item.case for item in instruments) != cohort.cases:
        _invalid("BAMF_CHAMPIONSHIP_CAPABILITY_PANEL_DRIFT")
    solver, generation = factory_complete_solver(
        source_context, candidate, artifact_path, instruments)
    checkpoint = _native_checkpoint(candidate)
    if ((expected_checkpoint is not None and checkpoint != expected_checkpoint)
            or (expected_generation is not None and generation != expected_generation)):
        _invalid("BAMF_CHAMPIONSHIP_REPLAY_IDENTITY_DRIFT")
    contracts = tuple(solver_contracts or ())
    if not contracts:
        _invalid("BAMF_CHAMPIONSHIP_SOLVER_CONTRACTS_REQUIRED")

    def verify_generation(requested_generation, requested_checkpoint):
        return requested_generation == generation and requested_checkpoint == checkpoint

    return ReplayBinding(
        solver, generation, checkpoint, checkpoint_origin_group,
        contracts, verify_generation,
    )


def _current_binding(
        source_context, artifact_path, run_dir, release, parent, cache,
        successor, cohort, assessment, checkpoint_origin_group):
    if type(assessment) is not Assessment or assessment.cohort != cohort:
        _invalid("BAMF_CHAMPIONSHIP_ACCEPTED_ASSESSMENT_REQUIRED")
    return _solver_binding(
        source_context, artifact_path, run_dir, release, parent, cache,
        successor, cohort, checkpoint_origin_group,
        expected_generation=assessment.generation_digest,
        solver_contracts=tuple(sorted(set(assessment.solver_contracts))),
    )


def _incumbent_binding(
        source_context, artifact_path, run_dir, release, parent, cache,
        cohort, role):
    pointer = Checkpoint(**role["checkpoint"])
    student, _ = _accepted_ancestor(run_dir, parent, cache, pointer)
    provenance = role.get("complete_solver_provenance")
    if (not isinstance(provenance, dict)
            or provenance.get("weight_sha256") != pointer.sha256
            or not isinstance(provenance.get("generation_digest"), str)
            or not isinstance(provenance.get("solver_contracts"), (tuple, list))):
        _invalid("BAMF_CHAMPIONSHIP_ROLE_REPLAY_PROVENANCE_INVALID")
    origin = role.get("checkpoint_origin_group")
    if not isinstance(origin, str) or not origin:
        _invalid("BAMF_CHAMPIONSHIP_ROLE_ORIGIN_PROVENANCE_INVALID")
    return _solver_binding(
        source_context, artifact_path, run_dir, release, parent, cache,
        _as_candidate(student), cohort, origin,
        expected_checkpoint=pointer,
        expected_generation=provenance["generation_digest"],
        solver_contracts=tuple(provenance["solver_contracts"]),
    )


__all__ = ("_accepted_ancestor", "_current_binding", "_incumbent_binding")
