"""Neural-inert execution of one autonomous learner-evidence obligation."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from ..generated_assessment import make_cohort, score
from .adapters import SourceAdapterRegistry
from .autonomy import EvidenceKind, EvidenceObligation, EvidenceReceipt
from .generation import draw_release_rows, draw_executable_release_rows
from .model import FactoryRelease


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class EvidenceSourceDraw:
    """Exact source-generation coordinates for one qualified evidence row."""

    row_id: str
    source_seed: int
    source_each: int


def _draw_evidence_batch(source_root, graph, release: FactoryRelease,
                         registry: SourceAdapterRegistry,
                         obligation: EvidenceObligation, *, seed: int,
                         max_rounds: int = 8):
    """Return qualified rows together with their exact source draw coordinates."""
    release.verify()
    if not isinstance(registry, SourceAdapterRegistry):
        raise TypeError("FACTORY_EVIDENCE_REGISTRY_REQUIRED")
    if not isinstance(obligation, EvidenceObligation):
        raise TypeError("FACTORY_EVIDENCE_OBLIGATION_REQUIRED")
    legacy = isinstance(release, FactoryRelease)
    capability_map = (release.course.capability_map if legacy else
                      release.execution_plan.capability_map)
    if obligation.capability_id not in capability_map:
        raise ValueError("FACTORY_EVIDENCE_UNKNOWN_CAPABILITY")
    if type(seed) is not int or type(max_rounds) is not int or max_rounds < 1:
        raise ValueError("FACTORY_EVIDENCE_DRAW_ARGUMENT_INVALID")

    target = obligation.minimum_specimens
    each = target if obligation.kind is EvidenceKind.DIRECT else max(8, target * 4)
    found: dict[str, tuple[dict, EvidenceSourceDraw]] = {}
    for round_index in range(max_rounds):
        source_seed = seed + round_index
        rows = (draw_release_rows if legacy else draw_executable_release_rows)(
            source_root, graph, release, registry,
            seed=source_seed,
            capability=obligation.capability_id,
            each=each,
        )
        for row in rows:
            if registry.obligation_witness(
                    release.course if legacy else release.curriculum,
                    capability=obligation.capability_id,
                    row=row, obligation=obligation,
                    source_root=source_root, graph=graph,
                    release=None if legacy else release):
                found[row["id"]] = (
                    row,
                    EvidenceSourceDraw(row["id"], source_seed, each),
                )
                if len(found) >= target:
                    selected = tuple(found[key] for key in sorted(found)[:target])
                    return (
                        tuple(item[0] for item in selected),
                        tuple(item[1] for item in selected),
                    )
    raise ValueError(
        "FACTORY_EVIDENCE_WITNESS_EXHAUSTED:" + obligation.obligation_id)


def draw_evidence_rows(source_root, graph, release: FactoryRelease,
                       registry: SourceAdapterRegistry,
                       obligation: EvidenceObligation, *, seed: int,
                       max_rounds: int = 8) -> tuple[dict, ...]:
    """Materialize fresh source-checked rows that actually witness obligation."""
    rows, _source_draws = _draw_evidence_batch(
        source_root, graph, release, registry, obligation,
        seed=seed, max_rounds=max_rounds)
    return rows


def measure_evidence(source_root, graph, release: FactoryRelease,
                     registry: SourceAdapterRegistry,
                     obligation: EvidenceObligation, *,
                     checkpoint: dict, seed: int, predictor=None,
                     source_bound_predictor=None) -> EvidenceReceipt:
    """Score one intact checkpoint on a fresh obligation-specific cohort."""
    if ((predictor is None) == (source_bound_predictor is None)
            or (predictor is not None and not callable(predictor))
            or (source_bound_predictor is not None
                and not callable(source_bound_predictor))):
        raise TypeError("FACTORY_EVIDENCE_PREDICTOR_REQUIRED")
    rows, source_draws = _draw_evidence_batch(
        source_root, graph, release, registry, obligation, seed=seed)
    legacy = isinstance(release, FactoryRelease)
    generator = (release.course.capability_map[obligation.capability_id].lesson_generator
                 if legacy else release.source_bindings.by_capability[
                     obligation.capability_id].generator_id)
    cohort = make_cohort(
        rows,
        generator_version=generator,
        seed=seed,
        rubric_version=(
            release.release_sha256 + "/" + obligation.obligation_id),
    )
    predictions = (
        source_bound_predictor(tuple(rows), source_draws)
        if source_bound_predictor is not None
        else predictor(tuple(rows)))
    measured = score(cohort, predictions, checkpoint)
    evidence_id = _digest({
        "factory_release_sha256": release.release_sha256,
        "obligation_id": obligation.obligation_id,
        "cohort_sha256": cohort.digest,
        "checkpoint_sha256": checkpoint.get("sha256"),
        "optimizer_step": checkpoint.get("optimizer_step"),
        "predictions": sorted(predictions.items())
        if isinstance(predictions, dict) else None,
    })
    return EvidenceReceipt(
        obligation_id=obligation.obligation_id,
        evidence_id=evidence_id,
        checkpoint_sha256=checkpoint["sha256"],
        optimizer_step=checkpoint["optimizer_step"],
        cohort_sha256=cohort.digest,
        specimen_count=len(rows),
        passed=bool(measured["perfect_on_sample"]),
    )
