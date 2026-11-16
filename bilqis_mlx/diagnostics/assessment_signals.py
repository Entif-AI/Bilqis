"""S1/S2 from actually scored candidate answers on a source-bound cohort."""
from __future__ import annotations

from collections import Counter

from bilqis_mlx.semantics.domains import contract_digest

from .signals import DiagnosticStatus, LearningSignal


def _identity(answer):
    return (answer.type_name, answer.state.value,
            answer.semantic_release, contract_digest(answer.value))


def assessment_prediction_signals(assessment, capability_id: str) -> tuple[dict, dict]:
    """Use actual evaluated gold and predictions; no synthetic majority baseline."""
    rows = tuple(
        (case, result) for case, result in zip(
            assessment.cohort.cases, assessment.results, strict=True)
        if case.capability_id == capability_id)
    gold = Counter(_identity(case.gold) for case, _ in rows)
    predictions = Counter(_identity(result.answer) for _, result in rows)
    mixed = len(gold) > 1
    correct = sum(_identity(case.gold) == _identity(result.answer)
                  for case, result in rows)
    total = len(rows)
    constant = total > 1 and len(predictions) == 1
    s1 = {
        "signal": LearningSignal.REPETITIVE_ANSWERS.value,
        "status": (DiagnosticStatus.NOT_MEASURED.value if not mixed
                   else DiagnosticStatus.OBSERVED_IN_COHORT.value if constant
                   else DiagnosticStatus.NOT_OBSERVED.value),
        "note": ("Both source-attested gold classes required" if not mixed
                 else "Constant answer on varied gold" if constant
                 else "Predictions vary across the source cohort"),
        "evidence_count": total if mixed else 0,
    }
    s2 = {
        "signal": LearningSignal.CHANCE_LEVEL_OR_LAGGING.value,
        "status": (DiagnosticStatus.NOT_MEASURED.value if not mixed
                   else DiagnosticStatus.OBSERVED_IN_COHORT.value
                   if correct <= max(gold.values())
                   else DiagnosticStatus.NOT_OBSERVED.value),
        "note": ("Capability-conditioned majority baseline unavailable"
                 if not mixed else
                 "At or below source gold majority baseline"
                 if correct <= max(gold.values())
                 else "Above source gold majority baseline"),
        "evidence_count": total if mixed else 0,
    }
    return s1, s2


def optional_prediction_signals(observer, assessment, capability_id):
    """Diagnostics cannot make an otherwise valid retention screen fail."""
    if observer is None:
        return ()
    try:
        return assessment_prediction_signals(assessment, capability_id)
    except Exception:
        return ()
