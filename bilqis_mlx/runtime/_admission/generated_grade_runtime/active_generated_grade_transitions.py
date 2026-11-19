"""Authorized successor transitions for active generated-grade custody."""
from pathlib import Path

from . import active_generated_grade_custody as _custody
def activate_corrected_generated_grade(
        run_dir: Path, proposal, *, correction_event_id: str):
    from . import active_generated_grade as owner
    root = Path(run_dir)
    predecessor = owner.read_active_generated_grade(root)
    if (predecessor.transition_kind == "CORRECTION"
            and predecessor.proposal_sha256 == proposal.proposal_sha256):
        prior = owner.require_correction_transition_authority(root, predecessor)
        if prior.correction_record_sha256 == correction_event_id:
            return predecessor
    identity = owner._accepted_generation_identity(root)
    definition = owner.seal_accepted_generated_grade(root, proposal)
    from bilqis_mlx.runtime.bamf_bundle.publication import _pointer_lock
    with _pointer_lock(root, create=True):
        owner._require_identity_still_current(root, identity)
        current = _custody._read_stored_active(root)
        if current is None:
            owner._fail("BAMF_ACTIVE_GENERATED_GRADE_PREDECESSOR_DRIFT")
        if current.activation_sha256 != predecessor.activation_sha256:
            if (current.transition_kind == "CORRECTION"
                    and current.proposal_sha256 == proposal.proposal_sha256):
                prior = owner.require_correction_transition_authority(root, current)
                if prior.correction_record_sha256 == correction_event_id:
                    return current
            owner._fail("BAMF_ACTIVE_GENERATED_GRADE_PREDECESSOR_DRIFT")
        authority = owner._issue_correction_transition_authority(
            root, accepted_manifest_sha256=identity[2],
            correction_record_sha256=correction_event_id,
            predecessor=predecessor, proposal=proposal, definition=definition)
        active = owner._active_from_proposal(
            identity, proposal, definition, predecessor=predecessor,
            transition_kind="CORRECTION",
            transition_receipt_sha256=authority.authority_sha256,
            transition_reason=authority.reason_code)
        owner._persist_proposal_acceptance(root, active, proposal)
        _custody._persist_activation(root, active)
    return owner.read_active_generated_grade(root)


def activate_certified_generated_grade(
        run_dir: Path, *, certification_receipt_sha256: str):
    from . import active_generated_grade as owner
    root = Path(run_dir)
    predecessor = owner.read_active_generated_grade(root)
    proposal = _custody._accepted_bound_generated_grade_proposal(root)
    if proposal.predecessor_certification_sha256 != certification_receipt_sha256:
        owner._fail("BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_ANCESTRY_DRIFT")
    identity = owner._accepted_generation_identity(root)
    definition = owner.seal_accepted_generated_grade(root, proposal)
    from bilqis_mlx.runtime.bamf_bundle.publication import _pointer_lock
    with _pointer_lock(root, create=True):
        owner._require_identity_still_current(root, identity)
        current = _custody._read_stored_active(root)
        if (current is None
                or current.activation_sha256 != predecessor.activation_sha256):
            owner._fail("BAMF_ACTIVE_GENERATED_GRADE_PREDECESSOR_DRIFT")
        authority = owner._issue_certification_transition_authority(
            root, accepted_manifest_sha256=identity[2],
            certification_receipt_sha256=certification_receipt_sha256,
            predecessor=predecessor, proposal=proposal, definition=definition)
        active = owner._active_from_proposal(
            identity, proposal, definition, predecessor=predecessor,
            transition_kind="CERTIFICATION",
            transition_receipt_sha256=authority.authority_sha256,
            transition_reason=authority.reason_code)
        owner._persist_proposal_acceptance(root, active, proposal)
        _custody._persist_activation(root, active)
    return owner.read_active_generated_grade(root)
