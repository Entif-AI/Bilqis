"""Validation at the operator entry boundary."""
import pathlib as _pathlib
from bilqis_mlx import paths
import bilqis_mlx.runtime.experiment_runs as experiment_runs
import bilqis_mlx.runtime.admission as admission
import bilqis_mlx.state_dag as state_dag


def validate_operator_preflight(*, run_dir, minutes, steps_per_visit, max_visits,
                                batch_size, source_prefetch_workers,
                                stagnation_grace_grade, stagnation_grace_steps,
                                resume, flash_mode, boolean_composite,
                                boolean_idboolops, boolean_association_bridge,
                                admit_next_grade_with_debt, numeric_staircase,
                                autonomous_curriculum, retention_enabled,
                                experiment_budget):
    if (type(minutes) is not int or not 1 <= minutes <= 1440 or
            type(steps_per_visit) is not int or not 1 <= steps_per_visit <= 2048 or
            type(max_visits) is not int or max_visits < 0 or
            type(batch_size) is not int or batch_size < 2 or batch_size % 2 or
            type(source_prefetch_workers) is not int or
            not 0 <= source_prefetch_workers <= 2):
        raise ValueError("HUMAN_TRAINER_INVALID_OPERATOR_LIMITS")
    grace_requested = stagnation_grace_grade is not None or stagnation_grace_steps != 0
    if grace_requested and (
            not resume or not isinstance(stagnation_grace_grade, str) or
            not stagnation_grace_grade or type(stagnation_grace_steps) is not int or
            stagnation_grace_steps <= 0):
        raise ValueError("STAGNATION_GRACE_REQUIRES_EXPLICIT_RESUME_REQUEST")
    if flash_mode and not resume:
        raise ValueError("FLASH_MODE_REQUIRES_RESUME")
    if boolean_composite and not resume:
        raise ValueError("BOOLEAN_COMPOSITE_REQUIRES_RESUME")
    if boolean_idboolops and not resume:
        raise ValueError("BOOLEAN_IDBOOLOPS_REQUIRES_RESUME")
    if boolean_association_bridge and not resume:
        raise ValueError("BOOLEAN_ASSOCIATION_BRIDGE_REQUIRES_RESUME")
    if admit_next_grade_with_debt and not resume:
        raise ValueError("DEBT_GRADE_ADMISSION_REQUIRES_RESUME")
    if admit_next_grade_with_debt and numeric_staircase:
        raise ValueError("DEBT_GRADE_ADMISSION_INCOMPATIBLE_WITH_NUMERIC_STAIRCASE")
    if autonomous_curriculum and not retention_enabled:
        raise ValueError("AUTONOMOUS_CURRICULUM_REQUIRES_RETENTION")
    if autonomous_curriculum and flash_mode:
        raise ValueError("AUTONOMOUS_CURRICULUM_INCOMPATIBLE_WITH_FLASH_MODE")
    if experiment_budget is not None:
        experiment_runs.require_training_run(
            run_dir, paths.REPO_ROOT / "runs",
            issue_budget=experiment_budget)
        experiment_budget.assert_can_allocate(600_000_000)
    if boolean_association_bridge:
        saved_path = _pathlib.Path(run_dir).expanduser().resolve() / "state.json"
        if not saved_path.is_file():
            raise ValueError("TEACHING_ENRICHMENT_REQUIRES_ADMITTED_FACTORY_RELEASE")
        saved_release = state_dag.read_current(_pathlib.Path(run_dir))
        if not admission.admitted_release_supports_teaching_option(
                _pathlib.Path(run_dir).expanduser().resolve(), saved_release):
            raise ValueError("TEACHING_ENRICHMENT_NOT_ADMITTED_BY_FACTORY_RELEASE")
    if not retention_enabled and resume:
        # Fail before GPU loading, orphan recovery, or any state mutation when
        # a protected student's policy would otherwise be silently disabled.
        saved_path = _pathlib.Path(run_dir).expanduser().resolve() / "state.json"
        if (saved_path.is_file() and state_dag.read_current(_pathlib.Path(run_dir)).get(
                "learning_experiment") is not None):
            raise ValueError("LEARNING_EXPERIMENT_PROTECTED_RESUME_REQUIRES_RETENTION")
