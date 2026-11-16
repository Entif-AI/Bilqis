"""Read-only BAMF observation projection; source counts never imply learning.

This versioned reader validates receipt structure, not producer qualification.
Real producer integration remains with C11.1 and its source/custody owners.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Mapping

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.mission_control.consumers import (
    decode_operator_view as decode_mission_control_operator_view,
    terminal_status as render_mission_control_operator_status,
)
from bilqis_mlx.mission_control.snapshots import OperatorView as MissionControlOperatorView
from .atlas_evidence import OperatorEvidence, compact_debt, parse_evidence, render_evidence

SCHEMA = "bilqis.bamf.operator-status/v1"
_BINDINGS = ("source_release_sha256", "model_sha256", "evaluator_sha256",
             "rights_sha256", "coverage_census_sha256")
_COVERAGE = ("source_eligible", "source_held", "implementation_uncovered", "ready",
             "staged", "admitted", "exposed", "qualified")
_COUNTS = ("active_concepts", "active_banks", "memory_used_bytes", "memory_budget_bytes")
_FRACTIONS = ("fallback_fraction", "expansion_fraction", "motif_hit_fraction")
_OBSERVATIONS = (*_COUNTS, *_FRACTIONS, "atoms_per_frame", "plasticity_mode")


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.BAMF_OPERATOR.INVALID, reason=reason)


def _count(value):
    return type(value) is int and value >= 0


@dataclass(frozen=True)
class AtlasOperatorView:
    """Detached immutable copy of one source/model/evaluator-bound observation."""

    bindings: tuple[tuple[str, str], ...]
    coverage: tuple[tuple[str, int], ...]
    observations: tuple[tuple[str, object], ...]
    evidence: OperatorEvidence = OperatorEvidence()


def bamf_status(receipt: Mapping) -> AtlasOperatorView | MissionControlOperatorView:
    """Validate and copy an external observation before replacing any live view."""
    if isinstance(receipt, Mapping) and "schema_version" in receipt:
        return decode_mission_control_operator_view(receipt)
    if not isinstance(receipt, Mapping) or receipt.get("schema") != SCHEMA:
        _invalid("schema")
    bindings = []
    for key in _BINDINGS:
        value = receipt.get(key)
        if (not isinstance(value, str) or len(value) != 64 or
                any(ch not in "0123456789abcdef" for ch in value)):
            _invalid(key)
        bindings.append((key, value))
    coverage = receipt.get("coverage")
    if (not isinstance(coverage, Mapping) or set(coverage) != set(_COVERAGE) or
            any(not _count(coverage.get(key)) for key in _COVERAGE)):
        _invalid("coverage counts")
    if sum(coverage[key] for key in _COVERAGE[2:]) != coverage["source_eligible"]:
        _invalid("coverage census partition")
    observations = receipt.get("observations", {})
    if not isinstance(observations, Mapping) or set(observations) - set(_OBSERVATIONS):
        _invalid("observations")
    for key, value in observations.items():
        if value is None:
            continue
        if key in _COUNTS and not _count(value):
            _invalid(key)
        if key in (*_FRACTIONS, "atoms_per_frame"):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                _invalid(key)
            if key in _FRACTIONS and value > 1:
                _invalid(key)
        if key == "plasticity_mode" and value not in ("FAST", "FULL", "FROZEN"):
            _invalid(key)
    active = observations.get("active_concepts")
    if active is not None and active > coverage["source_eligible"]:
        _invalid("active concepts outside source census")
    return AtlasOperatorView(tuple(bindings), tuple((key, coverage[key]) for key in _COVERAGE),
                             tuple((key, observations.get(key)) for key in _OBSERVATIONS),
                             parse_evidence(receipt.get("evidence")))


def render_panel(view: AtlasOperatorView | MissionControlOperatorView, state: Mapping,
                 *, expanded=False, width=100):
    """Reuse existing telemetry's GREW and retention counters without scoring."""
    if type(view) is MissionControlOperatorView:
        lines = render_mission_control_operator_status(view)
        return tuple(line if width is None else line[:width] for line in lines)
    coverage, observed = dict(view.coverage), dict(view.observations)
    def measured(key):
        value = observed.get(key)
        return "NOT MEASURED" if value is None else str(value)
    grew = state.get("grew")
    growth = f"{grew:+d}" if type(grew) is int else "NOT MEASURED"
    retained = state.get("retained_steps")
    retained = str(retained) if _count(retained) else "NOT MEASURED"
    debt = compact_debt(view.evidence)
    transfer = ("observed (details)" if view.evidence.learned_transfer is not None
                and view.evidence.learned_transfer.total else "NOT MEASURED")
    lines = [
        (f"ATLAS grade-neutral | eligible {coverage['source_eligible']} | "
         f"source-held {coverage['source_held']} | uncovered {coverage['implementation_uncovered']} | "
         f"ready {coverage['ready']} | staged {coverage['staged']} | "
         f"active {measured('active_concepts')} | banks {measured('active_banks')}"),
        (f"LEARNING | GREW {growth} | retained steps {retained} | {debt} | "
         f"perfect mastery NOT MEASURED | transfer {transfer}"),
    ]
    if expanded:
        lines.append("ATLAS complete snapshot: --once --atlas-details")
        def fraction(key):
            value = observed.get(key)
            return "NOT MEASURED" if value is None else f"{value:.1%}"
        used, budget = observed.get("memory_used_bytes"), observed.get("memory_budget_bytes")
        memory = "NOT MEASURED" if used is None or budget is None else f"{used}/{budget} bytes"
        lines.extend([
            (f"ATLAS STATUS | admitted {coverage['admitted']} | exposed {coverage['exposed']} | "
             f"qualified {coverage['qualified']} | atoms/frame {measured('atoms_per_frame')}"),
            (f"ATLAS WORK | fallback {fraction('fallback_fraction')} | "
             f"expansion {fraction('expansion_fraction')} | motif hits {fraction('motif_hit_fraction')} | "
             f"plasticity {measured('plasticity_mode')} | memory {memory}"),
        ])
        labels = ("source", "model", "rubric", "rights", "census")
        lines.extend(f"ATLAS {label} {digest}" for label, (_, digest) in zip(labels, view.bindings))
        lines.extend(render_evidence(view.evidence))
    return tuple(line[:width] for line in lines)
