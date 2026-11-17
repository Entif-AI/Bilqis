"""C07 must seal the exact R06 championship reset it authorizes."""
from dataclasses import fields, replace
from pathlib import Path
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.capability_championship_state import (
    championship_epoch_identity, clear_championship_epoch,
    compact_championship_state,
)
from bilqis_mlx.runtime.bamf_bundle import BamfBundleCandidate, CompleteStudent
from bilqis_mlx.runtime.bamf_bundle.atlas_admission import (
    ATLAS_ADMISSION_SCHEMA_V4, AtlasAdmissionBinding,
    _issue_atlas_admission_binding, require_atlas_admission_binding,
    validate_parsed_atlas_championship_state,
)
from bilqis_mlx.runtime.bamf_bundle.genesis import BamfRunIdentity
from bilqis_mlx.runtime.bamf_bundle.publication import _authorize_publication_candidate
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import candidate, parent_state


def _parent_and_candidate():
    identity = BamfRunIdentity(
        "fixture-run", 17, "1" * 64, "bundles/foundation-origin", 0,
        "2" * 64, "3" * 64, "4" * 64, "5" * 64, "6" * 64,
        "7" * 64, "fixture-source", "8" * 64, "fixture-teacher", 0)
    base = candidate(parent_state())
    values = {item.name: getattr(base, item.name) for item in fields(BamfBundleCandidate)}
    values["run_identity"] = identity
    parent = CompleteStudent(**values)
    epoch_identity = championship_epoch_identity(
        factory_release_sha256="1" * 64, semantic_catalog_sha256="2" * 64,
        curriculum_sha256="3" * 64,
        capability_groups=(("future:capability", "future:group"),),
        fixed_cohort_sha256="4" * 64, rubric_sha256="5" * 64,
        scope_sha256="6" * 64, source_sha256="7" * 64,
        policy_sha256="8" * 64, topology_sha256=parent.topology.digest,
        extents_sha256=parent.extents.digest, semantic_abi=parent.semantic_abi)
    live = compact_championship_state({
        "active_roles": {},
        "settled_matchups": {
            "future:capability|" + "9" * 64 + "|" + "a" * 64: {
                "capability": "future:capability", "winner_sha256": "9" * 64,
            },
        },
    }, epoch_identity)
    parent = replace(parent, championship_state=live)
    staged = replace(
        base, generation=1, parent_manifest_sha256="a" * 64,
        transition={
            "schema": "bilqis.mlx.bamf-generation-transition/v1",
            "kind": "PARAMETER_EXTENSION", "invalidate_derived_caches": True,
        },
        run_identity=identity,
        championship_state=clear_championship_epoch(
            live, source_manifest_sha256="a" * 64,
            source_generation=parent.generation),
    )
    return parent, staged, live


def _binding(parent, staged):
    return _issue_atlas_admission_binding(
        staged, parent, lease_sha256="9" * 64,
        source_approval_sha256="8" * 64, proposal_sha256="7" * 64,
        factory_release_sha256="6" * 64, staging_receipt_sha256="5" * 64,
        parent_feature_receipt_sha256="4" * 64)


class AtlasChampionshipAdmissionTests(unittest.TestCase):
    def test_v4_roundtrip_seals_championship_reset_digest(self):
        parent, staged, _live = _parent_and_candidate()
        binding = _binding(parent, staged)
        self.assertEqual(binding.schema_version, ATLAS_ADMISSION_SCHEMA_V4)
        historical = AtlasAdmissionBinding.from_record(binding.to_record())
        self.assertEqual(historical.championship_state_sha256,
                         binding.championship_state_sha256)
        self.assertEqual(historical.digest, binding.digest)

    def test_live_binding_rejects_replaced_valid_championship_sidecar(self):
        parent, staged, live = _parent_and_candidate()
        binding = _binding(parent, staged)
        forged = replace(
            staged,
            championship_state=clear_championship_epoch(
                live, source_manifest_sha256="b" * 64,
                source_generation=parent.generation))
        with self.assertRaises(BilqisError):
            require_atlas_admission_binding(forged, binding)
        with self.assertRaises(BilqisError):
            _authorize_publication_candidate(Path("/unused"), forged, binding)

    def test_cold_v4_binding_rejects_replaced_valid_championship_sidecar(self):
        parent, staged, live = _parent_and_candidate()
        parsed = AtlasAdmissionBinding.from_record(_binding(parent, staged).to_record())
        forged = CompleteStudent(**replace(
            staged,
            championship_state=clear_championship_epoch(
                live, source_manifest_sha256="b" * 64,
                source_generation=parent.generation)).__dict__)
        with self.assertRaises(BilqisError):
            validate_parsed_atlas_championship_state(forged, parsed)
