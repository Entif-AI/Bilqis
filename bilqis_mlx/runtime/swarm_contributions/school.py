"""Current canonical-school identity checks shared by C14.4 admission paths."""
from pathlib import Path

from bilqis_mlx.runtime.cognitive_package.receiver import _load_current_generation

from .contracts import RemoteWorkManifest, invalid


def require_current_school_identity(
        manifest: RemoteWorkManifest, run_dir: Path) -> None:
    """Reject work issued for any generation/source/model/topology no longer current."""
    pointer, student = _load_current_generation(Path(run_dir))
    if (manifest.retained_generation != pointer.get("manifest_sha256")
            or manifest.source_release != student.provenance.release_digest
            or manifest.model_identity != student.implementation_sha256
            or manifest.topology_identity != student.topology.digest):
        invalid("BAMF_C14_CANONICAL_SCHOOL_IDENTITY_MISMATCH")
