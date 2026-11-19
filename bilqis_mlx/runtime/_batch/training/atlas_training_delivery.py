"""Bounded microbatch delivery, backend dispatch and observed teacher attribution."""
from __future__ import annotations

from dataclasses import replace

from .atlas_training_contracts import (
    PaddedMicrobatch, _invalid, _freeze, _reissue_training_batch,
    require_current_release,
)

MAX_COMPILED_CONTEXT_POSITIONS = 1024
AUXILIARY_EVIDENCE_ARITY = 3


def pad_microbatches(batch, topology, memory_budget, *, plan_microbatches, indices_for_plan, positions_for):
    """Consume C08's partition; preserve every logical row and actual lengths."""
    plan = plan_microbatches(batch.rows, topology, memory_budget)
    groups = tuple(tuple(group) for group in indices_for_plan(plan))
    flattened = tuple(index for group in groups for index in group)
    if (not groups or any(not group for group in groups) or
            any(type(index) is not int for index in flattened) or
            flattened != tuple(range(len(batch.rows)))):
        _invalid('MICROBATCH_PARTITION_INVALID')
    result = []
    for group in groups:
        rows = tuple(tuple(positions_for(batch.rows[index].model_input.prefix)) for index in group)
        if any(not row or len(row) + dict(batch.rows[index].model_input.answer_plan)['maximum_decisions'] > MAX_COMPILED_CONTEXT_POSITIONS
               for index, row in zip(group, rows)):
            _invalid('COMPILED_CONTEXT_INVALID')
        width = max(map(len, rows))
        result.append(PaddedMicrobatch(group,
            tuple(row + (None,) * (width - len(row)) for row in rows),
            tuple((True,) * len(row) + (False,) * (width - len(row)) for row in rows)))
    return tuple(result)


def attach_auxiliaries(batch, evidence_by_row, *, verify):
    """Keep absent labels absent; require the source/outcome owner's verification."""
    known = {row.provenance.row_id for row in batch.rows}
    if not isinstance(evidence_by_row, dict) or not set(evidence_by_row) <= known:
        _invalid('AUXILIARY_EVIDENCE_INVALID')
    result = []
    for row in batch.rows:
        labels = evidence_by_row.get(row.provenance.row_id, {})
        if not isinstance(labels, dict):
            _invalid('AUXILIARY_EVIDENCE_INVALID')
        targets = []
        for name, evidence in sorted(labels.items()):
            if name == 'frame_atomic_consistency':
                _invalid('TRAINING_OBJECTIVE_FRAME_ATOMIC_KERNEL_UNAVAILABLE')
            if (name not in {'role', 'epistemic_state', 'impact', 'exigency', 'novelty'}
                    or not isinstance(evidence, (tuple, list)) or len(evidence) != AUXILIARY_EVIDENCE_ARITY):
                _invalid('AUXILIARY_EVIDENCE_INVALID')
            value, regime, receipt = evidence
            if regime not in ('SOURCE', 'OUTCOME') or not receipt or verify(row.provenance.row_id, name, value, regime, receipt) is not True:
                _invalid('AUXILIARY_EVIDENCE_UNVERIFIED')
            targets.append((name, _freeze(value), regime, _freeze(receipt)))
        result.append(replace(row, auxiliaries=tuple(targets)))
    return _reissue_training_batch(batch, rows=tuple(result))


def execute_with_backend(batch, source_context, topology, *, generation_binding, training, model_backend, invoke):
    """Use B11's single selector; inference receives no gold or auxiliary targets."""
    require_current_release(batch, source_context, generation_binding=generation_binding)
    if type(training) is not bool:
        _invalid('EXECUTION_MODE_INVALID')
    backend = model_backend(topology)
    inputs = tuple(row.model_input for row in batch.rows)
    targets = tuple((row.target, row.native_target, row.auxiliaries) for row in batch.rows) if training else None
    return invoke(backend, inputs, targets)


def capture_realized_delivery(batch, source_context, capture, capability, step, rows, *,
                              generation_binding, option_rows, priority, preservation, support,
                              enrichment, guidance, controls, seed, cost, prior=(), mentors=None):
    """Forward actual delivery and measured cost to the existing #333 owner."""
    from bilqis_mlx.factory.teaching import content_digest
    require_current_release(batch, source_context, generation_binding=generation_binding)
    if (type(step) is not int or step < 1 or content_digest(rows) != batch.delivered_content_sha256
            or tuple(row.get('id') for row in rows) != tuple(row.provenance.row_id for row in batch.rows)
            or not isinstance(controls, dict) or 'realized_cost' in controls
            or not isinstance(cost, dict) or not cost):
        _invalid('OBSERVATION_DELIVERY_INVALID')
    capture.delivery(source_context.release, capability, step, rows, option_rows=option_rows,
        priority=priority, preservation=preservation, support=support, enrichment=enrichment,
        guidance=guidance, controls={**controls, 'realized_cost': cost,
                                    'delivered_content_sha256': content_digest(rows)},
        seed=seed, prior=prior, mentors=mentors)


def require_independent_cohorts(training, holdout):
    """Refuse missing provenance and known family/episode siblings as independent."""
    def identities(batch):
        families, episodes = set(), set()
        for row in batch.rows:
            family, episode = row.provenance.source_family_id, row.provenance.episode_id
            if not family or not episode:
                _invalid('SOURCE_INDEPENDENCE_NOT_MEASURED')
            families.add(family)
            episodes.add(episode)
        return families, episodes
    train_families, train_episodes = identities(training)
    test_families, test_episodes = identities(holdout)
    if train_families & test_families or train_episodes & test_episodes:
        _invalid('SOURCE_FAMILY_LEAK')


def resolve_batch_rules(batch, source_context, *, released_signatures_for, rule_set_for):
    """Dispatch source-domain rules from released signatures without grade metadata."""
    require_current_release(batch, source_context, generation_binding=batch.generation_binding)
    release = source_context.release
    result = []
    for row in batch.rows:
        family = row.provenance.source_family_id
        if not family:
            _invalid('RULE_SOURCE_FAMILY_REQUIRED')
        capability = release.curriculum.capability_map[row.provenance.capability_id]
        binding = release.source_bindings.by_capability[row.provenance.capability_id]
        signatures = _freeze(released_signatures_for(release, source_context.graph, capability.taught_roots))
        if not signatures:
            _invalid('RELEASED_SIGNATURES_REQUIRED')
        policy = _freeze(rule_set_for(binding.source_anchor, signatures, family))
        if not isinstance(policy, tuple) or not policy:
            _invalid('SOURCE_RULE_POLICY_REQUIRED')
        result.append(replace(row, rule_policy=policy))
    return _reissue_training_batch(batch, rows=tuple(result))
