"""Read-only BAMF learner identity discovery for CP01."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.runtime.bamf_operator.locking import bamf_operator_lock_held

from .contracts import ControlPlaneState, LearnerIdentity


def _failure_code(error: Exception) -> str:
    code = getattr(error, "code", None)
    if isinstance(code, str) and code:
        return code
    return error.__class__.__name__


def discover_learner(run_dir: Path) -> LearnerIdentity:
    """Resolve current accepted BAMF generation without creating or mutating a run."""
    run_dir = Path(run_dir).expanduser().resolve()
    operator_active = bamf_operator_lock_held(run_dir)
    pointer = run_dir / "bamf-state.json"
    if not pointer.exists() and not pointer.is_symlink():
        return LearnerIdentity(
            ControlPlaneState.LEARNER_UNAVAILABLE, str(run_dir),
            operator_active=operator_active)
    try:
        from bilqis_mlx.runtime.bamf_bundle import inspect_accepted_generation
        accepted = inspect_accepted_generation(pointer)
    except FileNotFoundError as error:
        return LearnerIdentity(
            ControlPlaneState.STALE, str(run_dir),
            operator_active=operator_active,
            failure_code=_failure_code(error))
    except Exception as error:
        return LearnerIdentity(
            ControlPlaneState.DEGRADED, str(run_dir),
            operator_active=operator_active,
            failure_code=_failure_code(error))
    return LearnerIdentity(
        ControlPlaneState.HEALTHY,
        str(run_dir),
        operator_active=operator_active,
        run_id=accepted.run_id,
        run_identity_sha256=accepted.run_identity_sha256,
        generation=accepted.generation,
        generation_manifest_sha256=accepted.generation_manifest_sha256,
        optimizer_step=accepted.optimizer_step,
        factory_release_sha256=accepted.factory_release_sha256,
        topology_sha256=accepted.topology_sha256,
    )
