"""Production-shaped, neural-inert support for the BAMF operator journey."""
from __future__ import annotations

from contextlib import ExitStack
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from bilqis_mlx.compatibility.executable_projection import (
    LIVE_V2_VERIFICATION_SEED, project_legacy_course,
)
from bilqis_mlx.compatibility.live_releases import (
    boolean_composite_successor, boolean_identification_successor,
    boolean_successor, initial_course, numeric_successor,
)
from bilqis_mlx.factory.adapters import SourceAdapterRegistry
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.live_answers import live_answer_registry
from bilqis_mlx.grade_a_release import accepted_grade_a
from bilqis_mlx.live_grade_c import REGISTRY_COUNTING_TARGET, registry_graph
from bilqis_mlx.runtime.atlas_source_authority import SourceAuthorityRegistry
from bilqis_mlx.runtime.bamf_bundle._darwin_salience_signer import (
    HostSourceAuthoritySigner,
)
from bilqis_mlx.runtime.model_topology_v2 import (
    Initializer, ParameterGroup, ParameterSpec,
)
from bilqis_mlx.runtime.tests.admission.atlas.test_atlas_admission import (
    _REGISTRY as ATLAS_REGISTRY,
)
from bilqis_mlx.runtime.tests.admission.atlas.v2.mixed_witness_support import (
    MixedWitnessSupport,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle import helpers as custody_helpers
from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import (
    selection_teacher,
)
from bilqis_mlx.runtime.tests.teacher.priority.test_priority_signer import (
    _registry as priority_registry,
)
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.atlas_features import FeatureSchema, build_feature_manifest
from bilqis_mlx.semantics.tests.frame_adapters.helpers import (
    _snapshot as accepted_abi_snapshot,
)
from bilqis_mlx.factory.tests.sources.test_skos_curriculum import (
    _snapshot as source_atlas_snapshot,
)
from bilqis_mlx.source_adapters.copular_curriculum import SENSE_ID, atlas_semantic_id
from bilqis_mlx.source_adapters.school import live_source_registry


ROOT = Path(__file__).resolve().parents[4]
LEGACY = ROOT / "vendor" / "legacy-v16"
MANIFEST = ROOT / "docs/provenance/GRADE_A_CANDIDATE_MANIFEST_V2.json"
COPULAR_REGISTRY = ROOT / "bilqis_mlx/semantics/copular_registry_v1.json"
AUTHORIZED_ATLAS = (
    "5f8fba20ecc0adebf39c3b663fdffa4f766e780915197f09d116713042a479e7",
    "58e0c281b5da18b9b7e6c803709b29eeeb0a88f16b06f48de692808e2fb88306",
    "f1c89c1d1bcd72695c81f8e777d0fbbdf446e92cb27132bebf1cd6873ec689ec",
)
COMBINED_REGISTRY = SourceAuthorityRegistry(tuple(sorted(
    (*ATLAS_REGISTRY.keys, *priority_registry().keys),
    key=lambda key: key.owner_id,
)))


def _historical_implementations():
    return {
        "source.micro.predicates/v1":
            "c451c3e6bf5ab538450c691d504230036b9a729ddfc67b53163c6a1f106d62a9",
        "source.micro.boolean-identification/v1":
            "6399dae052a289d46063df0e897e14f1392e2f1b99e90c2ae791fda9a8246743",
        "source.finite-numeric/v2":
            "2758cf678e9d2a45f3f5a1b5edd85d5ae513e54506c0d98853b9402b91572754",
    }


def _teacher_authority():
    return {
        "schema": "bilqis.bamf.legacy-trainer-authority/v1",
        "version": "1.0.0",
        "source_branch": "fixture",
        "source_worktree": "/fixture",
        "source_run": "/fixture/run",
        "source_state": "/fixture/run/state.json",
    }


def historical_school_release():
    """Compile current A/B/C behavior under the exact sealed predecessor providers."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    grade_a = initial_course(accepted_grade_a(manifest))
    course = boolean_successor(grade_a, LEGACY)
    course = boolean_composite_successor(course, LEGACY)
    course = boolean_identification_successor(course, LEGACY)
    course, _ = numeric_successor(course, maximum=REGISTRY_COUNTING_TARGET)
    answers = live_answer_registry()
    curriculum, bindings, profile, _ = project_legacy_course(
        course, grade_a, LEGACY, answer_kinds=answers.kinds)
    current_registry = live_source_registry()
    current = compile_executable_factory_release(
        curriculum, bindings, profile, current_registry, answers,
        source_root=LEGACY, graph=registry_graph(),
        verification_seed=LIVE_V2_VERIFICATION_SEED)
    adapters = []
    for descriptor in current.source_adapters:
        sealed = _historical_implementations()[descriptor.adapter_id]
        registered = current_registry.resolve_owner(descriptor.generator_id)
        cohorts = registered.descriptor.cohort_releases
        if descriptor.adapter_id != "source.finite-numeric/v2":
            cohorts = ((cohorts[0][0], sealed),)
        adapters.append(replace(
            registered,
            descriptor=replace(
                registered.descriptor,
                implementation_sha256=sealed,
                cohort_releases=cohorts,
            ),
        ))
    return compile_executable_factory_release(
        curriculum, bindings, profile, SourceAdapterRegistry(tuple(adapters)),
        answers, source_root=LEGACY, graph=registry_graph(),
        verification_seed=LIVE_V2_VERIFICATION_SEED), registry_graph()


def portable_atlas_snapshot():
    """Mount the accepted native ABI plus one source-backed copular candidate."""
    base = accepted_abi_snapshot()
    source = source_atlas_snapshot(((
        atlas_semantic_id(), ("lexicon", "lexicon_root_senses", SENSE_ID), None),))
    index = len(base.abi_entries)
    entry = replace(source.abi_entries[0], index=index, row=index)
    concept = replace(source.concepts[0], abi_index=index, abi_row=index)
    counts = replace(
        base.counts, source_rows=1, rdf_terms=1, semantic_concepts=1,
        abi_entries=index + 1, implementation_uncovered=1)
    prior = hashlib.sha256(COPULAR_REGISTRY.read_bytes()).hexdigest()
    return replace(
        base,
        bundle_id=AUTHORIZED_ATLAS[0],
        release_sha256=AUTHORIZED_ATLAS[1],
        source_bundle_id=AUTHORIZED_ATLAS[2],
        prior_abi_sha256=prior,
        counts=counts,
        abi_entries=(*base.abi_entries, entry),
        concepts=(concept,),
        semantic_lookup=tuple(sorted(
            (*base.semantic_lookup, (entry.semantic_id, index)))),
        concept_lookup=((concept.concept.semantic_id, 0),),
    )


def wide_shape_patch(row_count: int):
    declared = (ParameterSpec(
        custody_helpers.NAME, (row_count, 2), Initializer.EMBEDDING,
        ParameterGroup.IDENTITY_ROW_AGE, True),)
    stack = ExitStack()
    stack.enter_context(patch.object(custody_helpers, "DECLARED", declared))
    stack.enter_context(custody_helpers.shape_patch())
    return stack


class PreNeuralJourneySupport(MixedWitnessSupport):
    @staticmethod
    def host_registry():
        return patch(
            "bilqis_mlx.runtime.bamf_bundle.source_authority_custody."
            "read_host_system_source_authority_registry",
            return_value=COMBINED_REGISTRY,
        )

    def journey_mounts(self, snapshot, schema, features, selection):
        stack = ExitStack()
        stack.enter_context(self.source_replay(snapshot, schema, features))
        for target in (
            "bilqis_mlx.semantics.atlas.snapshot.load_pinned_atlas_snapshot",
            "bilqis_mlx.factory.skos_curriculum.load_pinned_atlas_snapshot",
            "bilqis_mlx.semantics.released_frame_schemas.load_pinned_atlas_snapshot",
            "bilqis_mlx.source_adapters.atoms.admission.load_pinned_atlas_snapshot",
            "bilqis_mlx.source_adapters.atom_binding.load_pinned_atlas_snapshot",
        ):
            stack.enter_context(patch(target, return_value=snapshot))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.atlas_flywheel_runtime."
            "resolve_atlas_artifact_selection",
            return_value=selection))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.foundation_teacher_owner.live_authority",
            return_value=(_teacher_authority(), "d" * 40,
                          {"teacher": selection_teacher()})))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_bundle._darwin_salience_signer."
            "read_host_system_source_authority_signer",
            side_effect=lambda registry: HostSourceAuthoritySigner(
                "owner:c06", "44" * 32, registry)))
        return stack


def journey_source(snapshot):
    schema = FeatureSchema((), ())
    return (
        schema,
        build_feature_manifest(snapshot, schema),
        AtlasArtifactSelection("/artifact", *AUTHORIZED_ATLAS),
    )
