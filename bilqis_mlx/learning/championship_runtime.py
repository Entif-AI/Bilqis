"""Fresh title adjudication and championship evidence orchestration.

Implementation lives in small internal modules; this facade preserves the established API.
"""
from .capability_championship import (
    assessment_exam as complete_solver_championship_exam,
    assessment_path_attribution,
    assessment_progress,
    fresh_title_match as fresh_complete_solver_title_match,
)
from ._championship_runtime.exams import (
    _compare_incumbents, _epoch_paired_examinations,
)
from ._championship_runtime.governance import (
    _championship_identity, _championship_pair_key,
    _historical_championship_authority, _is_profile_revision_epoch_history_artifact,
    _live_championship_identity, _repair_profile_revision_epoch_history,
    _without_profile_revision_epoch_history_artifact,
)
from ._championship_runtime.matches import (
    _fresh_battery_results, _fresh_fanout_screen, _fresh_title_match,
)
from ._championship_runtime.migration import (
    _bind_checkpoint_origin, _migrate_championship_governance,
)
from ._championship_runtime.orchestration import (
    _advance_exam_championship_group, _advance_exam_championships,
)
from ._championship_runtime.witnesses import (
    _championship_correct_questions, _championship_questions,
    _fresh_title_current_exam, _hydrate_championship_witnesses,
    _readable_championship_rows,
)
