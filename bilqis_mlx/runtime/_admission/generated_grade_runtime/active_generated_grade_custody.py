"""Immutable filesystem custody for #1314 active generated grades."""
from __future__ import annotations

import json
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade import GeneratedGradeProposal
from bilqis_mlx.runtime.state import _durable_json

from .active_generated_grade_contracts import (
    ACTIVE_GRADE_POINTER_SCHEMA,
    ActiveGeneratedGrade,
    active_from_record,
    definition_from_record,
    definition_record,
)
from .generated_grade import _read_issued_proposal


def _fail(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_ATLAS_ADMISSION.INVALID, reason=reason)


def _roots(run_dir: Path) -> tuple[Path, Path, Path]:
    root = Path(run_dir) / "generated-grades"
    definitions = root / "definitions"
    activations = root / "activations"
    for path in (root, definitions, activations):
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            _fail("BAMF_ACTIVE_GENERATED_GRADE_CUSTODY_UNSAFE")
    return root, definitions, activations


def _commit_root(run_dir: Path) -> Path:
    commits = Path(run_dir) / "generated-grades" / "commits"
    if commits.is_symlink() or (commits.exists() and not commits.is_dir()):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CUSTODY_UNSAFE")
    return commits


def _json(path: Path, reason: str) -> dict:
    if path.is_symlink() or not path.is_file():
        _fail(reason)
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        _fail(reason)
    if not isinstance(value, dict):
        _fail(reason)
    canonical = json.dumps(
        value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if raw != canonical:
        _fail(reason)
    return value


def _persist_immutable(path: Path, payload: dict, reason: str) -> None:
    if path.exists():
        if _json(path, reason) != payload:
            _fail(reason)
        return
    _durable_json(path, payload)
    if _json(path, reason) != payload:
        _fail(reason)


def _pointer_path(run_dir: Path) -> Path:
    return Path(run_dir) / "generated-grades" / "current.json"


def _activation_history_exists(run_dir: Path) -> bool:
    """Distinguish genuine first activation from a lost current pointer."""
    _root, _definitions, activations = _roots(run_dir)
    if not activations.exists():
        return False
    entries = tuple(activations.iterdir())
    if any(item.is_symlink() or not item.is_file() for item in entries):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CUSTODY_UNSAFE")
    return bool(entries)


def _commit_record(active: ActiveGeneratedGrade) -> dict:
    return {
        "schema": "bilqis.bamf.active-generated-grade-publication/v1",
        "activation_sha256": active.activation_sha256,
        "definition_sha256": active.definition.definition_sha256,
        "predecessor_activation_sha256": active.predecessor_activation_sha256,
        "transition_kind": active.transition_kind,
    }


def _persist_commit(run_dir: Path, active: ActiveGeneratedGrade) -> None:
    path = _commit_root(run_dir) / f"{active.activation_sha256}.json"
    _persist_immutable(
        path,
        _commit_record(active),
        "BAMF_ACTIVE_GENERATED_GRADE_COMMIT_INVALID",
    )


def _committed_history_exists(run_dir: Path) -> bool:
    commits = _commit_root(run_dir)
    if not commits.exists():
        return False
    entries = tuple(commits.iterdir())
    if any(item.is_symlink() or not item.is_file() for item in entries):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CUSTODY_UNSAFE")
    for item in entries:
        _json(item, "BAMF_ACTIVE_GENERATED_GRADE_COMMIT_INVALID")
    return bool(entries)


def _recoverable_initial_orphan(
    run_dir: Path,
    active: ActiveGeneratedGrade,
) -> bool:
    """Recognize bytes durably staged before the first pointer write crashed."""
    if (active.transition_kind not in {"INITIAL", "BOOTSTRAP"}
            or _committed_history_exists(run_dir)):
        return False
    _root, definitions, activations = _roots(run_dir)
    if not activations.exists():
        return False
    entries = tuple(activations.iterdir())
    if len(entries) != 1 or entries[0].name != f"{active.activation_sha256}.json":
        return False
    definition_path = definitions / f"{active.definition.definition_sha256}.json"
    if not definition_path.is_file() or definition_path.is_symlink():
        return False
    definition = definition_from_record(_json(
        definition_path,
        "BAMF_ACTIVE_GENERATED_GRADE_DEFINITION_INVALID",
    ))
    stored = active_from_record(_json(
        entries[0],
        "BAMF_ACTIVE_GENERATED_GRADE_RECORD_INVALID",
    ), definition)
    return stored == active


def _read_stored_active(run_dir: Path) -> ActiveGeneratedGrade | None:
    root, definitions, activations = _roots(run_dir)
    pointer = root / "current.json"
    if not pointer.exists() and not pointer.is_symlink():
        return None
    record = _json(pointer, "BAMF_ACTIVE_GENERATED_GRADE_POINTER_INVALID")
    if set(record) != {
        "schema", "activation_sha256", "definition_sha256",
    } or record.get("schema") != ACTIVE_GRADE_POINTER_SCHEMA:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_POINTER_INVALID")
    definition = definition_from_record(_json(
        definitions / f"{record['definition_sha256']}.json",
        "BAMF_ACTIVE_GENERATED_GRADE_DEFINITION_INVALID",
    ))
    active = active_from_record(_json(
        activations / f"{record['activation_sha256']}.json",
        "BAMF_ACTIVE_GENERATED_GRADE_RECORD_INVALID",
    ), definition)
    if (active.activation_sha256 != record["activation_sha256"]
            or active.definition.definition_sha256 != record["definition_sha256"]):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_POINTER_DRIFT")
    if active.transition_kind == "BOOTSTRAP":
        from .initial_grade_bootstrap import read_initial_grade_bootstrap
        proposal = read_initial_grade_bootstrap(run_dir, active.proposal_sha256)
        if (proposal.a09_snapshot_sha256 != active.a09_snapshot_sha256
                or proposal.a09_closure_sha256 != active.a09_closure_sha256
                or active.a09_proposal_sha256 is not None
                or proposal.proposal_sha256 != active.definition.proposal_sha256
                or proposal.learner_foot_sha256
                   != active.definition.learner_foot_sha256
                or proposal.policy_sha256 != active.definition.policy_sha256
                or proposal.policy_epoch != active.definition.policy_epoch
                or proposal.current_release_sha256
                   != active.definition.adopted_release_sha256):
            _fail("BAMF_ACTIVE_GENERATED_GRADE_PROVENANCE_DRIFT")
    else:
        proposal = _read_issued_proposal(run_dir, active.proposal_sha256)
        if (proposal.snapshot_sha256 != active.a09_snapshot_sha256
                or proposal.closure_sha256 != active.a09_closure_sha256
                or proposal.a09_proposal_sha256 != active.a09_proposal_sha256
                or proposal.proposal_sha256 != active.definition.proposal_sha256
                or proposal.learner_foot_sha256
                   != active.definition.learner_foot_sha256
                or proposal.policy_sha256 != active.definition.policy_sha256
                or proposal.policy_epoch != active.definition.policy_epoch):
            _fail("BAMF_ACTIVE_GENERATED_GRADE_PROVENANCE_DRIFT")
    return active


def _accepted_bound_generated_grade_proposal(run_dir: Path) -> GeneratedGradeProposal:
    """Read the newest #1320 proposal proven by accepted C07/B13 ancestry."""
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest,
        accepted_generation,
        parent_acceptance_anchor_from_manifest,
    )
    root = Path(run_dir)
    pointer, student = accepted_generation(root / "bamf-state.json")
    manifest = pointer["manifest_sha256"]
    acceptance = pointer["acceptance_sha256"]
    visited = set()
    while True:
        if manifest in visited:
            _fail("BAMF_ACTIVE_GENERATED_GRADE_ACCEPTED_ANCESTRY_DRIFT")
        visited.add(manifest)
        binding = accepted_binding_for_manifest(
            root, manifest, student, expected_acceptance_sha256=acceptance)
        proposal_sha256 = getattr(binding, "generated_grade_proposal_sha256", None)
        if proposal_sha256 is not None:
            return _read_issued_proposal(root, proposal_sha256)
        if student.generation == 0:
            break
        parent_manifest = student.parent_manifest_sha256
        parent_acceptance = parent_acceptance_anchor_from_manifest(root, manifest)
        if parent_manifest is None or parent_acceptance is None:
            break
        student = load_bamf_bundle(
            root / "bamf-bundles" / parent_manifest,
            expected_manifest_sha256=parent_manifest)
        manifest, acceptance = parent_manifest, parent_acceptance
    _fail("BAMF_ACTIVE_GENERATED_GRADE_ADMITTED_PROPOSAL_REQUIRED")


def _accepted_generation_identity(run_dir: Path) -> tuple[str, int, str, str]:
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest,
        accepted_generation,
    )
    pointer, student = accepted_generation(Path(run_dir) / "bamf-state.json")
    accepted_binding_for_manifest(
        Path(run_dir), pointer["manifest_sha256"], student,
        expected_acceptance_sha256=pointer["acceptance_sha256"])
    return (
        student.run_id, student.generation,
        pointer["manifest_sha256"], pointer["acceptance_sha256"],
    )


def _activation_is_accepted_ancestor(
    run_dir: Path,
    active: ActiveGeneratedGrade,
) -> bool:
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest,
        accepted_generation,
        parent_acceptance_anchor_from_manifest,
    )
    root = Path(run_dir)
    pointer, student = accepted_generation(root / "bamf-state.json")
    manifest = pointer["manifest_sha256"]
    acceptance = pointer["acceptance_sha256"]
    while True:
        accepted_binding_for_manifest(
            root, manifest, student, expected_acceptance_sha256=acceptance)
        if manifest == active.activation_manifest_sha256:
            return (
                acceptance == active.activation_acceptance_sha256
                and student.run_id == active.run_id
                and student.generation == active.activation_generation)
        if student.generation == 0:
            return False
        parent_manifest = student.parent_manifest_sha256
        parent_acceptance = parent_acceptance_anchor_from_manifest(root, manifest)
        if parent_manifest is None or parent_acceptance is None:
            return False
        student = load_bamf_bundle(
            root / "bamf-bundles" / parent_manifest,
            expected_manifest_sha256=parent_manifest)
        manifest, acceptance = parent_manifest, parent_acceptance


def _require_identity_still_current(run_dir: Path, identity) -> None:
    from bilqis_mlx.runtime.bamf_bundle.publication import _read_pointer
    bamf = _read_pointer(Path(run_dir) / "bamf-state.json")
    if (bamf is None
            or (bamf["run_id"], bamf["generation"],
                bamf["manifest_sha256"], bamf["acceptance_sha256"]) != identity):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_ACCEPTED_GENERATION_DRIFT")


def _persist_activation(run_dir: Path, active: ActiveGeneratedGrade) -> None:
    root, definitions, activations = _roots(run_dir)
    _persist_immutable(
        definitions / f"{active.definition.definition_sha256}.json",
        definition_record(active.definition),
        "BAMF_ACTIVE_GENERATED_GRADE_DEFINITION_COLLISION",
    )
    _persist_immutable(
        activations / f"{active.activation_sha256}.json",
        active.to_record(),
        "BAMF_ACTIVE_GENERATED_GRADE_ACTIVATION_COLLISION",
    )
    _durable_json(root / "current.json", {
        "schema": ACTIVE_GRADE_POINTER_SCHEMA,
        "activation_sha256": active.activation_sha256,
        "definition_sha256": active.definition.definition_sha256,
    }, replace_existing=True)
    _persist_commit(run_dir, active)
