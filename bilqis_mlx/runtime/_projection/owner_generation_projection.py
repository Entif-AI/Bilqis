"""Accepted B13/C07 owner projections into the C10 immutable envelope."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.semantics.domains import contract_digest

from .akasha_outbox import AkashaEventKind, _invalid


def _factory_release(issue, require_source, source):
    from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
        ParsedFactoryReleaseAdmissionBinding,
    )
    source = require_source(source)
    student, binding = source.student, source.binding
    if not isinstance(binding, ParsedFactoryReleaseAdmissionBinding):
        return None
    return issue(
        kind=AkashaEventKind.FACTORY_RELEASE,
        subject_id="factory-release:" + binding.factory_release_sha256,
        source_receipt_sha256=binding.digest,
        payload={
            "run_id": student.run_id,
            "generation": student.generation,
            "owner_event_type": "BAMF_FACTORY_RELEASE_ADOPTION_COMMITTED",
            "predecessor_factory_release_sha256":
                binding.predecessor_factory_release_sha256,
            "factory_release_sha256": binding.factory_release_sha256,
            "transition_sha256": binding.transition_sha256,
            "admission_receipt_sha256": binding.digest,
        },
        source_time=None, effective_time=None, observed_at=None, recorded_at=None)


def _teacher_visit(issue, require_source, source):
    from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
    from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
    from bilqis_mlx.learning.teacher_visit_identity import TeacherVisitIdentity
    source = require_source(source)
    if source.parent is None or source.parent_binding is None:
        return None
    teacher_state = source.student.teacher_state
    record = teacher_state.get("last_visit")
    if record is None:
        return None
    restore_teacher_lineage(teacher_state)
    visit = TeacherVisitIdentity.from_record(record)
    if (visit.generation != source.parent.generation
            or visit.accepted_manifest_sha256
            != source.student.parent_manifest_sha256
            or visit.student_sha256
            != candidate_identity_digest(source.parent.retained_state)):
        _invalid("BAMF_C10_TEACHER_VISIT_OWNER_DRIFT")
    return issue(
        kind=AkashaEventKind.TEACHER_VISIT,
        subject_id="teacher-visit:" + visit.visit_id,
        source_receipt_sha256=source.binding.digest,
        payload={
            "run_id": source.student.run_id,
            "generation": visit.generation,
            "visit_id": visit.visit_id,
            "accepted_manifest_sha256": visit.accepted_manifest_sha256,
            "teacher_identity": visit.teacher_identity,
            "student_sha256": visit.student_sha256,
            "capability_id": visit.capability_id,
            "policy_key": visit.policy_key,
            "admission_receipt_sha256": source.binding.digest,
        },
        source_time=None, effective_time=None, observed_at=None, recorded_at=None)


def _bank_allocation(issue, require_source, source):
    from bilqis_mlx.runtime.bamf_bundle.atlas_admission import (
        ParsedAtlasAdmissionBinding,
    )
    source = require_source(source)
    student, binding = source.student, source.binding
    if (not isinstance(binding, ParsedAtlasAdmissionBinding)
            or dict(student.transition).get("kind") != "PARAMETER_EXTENSION"):
        return None
    return issue(
        kind=AkashaEventKind.BANK_ALLOCATION,
        subject_id="feature-allocation:" + binding.feature_sha256,
        source_receipt_sha256=binding.digest,
        payload={
            "run_id": student.run_id,
            "generation": student.generation,
            "transition_kind": "PARAMETER_EXTENSION",
            "feature_sha256": binding.feature_sha256,
            "factory_release_sha256": binding.factory_release_sha256,
            "admission_receipt_sha256": binding.digest,
        },
        source_time=None, effective_time=None, observed_at=None, recorded_at=None)


def _motif(issue, require_source, source):
    from bilqis_mlx.learning.atlas_acceptance import (
        MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
        EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
    )
    from bilqis_mlx.runtime.bamf_bundle.motif.transition import (
        is_motif_allocation_transition, validate_motif_allocation_transition,
    )
    from bilqis_mlx.runtime.bamf_bundle.records import canonical, sha
    source = require_source(source)
    student, binding = source.student, source.binding
    transition = dict(student.transition)
    if (getattr(binding, "schema_version", None) not in (
            MOTIF_CLOSURE_ACCEPTANCE_SCHEMA, EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA)
            or not is_motif_allocation_transition(transition)):
        return None
    validate_motif_allocation_transition(transition)
    return issue(
        kind=AkashaEventKind.MOTIF_CANDIDATE,
        subject_id="motif-candidate:" + transition["motif_candidate_sha256"],
        source_receipt_sha256=binding.digest,
        payload={
            "run_id": student.run_id,
            "generation": student.generation,
            "motif_candidate_sha256": transition["motif_candidate_sha256"],
            "approved_context_sha256": transition["approved_context_sha256"],
            "candidate_allocation_sha256": transition["candidate_allocation_sha256"],
            "transition_sha256": sha(canonical(transition)),
            "added_pages": transition["added_pages"],
            "admission_receipt_sha256": binding.digest,
        },
        source_time=None, effective_time=None, observed_at=None, recorded_at=None)


def _plasticity(issue, require_source, source):
    source = require_source(source)
    student, binding = source.student, source.binding
    parent, parent_binding = source.parent, source.parent_binding
    if parent_binding is None or parent is None:
        return None
    parent_policy = contract_digest(parent.retained_state.policy.to_record())
    policy = contract_digest(student.retained_state.policy.to_record())
    if policy == parent_policy:
        return None
    return issue(
        kind=AkashaEventKind.PLASTICITY_EPOCH,
        subject_id=f"plasticity:{student.run_id}:{student.generation}",
        source_receipt_sha256=binding.digest,
        payload={
            "run_id": student.run_id,
            "generation": student.generation,
            "optimizer_step": student.retained_state.optimizer_step,
            "mode": student.retained_state.policy.mode,
            "parent_policy_sha256": parent_policy,
            "policy_sha256": policy,
            "parent_acceptance_receipt_sha256": parent_binding.digest,
            "admission_receipt_sha256": binding.digest,
        },
        source_time=None, effective_time=None, observed_at=None, recorded_at=None)


def _project(events, domain):
    from .bamf_projection import (
        BamfProjectionEvent, ProjectionDomainContract, project_generation_outbox,
    )
    if not isinstance(domain, ProjectionDomainContract):
        _invalid("BAMF_C10_OWNER_PROJECTION_DOMAIN_REQUIRED")
    projected = tuple(BamfProjectionEvent(
        event, domain.source_id, domain.release_digest, domain.model_digest,
        domain.evaluator_digest, domain.rights_digest, domain.as_of)
        for event in events)
    return project_generation_outbox(projected, domain)


def build_generation_adapters(issue, load_source, require_source):
    """Bind private capabilities into the two public generation adapter operations."""
    adapters = (
        _factory_release, _teacher_visit, _bank_allocation, _motif, _plasticity)

    def events_from(run_dir: Path):
        source = load_source(Path(run_dir))
        events = tuple(
            adapter(issue, require_source, source) for adapter in adapters)
        return tuple(event for event in events if event is not None)

    def append(run_dir: Path, domain):
        return _project(events_from(run_dir), domain)

    return events_from, append
