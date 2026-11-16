"""Private C05 Factory retention preparation and cohort helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_candidate import CandidateTransaction, resolve_candidate
from bilqis_mlx.learning.atlas_package_import import PackageImportTransaction
from bilqis_mlx.runtime.atlas_training_authority import (
    BamfLogicalBatchTrainingAuthority, BamfTrainingAuthority,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache, derive_motif_successor_bundle,
    derive_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.capability_retention import (
    EvidenceKind, EvidenceStage, EvaluationCohort, RetentionPolicy, case_census_digest,
)
from bilqis_mlx.runtime.source_execution import _source_family
from bilqis_mlx.semantics.domains import contract_digest

from .capability_evaluation import _invalid
from .factory_complete_solver import _factory_evaluation_instrument, _generation

C05_PROBE_EACH = 6
C05_PROTECTED_REFERENCE_LOSS = 1
C05_FRESH_TARGET_SEED_OFFSET = 104729
C05_FRESH_LESSON_SEED_OFFSET = 130363
C05_MAX_FRESH_DRAWS = 32


def _training_exclusions(candidate: CandidateTransaction):
    families, episodes = set(), set()
    if not candidate.training_authorities:
        _invalid("BAMF_C05_TRAINING_SOURCE_INDEPENDENCE_UNAVAILABLE")
    for proof, authority in zip(candidate.step_proofs, candidate.training_authorities):
        if type(authority) is BamfTrainingAuthority:
            authority.__post_init__()
            members = (authority,)
            valid = (proof.training_authority_sha256 == authority.digest
                     and proof.source_family_id == authority.source_family_id
                     and proof.episode_id == authority.episode_id)
        elif type(authority) is BamfLogicalBatchTrainingAuthority:
            authority.__post_init__()
            members = authority.members
            valid = (proof.training_authority_sha256 == authority.digest
                     and proof.training_authority_members == tuple(
                         (member.digest, member.source_family_id, member.episode_id)
                         for member in members))
        else:
            members, valid = (), False
        if not valid:
            _invalid("BAMF_C05_TRAINING_SOURCE_INDEPENDENCE_UNAVAILABLE")
        families.update(member.source_family_id for member in members)
        episodes.update(member.episode_id for member in members)
    if not families or not episodes:
        _invalid("BAMF_C05_TRAINING_SOURCE_INDEPENDENCE_UNAVAILABLE")
    return tuple(sorted(families)), tuple(sorted(episodes))


def _owner_seed(release_sha256, cache, target_capability, candidate_sha256):
    digest = contract_digest({
        "schema": "bilqis.mlx.c05-fresh-seed/v1",
        "factory_release": release_sha256,
        "run": cache.run_id,
        "parent_generation": cache.generation,
        "parent_manifest": cache.accepted_manifest_sha256,
        "candidate": candidate_sha256,
        "target_capability": target_capability,
    })
    return int(digest[:16], 16)


def _candidate_from_live_parent(run_dir: Path, transaction: CandidateTransaction):
    """Bind one speculative B12 transaction to the current accepted B13 parent."""
    parent = load_accepted_generation(run_dir)
    cache = bind_accepted_execution_cache(run_dir)
    custody = transaction.parent.custody
    if (transaction.update_steps < 1 or custody is None
            or candidate_identity_digest(transaction.parent)
            != candidate_identity_digest(parent.retained_state)
            or custody.run_id != cache.run_id
            or custody.generation != cache.generation
            or custody.manifest_sha256 != cache.accepted_manifest_sha256
            or custody.topology_digest != parent.topology.digest
            or custody.extents_digest != parent.extents.digest):
        _invalid("BAMF_C05_CANDIDATE_PARENT_CUSTODY_MISMATCH")
    preview = resolve_candidate(transaction, accepted=True)
    if transaction.motif_transition is None:
        successor = derive_successor_bundle(
            parent, preview,
            parent_manifest_sha256=cache.accepted_manifest_sha256,
            delivery_events=())
    else:
        successor = derive_motif_successor_bundle(
            parent, transaction,
            parent_manifest_sha256=cache.accepted_manifest_sha256,
            delivery_events=())
    return parent, successor, preview, cache


def _package_import_from_live_parent(
        run_dir: Path, transaction: PackageImportTransaction):
    """Bind one B12 package-import proposal to the current accepted B13 parent."""
    if type(transaction) is not PackageImportTransaction:
        _invalid("BAMF_C05_PACKAGE_IMPORT_PARENT_CUSTODY_MISMATCH")
    parent = load_accepted_generation(run_dir)
    cache = bind_accepted_execution_cache(run_dir)
    custody = transaction.parent.custody
    if (custody is None
            or candidate_identity_digest(transaction.parent)
            != candidate_identity_digest(parent.retained_state)
            or custody.run_id != cache.run_id
            or custody.generation != cache.generation
            or custody.manifest_sha256 != cache.accepted_manifest_sha256
            or custody.topology_digest != parent.topology.digest
            or custody.extents_digest != parent.extents.digest):
        _invalid("BAMF_C05_PACKAGE_IMPORT_PARENT_CUSTODY_MISMATCH")
    successor = derive_successor_bundle(
        parent, transaction.candidate,
        parent_manifest_sha256=cache.accepted_manifest_sha256,
        delivery_events=())
    return parent, successor, transaction.candidate, cache


def _instruments(source_context, candidate, artifact_path, rows, *, seed, each=None):
    generation = _generation(candidate)
    counts = {}
    if each is None:
        for row in rows:
            capability = row.get("capability")
            counts[capability] = counts.get(capability, 0) + 1
    return tuple(_factory_evaluation_instrument(
        source_context, candidate, artifact_path, row,
        source_seed=seed,
        source_each=(each if each is not None else counts[row.get("capability")]),
        generation=generation,
    ) for row in rows)


@dataclass(frozen=True)
class _FreshDraw:
    seed: int
    rows: tuple[dict, ...]


def _independent_draw(source_context, rows, seed, training):
    families, episodes, identities = set(), set(), set()
    for row in rows:
        identity = row.get("id")
        if not isinstance(identity, str) or not identity:
            _invalid("BAMF_C05_FRESH_SOURCE_ROW_INVALID")
        family = row.get("source_family_id")
        if not isinstance(family, str) or not family:
            execution = source_context.release.execution_plan.capability_map[row["capability"]]
            family = _source_family(execution)
        episode = row.get("episode_id")
        if not isinstance(episode, str) or not episode:
            episode = identity
        if identity in identities or episode in episodes:
            return False
        identities.add(identity)
        episodes.add(episode)
        families.add(family)
    return not (families.intersection(training[0])
                or episodes.intersection(training[1])
                or identities.intersection(training[1]))


def _fresh_rows(
        source_context, capabilities, *, seed, training, require_independent=True):
    """Redraw whole owner cohorts on provenance collisions, never on scores."""
    for offset in range(C05_MAX_FRESH_DRAWS):
        draw_seed = seed + offset
        rows = []
        for capability in capabilities:
            drawn = source_context.draw_rows(
                seed=draw_seed, capability=capability, each=C05_PROBE_EACH)
            if (len(drawn) != C05_PROBE_EACH
                    or any(row.get("capability") != capability for row in drawn)):
                _invalid("BAMF_C05_FRESH_SOURCE_COVERAGE_INCOMPLETE")
            rows.extend(drawn)
        comparison = training if require_independent else ((), ())
        if _independent_draw(source_context, rows, draw_seed, comparison):
            return _FreshDraw(draw_seed, tuple(rows))
    _invalid("BAMF_C05_INDEPENDENT_SOURCE_DRAW_EXHAUSTED")


def _cohort(
        kind, instruments, groups, release, policy, training, *,
        evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION):
    cases = tuple(item.case for item in instruments)
    rubric = contract_digest(tuple(
        (item.grade_id, item.assessment_blueprint_sha256)
        for item in release.execution_plan.grades))
    scope = contract_digest((
        release.execution_plan.curriculum_sha256,
        release.execution_plan.profile_id,
        policy.capability_groups,
    ))
    source = release.execution_plan.projection_digests.source
    return EvaluationCohort(
        kind, cases, tuple(groups), rubric, scope, source, policy.digest(),
        training[0], training[1], case_census_digest(cases),
        evidence_stage=evidence_stage)


def _policy_and_cohorts(
    release, groups, target_capability, target_group, training,
    target_instruments, lesson_instruments, fixed_instruments, *,
    evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
):
    required = (
        (EvidenceKind.FRESH_TARGET,
         case_census_digest(tuple(item.case for item in target_instruments))),
        (EvidenceKind.FRESH_LESSON,
         case_census_digest(tuple(item.case for item in lesson_instruments))),
        (EvidenceKind.FIXED_SCHOOL,
         case_census_digest(tuple(item.case for item in fixed_instruments))),
    )
    policy = RetentionPolicy(
        groups, tuple(dict.fromkeys(group for _, group in groups)),
        tuple((capability, C05_PROTECTED_REFERENCE_LOSS)
              for capability, _ in groups if capability != target_capability),
        C05_PROBE_EACH, required)
    target_cohort = _cohort(
        EvidenceKind.FRESH_TARGET, target_instruments,
        ((target_capability, target_group),), release, policy, training,
        evidence_stage=evidence_stage)
    lesson_groups = tuple(pair for pair in groups if pair[1] == target_group)
    lesson_cohort = _cohort(
        EvidenceKind.FRESH_LESSON, lesson_instruments,
        lesson_groups, release, policy, training, evidence_stage=evidence_stage)
    fixed_cohort = _cohort(
        EvidenceKind.FIXED_SCHOOL, fixed_instruments,
        groups, release, policy, training, evidence_stage=evidence_stage)
    return policy, (target_cohort, lesson_cohort, fixed_cohort)
