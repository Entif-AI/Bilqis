"""C11/C16 BAMF v2 create, dry-run, enrollment and resume boundary."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactIdentity

from .bamf_lifecycle_inputs import (
    atlas_manifest_identity, foundation_hyperparameters, invalid, source_foundation,
    source_run_dir,
)


SCHEMA = "bilqis.bamf.operator-lifecycle/v1"


def _optimizer_record(value) -> dict:
    if isinstance(value, dict):
        learning_rate = value["learning_rate"]
        betas = value["betas"]
        eps = value["eps"]
        weight_decay = value["weight_decay"]
    else:
        learning_rate = value.learning_rate
        betas = value.betas
        eps = value.eps
        weight_decay = value.weight_decay
    return {
        "learning_rate": learning_rate,
        "betas": [betas[0], betas[1]],
        "eps": eps,
        "weight_decay": weight_decay,
    }


def _report(*, result, run_identity, topology, atlas, policy, hp,
            source_prefetch_workers, manifest_sha256=None):
    return {
        "schema": SCHEMA,
        "result": result,
        "run_id": run_identity.run_id,
        "run_seed": run_identity.run_seed,
        "run_identity": run_identity.to_record(),
        "model_topology": topology.to_record(),
        "atlas_release_manifest": {
            "sha256": atlas.bundle_id,
            "release_sha256": atlas.release_sha256,
            "source_bundle_id": atlas.source_bundle_id,
            "qualification": "A01_SOURCE_PINNED",
        },
        "admission_policy": policy,
        "optimizer_hyperparameters": _optimizer_record(hp),
        "source_prefetch_workers": source_prefetch_workers,
        "generation_manifest_sha256": manifest_sha256,
        "ready_for_training": False,
        "neural_updates": 0,
    }


def _validate_fresh_identity(args):
    if not args.run_id or type(args.run_seed) is not int or args.run_seed < 0:
        invalid("BAMF_OPERATOR_FOUNDATION_IDENTITY_REQUIRED")


def _fresh_request_inputs(args, topology):
    """Validate only caller-known facts; do not consume source Factory authority."""
    _validate_fresh_identity(args)
    hp = foundation_hyperparameters(args, required=True, materialize=True)
    if not isinstance(topology, ModelTopologySpecV2):
        invalid("BAMF_OPERATOR_V2_TOPOLOGY_REQUIRED")
    if topology != ModelTopologySpecV2():
        invalid("BAMF_OPERATOR_CREATE_TOPOLOGY_CONFLICT")
    if args.atlas_release_manifest is None:
        invalid("BAMF_OPERATOR_ATLAS_MANIFEST_REQUIRED")
    atlas = atlas_manifest_identity(args.atlas_release_manifest)
    if args.admission_policy == "staged" and args.atlas_admission_scope is not None:
        invalid("BAMF_ATLAS_SCOPE_REQUIRES_EXPLICIT_POLICY")
    if args.admission_policy == "atlas-release" and args.atlas_admission_scope is None:
        invalid("BAMF_ATLAS_EXPLICIT_SCOPE_FILE_REQUIRED")
    request = None
    if args.admission_policy == "atlas-release":
        from bilqis_mlx.runtime.atlas_admission import read_atlas_enrollment_request_v2
        request = read_atlas_enrollment_request_v2(args.atlas_admission_scope)
    return atlas, hp, request


def _validate_fresh_request_compatibility(args, topology, atlas, request) -> None:
    if request is None:
        return
    if request.requested_run_id != args.run_id:
        invalid("BAMF_OPERATOR_ATLAS_REQUEST_RUN_ID_CONFLICT")
    if request.requested_run_seed != args.run_seed:
        invalid("BAMF_OPERATOR_ATLAS_REQUEST_RUN_SEED_CONFLICT")
    if request.requested_topology_digest != topology.digest:
        invalid("BAMF_OPERATOR_ATLAS_REQUEST_TOPOLOGY_CONFLICT")
    if request.source_approval.atlas_release_sha256 != atlas.release_sha256:
        invalid("BAMF_OPERATOR_ATLAS_REQUEST_MANIFEST_CONFLICT")


def _accepted_atlas(run_dir: Path, identity) -> AtlasArtifactIdentity:
    from bilqis_mlx.runtime.bamf_bundle import read_accepted_generation_feature_receipt

    features = read_accepted_generation_feature_receipt(run_dir / "bamf-state.json")
    if features.source_release_sha256 != identity.initial_release_digest:
        invalid("BAMF_ATLAS_V2_ACCEPTED_ATLAS_CUSTODY_DRIFT")
    return AtlasArtifactIdentity(
        features.source_atlas_bundle_id,
        features.source_release_sha256,
        features.source_source_bundle_id,
    )


def _saved_policy(run_dir: Path) -> str:
    from bilqis_mlx.runtime.atlas_lease_storage import classify_accepted_atlas_epoch
    epoch = classify_accepted_atlas_epoch(run_dir)
    if epoch == "staged":
        return "staged"
    from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
    host = AcceptedRuntimeHost(run_dir)
    source_authority = host.source_authority()
    if epoch == "v2":
        from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_lease_v2
        lease = read_accepted_atlas_lease_v2(
            run_dir, source_authority=source_authority)
    else:
        from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_lease
        lease = read_accepted_atlas_lease(
            run_dir, source_authority=source_authority)
    if lease is None:
        invalid("BAMF_OPERATOR_SAVED_ADMISSION_POLICY_INVALID")
    return lease.admission_policy


def _validate_resume_overrides(args, student):
    identity = student.run_identity
    if identity is None:
        invalid("BAMF_OPERATOR_RESUME_RUN_IDENTITY_REQUIRED")
    if args.run_id is not None and args.run_id != identity.run_id:
        invalid("BAMF_OPERATOR_RESUME_RUN_ID_CONFLICT")
    if args.run_seed is not None and args.run_seed != identity.run_seed:
        invalid("BAMF_OPERATOR_RESUME_RUN_SEED_CONFLICT")
    requested_topology = None
    if args.model_topology is not None:
        from bilqis_mlx.runtime.topology_lifecycle import topology_from_file
        requested_topology = topology_from_file(args.model_topology)
    if requested_topology is not None and requested_topology != student.topology:
        invalid("BAMF_OPERATOR_RESUME_TOPOLOGY_CONFLICT")
    requested_hp = foundation_hyperparameters(args, required=False)
    if requested_hp is not None and requested_hp != student.optimizer_hyperparameters:
        invalid("BAMF_OPERATOR_RESUME_OPTIMIZER_CONFLICT")
    return identity


def _validate_resume_atlas_override(args, atlas):
    if args.atlas_release_manifest is not None:
        requested_atlas = atlas_manifest_identity(args.atlas_release_manifest)
        if requested_atlas != atlas:
            invalid("BAMF_OPERATOR_RESUME_ATLAS_MANIFEST_CONFLICT")


def _resume(args, requested_topology):
    from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority

    run_dir = Path(args.run_dir).expanduser().resolve()
    request = None
    if args.atlas_admission_scope is not None:
        if not args.admission_policy_explicit or args.admission_policy != "atlas-release":
            invalid("BAMF_ATLAS_SCOPE_REQUIRES_EXPLICIT_POLICY")
        if args.human_run is not True:
            invalid("BAMF_ATLAS_V2_EXPLICIT_HUMAN_REQUEST_REQUIRED")
        from bilqis_mlx.runtime.atlas_admission import read_atlas_enrollment_request_v2
        request = read_atlas_enrollment_request_v2(args.atlas_admission_scope)
    pointer = run_dir / "bamf-state.json"
    student, manifest_sha256 = load_bamf_generation_authority(pointer)
    identity = student.run_identity
    if identity is None:
        invalid("BAMF_OPERATOR_RESUME_RUN_IDENTITY_REQUIRED")
    atlas = _accepted_atlas(run_dir, identity)
    identity = _validate_resume_overrides(args, student)
    _validate_resume_atlas_override(args, atlas)

    if request is not None:
        from bilqis_mlx.runtime.atlas_admission import enroll_accepted_atlas_lease_v2
        from bilqis_mlx.runtime.atlas_lease_storage import (
            require_accepted_atlas_epoch_available_v2,
        )
        require_accepted_atlas_epoch_available_v2(run_dir)
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        host = AcceptedRuntimeHost(run_dir)
        enroll_accepted_atlas_lease_v2(
            run_dir, request, human_started=True,
            source_authority=host.source_authority())
        policy = "atlas-release"
        result = "ENROLLED"
    else:
        policy = _saved_policy(run_dir)
        if args.admission_policy_explicit and args.admission_policy != policy:
            if policy == "staged" and args.admission_policy == "atlas-release":
                invalid("BAMF_ATLAS_EXPLICIT_SCOPE_FILE_REQUIRED")
            invalid("BAMF_OPERATOR_RESUME_ADMISSION_POLICY_CONFLICT")
        result = "READY_TO_RESUME"

        if policy == "atlas-release" and args.human_run is True and not args.dry_run:
            from bilqis_mlx.runtime.atlas_flywheel_runtime import (
                run_accepted_atlas_flywheel,
            )
            _source, _release, graph = source_foundation(args.source_run_dir)
            flywheel = run_accepted_atlas_flywheel(
                run_dir, graph, reserve_gib=args.reserve_gib)
            result = flywheel.status.value
            student, manifest_sha256 = load_bamf_generation_authority(pointer)
            identity = _validate_resume_overrides(args, student)
            atlas = _accepted_atlas(run_dir, identity)

    return _report(
        result=result, run_identity=identity, topology=student.topology, atlas=atlas,
        policy=policy, hp=student.optimizer_hyperparameters,
        source_prefetch_workers=args.source_prefetch_workers,
        manifest_sha256=manifest_sha256,
    )


def _cold_recovery(args, topology, atlas, hp):
    from bilqis_mlx.runtime.bamf_bundle import recover_sealed_initial_generation
    from bilqis_mlx.runtime.bamf_bundle.genesis.records import (
        optimizer_hyperparameters_digest,
    )
    return recover_sealed_initial_generation(
        Path(args.run_dir), expected_run_id=args.run_id,
        expected_run_seed=args.run_seed,
        expected_topology_digest=topology.digest,
        expected_atlas_artifact=atlas,
        expected_optimizer_hyperparameters_sha256=optimizer_hyperparameters_digest(hp),
    )


def _fresh_target(args):
    from bilqis_mlx.runtime._bamf_first_student_support import (
        _canonical_disjoint_run_paths, _canonical_run_dir_shape,
    )
    selected_source = source_run_dir(args.source_run_dir)
    _source, target = _canonical_disjoint_run_paths(
        str(selected_source), args.run_dir)
    target = _canonical_run_dir_shape(target)
    pointer_path = target / "bamf-state.json"
    if pointer_path.exists() or pointer_path.is_symlink():
        invalid("BAMF_OPERATOR_CREATE_USE_RESUME")
    return selected_source, target, pointer_path


def bamf_lifecycle(args, topology):
    """Resolve one BAMF v2 lifecycle request without entering the neural loop."""
    if args.resume:
        return _resume(args, topology)

    atlas, hp, request = _fresh_request_inputs(args, topology)
    if not args.dry_run:
        if request is not None and args.human_run is not True:
            invalid("BAMF_ATLAS_V2_EXPLICIT_HUMAN_REQUEST_REQUIRED")
        if args.human_run is not True:
            invalid("BAMF_OPERATOR_CREATE_EXPLICIT_HUMAN_REQUEST_REQUIRED")
    _validate_fresh_request_compatibility(args, topology, atlas, request)
    from bilqis_mlx.runtime._bamf_first_student_support import _fresh_run_dir
    selected_source, target, pointer_path = _fresh_target(args)

    if args.dry_run:
        _fresh_run_dir(target)
        source, release, graph = source_foundation(selected_source)
        from bilqis_mlx.runtime.bamf_first_student import (
            BamfFoundationConfig, preview_bamf_foundation_run_identity,
        )
        config = BamfFoundationConfig(
            str(source), args.run_id, args.run_seed, graph, atlas, hp)
        identity = preview_bamf_foundation_run_identity(
            config, release, target)
        return _report(
            result="READY_TO_CREATE", run_identity=identity, topology=topology,
            atlas=atlas, policy=args.admission_policy, hp=hp,
            source_prefetch_workers=args.source_prefetch_workers)

    recovered = None
    if target.is_dir() and any(target.iterdir()):
        from bilqis_mlx.runtime._coordination import run_root_claim
        from bilqis_mlx.runtime.bamf_bundle.publication.storage import (
            _classify_initial_generation_target,
        )
        with run_root_claim(target, create_parent=True):
            if _classify_initial_generation_target(target) == "recovery":
                recovered = _cold_recovery(args, topology, atlas, hp)

    if recovered is None:
        source, release, graph = source_foundation(selected_source)
        from bilqis_mlx.runtime.bamf_first_student import (
            BamfFoundationConfig, preflight_bamf_foundation,
        )
        config = BamfFoundationConfig(
            str(source), args.run_id, args.run_seed, graph, atlas, hp)
        receipt = preflight_bamf_foundation(config, release, target)
        identity = receipt.run_identity
        manifest_sha256 = receipt.manifest_sha256
        persisted_atlas = receipt.atlas_artifact
        persisted_hp = receipt.optimizer_hyperparameters
    else:
        from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
        student, manifest_sha256 = load_bamf_generation_authority(pointer_path)
        identity = student.run_identity
        persisted_atlas = _accepted_atlas(target, identity)
        persisted_hp = student.optimizer_hyperparameters

    policy = "staged"
    if request is not None:
        from bilqis_mlx.runtime.atlas_lease_storage import (
            require_accepted_atlas_epoch_available_v2,
        )
        require_accepted_atlas_epoch_available_v2(target)
        from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
        from bilqis_mlx.runtime.atlas_admission import enroll_accepted_atlas_lease_v2
        host = AcceptedRuntimeHost(target)
        enroll_accepted_atlas_lease_v2(
            target, request, human_started=True,
            source_authority=host.source_authority())
        policy = "atlas-release"

    return _report(
        result="CREATED", run_identity=identity, topology=topology,
        atlas=persisted_atlas, policy=policy, hp=persisted_hp,
        source_prefetch_workers=args.source_prefetch_workers,
        manifest_sha256=manifest_sha256)


__all__ = ("SCHEMA", "bamf_lifecycle")
