"""Public facade for learner-relative lawful teaching frontiers."""
from bilqis_mlx.runtime.lawful_teaching_frontier_contracts import (
    ActiveGeneratedGradeState,
    LawfulTeachingCapability,
    LawfulTeachingDisposition,
    LawfulTeachingExclusion,
    LawfulTeachingExclusionCode,
    LawfulTeachingFrontier,
    LawfulTeachingHold,
)
from bilqis_mlx.runtime.lawful_teaching_frontier_projection import (
    _active_grade_state,
    _active_member_projection,
    _capabilities,
    _evidence_digest,
    _exclusions,
    _recovery_yield_capabilities,
)

from .lawful_teaching_frontier_issue import (
    _issue_lawful_teaching_frontier_from_epoch,
    issue_lawful_teaching_frontier,
)
from .lawful_teaching_frontier_validation import (
    require_bound_lawful_teaching_frontier,
    require_current_lawful_teaching_frontier,
)
from .lawful_teaching_frontier_yield import (
    issue_recovery_yield_teaching_frontier,
)


__all__ = (
    "ActiveGeneratedGradeState",
    "LawfulTeachingCapability",
    "LawfulTeachingDisposition",
    "LawfulTeachingExclusion",
    "LawfulTeachingExclusionCode",
    "LawfulTeachingFrontier",
    "LawfulTeachingHold",
    "issue_lawful_teaching_frontier",
    "issue_recovery_yield_teaching_frontier",
    "require_bound_lawful_teaching_frontier",
    "require_current_lawful_teaching_frontier",
)
