"""Cheap live currentness for one deeply authenticated active generated grade."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL

from .active_generated_grade_contracts import ActiveGeneratedGrade


_ISSUER = object()


def _fail(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_ATLAS_ADMISSION.INVALID, reason=reason)


def _file_identity(path: Path) -> tuple[int, int, int, int, int]:
    try:
        if path.is_symlink() or not path.is_file():
            raise OSError
        info = path.stat()
    except OSError:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CURRENTNESS_DRIFT")
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


@dataclass(frozen=True, init=False, eq=False)
class _ActiveGeneratedGradeCurrentness:
    run_dir: Path
    active: ActiveGeneratedGrade
    file_identities: tuple
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CURRENTNESS_CALLER_CONSTRUCTION_FORBIDDEN")


def _bootstrap_paths(
        run_dir: Path, active: ActiveGeneratedGrade) -> tuple[Path, ...]:
    root = Path(run_dir)
    return (
        root / "generated-grades" / "current.json",
        root / "generated-grades" / "definitions"
            / f"{active.definition.definition_sha256}.json",
        root / "generated-grades" / "activations"
            / f"{active.activation_sha256}.json",
        root / "generated-grade-proposals" / "initial-bootstrap"
            / f"{active.proposal_sha256}.json",
        root / "factory-releases"
            / f"{active.definition.adopted_release_sha256}.json",
    )


def _snapshot(run_dir: Path, active: ActiveGeneratedGrade) -> tuple:
    return tuple(
        (path.resolve(), _file_identity(path))
        for path in _bootstrap_paths(run_dir, active)
    )


def bind_active_generated_grade_currentness(
        run_dir: Path, active: ActiveGeneratedGrade):
    """Bind only the live BOOTSTRAP lineage; successors keep deep validation."""
    if type(active) is not ActiveGeneratedGrade or active.transition_kind != "BOOTSTRAP":
        return None
    before = _snapshot(run_dir, active)
    from .active_generated_grade import read_active_generated_grade
    observed = read_active_generated_grade(Path(run_dir), repair=False)
    after = _snapshot(run_dir, active)
    if before != after or observed != active:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CURRENTNESS_DRIFT")
    witness = object.__new__(_ActiveGeneratedGradeCurrentness)
    for name, value in (
        ("run_dir", Path(run_dir).resolve()),
        ("active", active),
        ("file_identities", after),
        ("_issuance", _ISSUER),
    ):
        object.__setattr__(witness, name, value)
    return witness


def require_active_generated_grade_currentness(
        witness, run_dir: Path, *, expected_activation_sha256: str,
        expected_definition_sha256: str) -> ActiveGeneratedGrade:
    if (type(witness) is not _ActiveGeneratedGradeCurrentness
            or getattr(witness, "_issuance", None) is not _ISSUER
            or witness.run_dir != Path(run_dir).resolve()
            or type(witness.active) is not ActiveGeneratedGrade
            or witness.active.transition_kind != "BOOTSTRAP"
            or witness.active.activation_sha256 != expected_activation_sha256
            or witness.active.definition.definition_sha256
               != expected_definition_sha256
            or _snapshot(run_dir, witness.active) != witness.file_identities):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CURRENTNESS_DRIFT")
    return witness.active


_bind_active_generated_grade_currentness = bind_active_generated_grade_currentness
_require_active_generated_grade_currentness = require_active_generated_grade_currentness
