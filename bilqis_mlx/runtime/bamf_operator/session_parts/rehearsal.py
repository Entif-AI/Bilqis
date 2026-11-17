"""Authority-bounded R14 rehearsal planning for native BAMF lessons."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from bilqis_mlx.factory._model.weakness import WeaknessClassId, classify_weakness
from bilqis_mlx.runtime.factory_retention_owner import require_current_retention_plan
from bilqis_mlx.runtime.priority_rejection_replay import current_structural_weaknesses
from bilqis_mlx.semantics.domains import contract_digest


@dataclass(frozen=True)
class RehearsalPlan:
    target_capability_id: str
    target_grade_id: str
    prior_capability_ids: tuple[str, ...]
    retention_support_capability_ids: tuple[str, ...]
    weakness_records: tuple[dict, ...]
    protection_plan_sha256: str
    active_grade_definition_sha256: str
    active_grade_activation_sha256: str
    identity: str


@dataclass(frozen=True)
class RehearsalRows:
    prior: tuple[dict, ...] = ()
    preservation: tuple[dict, ...] = ()
    retention_support: tuple[dict, ...] = ()
    bindings: tuple[dict, ...] = ()
    authorities: tuple[tuple[str, object], ...] = ()

    @property
    def by_id(self) -> dict[str, str]:
        return {
            **{row["id"]: "prior" for row in self.prior},
            **{row["id"]: "preservation" for row in self.preservation},
            **{row["id"]: "retention_support" for row in self.retention_support},
        }

    @property
    def bindings_by_id(self) -> dict[str, dict]:
        return {item["row_id"]: item for item in self.bindings}

    @property
    def authorities_by_id(self) -> dict[str, object]:
        return dict(self.authorities)


def _seed(plan: RehearsalPlan, role: str, capability: str, ordinal: int) -> int:
    digest = hashlib.sha256(
        f"{plan.identity}|{role}|{capability}|{ordinal}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def compile_rehearsal_plan(run_dir, parent, cache, source_context, selection) -> RehearsalPlan:
    """Compile WHAT to rehearse from R05/R13 authority without choosing curriculum."""
    capability = selection.offer.capability_id
    protection, target = require_current_retention_plan(
        cache, source_context.release, capability)
    execution = source_context.release.execution_plan.capability_map[capability]
    if target.target_grade_id != execution.grade_id:
        raise ValueError("BAMF_REHEARSAL_GRADE_AUTHORITY_DRIFT")
    from bilqis_mlx.runtime.active_generated_grade import read_active_generated_grade
    active = read_active_generated_grade(Path(run_dir), repair=False)
    if capability not in active.member_capability_ids:
        raise ValueError("BAMF_REHEARSAL_TARGET_OUTSIDE_ACTIVE_GRADE")
    from bilqis_mlx.runtime.retention.protection_plan import ProtectionReason
    prior_reasons = {ProtectionReason.PREREQUISITE, ProtectionReason.CONSTITUENT}
    prior = tuple(sorted({
        edge.capability_id for edge in target.affected_edges
        if edge.reason in prior_reasons
        and edge.capability_id in set(target.protected_capability_ids)
    }))
    support = tuple(
        item for item in target.protected_capability_ids if item not in set(prior))
    weaknesses = current_structural_weaknesses(
        run_dir, parent, cache, source_context, selection, capability)
    weakness_records = tuple(item["weakness"] for item in weaknesses)
    payload = {
        "schema": "bilqis.bamf.rehearsal-plan/v1",
        "target_capability_id": capability,
        "target_grade_id": target.target_grade_id,
        "prior_capability_ids": prior,
        "retention_support_capability_ids": support,
        "weakness_evidence_sha256": tuple(
            item["weakness_evidence_sha256"] for item in weakness_records),
        "protection_plan_sha256": protection.digest,
        "active_grade_definition_sha256": active.definition.definition_sha256,
        "active_grade_activation_sha256": active.activation_sha256,
    }
    return RehearsalPlan(
        capability, target.target_grade_id, prior, support, weakness_records,
        protection.digest, active.definition.definition_sha256,
        active.activation_sha256, contract_digest(payload))


def _binding(source_context, row, authority, *, role, capability, seed, each):
    execution = source_context.execution_for(capability)
    family = row.get("source_family_id")
    if not isinstance(family, str) or not family:
        family = contract_digest({
            "schema": "bilqis.mlx.source-draw-family/v1",
            "provider": execution.provider_id,
            "implementation": execution.provider_implementation_sha256,
            "capability": capability,
        })
    episode = row.get("episode_id")
    if not isinstance(episode, str) or not episode:
        episode = row["id"]
    if (authority.capability_id != capability or authority.seed != seed
            or authority.each != each or authority.source_family_id != family):
        raise ValueError("BAMF_REHEARSAL_SOURCE_AUTHORITY_DRIFT")
    return {
        "row_id": row["id"], "role": role, "capability": capability,
        "seed": seed, "each": each, "source_family_id": family,
        "episode_id": episode,
    }


def _draw_one(source_context, plan, role, capability, ordinal):
    seed = _seed(plan, role, capability, ordinal)
    rows, authority = source_context.draw_bound_rows(
        seed=seed, capability=capability, each=1)
    rows = tuple(rows)
    if len(rows) != 1 or rows[0].get("capability") != capability:
        raise ValueError("BAMF_REHEARSAL_SOURCE_DRAW_INVALID")
    return rows[0], _binding(
        source_context, rows[0], authority, role=role, capability=capability,
        seed=seed, each=1), authority


def materialize_rehearsal_rows(source_context, plan: RehearsalPlan, ordinal: int) -> RehearsalRows:
    """Materialize fresh rows for an already-compiled plan; never expand its scope."""
    prior_pairs = tuple(_draw_one(source_context, plan, "prior", cap, ordinal)
                        for cap in plan.prior_capability_ids)
    support_pairs = tuple(_draw_one(source_context, plan, "retention_support", cap, ordinal)
                          for cap in plan.retention_support_capability_ids)
    prior = tuple(row for row, _binding_record, _authority in prior_pairs)
    support = tuple(row for row, _binding_record, _authority in support_pairs)
    bindings = [record for _row, record, _authority in (*prior_pairs, *support_pairs)]
    authorities = [(row["id"], authority)
                   for row, _record, authority in (*prior_pairs, *support_pairs)]
    preservation = []
    if plan.weakness_records:
        from bilqis_mlx.runtime.structural_weakness_capture import _provider_for_context
        execution, adapter, admitted = _provider_for_context(
            source_context, plan.target_capability_id)
        for record in plan.weakness_records:
            weakness = WeaknessClassId.from_record(record["weakness_class"])
            match = match_authority = match_seed = None
            for attempt in range(16):
                seed = _seed(
                    plan, "preservation", weakness.class_sha256,
                    ordinal * 16 + attempt)
                candidates, authority = source_context.draw_bound_rows(
                    seed=seed, capability=plan.target_capability_id, each=1)
                row = tuple(candidates)[0]
                classified = classify_weakness(
                    adapter, execution, row, provider_descriptor=admitted)
                if classified is not None and classified.class_sha256 == weakness.class_sha256:
                    match, match_authority, match_seed = row, authority, seed
                    break
            if match is None or match_authority is None or match_seed is None:
                raise ValueError("BAMF_REHEARSAL_WEAKNESS_SPECIMEN_UNAVAILABLE")
            preservation.append(match)
            bindings.append(_binding(
                source_context, match, match_authority, role="preservation",
                capability=plan.target_capability_id, seed=match_seed, each=1))
            authorities.append((match["id"], match_authority))
    rows = RehearsalRows(
        prior, tuple(preservation), support, tuple(bindings), tuple(authorities))
    ids = [row["id"] for row in (*rows.prior, *rows.preservation, *rows.retention_support)]
    if len(ids) != len(set(ids)):
        raise ValueError("BAMF_REHEARSAL_ROW_ID_COLLISION")
    if set(ids) != set(rows.bindings_by_id):
        raise ValueError("BAMF_REHEARSAL_BINDING_COVERAGE_INVALID")
    if set(ids) != set(rows.authorities_by_id):
        raise ValueError("BAMF_REHEARSAL_AUTHORITY_COVERAGE_INVALID")
    return rows


__all__ = (
    "RehearsalPlan", "RehearsalRows", "compile_rehearsal_plan",
    "materialize_rehearsal_rows",
)
