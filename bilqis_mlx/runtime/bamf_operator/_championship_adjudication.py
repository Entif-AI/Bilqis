"""Fresh defended-match and bounded one-hop fan-out orchestration."""
from __future__ import annotations

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.capability_championship import assessment_exam, fresh_title_match
from bilqis_mlx.learning.epoch_championships import advance_epoch, needed_incumbents
from bilqis_mlx.runtime.retention.championship_evidence import (
    capability_championship_evidence,
)

from ._championship_replay import _current_binding, _incumbent_binding


MAX_ADJUDICATION_ROUNDS = 8


def _invalid(reason):
    ErrorBus.raise_(SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID, reason=reason)


def _resolve_current_cohort(cohort):
    from bilqis_mlx.learning.capability_championship import _source_context
    expected = _source_context(cohort)

    def resolve(key):
        if dict(key) != {name: expected[name] for name, _ in key}:
            _invalid("BAMF_CHAMPIONSHIP_BATTERY_CONTEXT_DRIFT")
        return cohort

    return resolve


def _fresh_exam(binding, cohort, group):
    return assessment_exam(binding.measure(cohort), binding, challenge_group=group)


def _adjudicate_group(
        epoch, capability_groups, group, challenger_exam, challenger_binding,
        incumbent_bindings, cohort, *, fanout_provider):
    incumbent_exams = {
        sha256: _fresh_exam(binding, cohort, group)
        for sha256, binding in incumbent_bindings.items()
    }
    title_matches = {}
    fanout_screen = None
    fanout_contexts = {}
    for _ in range(MAX_ADJUDICATION_ROUNDS):
        proposed, _, decisions = advance_epoch(
            epoch, capability_groups=capability_groups,
            challenger_exam=challenger_exam,
            incumbent_exams=incumbent_exams,
            title_matches=title_matches,
            fanout_screen=fanout_screen,
        )
        screen = next((item for item in decisions
                       if item.get("decision") == "FANOUT_SCREEN_REQUIRED"), None)
        if screen is not None:
            if fanout_screen is not None:
                _invalid("BAMF_CHAMPIONSHIP_FANOUT_RECURSION")
            fanout_screen = {}
            for capability in screen["capabilities"]:
                role = epoch["active_roles"][capability]
                sibling_cohort, sibling_challenger, incumbent = fanout_provider(
                    capability, role)
                challenger_fresh = _fresh_exam(sibling_challenger, sibling_cohort, group)
                incumbent_exam = _fresh_exam(incumbent, sibling_cohort, group)
                fanout_contexts[capability] = (
                    sibling_cohort, sibling_challenger, incumbent)
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
            } and item["capability"] not in title_matches)
        if not pending:
            return proposed
        for capability in pending:
            role = epoch["active_roles"][capability]
            match_cohort = cohort
            match_challenger = challenger_binding
            incumbent = incumbent_bindings.get(role["checkpoint"]["sha256"])
            if capability in fanout_contexts:
                match_cohort, match_challenger, incumbent = fanout_contexts[capability]
            if incumbent is None:
                _invalid("BAMF_CHAMPIONSHIP_INCUMBENT_BINDING_MISSING")
            title_matches[capability] = fresh_title_match(
                role, incumbent, match_challenger, match_cohort,
                resolve_cohort=_resolve_current_cohort(match_cohort),
                settled_matchups=epoch.get("settled_matchups", {}),
                challenge_group=group,
                comparison_context_sha256=epoch.get("comparison_context_sha256"),
            )
    _invalid("BAMF_CHAMPIONSHIP_ADJUDICATION_RECURSION")


def adjudicate_measured_capability(
        run_dir, parent, cache, successor, source_context, artifact_path,
        epoch, capability_groups, capability, cohort, assessment,
        checkpoint_origin_group):
    title_group = dict(cohort.capability_groups).get(capability)
    if (title_group is None
            or capability not in capability_groups.get(title_group, ())):
        _invalid("BAMF_CHAMPIONSHIP_TARGET_GROUP_DRIFT")
    challenger = _current_binding(
        source_context, artifact_path, run_dir, source_context.release,
        parent, cache, successor, cohort, assessment, checkpoint_origin_group)

    def fanout_provider(sibling, role):
        sibling_cohort, sibling_assessment = capability_championship_evidence(
            source_context, successor, artifact_path, cache, sibling,
            (cohort.training_family_ids, cohort.training_episode_ids),
            cohort.evidence_stage)
        sibling_group = dict(sibling_cohort.capability_groups).get(sibling)
        if sibling_group != title_group:
            _invalid("BAMF_CHAMPIONSHIP_FANOUT_GROUP_DRIFT")
        sibling_challenger = _current_binding(
            source_context, artifact_path, run_dir, source_context.release,
            parent, cache, successor, sibling_cohort, sibling_assessment,
            checkpoint_origin_group)
        sibling_incumbent = _incumbent_binding(
            source_context, artifact_path, run_dir, source_context.release,
            parent, cache, sibling_cohort, role)
        return sibling_cohort, sibling_challenger, sibling_incumbent

    challenger_exam = assessment_exam(assessment, challenger, challenge_group=title_group)
    incumbent_bindings = {}
    for sha256 in needed_incumbents(
            epoch, capability_groups=capability_groups,
            challenger_exam=challenger_exam):
        role = next(role for role in epoch.get("active_roles", {}).values()
                    if role["checkpoint"]["sha256"] == sha256)
        incumbent_bindings[sha256] = _incumbent_binding(
            source_context, artifact_path, run_dir, source_context.release,
            parent, cache, cohort, role)
    return _adjudicate_group(
        epoch, capability_groups, title_group, challenger_exam, challenger,
        incumbent_bindings, cohort, fanout_provider=fanout_provider)


__all__ = ("adjudicate_measured_capability",)
