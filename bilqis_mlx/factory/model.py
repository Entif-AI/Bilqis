"""Typed, neural-inert contracts for the mandatory curriculum factory.

This module preserves the historical public import surface while cohesive
contracts live in focused implementation modules.
"""
from ._model.assessment import (
    AdmissionReceipt,
    AssessmentPlan,
    LearningEvidence,
    assessment_plans,
)
from ._model.contracts import (
    AssessmentClass,
    CapabilityDefinition,
    ConstructionProgram,
    CoveragePlan,
    GradeDefinition,
    SemanticRelease,
    SourceAdapter,
    TeachingOption,
)
from ._model.release import FactoryRelease

__all__ = (
    "AdmissionReceipt",
    "AssessmentClass",
    "AssessmentPlan",
    "CapabilityDefinition",
    "ConstructionProgram",
    "CoveragePlan",
    "FactoryRelease",
    "GradeDefinition",
    "LearningEvidence",
    "SemanticRelease",
    "SourceAdapter",
    "TeachingOption",
    "assessment_plans",
)
