"""C16.3 production owner for the first BAMF C03 bootstrap and trajectory."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import random

from bilqis_mlx.compatibility.legacy_trainer_authority import live_authority
from bilqis_mlx.compatibility import historical_teacher_policy
from bilqis_mlx.learning.teacher_lineage import adaptation_authority_ref
from bilqis_mlx.learning.teacher_lineage import (
    advance_priority_rotation, record_instruction_history,
)
from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
from bilqis_mlx.learning.teacher_lineage_records import digest, invalid
from bilqis_mlx.runtime.accepted_teacher_custody import BoundTeacherVisit


TRAJECTORY_SCHEMA = "bilqis.bamf.c16.3-teacher-trajectory/v1"
_BOOTSTRAP_ISSUER = object()
_ADVANCE_ISSUER = object()


@dataclass(frozen=True, init=False)
class FoundationTeacherBootstrap:
    """Unforgeable source-derived bootstrap for a pre-C03 accepted student."""

    legacy_receipt: dict
    adaptation: dict
    prior_region: str
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        invalid("TEACHER_BOOTSTRAP_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self):
        if (
            getattr(self, "_issuance", None) is not _BOOTSTRAP_ISSUER
            or not isinstance(self.legacy_receipt.get("teacher"), dict)
            or not isinstance(self.adaptation, dict)
            or not isinstance(self.prior_region, str)
            or not self.prior_region
        ):
            invalid("TEACHER_BOOTSTRAP_AUTHORITY_INVALID")


@dataclass(frozen=True, init=False)
class TeacherTrajectoryAdvance:
    """Owner-issued next accepted C03 trajectory coordinates."""

    next_seed: int
    cursor: str
    policy_schema: str
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        invalid("TEACHER_TRAJECTORY_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self):
        if (
            getattr(self, "_issuance", None) is not _ADVANCE_ISSUER
            or type(self.next_seed) is not int
            or self.next_seed < 0
            or not isinstance(self.cursor, str)
            or not self.cursor
            or self.policy_schema != TRAJECTORY_SCHEMA
        ):
            invalid("TEACHER_TRAJECTORY_INVALID")


def foundation_teacher_bootstrap() -> FoundationTeacherBootstrap:
    """Bind the declared latest legacy teacher without importing its learner."""
    authority, observed_head, current = live_authority()
    teacher = current["teacher"]
    adaptation = adaptation_authority_ref(
        authority, observed_source_head=observed_head)
    prior_region = digest({
        "schema": "bilqis.bamf.c16.3-prior-teacher-region/v1",
        "adaptation": adaptation,
        "teacher_sha256": digest(teacher),
    })
    result = object.__new__(FoundationTeacherBootstrap)
    for name, value in (
        ("legacy_receipt", {"teacher": teacher}),
        ("adaptation", adaptation),
        ("prior_region", prior_region),
        ("_issuance", _BOOTSTRAP_ISSUER),
    ):
        object.__setattr__(result, name, value)
    result.__post_init__()
    return result


def current_foundation_teacher_projection(run_dir):
    """Project the current accepted C03 teacher without selecting a capability."""
    from bilqis_mlx.runtime.accepted_teacher_custody import (
        _accepted_parent, _c03_projection, current_teacher_projection,
    )

    parent, cache = _accepted_parent(run_dir)
    state = parent.teacher_state
    bootstrap = {"legacy_receipt": None, "adaptation": None, "prior_region": None}
    if "c03_lineage" not in state:
        owned = foundation_teacher_bootstrap()
        bootstrap = {
            "legacy_receipt": owned.legacy_receipt,
            "adaptation": owned.adaptation,
            "prior_region": owned.prior_region,
        }
    projection = _c03_projection(parent, **bootstrap)
    projection = current_teacher_projection(run_dir, parent, cache, projection)
    restore_teacher_lineage(projection.teacher_state)
    return projection


def select_foundation_priority_visit(
        run_dir, source_context, atlas_artifact_path, *, program, school,
        progress=None, resource_holds=frozenset()):
    """Compose C16.3 bootstrap with the production C03.4 priority owner."""
    from bilqis_mlx.learning.learning_experiment import Settings
    from bilqis_mlx.runtime.accepted_priority_visit import select_accepted_priority_visit
    from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
    from bilqis_mlx.runtime.priority_authority import issue_foundation_priority_authority

    parent = load_accepted_generation(run_dir)
    projection = current_foundation_teacher_projection(run_dir)
    epoch = restore_teacher_lineage(projection.teacher_state)
    authority = issue_foundation_priority_authority(
        run_dir, source_context, parent, epoch, atlas_artifact_path,
        teacher_state=projection.teacher_state, progress=progress)
    if authority.cadence.phase.value in {"MAIN", "RECOVERY_1", "RECOVERY_2"}:
        school = replace(school, stage=authority.cadence.phase.value)
    bootstrap = {"legacy_receipt": None, "adaptation": None, "prior_region": None}
    if "c03_lineage" not in parent.teacher_state:
        owned = foundation_teacher_bootstrap()
        bootstrap = {
            "legacy_receipt": owned.legacy_receipt,
            "adaptation": owned.adaptation,
            "prior_region": owned.prior_region,
        }
    if progress is not None:
        progress("teacher: selecting current priority visit")
    result = select_accepted_priority_visit(
        run_dir, source_context, authority.frontier, authority.history,
        authority.planning,
        authority.offers, historical_teacher_policy, school,
        random.Random(parent.teacher_state["next_seed"]), Settings(),
        program=program, now=authority.now,
        lawful_frontier=authority.lawful_frontier,
        cadence_authorization=authority.cadence,
        total_capabilities=len(source_context.release.execution_plan.capabilities),
        accepted_parent=parent, planning_generation=authority.planning_generation,
        resource_holds=resource_holds, **bootstrap)
    if progress is not None:
        progress(f"teacher: priority selection complete ({result.status})")
    return result


def accepted_teacher_trajectory(visit: BoundTeacherVisit) -> TeacherTrajectoryAdvance:
    """Advance only from the exact accepted visit identity.

    C16.3 deliberately defines a BAMF-native generic trajectory instead of
    inheriting the retired trainer's receipt/generation hash RNG.  The cursor is
    an opaque accepted-visit chain identity, not a source row or grade position.
    Rejected candidates never call this owner and therefore burn no seed.
    """
    if type(visit) is not BoundTeacherVisit:
        invalid("TEACHER_VISIT_CUSTODY_REQUIRED")
    visit.__post_init__()
    result = object.__new__(TeacherTrajectoryAdvance)
    for name, value in (
        ("next_seed", visit.identity.selection_seed + 1),
        ("cursor", visit.identity.visit_id),
        ("policy_schema", TRAJECTORY_SCHEMA),
        ("_issuance", _ADVANCE_ISSUER),
    ):
        object.__setattr__(result, name, value)
    result.__post_init__()
    return result


def derive_accepted_teacher_successor(
        run_dir, retained_state, visit: BoundTeacherVisit, *,
        delivery_events: tuple, candidate_transaction=None):
    """Build an accepted B13 successor with C16.3-owned trajectory state."""
    from bilqis_mlx.runtime.accepted_teacher_custody import (
        derive_c03_successor_bundle,
    )
    trajectory = accepted_teacher_trajectory(visit)
    candidate = derive_c03_successor_bundle(
        run_dir, retained_state, visit,
        next_seed=trajectory.next_seed, cursor=trajectory.cursor,
        delivery_events=delivery_events,
        candidate_transaction=candidate_transaction)
    from dataclasses import replace
    teacher_state = advance_priority_rotation(
        candidate.teacher_state, visit.identity.capability_id)
    for event in delivery_events:
        if (isinstance(event, dict)
                and event.get("event") == "BAMF_INSTRUCTION_HISTORY"
                and event.get("schema") == "bilqis.bamf.instruction-history/v1"):
            teacher_state = record_instruction_history(
                teacher_state, event.get("capability_ids", ()),
                state=event.get("state"))
    return replace(candidate, teacher_state=teacher_state)


__all__ = (
    "FoundationTeacherBootstrap", "TeacherTrajectoryAdvance",
    "TRAJECTORY_SCHEMA", "accepted_teacher_trajectory",
    "current_foundation_teacher_projection", "derive_accepted_teacher_successor",
    "foundation_teacher_bootstrap", "select_foundation_priority_visit",
)
