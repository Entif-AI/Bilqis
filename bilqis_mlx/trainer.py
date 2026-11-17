"""Compatibility facade for the serialized MLX runtime services."""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import asdict, replace
from functools import lru_cache
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import shlex
import sys
import time
import uuid

from .fixed_frontier import frontier_exam
from .backup import digest_file
from .runtime.experiment_runs import ExperimentRunBudget, require_training_run
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.learning.champion_confidence import MAX_INFLUENCE as MAX_CHAMPION_INFLUENCE
from bilqis_mlx.learning.champion_confidence import vote_targets_typed
from bilqis_mlx.learning.champion_confidence import POLICY as CHAMPION_CONFIDENCE_POLICY
from bilqis_mlx.learning.champion_confidence import perfect_role_roster, vote_targets
from bilqis_mlx.learning.grade_soup import (grade_soup_recipe, partitioned_recipe,
                         PARTITIONED_SCHEMA, soup_shards, needs_refresh, soup_vote_count,
                         weighted_average, save_frozen_soup, verify_frozen_soup,
                         retire_stale_soups)
from bilqis_mlx.learning.learning_experiment import (
    VERSION as LEARNING_EXPERIMENT_VERSION, Settings as LearningSettings,
    contextual_pick, paired_outcomes, decide as decide_learning_trial,
    observe_context, selection_credit, fork_student, commit_trial,
    earlier_grade_capabilities, reserve_weakness_targets, select_source_lesson, sampled_protection,
    missing_grade_capabilities,
)
from bilqis_mlx.learning.whole_student_retention import advance_peaks
from bilqis_mlx.learning.epoch_championships import (
    active_frontier as epoch_active_frontier,
    needed_incumbents as epoch_needed_incumbents,
    advance_epoch as advance_championship_epoch,
    sanitize_role_origins as sanitize_championship_role_origins,
)
from bilqis_mlx.learning.championship_identity import (
    build_school_identity, enforce_school_identity)
from .source_adapters.school import live_source_registry
from .compatibility.executable_projection import (
    compile_projected_executable_release,
    legacy_execution_metadata,
    legacy_course_for_profile,
    resolve_legacy_resume_course,
    verify_legacy_resume_binding,
)
from .factory.assessment import qualification_complete
from .factory.schedule import ScheduleProgram, schedule_program_from_executable_release
from .factory.executable_release import (
    answer_heads_from_executable_release,
    compile_successor_profile_release,
)
from .factory.live_answers import live_answer_registry
from .profiles.school import (
    boolean_entry_profile,
    with_disabled_future_grades,
)
from .profiles.catalog import (
    next_numeric_scope_profile,
    numeric_scope_profile,
    numeric_row_in_scope,
    numeric_entry_transition,
)
from .profiles.retention import fragile_preservation_capabilities
from .operator_vocabulary import (
    AUTONOMY_SAFE_HOLD, AUTONOMY_SOURCE_DEVELOPMENT_REQUIRED,
)
from .compatibility.live_releases import (
    boolean_identification_answer_heads,
    initial_course,
    numeric_answer_heads,
    predecessor_course,
)
from .factory.model import AssessmentClass, LearningEvidence
from bilqis_mlx.learning.mentor_epoch import EARNED_ONLY_POLICY, begin_initial_epoch
from bilqis_mlx.learning.championship_witnesses import (
    earning_witness, verified_battery, verified_witnesses)
from bilqis_mlx.learning.capability_frontier import (
    candidate_roles, historical_frontier, pinned, promote,
    recover_graduation_breadth, retire_bundles,
)
from bilqis_mlx.runtime.disk import assert_headroom, headroom_snapshot
from .diagnostics.teaching import inspect_lesson_step, summarize_teaching_visit
from .diagnostics.exam_events import (apply_paired_checkpoint_s3,
                                      summarize_completed_exam_safely)
from .generated_assessment import (
    GENERALIZATION_LIFECYCLE, PROMOTION_ATTEMPT_LIFECYCLE,
    ROUTINE_EVAL_LIFECYCLE, make_cohort, score as score_cohort,
    verify_stored_cohort,
)
from .grade_a_manifest import verify_manifest
from .compatibility.source_bootstrap import AUTHORITY, accepted_grade_a
from .live_curriculum import (
    assessment_rubric_for_scope, cohort_contract as _cohort_contract,
    lesson_contract, numeric_maximum,
)
from bilqis_mlx.runtime.mlx_checkpoint import save_new_bundle, load_semantically_bound_bundle
from bilqis_mlx.runtime.mlx_parity import (clip_gradients, forward_arrays,
                         native_optimizer_to_mlx)
from bilqis_mlx.curriculum.scheduler import (start_new, visit, assess, assess_withheld, next_capability,
                     adopt_appended_program, adopt_revised_program,
                     append_next_grade_with_debt,
                     append_next_grade, assessment_capabilities,
                     revise_admitted_grade, replace_admitted_grade,
                     reactivate_stagnation_debt, weakest_three,
                     require_assessment_after_flash,
                     assess_flash, SchoolState, Assessment, Score)
from bilqis_mlx.learning.stagnation_control import (
    activate_sole_grade_rehabilitation,
    begin_recovery_cycle, complete_recovery_cycle, end_of_run_alerts,
    grace_suppressed_capabilities, reconcile_optimizer_step_grace,
    observe_paired_progress, reconcile_required_scope,
    quarantined_capabilities, record_visit as record_stagnation_visit,
    start_session as start_stagnation_session,
)
from .semantics.abi import HISTORICAL_PREFIX_SIZE
from .source import AUDITED_PARENT
from .vocabulary_growth import extend_mlx_student
from bilqis_mlx.learning.teacher_feedback import (
    WeaknessTargetRequest, TeacherDecisionInput, active_warning_signals, reconcile_unresolved_misses,
    select_weakness_targets, summarize_teacher_decision,
    summarize_teacher_outcomes,
)
from bilqis_mlx.runtime.timing_trace import trace_mark, trace_span
from .runtime.state import (
    _canonical, _fingerprint, _durable_json, _state_from_json, _seed,
)
from .runtime.admission import (
    admitted_release_supports_teaching_option,
    _executable_factory_admission,
    _factory_release, _persist_factory_release, _factory_admission,
    _read_factory_release,
    _read_executable_factory_release_artifact,
    _require_executable_factory_admission, _require_factory_admission,
    _verified_legacy_upgrade_release,
)
from .runtime.assessment import (
    load_championship_cohort,
    _candidate_executable_cohort, _generalization_executable_cohort,
    _promotion_executable_cohort, _routine_executable_cohort,
    _draw_live_rows, _persist_live_cohort, _load_current_cohort,
    released_lesson_source_identity,
    _verify_saved_cohort, _grade_test_cohort, _promotion_cohort,
    _generalization_cohort, _candidate_cohort, _introduced_cohort,
    _without_stagnant_capabilities, _require_active_stagnation_scope,
)

from .runtime.session import VERSION, LOCKFILE
from .runtime.checkpoints import _event_view
from bilqis_mlx.learning.championship_runtime import (
    _championship_identity,
    _live_championship_identity,
    _championship_pair_key,
    _historical_championship_authority,
    _is_profile_revision_epoch_history_artifact,
    _without_profile_revision_epoch_history_artifact,
    _repair_profile_revision_epoch_history,
    _migrate_championship_governance,
    _bind_checkpoint_origin,
    _compare_incumbents,
    _epoch_paired_examinations,
    _readable_championship_rows,
    _championship_correct_questions,
    _championship_questions,
    _hydrate_championship_witnesses,
    _fresh_title_current_exam,
    _fresh_battery_results,
    _fresh_title_match,
    _fresh_fanout_screen,
    _advance_exam_championship_group,
    _advance_exam_championships,
)
from bilqis_mlx.learning.lesson_guidance import (
    choose_lesson_batch,
    replay_missed_lessons,
    _cached_frozen_champion,
    _frozen_confidence_champions,
    _mentor_sources_for_visit,
    _cook_new_grade_soups,
    _cached_grade_soup,
    _frozen_grade_soup_votes,
    _confidence_guidance,
    _typed_confidence_guidance,
)
from bilqis_mlx.learning.student_ops import (
    _initial_model,
    _make_batch,
    _predictions,
    _train_score,
    _compatible_graphs,
    _compatible_answer_config,
    _train_step,
)
from bilqis_mlx.runtime.boundary_commit import (
    _live_exam_factors_complete,
    _verify_live_rubric_lineage,
    _commit_scored_student,
    _flush_working_student,
    _flush_flash_student,
)
from bilqis_mlx.runtime.candidate_evidence import (
    _learning_probe_rows,
    _fixed_same_grade_rows,
    _reusable_exam_identity,
    _frontier_fixed_evidence,
    _same_grade_fixed_evidence,
    _fragile_replay_evidence,
    _candidate_fixed_evidence,
    _candidate_grade_evidence,
    _fresh_fragile_preservation_rows,
    _inject_preservation_rows,
)
from bilqis_mlx.runtime.checkpoints import (
    operator_view,
    _persist,
    _recover_orphaned_commit,
    _record,
    _notify_viewer,
    _bundle_pointer,
    _clean_staged_bundles,
    _mentor_epoch_references,
    _verify_frozen_soup_custody,
    _verify_best_custody,
    _advance,
    _boundary_delivery_events,
    _with_delivery_outbox,
    _require_outbox_lineage,
    _outbox_source_generation,
    _expected_outbox_events,
    _observed_outbox_events,
    _reconcile_delivery_outbox,
    _publish_boundary,
    _quarantine_newer_uncommitted_bundles,
)
from bilqis_mlx.runtime.exam_execution import (
    _score_parent_for_paired_s3,
    _paired_stagnation_progress,
    _school_result_label,
    _promotion_due_after_routine,
    _assessment_scope_sha256,
    _measure_debt_admission_boundary,
    _take_exam,
)
from bilqis_mlx.runtime.frontier_refresh import (
    _refresh_fixed_frontier,
)
from bilqis_mlx.runtime.operating_loop import (
    operate,
)
from bilqis_mlx.runtime.reconciliation import (
    _require_championship_source_context_custody,
    _affected_championship_source_context,
    _invalidate_championship_source_context,
    _repair_championship_source_context,
    _reconcile_vocabulary_metadata,
    _reconcile_learning_settings,
    _seed_saved_whole_student_peak,
    _rehabilitate_sole_grade_debt,
    _reconcile_stagnation_scope,
    _advance_stagnation_after_routine,
)
from bilqis_mlx.runtime.release_adoption import (
    _ensure_factory_admission,
    _migrate_executable_release,
    _ensure_executable_release,
    _cached_schedule_program,
    _schedule_for_receipt,
    _verify_profile_successor,
    _profile_transition,
    _profile_championship_state,
    _profile_adoption_receipt,
    _adopt_executable_profile,
    _require_complete_profile_boundary,
    _catalog_boundary_evidence,
    _catalog_epoch_state,
    _catalog_adoption_receipt,
    _catalog_adoption_event,
    _adopt_catalog_profile,
    _adopt_jit_proposal,
)
from bilqis_mlx.runtime.session import (
    operator_lock,
    prepare_source,
    _init,
    _resume,
    _resume_command,
    session_stop_reason,
)
from bilqis_mlx.runtime.visits import (
    _teaching_enrichment_rows,
    _extend_binary_guidance,
    _skip_perfect_target_visit,
    _skip_stagnant_target_visit,
    _take_visit,
)
