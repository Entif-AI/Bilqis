"""Typed school bamf error contracts."""
from __future__ import annotations

from .base import _spec

class BAMF_ATLAS_ADMISSION:
    INVALID = _spec(
        ("SCHOOL", "BAMF_ATLAS_ADMISSION", "INVALID"),
        owner="runtime.atlas_admission",
        title="BAMF Atlas lease or admission boundary invalid",
        message_template="BAMF Atlas admission is invalid: {reason}",
        disposition="STAGE_AND_INSPECT",
        next_action="Keep the retained run unchanged; reconcile explicit human authorization, source rights and exact successor custody.",
    )
    FLYWHEEL_RUNTIME_INVALID = _spec(
        ("SCHOOL", "BAMF_ATLAS_ADMISSION", "FLYWHEEL_RUNTIME_INVALID"),
        owner="runtime.atlas_flywheel_runtime",
        title="Accepted Atlas flywheel runtime invalid",
        message_template="The accepted-custody flywheel runtime inputs are invalid.",
        disposition="PRESERVE_AND_INSPECT",
        next_action="Preserve accepted custody and reconstruct the flywheel only from the accepted run, source graph and configured reserve.",
        legacy_codes=("BAMF_ATLAS_FLYWHEEL_RUNTIME_INVALID",),
    )
    ACCEPTED_LEASE_REQUIRED = _spec(
        ("SCHOOL", "BAMF_ATLAS_ADMISSION", "ACCEPTED_LEASE_REQUIRED"),
        owner="runtime.atlas_flywheel_runtime",
        title="Accepted Atlas lease required",
        message_template="The cold admission flywheel has no accepted Atlas v2 lease for this run.",
        disposition="STAGE_AND_INSPECT",
        next_action="Leave accepted custody unchanged and require the existing explicit human enrollment path before admission can continue.",
        legacy_codes=("BAMF_ATLAS_V2_ACCEPTED_LEASE_REQUIRED",),
    )
    FLYWHEEL_PREDECESSOR_DRIFT = _spec(
        ("SCHOOL", "BAMF_ATLAS_ADMISSION", "FLYWHEEL_PREDECESSOR_DRIFT"),
        owner="runtime.atlas_flywheel_runtime",
        title="Atlas flywheel predecessor drift",
        message_template="The accepted Factory release no longer matches the predecessor bound into the proposed Atlas handoff.",
        disposition="PRESERVE_AND_RELOAD",
        next_action="Reject the stale handoff, preserve the accepted generation, and rebuild planner state from current accepted custody.",
        legacy_codes=("BAMF_ATLAS_FLYWHEEL_ACCEPTED_PREDECESSOR_DRIFT",),
    )


class BAMF_CONTROL_PLANE:
    INVALID = _spec(
        ("SCHOOL", "BAMF_CONTROL_PLANE", "INVALID"),
        owner="control_plane.service",
        title="BAMF local control-plane boundary invalid",
        message_template="The BAMF local control-plane boundary is invalid: {reason}",
        disposition="PRESERVE_AND_INSPECT",
        next_action="Keep learner and checkpoint custody unchanged; reconcile the local service transport, protocol session, or accepted-generation read boundary before retry.",
    )


class BAMF_SALIENCE:
    INVALID = _spec(
        ("SCHOOL", "BAMF_SALIENCE", "INVALID"),
        owner="learning.atlas_salience",
        title="BAMF salience evidence or policy invalid",
        message_template="BAMF salience evidence is invalid: {reason}",
        disposition="PRESERVE_AND_INSPECT",
        next_action="Preserve the signed facts and source frontier; reconcile policy, scope and causal evidence.",
    )


class BAMF_CAPABILITY_EVIDENCE:
    INVALID = _spec(
        ("SCHOOL", "BAMF_CAPABILITY_EVIDENCE", "INVALID"),
        owner="runtime.capability_retention",
        title="BAMF paired capability evidence invalid",
        message_template="BAMF paired capability evidence is invalid: {reason}",
        disposition="PRESERVE_AND_INSPECT",
        next_action="Preserve both generations; reconcile source, cohort, rubric and complete capability coverage.",
    )


class BAMF_SOLVER:
    INVALID = _spec(
        ("SCHOOL", "BAMF_SOLVER", "INVALID"),
        owner="runtime.cognitive_solver",
        title="BAMF cognitive solver route or source binding invalid",
        message_template="A BAMF cognitive solver route is invalid: {reason}",
        disposition="PRESERVE_AND_INSPECT",
        next_action="Retain the source-bound task and generation; reconcile exact operator, cache and neural proposal authority.",
    )


class BAMF_AKASHA:
    INVALID = _spec(
        ("SCHOOL", "BAMF_AKASHA", "INVALID"),
        owner="runtime.akasha_outbox",
        title="BAMF Akasha event or outbox contract invalid",
        message_template="A source-bound Akasha event or delivery attempt is invalid: {reason}",
        disposition="PRESERVE_AND_INSPECT",
        next_action="Keep the append-only history intact; reconcile event identity and source receipts before retry.",
    )


class BAMF_RESOURCES:
    INVALID = _spec(
        ("SCHOOL", "BAMF_RESOURCES", "INVALID"),
        owner="runtime.atlas_resources",
        title="BAMF resource plan or gradient boundary invalid",
        message_template="A BAMF resource or optimizer-step contract is invalid: {reason}",
        disposition="PRESERVE_AND_INSPECT",
        next_action="Keep the retained candidate unchanged; reconcile the exact source rows, topology, budget and gradient receipt.",
    )


class BAMF_REVALIDATION:
    INVALID = _spec(
        ("SCHOOL", "BAMF_REVALIDATION", "INVALID"),
        owner="runtime.atlas_revalidation",
        title="BAMF correction dependency or revalidation invalid",
        message_template="A source-bound correction or derived artifact is not safe to use: {reason}",
        disposition="PRESERVE_AND_INSPECT",
        next_action="Hold the affected artifact and reconcile its source-owned evidence before reuse.",
    )
    PROPAGATION_FAILURE = _spec(
        ("SCHOOL", "BAMF_REVALIDATION", "PROPAGATION_FAILURE"),
        owner="runtime.atlas_temporal_revalidation",
        title="Correction remediation failed to prevent stale replay",
        message_template="Superseded source evidence reappeared after remediation: {reason}",
        disposition="REQUALIFICATION_REQUIRED",
        next_action="Hold the affected lineage, preserve the original source and remediation receipts, then require fresh source-grounded requalification.",
    )


class BAMF_TEACHER:
    INVALID = _spec(
        ("SCHOOL", "BAMF_TEACHER", "INVALID"), owner="learning.teacher_vnext_replay",
        title="Invalid BAMF teacher successor binding",
        message_template="The teacher successor binding is invalid: {reason}",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Inspect replay and student identity without modifying the retained learner.",
    )


class BAMF_TRAINING_ADAPTER:
    INVALID = _spec(
        ("SCHOOL", "BAMF_TRAINING_ADAPTER", "INVALID"), owner="runtime.atlas_training_adapter",
        title="Invalid BAMF training input",
        message_template="The delivered training input violates its contract: {reason}",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Inspect the released source and delivery metadata before retrying.",
    )


class BAMF_FIRST_STUDENT:
    INVALID = _spec(
        ("SCHOOL", "BAMF_FIRST_STUDENT", "INVALID"),
        owner="runtime.bamf_first_student",
        title="BAMF first-student preflight is invalid",
        message_template="The BAMF first-student preflight is invalid: {reason}",
        disposition="PRESERVE_AND_INSPECT",
        next_action="Keep the admitted source run unchanged; reconcile the launch config, Factory/Atlas bindings and empty target before retrying.",
    )


class BAMF_WORKSTACK:
    VALIDATION_INVALID = _spec(
        ("SCHOOL", "BAMF_WORKSTACK", "VALIDATION_INVALID"), owner="scripts.check_bamf_workstack",
        title="BAMF workstack validation failed",
        message_template="Workstack validation failed: {reason}",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Inspect the reported workstack invariant and preserve source evidence.",
    )
    INPUT_INVALID = _spec(
        ("SCHOOL", "BAMF_WORKSTACK", "INPUT_INVALID"), owner="scripts.check_bamf_workstack",
        title="BAMF workstack input unavailable or malformed",
        message_template="Workstack or registry input could not be read: {error_type}",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Inspect the input file and preserve its current contents.",
    )


class QUALIFICATION:
    INVALID = _spec(
        ("SCHOOL", "QUALIFICATION", "INVALID"), owner="runtime.qualification_manifest",
        title="Qualification preflight failed",
        message_template="Frozen qualification input or operator boundary is invalid: {detail}",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Inspect the pinned qualification manifest and retain all existing run evidence.",
    )


class TEACHER_OBSERVATION:
    INVALID = _spec(
        ("SCHOOL", "TEACHER_OBSERVATION", "INVALID"), owner="runtime.teacher_observations",
        title="Invalid teacher observation", message_template="The teacher observation record or provenance is invalid.",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Preserve the candidate result and inspect the observation schema and provenance.",
    )
    CONTENT_MISMATCH = _spec(
        ("SCHOOL", "TEACHER_OBSERVATION", "CONTENT_MISMATCH"), owner="runtime.teacher_observations",
        title="Teacher observation content mismatch", message_template="The content-addressed teacher observation sidecar is missing, corrupt, or not the recorded content.",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Preserve the run and reconcile the sidecar path and digest before replay.",
    )
    DUPLICATE_ATTEMPT = _spec(
        ("SCHOOL", "TEACHER_OBSERVATION", "DUPLICATE_ATTEMPT"), owner="runtime.teacher_observations",
        title="Divergent duplicate teacher observation", message_template="One candidate attempt has divergent committed teacher observations.",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Preserve both receipts and reconcile the durable outbox before any replay.",
    )


class MODEL_TOPOLOGY:
    INVALID = _spec(
        ("SCHOOL", "MODEL_TOPOLOGY", "INVALID"), owner="runtime.model_topology",
        title="Invalid model topology", message_template="The requested model topology is invalid.",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Provide positive structural dimensions with a width divisible by head count.",
        legacy_codes=("MODEL_TOPOLOGY_INVALID",),
    )
    RECORD_INVALID = _spec(
        ("SCHOOL", "MODEL_TOPOLOGY", "RECORD_INVALID"), owner="runtime.model_topology",
        title="Invalid persisted model topology", message_template="The persisted model topology record is invalid.",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Preserve the run and inspect its immutable topology metadata.",
        legacy_codes=("MODEL_TOPOLOGY_RECORD_INVALID",),
    )
    MISMATCH = _spec(
        ("SCHOOL", "MODEL_TOPOLOGY", "MISMATCH"), owner="runtime.model_topology",
        title="Model topology mismatch", message_template="Requested, persisted, or recovered model topology does not match.",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Resume with the persisted topology; do not mutate a run's structure.",
        legacy_codes=("MODEL_TOPOLOGY_MISMATCH",),
    )
    PARAMETER_SHAPES_INVALID = _spec(
        ("SCHOOL", "MODEL_TOPOLOGY", "PARAMETER_SHAPES_INVALID"), owner="runtime.model_topology",
        title="Model parameter shapes do not match topology", message_template="Loaded parameters do not match the persisted model topology.",
        disposition="CORRECT_INPUT_OR_STATE",
        next_action="Preserve the checkpoint and inspect topology and tensor provenance.",
        legacy_codes=("MODEL_TOPOLOGY_PARAMETER_SHAPES_INVALID",),
    )


class BAMF_DELIVERY:
    INVALID = _spec(
        ("SCHOOL", "BAMF_DELIVERY", "INVALID"), owner="runtime.delivery",
        title="BAMF delivery evidence invalid",
        message_template="BAMF delivery evidence is invalid: {reason}",
        disposition="PRESERVE_AND_INSPECT",
        next_action="Preserve the last valid delivery receipt; reconcile immutable issue, commit, proof, review and command evidence before publication.",
    )


class BAMF_PACKAGE:
    INVALID = _spec(
        ("SCHOOL", "BAMF_PACKAGE", "INVALID"), owner="runtime.cognitive_package",
        title="BAMF cognitive package invalid",
        message_template="Cognitive package is invalid: {reason}",
        disposition="PRESERVE_AND_INSPECT",
        next_action="Preserve the receiver generation; inspect exact bindings and source clearance before staging again.",
    )
