"""Immutable factory artifacts and fail-closed runtime admission readback."""
from __future__ import annotations

import json
from pathlib import Path

from ..source_adapters.school import live_source_registry
from ..factory.executable_release import (
    ExecutableAdmissionReceipt,
    ExecutableFactoryRelease,
    SCHEMA as EXECUTABLE_SCHEMA,
    admit_executable_factory_release,
)
from ..factory.model import AdmissionReceipt, FactoryRelease
from ..factory.release import admit_factory_release, compile_factory_release
from ..compatibility.factory_release_v1 import decode_sealed_factory_release_v1
from .state import _canonical, _durable_json

SCHEMA = "bilqis.mlx.factory-release/v1"
_ADMISSION_RECEIPT_INVALID = "FACTORY_ADMISSION_RECEIPT_INVALID"
_UNSAFE_ARTIFACT_DIRECTORY = "FACTORY_RELEASE_UNSAFE_ARTIFACT_DIRECTORY"


def _factory_release(course, *, registry=None):
    return compile_factory_release(course, registry if registry is not None else live_source_registry())


def _persist_factory_release(run_dir: Path, release):
    """Publish one immutable release manifest and verify exact readback."""
    release.verify()
    path = run_dir / "factory-releases" / (release.release_sha256 + ".json")
    if (run_dir / "factory-releases").is_symlink():
        raise ValueError(_UNSAFE_ARTIFACT_DIRECTORY)
    payload = {"schema": SCHEMA,
               "factory_release_sha256": release.release_sha256,
               **release.manifest()}
    # Compare the persisted JSON data model, not Python tuple/list container
    # accidents. The release hash itself is already bound to canonical JSON.
    payload = json.loads(_canonical(payload))
    if path.exists():
        if path.is_symlink() or json.loads(path.read_text()) != payload:
            raise ValueError("FACTORY_RELEASE_DURABLE_ARTIFACT_DRIFT")
    else:
        _durable_json(path, payload)
    if json.loads(path.read_text()) != payload:
        raise ValueError("FACTORY_RELEASE_DURABLE_READBACK_DRIFT")
    return str(path.relative_to(run_dir))


def _factory_admission(run_dir, course, student, graph_sha256, *, registry=None):
    release = _factory_release(course, registry=registry)
    release_file = _persist_factory_release(run_dir, release)
    admission = admit_factory_release(
        release, student_sha256=student.sha256,
        optimizer_step=student.optimizer_step,
        semantic_graph_sha256=graph_sha256)
    return release, release_file, admission


def _persist_executable_factory_release(
        run_dir: Path, release: ExecutableFactoryRelease) -> str:
    """Publish one immutable v2 release without changing the live v1 path."""
    if not isinstance(release, ExecutableFactoryRelease):
        raise TypeError("FACTORY_EXECUTABLE_RELEASE_REQUIRED")
    release.verify()
    directory = run_dir / "factory-releases"
    path = directory / (release.release_sha256 + ".json")
    if directory.is_symlink():
        raise ValueError(_UNSAFE_ARTIFACT_DIRECTORY)
    payload = {
        "factory_release_sha256": release.release_sha256,
        **release.manifest(),
    }
    payload = json.loads(_canonical(payload))
    if path.exists():
        if path.is_symlink() or json.loads(path.read_text()) != payload:
            raise ValueError("FACTORY_EXECUTABLE_RELEASE_DURABLE_ARTIFACT_DRIFT")
    else:
        _durable_json(path, payload)
    if json.loads(path.read_text()) != payload:
        raise ValueError("FACTORY_EXECUTABLE_RELEASE_DURABLE_READBACK_DRIFT")
    return str(path.relative_to(run_dir))


def _executable_factory_admission(
        run_dir: Path, release: ExecutableFactoryRelease, student,
        graph_sha256: str, graph: dict):
    """Publish and admit v2 without switching the existing live v1 caller."""
    admission = admit_executable_factory_release(
        release,
        student_sha256=student.sha256,
        optimizer_step=student.optimizer_step,
        semantic_graph_sha256=graph_sha256,
        graph=graph,
    )
    release_file = _persist_executable_factory_release(run_dir, release)
    return release, release_file, admission


def _read_factory_release(run_dir, receipt):
    """Decode the persisted artifact without rebuilding a grade provider."""
    digest = receipt.get("factory_release_sha256")
    if (not isinstance(digest, str) or len(digest) != 64 or
            any(char not in "0123456789abcdef" for char in digest)):
        raise ValueError("FACTORY_RELEASE_DIGEST_INVALID")
    release_file = receipt.get("factory_release_file")
    expected_file = "factory-releases/" + digest + ".json"
    if release_file != expected_file:
        raise ValueError("FACTORY_RELEASE_NOT_ADMITTED_FOR_RUNTIME")
    path = run_dir / expected_file
    if path.parent.is_symlink() or path.is_symlink() or not path.is_file():
        raise ValueError("FACTORY_RELEASE_DURABLE_ARTIFACT_MISSING")
    payload = json.loads(path.read_text())
    if payload.get("schema") != SCHEMA:
        raise ValueError("FACTORY_RELEASE_DURABLE_SCHEMA_INVALID")
    if payload.get("factory_release_sha256") != digest:
        raise ValueError("FACTORY_RELEASE_ARTIFACT_DIGEST_DRIFT")
    return decode_sealed_factory_release_v1(
        {key: value for key, value in payload.items()
         if key not in {"schema", "factory_release_sha256"}}, digest)


def _verified_legacy_upgrade_release(run_dir: Path, receipt: dict) -> FactoryRelease | None:
    """Reopen exact sealed v1 course solely for a source-verified v2 migration.

    Reconstructing the old course from subsequently edited constructor source
    changes its B/C digest. The original admitted release is the only valid
    historical course authority. This is NOT a waiver of provider verification:
    the caller must compile/admit the new v2 source and oracle contract before
    any resumed learning is permitted.
    """
    if receipt.get("factory_admission_v2") is not None:
        return None
    raw = receipt.get("factory_admission")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError(_ADMISSION_RECEIPT_INVALID)
    release = _read_factory_release(Path(run_dir), receipt)
    try:
        admission = AdmissionReceipt(**raw)
    except TypeError as exc:
        raise ValueError(_ADMISSION_RECEIPT_INVALID) from exc
    admission.verify(release)
    school = receipt["school"]
    student = school["current_student"]
    if (receipt.get("curriculum_mode") != release.course.version or
            school.get("course_digest") != release.course.digest() or
            receipt.get("semantic_graph_sha256") != admission.semantic_graph_sha256 or
            admission.optimizer_step > student["optimizer_step"] or
            (admission.optimizer_step == student["optimizer_step"] and
             admission.student_sha256 != student["sha256"])):
        raise ValueError("FACTORY_ADMISSION_SEALED_RESUME_IDENTITY_DRIFT")
    return release


def _verified_historical_cohort_release(run_dir: Path, receipt: dict) -> FactoryRelease | None:
    """Resolve a retained v1 exam's original signed authority after v2 admission.

    An admitted v2 curriculum may still reference its most recent historical
    exam. Only the separately signed v1 admission can validate those cohort
    bytes. The v2 release remains authoritative for *new* training and exams.
    """
    exam = receipt.get("last_exam") or {}
    if (receipt.get("factory_admission_v2") is None or
            exam.get("cohort_sha256") is None or
            exam.get("factory_release_sha256") is not None):
        return None
    prior = receipt.get("factory_admission")
    if not isinstance(prior, dict):
        raise ValueError("HUMAN_TRAINER_HISTORICAL_EXAM_ADMISSION_REQUIRED")
    sha = prior.get("factory_release_sha256")
    if not isinstance(sha, str) or len(sha) != 64:
        raise ValueError("HUMAN_TRAINER_HISTORICAL_EXAM_RELEASE_INVALID")
    historical = _read_factory_release(Path(run_dir), {
        "factory_release_sha256": sha,
        "factory_release_file": f"factory-releases/{sha}.json",
    })
    try:
        admission = AdmissionReceipt(**prior)
    except TypeError as exc:
        raise ValueError("HUMAN_TRAINER_HISTORICAL_EXAM_ADMISSION_INVALID") from exc
    admission.verify(historical)
    latest = receipt["school"]["current_student"]
    if (historical.course.version != receipt.get("curriculum_mode") or
            receipt.get("semantic_graph_sha256") != admission.semantic_graph_sha256 or
            admission.optimizer_step > latest["optimizer_step"] or
            (admission.optimizer_step == latest["optimizer_step"] and
             admission.student_sha256 != latest["sha256"])):
        raise ValueError("HUMAN_TRAINER_HISTORICAL_EXAM_LINEAGE_DRIFT")
    return historical


def _read_executable_factory_release_artifact(
        run_dir: Path, receipt: dict) -> ExecutableFactoryRelease:
    """Cold-read and structurally verify the immutable v2 artifact."""
    digest = receipt.get("factory_release_sha256")
    if (not isinstance(digest, str) or len(digest) != 64 or
            any(char not in "0123456789abcdef" for char in digest)):
        raise ValueError("FACTORY_EXECUTABLE_RELEASE_DIGEST_INVALID")
    release_file = receipt.get("factory_release_file")
    expected_file = "factory-releases/" + digest + ".json"
    if release_file != expected_file:
        raise ValueError("FACTORY_EXECUTABLE_RELEASE_NOT_ADMITTED_FOR_RUNTIME")
    path = run_dir / expected_file
    if path.parent.is_symlink() or path.is_symlink() or not path.is_file():
        raise ValueError("FACTORY_EXECUTABLE_RELEASE_DURABLE_ARTIFACT_MISSING")
    payload = json.loads(path.read_text())
    if payload.get("schema") != EXECUTABLE_SCHEMA:
        raise ValueError("FACTORY_EXECUTABLE_RELEASE_DURABLE_SCHEMA_INVALID")
    if payload.get("factory_release_sha256") != digest:
        raise ValueError("FACTORY_EXECUTABLE_RELEASE_ARTIFACT_DIGEST_DRIFT")
    release = ExecutableFactoryRelease.from_manifest(
        {key: value for key, value in payload.items()
         if key != "factory_release_sha256"}, digest)
    return release


def _read_executable_factory_release(
        run_dir: Path, receipt: dict, graph: dict) -> ExecutableFactoryRelease:
    """Cold-read v2 authority and bind it to the actual loaded semantic catalog."""
    release = _read_executable_factory_release_artifact(run_dir, receipt)
    release.require_foundation_capability_ids()
    release.verify_semantic_catalog(graph)
    return release


def _require_executable_factory_admission(
        run_dir: Path, receipt: dict, graph: dict) -> ExecutableFactoryRelease:
    """Verify cold v2 artifact plus exact student/catalog/graph baseline."""
    release = _read_executable_factory_release(run_dir, receipt, graph)
    raw = receipt.get("factory_admission_v2")
    if not isinstance(raw, dict):
        raise ValueError("FACTORY_EXECUTABLE_ADMISSION_RECEIPT_REQUIRED")
    try:
        admission = ExecutableAdmissionReceipt(**raw)
    except TypeError as exc:
        raise ValueError("FACTORY_EXECUTABLE_ADMISSION_RECEIPT_INVALID") from exc
    admission.verify(release)
    current = receipt["school"]["current_student"]
    admission.verify_baseline(
        student_sha256=current["sha256"], optimizer_step=current["optimizer_step"],
        semantic_graph_sha256=receipt.get("semantic_graph_sha256"))
    return release


def _require_factory_admission(run_dir, receipt, course, *, registry=None):
    """Fail closed before any live school work can use an admitted grade."""
    release = _read_factory_release(run_dir, receipt)
    if release.course != course:
        raise ValueError("FACTORY_ADMISSION_COURSE_MISMATCH")
    registry = registry if registry is not None else live_source_registry()
    if registry.descriptors_for(course) != release.source_adapters:
        raise ValueError("FACTORY_RELEASE_RUNTIME_SOURCE_ADAPTER_DRIFT")
    raw = receipt.get("factory_admission")
    if not isinstance(raw, dict):
        raise ValueError("FACTORY_ADMISSION_RECEIPT_REQUIRED")
    try:
        admission = AdmissionReceipt(**raw)
    except TypeError as exc:
        raise ValueError(_ADMISSION_RECEIPT_INVALID) from exc
    admission.verify(release)
    current = receipt["school"]["current_student"]
    if (admission.semantic_graph_sha256 != receipt.get("semantic_graph_sha256") or
            admission.optimizer_step > current["optimizer_step"] or
            (admission.optimizer_step == current["optimizer_step"] and
             admission.student_sha256 != current["sha256"])):
        raise ValueError("FACTORY_ADMISSION_BASELINE_DRIFT")
    return release


def admitted_release_supports_teaching_option(run_dir: Path, receipt: dict,
                                               option_id: str | None = None) -> bool:
    if option_id is not None and (not isinstance(option_id, str) or not option_id):
        raise ValueError("FACTORY_TEACHING_OPTION_ID_REQUIRED")
    if receipt.get("factory_admission_v2") is not None:
        release = _read_executable_factory_release_artifact(run_dir, receipt)
        return any(option_id is None or option_id in adapter.teaching_option_ids
                   for adapter in release.source_adapters if adapter.teaching_option_ids)
    release = _read_factory_release(run_dir, receipt)
    return any(option_id is None or item.option_id == option_id
               for item in release.teaching_options)
