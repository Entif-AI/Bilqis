"""Championship question evidence and earning-witness hydration."""
from __future__ import annotations

import copy as _copy

import bilqis_mlx.generated_assessment as _bilqis_mlx_generated_assessment
import bilqis_mlx.learning.championship_witnesses as _learning_championship_witnesses
import bilqis_mlx.learning.lesson_guidance as _learning_lesson_guidance
import bilqis_mlx.learning.student_ops as _learning_student_ops
import bilqis_mlx.runtime.assessment as _runtime_assessment
import bilqis_mlx.runtime.state as _runtime_state


def _readable_championship_rows(cohort, graph, receipt):
    """A prefix incumbent must answer each entire comparable capability panel."""
    vocabulary = len(graph["tokens"])
    unsupported = set()
    for row in cohort.rows:
        kind = row.get("answer_kind", "binary")
        answers = (receipt["answer_ids"] if kind == "binary" else
                   receipt["config"].get("answer_heads", {}).get(kind, {}).get("token_ids", ()))
        if max(row["tokens"]) >= vocabulary or not answers or max(answers) >= vocabulary:
            unsupported.add(row["capability"])
    return tuple(row for row in cohort.rows if row["capability"] not in unsupported)


def _championship_correct_questions(cohort, predictions):
    return {cap: [{"id": row["id"], "gold": row["gold"]}
                  for row in cohort.rows
                  if row["capability"] == cap and predictions[row["id"]] == row["gold"]]
            for cap in {row["capability"] for row in cohort.rows}}


def _championship_questions(cohort):
    return {cap: [{"id": row["id"], "gold": row["gold"]}
                  for row in cohort.rows if row["capability"] == cap]
            for cap in {row["capability"] for row in cohort.rows}}


def _hydrate_championship_witnesses(mx, run_dir, receipt, epoch, graph):
    """Recover legacy earning questions from their immutable cohort and owner."""
    updated = _copy.deepcopy(epoch)
    recovered = {}
    for role in updated.get("active_roles", {}).values():
        if _learning_championship_witnesses.verified_witnesses(role):
            continue
        context = {
            "cohort_sha256": role["cohort_sha256"], "rubric_sha256": role["rubric"],
            "cohort_rubric_sha256": role.get(
                "cohort_rubric_sha256", role["rubric"]),
            "source_oracle_sha256": receipt["source_manifest_sha256"],
        }
        pointer = role["checkpoint"]
        identity = (pointer["sha256"], context["cohort_sha256"])
        if identity not in recovered:
            cohort = _runtime_assessment.load_championship_cohort(run_dir, context)
            context["assessment_scope_sha256"] = role.get(
                "assessment_scope_sha256", _runtime_state._fingerprint(tuple(dict.fromkeys(
                    row["capability"] for row in cohort.rows))))
            path = run_dir / pointer["filename"]
            if path.is_symlink() or path.parent != run_dir / "bundles":
                raise ValueError("CHAMPIONSHIP_EARNING_CHECKPOINT_UNSAFE")
            content = (path / "model-and-own-adamw.safetensors").stat()
            weights, source_graph = _learning_lesson_guidance._cached_frozen_champion(
                str(path), pointer["sha256"], pointer["optimizer_step"],
                content.st_size, content.st_mtime_ns)
            if not _learning_student_ops._compatible_graphs(source_graph, graph):
                raise ValueError("CHAMPIONSHIP_EARNING_GRAPH_DRIFT")
            context["source_graph_sha256"] = _runtime_state._fingerprint(source_graph)
            config = (_learning_student_ops._compatible_answer_config(receipt["config"], source_graph)
                      if any(row.get("answer_kind", "binary") != "binary" for row in cohort.rows)
                      else receipt["config"])
            guesses = _learning_student_ops._predictions(mx, weights, list(cohort.rows),
                                   config, receipt["answer_ids"])
            measured = _bilqis_mlx_generated_assessment.score(cohort, guesses, pointer)
            recovered[identity] = {
                **context, "scores": measured["scores"],
                "questions": _championship_questions(cohort),
                "correct_questions": _championship_correct_questions(cohort, guesses)}
        earned = recovered[identity]
        if earned["scores"][role["capability"]] != {
                "correct": role["correct"], "total": role["total"]}:
            raise ValueError("CHAMPIONSHIP_EARNING_SCORE_DRIFT")
        role["qualification_witnesses"] = [_learning_championship_witnesses.earning_witness(earned, tuple(earned["scores"]))]
    return updated


def _fresh_title_current_exam(mx, receipt, cohort, pointer, parameters, graph, context,
                              capability):
    """Freshly replay the current cohort; title adjudication never reuses model answers."""
    panel_rows = [row for row in cohort.rows if row["capability"] == capability]
    if not panel_rows:
        raise ValueError("CHAMPIONSHIP_TITLE_MATCH_CURRENT_PANEL_UNMEASURED")
    panel = _bilqis_mlx_generated_assessment.make_cohort(
        panel_rows,
        generator_version=cohort.generator_version, seed=cohort.seed,
        rubric_version=cohort.rubric_version)
    readable = _readable_championship_rows(panel, graph, receipt)
    if len(readable) != len(panel.rows):
        raise ValueError("CHAMPIONSHIP_TITLE_MATCH_CURRENT_PANEL_INCOMPARABLE")
    subset = _bilqis_mlx_generated_assessment.make_cohort(readable, generator_version=cohort.generator_version,
                         seed=cohort.seed, rubric_version=cohort.rubric_version)
    config = (_learning_student_ops._compatible_answer_config(receipt["config"], graph)
              if any(row.get("answer_kind", "binary") != "binary" for row in readable)
              else receipt["config"])
    predictions = _learning_student_ops._predictions(mx, parameters, readable, config, receipt["answer_ids"])
    measured = _bilqis_mlx_generated_assessment.score(subset, predictions, pointer)
    return {
        **context, "checkpoint": dict(pointer), "scores": measured["scores"],
        "questions": _championship_questions(subset),
        "correct_questions": _championship_correct_questions(subset, predictions),
    }
