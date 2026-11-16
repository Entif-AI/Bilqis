"""Authority labels preserve distinctions without manufacturing learner evidence."""
import pytest

from bilqis_mlx.errors import SCHOOL
from bilqis_mlx.errors.authority import authority_label, authority_report


@pytest.mark.parametrize('reason,spec', [
    ('CAPABILITY_NOT_ADMITTED', SCHOOL.BAMF_CURRICULUM.NOT_ADMITTED),
    ('CAPABILITY_NOT_TEACHABLE', SCHOOL.BAMF_CURRICULUM.NOT_TEACHABLE),
    ('PREREQUISITE_HELD', SCHOOL.BAMF_CURRICULUM.PREREQUISITE_HELD),
    ('LEARNER_EVIDENCE_HELD', SCHOOL.BAMF_CURRICULUM.PREREQUISITE_HELD),
    ('SOURCE_OFFER_HELD', SCHOOL.BAMF_CURRICULUM.SOURCE_HELD),
    ('SOURCE_OFFER_MISSING', SCHOOL.BAMF_CURRICULUM.SOURCE_HELD),
    ('RIGHTS_HELD', SCHOOL.BAMF_CURRICULUM.SOURCE_HELD),
    ('CORRECTION_HELD', SCHOOL.BAMF_CURRICULUM.SOURCE_HELD),
    ('BASELINE_ABSENT', SCHOOL.BAMF_RETENTION.BASELINE_ABSENT),
    ('UNMEASURED', SCHOOL.BAMF_RETENTION.BASELINE_ABSENT),
    ('NOT_MEASURED', SCHOOL.BAMF_RETENTION.BASELINE_ABSENT),
])
def test_reason_reports_bind_exact_owner_and_recovery(reason, spec):
    report = authority_report(reason)
    assert report.code == spec.code
    assert reason in report.summary
    assert report.next_action == spec.recovery.next_action
    assert report.preserve_state


@pytest.mark.parametrize('reason', ['BASELINE_ABSENT', 'NOT_MEASURED', 'UNMEASURED'])
def test_missing_baseline_never_renders_regressed(reason):
    assert 'regress' not in authority_label(reason).lower()


def test_reported_regression_names_exact_blocker_without_claiming_new_evidence():
    label = authority_label('PROTECTED_CAPABILITY_REGRESSION', blocking_capability='Z.retained')
    assert 'PROTECTED_CAPABILITY_REGRESSION' in label
    assert 'blocking capability Z.retained' in label
    assert 'blocking scope unspecified' in authority_label('WHOLE_SCHOOL_NET_REGRESSION')
    assert 'blocking scope exact-scope' in authority_label(
        'ACTIVE_SCHOOL_GRADE_REGRESSION', blocking_scope='exact-scope')


@pytest.mark.parametrize('status', ['LEASE_REQUIRED', 'WAITING_FOR_EVIDENCE', 'HELD',
                                   'IMPLEMENTATION_UNCOVERED', 'FIXED_POINT'])
def test_admission_status_uses_exact_typed_meaning(status):
    report = authority_report(status, domain='admission')
    assert report.code == getattr(SCHOOL.BAMF_ADMISSION, status).code
    assert authority_label(status, domain='admission') == report.title


def test_unknown_and_planning_selection_do_not_invent_authority():
    for value in ('A09_PLANNING_UNAVAILABLE', 'CUSTOM_REASON', 'ALMOST_FIXED_POINT'):
        assert authority_label(value) == value
        assert authority_report(value) is None
    assert authority_label(None) == 'UNKNOWN'
    assert authority_report('HELD') is None
    assert authority_report('SOURCE_HELD').code != authority_report('PREREQUISITE_HELD').code
