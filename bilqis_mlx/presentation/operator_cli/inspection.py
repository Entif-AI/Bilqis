"""Read-only run and executable-release inspection."""
from __future__ import annotations
from bilqis_mlx.compatibility.cli_preflight import legacy_new_run_inspection, legacy_qualification_scope, legacy_status_fields, historical_session_stop
from bilqis_mlx.source import AUDITED_PARENT
from bilqis_mlx.state_dag import read_current
from pathlib import Path
import json
from .settings import LEGACY_ROOT


def _qualification_scope() -> dict:
    """Compatibility facade retained for callers of the historical CLI seam."""
    return legacy_qualification_scope()


def _latest_session_stop(run_dir: Path, generation: int, step: int) -> dict | None:
    """The append-only event ledger owns per-invocation stop reasons."""
    events = run_dir / "events.jsonl"
    if not events.is_file():
        return None
    lines = events.read_text(encoding="utf-8").splitlines()
    if not lines:
        return None
    event = json.loads(lines[-1])
    if ((event.get("event") != "SCHOOL_SESSION_STOPPED" and
            not historical_session_stop(event.get("event"))) or
            event.get("generation") != generation or
            event.get("optimizer_step") != step):
        return None
    return {"reason": event["stop_reason"],
            "visits_this_command": event["visits_this_command"],
            "elapsed_seconds": event["elapsed_seconds"],
            "time_limit_minutes": event["minutes"],
            "max_visits": event["max_visits"],
            "disk_free_gib": round(event["free_bytes"]/1024**3, 3)
                if "free_bytes" in event else None}


def _executable_release_summary(run_dir: Path, saved: dict) -> dict | None:
    """Read current executable authority without reconstructing a Course."""
    if saved.get("factory_admission_v2") is None:
        return None
    from bilqis_mlx.runtime.admission import _read_executable_factory_release_artifact
    release = _read_executable_factory_release_artifact(run_dir, saved)
    plan = release.execution_plan
    return {
        "schema": release.schema,
        "release_sha256": release.release_sha256,
        "profile_id": release.profile.profile_id,
        "curriculum_sha256": plan.curriculum_sha256,
        "source_binding_sha256": plan.source_binding_sha256,
        "semantic_catalog_sha256": release.semantic_catalog_sha256,
        "active_grades": [grade.grade_id for grade in plan.grades],
        "canonical_grades": [
            {
                "id": grade.grade_id,
                "capabilities": [
                    capability.capability_id
                    for capability in grade.capabilities],
            }
            for grade in release.curriculum.grades
        ],
        "active_capabilities": [
            capability.capability_id for capability in plan.capabilities],
        "answer_domains": {
            head.kind: list(head.values) for head in release.answer_heads},
        "projection_digests": {
            name: getattr(plan.projection_digests, name)
            for name in (
                "roster", "schedule", "assessment", "source",
                "answer_schema", "coverage", "teaching")},
        "transition": (
            None if release.transition is None else {
                "semantic_geometry": release.transition.semantic_geometry,
                "added_grades": list(release.transition.added_grades),
                "revised_grades": list(release.transition.revised_grades),
                "added_capabilities": list(
                    release.transition.added_capabilities),
                "removed_capabilities": list(
                    release.transition.removed_capabilities),
            }),
    }


def _inspect(run_dir: Path) -> dict:
    bamf_pointer = run_dir / "bamf-state.json"
    if bamf_pointer.exists() or bamf_pointer.is_symlink():
        from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
        student, manifest_sha256 = load_bamf_generation_authority(bamf_pointer)
        teacher = student.teacher_state
        return {
            "status": "BAMF_ACCEPTED_GENERATION_READ_ONLY",
            "run_id": student.run_id,
            "generation": student.generation,
            "generation_manifest_sha256": manifest_sha256,
            "optimizer_step": student.retained_state.optimizer_step,
            "factory_release_sha256": student.run_identity.factory_release_sha256,
            "topology_sha256": student.topology.digest,
            "teacher_epoch": teacher.get("teacher_epoch"),
            "teacher_cursor": teacher.get("cursor"),
            "teacher_next_seed": teacher.get("next_seed"),
            "c03_lineage_active": "c03_lineage" in teacher,
            "neural_training_started_by_this_command": False,
            "run_dir": str(run_dir),
        }
    state = run_dir / "state.json"
    if state.is_file():
        saved = read_current(run_dir)
        if saved.get("schema") == "bilqis.mlx.human-grade-a-trainer/v1":
            return _human_status(saved, run_dir)
        if saved.get("schema") != "bilqis.mlx.letter-grade/v1":
            raise ValueError("UNRECOGNIZED_SCHOOL_RUN_SCHEMA")
        grade_index = saved.get("grade_index", 0)
        active_grades = saved.get("active_grades") or []
        grade = active_grades[grade_index] if 0 <= grade_index < len(active_grades) else "INVALID"
        return {"status":"PREPARED_SOURCE_STATE_READ_ONLY",
                "grade":grade,"phase":saved.get("stage"),
                "revalidation_target_grade":saved.get("revalidation_target_grade"),
                "visits":saved.get("visits",0),
                "optimizer_step":(saved.get("current_student") or {}).get("optimizer_step"),
                "checkpoint_sha256":(saved.get("current_student") or {}).get("sha256"),
                "champion_pointer_count":len(saved.get("champions") or {}),
                **_qualification_scope(),
                "neural_training_started_by_this_command":False,
                "run_dir":str(run_dir)}
    return {**legacy_new_run_inspection(historical_seed=AUDITED_PARENT.__dict__),
            **_qualification_scope(),
            "neural_training_started_by_this_command":False,
            "run_dir":str(run_dir)}


def _print_status(result: dict) -> int:
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def status(run_dir: Path):
    return _print_status(_inspect(run_dir))


def _vocabulary_status(saved):
    # The historical ABI prefix is not the active student's size.
    # Read the actual checkpoint-bound parameter geometry, and show
    # stale pre-growth metadata without silently rewriting evidence.
    saved_embedding_shape = saved.get("parameter_shapes", {}).get("embedding.weight")
    actual_tokens = (saved_embedding_shape[0] if saved_embedding_shape else None)
    reported_tokens = saved.get("config", {}).get("vocab_size")
    return {
                    "active_checkpoint_token_count": actual_tokens,
                    "declared_config_token_count": reported_tokens,
                    "metadata_reconciliation_needed": (
                        reported_tokens != actual_tokens
                        if actual_tokens is not None and reported_tokens is not None
                        else "NOT_MEASURED"),
                }


def _championship_status(saved):
    return ({
                    "introduced_grade": saved["mentor_epoch"]["introduced_grade"],
                    "baseline_sha256": saved["mentor_epoch"]["baseline"]["sha256"],
                    "baseline_optimizer_step":
                        saved["mentor_epoch"]["baseline"]["optimizer_step"],
                    "earned_active_roles":
                        len(saved["mentor_epoch"].get("active_roles", {})),
                    "active_soup_votes": {
                        grade: item["vote_count"]
                        for grade, item in saved["mentor_epoch"].get(
                            "active_grade_soups", {}).items()},
                    "archived_champion_roles":
                        len(saved.get("graduation_perfect", {})),
                    "archived_soup_grades":
                        sorted(saved.get("grade_soups", {})),
                    "active_baseline_advisers": 0 if saved["mentor_epoch"].get(
                        "guidance_policy") == "bilqis.mlx.earned-champions-only/v1"
                        else "LEGACY_POLICY_REQUIRES_RESET",
                    "championship_eligibility_after_step":
                        saved["mentor_epoch"].get(
                            "championship_eligibility_after_step"),
                    "administrative_empty_reset":
                        saved["mentor_epoch"].get("active_championship_reset"),
                    "legacy_mid_grade_activation":
                        saved["mentor_epoch"].get("experimental_refresh") ==
                        "MID_GRADE_FROZEN_CURRENT_STUDENT",
                } if saved.get("mentor_epoch") is not None else None)


def _human_status(saved, run_dir):
    school = saved["school"]
    active = school["active_grades"]
    grade = active[school["grade_index"]]
    student = school["current_student"]
    return {
        "status": saved["result"],
        "grade": grade, "phase": school["stage"],
        "revalidation_target_grade": school.get("revalidation_target_grade"),
        "visits": school["visits"],
        "optimizer_step": student["optimizer_step"],
        "checkpoint_sha256": student["sha256"],
        "model_topology": saved.get("model_topology"),
        "model_implementation": saved.get("model_implementation"),
        "vocabulary": _vocabulary_status(saved),
        "champion_pointer_count": len(school["champions"]),
        "championship_epoch": _championship_status(saved),
        "capability_best_pointer_count": len(saved.get("capability_best", {})),
        "capability_best_bundle_count": len({
            item["checkpoint"]["sha256"]
            for item in saved.get("capability_best", {}).values()}),
        "teacher_events": saved["teacher"]["events"],
        "teacher_strategy_count": len(saved["teacher"]["strategies"]),
        "whole_student_peaks": [{
            "scope_sha256": peak["scope_sha256"],
            "numeric_maximum": peak.get("numeric_maximum"),
            "correct": peak["correct"], "total": peak["total"],
            "optimizer_step": peak["checkpoint"]["optimizer_step"],
            "checkpoint_sha256": peak["checkpoint"]["sha256"]}
            for peak in saved.get("whole_student_peaks", ())],
        "experimental_retention_settings": (saved.get("learning_experiment") or {}).get("settings"),
        "retention_settings": (saved.get("learning_experiment") or {}).get("settings"),
        "last_exam": saved["last_exam"],
        "last_session_stop": _latest_session_stop(
            run_dir, saved["generation"], student["optimizer_step"]),
        **legacy_status_fields(saved),
        "introduction_stage": school.get("introduction_stage", 0),
        "numeric_maximum": saved.get("numeric_maximum"),
        "factory": _executable_release_summary(run_dir, saved),
        "assessment_cohort_sha256": (saved.get("last_exam") or {}).get("cohort_sha256"),
        "source_grounded_grade_a_admitted": True,
        **_qualification_scope(),
        "human_live_grade_a_trainer_end_to_end_qualified": "A" in school["champions"],
        "neural_training_started_by_this_command": False,
        "run_dir": str(run_dir),
        "repository_local_source": str(LEGACY_ROOT),
    }
