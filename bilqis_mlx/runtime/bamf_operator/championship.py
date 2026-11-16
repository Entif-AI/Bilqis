"""Native BAMF championship adjudication over accepted C05 evidence and B13 custody."""
from __future__ import annotations

from dataclasses import asdict, fields, replace
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_for_canonical_consumer,
)
from bilqis_mlx.learning.capability_championship import (
    ReplayBinding, assessment_exam, fresh_title_match,
)
from bilqis_mlx.learning.capability_championship_state import (
    championship_epoch_identity, compact_championship_state,
    empty_championship_state, reset_championship_state,
    validate_championship_state,
)
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.learning.epoch_championships import (
    advance_epoch, needed_incumbents,
)
from bilqis_mlx.runtime.bamf_bundle import BamfBundleCandidate
from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
from bilqis_mlx.runtime.capability_retention import Assessment, EvaluationCohort
from bilqis_mlx.runtime.factory_complete_solver import factory_complete_solver
from bilqis_mlx.runtime._factory_identity_evaluation import (
    _require_factory_evaluation,
)
from bilqis_mlx.runtime.factory_retention_owner import _fixed_school_instruments


MAX_ADJUDICATION_ROUNDS = 8
GENERATION_LOCATOR_ARITY = 2


def _invalid(reason):
    ErrorBus.raise_(SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID, reason=reason)


def _group_map(cohort: EvaluationCohort) -> dict[str, tuple[str, ...]]:
    groups = {}
    for capability, group in cohort.capability_groups:
        groups.setdefault(group, []).append(capability)
    return {group: tuple(capabilities) for group, capabilities in groups.items()}


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
        if (
            prior.run_id != current.run_id
            or prior.generation + 1 != current.generation
            or current.parent_manifest_sha256 != parent_sha256
        ):
            _invalid("BAMF_CHAMPIONSHIP_ACCEPTED_ANCESTRY_DRIFT")
        current, manifest_sha256 = prior, parent_sha256
    if (
        current.generation != target_generation
        or candidate_identity_for_canonical_consumer(current.retained_state)
        != checkpoint.sha256
        or current.retained_state.optimizer_step != checkpoint.optimizer_step
    ):
        _invalid("BAMF_CHAMPIONSHIP_CHECKPOINT_IDENTITY_DRIFT")
    return current, manifest_sha256


def _solver_binding(
        source_context, artifact_path, run_dir, release, parent, cache,
        candidate, cohort, checkpoint_origin_group, *,
        expected_checkpoint=None, expected_generation=None, solver_contracts=None,
):
    instruments = _fixed_school_instruments(
        source_context, candidate, artifact_path, run_dir, release,
        parent=parent, cache=cache)
    if tuple(item.case for item in instruments) != cohort.cases:
        _invalid("BAMF_CHAMPIONSHIP_FIXED_SCHOOL_DRIFT")
    solver, generation = factory_complete_solver(
        source_context, candidate, artifact_path, instruments)
    checkpoint = _native_checkpoint(candidate)
    if (
        expected_checkpoint is not None and checkpoint != expected_checkpoint
        or expected_generation is not None and generation != expected_generation
    ):
        _invalid("BAMF_CHAMPIONSHIP_REPLAY_IDENTITY_DRIFT")
    contracts = tuple(solver_contracts or ())
    if not contracts:
        _invalid("BAMF_CHAMPIONSHIP_SOLVER_CONTRACTS_REQUIRED")

    def verify_generation(requested_generation, requested_checkpoint):
        return (
            requested_generation == generation
            and requested_checkpoint == checkpoint
        )

    return ReplayBinding(
        solver, generation, checkpoint, checkpoint_origin_group,
        contracts, verify_generation,
    )


def _current_binding(
        source_context, artifact_path, run_dir, release, parent, cache,
        successor, cohort, assessment, checkpoint_origin_group):
    if (
        type(assessment) is not Assessment
        or assessment.cohort != cohort
    ):
        _invalid("BAMF_CHAMPIONSHIP_ACCEPTED_ASSESSMENT_REQUIRED")
    return _solver_binding(
        source_context, artifact_path, run_dir, release, parent, cache,
        successor, cohort, checkpoint_origin_group,
        expected_generation=assessment.generation_digest,
        solver_contracts=assessment.solver_contracts,
    )


def _incumbent_binding(
        source_context, artifact_path, run_dir, release, parent, cache,
        cohort, role):
    pointer = Checkpoint(**role["checkpoint"])
    student, _ = _accepted_ancestor(run_dir, parent, cache, pointer)
    provenance = role.get("complete_solver_provenance")
    if (
        not isinstance(provenance, dict)
        or provenance.get("weight_sha256") != pointer.sha256
        or not isinstance(provenance.get("generation_digest"), str)
        or not isinstance(provenance.get("solver_contracts"), (tuple, list))
    ):
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


def _epoch_identity(source_context, successor, cohort):
    release = source_context.release
    return championship_epoch_identity(
        factory_release_sha256=release.release_sha256,
        semantic_catalog_sha256=release.semantic_catalog_sha256,
        curriculum_sha256=release.execution_plan.curriculum_sha256,
        capability_groups=cohort.capability_groups,
        fixed_cohort_sha256=cohort.expected_case_digest,
        rubric_sha256=cohort.rubric_sha256,
        scope_sha256=cohort.scope_sha256,
        source_sha256=cohort.source_sha256,
        policy_sha256=cohort.policy_sha256,
        topology_sha256=successor.topology.digest,
        extents_sha256=successor.extents.digest,
        semantic_abi=successor.semantic_abi,
    )


def _resolve_current_cohort(cohort):
    from bilqis_mlx.learning.capability_championship import _source_context
    expected = _source_context(cohort)

    def resolve(key):
        if dict(key) != {name: expected[name] for name, _ in key}:
            _invalid("BAMF_CHAMPIONSHIP_BATTERY_CONTEXT_DRIFT")
        return cohort

    return resolve


def _fresh_exam(binding, cohort, group):
    return assessment_exam(
        binding.measure(cohort), binding, challenge_group=group)


def _adjudicate_group(
        epoch, capability_groups, group, challenger_exam, challenger_binding,
        incumbent_bindings, cohort):
    incumbent_exams = {
        sha256: _fresh_exam(binding, cohort, group)
        for sha256, binding in incumbent_bindings.items()
    }
    title_matches = {}
    fanout_screen = None
    resolve_cohort = _resolve_current_cohort(cohort)
    for _ in range(MAX_ADJUDICATION_ROUNDS):
        proposed, _, decisions = advance_epoch(
            epoch, capability_groups=capability_groups,
            challenger_exam=challenger_exam,
            incumbent_exams=incumbent_exams,
            title_matches=title_matches,
            fanout_screen=fanout_screen,
        )
        screen = next(
            (item for item in decisions
             if item.get("decision") == "FANOUT_SCREEN_REQUIRED"),
            None,
        )
        if screen is not None:
            if fanout_screen is not None:
                _invalid("BAMF_CHAMPIONSHIP_FANOUT_RECURSION")
            challenger_fresh = _fresh_exam(challenger_binding, cohort, group)
            fanout_screen = {}
            for capability in screen["capabilities"]:
                role = epoch["active_roles"][capability]
                incumbent = incumbent_bindings[role["checkpoint"]["sha256"]]
                incumbent_exam = _fresh_exam(incumbent, cohort, group)
                fanout_screen[capability] = {
                    "incumbent_checkpoint_sha256": incumbent.checkpoint.sha256,
                    "challenger_checkpoint_sha256": challenger_binding.checkpoint.sha256,
                    "incumbent_exam": incumbent_exam,
                    "challenger_exam": challenger_fresh,
                }
            continue
        pending = tuple(
            item["capability"] for item in decisions
            if item.get("decision") in {
                "TITLE_MATCH_REQUIRED", "FANOUT_TITLE_MATCH_REQUIRED",
            }
            and item["capability"] not in title_matches
        )
        if not pending:
            return proposed
        for capability in pending:
            role = epoch["active_roles"][capability]
            incumbent = incumbent_bindings[role["checkpoint"]["sha256"]]
            title_matches[capability] = fresh_title_match(
                role, incumbent, challenger_binding, cohort,
                resolve_cohort=resolve_cohort,
                settled_matchups=epoch.get("settled_matchups", {}),
                challenge_group=group,
            )
    _invalid("BAMF_CHAMPIONSHIP_ADJUDICATION_RECURSION")


def bind_accepted_championship_successor(
        run_dir, parent, cache, successor, source_context, artifact_path,
        target_capability, evaluation):
    """Attach one neural-inert championship projection to an accepted successor."""
    _require_factory_evaluation(evaluation)
    cohort = evaluation.championship_cohort
    assessment = evaluation.championship_assessment
    if cohort is None or assessment is None:
        return successor
    if type(cohort) is not EvaluationCohort or type(assessment) is not Assessment:
        _invalid("BAMF_CHAMPIONSHIP_ACCEPTED_EVIDENCE_INVALID")
    groups_by_capability = dict(cohort.capability_groups)
    origin_group = groups_by_capability.get(target_capability)
    if origin_group is None:
        _invalid("BAMF_CHAMPIONSHIP_TARGET_GROUP_MISSING")
    identity = _epoch_identity(source_context, successor, cohort)
    prior = parent.championship_state
    if prior is None:
        epoch = empty_championship_state(identity)
    else:
        prior = dict(prior)
        validate_championship_state(prior)
        epoch = (
            prior if prior["identity"] == identity
            else reset_championship_state(prior, identity)
        )
    capability_groups = _group_map(cohort)
    challenger = _current_binding(
        source_context, artifact_path, run_dir, source_context.release,
        parent, cache, successor, cohort, assessment, origin_group)
    for group in capability_groups:
        challenger_exam = assessment_exam(
            assessment, challenger, challenge_group=group)
        needed = needed_incumbents(
            epoch, capability_groups=capability_groups,
            challenger_exam=challenger_exam)
        incumbent_bindings = {}
        for sha256 in needed:
            role = next(
                role for role in epoch.get("active_roles", {}).values()
                if role["checkpoint"]["sha256"] == sha256)
            incumbent_bindings[sha256] = _incumbent_binding(
                source_context, artifact_path, run_dir, source_context.release,
                parent, cache, cohort, role)
        epoch = _adjudicate_group(
            epoch, capability_groups, group, challenger_exam, challenger,
            incumbent_bindings, cohort)
    return replace(
        successor,
        championship_state=compact_championship_state(epoch, identity),
    )
