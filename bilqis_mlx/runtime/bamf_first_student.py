"""C16.1b owner adapter for one fresh B13 generation-zero foundation."""
from __future__ import annotations

from copy import deepcopy
from typing import Mapping

from bilqis_mlx.factory.executable_release import ExecutableFactoryRelease
from bilqis_mlx.runtime.atlas_optimizer import STATE_SCHEMA
from bilqis_mlx.runtime.bamf_bundle import (
    issue_initial_factory_foundation_authority,
    issue_initial_foundation_feature_authority,
    load_bamf_generation_authority,
    prepare_initial_generation,
    publish_initial_generation,
)
from bilqis_mlx.runtime.bamf_bundle.genesis.records import (
    INITIAL_BINDING_SCHEMA, RUN_IDENTITY_SCHEMA, BamfRunIdentity,
)
from bilqis_mlx.runtime.bamf_bundle.records import (
    ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA, BAMF_POINTER_SCHEMA,
)
from bilqis_mlx.runtime.model_topology_v2 import GenerationProvenance
from bilqis_mlx.semantics.atlas.snapshot import resolve_atlas_artifact_selection

from ._bamf_first_student_contracts import (
    BAMF_DASHBOARD_METRICS_SCHEMA, BAMF_FOUNDATION_CONFIG_SCHEMA,
    BAMF_LAUNCH_RECEIPT_SCHEMA, BamfFoundationConfig,
    BamfFoundationDashboardProjection, DashboardMetrics, LaunchReceipt, _invalid,
)
from ._bamf_first_student_support import (
    _canonical_disjoint_run_paths, _canonical_run_dir_shape,
    _dashboard_metrics_from_projection,
    _fresh_run_dir, _model_authority, _resolved_run_path,
)

def load_bamf_foundation_dashboard_projection(
        run_dir) -> BamfFoundationDashboardProjection | None:
    """Project newborn dashboard facts from the accepted B13 pointer only."""
    pointer = _resolved_run_path(run_dir, reason="BAMF_FIRST_STUDENT_DASHBOARD_PATH_INVALID") / "bamf-state.json"
    if not pointer.exists() and not pointer.is_symlink():
        return None
    student, _manifest_sha256 = load_bamf_generation_authority(pointer)
    identity = getattr(student, "run_identity", None)
    retained = getattr(student, "retained_state", None)
    compiler = getattr(student, "compiler_features", None)
    teacher = getattr(student, "teacher_state", None)
    grades = compiler.get("factory_grade_ids") if isinstance(compiler, Mapping) else None
    if (getattr(student, "generation", None) != 0
            or type(identity) is not BamfRunIdentity
            or getattr(student, "run_id", None) != identity.run_id
            or getattr(retained, "optimizer_step", None) != 0
            or identity.initial_teacher_epoch != 0
            or not isinstance(compiler, Mapping)
            or compiler.get("factory_release_sha256") != identity.factory_release_sha256
            or not isinstance(grades, list) or not grades
            or len(set(grades)) != len(grades)
            or any(type(grade) is not str or not grade for grade in grades)
            or not isinstance(teacher, Mapping)
            or teacher.get("cursor") != "GENESIS"
            or teacher.get("teacher_epoch") != 0
            or teacher.get("teacher_identity") != identity.initial_teacher_identity
            or teacher.get("next_seed") != identity.run_seed):
        _invalid("BAMF_FIRST_STUDENT_DASHBOARD_PROJECTION_INVALID")
    return BamfFoundationDashboardProjection(
        factory_release_sha256=identity.factory_release_sha256,
        optimizer_step=0,
        grade_visits=0,
        teacher_events=0,
        stage="READY_FOR_HUMAN_START",
        active_grades=tuple(grades),
        current_grade=grades[0],
        last_run_status="NOT_STARTED",
    )


def _prepare_bamf_foundation(
        config: BamfFoundationConfig,
        admitted_release: ExecutableFactoryRelease,
        new_run_dir):
    if type(config) is not BamfFoundationConfig:
        _invalid("BAMF_FIRST_STUDENT_CONFIG_INVALID")
    config.validate()
    source, canonical_target = _canonical_disjoint_run_paths(
        config.source_run_dir, new_run_dir)
    graph = deepcopy(dict(config.semantic_graph))
    factory = issue_initial_factory_foundation_authority(source, graph)
    if type(admitted_release) is not ExecutableFactoryRelease or admitted_release != factory.release:
        _invalid("BAMF_FIRST_STUDENT_FACTORY_RELEASE_DRIFT")

    selection = resolve_atlas_artifact_selection(config.atlas_artifact)
    features = issue_initial_foundation_feature_authority(selection)
    source_identity = (admitted_release.source_bindings.source_attestation_sha256
                       or admitted_release.source_bindings.digest())
    provenance = GenerationProvenance(
        source_identity, features.features.semantic_release,
        admitted_release.execution_plan.projection_digests.teaching, 0)
    model_authority = _model_authority(
        admitted_release, factory.admission, graph, config.run_seed,
        features, provenance)
    prepared = prepare_initial_generation(
        run_id=config.run_id,
        run_seed=config.run_seed,
        graph=graph,
        factory_authority=factory,
        model_authority=model_authority,
        optimizer_hyperparameters=config.optimizer_hyperparameters,
        provenance=provenance,
        foundation_features=features,
        delivery_events=({
            "event": "BAMF_GENERATION_ACCEPTED",
            "optimizer_step": 0,
        },),
    )
    return canonical_target, prepared


def preview_bamf_foundation_run_identity(
        config: BamfFoundationConfig,
        admitted_release: ExecutableFactoryRelease,
        new_run_dir) -> BamfRunIdentity:
    """Derive exact generation-zero identity without mutating target custody."""
    _target, prepared = _prepare_bamf_foundation(
        config, admitted_release, new_run_dir)
    return prepared.candidate.run_identity


def preflight_bamf_foundation(
        config: BamfFoundationConfig,
        admitted_release: ExecutableFactoryRelease,
        new_run_dir) -> LaunchReceipt:
    """Publish one owner-derived generation zero without performing a neural update."""
    canonical_target, prepared = _prepare_bamf_foundation(
        config, admitted_release, new_run_dir)
    target = _canonical_run_dir_shape(new_run_dir)
    if target != canonical_target:
        _invalid("BAMF_FIRST_STUDENT_TARGET_PATH_DRIFT")
    from bilqis_mlx.runtime._coordination import run_root_claim
    from bilqis_mlx.runtime.bamf_bundle.publication.storage import (
        _classify_initial_generation_target,
        _reclaim_empty_initial_staging_root,
    )
    with run_root_claim(target, create_parent=True):
        target = _canonical_run_dir_shape(new_run_dir)
        if target != canonical_target:
            _invalid("BAMF_FIRST_STUDENT_TARGET_PATH_DRIFT")
        if ((target / "bamf-state.json").exists()
                or (target / "bamf-state.json").is_symlink()):
            _invalid("BAMF_FIRST_STUDENT_RUN_DIRECTORY_OCCUPIED")
        target_state = _classify_initial_generation_target(target)
        if target_state == "lock-stage":
            _reclaim_empty_initial_staging_root(target)
            target_state = _classify_initial_generation_target(target)
            if target_state != "lock-only":
                _invalid("BAMF_FIRST_STUDENT_PRESEAL_STAGING_RESIDUE")
        if target_state == "recovery":
            from bilqis_mlx.runtime.bamf_bundle.genesis import (
                recover_prepared_initial_generation,
            )
            pointer = recover_prepared_initial_generation(target, prepared)
            if pointer is None:
                _invalid("BAMF_FIRST_STUDENT_RUN_DIRECTORY_OCCUPIED")
        elif target_state == "empty":
            _fresh_run_dir(target)
            pointer = publish_initial_generation(target, prepared)
        elif target_state == "lock-only":
            pointer = publish_initial_generation(target, prepared)
        else:
            _invalid("BAMF_FIRST_STUDENT_RUN_DIRECTORY_OCCUPIED")
    projection = load_bamf_foundation_dashboard_projection(target)
    if projection is None:
        _invalid("BAMF_FIRST_STUDENT_PERSISTED_FOUNDATION_DRIFT")
    student, manifest_sha256 = load_bamf_generation_authority(target / "bamf-state.json")
    if (student.run_identity != prepared.candidate.run_identity
            or student.retained_state.optimizer_step != 0
            or manifest_sha256 != pointer["manifest_sha256"]
            or projection.factory_release_sha256 != admitted_release.release_sha256):
        _invalid("BAMF_FIRST_STUDENT_PERSISTED_FOUNDATION_DRIFT")

    return LaunchReceipt(
        run_identity=student.run_identity,
        manifest_sha256=manifest_sha256,
        factory_release_sha256=projection.factory_release_sha256,
        atlas_artifact=config.atlas_artifact,
        optimizer_hyperparameters=student.optimizer_hyperparameters,
        dashboard_metrics=_dashboard_metrics_from_projection(projection),
        input_schema_versions=(
            ("config", BAMF_FOUNDATION_CONFIG_SCHEMA),
            ("factory_release", admitted_release.schema),
            ("atlas_artifact_identity", config.atlas_artifact.schema),
        ),
        output_schema_versions=(
            ("launch_receipt", BAMF_LAUNCH_RECEIPT_SCHEMA),
            ("dashboard_metrics", BAMF_DASHBOARD_METRICS_SCHEMA),
            ("run_identity", RUN_IDENTITY_SCHEMA),
            ("initial_generation_binding", INITIAL_BINDING_SCHEMA),
            ("optimizer_state", STATE_SCHEMA),
            ("generation_bundle", ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA),
            ("generation_pointer", BAMF_POINTER_SCHEMA),
        ),
    )


__all__ = (
    "BAMF_FOUNDATION_CONFIG_SCHEMA", "BAMF_DASHBOARD_METRICS_SCHEMA",
    "BAMF_LAUNCH_RECEIPT_SCHEMA",
    "BamfFoundationConfig", "BamfFoundationDashboardProjection",
    "DashboardMetrics", "LaunchReceipt",
    "load_bamf_foundation_dashboard_projection", "preflight_bamf_foundation",
    "preview_bamf_foundation_run_identity",
)
