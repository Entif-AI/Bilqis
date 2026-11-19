"""Independent capability-local assessment evidence for championship authority."""
import time

from bilqis_mlx.factory.assessment import AssessmentScopeContract
from bilqis_mlx.generated_assessment import make_cohort
from bilqis_mlx.runtime.capability_retention import (
    EvaluationCohort, EvidenceKind, case_census_digest, evaluate_capabilities,
)
from bilqis_mlx.runtime.factory_complete_solver import factory_complete_solver
from bilqis_mlx.semantics.domains import contract_digest

from .._factory_retention_support import _instruments


def _observe(observer, **fields):
    if observer is None:
        return
    try:
        observer(fields)
    except Exception:
        pass


def championship_capability_seed(cache, release, capability_id: str, contract) -> int:
    digest = contract_digest({
        "schema": "bilqis.mlx.capability-championship-panel-seed/v1",
        "run_id": cache.run_id,
        "factory_release_sha256": release.release_sha256,
        "semantic_catalog_sha256": release.semantic_catalog_sha256,
        "capability_id": capability_id,
        "rubric_sha256": contract.rubric_sha256,
        "source_sha256": contract.source_sha256,
    })
    return int(digest[:16], 16)


def capability_championship_instruments(
        source_context, candidate_bundle, artifact_path, cache, capability_id):
    """Draw one stable assessment-only target panel, never the complete school."""
    release = source_context.release
    execution = source_context.execution_for(capability_id)
    projection = source_context.assessment_projection_for(capability_id)
    verification = source_context.verification_for(capability_id)
    source_sha256 = contract_digest({
        "schema": "bilqis.mlx.assessment-scope-source/v2",
        "capabilities": (capability_id,),
        "source_projections": ((capability_id, projection.source),),
        "verified_receipts": ((capability_id, verification.digest()),),
    })
    contract = AssessmentScopeContract(
        capabilities=(capability_id,),
        rubric_sha256=contract_digest({
            "schema": "bilqis.mlx.assessment-scope-rubric/v2",
            "capabilities": (capability_id,),
            "assessment_projections": ((capability_id, projection.assessment),),
        }),
        source_sha256=source_sha256,
        factory_release_sha256=release.release_sha256,
        semantic_catalog_sha256=release.semantic_catalog_sha256,
        generator_version=source_sha256,
    )
    seed = championship_capability_seed(cache, release, capability_id, contract)
    rows = source_context.draw_rows(seed=seed, capability=capability_id)
    raw = make_cohort(
        rows, generator_version=contract.generator_version, seed=seed,
        rubric_version=contract.rubric_sha256)
    instruments = _instruments(
        source_context, candidate_bundle, artifact_path, raw.rows,
        seed=seed, each=len(raw.rows), release_prevalidated=True)
    return instruments, contract


def capability_championship_evidence(
        source_context, candidate_bundle, artifact_path, cache, capability_id,
        training, evidence_stage, *, observer=None):
    started = time.perf_counter()
    instruments, contract = capability_championship_instruments(
        source_context, candidate_bundle, artifact_path, cache, capability_id)
    _observe(
        observer,
        championship_prepare_wall_seconds=max(
            0.0, time.perf_counter() - started))
    cases = tuple(item.case for item in instruments)
    execution = source_context.execution_for(capability_id)
    policy_sha256 = contract_digest({
        "schema": "bilqis.mlx.capability-championship-policy/v1",
        "minimum_percent_exclusive": 90,
        "incumbent_defense": "STRICTLY_HIGHER",
        "tie_winner": "CHALLENGER",
    })
    cohort = EvaluationCohort(
        EvidenceKind.FRESH_TARGET, cases,
        ((capability_id, execution.grade_id),),
        contract.rubric_sha256,
        contract_digest({
            "schema": "bilqis.mlx.capability-championship-scope/v1",
            "capability_id": capability_id,
            "factory_release_sha256": contract.factory_release_sha256,
            "semantic_catalog_sha256": contract.semantic_catalog_sha256,
        }),
        contract.source_sha256, policy_sha256,
        tuple(training[0]), tuple(training[1]), case_census_digest(cases),
        evidence_stage=evidence_stage)
    started = time.perf_counter()
    solver, generation = factory_complete_solver(
        source_context, candidate_bundle, artifact_path, instruments)
    _observe(
        observer,
        championship_solver_wall_seconds=max(
            0.0, time.perf_counter() - started))
    started = time.perf_counter()
    assessment = evaluate_capabilities(solver, cohort, generation)
    _observe(
        observer,
        championship_candidate_wall_seconds=max(
            0.0, time.perf_counter() - started))
    if observer is not None:
        try:
            telemetry_for = getattr(solver, "telemetry_for", None)
            telemetry = telemetry_for() if callable(telemetry_for) else {}
            observer({
                "championship_case_count": len(cases),
                "championship_shared_backbone_launches": int(
                    telemetry.get("shared_backbone_launches", 0) or 0),
                "championship_scalar_neural_launches": int(
                    telemetry.get("scalar_neural_launches", 0) or 0),
            })
        except Exception:
            pass
    return cohort, assessment


__all__ = (
    "capability_championship_evidence", "capability_championship_instruments",
    "championship_capability_seed",
)
