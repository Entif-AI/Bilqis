"""FactoryRelease v2: one immutable executable curriculum authority.

The historical :class:`FactoryRelease` remains the byte-stable v1 compatibility
artifact while current callers migrate.  This module is the target release
contract: canonical curriculum, source bindings, execution profile, compiled
plan, provider/modality implementation identity and source-verified release
specimens are hashed together.  Runtime cutover is deliberately separate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json

from ..curriculum import AnswerFamily
from .adapters import SourceAdapterRegistry
from .answers import (
    AnswerModality, AnswerModalityRegistry, compile_answer_heads,
)
from .curriculum_definition import (
    CapabilitySourceBinding, CapabilitySpec, CurriculumDefinition, GradeSpec,
    SourceBindingSet, validate_curriculum_definition, validate_source_bindings,
)
from .execution import (
    CapabilityExecution, CapabilityProfile, CapabilityProjectionDigests,
    CurriculumDelta, CurriculumProfile, ExecutionPlan, GradeExecution,
    GradeProfile, PlanLineage, ProjectionDigests, SemanticGeometryChange,
    compile_execution_plan, diff_execution_plans,
)
from .generation import draw_execution_rows
from .model import ProviderDimensionPolicy, SourceAdapter


SCHEMA = "bilqis.mlx.factory-release/v2"


def _source_adapter_record(item: SourceAdapter) -> dict:
    """Preserve historical v2 bytes while sealing declared R13 classifier metadata."""
    record = asdict(item)
    if item.weakness_classifier_id is None:
        record.pop("weakness_classifier_id")
        record.pop("weakness_classifier_sha256")
    return record


from ._executable_release.primitives import (
    _ReleaseError,
    _require,
    _digest,
    _require_sha256,
    _tuples,
    AnswerHeadBinding,
    CapabilityVerificationReceipt,
    VerifiedAssessmentSeal,
    ExecutableVerificationReceipt,
    ExecutableAdmissionReceipt,
)
from ._executable_release.release import (
    ExecutableFactoryRelease,
)
from ._executable_release.verification import (
    _verify_release_structure,
    _verify_release_providers,
    _verify_release_answers,
    _verify_release_evidence,
    _verify_release_assessments,
    _verify_release_lineage,
)
from ._executable_release.decode import (
    _decode_curriculum,
    _decode_source_bindings,
    _decode_profile,
    _decode_plan,
    _decode_verification,
)
from ._executable_release.evidence import (
    _provider_descriptors,
    _answer_head_bindings,
    _verification_receipt,
)
from ._executable_release.compile import (
    compile_executable_factory_release,
)
from ._executable_release.operations import (
    compile_successor_profile_release,
    admit_executable_factory_release,
    answer_heads_from_executable_release,
    _prepare_predecessor_transition,
)

# Resolve the receipt method’s forward annotation after both classes exist.
from ._executable_release import primitives as _primitives
_primitives.ExecutableFactoryRelease = ExecutableFactoryRelease
del _primitives

# Preserve public identities for introspection and pickling.
from types import FunctionType as _FunctionType

for _public_object in (
    _ReleaseError,
    _require,
    _digest,
    _require_sha256,
    _tuples,
    AnswerHeadBinding,
    CapabilityVerificationReceipt,
    VerifiedAssessmentSeal,
    ExecutableVerificationReceipt,
    ExecutableAdmissionReceipt,
    ExecutableFactoryRelease,
    _verify_release_structure,
    _verify_release_providers,
    _verify_release_answers,
    _verify_release_evidence,
    _verify_release_assessments,
    _verify_release_lineage,
    _decode_curriculum,
    _decode_source_bindings,
    _decode_profile,
    _decode_plan,
    _decode_verification,
    _provider_descriptors,
    _answer_head_bindings,
    _verification_receipt,
    compile_executable_factory_release,
    compile_successor_profile_release,
    admit_executable_factory_release,
    answer_heads_from_executable_release,
    _prepare_predecessor_transition,
):
    _public_object.__module__ = __name__
    if isinstance(_public_object, type):
        for _member in vars(_public_object).values():
            if isinstance(_member, (classmethod, staticmethod)):
                _member = _member.__func__
            if isinstance(_member, _FunctionType):
                _member.__module__ = __name__
del _public_object, _member, _FunctionType
