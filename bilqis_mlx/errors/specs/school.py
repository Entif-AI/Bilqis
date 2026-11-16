"""Typed school error contracts."""
from __future__ import annotations

from .state_identity import StateIdentity
from .state_assessment import StateAssessment


class STATE(StateIdentity, StateAssessment):
    """Stable school-state namespace; identity and assessment contracts share one owner."""


class SCHOOL:
    from .school_custody import CHECKPOINT_CUSTODY as CHECKPOINT_CUSTODY
    from .school_bamf import BAMF_DELIVERY as BAMF_DELIVERY
    from .school_bamf import BAMF_PACKAGE as BAMF_PACKAGE
    from .school_bamf import BAMF_CONTROL_PLANE as BAMF_CONTROL_PLANE
    from .school_operator import BAMF_OPERATOR as BAMF_OPERATOR
    from .school_bamf import BAMF_FIRST_STUDENT as BAMF_FIRST_STUDENT
    from .school_bamf import BAMF_ATLAS_ADMISSION as BAMF_ATLAS_ADMISSION
    from .school_bamf import BAMF_SALIENCE as BAMF_SALIENCE
    from .school_bamf import BAMF_CAPABILITY_EVIDENCE as BAMF_CAPABILITY_EVIDENCE
    from .school_bamf import BAMF_SOLVER as BAMF_SOLVER
    from .school_bamf import BAMF_AKASHA as BAMF_AKASHA
    from .school_bamf import BAMF_RESOURCES as BAMF_RESOURCES
    from .school_bamf import BAMF_REVALIDATION as BAMF_REVALIDATION
    from .school_bamf import BAMF_TEACHER as BAMF_TEACHER
    from .school_bamf import BAMF_TRAINING_ADAPTER as BAMF_TRAINING_ADAPTER
    from .school_bamf import BAMF_WORKSTACK as BAMF_WORKSTACK
    from .school_bamf import QUALIFICATION as QUALIFICATION
    from .school_bamf import TEACHER_OBSERVATION as TEACHER_OBSERVATION
    from .school_bamf import MODEL_TOPOLOGY as MODEL_TOPOLOGY
    from .school_lifecycle import RESUME as RESUME
    from .school_lifecycle import SCHEDULE as SCHEDULE
    from .school_lifecycle import LEARNING as LEARNING
    STATE = STATE
