"""Qualify signed C06 priorities against admitted source offers and A09 planning."""
from dataclasses import dataclass
from bilqis_mlx.errors import ErrorBus, SCHOOL

from bilqis_mlx.factory.atlas_frontier_selection import FrontierDeltaSelection, validate_frontier_selection
from bilqis_mlx.factory.atlas_frontier_selection_validation import TargetDeltaProjection, validate_closure_structure
from bilqis_mlx.factory.atlas_frontier_progress_contracts import FrontierProgress
from bilqis_mlx.factory.atlas_frontier_closure import FrontierClosure
from bilqis_mlx.factory import candidate_realizations
from bilqis_mlx.learning.atlas_salience import derive_salience, rank_attention_options, verify_salience_inputs
from bilqis_mlx.learning.salience_contracts import ActionKind
from bilqis_mlx.learning.salience_history import completed_windows
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _accepted_correction_registry
from bilqis_mlx.semantics.domains import contract_digest

PRIORITY_OFFER_PAIR_WIDTH = 2


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


@dataclass(frozen=True)
class PriorityPlanningInput:
    progress: object
    closure: object
    selection: object | None
    selected_projection: object | None


@dataclass(frozen=True)
class QualifiedPriority:
    ranked: object
    offers: tuple
    holds: tuple


def _planning(planning, release):
    if type(planning) is not PriorityPlanningInput:
        _invalid('BAMF_PRIORITY_PLANNING_INVALID')
    progress, closure = planning.progress, planning.closure
    if (type(progress) is not FrontierProgress or type(closure) is not FrontierClosure
            or (planning.selection is not None and type(planning.selection) is not FrontierDeltaSelection)
            or (planning.selected_projection is not None and type(planning.selected_projection) is not TargetDeltaProjection)):
        _invalid('BAMF_PRIORITY_PLANNING_INVALID')
    progress.verify()
    closure.verify()
    snapshot = progress.input_snapshot
    if (closure.snapshot_sha256 != progress.input_snapshot_sha256
            or snapshot.admitted_factory_release_sha256 != release.release_sha256):
        _invalid('BAMF_PRIORITY_PLANNING_DRIFT')
    validate_closure_structure(snapshot, closure)
    selection, projection = planning.selection, planning.selected_projection
    if (selection is None) != (projection is None):
        _invalid('BAMF_PRIORITY_PLANNING_SELECTION_REQUIRED')
    if selection is not None:
        validate_frontier_selection(snapshot, closure, selection, release, projection)
        if progress.proposal_selection_sha256 != selection.selection_sha256:
            _invalid('BAMF_PRIORITY_PLANNING_SELECTION_DRIFT')
    elif progress.proposal_selection_sha256 is not None:
        _invalid('BAMF_PRIORITY_PLANNING_SELECTION_REQUIRED')


def _planning_hold(option, selection):
    if option.downstream_unlocks == 0:
        return False
    try:
        identity = candidate_realizations.realized_atlas_semantic_id(option.context.capability_id)
    except ValueError:
        return True
    return (selection is None or identity != selection.selected_semantic_id
            or option.downstream_unlocks != selection.downstream_unlocks)


def _grade(program, school, capability):
    grades = tuple(grade.id for grade in program.grades
                   if any(item.id == capability for item in grade.capabilities))
    return grades[0] if len(grades) == 1 and grades[0] in school.active_grades else None


def _verify_planning(planning, release, observer):
    if observer is None:
        _planning(planning, release)
        return
    from bilqis_mlx.factory.atlas_frontier_progress_metrics import (
        frontier_verification_measurement,
    )
    with frontier_verification_measurement(observer):
        _planning(planning, release)


def requalify_priority(run_dir, source_context, parent, frontier, history,
                       planning, offers, program, school, teacher_epoch, *, now,
                       planning_generation=None, planning_observer=None):
    from bilqis_mlx.runtime.priority_source_offer import PreparedPrioritySourceOffer

    if planning_generation is None:
        source_context.require_accepted_runtime(run_dir)
        cache, registry = _accepted_correction_registry(run_dir)
    else:
        from bilqis_mlx.runtime.priority_source_offer import _require_planning_generation
        cache, _authenticated = _require_planning_generation(
            planning_generation, source_context, parent)
        registry = cache._correction_registry
    if (frontier.snapshot.registry.digest != registry.digest
            or frontier.snapshot.as_of != now or school.course_digest != program.digest()):
        _invalid('BAMF_PRIORITY_AUTHORITY_DRIFT')
    _verify_planning(planning, source_context.release, planning_observer)
    completed_windows(history)
    evidence = dict(frontier.evidence)
    # Reverify every source fact and policy before applying per-option holds.
    for item in evidence.values():
        basis = item.basis
        verified = verify_salience_inputs(basis.facts, basis.policy, frontier.snapshot, basis.context)
        if derive_salience(verified) != item:
            _invalid('BAMF_PRIORITY_EVIDENCE_DRIFT')
    rank_attention_options(frontier.options, evidence, frontier.snapshot)
    if (type(offers) is not tuple
            or any(type(pair) is not tuple
            or len(pair) != PRIORITY_OFFER_PAIR_WIDTH
            or not isinstance(pair[0], str) or type(pair[1]) is not PreparedPrioritySourceOffer
            for pair in offers) or len(dict(offers)) != len(offers)
            or not set(dict(offers)).issubset({option.stable_id for option in frontier.options})):
        _invalid('BAMF_PRIORITY_OFFERS_INVALID')
    by_id = dict(offers)
    eligible, holds = [], []
    release = source_context.release
    for option in frontier.options:
        if option.action_kind not in (ActionKind.TEACHING, ActionKind.EXPLORATION):
            eligible.append(option)
            continue
        cap, context = option.context.capability_id, option.context
        offer = by_id.get(option.stable_id)
        if offer is None:
            holds.append((option.stable_id, 'SOURCE_OFFER_MISSING'))
            continue
        if (cap not in release.execution_plan.capability_map
                or cap not in release.curriculum.capability_map
                or cap not in release.source_bindings.by_capability
                or _grade(program, school, cap) is None):
            holds.append((option.stable_id, 'CAPABILITY_NOT_ADMITTED'))
            continue
        if (context.semantic_release != release.release_sha256
                or context.generation_digest != cache.generation_binding
                or context.teacher_epoch_digest != contract_digest(teacher_epoch)
                or context.source_binding_digest != contract_digest(release.source_bindings.by_capability[cap])
                or context.source_binding_digest != offer.source_binding_digest
                or context.source_family_id != offer.source_family_id
                or offer.source_family_id != offer.source_authority.source_family_id
                or offer.source_seed != offer.source_authority.seed
                or offer.source_each != offer.source_authority.each
                or cap != offer.capability_id or cap != offer.source_authority.capability_id
                or offer.release_sha256 != release.release_sha256
                or offer.accepted_manifest_sha256 != cache.accepted_manifest_sha256
                or offer.generation_binding != cache.generation_binding):
            _invalid('BAMF_PRIORITY_OFFER_IDENTITY_DRIFT')
        if _planning_hold(option, planning.selection):
            holds.append((option.stable_id, 'A09_PLANNING_UNAVAILABLE'))
            continue
        try:
            offer.require_qualified_current(source_context, parent)
        except ValueError:
            holds.append((option.stable_id, 'SOURCE_OFFER_HELD'))
            continue
        eligible.append(option)
    ranked = rank_attention_options(tuple(eligible),
        {option.stable_id: evidence[option.stable_id] for option in eligible}, frontier.snapshot)
    holds.extend(ranked.held)
    return QualifiedPriority(ranked, tuple((option.stable_id, by_id[option.stable_id])
        for option in eligible if option.stable_id in by_id), tuple(sorted(holds)))
