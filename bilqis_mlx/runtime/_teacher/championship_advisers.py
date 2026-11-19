"""Native R05 championship advisers over already-lawful Factory source rows."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import math

import mlx.core as mx

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning._championship.adviser_supervision import (
    MentorRowInfluence, issue_mentor_supervision, mentor_policy_binding,
)
from bilqis_mlx.learning._championship.champion_confidence import MAX_INFLUENCE
from bilqis_mlx.learning._championship.cohort_soup import (
    POLICY_ID, cohort_soup_recipe, cohort_vote_count, partitioned_recipes,
    read_frozen_cohort_soup, save_frozen_cohort_soup, seal_frozen_cohort_soup,
    weighted_average,
)
from bilqis_mlx.learning.capability_championship_state import validate_championship_state
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.factory_complete_solver import (
    factory_complete_solver, factory_evaluation_instruments,
)
from bilqis_mlx.semantics.domains import contract_digest

from bilqis_mlx.runtime.bamf_operator._championship_replay import _accepted_ancestor


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def _answer_identity(answer):
    return (answer.type_name, answer.state, answer.semantic_release,
            contract_digest(answer.value))


@dataclass(frozen=True)
class _Adviser:
    kind: str
    adviser_id: str
    weights: dict
    breadth: int
    capabilities: tuple[str, ...]
    soup_snapshot: dict | None = None


@dataclass(frozen=True)
class ChampionshipAdviserPool:
    accepted_manifest_sha256: str
    epoch_sha256: str
    parent: object
    source_context: object
    atlas_artifact_path: str
    direct: tuple[_Adviser, ...]
    soups: tuple[_Adviser, ...]
    eligible_roles: int
    cohort_count: int


def _cohort_definition(release, cohort_id, capabilities):
    return contract_digest({
        "schema": "bilqis.mlx.generated-cohort-definition/v1",
        "factory_release_sha256": release.release_sha256,
        "curriculum_sha256": release.execution_plan.curriculum_sha256,
        "cohort_id": cohort_id,
        "capabilities": tuple(capabilities),
    })


def _accepted_weights(run_dir, parent, cache, roles):
    by_sha, custody_by_sha = {}, {}
    for role in roles.values():
        sha256 = role["checkpoint"]["sha256"]
        if sha256 in by_sha:
            continue
        student, manifest_sha256 = _accepted_ancestor(
            run_dir, parent, cache, Checkpoint(**role["checkpoint"]))
        if (student.topology.digest != parent.topology.digest
                or student.extents.digest != parent.extents.digest):
            _invalid("BAMF_ADVISER_PARAMETER_GEOMETRY_DRIFT")
        graph_sha256 = dict(student.compiler_features).get(
            "factory_semantic_graph_sha256")
        if (not isinstance(graph_sha256, str)
                or len(graph_sha256) != SHA256_HEX_LENGTH):
            _invalid("BAMF_ADVISER_SOURCE_GRAPH_IDENTITY_INVALID")
        by_sha[sha256] = dict(student.retained_state.optimizer.parameters)
        custody_by_sha[sha256] = {
            "accepted_manifest_sha256": manifest_sha256,
            "source_graph_sha256": graph_sha256,
        }
    return by_sha, custody_by_sha


def _frozen_soups(run_dir, parent, release, state, weights_by_sha, custody_by_sha, *,
                  reserve_gib):
    epoch_sha256 = contract_digest(state["identity"])
    soups = []
    for cohort in release.execution_plan.grades:
        recipe = cohort_soup_recipe(
            state, cohort.grade_id, tuple(cohort.capabilities),
            championship_epoch_sha256=epoch_sha256,
            cohort_definition_sha256=_cohort_definition(
                release, cohort.grade_id, cohort.capabilities),
            factory_release_sha256=release.release_sha256)
        if recipe is None:
            continue
        for shard in partitioned_recipes(recipe, custody_by_sha):
            ingredients = tuple(
                (member["votes"], weights_by_sha[member["checkpoint"]["sha256"]])
                for member in shard["members"])
            trusted_frozen = weighted_average(mx, ingredients)
            snapshot = read_frozen_cohort_soup(
                run_dir, shard, expected_weights=trusted_frozen)
            if snapshot is None:
                snapshot = save_frozen_cohort_soup(
                    run_dir, shard, trusted_frozen, reserve_gib=reserve_gib)
                seal_frozen_cohort_soup(run_dir, snapshot)
            else:
                from bilqis_mlx.learning._championship.cohort_soup import (
                    verify_frozen_cohort_soup,
                )
                verify_frozen_cohort_soup(
                    run_dir, snapshot, expected_weights=trusted_frozen)
            soups.append(_Adviser(
                "SOUP", snapshot["recipe_sha256"], trusted_frozen,
                snapshot["vote_count"], tuple(snapshot["covered_capabilities"]),
                snapshot))
    return tuple(soups)


def prepare_championship_adviser_pool(
        run_dir: Path, parent, source_context, atlas_artifact_path: str, cache, *,
        reserve_gib: float) -> ChampionshipAdviserPool | None:
    """Load each native champion once and materialize immutable cohort soups."""
    state = getattr(parent, "championship_state", None)
    if state is None:
        return None
    state = dict(state)
    validate_championship_state(state)
    roles = state["active_roles"]
    if not roles:
        return None
    release = source_context.release
    if state["identity"]["factory_release_sha256"] != release.release_sha256:
        _invalid("BAMF_ADVISER_FACTORY_RELEASE_DRIFT")
    capability_map = release.execution_plan.capability_map
    if any(capability not in capability_map
           or role["capability_group"] != capability_map[capability].grade_id
           for capability, role in roles.items()):
        _invalid("BAMF_ADVISER_COHORT_IDENTITY_DRIFT")
    weights_by_sha, custody_by_sha = _accepted_weights(
        Path(run_dir), parent, cache, roles)
    role_counts = Counter(role["checkpoint"]["sha256"] for role in roles.values())
    role_caps = {}
    for capability, role in roles.items():
        role_caps.setdefault(role["checkpoint"]["sha256"], []).append(capability)
    direct = tuple(_Adviser(
        "DIRECT", sha256, weights_by_sha[sha256], role_counts[sha256],
        tuple(sorted(role_caps[sha256]))) for sha256 in sorted(role_counts))
    soups = _frozen_soups(
        Path(run_dir), parent, release, state, weights_by_sha, custody_by_sha,
        reserve_gib=reserve_gib)
    return ChampionshipAdviserPool(
        cache.accepted_manifest_sha256, contract_digest(state["identity"]),
        parent, source_context,
        str(atlas_artifact_path), direct, soups, len(roles),
        len(release.execution_plan.grades))


def _evaluate(adviser, pool, instruments):
    solver, generation = factory_complete_solver(
        pool.source_context, pool.parent, pool.atlas_artifact_path,
        instruments, parameters=adviser.weights)
    measured = solver.evaluate_cases(
        tuple(item.case.goal for item in instruments), generation)
    telemetry = solver.telemetry_for() if solver.telemetry_for is not None else {}
    launches = int(telemetry.get("shared_backbone_launches", 0)) + int(
        telemetry.get("scalar_neural_launches", 0))
    return tuple(_answer_identity(result.answer) == _answer_identity(item.case.gold)
                 for item, (result, _tools) in zip(instruments, measured, strict=True)), launches


def championship_mentor_supervision(
        pool: ChampionshipAdviserPool | None, rows, *, source_seed: int,
        teacher_strategy: dict) -> object | None:
    """Gold-gate frozen advisers and return bounded HOW-only row influence."""
    if pool is None:
        return None
    distill = teacher_strategy.get("distill", 0.0) if isinstance(teacher_strategy, dict) else None
    if type(distill) not in (int, float) or not math.isfinite(distill) or not 0 <= distill <= 1:
        _invalid("BAMF_ADVISER_DISTILL_INVALID")
    if distill == 0:
        return None
    rows = tuple(rows)
    instruments = factory_evaluation_instruments(
        pool.source_context, pool.parent, pool.atlas_artifact_path, rows,
        seed=source_seed, release_prevalidated=True)
    direct_results, soup_results, launches = [], [], 0
    for adviser in pool.direct:
        accepted, count = _evaluate(adviser, pool, instruments)
        launches += count
        direct_results.append((adviser, accepted))
    for adviser in pool.soups:
        accepted, count = _evaluate(adviser, pool, instruments)
        launches += count
        soup_results.append((adviser, accepted))
    capability_map = pool.source_context.release.execution_plan.capability_map
    influence_rows = []
    soup_total = 0.0
    for index, (row, instrument) in enumerate(zip(rows, instruments, strict=True)):
        target_cohort = capability_map[instrument.case.capability_id].grade_id
        direct_records, soup_records = [], []
        direct_votes, soup_votes, influence = 0, 0.0, 0.0
        for adviser, accepted in direct_results:
            correct = bool(accepted[index])
            eligible = instrument.case.capability_id in adviser.capabilities
            logical_votes = int(eligible)
            direct_records.append({
                "kind": "DIRECT", "adviser_id": adviser.adviser_id,
                "logical_votes": logical_votes,
                "accepted": bool(correct and eligible),
                "capabilities": list(adviser.capabilities),
            })
            if correct and eligible:
                direct_votes += logical_votes
                influence += (
                    MAX_INFLUENCE * float(distill)
                    * logical_votes / pool.eligible_roles)
        for adviser, accepted in soup_results:
            breadth = cohort_vote_count(
                adviser.soup_snapshot, target_cohort, pool.cohort_count)
            correct = bool(accepted[index])
            soup_records.append({
                "kind": "SOUP", "adviser_id": adviser.adviser_id,
                "cohort_id": adviser.soup_snapshot["cohort_id"],
                "logical_votes": breadth, "accepted": correct,
            })
            if correct:
                soup_votes += breadth
                influence += MAX_INFLUENCE * float(distill) * breadth / pool.eligible_roles
        influence = min(float(MAX_INFLUENCE), float(influence))
        soup_total += soup_votes
        source_row = dict(row)
        from bilqis_mlx.runtime.source_execution import source_content_digest
        influence_rows.append(MentorRowInfluence(
            source_row["id"], instrument.case.capability_id,
            source_content_digest((source_row,)), influence, direct_votes, soup_votes,
            tuple(direct_records), tuple(soup_records)))
    return issue_mentor_supervision(
        pool.accepted_manifest_sha256, pool.epoch_sha256, POLICY_ID,
        mentor_policy_binding(POLICY_ID, teacher_strategy),
        source_seed, tuple(influence_rows),
        physical_inference_launches=launches,
        logical_direct_votes=pool.eligible_roles,
        logical_soup_votes=soup_total)


__all__ = (
    "ChampionshipAdviserPool", "championship_mentor_supervision",
    "prepare_championship_adviser_pool",
)
