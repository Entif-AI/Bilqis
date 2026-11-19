"""Generation-zero custody for the exact admitted executable Factory release."""
from __future__ import annotations

from pathlib import Path

from ..records import invalid


def _release_receipt(release_sha256: str) -> dict:
    return {
        "factory_release_sha256": release_sha256,
        "factory_release_file": f"factory-releases/{release_sha256}.json",
    }


def _is_release_artifact_name(name: str) -> bool:
    if not name.endswith(".json"):
        return False
    digest = name[:-5]
    return (len(digest) == 64
            and all(char in "0123456789abcdef" for char in digest))


def _require_release_root_shape(
        run_dir: Path, release_sha256: str, *,
        allow_other_releases: bool = False) -> None:
    root = Path(run_dir) / "factory-releases"
    if not root.exists() and not root.is_symlink():
        return
    if root.is_symlink() or not root.is_dir():
        invalid("BAMF_INITIAL_FACTORY_RELEASE_CUSTODY_INVALID")
    expected = f"{release_sha256}.json"
    entries = tuple(root.iterdir())
    if any(
            entry.is_symlink()
            or not entry.is_file()
            or not _is_release_artifact_name(entry.name)
            or (not allow_other_releases and entry.name != expected)
            for entry in entries):
        invalid("BAMF_INITIAL_FACTORY_RELEASE_CUSTODY_INVALID")


def persist_prepared_initial_factory_release(run_dir: Path, prepared) -> dict:
    """Persist the exact prepared release before generation-zero pointer install."""
    expected = prepared.candidate.run_identity.factory_release_sha256
    release = prepared.release
    if release.release_sha256 != expected:
        invalid("BAMF_INITIAL_FACTORY_RELEASE_CUSTODY_INVALID")
    _require_release_root_shape(run_dir, expected)
    from bilqis_mlx.runtime.admission import _persist_executable_factory_release

    relative = _persist_executable_factory_release(Path(run_dir), release)
    receipt = _release_receipt(expected)
    if relative != receipt["factory_release_file"]:
        invalid("BAMF_INITIAL_FACTORY_RELEASE_CUSTODY_INVALID")
    _require_release_root_shape(run_dir, expected)
    return receipt


def _require_initial_foundation_capability_ids(release) -> tuple[str, ...]:
    """Resolve foundation identity without rewriting historical release bytes.

    Current releases sign the inventory explicitly. Pre-upgrade v2 releases did
    not carry that wire field, but their execution plan was already part of the
    content-addressed release manifest. For an accepted generation-zero release,
    that sealed plan is the only lawful compatibility source.
    """
    if getattr(release, "_foundation_capability_wire", True):
        return release.require_foundation_capability_ids()
    release.verify()
    foundation = release.execution_plan.active_capability_inventory
    if (type(foundation) is not tuple or not foundation
            or len(set(foundation)) != len(foundation)
            or any(not isinstance(item, str) or not item for item in foundation)):
        invalid("BAMF_INITIAL_FACTORY_RELEASE_CUSTODY_INVALID")
    return foundation


def require_initial_factory_release(run_dir: Path, student):
    """Cold-verify release custody from accepted/sealed student identity only."""
    expected = student.run_identity.factory_release_sha256
    _require_release_root_shape(run_dir, expected, allow_other_releases=True)
    receipt = _release_receipt(expected)
    from bilqis_mlx.runtime.admission import _read_executable_factory_release_artifact

    release = _read_executable_factory_release_artifact(Path(run_dir), receipt)
    if (release.release_sha256 != expected
            or not _require_initial_foundation_capability_ids(release)):
        invalid("BAMF_INITIAL_FACTORY_RELEASE_CUSTODY_INVALID")
    _require_release_root_shape(run_dir, expected, allow_other_releases=True)
    return release


__all__ = (
    "persist_prepared_initial_factory_release",
    "require_initial_factory_release",
)
