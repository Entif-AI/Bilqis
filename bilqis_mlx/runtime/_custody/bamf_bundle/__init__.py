"""Versioned BAMF generation bundle custody."""
from importlib import import_module
from types import MappingProxyType

from .codec import load_bamf_bundle, save_bamf_bundle
from .feature_authority import (
    AcceptedGenerationFeatureContext, AcceptedGenerationFeatureReceipt,
    AuthenticatedCandidateFeatureContext, AuthenticatedGenerationFeatureContext,
    authenticate_bamf_execution_feature_context,
    authenticate_bamf_generation_feature_context,
    authenticate_bamf_candidate_feature_context, authenticate_bamf_candidate_features,
    feature_schema_from_compiler_features,
    read_accepted_generation_feature_context,
    read_accepted_generation_feature_lineage, read_accepted_generation_feature_receipt,
    verify_accepted_generation_feature_receipt,
)
from .publication import (
    AcceptedGenerationInspection, inspect_accepted_generation,
    load_bamf_generation, load_bamf_generation_authority,
    publish_atlas_admission_generation, publish_bamf_generation,
    record_bamf_rejection,
)
from .vocabulary.admission_records import (
    A02StagedVocabularyExtension, A02VocabularyStagingReceipt,
    require_issued_a02_staged_vocabulary_extension,
)
from .package_import_transition import PackageImportTransition
from .motif.source_continuation import (
    SourceQualifiedMotifContinuation,
    continue_source_qualified_motifs_from_bundle,
    seal_source_qualified_motif_batch_from_bundle,
    seal_source_qualified_motifs_from_bundle,
    stage_source_qualified_motif_allocation,
)
from .records import (
    BAMF_BUNDLE_SCHEMA, BAMF_POINTER_SCHEMA, BamfBundleCandidate,
    BamfGenerationManifest, CompleteStudent,
)

_LAZY_EXPORTS = MappingProxyType({
    "BamfRunIdentity": ".genesis",
    "InitialGenerationBinding": ".genesis",
    "PreparedInitialGeneration": ".genesis",
    "prepare_initial_generation": ".genesis",
    "publish_initial_generation": ".genesis",
    "recover_prepared_initial_generation": ".genesis",
    "recover_sealed_initial_generation": ".genesis",
    "InitialFoundationFeatureAuthority": ".genesis.foundation",
    "issue_initial_foundation_feature_authority": ".genesis.foundation",
    "InitialFactoryFoundationAuthority": ".genesis.origin",
    "issue_initial_factory_foundation_authority": ".genesis.origin",
    "stage_vocabulary_extension": ".vocabulary.admission",
    "stage_vocabulary_extension_from_source_id": ".vocabulary.admission",
    "require_staged_vocabulary_admission_headroom": ".vocabulary.admission",
    "AcceptedVocabularyRegistryExport": ".vocabulary.registry_export",
    "read_accepted_vocabulary_registry_export": ".vocabulary.registry_export",
})


def __getattr__(name: str):
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(name)
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value


__all__ = (
    "BAMF_BUNDLE_SCHEMA", "BAMF_POINTER_SCHEMA", "BamfBundleCandidate",
    "BamfGenerationManifest", "CompleteStudent", "save_bamf_bundle", "load_bamf_bundle",
    "continue_source_qualified_motifs_from_bundle",
    "seal_source_qualified_motif_batch_from_bundle",
    "seal_source_qualified_motifs_from_bundle",
    "stage_source_qualified_motif_allocation",
    "SourceQualifiedMotifContinuation",
    "publish_bamf_generation", "load_bamf_generation",
    "publish_atlas_admission_generation",
    "AcceptedGenerationInspection", "inspect_accepted_generation",
    "load_bamf_generation_authority", "record_bamf_rejection",
    "A02StagedVocabularyExtension", "A02VocabularyStagingReceipt",
    "require_issued_a02_staged_vocabulary_extension", "stage_vocabulary_extension",
    "stage_vocabulary_extension_from_source_id",
    "require_staged_vocabulary_admission_headroom",
    "AcceptedVocabularyRegistryExport", "read_accepted_vocabulary_registry_export",
    "PackageImportTransition",
    "AcceptedGenerationFeatureContext", "AcceptedGenerationFeatureReceipt",
    "AuthenticatedCandidateFeatureContext", "AuthenticatedGenerationFeatureContext",
    "authenticate_bamf_candidate_feature_context", "read_accepted_generation_feature_lineage",
    "authenticate_bamf_execution_feature_context",
    "authenticate_bamf_generation_feature_context",
    "read_accepted_generation_feature_context", "feature_schema_from_compiler_features",
    "read_accepted_generation_feature_receipt",
    "authenticate_bamf_candidate_features",
    "verify_accepted_generation_feature_receipt",
    "BamfRunIdentity", "InitialGenerationBinding", "PreparedInitialGeneration",
    "InitialFactoryFoundationAuthority", "issue_initial_factory_foundation_authority",
    "InitialFoundationFeatureAuthority", "issue_initial_foundation_feature_authority",
    "recover_prepared_initial_generation", "recover_sealed_initial_generation",
    "prepare_initial_generation", "publish_initial_generation",
)
