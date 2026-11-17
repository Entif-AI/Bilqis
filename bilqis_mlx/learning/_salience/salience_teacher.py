"""Grade-neutral WHAT dispatch into the existing replay teacher's HOW selector."""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
import re

from ..curriculum.state import SchoolState
from ..factory.schedule import ScheduleProgram
from ..runtime.teacher_policy_selection import select_visit_policy
from ..semantics.domains import contract_digest
from .atlas_salience import SalienceEvidence, rank_attention_options, salience_priority_features
from .learning_experiment import Settings
from .salience_contracts import ActionKind, AttentionOption, AuthoritySnapshot, _invalid, _name, _sha
from .salience_history import SalienceHistory, completed_windows
from .teacher_strategy_population import BAMF_SUCCESSOR_SELECTION, effective_policy_key
from .teacher_vnext_replay import TeacherEpoch


@dataclass(frozen=True)
class AttentionFrontier:
    options: tuple[AttentionOption, ...]
    evidence: tuple[tuple[str, SalienceEvidence], ...]
    snapshot: AuthoritySnapshot

    def __post_init__(self):
        if (not isinstance(self.options, tuple) or not isinstance(self.evidence, tuple)
                or any(not isinstance(item, tuple) or len(item) != 2 for item in self.evidence)
                or len(dict(self.evidence)) != len(self.evidence)
                or set(dict(self.evidence)) != {option.stable_id for option in self.options}):
            _invalid("BAMF_SALIENCE_FRONTIER_INVALID")
        rank_attention_options(self.options, dict(self.evidence), self.snapshot)


@dataclass(frozen=True)
class PriorityStudentIdentity:
    """The only student fact C03 priority selection needs from school custody."""
    sha256: str

    def __post_init__(self):
        if re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None:
            _invalid("BAMF_PRIORITY_STUDENT_IDENTITY_INVALID")


@dataclass(frozen=True)
class PrioritySchoolContext:
    """Grade-neutral C03 view of accepted BAMF custody, not legacy SchoolState."""
    course_digest: str
    active_grades: tuple[str, ...]
    current_student: PriorityStudentIdentity
    stage: str = "MAIN"

    def __post_init__(self):
        if (not _sha(self.course_digest)
                or not isinstance(self.active_grades, tuple) or not self.active_grades
                or any(not _name(grade) for grade in self.active_grades)
                or len(set(self.active_grades)) != len(self.active_grades)
                or not isinstance(self.current_student, PriorityStudentIdentity)
                or self.stage not in {"MAIN", "RECOVERY_1", "RECOVERY_2"}):
            _invalid("BAMF_PRIORITY_SCHOOL_CONTEXT_INVALID")


def propose_attention_options(frontier, history):
    if not isinstance(frontier, AttentionFrontier) or not isinstance(history, SalienceHistory):
        _invalid("BAMF_SALIENCE_FRONTIER_OR_HISTORY_REQUIRED")
    # History nominates investigation only; it never creates a teaching option.
    completed_windows(history)
    return rank_attention_options(frontier.options, dict(frontier.evidence), frontier.snapshot)


def _teacher(epoch, school):
    if (not isinstance(epoch, TeacherEpoch)
            or not isinstance(school, (SchoolState, PrioritySchoolContext))
            or epoch.schema != "bilqis.bamf.teacher-epoch/v1"
            or epoch.replay_head != "d21797e72365bf93ea7cad3a4ef9020ec9817f23"
            or not _sha(epoch.student_sha256) or school.current_student.sha256 != epoch.student_sha256
            or not _name(epoch.prior_region) or not _name(epoch.current_region)
            or epoch.prior_region == epoch.current_region):
        _invalid("BAMF_SALIENCE_TEACHER_EPOCH_INVALID")
    try:
        teacher, prior = epoch.teacher(), epoch.prior_teacher()
        json.dumps((teacher, prior), allow_nan=False)
        if (teacher.get("selection_contract") != BAMF_SUCCESSOR_SELECTION
                or teacher["causal_experiment"]["student_policy_epoch"]["student_sha256"] != epoch.student_sha256
                or not isinstance(prior, dict) or not isinstance(teacher.get("strategies"), dict)
                or not teacher["strategies"]):
            _invalid("BAMF_SALIENCE_TEACHER_EPOCH_INVALID")
        for policy in teacher['strategies'].values():
            effective_policy_key(policy)
    except (ValueError, TypeError, KeyError, AttributeError):
        _invalid("BAMF_SALIENCE_TEACHER_RECORD_INVALID")
    return teacher


@dataclass(frozen=True)
class PriorityTeachingDecision:
    status: str
    selected_option_id: str | None
    salience_inputs_digest: str | None
    policy_key: str | None
    policy_json: str | None
    metadata_json: str | None
    teacher_epoch: TeacherEpoch
    lesson_grade: str | None = None
    schema_version: str = "bilqis.c06.priority-teaching/v1"


def choose_priority_teaching(frontier, history, teacher_epoch, engine, school, rng,
                            learning_settings, *, program, total_capabilities=None,
                            plasticity_escape=None):
    teacher = _teacher(teacher_epoch, school)
    if (not isinstance(program, ScheduleProgram) or school.course_digest != program.digest()):
        _invalid("BAMF_SALIENCE_TEACHER_ROSTER_DRIFT")
    if not isinstance(learning_settings, Settings):
        _invalid("BAMF_SALIENCE_CONTEXTUAL_SETTINGS_REQUIRED")
    ranked = propose_attention_options(frontier, history)
    if not ranked.ordered:
        return PriorityTeachingDecision("NO_ADMISSIBLE_TEACHING", None, None, None, None, None, teacher_epoch)
    option = ranked.ordered[0]
    evidence = dict(frontier.evidence)[option.stable_id]
    salience_priority_features(evidence, option.context.capability_id, option.context.scope,
                              contract_digest(teacher_epoch))
    if option.action_kind in (ActionKind.CORRECTION, ActionKind.PROCEDURE_REPAIR):
        return PriorityTeachingDecision("ACTION_REQUIRED", option.stable_id, option.salience_inputs_digest,
                                        None, None, None, teacher_epoch)
    membership = tuple(grade.id for grade in program.grades
                       if any(capability.id == option.context.capability_id for capability in grade.capabilities))
    if len(membership) != 1:
        _invalid("BAMF_SALIENCE_TEACHER_CAPABILITY_NOT_ADMITTED")
    lesson_grade = membership[0]
    key, policy, metadata = select_visit_policy(
        engine, teacher, option.context.capability_id, school, rng, learning_settings,
        option.context.scope,
        {"salience_evidence": evidence, "teacher_epoch_digest": contract_digest(teacher_epoch)},
        lesson_grade, total_capabilities=total_capabilities, plasticity_escape=plasticity_escape)
    return PriorityTeachingDecision("TEACHER_SELECTED", option.stable_id, option.salience_inputs_digest,
        key, json.dumps(policy, sort_keys=True, allow_nan=False),
        json.dumps(metadata, sort_keys=True, allow_nan=False),
        replace(teacher_epoch, current_json=json.dumps(teacher, sort_keys=True, allow_nan=False)),
        lesson_grade=lesson_grade)
