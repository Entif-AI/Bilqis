"""Read disposable trainer posture without granting it accepted-state authority."""
from dataclasses import fields
import json
import os
from pathlib import Path
import time

from bilqis_mlx.mission_control.contracts.model import (
    AuthorityClass, CoverageState, RecordMeta, is_time,
)
from bilqis_mlx.mission_control.contracts.trainer import (
    CandidateStepPerformance, DeferredGradeCandidate, GeneratedGradeEvidence,
    GeneratedGradeHold, GeneratedGradeMemberEvidence, GradeSynthesisDimension,
    RetentionStageTiming, TrainerObservation, TrainerObservationV2, TrainerObservationV3,
    TrainerObservationV4, TrainerObservationV5, VisitCapabilityScore,
    VisitEvidence, VisitRankingEvidence, VisitRoleCount,
)
from bilqis_mlx.mission_control.contracts.trainer_evidence import (
    LearningHealthEvidence, LearningHealthScore, LearningHealthWarning,
    LearningHealthCheckpoint,
)


MAX_BYTES = 64 * 1024
MAX_VISITS = 8
MAX_HEARTBEAT_AGE_MS = 10_000
MAX_FUTURE_SKEW_MS = 5_000
_SCHEMAS = frozenset({
    'bilqis.bamf.trainer-observed/v1',
    'bilqis.bamf.trainer-observed/v2',
    'bilqis.bamf.trainer-observed/v3',
    'bilqis.bamf.trainer-observed/v4',
    'bilqis.bamf.trainer-observed/v5',
    'bilqis.bamf.trainer-observed/v6',
})
_FIELDS = {field.name for field in fields(TrainerObservation)} - {
    'meta', 'posture', 'connection_state'}
_OPTIONAL_FIELDS = frozenset(('error_code', 'error_detail'))
_V2_FIELDS = {field.name for field in fields(TrainerObservationV2)} - {
    'meta', 'posture', 'connection_state'}
_V2_ONLY = _V2_FIELDS - _FIELDS
_V3_FIELDS = {field.name for field in fields(TrainerObservationV3)} - {
    'meta', 'posture', 'connection_state'}
_V3_ONLY = _V3_FIELDS - _V2_FIELDS
_V4_FIELDS = {field.name for field in fields(TrainerObservationV4)} - {
    'meta', 'posture', 'connection_state'}
_V4_ONLY = _V4_FIELDS - _V3_FIELDS
_V5_FIELDS = {field.name for field in fields(TrainerObservationV5)} - {
    'meta', 'posture', 'connection_state'}
_V5_ONLY = _V5_FIELDS - _V4_FIELDS


def _learning_health(record):
    if record is None:
        return None
    from bilqis_mlx.diagnostics.learning_health import SCHEMA
    if not isinstance(record, dict) or record.get('schema') != SCHEMA:
        from bilqis_mlx.errors import ErrorBus, SCHOOL
        ErrorBus.raise_(
            SCHOOL.BAMF_LEARNING_HEALTH.INVALID,
            reason='OBSERVATION_LEARNING_HEALTH_SCHEMA')
    values = {key: value for key, value in record.items() if key != 'schema'}
    for name in ('first', 'latest', 'best'):
        if values.get(name) is not None:
            values[name] = LearningHealthScore(**values[name])
    for name in ('regressed_protected_capabilities',
                 'prior_certified_surface_ids'):
        values[name] = tuple(values[name])
    values['warnings'] = tuple(
        LearningHealthWarning(**item) for item in values['warnings'])
    values['recent_checkpoints'] = tuple(
        LearningHealthCheckpoint(**item)
        for item in values['recent_checkpoints'])
    return LearningHealthEvidence(**values)


def _score(record):
    record = record or {'state': 'UNKNOWN'}
    state = record.get('state', 'UNKNOWN')
    return VisitCapabilityScore(
        capability_id=record.get('capability_id'), state=state,
        baseline=record.get('baseline') if state == 'MEASURED' else None,
        before=record.get('before') if state == 'MEASURED' else None,
        after=record.get('after') if state == 'MEASURED' else None,
        total=record.get('total') if state == 'MEASURED' else None,
        delta=record.get('delta') if state == 'MEASURED' else None,
        loss_allowance=record.get('loss_allowance'))


def _visit_evidence(record):
    if record is None:
        return None
    ranking = record.get('ranking') or {}
    coverage = record.get('baseline_coverage') or {}
    return VisitEvidence(
        state=record.get('state', 'PARTIAL'), grade_id=record.get('grade_id'),
        grade_definition_id=record.get('grade_definition_id'),
        grade_definition_version=record.get('grade_definition_version'),
        capability_id=record.get('capability_id'),
        semantic_ids=tuple(record.get('semantic_ids', ())),
        prerequisites=tuple(record.get('prerequisites', ())),
        semantic_prerequisites=tuple(record.get('semantic_prerequisites', ())),
        constituents=tuple(record.get('constituents', ())),
        lawful_frontier_sha256=record.get('lawful_frontier_sha256'),
        a09_snapshot_sha256=record.get('a09_snapshot_sha256'),
        a09_closure_sha256=record.get('a09_closure_sha256'),
        ranking=VisitRankingEvidence(
            policy_sha256=ranking.get('policy_digest'),
            ordinals=tuple(ranking.get('ordinals', ())),
            known=tuple(ranking.get('known', ())),
            dispatch_tier=ranking.get('dispatch_tier'),
            eligible_since=ranking.get('eligible_since'),
            downstream_unlocks=ranking.get('downstream_unlocks'),
            stable_id=ranking.get('stable_id')),
        teacher_visit_id=record.get('teacher_visit_id'),
        teacher_policy_key=record.get('teacher_policy_key'),
        selected_option_id=record.get('selected_option_id'),
        lesson_roles=tuple(VisitRoleCount(role=k, count=v)
                           for k, v in sorted((record.get('lesson_roles') or {}).items())),
        target=_score(record.get('target')),
        affected_scope_state=record.get('affected_scope_state', 'UNKNOWN'),
        affected=tuple(_score(item) for item in record.get('affected', ())),
        protected_scope_state=record.get('protected_scope_state', 'UNKNOWN'),
        protected=tuple(_score(item) for item in record.get('protected', ())),
        retention_economics_state=record.get('retention_economics_state', 'UNKNOWN'),
        retention_policy_sha256=record.get('retention_policy_sha256'),
        threshold_refs=tuple(record.get('threshold_refs', ())),
        budget_refs=tuple(record.get('budget_refs', ())),
        probe_each=record.get('probe_each'),
        baseline_measured_capabilities=tuple(coverage.get('measured_capabilities', ())),
        baseline_unmeasured_capabilities=tuple(coverage.get('unmeasured_capabilities', ())),
        baseline_epoch_sha256=coverage.get('epoch_sha256'),
        decision=record.get('decision'), blocking_capability=record.get('blocking_capability'),
        blocking_scope=record.get('blocking_scope'), reason=record.get('reason'),
        human_reason=record.get('human_reason'),
        candidate_evidence_sha256=record.get('candidate_evidence_sha256'),
        candidate_evidence_file=record.get('candidate_evidence_file'))


def _grade_evidence(record):
    if record is None:
        return None
    return GeneratedGradeEvidence(
        state=record.get('state', 'UNKNOWN'), grade_id=record.get('grade_id'),
        proposal_id=record.get('proposal_id'), definition_id=record.get('definition_id'),
        definition_version=record.get('definition_version'),
        predecessor_definition_id=record.get('predecessor_definition_id'),
        learner_evidence_epoch=record.get('learner_evidence_epoch'),
        factory_release_sha256=record.get('factory_release_sha256'),
        policy_epoch=record.get('policy_epoch'),
        a08_provenance=tuple(record.get('a08_provenance', ())),
        a09_provenance=tuple(record.get('a09_provenance', ())),
        selected_semantic_ids=tuple(record.get('selected_semantic_ids', ())),
        members=tuple(GeneratedGradeMemberEvidence(
            semantic_id=item['semantic_id'],
            developmental_cost_state=item.get('developmental_cost_state', 'UNKNOWN'),
            a08_provenance=tuple(item.get('a08_provenance', ())),
            a09_provenance=tuple(item.get('a09_provenance', ())),
            acquisition_cost_ref=item.get('acquisition_cost_ref'))
            for item in record.get('members', ())),
        developmental_slope_state=record.get('developmental_slope_state', 'UNKNOWN'),
        synthesis_dimensions=tuple(GradeSynthesisDimension(
            dimension=item['dimension'], state=item.get('state', 'UNKNOWN'),
            evidence_refs=tuple(item.get('evidence_refs', ())))
            for item in record.get('synthesis_dimensions', ())),
        representative_coverage=record.get('representative_coverage'),
        downstream_unlocks=record.get('downstream_unlocks'),
        constituent_rationale=record.get('constituent_rationale'),
        required_bridges=tuple(record.get('required_bridges', ())),
        deferred_candidates=tuple(DeferredGradeCandidate(
            semantic_id=item['semantic_id'], reasons=tuple(item.get('reasons', ())))
            for item in record.get('deferred_candidates', ())),
        holds=tuple(GeneratedGradeHold(
            code=item['code'], semantic_id=item.get('semantic_id'),
            detail=item.get('detail')) for item in record.get('holds', ())),
        predecessor_certification_receipt=record.get('predecessor_certification_receipt'))


def process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _connection(row, now_ms):
    if row.get('outcome') != 'RUNNING':
        return 'FINISHED'
    age = now_ms - row['observed_at']
    pid = row.get('process_id')
    if type(pid) is not int or pid <= 0 or age > MAX_HEARTBEAT_AGE_MS or age < -MAX_FUTURE_SKEW_MS:
        return 'DISCONNECTED'
    return 'LIVE' if process_exists(pid) else 'DISCONNECTED'


def _record(row, runs, now_ms, accepted_health=None):
    parent = runs.get((row.get('run_id'), row.get('parent_manifest_sha256')))
    if parent is None or not is_time(row.get('observed_at')):
        return None
    if (isinstance(accepted_health, dict)
            and row.get('learning_health') is None
            and row.get('outcome') != 'ACCEPTED'
            and row.get('capability_id') in accepted_health):
        try:
            _learning_health(accepted_health[row['capability_id']])
        except (ValueError, TypeError, KeyError, AttributeError):
            pass
        else:
            row = {**row, 'learning_health': accepted_health[row['capability_id']]}
    state = _connection(row, now_ms)
    identifier = f"trainer-observed:{row['observation_id']}:{row['revision']}:{state}"
    observed_at_seconds = row['observed_at'] // 1000
    meta = RecordMeta(
        record_id=identifier, run=parent, materialized_at=observed_at_seconds,
        observed_at=observed_at_seconds, as_of=None, coverage=CoverageState.PARTIAL,
        authority=AuthorityClass.MEASURED,
        source_refs=(f"trainer-observed:{row['observation_id']}",),
    )
    record_type = (
        TrainerObservationV5 if _V5_ONLY <= set(row) else
        TrainerObservationV4 if _V4_ONLY <= set(row) else
        TrainerObservationV3 if _V3_ONLY <= set(row) else
        TrainerObservationV2 if _V2_ONLY <= set(row) else TrainerObservation)
    record_fields = (
        _V5_FIELDS if record_type is TrainerObservationV5 else
        _V4_FIELDS if record_type is TrainerObservationV4 else
        _V3_FIELDS if record_type is TrainerObservationV3 else
        _V2_FIELDS if record_type is TrainerObservationV2 else _FIELDS)
    values = {
        key: row.get(key) if key in _OPTIONAL_FIELDS else row[key]
        for key in record_fields
    }
    if record_type in (TrainerObservationV3, TrainerObservationV4,
                       TrainerObservationV5):
        step_fields = {field.name for field in fields(CandidateStepPerformance)}
        values['candidate_steps'] = tuple(
            CandidateStepPerformance(**{
                key: value for key, value in item.items() if key in step_fields
            }) for item in values['candidate_steps'])
    if record_type in (TrainerObservationV4, TrainerObservationV5):
        values['visit_evidence'] = _visit_evidence(values['visit_evidence'])
        values['generated_grade_evidence'] = _grade_evidence(
            values['generated_grade_evidence'])
        values['retention_stage_timings'] = tuple(
            RetentionStageTiming(**item) for item in values['retention_stage_timings'])
    if record_type is TrainerObservationV5:
        values['learning_health'] = _learning_health(values['learning_health'])
    return record_type(
        meta=meta, posture='OBSERVED', connection_state=state, **values)


def observed_records(run_dir: Path, runs, *, now_ms=None) -> tuple[TrainerObservation, ...]:
    """Bound input bytes and rows; malformed observations cannot hide accepted state."""
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    try:
        with (Path(run_dir) / 'trainer-observed.json').open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return ()
        payload = json.loads(raw)
        if (not isinstance(payload, dict) or payload.get('schema') not in _SCHEMAS
                or not isinstance(payload.get('visits'), list)):
            return ()
    except (OSError, ValueError, UnicodeError, RecursionError):
        return ()
    parents = {(run.run_id, run.generation_manifest_sha256): run for run in runs}
    records = {}
    # Older or interrupted producers may leave more history than the current
    # reader budget.  Currentness is in the tail, so bound the projection rather
    # than discarding every observation from an otherwise valid snapshot.
    bounded_visits = payload['visits'][-MAX_VISITS:]
    accepted_health = None
    if bounded_visits:
        latest = bounded_visits[-1]
        try:
            pointer = json.loads((Path(run_dir) / 'bamf-state.json').read_text())
            if (latest.get('run_id') == pointer.get('run_id')
                    and latest.get('parent_manifest_sha256')
                    == pointer.get('manifest_sha256')):
                from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
                from bilqis_mlx.runtime.bamf_operator.learning_health_runtime import (
                    accepted_learning_health_from_parent,
                )
                accepted_health = accepted_learning_health_from_parent(
                    load_accepted_generation(Path(run_dir)))
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            accepted_health = None
    for index, row in enumerate(bounded_visits):
        try:
            health = accepted_health if index == len(bounded_visits) - 1 else None
            record = _record(row, parents, now_ms, health)
            if record is not None:
                records[record.observation_id] = record
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            continue
    return tuple(records.values())
