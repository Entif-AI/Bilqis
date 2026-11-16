"""Read-only labels for decisions issued by curriculum, C05 and C07 owners."""
from types import MappingProxyType

from .bus import ErrorBus
from .catalog import SCHOOL
from .model import BilqisError, ErrorReport


_CURRICULUM = MappingProxyType({
    'CAPABILITY_NOT_ADMITTED': SCHOOL.BAMF_CURRICULUM.NOT_ADMITTED,
    'CAPABILITY_NOT_TEACHABLE': SCHOOL.BAMF_CURRICULUM.NOT_TEACHABLE,
    'PREREQUISITE_HELD': SCHOOL.BAMF_CURRICULUM.PREREQUISITE_HELD,
    'LEARNER_EVIDENCE_HELD': SCHOOL.BAMF_CURRICULUM.PREREQUISITE_HELD,
    'SOURCE_OFFER_HELD': SCHOOL.BAMF_CURRICULUM.SOURCE_HELD,
    'SOURCE_OFFER_MISSING': SCHOOL.BAMF_CURRICULUM.SOURCE_HELD,
    'SOURCE_HELD': SCHOOL.BAMF_CURRICULUM.SOURCE_HELD,
    'RIGHTS_HELD': SCHOOL.BAMF_CURRICULUM.SOURCE_HELD,
    'CORRECTION_HELD': SCHOOL.BAMF_CURRICULUM.SOURCE_HELD,
})
_RETENTION = MappingProxyType({
    'UNMEASURED': SCHOOL.BAMF_RETENTION.BASELINE_ABSENT,
    'NOT_MEASURED': SCHOOL.BAMF_RETENTION.BASELINE_ABSENT,
    'BASELINE_ABSENT': SCHOOL.BAMF_RETENTION.BASELINE_ABSENT,
    'TARGET_BASELINE_REGRESSION': SCHOOL.BAMF_RETENTION.COMPARABLE_REGRESSION,
    'PROTECTED_CAPABILITY_REGRESSION': SCHOOL.BAMF_RETENTION.COMPARABLE_REGRESSION,
    'FIXED_LESSON_GRADE_REGRESSION': SCHOOL.BAMF_RETENTION.COMPARABLE_REGRESSION,
    'ACTIVE_SCHOOL_GRADE_REGRESSION': SCHOOL.BAMF_RETENTION.COMPARABLE_REGRESSION,
    'WHOLE_SCHOOL_NET_REGRESSION': SCHOOL.BAMF_RETENTION.COMPARABLE_REGRESSION,
})
_ADMISSION = MappingProxyType({
    'LEASE_REQUIRED': SCHOOL.BAMF_ADMISSION.LEASE_REQUIRED,
    'WAITING_FOR_EVIDENCE': SCHOOL.BAMF_ADMISSION.WAITING_FOR_EVIDENCE,
    'HELD': SCHOOL.BAMF_ADMISSION.HELD,
    'IMPLEMENTATION_UNCOVERED': SCHOOL.BAMF_ADMISSION.IMPLEMENTATION_UNCOVERED,
    'FIXED_POINT': SCHOOL.BAMF_ADMISSION.FIXED_POINT,
})


def authority_report(reason, *, domain=None) -> ErrorReport | None:
    """Explain an exact owner-issued reason; unknown reasons retain their identity."""
    reason = str(reason or 'UNKNOWN')
    if domain == 'admission':
        spec = _ADMISSION.get(reason)
    elif domain == 'retention':
        spec = _RETENTION.get(reason)
    elif domain == 'curriculum':
        spec = _CURRICULUM.get(reason)
    elif domain is None:
        spec = _CURRICULUM.get(reason) or _RETENTION.get(reason)
    else:
        spec = None
    return None if spec is None else ErrorBus.report(BilqisError(spec, {'reason': reason}))


def authority_label(reason, *, domain=None, blocking_capability=None, blocking_scope=None) -> str:
    """Render reported decisions without deriving baselines or mastery from scores."""
    report = authority_report(reason, domain=domain)
    if report is None:
        return str(reason or 'UNKNOWN')
    if report.code != SCHOOL.BAMF_RETENTION.COMPARABLE_REGRESSION.code:
        return report.title
    if blocking_capability:
        blocker = 'blocking capability ' + str(blocking_capability)
    elif blocking_scope:
        blocker = 'blocking scope ' + str(blocking_scope)
    else:
        blocker = 'blocking scope unspecified'
    return f'{report.title} | {reason} | {blocker}'
