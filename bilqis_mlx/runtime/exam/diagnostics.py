"""Read-only paired-checkpoint diagnostics for school exams."""
from __future__ import annotations

import dataclasses as _dataclasses

import bilqis_mlx.generated_assessment as _bilqis_mlx_generated_assessment
import bilqis_mlx.learning.champions as _learning_champions
import bilqis_mlx.learning.student_ops as _learning_student_ops
import bilqis_mlx.runtime.mlx_checkpoint as _runtime_mlx_checkpoint


def _score_parent_for_paired_s3(mx, run_dir, receipt, parent, cohort, graph,
                                current_scores):
    """Read-only parent inference on this fresh cohort for S3 comparability."""
    path = run_dir / parent.filename
    try:
        if (path.is_symlink() or path.parent != run_dir / "bundles" or
                not parent.filename.startswith("bundles/")):
            raise ValueError("DIAGNOSTIC_PAIRED_S3_UNSAFE_PARENT")
        weights, own_adamw, meta, loaded_graph = (
            _runtime_mlx_checkpoint.load_semantically_bound_bundle(path))
        if (meta["safetensors_sha256"] != parent.sha256 or
                meta["optimizer_step"] != parent.optimizer_step or
                loaded_graph != graph):
            raise ValueError("DIAGNOSTIC_PAIRED_S3_PARENT_DRIFT")
        del own_adamw
        predictions = _learning_student_ops._predictions(
            mx, weights, tuple(cohort.rows), receipt["config"],
            receipt["answer_ids"])
        measured = _bilqis_mlx_generated_assessment.score(
            cohort, predictions, _dataclasses.asdict(parent))["scores"]
        del weights
        if set(measured) != set(current_scores):
            raise ValueError("DIAGNOSTIC_PAIRED_S3_SCOPE_DRIFT")
        return measured, None
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return None, str(exc)


def _paired_stagnation_progress(mx, run_dir, receipt, stagnation, cohort, graph,
                                current_checkpoint, current_scores):
    """Compare consecutive assessment checkpoints on this same fresh cohort."""
    pointer = (stagnation or {}).get("progress_checkpoint")
    if pointer is None:
        return (), False
    try:
        previous = _learning_champions.Checkpoint(**pointer)
    except (TypeError, ValueError):
        return (), False
    if (previous.sha256 == current_checkpoint.sha256 and
            previous.optimizer_step == current_checkpoint.optimizer_step):
        return (), True
    previous_scores, issue = _score_parent_for_paired_s3(
        mx, run_dir, receipt, previous, cohort, graph, current_scores)
    if issue is not None or previous_scores is None:
        return (), False
    improved = []
    for capability, current in current_scores.items():
        prior = previous_scores.get(capability)
        if (not isinstance(prior, dict) or
                type(prior.get("correct")) is not int or
                type(prior.get("total")) is not int or
                prior["total"] != current.get("total")):
            return (), False
        if current["correct"] > prior["correct"]:
            improved.append(capability)
    return tuple(improved), True
