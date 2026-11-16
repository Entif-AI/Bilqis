"""Fresh title adjudication and championship evidence orchestration."""
from __future__ import annotations

import bilqis_mlx.curriculum.scheduler as _curriculum_scheduler
import bilqis_mlx.factory.schedule as _factory_schedule
import bilqis_mlx.generated_assessment as _bilqis_mlx_generated_assessment
import bilqis_mlx.learning.championship_identity as _learning_championship_identity
import bilqis_mlx.learning.championship_witnesses as _learning_championship_witnesses
import bilqis_mlx.learning.epoch_championships as _learning_epoch_championships
import bilqis_mlx.learning.lesson_guidance as _learning_lesson_guidance
import bilqis_mlx.learning.student_ops as _learning_student_ops
import bilqis_mlx.runtime.admission as _runtime_admission
import bilqis_mlx.runtime.assessment as _runtime_assessment
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints
import bilqis_mlx.runtime.mlx_checkpoint as _runtime_mlx_checkpoint
import bilqis_mlx.runtime.release_adoption as _runtime_release_adoption
import bilqis_mlx.runtime.state as _runtime_state
import bilqis_mlx.runtime.timing_trace as _runtime_timing_trace
import copy as _copy
import dataclasses as _dataclasses
import json as _json

from .capability_championship import (
    assessment_exam as complete_solver_championship_exam,
    assessment_path_attribution, assessment_progress,
    fresh_title_match as fresh_complete_solver_title_match,
)


def _championship_identity(receipt, course):
    return _learning_championship_identity.build_school_identity(
        course_sha256=(receipt.get("factory_admission_v2") or {}).get(
            "curriculum_sha256", course.digest()),
        semantic_graph_sha256=receipt["semantic_graph_sha256"],
        parameter_shapes=receipt["parameter_shapes"],
        factory_release_sha256=receipt["factory_release_sha256"])


def _live_championship_identity(receipt, course, graph, parameters):
    return _learning_championship_identity.build_school_identity(
        course_sha256=(receipt.get("factory_admission_v2") or {}).get(
            "curriculum_sha256", course.digest()),
        semantic_graph_sha256=_runtime_state._fingerprint(graph),
        parameter_shapes={name: list(value.shape) for name, value in parameters.items()},
        factory_release_sha256=receipt["factory_release_sha256"])


def _championship_pair_key(capability, left_sha256, right_sha256):
    return capability + "|" + "|".join(sorted((left_sha256, right_sha256)))


def _historical_championship_authority(run_dir):
    """Recover immutable matchup and checkpoint-origin facts from durable events."""
    origins = {}
    settled = {}
    duplicate_settlements = 0
    path = run_dir / "events.jsonl"
    if not path.is_file():
        return {}, {}, {}, 0
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            event = _json.loads(line)
            if (event.get("event") == "SCHOOL_TEACHER_VISIT_COMMITTED" and
                    type(event.get("retained_optimizer_updates")) is int and
                    event["retained_optimizer_updates"] > 0 and
                    isinstance(event.get("recovered_at_student_sha256"), str) and
                    isinstance(event.get("grade"), str) and event["grade"]):
                origins.setdefault(event["recovered_at_student_sha256"], set()).add(
                    event["grade"])
            epoch = event.get("championship_epoch")
            if not isinstance(epoch, dict):
                continue
            for decision in epoch.get("cross_origin_decisions", ()):
                if (not isinstance(decision, dict) or
                        decision.get("decision") not in ("TITLE_WON", "TITLE_DEFENDED")):
                    continue
                capability = decision.get("capability")
                incumbent = decision.get("incumbent_sha256")
                challenger = decision.get("challenger_sha256")
                if not all(isinstance(value, str) and value for value in
                           (capability, incumbent, challenger)):
                    raise ValueError("CHAMPIONSHIP_HISTORICAL_SETTLEMENT_INVALID")
                key = _championship_pair_key(capability, incumbent, challenger)
                record = {**decision,
                          "source_generation": event.get("generation"),
                          "historical_backfill": True}
                if key in settled:
                    duplicate_settlements += 1
                else:
                    settled[key] = record
    proven = {sha: next(iter(grades)) for sha, grades in origins.items()
              if len(grades) == 1}
    ambiguous = {sha: sorted(grades) for sha, grades in origins.items()
                 if len(grades) > 1}
    return proven, ambiguous, settled, duplicate_settlements


def _is_profile_revision_epoch_history_artifact(entry):
    return entry == {
        "kind": "profile-revision-school-identity-reset",
        "event": True,
    }


def _without_profile_revision_epoch_history_artifact(receipt):
    """Remove only the malformed administrative receipt emitted by 413239a.

    `championship_epoch_history` is typed mentor-epoch history.  One short-lived
    profile-revision producer incorrectly appended this non-epoch marker there.
    Preserve every real epoch and every other unknown value so unrelated drift
    still fails closed at its normal verifier.
    """
    history = list(receipt.get("championship_epoch_history", ()))
    cleaned = [
        entry for entry in history
        if not _is_profile_revision_epoch_history_artifact(entry)
    ]
    removed = len(history) - len(cleaned)
    if not removed:
        return receipt, 0
    return {**receipt, "championship_epoch_history": cleaned}, removed


def _repair_profile_revision_epoch_history(run_dir, receipt, course):
    """Persist the exact malformed-history cleanup before custody verification."""
    repaired, removed = _without_profile_revision_epoch_history_artifact(receipt)
    if not removed:
        return receipt
    program = _runtime_release_adoption._schedule_for_receipt(run_dir, repaired, course)
    school = _runtime_state._state_from_json(repaired["school"], program)
    record = _runtime_checkpoints._advance(run_dir, repaired, school, persist=False)
    event = {
        "event": "SCHOOL_PROFILE_REVISION_EPOCH_HISTORY_REPAIRED",
        "generation": record["generation"],
        "grade": school.grade,
        "removed_malformed_entries": removed,
        "student_sha256": school.current_student.sha256,
        "optimizer_step": school.current_student.optimizer_step,
        "actual_neural_updates": 0,
        "model_and_own_adamw_unchanged": True,
    }
    record = _runtime_checkpoints._persist(run_dir, _runtime_checkpoints._with_delivery_outbox(record, (event,)))
    _runtime_checkpoints._reconcile_delivery_outbox(run_dir, record)
    return record


def _migrate_championship_governance(run_dir, receipt, course):
    """Neural-inert rev7 migration from durable run evidence."""
    identity = _championship_identity(receipt, course)
    proven, ambiguous, historical_settled, duplicate_count = (
        _historical_championship_authority(run_dir))
    updated = _copy.deepcopy(receipt)
    changed = updated.get("championship_school_identity") != identity
    updated["championship_school_identity"] = identity

    origin_map = dict(updated.get("championship_checkpoint_origins", {}))
    for sha, grade in proven.items():
        existing = origin_map.get(sha)
        if existing is not None and existing != grade:
            raise ValueError("CHAMPIONSHIP_CHECKPOINT_ORIGIN_PROVENANCE_CONFLICT")
        if existing is None:
            origin_map[sha] = grade
            changed = True
    if updated.get("championship_checkpoint_origins") != origin_map:
        updated["championship_checkpoint_origins"] = origin_map
    if ambiguous:
        if updated.get("championship_checkpoint_origin_ambiguities") != ambiguous:
            changed = True
        updated["championship_checkpoint_origin_ambiguities"] = ambiguous
    else:
        if "championship_checkpoint_origin_ambiguities" in updated:
            changed = True
        updated.pop("championship_checkpoint_origin_ambiguities", None)

    program = _runtime_release_adoption._schedule_for_receipt(run_dir, updated, course)
    school = _runtime_state._state_from_json(updated["school"], program)
    current_origin = origin_map.get(school.current_student.sha256)
    if current_origin is not None:
        if updated.get("last_retained_update_grade") != current_origin:
            changed = True
        updated["last_retained_update_grade"] = current_origin
    elif school.current_student.sha256 in ambiguous:
        if "last_retained_update_grade" in updated:
            changed = True
        updated.pop("last_retained_update_grade", None)

    epoch = updated.get("mentor_epoch")
    reset = False
    origins_invalidated = False
    if epoch is not None:
        epoch = _copy.deepcopy(epoch)
        ledger = epoch.setdefault("settled_matchups", {})
        if not isinstance(ledger, dict):
            raise ValueError("CHAMPIONSHIP_SETTLED_MATCH_LEDGER_INVALID")
        for key, settlement in historical_settled.items():
            if key not in ledger:
                ledger[key] = settlement
                changed = True
        for role in epoch.get("active_roles", {}).values():
            if role.get("origin_grade") is None:
                grade = origin_map.get(role.get("checkpoint", {}).get("sha256"))
                if grade is not None:
                    role["origin_grade"] = grade
                    changed = True
        epoch, reset = _learning_championship_identity.enforce_school_identity(
            epoch, identity, generation=updated["generation"] + 1,
            student=_dataclasses.asdict(school.current_student))
        if reset:
            changed = True
        else:
            epoch, origins_invalidated = _learning_epoch_championships.sanitize_role_origins(
                epoch, grades={
                    grade.id: tuple(
                        capability.id for capability in grade.capabilities)
                    for grade in program.grades})
            if origins_invalidated:
                changed = True
        updated["mentor_epoch"] = epoch

    if not changed:
        return receipt
    record = _runtime_checkpoints._advance(run_dir, updated, school, persist=False)
    migration = {
        "event": "SCHOOL_CHAMPIONSHIP_GOVERNANCE_MIGRATED",
        "generation": record["generation"],
        "grade": school.grade,
        "student_sha256": school.current_student.sha256,
        "optimizer_step": school.current_student.optimizer_step,
        "championship_school_identity_sha256": identity["sha256"],
        "checkpoint_origins_proven": len(origin_map),
        "checkpoint_origins_ambiguous": len(ambiguous),
        "settled_matchups_backfilled": len(historical_settled),
        "duplicate_historical_settlements_ignored": duplicate_count,
        "holistic_authority_reset": reset,
        "invalid_origin_roles_archived": origins_invalidated,
        "actual_neural_updates": 0,
    }
    record = _runtime_checkpoints._persist(run_dir, _runtime_checkpoints._with_delivery_outbox(record, (migration,)))
    _runtime_checkpoints._reconcile_delivery_outbox(run_dir, record)
    return record


def _bind_checkpoint_origin(receipt, checkpoint):
    """Attach the last proven retained-update grade to a newly sealed checkpoint."""
    grade = receipt.get("last_retained_update_grade")
    if grade is None:
        return receipt
    if not isinstance(grade, str) or not grade:
        raise ValueError("CHAMPIONSHIP_LAST_RETAINED_GRADE_INVALID")
    origins = dict(receipt.get("championship_checkpoint_origins", {}))
    existing = origins.get(checkpoint.sha256)
    if existing is not None and existing != grade:
        raise ValueError("CHAMPIONSHIP_CHECKPOINT_ORIGIN_PROVENANCE_CONFLICT")
    origins[checkpoint.sha256] = grade
    return {**receipt, "championship_checkpoint_origins": origins}


def _compare_incumbents(mx, run_dir, receipt, cohort, config, answer_ids, graph):
    """Replay every unique historical and current leader on this exact cohort."""
    historic = receipt.get("historical_capability_best", {}) if receipt.get(
        "legacy_frontier_pending_replay") else {}
    current = receipt.get("capability_best", {})
    references = list(current.values()) + list(historic.values()) + list(receipt.get("graduation_perfect", {}).values())
    references.extend({"checkpoint": p} for p in
                      receipt.get("historical_grade_champions", {}).values())
    # A graduate keeps a teacher/champion vote even if its current capability
    # best slot was superseded under a newer multi-grade rubric.
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


def _epoch_paired_examinations(mx, run_dir, receipt, course, school,
                               cohort, scores, predictions, graph, *,
                               challenge_grade=None):
    """Re-examine only potentially displaced epoch incumbents on these rows."""
    epoch = receipt["mentor_epoch"]
    if epoch["source_graph_sha256"] != _runtime_state._fingerprint(graph):
        raise ValueError("CHAMPIONSHIP_EPOCH_SOURCE_GRAPH_DRIFT")
    if (epoch.get("championship_school_identity") !=
            receipt.get("championship_school_identity")):
        raise ValueError("CHAMPIONSHIP_EPOCH_SCHOOL_IDENTITY_RESET_REQUIRED")
    executable_release = _runtime_admission._read_executable_factory_release_artifact(
        run_dir, receipt)
    program = _factory_schedule.schedule_program_from_executable_release(executable_release)
    grades = {
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
    checkpoint_origin_grade = receipt.get(
        "championship_checkpoint_origins", {}).get(school.current_student.sha256)
    title_grade = challenge_grade or checkpoint_origin_grade or school.grade
    if title_grade not in grades:
        raise ValueError("CHAMPIONSHIP_EPOCH_CHALLENGE_GRADE_INVALID")
    if checkpoint_origin_grade not in grades:
        raise ValueError("CHAMPIONSHIP_CHECKPOINT_ORIGIN_PROVENANCE_INVALID")
    if not any(capability in scores for capability in grades[title_grade]):
        raise ValueError("CHAMPIONSHIP_EPOCH_CHALLENGE_GRADE_UNMEASURED")
    context = {
        "cohort_sha256": cohort.digest,
        "rubric_sha256": rubric,
        "cohort_rubric_sha256": cohort_rubric,
        "assessment_scope_sha256": _runtime_state._fingerprint(scope),
        "source_graph_sha256": _runtime_state._fingerprint(graph),
        "source_oracle_sha256": receipt["source_manifest_sha256"],
        # Title jurisdiction follows the capability grade being adjudicated.
        # The optimizer visit that produced this intact checkpoint remains
        # separate provenance and must never suppress valid capability evidence.
        "challenge_grade": title_grade,
        "checkpoint_origin_grade": checkpoint_origin_grade,
    }
    challenger = {**context, "checkpoint": _dataclasses.asdict(school.current_student),
                  "scores": scores,
                  "questions": _championship_questions(cohort),
                  "correct_questions": _championship_correct_questions(cohort, predictions)}
    requested = _learning_epoch_championships.needed_incumbents(
        epoch, grades=grades, challenger_exam=challenger)
    incumbents = {}
    for sha, pointer in sorted(requested.items()):
        if sha == school.current_student.sha256:
            incumbents[sha] = challenger
            continue
        path = run_dir / pointer["filename"]
        if (path.is_symlink() or path.parent != run_dir / "bundles" or
                not pointer["filename"].startswith("bundles/")):
            raise ValueError("CHAMPIONSHIP_EPOCH_UNSAFE_INCUMBENT")
        weights, own_adamw, meta, loaded_graph = _runtime_mlx_checkpoint.load_semantically_bound_bundle(path)
        if (meta["safetensors_sha256"] != sha or
                meta["optimizer_step"] != pointer["optimizer_step"] or
                not _learning_student_ops._compatible_graphs(loaded_graph, graph)):
            raise ValueError("CHAMPIONSHIP_EPOCH_INCOMPARABLE_INCUMBENT_GRAPH")
        del own_adamw
        challenge_caps = set(grades[title_grade])
        grade_rows = tuple(row for row in cohort.rows
                           if row["capability"] in challenge_caps)
        grade_cohort = _bilqis_mlx_generated_assessment.make_cohort(
            grade_rows, generator_version=cohort.generator_version,
            seed=cohort.seed, rubric_version=cohort.rubric_version)
        readable = _readable_championship_rows(grade_cohort, loaded_graph, receipt)
        subset = _bilqis_mlx_generated_assessment.make_cohort(readable, generator_version=cohort.generator_version,
                             seed=cohort.seed, rubric_version=cohort.rubric_version) if readable else None
        config = (_learning_student_ops._compatible_answer_config(receipt["config"], loaded_graph)
                  if any(row.get("answer_kind", "binary") != "binary" for row in readable)
                  else receipt["config"])
        predictions = (_learning_student_ops._predictions(mx, weights, readable, config, receipt["answer_ids"])
                       if readable else {})
        measured = _bilqis_mlx_generated_assessment.score(subset, predictions, pointer) if subset else {"scores": {}}
        incumbents[sha] = {**context, "checkpoint": dict(pointer),
                           "checkpoint_graph_sha256": _runtime_state._fingerprint(loaded_graph),
                           "scored_subset_sha256": subset.digest if subset else None,
                           "scores": measured["scores"],
                           "questions": _championship_questions(subset) if subset else {},
                           "correct_questions": (
                               _championship_correct_questions(subset, predictions)
                               if subset else {})}
        del weights
    return grades, challenger, incumbents


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


def _advance_exam_championship_grade(mx, run_dir, receipt, epoch, course, school,
                                     cohort, measured, predictions, parameters, graph,
                                     *, challenge_grade):
    current = {**receipt, "mentor_epoch": epoch}
    grades, challenger, incumbents = _epoch_paired_examinations(
        mx, run_dir, current, course, school, cohort, measured["scores"], predictions,
        graph, challenge_grade=challenge_grade)
    title_matches = {}
    fanout_screen = None
    proposed = epoch
    changes = decisions = ()
    for round_index in range(5):
        proposed, changes, decisions = _learning_epoch_championships.advance_epoch(
            epoch, grades=grades, challenger_exam=challenger,
            incumbent_exams=incumbents, title_matches=title_matches,
            fanout_screen=fanout_screen)
        screen_requests = [decision for decision in decisions
                           if decision["decision"] == "FANOUT_SCREEN_REQUIRED"]
        if screen_requests:
            if fanout_screen is not None or len(screen_requests) != 1:
                raise ValueError("CHAMPIONSHIP_FANOUT_SCREEN_RECURSION")
            request = screen_requests[0]
            fanout_screen = _fresh_fanout_screen(
                mx, run_dir, receipt, epoch, cohort, challenger,
                parameters, graph, request["capabilities"])
            continue
        pending = {
            decision["capability"] for decision in decisions
            if decision["decision"] in (
                "TITLE_MATCH_REQUIRED", "FANOUT_TITLE_MATCH_REQUIRED") and
            decision["capability"] not in title_matches}
        if not pending:
            return proposed, changes, decisions
        if round_index == 4:
            raise ValueError("CHAMPIONSHIP_TITLE_MATCH_RECURSION")
        for cap in sorted(pending):
            role = epoch["active_roles"][cap]
            title_matches[cap] = _fresh_title_match(
                mx, run_dir, receipt, epoch, cohort, challenger,
                parameters, graph, cap)
    raise AssertionError("unreachable")


def _advance_exam_championships(mx, run_dir, receipt, epoch, course, school,
                                cohort, measured, predictions, parameters, graph):
    """Adjudicate every measured capability grade for the intact checkpoint."""
    scores = measured["scores"]
    represented = [
        grade.id for grade in _runtime_release_adoption._schedule_for_receipt(run_dir, receipt, course).grades
        if any(cap.id in scores for cap in grade.capabilities)
    ]
    if not represented:
        raise ValueError("CHAMPIONSHIP_EPOCH_NO_MEASURED_TITLE_GRADE")
    updated = epoch
    changed_roles, decisions = set(), []
    for grade in represented:
        updated, changed, verdicts = _advance_exam_championship_grade(
            mx, run_dir, receipt, updated, course, school, cohort, measured,
            predictions, parameters, graph, challenge_grade=grade)
        changed_roles.update(changed)
        decisions.extend(verdicts)
    return updated, tuple(sorted(changed_roles)), tuple(decisions)
