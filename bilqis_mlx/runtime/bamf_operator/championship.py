"""Native BAMF championship adjudication over accepted C05 evidence and B13 custody."""
from __future__ import annotations

from dataclasses import asdict, replace
import time

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.capability_championship import (
    assessment_exam,
)
from bilqis_mlx.learning.capability_championship_state import (
    championship_epoch_identity, compact_championship_state,
    empty_championship_state, reset_championship_state,
    upgrade_championship_state, validate_championship_state,
)
from bilqis_mlx.runtime.capability_retention import Assessment, EvaluationCohort
from bilqis_mlx.runtime.retention.championship_evidence import capability_championship_evidence
from bilqis_mlx.runtime._factory_identity_evaluation import (
    _require_factory_evaluation,
)
from bilqis_mlx.semantics.domains import contract_digest
from ._championship_replay import (
    _accepted_ancestor, _current_binding, _incumbent_binding,
)
from ._championship_adjudication import adjudicate_measured_capability




def _invalid(reason):
    ErrorBus.raise_(SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID, reason=reason)


def _observe(observer, **fields):
    if observer is None:
        return
    try:
        observer(fields)
    except Exception:
        pass


_BOUNDARY_CUMULATIVE_FIELDS = frozenset({
    "championship_prepare_wall_seconds",
    "championship_solver_wall_seconds",
    "championship_candidate_wall_seconds",
    "championship_case_count",
    "championship_shared_backbone_launches",
    "championship_scalar_neural_launches",
})
_TRAINING_EXCLUSION_ARITY = 2


def _boundary_observer(observer):
    if observer is None:
        return None
    totals = {}

    def observe(fields):
        if not isinstance(fields, dict):
            return
        projected = {}
        for field, value in fields.items():
            if field in _BOUNDARY_CUMULATIVE_FIELDS and type(value) in (int, float):
                value = totals.get(field, 0) + value
                totals[field] = value
            projected[field] = value
        observer(projected)

    return observe


def championship_boundary_capabilities(selection, target_capability: str) -> tuple[str, ...]:
    """Return the current cadence phase only at its final accepted teaching attempt.

    Championship observation follows the already-authoritative active-grade cadence;
    it does not create an independent tournament cadence. Ordinary candidates with
    remaining phase work therefore carry no championship tail.
    """
    metadata = getattr(selection, "metadata", None)
    cadence = metadata.get("cadence") if isinstance(metadata, dict) else None
    if (not isinstance(cadence, dict)
            or cadence.get("schema")
            != "bilqis.bamf.active-grade-cadence-authorization/v1"
            or cadence.get("disposition") != "TEACHING"):
        return ()
    authorized = cadence.get("authorized_capability_ids")
    phase = cadence.get("phase_capability_ids")
    if (not isinstance(authorized, list) or authorized != [target_capability]
            or not isinstance(phase, list) or target_capability not in phase
            or not phase or len(set(phase)) != len(phase)
            or any(not isinstance(item, str) or not item for item in phase)):
        return ()
    return tuple(phase)


def _group_map(cohort: EvaluationCohort) -> dict[str, tuple[str, ...]]:
    groups = {}
    for capability, group in cohort.capability_groups:
        groups.setdefault(group, []).append(capability)
    return {group: tuple(capabilities) for group, capabilities in groups.items()}


def _release_group_map(source_context) -> dict[str, tuple[str, ...]]:
    """Compile the opaque current Factory capability census for sibling jurisdiction."""
    groups = {}
    for capability in source_context.release.execution_plan.capabilities:
        capability_id = getattr(capability, "capability_id", None)
        group_id = getattr(capability, "grade_id", None)
        if not isinstance(capability_id, str) or not capability_id or not isinstance(
                group_id, str) or not group_id:
            _invalid("BAMF_CHAMPIONSHIP_RELEASE_CAPABILITY_CENSUS_INVALID")
        groups.setdefault(group_id, []).append(capability_id)
    census = tuple(capability for members in groups.values() for capability in members)
    if not census or len(census) != len(set(census)):
        _invalid("BAMF_CHAMPIONSHIP_RELEASE_CAPABILITY_CENSUS_INVALID")
    return {group: tuple(members) for group, members in groups.items()}


def _epoch_identity(source_context, successor, cohort):
    release = source_context.release
    projections = release.execution_plan.projection_digests
    policy_sha256 = contract_digest({
        "schema": "bilqis.bamf.championship-policy/v1",
        "minimum_percent_exclusive": 90,
        "incumbent_defense": "STRICTLY_HIGHER",
        "tie_winner": "CHALLENGER",
    })
    return championship_epoch_identity(
        factory_release_sha256=release.release_sha256,
        semantic_catalog_sha256=release.semantic_catalog_sha256,
        curriculum_sha256=release.execution_plan.curriculum_sha256,
        capability_groups_sha256=projections.roster,
        fixed_cohort_sha256=projections.assessment,
        rubric_sha256=projections.assessment,
        scope_sha256=projections.coverage,
        source_sha256=projections.source,
        policy_sha256=policy_sha256,
        topology_sha256=successor.topology.digest,
        extents_sha256=successor.extents.digest,
        semantic_abi=successor.semantic_abi,
    )


def bind_accepted_championship_successor(
        run_dir, parent, cache, successor, source_context, artifact_path,
        target_capability, evaluation, *, checkpoint_origin_group,
        training=None, evidence_stage=None, observer=None,
        boundary_capabilities=None):
    """Run the explicit accepted-candidate championship boundary outside C05."""
    _require_factory_evaluation(evaluation)
    started = time.perf_counter()
    evidence_observer = _boundary_observer(observer)
    cohort = evaluation.championship_cohort
    assessment = evaluation.championship_assessment
    if (cohort is None) != (assessment is None):
        _invalid("BAMF_CHAMPIONSHIP_ACCEPTED_EVIDENCE_INVALID")
    if cohort is None:
        if (not isinstance(training, tuple)
                or len(training) != _TRAINING_EXCLUSION_ARITY
                or evidence_stage is None):
            _invalid("BAMF_CHAMPIONSHIP_BOUNDARY_CONTEXT_REQUIRED")
        cohort, assessment = capability_championship_evidence(
            source_context, successor, artifact_path, cache, target_capability,
            training, evidence_stage, observer=evidence_observer)
    if type(cohort) is not EvaluationCohort or type(assessment) is not Assessment:
        _invalid("BAMF_CHAMPIONSHIP_ACCEPTED_EVIDENCE_INVALID")
    groups_by_capability = dict(cohort.capability_groups)
    title_group = groups_by_capability.get(target_capability)
    if title_group is None:
        _invalid("BAMF_CHAMPIONSHIP_TARGET_GROUP_MISSING")
    if not isinstance(checkpoint_origin_group, str) or not checkpoint_origin_group:
        _invalid("BAMF_CHAMPIONSHIP_CHECKPOINT_ORIGIN_GROUP_REQUIRED")
    identity = _epoch_identity(source_context, successor, cohort)
    prior = parent.championship_state
    if prior is None:
        epoch = empty_championship_state(identity)
    else:
        prior = dict(prior)
        validate_championship_state(prior)
        prior = upgrade_championship_state(prior)
        epoch = (
            prior if prior["identity"] == identity
            else reset_championship_state(
                prior, identity,
                source_manifest_sha256=cache.accepted_manifest_sha256,
                source_generation=parent.generation,
            )
        )
    capability_groups = _release_group_map(source_context)
    decision = getattr(evaluation, "decision", None)
    measured_capabilities = tuple(boundary_capabilities or
        getattr(decision, "evaluated_capability_ids", ()) or (target_capability,))
    if (not measured_capabilities or len(set(measured_capabilities)) != len(
            measured_capabilities)):
        _invalid("BAMF_CHAMPIONSHIP_BOUNDARY_SCOPE_INVALID")
    if target_capability not in measured_capabilities:
        _invalid("BAMF_CHAMPIONSHIP_TARGET_EVIDENCE_MISSING")
    evidence = [(target_capability, cohort, assessment)]
    championship_training = (
        cohort.training_family_ids, cohort.training_episode_ids)
    for capability in measured_capabilities:
        if capability == target_capability:
            continue
        measured_cohort, measured_assessment = capability_championship_evidence(
            source_context, successor, artifact_path, cache, capability,
            championship_training, cohort.evidence_stage, observer=evidence_observer)
        evidence.append((capability, measured_cohort, measured_assessment))

    for capability, measured_cohort, measured_assessment in evidence:
        epoch = adjudicate_measured_capability(
            run_dir, parent, cache, successor, source_context, artifact_path,
            epoch, capability_groups, capability, measured_cohort,
            measured_assessment, checkpoint_origin_group)
    result = replace(
        successor,
        championship_state=compact_championship_state(epoch, identity),
    )
    _observe(
        observer,
        championship_wall_seconds=max(0.0, time.perf_counter() - started))
    return result
