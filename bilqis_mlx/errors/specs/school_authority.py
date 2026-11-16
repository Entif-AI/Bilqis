"""Operator contracts for curriculum, retained evidence and execution authority."""
from .base import _spec


class BAMF_CURRICULUM:
    INVALID = _spec(
        ('SCHOOL', 'BAMF_CURRICULUM', 'INVALID'),
        owner='runtime.priority_qualification', title='Curriculum priority authority invalid',
        message_template='Curriculum priority authority invalid: {reason}',
        disposition='PRESERVE_AND_INSPECT',
        next_action='Reload accepted learner, release and teacher authority; inspect the detailed reason before selecting work.')
    NOT_ADMITTED = _spec(
        ('SCHOOL', 'BAMF_CURRICULUM', 'NOT_ADMITTED'),
        owner='runtime.priority_qualification', title='Capability not admitted',
        message_template='Capability not admitted: {reason}', disposition='PRESERVE_AND_INSPECT',
        next_action='Use C07 to admit a source-qualified executable capability before teaching it.')
    NOT_TEACHABLE = _spec(
        ('SCHOOL', 'BAMF_CURRICULUM', 'NOT_TEACHABLE'),
        owner='runtime.priority_qualification', title='Admitted capability not currently teachable',
        message_template='Admitted capability not currently teachable: {reason}',
        disposition='PRESERVE_AND_INSPECT',
        next_action='Rebuild the current learner frontier and inspect its eligibility evidence.')
    PREREQUISITE_HELD = _spec(
        ('SCHOOL', 'BAMF_CURRICULUM', 'PREREQUISITE_HELD'),
        owner='runtime.priority_qualification', title='Prerequisite or learner evidence required',
        message_template='Prerequisite or learner evidence required: {reason}',
        disposition='PRESERVE_AND_INSPECT',
        next_action='Establish the required prerequisite evidence through lawful teaching and reassess this dependent capability.')
    SOURCE_HELD = _spec(
        ('SCHOOL', 'BAMF_CURRICULUM', 'SOURCE_HELD'),
        owner='runtime.priority_qualification', title='Source, rights or correction authority held',
        message_template='Source, rights or correction authority held: {reason}',
        disposition='PRESERVE_AND_INSPECT',
        next_action='Requalify the exact source binding, rights and correction epoch; preserve unrelated lawful work.')


class BAMF_RETENTION:
    BASELINE_ABSENT = _spec(
        ('SCHOOL', 'BAMF_RETENTION', 'BASELINE_ABSENT'),
        owner='runtime.capability_retention', title='Baseline absent or unmeasured',
        message_template='Baseline absent or unmeasured: {reason}',
        disposition='MEASURE_WITH_CURRENT_AUTHORITY',
        next_action='Obtain a lawful baseline under the current evidence identity before comparing regression.')
    COMPARABLE_REGRESSION = _spec(
        ('SCHOOL', 'BAMF_RETENTION', 'COMPARABLE_REGRESSION'),
        owner='runtime.capability_retention', title='Comparable retention regression',
        message_template='Comparable retention regression: {reason}',
        disposition='PRESERVE_AND_INSPECT',
        next_action="Inspect the producer's blocking capability or scope and comparable evidence; preserve the accepted learner.")


class BAMF_B11:
    SOURCE_EXECUTION_AUTHORITY_INVALID = _spec(
        ('SCHOOL', 'BAMF_B11', 'SOURCE_EXECUTION_AUTHORITY_INVALID'),
        owner='runtime.b11_source_execution_authority', title='B11 exact source execution authority invalid',
        message_template='B11 exact source execution authority invalid: {reason}',
        disposition='PRESERVE_AND_INSPECT',
        next_action='Rebind the exact emitted row to its canonical source owner and current rights/correction authority before execution.')


class BAMF_ADMISSION:
    LEASE_REQUIRED = _spec(
        ('SCHOOL', 'BAMF_ADMISSION', 'LEASE_REQUIRED'),
        owner='runtime.atlas_flywheel', title='C07 admission lease required',
        message_template='C07 admission lease required: {reason}', disposition='PRESERVE_AND_INSPECT',
        next_action='Use the existing explicit enrollment path for an accepted lease covering this successor.')
    WAITING_FOR_EVIDENCE = _spec(
        ('SCHOOL', 'BAMF_ADMISSION', 'WAITING_FOR_EVIDENCE'),
        owner='runtime.atlas_flywheel', title='C07 waiting for learner evidence',
        message_template='C07 waiting for learner evidence: {reason}', disposition='PRESERVE_AND_INSPECT',
        next_action="Establish the planner's required learner evidence and replan through C07.")
    HELD = _spec(
        ('SCHOOL', 'BAMF_ADMISSION', 'HELD'),
        owner='runtime.atlas_flywheel', title='C07 admission held',
        message_template='C07 admission held: {reason}', disposition='PRESERVE_AND_INSPECT',
        next_action='Inspect the exact admission hold and source/custody authority before retrying.')
    IMPLEMENTATION_UNCOVERED = _spec(
        ('SCHOOL', 'BAMF_ADMISSION', 'IMPLEMENTATION_UNCOVERED'),
        owner='runtime.atlas_flywheel', title='C07 implementation uncovered',
        message_template='C07 implementation uncovered: {reason}', disposition='PRESERVE_AND_INSPECT',
        next_action='Implement and independently qualify the missing Factory construction before admission.')
    FIXED_POINT = _spec(
        ('SCHOOL', 'BAMF_ADMISSION', 'FIXED_POINT'),
        owner='runtime.atlas_flywheel', title='C07 no ready delta',
        message_template='C07 no ready delta: {reason}', disposition='NO_READY_DELTA',
        next_action='Inspect current coverage and obligations; replan only after source, evidence or admission state changes.')
