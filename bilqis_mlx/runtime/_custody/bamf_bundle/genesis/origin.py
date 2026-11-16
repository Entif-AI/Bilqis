"""Persisted runtime authority for one B13 generation-zero Factory foundation."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.factory.executable_release import (
    ExecutableAdmissionReceipt, ExecutableFactoryRelease,
)
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.admission import _require_executable_factory_admission
from bilqis_mlx.runtime.state import _fingerprint
from bilqis_mlx.state_dag import read_current, read_generation

from ..records import invalid


_FACTORY_FOUNDATION_ISSUER = object()


@dataclass(frozen=True, init=False)
class InitialFactoryFoundationAuthority:
    """Live authority replayed from the canonical persisted operator state."""

    source_run_dir: str
    current_state_sha256: str
    release: ExecutableFactoryRelease
    admission: ExecutableAdmissionReceipt
    origin_checkpoint: Checkpoint
    semantic_graph_sha256: str
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        invalid("BAMF_INITIAL_GENERATION_FACTORY_AUTHORITY_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self) -> None:
        if (getattr(self, "_issuance", None) is not _FACTORY_FOUNDATION_ISSUER
                or not isinstance(self.source_run_dir, str) or not self.source_run_dir
                or not isinstance(self.current_state_sha256, str)
                or len(self.current_state_sha256) != SHA256_HEX_LENGTH
                or type(self.release) is not ExecutableFactoryRelease
                or type(self.admission) is not ExecutableAdmissionReceipt
                or type(self.origin_checkpoint) is not Checkpoint
                or not isinstance(self.semantic_graph_sha256, str)
                or len(self.semantic_graph_sha256) != SHA256_HEX_LENGTH):
            invalid("BAMF_INITIAL_GENERATION_FACTORY_AUTHORITY_INVALID")


def issue_initial_factory_foundation_authority(
        source_run_dir: str | Path, graph: dict) -> InitialFactoryFoundationAuthority:
    """Issue B13 bootstrap input only from the immutable current runtime owner."""
    run_dir = Path(source_run_dir).resolve()
    if not isinstance(graph, dict):
        invalid("BAMF_INITIAL_GENERATION_FACTORY_AUTHORITY_INVALID")
    try:
        current = read_current(run_dir)
        generation = current.get("generation")
        if (type(generation) is not int or generation < 0
                or read_generation(run_dir, generation) != current):
            invalid("BAMF_INITIAL_GENERATION_FACTORY_AUTHORITY_INVALID")
        release = _require_executable_factory_admission(run_dir, current, graph)
        raw = current.get("factory_admission_v2")
        school = current.get("school")
        student = school.get("current_student") if isinstance(school, dict) else None
        if not isinstance(raw, dict) or not isinstance(student, dict):
            invalid("BAMF_INITIAL_GENERATION_FACTORY_AUTHORITY_INVALID")
        admission = ExecutableAdmissionReceipt(**raw)
        origin = Checkpoint(**student)
    except Exception:
        invalid("BAMF_INITIAL_GENERATION_FACTORY_AUTHORITY_INVALID")
    if (admission.semantic_graph_sha256 != _fingerprint(graph)
            or admission.semantic_graph_sha256 != current.get("semantic_graph_sha256")):
        invalid("BAMF_INITIAL_GENERATION_FACTORY_AUTHORITY_DRIFT")
    authority = object.__new__(InitialFactoryFoundationAuthority)
    for name, value in (
            ("source_run_dir", str(run_dir)),
            ("current_state_sha256", _fingerprint(current)),
            ("release", release), ("admission", admission),
            ("origin_checkpoint", origin),
            ("semantic_graph_sha256", admission.semantic_graph_sha256),
            ("_issuance", _FACTORY_FOUNDATION_ISSUER)):
        object.__setattr__(authority, name, value)
    authority.__post_init__()
    return authority


def replay_initial_factory_foundation_authority(
        authority, graph: dict) -> InitialFactoryFoundationAuthority:
    """Re-enter the persisted owner immediately before bootstrap use or mutation."""
    if type(authority) is not InitialFactoryFoundationAuthority:
        invalid("BAMF_INITIAL_GENERATION_FACTORY_AUTHORITY_INVALID")
    authority.__post_init__()
    expected = issue_initial_factory_foundation_authority(
        authority.source_run_dir, graph)
    if authority != expected:
        invalid("BAMF_INITIAL_GENERATION_FACTORY_AUTHORITY_DRIFT")
    return expected


__all__ = (
    "InitialFactoryFoundationAuthority",
    "issue_initial_factory_foundation_authority",
    "replay_initial_factory_foundation_authority",
)
