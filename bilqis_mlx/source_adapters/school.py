"""Admitted finite-world, Boolean and numeric source adapters and independent checks."""
from __future__ import annotations

import hashlib
import json

from ..curriculum import BOOLEAN_SIGNATURE_OPERAND_COUNT
from ..paths import source_path

from bilqis_mlx.errors import ErrorBus, SOURCE

from dataclasses import dataclass as _dataclass
from typing import Callable as _Callable
from ..grade_b_oracle import _direct_truth, evaluate as grade_b_gold, operand_truth
from ..live_grade_b import _u7c_pattern_counts

from ..factory.adapters import RegisteredSourceAdapter, SourceAdapterRegistry
from ..factory.autonomy import SupplementalEvidenceSpec
from ..factory.model import ProviderDimensionPolicy, SourceAdapter
from ..curriculum import BOOLEAN_OPERATORS
from ._school.numeric import check_numeric, semantic_footprint as numeric_semantic_footprint
from .structure import inspect_boolean_identification, inspect_source_query

from ..grade_a_oracle import VERSION as A_ORACLE


from ..live_grade_a import (GENERATOR as A_COHORT_GENERATOR, RELEASE as A_RELEASE,
                            generator_source_digest)
from .grade_a_presentation import (
    IRRELEVANT_CONTEXT_VARIATION as A_IRRELEVANT_CONTEXT_VARIATION,
    MEMBER_CONTEXT_VARIATION as A_MEMBER_CONTEXT_VARIATION,
    constructor_digest as a_provider_digest,
    draw_a,
)


from ..grade_b_oracle import CONNECTIVES, VERSION as B_ORACLE

from ..boolean_composite import (
    CAPABILITY as B_COMPOSITE_CAPABILITY,
    GENERATOR as B_COMPOSITE_GENERATOR,
    ORACLE as B_COMPOSITE_ORACLE,
    RELEASE as B_COMPOSITE_RELEASE,
    constructor_digest as b_composite_digest,
    draw_composite,
)

from ..boolean_identification import (
    CAPABILITY as B_IDBOOLOPS_CAPABILITY,
    GENERATOR as B_IDBOOLOPS_GENERATOR,
    ORACLE as B_IDBOOLOPS_ORACLE,
    RELEASE as B_IDBOOLOPS_RELEASE,
    constructor_digest as b_idboolops_digest,
    draw_identification,
)


from ..live_grade_b import (GENERATOR as B_COHORT_GENERATOR, RELEASE as B_RELEASE,
                            draw_connectives, constructor_digest as b_digest)


from ..live_grade_c import (GENERATOR as C_COHORT_GENERATOR, RELEASE as C_RELEASE,
                            PLANS, constructor_digest as c_digest,
                            provider_implementation_digest as c_provider_digest)


from ..numeric_curriculum import ORACLE as C_ORACLE, draw_numeric


from ..numeric_staircase import (
    FINAL_MAXIMUM as NUMERIC_FINAL_MAXIMUM,
    INITIAL_MAXIMUM as NUMERIC_INITIAL_MAXIMUM,
    RELEASE as STAIRCASE_RELEASE,
    constructor_digest as staircase_digest,
)

from ..boolean_association import (
    VERSION as BOOLEAN_ASSOCIATION_OPTION,
    draw_b_grade_bridges,
)


BOOLEAN_RUNTIME_SAMPLER = "bilqis.mlx.grade-b-u7c-runtime-sampler/v3"








from ._school.boolean import (
    check_predicate,
    check_connective,
    check_boolean_composite,
    semantic_footprint,
    draw_b,
    _boolean_profile_operators,
    draw_b_composite_release,
    check_b_composite_release,
    draw_b_idboolops_release,
    check_b_idboolops_release,
    classify_boolean_expression_weakness,
    enrich_boolean,
)

from ._school.numeric import (
    classify_numeric_weakness,
    draw_c,
    witness_numeric_obligation,
)

from ._school.evidence import (
    witness_micro_obligation,
    boolean_evidence_dependencies,
)

from ._school.fragile import (
    TRUTH_PATTERNS,
    _U7C_RUNTIME_SAMPLER,
    _DIRECT_BOOLEAN_UNIVERSE,
    _is_direct_u7c_row,
    _preservation_pattern_counts,
    _replay_operand_pattern,
    _operand_kind,
    structural_signature,
    classify_boolean_connective_weakness,
    _fragile_row_pattern,
    _fragile_eligible,
    _fragile_verify_row,
    _fragile_structural_capability,
    _fragile_matching_keys,
    _FragileSourcePolicy,
    _FRAGILE_SOURCE_POLICY,
    fragile_source_policy,
)


def _weakness_classifier_digest(*paths: str) -> str:
    """Seal classifier implementation independently from source generation."""
    payload = {
        path: hashlib.sha256(source_path(path).read_bytes()).hexdigest()
        for path in paths
    }
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _numeric_registered_adapter() -> RegisteredSourceAdapter:
    return RegisteredSourceAdapter(SourceAdapter(
        "source.finite-numeric/v2", "bilqis_mlx.numeric_curriculum.draw_numeric",
        (C_ORACLE,), c_provider_digest(), cohort_generator_id=C_COHORT_GENERATOR,
        variation_axes=("source-valid", "fresh-seed", "typed-answer",
                        "numeric-scope", "construction-shape"),
        profile_dimensions=(("numbers", tuple(str(i) for i in range(11))),),
        cohort_releases=((C_RELEASE, c_digest()),
                         (STAIRCASE_RELEASE, staircase_digest())),
        weakness_classifier_id="bilqis.weakness.finite-numeric/v1",
        weakness_classifier_sha256=_weakness_classifier_digest(
            "source_adapters/numeric.py")), draw_c, check_numeric,
        witness=witness_numeric_obligation,
        semantic_footprint=numeric_semantic_footprint,
        weakness_classifier=classify_numeric_weakness,
        dimension_policies=(ProviderDimensionPolicy(
            provider_id="source.finite-numeric/v2",
            dimension_id="numeric-root",
            parameter_name="numbers",
            progression_values=tuple(
                str(value) for value in range(
                    NUMERIC_INITIAL_MAXIMUM, NUMERIC_FINAL_MAXIMUM + 1)),
            selection_mode="CANONICAL_PREFIX",
            step_mode="ADJACENT",
            advance_trigger="DEVELOPMENTAL_BOUNDARY",
            terminal_value=str(NUMERIC_FINAL_MAXIMUM),
            source_constraint="SAME_PROVIDER_BINDING",
            admission_constraint="EXISTING_CAPABILITY_PROFILE",
            telemetry_projection="INTROOT",
            answer_family_kind="numeric_active",
            changes_source_projection=True,
            changes_assessment_scope=True,
            changes_answer_domain=True,
        ),))


def live_source_registry() -> SourceAdapterRegistry:
    from .c13_episode import registered_adapter as c13_episode_adapter
    from .copular import registered_adapter as copular_adapter
    from .event_frames import registered_adapter as event_adapter
    from .event_intro import registered_adapter as event_intro_adapter
    from .event_pairs import registered_adapter as event_pairs_adapter
    return SourceAdapterRegistry((
        RegisteredSourceAdapter(SourceAdapter(
            "source.micro.predicates/v1", "bilqis_mlx.grade_a_probe.make_record",
            (A_ORACLE,), a_provider_digest(),
            cohort_generator_id=A_COHORT_GENERATOR,
            variation_axes=("source-valid", "balanced-gold", "fresh-seed",
                            A_MEMBER_CONTEXT_VARIATION, A_IRRELEVANT_CONTEXT_VARIATION),
            cohort_releases=((A_RELEASE, a_provider_digest()),)), draw_a, check_predicate,
            semantic_footprint=semantic_footprint),
        RegisteredSourceAdapter(SourceAdapter(
            "source.micro.boolean-connectives/v1", "bilqis_mlx.live_grade_b.draw_connectives",
            (B_ORACLE,), b_digest(), cohort_generator_id=B_COHORT_GENERATOR,
            cohort_releases=((B_RELEASE, b_digest()),),
            teaching_option_ids=(BOOLEAN_ASSOCIATION_OPTION,),
            weakness_classifier_id="bilqis.weakness.boolean-connective/v1",
            weakness_classifier_sha256=_weakness_classifier_digest(
                "source_adapters/_school/fragile.py")), draw_b, check_connective,
            enrich_boolean, witness_micro_obligation,
            semantic_footprint=semantic_footprint,
            weakness_classifier=classify_boolean_connective_weakness),
        RegisteredSourceAdapter(SourceAdapter(
            "source.micro.boolean-composite/v1", B_COMPOSITE_GENERATOR,
            (B_ORACLE, B_COMPOSITE_ORACLE), b_composite_digest(),
            cohort_generator_id=B_COMPOSITE_GENERATOR,
            variation_axes=("source-valid", "fresh-seed", "operator-composition",
                            "runtime-answer-balance"),
            profile_dimensions=(("operators", BOOLEAN_OPERATORS),),
            cohort_releases=((B_COMPOSITE_RELEASE, b_composite_digest()),),
            weakness_classifier_id="bilqis.weakness.boolean-expression/v1",
            weakness_classifier_sha256=_weakness_classifier_digest(
                "source_adapters/_school/boolean.py",
                "source_adapters/structure.py")),
            draw_b_composite_release, check_b_composite_release,
            witness=witness_micro_obligation,
            dependencies=boolean_evidence_dependencies,
            semantic_footprint=semantic_footprint,
            weakness_classifier=classify_boolean_expression_weakness),
        RegisteredSourceAdapter(SourceAdapter(
            "source.micro.boolean-identification/v1", B_IDBOOLOPS_GENERATOR,
            (B_ORACLE, B_COMPOSITE_ORACLE, B_IDBOOLOPS_ORACLE), b_idboolops_digest(),
            cohort_generator_id=B_IDBOOLOPS_GENERATOR,
            variation_axes=("source-valid", "fresh-seed", "inverse-operator-identification",
                            "balanced-operator-targets", "masked-operator-input"),
            profile_dimensions=(("operators", BOOLEAN_OPERATORS),),
            cohort_releases=((B_IDBOOLOPS_RELEASE, b_idboolops_digest()),),
            weakness_classifier_id="bilqis.weakness.boolean-expression/v1",
            weakness_classifier_sha256=_weakness_classifier_digest(
                "source_adapters/_school/boolean.py",
                "source_adapters/structure.py")),
            draw_b_idboolops_release, check_b_idboolops_release,
            witness=witness_micro_obligation,
            dependencies=boolean_evidence_dependencies,
            semantic_footprint=semantic_footprint,
            weakness_classifier=classify_boolean_expression_weakness),
        _numeric_registered_adapter(),
        copular_adapter(),
        event_adapter(),
        event_intro_adapter(),
        event_pairs_adapter(),
        c13_episode_adapter(),
    ))


# Public callable identities remain stable across the physical owner split.
for _public_callable in (
        check_predicate, check_connective, check_boolean_composite,
        semantic_footprint, draw_b, draw_b_composite_release,
        check_b_composite_release, draw_b_idboolops_release,
        check_b_idboolops_release, enrich_boolean, draw_c,
        witness_numeric_obligation, witness_micro_obligation,
        boolean_evidence_dependencies, structural_signature,
        fragile_source_policy):
    _public_callable.__module__ = __name__
del _public_callable
