"""C14.4 bridge from untrusted remote package bytes to C12/C05/B13 owners."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import os
from pathlib import Path

from bilqis_mlx.runtime.cognitive_package import CognitivePackage, PackageBinding, PackageKind
from bilqis_mlx.runtime.cognitive_package.adoption import publish_screened_delta_import
from bilqis_mlx.runtime.cognitive_package.delta import _all_delta_slices
from bilqis_mlx.runtime.cognitive_package import screen_received_package

from .admission import ContributionDecision
from .contracts import (
    ContributionClass, ContributionDisposition, RemoteWorkManifest,
    canonical_bytes, digest, invalid,
)
from .receipts import ReplayLedger, WorkerReceipt, verify_remote_receipt
from .replay import replay_store_for_run
from .school import require_current_school_identity


@dataclass(frozen=True)
class CanonicalPackageAdmissionContext:
    sender_dir: Path
    staging_dir: Path
    run_dir: Path
    max_wire_bytes: int
    source_context: object
    artifact_path: object
    target_capability: str
    export_clearance: object
    atlas_selection: object
    source_frontier: object
    reserve_gib: float = 100.0

    def __post_init__(self) -> None:
        if (not all(isinstance(value, Path) for value in (
                    self.sender_dir, self.staging_dir, self.run_dir))
                or type(self.max_wire_bytes) is not int
                or self.max_wire_bytes < 1
                or not isinstance(self.target_capability, str)
                or not self.target_capability
                or type(self.reserve_gib) not in (int, float)
                or float(self.reserve_gib) < 0):
            invalid("BAMF_C14_CANONICAL_ADMISSION_CONTEXT_INVALID")


def package_binding_digest(binding: PackageBinding) -> str:
    if type(binding) is not PackageBinding:
        invalid("BAMF_C14_PACKAGE_BINDING_INVALID")
    binding.__post_init__()
    return sha256(canonical_bytes(asdict(binding))).hexdigest()


def _package_from_receipt(
        manifest: RemoteWorkManifest, receipt: WorkerReceipt) -> CognitivePackage:
    if manifest.contribution_class is not ContributionClass.ADAPTER_DELTA:
        invalid("BAMF_C14_LEARNED_CONTRIBUTION_CLASS_INVALID")
    try:
        wire = receipt.artifact.payload.decode("utf-8")
    except UnicodeDecodeError:
        invalid("BAMF_C14_REMOTE_PACKAGE_ENCODING_INVALID")
    package = CognitivePackage.from_canonical_json(wire)
    expected_binding = package_binding_digest(package.binding)
    affected = tuple(sorted({
        value.parameter_name for value in _all_delta_slices(package)}))
    if (package.digest != receipt.artifact.digest
            or expected_binding != manifest.base_binding_digest
            or expected_binding != receipt.artifact.base_binding_digest
            or affected != receipt.artifact.affected_parameter_ids
            or not any(artifact.kind in {
                PackageKind.ADAPTER_DELTA, PackageKind.WEIGHT_DELTA}
                for artifact in package.artifacts)):
        invalid("BAMF_C14_REMOTE_PACKAGE_BINDING_INVALID")
    return package


def _require_c05_contract(manifest: RemoteWorkManifest, screened) -> None:
    """A learned manifest binds C05's live policy rather than inventing a score gate."""
    decision = getattr(screened, "decision", None)
    policy = getattr(decision, "policy_sha256", None)
    if (manifest.acceptance.requires_retention is not True
            or float(manifest.acceptance.minimum_score) != 0.0
            or manifest.acceptance.contract_digest != policy):
        invalid("BAMF_C14_CANONICAL_ACCEPTANCE_CONTRACT_MISMATCH")


def _materialize_ingress(package: CognitivePackage, directory: Path) -> Path:
    """Create only a local ingress copy; this path owns no canonical state."""
    raw = package.canonical_json.encode("utf-8")
    directory = Path(directory)
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        invalid("BAMF_C14_REMOTE_INGRESS_DIRECTORY_INVALID")
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{package.digest}.json"
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            invalid("BAMF_C14_REMOTE_INGRESS_ARTIFACT_INVALID")
        if destination.read_bytes() != raw:
            invalid("BAMF_C14_REMOTE_INGRESS_CONFLICT")
        return destination
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(destination, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(raw)
            target.flush()
            os.fsync(target.fileno())
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination


def admit_remote_cognitive_package(
        manifest: RemoteWorkManifest, receipt: WorkerReceipt, *,
        now: int, context: CanonicalPackageAdmissionContext) -> ContributionDecision:
    """Screen and, only when C05 accepts, publish through the canonical C12 path."""
    if type(context) is not CanonicalPackageAdmissionContext:
        invalid("BAMF_C14_CANONICAL_ADMISSION_CONTEXT_INVALID")
    context.__post_init__()
    verified = verify_remote_receipt(
        manifest, receipt, now=now, replay_ledger=ReplayLedger())
    require_current_school_identity(manifest, context.run_dir)
    if manifest.capability_id != context.target_capability:
        invalid("BAMF_C14_CANONICAL_CAPABILITY_MISMATCH")
    package = _package_from_receipt(manifest, receipt)
    ledger = replay_store_for_run(context.run_dir).claim(
        manifest.replay_id, manifest.digest, verified.receipt_digest)
    _materialize_ingress(package, context.sender_dir)
    screened = screen_received_package(
        context.sender_dir, context.staging_dir, package.digest, context.run_dir,
        max_wire_bytes=context.max_wire_bytes,
        source_context=context.source_context,
        artifact_path=context.artifact_path,
        target_capability=context.target_capability,
        export_clearance=context.export_clearance,
        atlas_selection=context.atlas_selection,
        source_frontier=context.source_frontier)
    _require_c05_contract(manifest, screened)
    evidence = screened.decision.evidence_sha256
    if not screened.decision.accepted:
        return ContributionDecision(
            ContributionDisposition.REJECTED, manifest.digest,
            verified.receipt_digest, evidence, ledger,
            screened.decision.reason)
    published = publish_screened_delta_import(
        screened, context.run_dir, export_clearance=context.export_clearance,
        atlas_selection=context.atlas_selection,
        source_frontier=context.source_frontier,
        source_context=context.source_context,
        reserve_gib=context.reserve_gib)
    generation = published.get("manifest_sha256") if isinstance(published, dict) else None
    if not digest(generation):
        invalid("BAMF_C14_CANONICAL_PUBLICATION_RECEIPT_INVALID")
    return ContributionDecision(
        ContributionDisposition.ADMITTED, manifest.digest,
        verified.receipt_digest, evidence, ledger,
        screened.decision.reason, generation)
