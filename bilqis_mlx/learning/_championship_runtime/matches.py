"""Fresh championship battery inference, title matches, and fan-out screens."""
from __future__ import annotations

import bilqis_mlx.generated_assessment as _bilqis_mlx_generated_assessment
import bilqis_mlx.learning.championship_witnesses as _learning_championship_witnesses
import bilqis_mlx.learning.student_ops as _learning_student_ops
import bilqis_mlx.runtime.assessment as _runtime_assessment
import bilqis_mlx.runtime.mlx_checkpoint as _runtime_mlx_checkpoint
import bilqis_mlx.runtime.timing_trace as _runtime_timing_trace

from .witnesses import _fresh_title_current_exam, _readable_championship_rows


def _fresh_battery_results(mx, run_dir, receipt, role, parameters, graph):
    """Fresh model inference over one capability's surviving battery, with no answer cache."""
    selected_by_segment = {}
    batched_rows = []
    for segment in _learning_championship_witnesses.verified_battery(role):
        cohort = _runtime_assessment.load_championship_cohort(run_dir, segment)
        rows = {row["id"]: row for row in cohort.rows}
        selected = []
        for question in segment["questions"]:
            row = rows.get(question["id"])
            if (row is None or row["gold"] != question["gold"] or
                    row["capability"] != question["capability"]):
                raise ValueError("CHAMPIONSHIP_BATTERY_QUESTION_DRIFT")
            selected.append(row)
        readable = _readable_championship_rows(
            _bilqis_mlx_generated_assessment.make_cohort(selected, generator_version=cohort.generator_version,
                        seed=cohort.seed, rubric_version=cohort.rubric_version),
            graph, receipt)
        if len(readable) != len(selected):
            raise ValueError("CHAMPIONSHIP_BATTERY_CHECKPOINT_INCOMPARABLE")
        selected_by_segment[segment["sha256"]] = tuple(readable)
        batched_rows.extend(readable)
    if not batched_rows:
        return {}
    if len({row["id"] for row in batched_rows}) != len(batched_rows):
        raise ValueError("CHAMPIONSHIP_BATTERY_BATCH_DUPLICATE_QUESTION")
    config = (_learning_student_ops._compatible_answer_config(receipt["config"], graph)
              if any(row.get("answer_kind", "binary") != "binary"
                     for row in batched_rows)
              else receipt["config"])
    # Freshness is about when model answers are produced, not one device launch
    # per immutable evidence segment.  Verify every segment independently above,
    # then infer the complete title battery once and partition those fresh
    # answers back to their original segment receipts.
    with _runtime_timing_trace.trace_span(
            "CHAMPIONSHIP_BATTERY_INFERENCE",
            capability=role.get("capability"),
            battery_segments=len(selected_by_segment),
            battery_rows=len(batched_rows)):
        predictions = _learning_student_ops._predictions(
            mx, parameters, batched_rows, config, receipt["answer_ids"])
    return {
        sha256: [row["id"] for row in rows
                 if predictions[row["id"]] == row["gold"]]
        for sha256, rows in selected_by_segment.items()
    }


def _fresh_title_match(mx, run_dir, receipt, epoch, cohort, challenger,
                       parameters, graph, capability):
    """Put incumbent and contender through fresh current + historic battery inference."""
    role = epoch["active_roles"][capability]
    pointer = role["checkpoint"]
    path = run_dir / pointer["filename"]
    if (path.is_symlink() or path.parent != run_dir / "bundles" or
            not pointer["filename"].startswith("bundles/")):
        raise ValueError("CHAMPIONSHIP_TITLE_MATCH_UNSAFE_INCUMBENT")
    weights, own_adamw, meta, incumbent_graph = _runtime_mlx_checkpoint.load_semantically_bound_bundle(path)
    if (meta["safetensors_sha256"] != pointer["sha256"] or
            meta["optimizer_step"] != pointer["optimizer_step"] or
            not _learning_student_ops._compatible_graphs(incumbent_graph, graph)):
        raise ValueError("CHAMPIONSHIP_TITLE_MATCH_INCUMBENT_DRIFT")
    del own_adamw
    context = {key: challenger[key] for key in (
        "cohort_sha256", "rubric_sha256", "assessment_scope_sha256",
        "source_graph_sha256", "source_oracle_sha256",
        "cohort_rubric_sha256")}
    fresh_incumbent = _fresh_title_current_exam(
        mx, receipt, cohort, pointer, weights, incumbent_graph, context, capability)
    fresh_challenger = _fresh_title_current_exam(
        mx, receipt, cohort, challenger["checkpoint"], parameters, graph, context, capability)
    incumbent_battery = _fresh_battery_results(
        mx, run_dir, receipt, role, weights, incumbent_graph)
    challenger_battery = _fresh_battery_results(
        mx, run_dir, receipt, role, parameters, graph)
    del weights
    return {
        "incumbent_checkpoint_sha256": pointer["sha256"],
        "challenger_checkpoint_sha256": challenger["checkpoint"]["sha256"],
        "incumbent_current_exam": fresh_incumbent,
        "challenger_current_exam": fresh_challenger,
        "battery_results": {
            pointer["sha256"]: incumbent_battery,
            challenger["checkpoint"]["sha256"]: challenger_battery,
        },
    }


def _fresh_fanout_screen(mx, run_dir, receipt, epoch, cohort, challenger,
                         parameters, graph, capabilities):
    """Freshly pair the new champion with same-grade sibling incumbents once."""
    context = {key: challenger[key] for key in (
        "cohort_sha256", "rubric_sha256", "assessment_scope_sha256",
        "source_graph_sha256", "source_oracle_sha256",
        "cohort_rubric_sha256")}
    result = {}
    for capability in capabilities:
        role = epoch["active_roles"].get(capability)
        if role is None:
            continue
        pointer = role["checkpoint"]
        if pointer["sha256"] == challenger["checkpoint"]["sha256"]:
            continue
        path = run_dir / pointer["filename"]
        if (path.is_symlink() or path.parent != run_dir / "bundles" or
                not pointer["filename"].startswith("bundles/")):
            raise ValueError("CHAMPIONSHIP_FANOUT_UNSAFE_INCUMBENT")
        weights, own_adamw, meta, incumbent_graph = _runtime_mlx_checkpoint.load_semantically_bound_bundle(path)
        if (meta["safetensors_sha256"] != pointer["sha256"] or
                meta["optimizer_step"] != pointer["optimizer_step"] or
                not _learning_student_ops._compatible_graphs(incumbent_graph, graph)):
            raise ValueError("CHAMPIONSHIP_FANOUT_INCUMBENT_DRIFT")
        del own_adamw
        incumbent_exam = _fresh_title_current_exam(
            mx, receipt, cohort, pointer, weights, incumbent_graph, context, capability)
        challenger_exam = _fresh_title_current_exam(
            mx, receipt, cohort, challenger["checkpoint"], parameters, graph,
            context, capability)
        del weights
        result[capability] = {
            "incumbent_checkpoint_sha256": pointer["sha256"],
            "challenger_checkpoint_sha256": challenger["checkpoint"]["sha256"],
            "incumbent_exam": incumbent_exam,
            "challenger_exam": challenger_exam,
        }
    return result
