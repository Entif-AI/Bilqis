"""Production-shaped, neural-inert support for the BAMF operator journey."""
from __future__ import annotations

from contextlib import ExitStack
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

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
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.grade_a_release import accepted_grade_a
from bilqis_mlx.live_grade_c import REGISTRY_COUNTING_TARGET, registry_graph
from bilqis_mlx.runtime.accepted_priority_visit import accepted_priority_school
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.runtime.bamf_operator.session import _execution_context
from bilqis_mlx.runtime.foundation_teacher_owner import select_foundation_priority_visit
from bilqis_mlx.runtime.atlas_source_authority import (
    SourceAuthorityKey, SourceAuthorityRegistry, SourceAuthorityScope,
)
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
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.atlas_projection import (
    _canonical_bytes as _atlas_bytes, _digest as _atlas_sha256,
)
from bilqis_mlx.semantics.atlas_features import FeatureSchema, build_feature_manifest
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind
from bilqis_mlx.semantics.frame_adapters import (
    BOOLEAN_CONNECTIVE_ADAPTER, FINITE_NUMERIC_ADAPTER, MICRO_PREDICATE_ADAPTER,
)
from bilqis_mlx.semantics.released_frame_schemas import (
    _load_pinned_released_frame_schemas,
)
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


def _priority_registry():
    key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("44" * 32))
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
    scopes = tuple(sorted((SourceAuthorityScope(kind, prefix) for kind, prefix in (
        (DependencyKind.POLICY, "salience-policy:"),
        (DependencyKind.SOURCE, "salience-fact:"),
        (DependencyKind.ARTIFACT, "salience-option:"),
        (DependencyKind.ARTIFACT, "salience-event:"),
    )), key=lambda scope: (scope.kind.value, scope.key_prefix)))
    return SourceAuthorityRegistry((SourceAuthorityKey("owner:c06", public, scopes),))


COMBINED_REGISTRY = SourceAuthorityRegistry(tuple(sorted(
    (*ATLAS_REGISTRY.keys, *_priority_registry().keys),
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
    entries = (*base.abi_entries, entry)
    active_indices = [item.index for item in entries if item.active]
    return replace(
        base,
        bundle_id=AUTHORIZED_ATLAS[0],
        release_sha256=AUTHORIZED_ATLAS[1],
        source_bundle_id=AUTHORIZED_ATLAS[2],
        prior_abi_sha256=prior,
        active_set_sha256=_atlas_sha256(_atlas_bytes(active_indices)),
        counts=counts,
        abi_entries=entries,
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
        stack = ExitStack()
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_bundle.source_authority_custody."
            "read_host_system_source_authority_registry",
            return_value=COMBINED_REGISTRY,
        ))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_bundle.source_authority_custody.currentness."
            "_trust_root_snapshot",
            return_value=("HOST_SYSTEM_V1", 1, 1, 1, 1, 1),
        ))
        return stack

    def journey_mounts(
            self, snapshot, schema, features, selection, *,
            patch_active_generated_grade=True):
        stack = ExitStack()
        active_cache = {}

        def historical_active_grade(run_dir):
            if "grade" not in active_cache:
                from bilqis_mlx.runtime.atlas_admission import (
                    read_accepted_atlas_factory_release,
                )
                release = read_accepted_atlas_factory_release(run_dir)
                members = []
                for capability_id in sorted(release.execution_plan.capability_map):
                    capability = release.curriculum.capability_map[capability_id]
                    semantic_ids = tuple(sorted(set((
                        *capability.taught_roots, *capability.examined_roots,
                    ))))
                    for semantic_id in semantic_ids:
                        members.append(SimpleNamespace(
                            capability_id=capability_id,
                            semantic_id=semantic_id,
                            source_anchor=(release.source_bindings.by_capability[
                                capability_id].source_anchor),
                        ))
                active_cache["grade"] = SimpleNamespace(
                    activation_sha256="e" * 64,
                    definition=SimpleNamespace(
                        definition_sha256="d" * 64,
                        members=tuple(members),
                    ),
                )
            return active_cache["grade"]

        stack.enter_context(self.source_replay(snapshot, schema, features))
        for target in (
            "bilqis_mlx.semantics.atlas.snapshot.load_pinned_atlas_snapshot",
            "bilqis_mlx.semantics.atlas.feature_io_pins.load_pinned_atlas_snapshot",
            "bilqis_mlx.semantics.atlas_features.formal.load_pinned_atlas_snapshot",
            "bilqis_mlx.factory.skos_curriculum.load_pinned_atlas_snapshot",
            "bilqis_mlx.semantics.released_frame_schemas.load_pinned_atlas_snapshot",
            "bilqis_mlx.source_adapters.atoms.admission.load_pinned_atlas_snapshot",
            "bilqis_mlx.source_adapters.atom_binding.load_pinned_atlas_snapshot",
            "bilqis_mlx.runtime.batch_training_authority.load_pinned_atlas_snapshot",
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
        if patch_active_generated_grade:
            stack.enter_context(patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "ensure_active_generated_grade",
                side_effect=historical_active_grade))
            stack.enter_context(patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "read_active_generated_grade",
                side_effect=historical_active_grade))
            stack.enter_context(patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_read_bound_active_generated_grade",
                side_effect=lambda *_args, **_kwargs: historical_active_grade(
                    self.run)))
        return stack

    def exercise_journey(self):
        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)
        with wide_shape_patch(len(snapshot.abi_entries)):
            pointer = self.publish_matching_genesis(snapshot, schema, features)
            before = load_accepted_generation(self.run)
            pointer_bytes = (self.run / "bamf-state.json").read_bytes()
            event_bytes = (self.run / "events.jsonl").read_bytes()
            with self.journey_mounts(
                    snapshot, schema, features, atlas_selection):
                parent, context, atlas_path, _feature_path = _execution_context(self.run)
                program = schedule_program_from_executable_release(context.release)
                school = accepted_priority_school(parent, program)
                selected = select_foundation_priority_visit(
                    self.run, context, atlas_path, program=program, school=school)
                rows = selected.offer.rows()
            after = load_accepted_generation(self.run)
        return pointer, before, after, context, selected, rows, pointer_bytes, event_bytes


def journey_source(snapshot):
    selection = AtlasArtifactSelection("/artifact", *AUTHORIZED_ATLAS)
    adapters = {
        "boolean": BOOLEAN_CONNECTIVE_ADAPTER,
        "micro": MICRO_PREDICATE_ADAPTER,
        "numeric": FINITE_NUMERIC_ADAPTER,
    }
    roles, schemas, bindings = set(), [], []
    with patch(
            "bilqis_mlx.semantics.released_frame_schemas.load_pinned_atlas_snapshot",
            return_value=snapshot):
        for family in ("boolean", "micro", "numeric"):
            manifest = _load_pinned_released_frame_schemas(
                family, selection).manifest
            for body in manifest.bodies:
                frame = body.parse()
                schemas.append(frame.schema_id)
                bindings.append((frame.schema_id, adapters[family]))
                roles.update(role.role_id for role in frame.roles)
    schema = FeatureSchema(
        tuple(sorted(roles)), tuple(sorted(schemas)),
        source_bindings=tuple(sorted(bindings)),
    )
    return (
        schema,
        build_feature_manifest(snapshot, schema),
        selection,
    )
