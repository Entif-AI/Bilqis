"""Factory-only acceptance binds one exact inert child and owner event."""
from dataclasses import fields, replace
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
    FACTORY_RELEASE_ADMISSION_SCHEMA_V2,
    FACTORY_RELEASE_ADMISSION_SCHEMA_V3,
    FactoryReleaseAdmissionBinding,
    ParsedFactoryReleaseAdmissionBinding,
    _issue_factory_release_admission_binding,
    require_factory_release_admission_binding,
    validate_parsed_factory_release_admission_binding,
)
from bilqis_mlx.runtime.bamf_bundle.factory_release_adoption import (
    FACTORY_RELEASE_ADOPTION_EVENT,
    FACTORY_RELEASE_ADOPTION_EVENT_SCHEMA,
    _issue_factory_release_adoption_transition,
    derive_factory_release_adoption_candidate,
)
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
from bilqis_mlx.runtime.bamf_bundle.publication import (
    publish_factory_release_adoption_generation,
)
from bilqis_mlx.runtime.bamf_bundle.records import (
    BamfBundleCandidate,
    CompleteStudent,
    canonical,
    sha,
    sidecar_records,
)
from bilqis_mlx.runtime.tests.admission.atlas.adoption.atlas_adoption_executor_support import (
    AtlasAdoptionExecutorFixture,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.acceptance._generation_acceptance_support import (
    GenerationAcceptanceFixture,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch


PUBLIC_BINDING_FIELDS = frozenset({
    "run_id",
    "generation",
    "candidate_identity_sha256",
    "parent_candidate_identity_sha256",
    "feature_sha256",
    "optimizer_step",
    "lease_sha256",
    "source_approval_sha256",
    "handoff_sha256",
    "proposal_sha256",
    "selection_receipt_sha256",
    "predecessor_factory_release_sha256",
    "factory_release_sha256",
    "transition_sha256",
    "adoption_event_sha256",
    "schema_version",
})
OWNER_EVENT_FIELDS = frozenset({
    "event",
    "schema",
    "run_id",
    "generation",
    "optimizer_step",
    "predecessor_factory_release_sha256",
    "factory_release_sha256",
    "handoff_sha256",
    "proposal_sha256",
    "selection_receipt_sha256",
    "lease_sha256",
    "source_approval_sha256",
    "transition_sha256",
})



class FactoryReleaseAdmissionBindingSupport(unittest.TestCase):
    @staticmethod
    def _transition():
        return _issue_factory_release_adoption_transition(
            predecessor_factory_release_sha256="1" * 64,
            factory_release_sha256="2" * 64,
            handoff_sha256="3" * 64,
            proposal_sha256="4" * 64,
            staged_candidate_sha256="5" * 64,
            selection_receipt_sha256="6" * 64,
            lease_sha256="7" * 64,
            source_approval_sha256="8" * 64,
        )

    @staticmethod
    def _historical_student(candidate):
        records = sidecar_records(candidate)
        values = {
            item.name: getattr(candidate, item.name)
            for item in fields(BamfBundleCandidate)
        }
        values["outbox"] = tuple(records["outbox"])
        return CompleteStudent(**values)

    def setUp(self):
        helper = object.__new__(AtlasAdoptionExecutorFixture)
        self.parent, _unused = AtlasAdoptionExecutorFixture._native_parent_and_candidate(
            helper
        )
        self.transition = self._transition()
        self.candidate = derive_factory_release_adoption_candidate(
            self.parent,
            parent_manifest_sha256="a" * 64,
            transition=self.transition,
        )
        self.binding = _issue_factory_release_admission_binding(
            self.candidate,
            self.parent,
            transition=self.transition,
        )

    def _parsed(self):
        return FactoryReleaseAdmissionBinding.from_record(self.binding.to_record())

    def _parsed_with(self, **changes):
        record = self.binding.to_record()
        for name, value in changes.items():
            record[name] = value
        public = {name: record[name] for name in PUBLIC_BINDING_FIELDS}
        record["binding_sha256"] = sha(canonical(public))
        return FactoryReleaseAdmissionBinding.from_record(record)


__all__ = [
    "FactoryReleaseAdmissionBindingSupport", "GenerationAcceptanceFixture",
    "PUBLIC_BINDING_FIELDS", "OWNER_EVENT_FIELDS",
    "FACTORY_RELEASE_ADMISSION_SCHEMA_V2", "FACTORY_RELEASE_ADMISSION_SCHEMA_V3",
    "FACTORY_RELEASE_ADOPTION_EVENT", "FACTORY_RELEASE_ADOPTION_EVENT_SCHEMA",
    "FactoryReleaseAdmissionBinding", "ParsedFactoryReleaseAdmissionBinding",
    "_issue_factory_release_admission_binding",
    "require_factory_release_admission_binding",
    "validate_parsed_factory_release_admission_binding",
    "_issue_factory_release_adoption_transition",
    "derive_factory_release_adoption_candidate",
    "publish_factory_release_adoption_generation",
    "load_bamf_generation_authority", "replace", "BilqisError", "sha", "canonical",
    "shape_patch", "patch", "mlx_checkpoint",
]
