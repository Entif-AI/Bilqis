"""Reusable real-owner mechanics for the disposable C16.2c witness."""
from __future__ import annotations

import random
from pathlib import Path
from types import SimpleNamespace

from bilqis_mlx.compatibility import historical_teacher_policy
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_candidate import resolve_candidate
from bilqis_mlx.learning.atlas_retention_decision import issue_factory_retention_decision
from bilqis_mlx.learning.learning_experiment import Settings
from bilqis_mlx.learning.student_ops import train_bamf_factory_step
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.accepted_teacher_custody import select_accepted_teacher_visit
from bilqis_mlx.runtime.atlas_visit_provenance import BamfVisitProvenance
from bilqis_mlx.runtime.bamf_bundle import authenticate_bamf_execution_feature_context
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.runtime.factory_candidate_training import FactoryDeliveryObservation
from bilqis_mlx.runtime.factory_retention_owner import evaluate_factory_retention_candidate
from bilqis_mlx.runtime.teacher_observation_capture import ObservationCapture, store_sidecar
from bilqis_mlx.runtime.tests.capability.factory.retention.factory_retention_live_support import (
    C05_TRAINING_LEARNING_RATE, HP, live_factory_context,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.cold_resume_probe import retained_digest
from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
    host_source_authority_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import (
    adaptation, selection_teacher,
)

CAPABILITY = "B.IDBOOLOPS"
SOURCE_SEED = 37116
C03_FIXTURE_SEED_OFFSET = 1
WITNESS_STAGE_INVALID = "C16_2C_WITNESS_STAGE_INVALID"


def bound_visit(parent, target, capability=CAPABILITY, lesson_grade="B"):
    school = SimpleNamespace(
        stage="RECOVERY_1",
        current_student=SimpleNamespace(
            sha256=candidate_identity_digest(parent.retained_state)),
    )
    bootstrap = {}
    if "c03_lineage" not in parent.teacher_state:
        bootstrap = {
            "legacy_receipt": {"teacher": selection_teacher()},
            "adaptation": adaptation(),
            "prior_region": "legacy-region",
        }
    bound, policy, _metadata = select_accepted_teacher_visit(
        target, historical_teacher_policy, school, random.Random(17), Settings(),
        "factory/7", {}, lesson_grade, capability_id=capability,
        total_capabilities=20,
        **bootstrap)
    provenance = BamfVisitProvenance.from_c03_record(bound.identity.to_record())
    return bound, provenance, policy


def real_candidate_training_step(
        target, parent, context, feature_path, artifact, *, learning_rate,
        capability=CAPABILITY, source_each=1):
    execution = context.release.execution_plan.capability_map[capability]
    bound, provenance, _policy = bound_visit(
        parent, target, capability, execution.grade_id)
    rows = tuple(context.draw_rows(
        seed=SOURCE_SEED, capability=capability, each=source_each))
    delivery = describe_delivered_teaching(
        context.release, capability, execution.teaching_option_ids[0], rows)
    capture = ObservationCapture(target, {})
    capture.attempt_id = "c16-2c-disposable"
    capture.proposal_id = store_sidecar(
        target, {"attempt_id": capture.attempt_id})["sha256"]
    capture.select_option(capability, None)
    observation = FactoryDeliveryObservation(capture, 1, rows, SOURCE_SEED)
    teacher_hp = type(HP)(learning_rate, HP.betas, HP.eps, HP.weight_decay)
    step = train_bamf_factory_step(
        target, context, parent, str(artifact), feature_path, rows,
        capability=capability, delivery=delivery,
        requested_count=max(2, len(rows)),
        source_seed=SOURCE_SEED, source_each=source_each, optimizer_step_seed=17,
        visit_provenance=provenance,
        teacher_strategy={"policy": "c16.2c-disposable"},
        teacher_hparams=teacher_hp, max_norm=1.0, observation=observation)
    return bound, rows, step


def real_candidate_training_horizon(
        target, parent, context, feature_path, artifact, *, learning_rate,
        horizon, capability=CAPABILITY, source_each=1):
    if type(horizon) is not int or horizon < 1:
        ErrorBus.raise_(
            SCHOOL.BAMF_TRAINING_ADAPTER.INVALID,
            reason="C16_2C_WITNESS_HORIZON_INVALID")
    execution = context.release.execution_plan.capability_map[capability]
    bound, provenance, _policy = bound_visit(
        parent, target, capability, execution.grade_id)
    rows = tuple(context.draw_rows(
        seed=SOURCE_SEED, capability=capability, each=source_each))
    delivery = describe_delivered_teaching(
        context.release, capability, execution.teaching_option_ids[0], rows)
    capture = ObservationCapture(target, {})
    capture.attempt_id = "c16-2c-disposable-horizon"
    capture.proposal_id = store_sidecar(
        target, {"attempt_id": capture.attempt_id})["sha256"]
    capture.select_option(capability, None)
    teacher_hp = type(HP)(learning_rate, HP.betas, HP.eps, HP.weight_decay)
    candidate = None
    steps = []
    for ordinal in range(1, horizon + 1):
        observation = FactoryDeliveryObservation(
            capture, parent.retained_state.optimizer_step + ordinal,
            rows, SOURCE_SEED)
        step = train_bamf_factory_step(
            target, context, parent, str(artifact), feature_path, rows,
            capability=capability, delivery=delivery,
            requested_count=max(2, len(rows)),
            source_seed=SOURCE_SEED, source_each=source_each,
            optimizer_step_seed=16 + ordinal, visit_provenance=provenance,
            teacher_strategy={"policy": "c16.2c-disposable-horizon"},
            teacher_hparams=teacher_hp, max_norm=1.0, observation=observation,
            candidate=candidate, finalize_candidate=(ordinal == horizon))
        candidate = step.transaction
        if candidate.update_steps != ordinal:
            ErrorBus.raise_(
                SCHOOL.BAMF_TRAINING_ADAPTER.INVALID,
                reason="C16_2C_WITNESS_HORIZON_DRIFT")
        steps.append(step)
    return bound, rows, tuple(steps)


def real_candidate_step(
        target, parent, context, feature_path, artifact, *, learning_rate,
        capability=CAPABILITY, source_each=1, observer=None):
    bound, rows, step = real_candidate_training_step(
        target, parent, context, feature_path, artifact,
        learning_rate=learning_rate, capability=capability, source_each=source_each)
    evaluation = evaluate_factory_retention_candidate(
        context, step.transaction, str(artifact), capability, run_dir=target,
        **({"observer": observer} if observer is not None else {}))
    decision = issue_factory_retention_decision(evaluation)
    return bound, rows, step, evaluation, decision


def next_update_receipt(target, context, feature_path, artifact):
    parent = load_accepted_generation(target)
    bound, _rows, step, evaluation, decision = real_candidate_step(
        target, parent, context, feature_path, artifact,
        learning_rate=C05_TRAINING_LEARNING_RATE)
    speculative = resolve_candidate(step.transaction, accepted=True)
    retained = resolve_candidate(step.transaction, accepted=decision.accepted)
    return {
        "visit": bound.identity.to_record(),
        "decision": decision.to_record(),
        "blocking_capability": evaluation.decision.blocking_capability,
        "speculative_candidate_digest": candidate_identity_digest(speculative),
        "speculative_retained_digest": retained_digest(speculative),
        "speculative_optimizer_step": speculative.optimizer_step,
        "owner_visible_retained_digest": retained_digest(retained),
        "owner_visible_optimizer_step": retained.optimizer_step,
        "training_authority": step.transaction.training_authorities[0].digest,
    }


def cold_probe(target, feature_path, artifact):
    repo = Path.cwd()
    source = (repo / "vendor/legacy-v16").resolve()
    base_context, _ = live_factory_context(repo, source)
    with host_source_authority_patch():
        parent = load_accepted_generation(target)
        context = AcceptedRuntimeHost(target).source_context(
            graph=base_context.graph, source_root=source)
        authenticate_bamf_execution_feature_context(parent, str(artifact), target)
        return next_update_receipt(target, context, feature_path, artifact)


def accepted_witness_receipt(
        parent, successor, published, decision, context, bound,
        uninterrupted, feature_artifact_path, *, process_nonce):
    """Persist accepted publication plus its same-process next update."""
    if (not isinstance(uninterrupted, dict)
            or not isinstance(process_nonce, str) or not process_nonce):
        raise ValueError(WITNESS_STAGE_INVALID)
    source = (context.release.source_bindings.source_attestation_sha256
              or context.release.source_bindings.digest())
    return {
        "schema": "bilqis.mlx.c16.2c-accepted-stage/v1",
        "parent_generation": parent.generation,
        "retained_generation": successor.generation,
        "parent_optimizer_step": parent.retained_state.optimizer_step,
        "retained_optimizer_step": successor.retained_state.optimizer_step,
        "parent_optimizer_state_sha256": retained_digest(parent.retained_state),
        "retained_optimizer_state_sha256": retained_digest(successor.retained_state),
        "retained_manifest_sha256": published["manifest_sha256"],
        "selected_visit": bound.identity.to_record(),
        "c05_decision": decision.to_record(),
        "factory_release_sha256": context.release.release_sha256,
        "source_identity_sha256": source,
        "feature_artifact_path": str(Path(feature_artifact_path).resolve()),
        "uninterrupted_next_update": uninterrupted,
        "uninterrupted_process_nonce": process_nonce,
        "c03_successor_fixture_authority": {
            "next_seed": bound.identity.selection_seed + C03_FIXTURE_SEED_OFFSET,
            "cursor_owner": "taught-source-row-id",
            "production_trajectory_authority": False,
        },
    }


def finalize_witness_receipt(accepted, cold):
    """Complete the receipt only after a separately launched cold process agrees."""
    if (not isinstance(accepted, dict)
            or accepted.get("schema") != "bilqis.mlx.c16.2c-accepted-stage/v1"
            or not isinstance(cold, dict)):
        raise ValueError(WITNESS_STAGE_INVALID)
    return {
        **accepted,
        "schema": "bilqis.mlx.c16.2c-launch-witness/v1",
        "cold_next_update": cold,
        "cold_next_update_equivalent": accepted["uninterrupted_next_update"] == cold,
    }


__all__ = (
    "C03_FIXTURE_SEED_OFFSET", "CAPABILITY", "accepted_witness_receipt",
    "cold_probe", "finalize_witness_receipt",
    "next_update_receipt", "real_candidate_step", "real_candidate_training_horizon",
    "real_candidate_training_step",
)
