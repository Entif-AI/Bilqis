"""Typed, neural-inert contracts for the mandatory curriculum factory.

This module preserves the historical public import surface while cohesive
contracts live in focused implementation modules.
"""
from .model_assessment import (
    AdmissionReceipt,
    AssessmentPlan,
    LearningEvidence,
    assessment_plans,
)
from .model_contracts import (
    AssessmentClass,
    CapabilityDefinition,
    ConstructionProgram,
    CoveragePlan,
    GradeDefinition,
    SemanticRelease,
    SourceAdapter,
    TeachingOption,
)
from .model_release import FactoryRelease

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
