"""Typed, neural-inert contracts for the mandatory curriculum factory.

This compatibility facade preserves the established public import path while the
cohesive contracts, release verification, and evidence records live in dedicated
internal modules.
"""
from __future__ import annotations

from ._model import (
    AdmissionReceipt, AssessmentClass, AssessmentPlan, CapabilityDefinition,
    ConstructionProgram, CoveragePlan, FactoryRelease, GradeDefinition,
    LearningEvidence, SemanticRelease, SourceAdapter, TeachingOption,
    assessment_plans,
)

# Preserve the historical public type identity for pickle/debug/introspection
# compatibility even though implementation now lives in cohesive submodules.
for _record in (
    AdmissionReceipt, AssessmentClass, AssessmentPlan, CapabilityDefinition,
    ConstructionProgram, CoveragePlan, FactoryRelease, GradeDefinition,
    LearningEvidence, SemanticRelease, SourceAdapter, TeachingOption,
):
    _record.__module__ = __name__

assessment_plans.__module__ = __name__

del _record

__all__ = [
    "AdmissionReceipt", "AssessmentClass", "AssessmentPlan",
    "CapabilityDefinition", "ConstructionProgram", "CoveragePlan",
    "FactoryRelease", "GradeDefinition", "LearningEvidence",
    "SemanticRelease", "SourceAdapter", "TeachingOption",
    "assessment_plans",
]
