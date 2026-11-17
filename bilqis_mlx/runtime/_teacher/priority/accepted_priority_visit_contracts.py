"""Issued result and school-view contracts for accepted priority visits."""
from dataclasses import dataclass, field
import hashlib
import json
import math
from weakref import WeakKeyDictionary

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.salience_teacher import PrioritySchoolContext, PriorityStudentIdentity


_ISSUED = WeakKeyDictionary()


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


@dataclass(frozen=True, init=False, eq=False)
class PriorityVisitResult:
    status: str
    option_id: str | None
    offer: object | None
    visit: object | None
    _policy_json: str | None
    _metadata_json: str | None
    _ranking_evidence_json: str | None
    _source_materialization_wall_seconds: float | None
    lesson_grade: str | None
    holds: tuple
    _run_dir: str
    _lawful_frontier: object = field(repr=False, compare=False)
    _cadence_authorization: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid('BAMF_PRIORITY_RESULT_CALLER_CONSTRUCTION_FORBIDDEN')

    @property
    def policy(self):
        return None if self._policy_json is None else json.loads(self._policy_json)

    @property
    def metadata(self):
        return None if self._metadata_json is None else json.loads(self._metadata_json)

    @property
    def ranking_evidence(self):
        return (None if self._ranking_evidence_json is None
                else json.loads(self._ranking_evidence_json))

    @property
    def source_materialization_wall_seconds(self):
        return self._source_materialization_wall_seconds

    @property
    def exclusions(self):
        return (() if self._lawful_frontier is None
                else self._lawful_frontier.exclusions)


def _issue_result(status, option_id, offer, visit, policy, metadata, grade, holds,
                  run_dir, lawful_frontier=None, ranking_evidence=None,
                  source_materialization_wall_seconds=None,
                  cadence_authorization=None):
    if status == 'TEACHER_SELECTED' and lawful_frontier is None:
        _invalid('BAMF_PRIORITY_LAWFUL_FRONTIER_REQUIRED')
    result = object.__new__(PriorityVisitResult)
    policy_json = None if policy is None else _json(policy)
    metadata_json = None if metadata is None else _json(metadata)
    ranking_evidence_json = None if ranking_evidence is None else _json(ranking_evidence)
    if (source_materialization_wall_seconds is not None
            and (type(source_materialization_wall_seconds) not in (int, float)
                 or not math.isfinite(source_materialization_wall_seconds)
                 or source_materialization_wall_seconds < 0)):
        _invalid('BAMF_PRIORITY_SOURCE_TIMING_INVALID')
    for name, value in (
            ('status', status), ('option_id', option_id), ('offer', offer),
            ('visit', visit), ('_policy_json', policy_json), ('_metadata_json', metadata_json),
            ('_ranking_evidence_json', ranking_evidence_json),
            ('_source_materialization_wall_seconds', source_materialization_wall_seconds),
            ('lesson_grade', grade), ('holds', tuple(holds)), ('_run_dir', str(run_dir)),
            ('_lawful_frontier', lawful_frontier),
            ('_cadence_authorization', cadence_authorization)):
        object.__setattr__(result, name, value)
    visit_digest = None if visit is None else _digest(_json(visit.identity.to_record()))
    _ISSUED[result] = (
        status, option_id, id(offer), id(visit), visit_digest,
        None if policy_json is None else _digest(policy_json),
        metadata_json, ranking_evidence_json, grade, tuple(holds), str(run_dir),
        id(lawful_frontier), id(cadence_authorization))
    return result


def _require_issued(result):
    if type(result) is not PriorityVisitResult or result not in _ISSUED:
        _invalid('BAMF_PRIORITY_RESULT_NOT_ISSUED')
    visit_digest = None if result.visit is None else _digest(_json(result.visit.identity.to_record()))
    actual = (
        result.status, result.option_id, id(result.offer), id(result.visit), visit_digest,
        None if result._policy_json is None else _digest(result._policy_json),
        result._metadata_json, result._ranking_evidence_json, result.lesson_grade,
        result.holds, result._run_dir, id(result._lawful_frontier))
    actual = (*actual, id(result._cadence_authorization))
    if actual != _ISSUED[result]:
        _invalid('BAMF_PRIORITY_RESULT_DRIFT')


def require_priority_cadence_authorization(result):
    _require_issued(result)
    authorization = result._cadence_authorization
    if authorization is None:
        return None
    from bilqis_mlx.runtime.active_grade_cadence_contracts import (
        ActiveGradeCadenceAuthorization,
    )
    if type(authorization) is not ActiveGradeCadenceAuthorization:
        _invalid('BAMF_ACTIVE_GRADE_CADENCE_AUTHORITY_INVALID')
    authorization.verify()
    return authorization


def require_priority_lawful_frontier(result):
    """Return only the live frontier retained by one issued priority result."""
    _require_issued(result)
    frontier = result._lawful_frontier
    if frontier is None:
        _invalid('BAMF_PRIORITY_LAWFUL_FRONTIER_REQUIRED')
    from bilqis_mlx.runtime.lawful_teaching_frontier_contracts import (
        LawfulTeachingFrontier,
        _is_issued,
    )
    if type(frontier) is not LawfulTeachingFrontier or not _is_issued(frontier):
        _invalid('BAMF_PRIORITY_LAWFUL_FRONTIER_INVALID')
    return frontier


def accepted_priority_school(parent, program, *, candidate_identity_sha256=None):
    """Project B13 + admitted Factory custody into C03's minimal school view."""
    from bilqis_mlx.factory.schedule import ScheduleProgram
    if not isinstance(program, ScheduleProgram):
        _invalid('BAMF_PRIORITY_PROGRAM_INVALID')
    grades = tuple(grade.id for grade in program.grades)
    if not grades:
        _invalid('BAMF_PRIORITY_PROGRAM_INVALID')
    if candidate_identity_sha256 is None:
        candidate_identity_sha256 = candidate_identity_digest(parent.retained_state)
    return PrioritySchoolContext(
        course_digest=program.digest(),
        active_grades=grades,
        current_student=PriorityStudentIdentity(candidate_identity_sha256),
    )


__all__ = (
    "PriorityVisitResult", "accepted_priority_school",
    "require_priority_cadence_authorization",
    "require_priority_lawful_frontier",
)
