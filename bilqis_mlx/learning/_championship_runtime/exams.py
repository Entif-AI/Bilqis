"""Comparable incumbent and epoch examination construction."""
from __future__ import annotations

import dataclasses as _dataclasses

from bilqis_mlx.errors import ErrorBus, SCHOOL
import bilqis_mlx.curriculum.scheduler as _curriculum_scheduler
import bilqis_mlx.factory.schedule as _factory_schedule
import bilqis_mlx.generated_assessment as _bilqis_mlx_generated_assessment
import bilqis_mlx.learning.capability_frontier as _learning_capability_frontier
import bilqis_mlx.learning.epoch_championships as _learning_epoch_championships
import bilqis_mlx.learning.student_ops as _learning_student_ops
import bilqis_mlx.runtime.admission as _runtime_admission
import bilqis_mlx.runtime.mlx_checkpoint as _runtime_mlx_checkpoint
import bilqis_mlx.runtime.state as _runtime_state

from .witnesses import (
    _championship_correct_questions, _championship_questions,
    _readable_championship_rows,
)


def _invalid(reason):
    ErrorBus.raise_(SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID, reason=reason)


def _compare_incumbents(mx, run_dir, receipt, cohort, config, answer_ids, graph):
    """Replay every unique historical and current leader on this exact cohort."""
    historic = receipt.get("historical_capability_best", {}) if receipt.get(
        "legacy_frontier_pending_replay") else {}
    epoch = receipt.get("mentor_epoch")
    current = (
        _learning_epoch_championships.active_frontier(epoch)
        if epoch is not None else
        _learning_capability_frontier.qualified_frontier(
            receipt.get("capability_best", {})))
    references = list(current.values())
    if epoch is None:
        references += list(historic.values())
        references += list(receipt.get("graduation_perfect", {}).values())
        # Legacy pre-epoch runs used graduated-grade checkpoint pointers as
        # frozen championship incumbents.  Once mentor_epoch exists, those
        # pointers are graduation-status metadata only and must not survive a
        # new-semantic reset as championship authority.
        references.extend({"checkpoint": p} for p in
                          receipt["school"]["champions"].values())
    unique = {}
    for item in references:
        pointer = item["checkpoint"]
        unique[pointer["sha256"]] = pointer
    best = {}
    comparisons = []
    for sha, pointer in sorted(unique.items()):
        path = run_dir / pointer["filename"]
        if (path.parent != run_dir / "bundles" or path.is_symlink()):
            raise ValueError("HUMAN_TRAINER_INCUMBENT_UNSAFE_PATH")
        weights, own_optimizer, meta, loaded_graph = _runtime_mlx_checkpoint.load_semantically_bound_bundle(path)
        if (not _learning_student_ops._compatible_graphs(loaded_graph, graph) or meta["safetensors_sha256"] != sha or
                meta["optimizer_step"] != pointer["optimizer_step"]):
            raise ValueError("HUMAN_TRAINER_INCUMBENT_CHECKPOINT_DRIFT")
        supported = {cap for cap in {r["capability"] for r in cohort.rows}
            if all(max(r["tokens"]) < len(loaded_graph["tokens"])
                   for r in cohort.rows if r["capability"] == cap)}
        readable = tuple(r for r in cohort.rows if r["capability"] in supported)
        if not readable:
            continue
        subset = _bilqis_mlx_generated_assessment.make_cohort(readable, generator_version=cohort.generator_version,
                             seed=cohort.seed, rubric_version=cohort.rubric_version)
        guesses = _learning_student_ops._predictions(mx, weights, readable,
            _learning_student_ops._compatible_answer_config(config, loaded_graph), answer_ids)
        measured = _bilqis_mlx_generated_assessment.score(subset, guesses, pointer)
        comparisons.append({"checkpoint": dict(pointer),
                            "cohort_sha256": cohort.digest,
                            "scored_capabilities": sorted(supported),
                            "unsupported_capabilities": sorted(
                                {r["capability"] for r in cohort.rows}-supported),
                            "scores": measured["scores"]})
        for cap, value in measured["scores"].items():
            prior = best.get(cap)
            if prior is None or value["correct"] > prior["correct"]:
                best[cap] = {"rubric": receipt["live_rubric_sha256"],
                             "capability": cap, **value, "checkpoint": dict(pointer),
                             "evaluation_id": "same-cohort-incumbent/" + cohort.digest}
        del weights, own_optimizer
    frontier = {item["rubric"] + ":" + cap: item for cap, item in best.items()}
    return frontier, comparisons


def _epoch_exam_context(
        run_dir, receipt, course, school, cohort, scores, graph, challenge_group):
    epoch = receipt["mentor_epoch"]
    if epoch["source_graph_sha256"] != _runtime_state._fingerprint(graph):
        raise ValueError("CHAMPIONSHIP_EPOCH_SOURCE_GRAPH_DRIFT")
    if (epoch.get("championship_school_identity") !=
            receipt.get("championship_school_identity")):
        raise ValueError("CHAMPIONSHIP_EPOCH_SCHOOL_IDENTITY_RESET_REQUIRED")
    executable_release = _runtime_admission._read_executable_factory_release_artifact(
        run_dir, receipt)
    program = _factory_schedule.schedule_program_from_executable_release(executable_release)
    capability_groups = {
        grade.id: tuple(capability.id for capability in grade.capabilities)
        for grade in program.grades}
    allowed_scope = _curriculum_scheduler.assessment_capabilities(program, school)
    materialized = tuple(dict.fromkeys(row["capability"] for row in cohort.rows))
    if (not materialized or set(scores) != set(materialized) or
            not set(materialized) <= set(allowed_scope)):
        raise ValueError("CHAMPIONSHIP_EPOCH_INCOMPLETE_EXAM")
    scope = tuple(cap for cap in allowed_scope if cap in set(materialized))
    from bilqis_mlx.factory.assessment import assessment_scope_contract
    rubric = assessment_scope_contract(
        executable_release, scope).rubric_sha256
    cohort_rubric = cohort.rubric_version
    checkpoint_origin_group = receipt.get(
        "championship_checkpoint_origins", {}).get(school.current_student.sha256)
    if challenge_group not in capability_groups:
        _invalid("CHAMPIONSHIP_EPOCH_CHALLENGE_GROUP_INVALID")
    if not any(capability in scores for capability in capability_groups[challenge_group]):
        _invalid("CHAMPIONSHIP_EPOCH_CHALLENGE_GROUP_UNMEASURED")
    context = {
        "cohort_sha256": cohort.digest,
        "rubric_sha256": rubric,
        "cohort_rubric_sha256": cohort_rubric,
        "assessment_scope_sha256": _runtime_state._fingerprint(scope),
        "source_graph_sha256": _runtime_state._fingerprint(graph),
        "source_oracle_sha256": receipt["source_manifest_sha256"],
        # Capability IDs own titles. Group is explicit Factory/curriculum
        # grouping context only; the checkpoint's optimizer origin is provenance.
        "challenge_group": challenge_group,
        "checkpoint_origin_group": checkpoint_origin_group,
    }
    return capability_groups, challenge_group, context


def _load_epoch_incumbent_exam(
        mx, run_dir, receipt, cohort, graph, capability_groups, group, context,
        sha, pointer,
):
    path = run_dir / pointer["filename"]
    if (path.is_symlink() or path.parent != run_dir / "bundles" or
            not pointer["filename"].startswith("bundles/")):
        raise ValueError("CHAMPIONSHIP_EPOCH_UNSAFE_INCUMBENT")
    weights, own_adamw, meta, loaded_graph = (
        _runtime_mlx_checkpoint.load_semantically_bound_bundle(path))
    if (meta["safetensors_sha256"] != sha or
            meta["optimizer_step"] != pointer["optimizer_step"] or
            not _learning_student_ops._compatible_graphs(loaded_graph, graph)):
        raise ValueError("CHAMPIONSHIP_EPOCH_INCOMPARABLE_INCUMBENT_GRAPH")
    del own_adamw
    challenge_caps = set(capability_groups[group])
    group_rows = tuple(
        row for row in cohort.rows if row["capability"] in challenge_caps)
    group_cohort = _bilqis_mlx_generated_assessment.make_cohort(
        group_rows, generator_version=cohort.generator_version,
        seed=cohort.seed, rubric_version=cohort.rubric_version)
    readable = _readable_championship_rows(group_cohort, loaded_graph, receipt)
    subset = (
        _bilqis_mlx_generated_assessment.make_cohort(
            readable, generator_version=cohort.generator_version,
            seed=cohort.seed, rubric_version=cohort.rubric_version)
        if readable else None)
    config = (
        _learning_student_ops._compatible_answer_config(
            receipt["config"], loaded_graph)
        if any(row.get("answer_kind", "binary") != "binary" for row in readable)
        else receipt["config"])
    predictions = (
        _learning_student_ops._predictions(
            mx, weights, readable, config, receipt["answer_ids"])
        if readable else {})
    measured = (
        _bilqis_mlx_generated_assessment.score(subset, predictions, pointer)
        if subset else {"scores": {}})
    result = {
        **context,
        "checkpoint": dict(pointer),
        "checkpoint_graph_sha256": _runtime_state._fingerprint(loaded_graph),
        "scored_subset_sha256": subset.digest if subset else None,
        "scores": measured["scores"],
        "questions": _championship_questions(subset) if subset else {},
        "correct_questions": (
            _championship_correct_questions(subset, predictions)
            if subset else {}),
    }
    del weights
    return result


def _epoch_paired_examinations(mx, run_dir, receipt, course, school,
                               cohort, scores, predictions, graph, *,
                               challenge_group):
    """Re-examine only potentially displaced epoch incumbents on these rows."""
    epoch = receipt["mentor_epoch"]
    capability_groups, group, context = _epoch_exam_context(
        run_dir, receipt, course, school, cohort, scores, graph, challenge_group)
    challenger = {**context, "checkpoint": _dataclasses.asdict(school.current_student),
                  "scores": scores,
                  "questions": _championship_questions(cohort),
                  "correct_questions": _championship_correct_questions(cohort, predictions)}
    requested = _learning_epoch_championships.needed_incumbents(
        epoch, capability_groups=capability_groups, challenger_exam=challenger)
    incumbents = {}
    for sha, pointer in sorted(requested.items()):
        if sha == school.current_student.sha256:
            incumbents[sha] = challenger
            continue
        incumbents[sha] = _load_epoch_incumbent_exam(
            mx, run_dir, receipt, cohort, graph, capability_groups, group, context,
            sha, pointer)
    return capability_groups, challenger, incumbents
