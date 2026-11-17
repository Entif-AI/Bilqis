"""Typed factory error contracts."""
from __future__ import annotations

from .base import _spec

class FACTORY:
    class PROFILE_EXPANSION:
        INVALID = _spec(
            ("FACTORY", "PROFILE_EXPANSION", "INVALID"),
            owner="factory.profile_expansion",
            title="Factory profile expansion invalid",
            message_template="Factory profile expansion invalid: {reason}",
            disposition="CORRECT_INPUT_OR_STATE",
            next_action=(
                "Preserve the accepted Factory release and correct the requested "
                "profile or its source and semantic authorities before retrying."),
        )

    class WEAKNESS:
        INVALID = _spec(
            ("FACTORY", "WEAKNESS", "INVALID"),
            owner="factory.weakness",
            title="Factory structural weakness contract invalid",
            message_template="Factory structural weakness contract invalid: {reason}",
            disposition="CORRECT_INPUT_OR_STATE",
            next_action=(
                "Restore the provider-declared weakness classifier, exact source "
                "context, and fresh-equivalent construction contract before retrying."),
        )

    class SOURCE_ADAPTER:
        COMPATIBILITY_INVALID = _spec(
            ("FACTORY", "SOURCE_ADAPTER", "COMPATIBILITY_INVALID"),
            owner="compatibility.source_adapter_resume",
            title="Factory source-adapter compatibility invalid",
            message_template="Factory source-adapter compatibility invalid: {reason}",
            disposition="PRESERVE_AND_REPAIR",
            next_action=(
                "Preserve the accepted release and repair the exact source-adapter "
                "identity or registry boundary before retrying."),
        )

    class DEVELOPMENTAL_PROGRAM:
        INVALID = _spec(
            ("FACTORY", "DEVELOPMENTAL_PROGRAM", "INVALID"),
            owner="factory.curriculum.developmental_program",
            title="Factory developmental program invalid",
            message_template="Factory developmental program invalid: {reason}",
            disposition="CORRECT_INPUT_OR_STATE",
            next_action=(
                "Restore the immutable C14 developmental-program manifest and "
                "source-qualified domain declarations before retrying."),
        )

    class SOURCE_BINDING:
        INVALID = _spec(
            ("FACTORY", "SOURCE_BINDING", "INVALID"),
            owner="factory.curriculum_definition",
            title="Factory source binding invalid",
            message_template="Factory source binding invalid: {reason}",
            disposition="CORRECT_INPUT_OR_STATE",
            next_action=(
                "Restore the canonical capability/source binding and reserved "
                "namespace ownership before retrying."),
        )

    class SEMANTIC_RULE:
        INVALID = _spec(
            ("FACTORY", "SEMANTIC_RULE", "INVALID"),
            owner="factory.curriculum.rule_registry",
            title="Factory semantic rule contract invalid",
            message_template="Factory semantic rule contract invalid: {reason}",
            disposition="CORRECT_INPUT_OR_STATE",
            next_action=(
                "Restore the canonical semantic rule identity, source authority, "
                "and registry binding before retrying."),
        )

    class ADMISSION:
        COMPLETE_PRIOR_EXAM_REQUIRED = _spec(
            ('FACTORY', 'ADMISSION', 'COMPLETE_PRIOR_EXAM_REQUIRED'), owner='compatibility.grade_transition',
            title='Grade admission requires complete perfect cumulative exam', message_template='Grade admission requires complete perfect cumulative exam',
            disposition="CORRECT_INPUT_OR_STATE",
            next_action="Inspect the owning contract and inputs; preserve recorded state.",
            legacy_codes=('GRADE_ADMISSION_REQUIRES_COMPLETE_PERFECT_CUMULATIVE_EXAM',),
        )

    class RELEASE:
        MANIFEST_CONTENT_DRIFT = _spec(
            ("FACTORY", "RELEASE", "MANIFEST_CONTENT_DRIFT"),
            owner="runtime.admission",
            title="Sealed factory release content does not match its wire identity",
            message_template=(
                "Factory release {release_sha256} does not match the canonical "
                "payload or embedded course identity that minted it."),
            disposition="PRESERVE_AND_REPAIR",
            next_action=(
                "Preserve the artifact. Decode it with the schema version that "
                "minted it; restore the original bytes if that verification fails."),
            self_heal_owner="compatibility.legacy.factory_release_v1",
            legacy_codes=("FACTORY_RELEASE_MANIFEST_CONTENT_DRIFT",),
        )

    class EXECUTION:
        CURRICULUM_DEFINITION_REQUIRED = _spec(
            ('FACTORY', 'EXECUTION', 'CURRICULUM_DEFINITION_REQUIRED'), owner='factory.curriculum_definition',
            title='Factory curriculum definition required', message_template='Factory curriculum definition required',
            disposition="CORRECT_INPUT_OR_STATE",
            next_action="Inspect the owning contract and inputs; preserve recorded state.",
            legacy_codes=('FACTORY_CURRICULUM_DEFINITION_REQUIRED',),
        )
        CURRICULUM_UNKNOWN_CAPABILITY = _spec(
            ('FACTORY', 'EXECUTION', 'CURRICULUM_UNKNOWN_CAPABILITY'), owner='factory.curriculum_definition',
            title='Factory curriculum unknown capability', message_template='Factory curriculum unknown capability',
            disposition="CORRECT_INPUT_OR_STATE",
            next_action="Inspect the owning contract and inputs; preserve recorded state.",
            legacy_codes=('FACTORY_CURRICULUM_UNKNOWN_CAPABILITY',),
        )
        ASSESSMENT_SOURCE_CONTEXT_REQUIRED = _spec(
            ('FACTORY', 'EXECUTION', 'ASSESSMENT_SOURCE_CONTEXT_REQUIRED'), owner='runtime.assessment',
            title='Factory assessment source context required', message_template='Factory assessment source context required',
            disposition="CORRECT_INPUT_OR_STATE",
            next_action="Inspect the owning contract and inputs; preserve recorded state.",
            legacy_codes=('FACTORY_ASSESSMENT_SOURCE_CONTEXT_REQUIRED',),
        )
        EXECUTABLE_PROFILE_TRANSITION_UNSUPPORTED = _spec(
            ('FACTORY', 'EXECUTION', 'EXECUTABLE_PROFILE_TRANSITION_UNSUPPORTED'), owner='runtime.release_adoption',
            title='Factory executable profile transition unsupported', message_template='Factory executable profile transition unsupported',
            disposition="CORRECT_INPUT_OR_STATE",
            next_action="Inspect the owning contract and inputs; preserve recorded state.",
            legacy_codes=('FACTORY_EXECUTABLE_PROFILE_TRANSITION_UNSUPPORTED',),
        )
        EXPECTED_A_SOURCEADAPTERREGISTRY = _spec(
            ('FACTORY', 'EXECUTION', 'EXPECTED_A_SOURCEADAPTERREGISTRY'), owner='runtime.source_execution',
            title='Expected a sourceadapterregistry', message_template='Expected a sourceadapterregistry',
            disposition="CORRECT_INPUT_OR_STATE",
            next_action="Inspect the owning contract and inputs; preserve recorded state.",
            legacy_codes=('Expected a SourceAdapterRegistry',),
        )
        EXPECTED_AN_ANSWERMODALITYREGISTRY = _spec(
            ('FACTORY', 'EXECUTION', 'EXPECTED_AN_ANSWERMODALITYREGISTRY'), owner='runtime.source_execution',
            title='Expected an answermodalityregistry', message_template='Expected an answermodalityregistry',
            disposition="CORRECT_INPUT_OR_STATE",
            next_action="Inspect the owning contract and inputs; preserve recorded state.",
            legacy_codes=('Expected an AnswerModalityRegistry',),
        )
        EXPECTED_AN_EXECUTABLEFACTORYRELEASE = _spec(
            ('FACTORY', 'EXECUTION', 'EXPECTED_AN_EXECUTABLEFACTORYRELEASE'), owner='runtime.source_execution',
            title='Expected an executablefactoryrelease', message_template='Expected an executablefactoryrelease',
            disposition="CORRECT_INPUT_OR_STATE",
            next_action="Inspect the owning contract and inputs; preserve recorded state.",
            legacy_codes=('Expected an ExecutableFactoryRelease',),
        )
        EXECUTABLE_GENERATION_UNKNOWN_CAPABILITY = _spec(
            ('FACTORY', 'EXECUTION', 'EXECUTABLE_GENERATION_UNKNOWN_CAPABILITY'), owner='runtime.source_execution',
            title='Factory executable generation unknown capability', message_template='Factory executable generation unknown capability',
            disposition="CORRECT_INPUT_OR_STATE",
            next_action="Inspect the owning contract and inputs; preserve recorded state.",
            legacy_codes=('FACTORY_EXECUTABLE_GENERATION_UNKNOWN_CAPABILITY',),
        )
