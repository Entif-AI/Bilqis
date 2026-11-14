"""Production C06 authority for ordinary grade-neutral BAMF teaching priority."""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.atlas_salience import derive_salience, verify_salience_inputs
from bilqis_mlx.learning.salience_contracts import (
    ActionKind, AttentionOption, AuthoritySnapshot, FactOrigin, Metric, MetricRule,
    NoveltyState, Ordinal, SalienceContext, SaliencePolicy, Signal, SignedFact,
)
from bilqis_mlx.learning.salience_history import (
    EventKind, SalienceEvent, SalienceHistory, WindowPolicy,
)
from bilqis_mlx.learning.salience_teacher import AttentionFrontier
from bilqis_mlx.learning.teacher_lineage import priority_rotation_state
from bilqis_mlx.runtime.priority_source_offer import prepare_priority_source_offer
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind, DependencyRef
from bilqis_mlx.semantics.domains import contract_digest
from .priority_planning_owner import priority_planning as _priority_planning
from .priority_rejection_replay import current_rejections as _current_rejections


_SCOPE = "factory/foundation"
_SOURCE_EACH = 1


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


@dataclass(frozen=True)
class AcceptedPriorityAuthority:
    frontier: AttentionFrontier
    history: SalienceHistory
    planning: object
    offers: tuple
    now: int


def _signed(record, signer, kind, key):
    dependency = DependencyRef(kind, key)
    return replace(record, signature_hex=signer.sign(dependency, record.signing_bytes()))


def _policy(release_sha256, families, now, signer):
    count_metrics = (Metric.DOWNSTREAM_COUNT, Metric.COVERAGE_COUNT,
                     Metric.BLOCKED_COUNT, Metric.REPAIR_COUNT)
    rules = (
        MetricRule(Metric.DECLARED_IMPACT, "ordinal-index", (1, 2, 3, 4),
                   tuple(Ordinal), "bamf/foundation/declared/v1"),
        MetricRule(Metric.DEADLINE_AT, "seconds-until-deadline", (1, 61, 3601),
                   (Ordinal.CRITICAL, Ordinal.HIGH, Ordinal.MODERATE, Ordinal.LOW),
                   "bamf/foundation/deadline/v1"),
        *(MetricRule(metric, "count", (1, 3, 8),
                    (Ordinal.LOW, Ordinal.MODERATE, Ordinal.HIGH, Ordinal.CRITICAL),
                    "bamf/foundation/" + metric.value + "/v1")
          for metric in count_metrics),
    )
    raw = SaliencePolicy(
        "bamf-foundation", "v1", release_sha256, tuple(sorted(set(families))), rules,
        ((NoveltyState.MATCHED, Ordinal.LOW),
         (NoveltyState.STRUCTURE_CHANGED, Ordinal.MODERATE),
         (NoveltyState.OUTCOME_CHANGED, Ordinal.HIGH),
         (NoveltyState.EXPECTED_MISSING, Ordinal.CRITICAL),
         (NoveltyState.REPORTED_NEGATIVE, Ordinal.LOW)),
        ((Signal.IMPACT, (Metric.DECLARED_IMPACT,)),
         (Signal.EXIGENCY, (Metric.BLOCKED_COUNT,)),
         (Signal.NOVELTY, (Metric.NOVELTY_COMPARISON,))),
        now, signer.owner_id, "0" * 128)
    return _signed(raw, signer, DependencyKind.POLICY,
                   "salience-policy:" + raw.policy_id)


def _unknown_fact(metric, context, policy, receipt, now, signer):
    fact_id = f"{context.capability_id}:{metric.value}"
    raw = SignedFact(
        fact_id, metric, 0, FactOrigin.SOURCE, context, policy.digest(), receipt,
        now, now, now, now, signer.owner_id, "0" * 128)
    return _signed(raw, signer, DependencyKind.SOURCE, "salience-fact:" + fact_id)


def _context(parent, offer, teacher_epoch_digest):
    binding = offer.source_binding_digest
    capability_epoch = contract_digest((
        "bilqis.bamf.c03.4-capability-epoch/v1", offer.release_sha256,
        offer.capability_id, binding))
    correction = parent.correction_frontier
    rights_epoch = correction.get("rights_epoch")
    correction_generation = correction.get("correction_generation")
    if (type(rights_epoch) is not int or rights_epoch < 0
            or type(correction_generation) is not int
            or correction_generation < 0):
        _invalid("BAMF_PRIORITY_CORRECTION_FRONTIER_INVALID")
    return SalienceContext(
        offer.release_sha256, binding, rights_epoch, correction_generation,
        offer.capability_id, capability_epoch,
        _SCOPE, offer.source_family_id, offer.generation_binding, teacher_epoch_digest)


def _offer_seed(next_seed: int, capability_id: str) -> int:
    raw = f"bilqis.bamf.c03.4-source-seed/v1|{next_seed}|{capability_id}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _planning_unlocks(capability_id, planning):
    selection = planning.selection
    if selection is None:
        return 0
    from bilqis_mlx.factory import candidate_realizations
    try:
        semantic_id = candidate_realizations.realized_atlas_semantic_id(capability_id)
    except ValueError:
        return 0
    return (selection.downstream_unlocks
            if semantic_id == selection.selected_semantic_id else 0)


def issue_foundation_priority_authority(
        run_dir, source_context, parent, teacher_epoch, atlas_artifact_path, *,
        teacher_state):
    """Issue only signed UNKNOWN salience; C06 ranking owns the resulting order."""
    from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _accepted_correction_registry
    from bilqis_mlx.runtime.bamf_bundle._darwin_salience_signer import (
        read_host_system_source_authority_signer,
    )
    cache, registry = _accepted_correction_registry(run_dir)
    signer = read_host_system_source_authority_signer(registry)
    next_seed = teacher_state.get("next_seed")
    if type(next_seed) is not int or next_seed < 0:
        _invalid("BAMF_PRIORITY_TEACHER_SEED_INVALID")
    counter, last_selected = priority_rotation_state(teacher_state)
    planning = _priority_planning(run_dir, source_context, atlas_artifact_path)
    offers = tuple((capability.capability_id, prepare_priority_source_offer(
        source_context, parent, atlas_artifact_path,
        capability=capability.capability_id,
        source_seed=_offer_seed(next_seed, capability.capability_id),
        source_each=_SOURCE_EACH))
        for capability in source_context.release.execution_plan.capabilities)
    rejections = _current_rejections(run_dir, parent, cache)
    option_ids = {capability for capability, _ in offers}
    if any(capability not in option_ids for capability, *_ in rejections):
        _invalid("BAMF_PRIORITY_REJECTION_OPTION_DRIFT")
    rejection_recency = {}
    for offset, (capability, *_rest) in enumerate(rejections, start=1):
        rejection_recency[capability] = counter + offset
    now = counter + len(rejections)
    policy = _policy(source_context.release.release_sha256,
                     (offer.source_family_id for _, offer in offers), now, signer)
    teacher_digest = contract_digest(teacher_epoch)
    contexts = tuple(_context(parent, offer, teacher_digest) for _, offer in offers)
    snapshot = AuthoritySnapshot(contexts, now, registry)
    options, evidence_rows = [], []
    for context, (stable_id, offer) in zip(contexts, offers, strict=True):
        facts = tuple(_unknown_fact(metric, context, policy,
                                    offer.source_authority.content_sha256,
                                    now, signer)
                      for metric in (Metric.IMPACT_UNKNOWN,
                                     Metric.EXIGENCY_UNKNOWN,
                                     Metric.NOVELTY_UNKNOWN))
        evidence = derive_salience(verify_salience_inputs(
            facts, policy, snapshot, context))
        option = AttentionOption(
            stable_id, context, evidence.basis.digest(), ActionKind.TEACHING,
            max(last_selected.get(stable_id, 0), rejection_recency.get(stable_id, 0)),
            True, True, True, True, _planning_unlocks(stable_id, planning),
            False, False, signer.owner_id, "0" * 128)
        option = _signed(option, signer, DependencyKind.ARTIFACT,
                         "salience-option:" + stable_id)
        options.append(option)
        evidence_rows.append((stable_id, evidence))
    window = WindowPolicy(
        "bamf-foundation-window", "v1", policy.digest(),
        source_context.release.release_sha256, 2, now,
        signer.owner_id, "0" * 128)
    window = _signed(window, signer, DependencyKind.POLICY,
                     "salience-policy:" + window.policy_id)
    evidence_by_id = dict(evidence_rows)
    history_events = []
    for stable_id, visit_id, reason, receipt_sha256 in rejections:
        raw = SalienceEvent(
            "bamf-rejection:" + receipt_sha256, EventKind.OBSERVATION,
            f"{cache.run_id}:{cache.generation}:{cache.accepted_manifest_sha256}",
            visit_id,
            contract_digest(("bilqis.bamf.c16.3-rejection-observation/v1",
                             stable_id, reason)),
            None, evidence_by_id[stable_id], now, receipt_sha256,
            None, None, None, None, None, None,
            signer.owner_id, "0" * 128)
        history_events.append(_signed(
            raw, signer, DependencyKind.ARTIFACT,
            "salience-event:" + raw.event_id))
    return AcceptedPriorityAuthority(
        AttentionFrontier(tuple(options), tuple(evidence_rows), snapshot),
        SalienceHistory(window, tuple(history_events)), planning, offers, now)


__all__ = ("AcceptedPriorityAuthority", "issue_foundation_priority_authority")
