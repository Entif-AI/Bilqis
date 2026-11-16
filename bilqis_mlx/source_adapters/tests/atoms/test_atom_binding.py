"""Pinned source-owner boundary for raw-atom semantic candidates."""
from dataclasses import replace
import hashlib
import os
from unittest import TestCase, skipUnless

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.adapters import RegisteredSourceAdapter, SourceAdapterRegistry
from bilqis_mlx.factory.model import SourceAdapter
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.atlas_projection import AbiEntry
from bilqis_mlx.semantics.frame_codec import SchemaTagMap
from bilqis_mlx.semantics.frame_compiler import atom_evidence_digest, compile_prefix
from bilqis_mlx.semantics.source_atom_binding import AtomBindingDisposition
from bilqis_mlx.semantics.tests.source_atom_binding.helpers import ROOT, case
from bilqis_mlx.source_adapters.atom_binding import (
    _build_source_atom_handoff_from_witness, _verified_source_row_witness,
    build_source_atom_handoff,
    require_pinned_embedding_ready, revalidate_source_atom_handoff,
    verify_source_row,
)
from bilqis_mlx.source_adapters.atoms.admission import (
    _public_formal_atom_context_from_witness,
)
from bilqis_mlx.source_adapters.atoms.authority import (
    project_verified_row, require_canonical_graph,
)
from bilqis_mlx.source_adapters.tests.atoms.helpers import source_case
from bilqis_mlx.source_adapters.copular import CAPABILITY, SYMBOL
from bilqis_mlx.source_adapters.copular_curriculum import proposed_graph
from bilqis_mlx.source_adapters.school import live_source_registry
from bilqis_mlx.source_adapters import event_frames
from bilqis_mlx.b11_observation import (
    note_atlas_reload, note_provider_draw, source_replay_observation,
)
from bilqis_mlx.live_grade_c import registry_graph
from bilqis_mlx.grade_a_probe import read_sources
from bilqis_mlx.semantics.tests.frame_adapters.helpers import _snapshot as frame_snapshot

REAL_BUNDLE = os.environ.get("BILQIS_A01_ATLAS_BUNDLE", "")


class SourceAtomAdapterTests(TestCase):
    def test_event_graph_extension_projects_source_owned_formal_signature(self):
        graph = event_frames.projected_graph(
            registry_graph(), ("D.EVENT_OCCURRENCE",))
        owner = live_source_registry().require(
            event_frames.GENERATOR, event_frames.ORACLE)
        row = owner.draw(
            source_root=ROOT / "vendor" / "legacy-v16", graph=graph,
            course=None, capability="D.EVENT_OCCURRENCE", seed=1319, each=2)[0]
        witness, reason = _verified_source_row_witness(
            row, expected_adapter_id=event_frames.ADAPTER_ID)
        self.assertIsNone(reason)

        snapshot = frame_snapshot()
        registry_path = ROOT / "bilqis_mlx/semantics/copular_registry_v1.json"
        event_index = graph["tokens"].index(
            event_frames.SYMBOLS["D.EVENT_OCCURRENCE"])
        self.assertEqual(event_index, len(snapshot.abi_entries))
        atlas_semantic_id = event_frames.atlas_semantic_id("D.EVENT_OCCURRENCE")
        event_entry = AbiEntry(
            2, 0, 2, atlas_semantic_id, atlas_semantic_id,
            "EVENT_TEST_EXTENSION", True, True, "EVENT_TEST_EXTENSION")
        snapshot = replace(
            snapshot,
            prior_abi_sha256=hashlib.sha256(registry_path.read_bytes()).hexdigest(),
            abi_entries=(*snapshot.abi_entries[:2], event_entry),
            semantic_lookup=tuple(sorted((
                *((entry.semantic_id, entry.index)
                  for entry in snapshot.abi_entries[:2]),
                (event_entry.semantic_id, 2),
            ))),
        )

        projection = project_verified_row(row, graph, snapshot, witness)
        position = row["tokens"].index(event_index)
        self.assertEqual(
            projection.formal_signatures[position], "Boolean*Boolean->Boolean")
        self.assertEqual(projection.semantic_ids[position], atlas_semantic_id)
        self.assertEqual(projection.abi_indices[position], event_entry.index)
        self.assertNotEqual(event_index, event_entry.index)

        forged = {**graph, "nodes": list(graph["nodes"])}
        forged["nodes"][event_index] = {
            **forged["nodes"][event_index], "signature": "Boolean->Boolean"}
        with self.assertRaises(BilqisError) as caught:
            require_canonical_graph(
                row, forged, ROOT / "vendor" / "legacy-v16")
        self.assertEqual(
            caught.exception.context["reason"],
            "SOURCE_ATOM_SOURCE_GRAPH_DRIFT")

    def test_cohort_owner_resolution_rejects_ambiguous_and_oracle_mismatched_owners(self):
        def registered(generator: str, cohort: str, oracle: str):
            descriptor = SourceAdapter(
                "source.test/" + generator, generator, (oracle,), "0" * 64,
                cohort_generator_id=cohort)
            return RegisteredSourceAdapter(
                descriptor, lambda **_: (), lambda *_args, **_kwargs: True)

        owner = registered("callable.one", "cohort.one", "oracle.v1")
        registry = SourceAdapterRegistry((owner,))
        self.assertIs(registry.resolve_owner("callable.one"), owner)
        self.assertIs(registry.resolve_owner("cohort.one"), owner)
        with self.assertRaisesRegex(ValueError, "FACTORY_SOURCE_ORACLE_NOT_ADAPTER_OWNED"):
            registry.resolve_owner("cohort.one", "forged.oracle")
        ambiguous = SourceAdapterRegistry((
            registered("callable.one", "shared.cohort", "oracle.v1"),
            registered("callable.two", "shared.cohort", "oracle.v1"),
        ))
        with self.assertRaisesRegex(ValueError, "FACTORY_SOURCE_ADAPTER_MISSING"):
            ambiguous.resolve_owner("shared.cohort")

    def test_grade_a_cohort_row_resolves_canonical_callable_owner(self):
        source_root = ROOT / "vendor" / "legacy-v16"
        _, _, graph, _, _ = read_sources(source_root)
        registry = live_source_registry()
        owner = registry.require(
            "bilqis_mlx.grade_a_probe.make_record",
            "bilqis.mlx.grade-a-record-oracle/v2")
        row = owner.draw(
            source_root=source_root, graph=graph, course=None,
            capability="A.IDENTITY", seed=31, each=2)[0]

        self.assertEqual(row["generator"], owner.descriptor.cohort_generator)
        self.assertNotEqual(row["generator"], owner.descriptor.generator_id)
        with source_replay_observation() as observed:
            witness, reason = verify_source_row(
                row, graph, source_root=source_root,
                source_seed=31, source_each=2, course=None,
                source_profile_parameters=None)
        self.assertIsNone(reason)
        self.assertIsNotNone(witness)
        self.assertEqual(observed["provider_draws"], 1)
        self.assertEqual(observed["atlas_reloads"], 0)
        self.assertEqual(witness.generator_id, owner.descriptor.generator_id)
        self.assertEqual(
            witness.oracle_id, owner.descriptor.accepted_oracle_ids[0])

        forged_generator = {**row, "generator": "forged.generator"}
        witness, reason = verify_source_row(
            forged_generator, graph, source_root=source_root,
            source_seed=31, source_each=2, course=None,
            source_profile_parameters=None)
        self.assertIsNone(witness)
        self.assertEqual(reason, "SOURCE_ATOM_SOURCE_ADAPTER_UNSUPPORTED")

        forged_oracle = {**row, "oracle": "forged.oracle"}
        witness, reason = verify_source_row(
            forged_oracle, graph, source_root=source_root,
            source_seed=31, source_each=2, course=None,
            source_profile_parameters=None)
        self.assertIsNone(witness)
        self.assertEqual(reason, "SOURCE_ATOM_SOURCE_ROW_UNVERIFIED")

    def test_prequalified_row_mints_same_witness_without_provider_replay(self):
        source_root = ROOT / "vendor" / "legacy-v16"
        _, _, graph, _, _ = read_sources(source_root)
        owner = live_source_registry().require(
            "bilqis_mlx.grade_a_probe.make_record",
            "bilqis.mlx.grade-a-record-oracle/v2")
        row = owner.draw(
            source_root=source_root, graph=graph, course=None,
            capability="A.IDENTITY", seed=31, each=2)[0]
        expected, reason = verify_source_row(
            row, graph, source_root=source_root, source_seed=31,
            source_each=2, course=None, source_profile_parameters=None)
        self.assertIsNone(reason)
        with source_replay_observation() as observed:
            actual, reason = _verified_source_row_witness(
                row, expected_adapter_id=owner.descriptor.adapter_id)
        self.assertIsNone(reason)
        self.assertEqual(actual, expected)
        self.assertEqual(observed, {
            "provider_draws": 0, "provider_checks": 0, "atlas_reloads": 0})

    @skipUnless(REAL_BUNDLE, "real pinned A01 artifact not mounted")
    def test_prepared_atom_context_and_handoff_match_cold_without_replay(self):
        from bilqis_mlx.semantics.atlas.snapshot import load_pinned_atlas_snapshot

        ast, config, compiled, handoff, selection, row, graph, args = source_case(
            visible_end=2)
        snapshot = load_pinned_atlas_snapshot(selection)
        witness, reason = verify_source_row(
            row, graph, source_root=args["source_root"],
            source_seed=args["source_seed"], source_each=args["source_each"],
            course=None, source_profile_parameters=None)
        self.assertIsNone(reason)
        with source_replay_observation() as observed:
            prepared_ast, prepared_config = _public_formal_atom_context_from_witness(
                selection, snapshot, row, graph, witness,
                source_root=args["source_root"], task=config.task,
                frontier=config.frontier, policy=config.policy)
            prepared_handoff = _build_source_atom_handoff_from_witness(
                compiled, config, selection, snapshot, row, graph, witness,
                source_root=args["source_root"])
        self.assertEqual(prepared_ast, ast)
        self.assertEqual(prepared_config, config)
        self.assertEqual(prepared_handoff, handoff)
        self.assertEqual(observed, {
            "provider_draws": 0, "provider_checks": 0, "atlas_reloads": 0})

    def test_replay_observation_counts_only_inside_active_scope(self):
        note_provider_draw()
        note_atlas_reload()
        with source_replay_observation() as observed:
            note_provider_draw()
            note_atlas_reload()
        self.assertEqual(observed, {
            "provider_draws": 1, "provider_checks": 0, "atlas_reloads": 1})

    def test_unsupported_or_unreproducible_source_row_has_no_witness(self):
        row = {"generator": "missing.generator", "oracle": "missing.oracle",
               "capability": "x", "tokens": [0]}
        witness, reason = verify_source_row(
            row, {"tokens": ["alpha"]}, source_root=ROOT,
            source_seed=1, source_each=1, course=None,
            source_profile_parameters=None)
        self.assertIsNone(witness)
        self.assertEqual(reason, "SOURCE_ATOM_SOURCE_ADAPTER_UNSUPPORTED")

    @skipUnless(REAL_BUNDLE, "real pinned A01 artifact not mounted")
    def test_real_pinned_copular_row_reaches_abi_227_but_remains_source_held(self):
        graph = proposed_graph(registry_graph())
        adapter = live_source_registry().require(
            "bilqis.ithkuil-reference-identity-constructor/v1",
            "bilqis.ithkuil-reference-identity-oracle/v1")
        row = adapter.draw(source_root=ROOT, graph=graph, course=None,
                           capability=CAPABILITY, seed=17, each=1)[0]
        symbols = tuple(graph["tokens"][index] for index in row["tokens"])
        ast, config, _ = case(symbols)
        release = "58e0c281b5da18b9b7e6c803709b29eeeb0a88f16b06f48de692808e2fb88306"
        ast = replace(ast, source_instance_id=row["source_id"])
        task = replace(config.task, semantic_release=release)
        schema_map = SchemaTagMap.from_schemas(release, ())
        atoms_by_reference = {atom.source_reference: atom for atom in ast.atoms}
        grants = tuple(replace(
            grant, semantic_release=release,
            evidence_digest=atom_evidence_digest(
                ast.source_instance_id, atoms_by_reference[grant.source_handle], release))
            for grant in config.frontier.grants)
        config = replace(config, task=task, schema_map=schema_map,
                         frontier=replace(config.frontier, grants=grants))
        compiled = compile_prefix(ast, len(ast.atoms), release, config)
        selection = AtlasArtifactSelection(
            REAL_BUNDLE,
            "5f8fba20ecc0adebf39c3b663fdffa4f766e780915197f09d116713042a479e7",
            release,
            "f1c89c1d1bcd72695c81f8e777d0fbbdf446e92cb27132bebf1cd6873ec689ec")
        handoff = build_source_atom_handoff(
            compiled, config, selection, row, graph,
            source_root=ROOT, source_seed=17, source_each=1, course=None)
        binding = handoff.bindings[symbols.index(SYMBOL)]
        self.assertEqual(binding.candidate_abi_index, 227)
        self.assertEqual(binding.candidate_semantic_id,
                         "ithkuil:LEXSENSE-5286ade9db42c7/finite-reference-identity/v1")
        self.assertEqual(binding.disposition, AtomBindingDisposition.SOURCE_HELD)
        self.assertIn("SOURCE_ATOM_REFERENCE_AUTHORITY_UNAVAILABLE", binding.reason_codes)
        self.assertIn("SOURCE_ATOM_INSTANCE_AUTHORITY_UNAVAILABLE", binding.reason_codes)
        self.assertIn("SOURCE_ATOM_TYPE_AUTHORITY_UNAVAILABLE", binding.reason_codes)
        self.assertFalse(handoff.embedding_ready)
        revalidate_source_atom_handoff(
            handoff, compiled, config, selection, row, graph,
            source_root=ROOT, source_seed=17, source_each=1, course=None)
        with self.assertRaises(BilqisError) as caught:
            require_pinned_embedding_ready(
                handoff, compiled, config, selection, row, graph,
                source_root=ROOT, source_seed=17, source_each=1, course=None)
        self.assertEqual(caught.exception.context["reason"], "BAMF_SOURCE_ATOM_BINDING_HELD")
        for changed in (replace(selection, release_sha256="9" * 64),
                        replace(selection, bundle_id="8" * 64)):
            with self.assertRaises(BilqisError):
                build_source_atom_handoff(
                    compiled, config, changed, row, graph,
                    source_root=ROOT, source_seed=17, source_each=1, course=None)
        with self.assertRaises(BilqisError):
            replace(handoff, visible_end=handoff.visible_end + 1,
                    bindings=(*handoff.bindings, handoff.bindings[-1]))
